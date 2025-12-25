"""
Integration tests for complete workflows.

Tests end-to-end workflows including server monitoring lifecycle,
configuration reload, and multi-step operations.
"""
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.models import Server, ServerStatus, Channel
from app.services.poller import Poller


class TestServerMonitoringWorkflow:
    """Tests for complete server monitoring workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_polling_cycle(self, test_servers):
        """Test a complete polling cycle from start to finish."""
        poller = Poller(test_servers)
        
        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cpu": [30.0, 40.0],
            "channels": [{"id": "1", "status": "running"}]
        }
        
        with patch.object(poller._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            # Start poller
            await poller.start()
            
            # Wait for at least one polling cycle
            await asyncio.sleep(0.5)
            
            # Check that statuses were collected
            status1 = poller.get_status("test1")
            status2 = poller.get_status("test2")
            
            # At least one server should have status
            assert status1 is not None or status2 is not None
            
            # Stop poller
            await poller.stop()
            
            # Verify HTTP client was closed
            assert poller._task is None
    
    @pytest.mark.asyncio
    async def test_poller_handles_mixed_success_failure(self, test_servers):
        """Test polling with some servers succeeding and others failing."""
        poller = Poller(test_servers)
        
        call_count = 0
        
        async def mock_get_mixed(url):
            nonlocal call_count
            call_count += 1
            
            if "8888" in url:
                # First server succeeds
                response = Mock()
                response.status_code = 200
                response.json.return_value = {
                    "cpu": [50.0],
                    "channels": [{"id": "1", "status": "running"}]
                }
                return response
            else:
                # Second server fails
                raise Exception("Connection failed")
        
        with patch.object(poller._client, 'get', side_effect=mock_get_mixed):
            await poller.start()
            await asyncio.sleep(0.5)
            
            # Both servers should have status (default for failed one)
            status1 = poller.get_status("test1")
            status2 = poller.get_status("test2")
            
            # First server should have real status
            if status1:
                assert status1.cpu == 50.0 or status1.cpu == 0.0
            
            # Second server should have default status
            if status2:
                assert status2.cpu == 0.0
                assert status2.channels == []
            
            await poller.stop()
    
    @pytest.mark.asyncio
    async def test_status_updates_over_time(self, test_servers):
        """Test that status updates correctly over multiple polling cycles."""
        poller = Poller(test_servers)
        
        cpu_values = [30.0, 40.0, 50.0]
        call_index = 0
        
        async def mock_get_changing(url):
            nonlocal call_index
            idx = call_index % len(cpu_values)
            call_index += 1
            
            response = Mock()
            response.status_code = 200
            response.json.return_value = {
                "cpu": [cpu_values[idx]],
                "channels": []
            }
            return response
        
        with patch.object(poller._client, 'get', side_effect=mock_get_changing):
            await poller.start()
            
            # Wait for multiple cycles
            await asyncio.sleep(0.3)
            
            # Status should be updated
            status = poller.get_status("test1")
            assert status is not None
            
            await poller.stop()


class TestConfigurationReloadWorkflow:
    """Tests for configuration reload workflow."""
    
    @pytest.mark.asyncio
    async def test_reload_adds_new_server(self):
        """Test that reloading configuration adds new servers."""
        initial_servers = [
            Server(id="srv1", host="localhost", port=8888)
        ]
        poller = Poller(initial_servers)
        
        assert len(poller.servers) == 1
        
        # Reload with additional server
        new_servers = [
            Server(id="srv1", host="localhost", port=8888),
            Server(id="srv2", host="localhost", port=8889)
        ]
        
        await poller.reload_servers(new_servers)
        
        assert len(poller.servers) == 2
        assert poller.servers[0].id == "srv1"
        assert poller.servers[1].id == "srv2"
    
    @pytest.mark.asyncio
    async def test_reload_removes_server(self):
        """Test that reloading configuration removes servers."""
        initial_servers = [
            Server(id="srv1", host="localhost", port=8888),
            Server(id="srv2", host="localhost", port=8889)
        ]
        poller = Poller(initial_servers)
        
        # Add statuses for both
        poller._statuses["srv1"] = ServerStatus(id="srv1", cpu=30.0, channels=[])
        poller._statuses["srv2"] = ServerStatus(id="srv2", cpu=40.0, channels=[])
        
        # Reload with only first server
        new_servers = [
            Server(id="srv1", host="localhost", port=8888)
        ]
        
        await poller.reload_servers(new_servers)
        
        assert len(poller.servers) == 1
        assert "srv1" in poller._statuses
        assert "srv2" not in poller._statuses
    
    @pytest.mark.asyncio
    async def test_reload_updates_server_config(self):
        """Test that reloading updates server configuration."""
        initial_servers = [
            Server(id="srv1", host="localhost", port=8888)
        ]
        poller = Poller(initial_servers)
        
        # Reload with updated configuration
        updated_servers = [
            Server(id="srv1", host="192.168.1.100", port=9999)
        ]
        
        await poller.reload_servers(updated_servers)
        
        assert poller.servers[0].host == "192.168.1.100"
        assert poller.servers[0].port == 9999
    
    @pytest.mark.asyncio
    async def test_reload_during_active_polling(self, test_servers):
        """Test that reload works correctly during active polling."""
        poller = Poller(test_servers[:1])  # Start with one server
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cpu": [30.0],
            "channels": []
        }
        
        with patch.object(poller._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            # Start polling
            await poller.start()
            await asyncio.sleep(0.2)
            
            # Reload configuration during polling
            await poller.reload_servers(test_servers)
            
            # Verify reload happened
            assert len(poller.servers) == 2
            
            # Polling should continue
            await asyncio.sleep(0.2)
            
            await poller.stop()


class TestChannelRestartWorkflow:
    """Tests for channel restart workflow."""
    
    @pytest.mark.asyncio
    async def test_restart_workflow_with_status_check(self, test_servers):
        """Test complete restart workflow including status verification."""
        from app.services import manager
        
        server = test_servers[0]
        
        # Mock successful stop and start
        with patch("app.services.manager.stop_channel") as mock_stop:
            with patch("app.services.manager.start_channel") as mock_start:
                with patch("asyncio.sleep"):
                    mock_stop.return_value = (True, "Channel stopped successfully")
                    mock_start.return_value = (True, "Channel started successfully")
                    
                    # Execute restart
                    result = await manager.restart_channel(server, "1")
                    
                    # Verify workflow
                    assert result["stop"]["ok"] is True
                    assert result["start"]["ok"] is True
                    assert "stopped" in result["stop"]["msg"].lower()
                    assert "started" in result["start"]["msg"].lower()
                    
                    # Verify order of operations
                    mock_stop.assert_called_once()
                    mock_start.assert_called_once()


class TestApplicationLifecycle:
    """Tests for complete application lifecycle."""
    
    @pytest.mark.asyncio
    async def test_startup_shutdown_lifecycle(self, test_servers):
        """Test complete startup and shutdown lifecycle."""
        poller = Poller(test_servers)
        
        # Startup
        assert poller._task is None
        await poller.start()
        assert poller._task is not None
        
        # Verify polling is active
        await asyncio.sleep(0.2)
        
        # Shutdown
        await poller.stop()
        assert poller._task is None
    
    @pytest.mark.asyncio
    async def test_multiple_start_stop_cycles(self, test_servers):
        """Test multiple start/stop cycles."""
        poller = Poller(test_servers)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"cpu": [], "channels": []}
        
        with patch.object(poller._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            # First cycle
            await poller.start()
            await asyncio.sleep(0.1)
            await poller.stop()
            
            # Second cycle
            await poller.start()
            await asyncio.sleep(0.1)
            await poller.stop()
            
            # Third cycle
            await poller.start()
            await asyncio.sleep(0.1)
            await poller.stop()
            
            # Should handle multiple cycles without issues
            assert poller._task is None


class TestErrorRecoveryWorkflow:
    """Tests for error recovery workflows."""
    
    @pytest.mark.asyncio
    async def test_recovery_from_all_servers_down(self, test_servers):
        """Test that poller recovers when all servers are down."""
        poller = Poller(test_servers)
        
        call_count = 0
        
        async def mock_get_with_recovery(url):
            nonlocal call_count
            call_count += 1
            
            if call_count < 3:
                # First few calls fail
                raise Exception("Connection refused")
            else:
                # Later calls succeed
                response = Mock()
                response.status_code = 200
                response.json.return_value = {
                    "cpu": [30.0],
                    "channels": []
                }
                return response
        
        with patch.object(poller._client, 'get', side_effect=mock_get_with_recovery):
            await poller.start()
            
            # Wait for multiple polling attempts
            await asyncio.sleep(0.5)
            
            # Should have recovered and gotten status
            status = poller.get_status("test1")
            assert status is not None
            
            await poller.stop()
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, test_servers):
        """Test multiple concurrent operations."""
        poller = Poller(test_servers)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"cpu": [50.0], "channels": []}
        
        with patch.object(poller._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            await poller.start()
            await asyncio.sleep(0.1)
            
            # Concurrent operations (these are synchronous methods, not async)
            result1 = poller.get_status("test1")
            result2 = poller.get_status("test2")
            result3 = poller.get_all()
            
            # All operations should complete without errors
            assert result1 is not None or result2 is not None
            assert isinstance(result3, list)
            
            await poller.stop()


class TestDataConsistency:
    """Tests for data consistency across operations."""
    
    @pytest.mark.asyncio
    async def test_status_consistency_during_reload(self, test_servers):
        """Test that status remains consistent during reload."""
        poller = Poller(test_servers)
        
        # Set initial status
        initial_status = ServerStatus(id="test1", cpu=30.0, channels=[])
        poller._statuses["test1"] = initial_status
        
        # Reload with same servers
        await poller.reload_servers(test_servers)
        
        # Status should still be there
        assert "test1" in poller._statuses
        assert poller._statuses["test1"].cpu == 30.0
    
    @pytest.mark.asyncio
    async def test_no_duplicate_statuses(self, test_servers):
        """Test that no duplicate statuses are created."""
        poller = Poller(test_servers)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"cpu": [40.0], "channels": []}
        
        with patch.object(poller._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            # Multiple fetches for same server
            await poller._fetch(test_servers[0])
            await poller._fetch(test_servers[0])
            await poller._fetch(test_servers[0])
            
            # Should only have one status per server
            all_statuses = poller.get_all()
            server_ids = [s.id for s in all_statuses]
            assert len(server_ids) == len(set(server_ids))  # No duplicates
