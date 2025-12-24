"""
Unit tests for the Poller service.

Tests polling logic, status caching, error handling, concurrency control,
and server list reloading.
"""
import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from app.models import Server, ServerStatus, Channel
from app.services.poller import Poller


class TestPollerInit:
    """Tests for Poller initialization."""
    
    def test_poller_init_with_servers(self, test_servers):
        """Test Poller initialization with server list."""
        poller = Poller(test_servers)
        assert poller.servers == test_servers
        assert len(poller.servers) == 2
        assert poller._task is None
        assert isinstance(poller._statuses, dict)
        assert len(poller._statuses) == 0
    
    def test_poller_init_respects_max_servers(self, test_servers):
        """Test that Poller respects MAX_SERVERS setting."""
        with patch("app.services.poller.settings") as mock_settings:
            mock_settings.MAX_SERVERS = 1
            mock_settings.HTTPX_TIMEOUT_SECONDS = 5
            mock_settings.POLL_CONCURRENCY = 10
            
            poller = Poller(test_servers)
            assert len(poller.servers) == 1
    
    def test_poller_init_with_empty_list(self):
        """Test Poller initialization with empty server list."""
        poller = Poller([])
        assert poller.servers == []
        assert len(poller.servers) == 0
    
    def test_poller_init_creates_semaphore(self, test_servers):
        """Test that Poller creates a semaphore for concurrency control."""
        with patch("app.services.poller.settings") as mock_settings:
            mock_settings.POLL_CONCURRENCY = 5
            mock_settings.MAX_SERVERS = 100
            mock_settings.HTTPX_TIMEOUT_SECONDS = 5
            
            poller = Poller(test_servers)
            assert poller._semaphore is not None
            assert isinstance(poller._semaphore, asyncio.Semaphore)


class TestPollerStartStop:
    """Tests for Poller start and stop methods."""
    
    @pytest.mark.asyncio
    async def test_poller_start_creates_task(self, test_servers):
        """Test that Poller.start() creates an async task."""
        poller = Poller(test_servers)
        await poller.start()
        
        assert poller._task is not None
        assert isinstance(poller._task, asyncio.Task)
        
        await poller.stop()
    
    @pytest.mark.asyncio
    async def test_poller_start_idempotent(self, test_servers):
        """Test that calling start() multiple times doesn't create multiple tasks."""
        poller = Poller(test_servers)
        await poller.start()
        task1 = poller._task
        
        await poller.start()
        task2 = poller._task
        
        assert task1 is task2
        
        await poller.stop()
    
    @pytest.mark.asyncio
    async def test_poller_stop_cleans_up_task(self, test_servers):
        """Test that Poller.stop() cleans up the task."""
        poller = Poller(test_servers)
        await poller.start()
        await poller.stop()
        
        assert poller._task is None
    
    @pytest.mark.asyncio
    async def test_poller_stop_without_start(self, test_servers):
        """Test that calling stop() without start() doesn't raise error."""
        poller = Poller(test_servers)
        await poller.stop()  # Should not raise
        assert poller._task is None
    
    @pytest.mark.asyncio
    async def test_poller_stop_closes_http_client(self, test_servers):
        """Test that Poller.stop() closes the HTTP client."""
        poller = Poller(test_servers)
        
        with patch.object(poller._client, 'aclose', new_callable=AsyncMock) as mock_aclose:
            await poller.start()
            await poller.stop()
            mock_aclose.assert_called_once()


class TestPollerFetch:
    """Tests for Poller._fetch method."""
    
    @pytest.mark.asyncio
    async def test_fetch_success_updates_status(self, test_servers):
        """Test successful fetch updates server status."""
        poller = Poller(test_servers)
        server = test_servers[0]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cpu": [30.0, 40.0, 50.0],
            "channels": [
                {"id": "1", "name": "Channel 1", "status": "running"}
            ]
        }
        
        with patch.object(poller._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            await poller._fetch(server)
            
            status = poller.get_status(server.id)
            assert status is not None
            assert status.id == server.id
            assert status.cpu == 40.0  # Average of [30, 40, 50]
            assert len(status.channels) == 1
            assert status.channels[0].id == "1"
    
    @pytest.mark.asyncio
    async def test_fetch_handles_timeout(self, test_servers):
        """Test that fetch handles timeout exceptions."""
        poller = Poller(test_servers)
        server = test_servers[0]
        
        with patch.object(poller._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Timeout")
            
            await poller._fetch(server)
            
            # Should create default status on timeout
            status = poller.get_status(server.id)
            assert status is not None
            assert status.cpu == 0.0
            assert status.channels == []
    
    @pytest.mark.asyncio
    async def test_fetch_handles_http_error(self, test_servers):
        """Test that fetch handles HTTP errors."""
        poller = Poller(test_servers)
        server = test_servers[0]
        
        with patch.object(poller._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.HTTPError("Connection failed")
            
            await poller._fetch(server)
            
            # Should create default status on error
            status = poller.get_status(server.id)
            assert status is not None
            assert status.cpu == 0.0
            assert status.channels == []
    
    @pytest.mark.asyncio
    async def test_fetch_handles_json_decode_error(self, test_servers):
        """Test that fetch handles JSON decode errors."""
        poller = Poller(test_servers)
        server = test_servers[0]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        with patch.object(poller._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            await poller._fetch(server)
            
            # Should create default status on JSON error
            status = poller.get_status(server.id)
            assert status is not None
            assert status.cpu == 0.0
            assert status.channels == []
    
    @pytest.mark.asyncio
    async def test_fetch_handles_non_200_status(self, test_servers):
        """Test that fetch handles non-200 HTTP status codes."""
        poller = Poller(test_servers)
        server = test_servers[0]
        
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch.object(poller._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            await poller._fetch(server)
            
            # Should create default status on error
            status = poller.get_status(server.id)
            assert status is not None
            assert status.cpu == 0.0
            assert status.channels == []
    
    @pytest.mark.asyncio
    async def test_fetch_cpu_calculation_average(self, test_servers):
        """Test CPU average calculation."""
        poller = Poller(test_servers)
        server = test_servers[0]
        
        test_cases = [
            ([10.0, 20.0], 15.0),
            ([30.0, 40.0, 50.0], 40.0),
            ([100.0], 100.0),
            ([], 0.0),  # Empty CPU array
        ]
        
        for cpu_values, expected_avg in test_cases:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "cpu": cpu_values,
                "channels": []
            }
            
            with patch.object(poller._client, 'get', new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_response
                
                await poller._fetch(server)
                
                status = poller.get_status(server.id)
                assert status.cpu == expected_avg
    
    @pytest.mark.asyncio
    async def test_fetch_uses_semaphore(self, test_servers):
        """Test that fetch uses semaphore for concurrency control."""
        poller = Poller(test_servers)
        server = test_servers[0]
        
        # Mock semaphore to track usage
        original_semaphore = poller._semaphore
        mock_semaphore = AsyncMock()
        mock_semaphore.__aenter__ = AsyncMock()
        mock_semaphore.__aexit__ = AsyncMock()
        poller._semaphore = mock_semaphore
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"cpu": [], "channels": []}
        
        with patch.object(poller._client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            await poller._fetch(server)
            
            # Semaphore should have been used
            assert mock_semaphore.__aenter__.called
            assert mock_semaphore.__aexit__.called


class TestPollerGetStatus:
    """Tests for Poller.get_status method."""
    
    def test_get_status_existing_server(self, test_servers):
        """Test getting status for existing server."""
        poller = Poller(test_servers)
        server_id = test_servers[0].id
        
        # Manually add status
        test_status = ServerStatus(id=server_id, cpu=50.0, channels=[])
        poller._statuses[server_id] = test_status
        
        status = poller.get_status(server_id)
        assert status is not None
        assert status.id == server_id
        assert status.cpu == 50.0
    
    def test_get_status_non_existing_server(self, test_servers):
        """Test getting status for non-existing server returns None."""
        poller = Poller(test_servers)
        
        status = poller.get_status("non_existing_server")
        assert status is None
    
    def test_get_status_empty_statuses(self, test_servers):
        """Test getting status when no statuses have been cached."""
        poller = Poller(test_servers)
        
        status = poller.get_status(test_servers[0].id)
        assert status is None


class TestPollerGetAll:
    """Tests for Poller.get_all method."""
    
    def test_get_all_with_statuses(self, test_servers):
        """Test getting all statuses when some exist."""
        poller = Poller(test_servers)
        
        # Add some statuses
        status1 = ServerStatus(id="srv1", cpu=30.0, channels=[])
        status2 = ServerStatus(id="srv2", cpu=40.0, channels=[])
        poller._statuses["srv1"] = status1
        poller._statuses["srv2"] = status2
        
        all_statuses = poller.get_all()
        assert len(all_statuses) == 2
        assert status1 in all_statuses
        assert status2 in all_statuses
    
    def test_get_all_empty_statuses(self, test_servers):
        """Test getting all statuses when none exist."""
        poller = Poller(test_servers)
        
        all_statuses = poller.get_all()
        assert len(all_statuses) == 0
        assert isinstance(all_statuses, list)


class TestPollerReloadServers:
    """Tests for Poller.reload_servers method."""
    
    @pytest.mark.asyncio
    async def test_reload_servers_updates_server_list(self, test_servers):
        """Test that reload_servers updates the server list."""
        poller = Poller(test_servers[:1])  # Start with 1 server
        assert len(poller.servers) == 1
        
        await poller.reload_servers(test_servers)  # Reload with 2 servers
        assert len(poller.servers) == 2
        assert poller.servers == test_servers
    
    @pytest.mark.asyncio
    async def test_reload_servers_removes_old_statuses(self, test_servers):
        """Test that reload_servers removes statuses for removed servers."""
        poller = Poller(test_servers)
        
        # Add statuses for both servers
        poller._statuses["test1"] = ServerStatus(id="test1", cpu=30.0, channels=[])
        poller._statuses["test2"] = ServerStatus(id="test2", cpu=40.0, channels=[])
        
        # Reload with only first server
        await poller.reload_servers(test_servers[:1])
        
        assert "test1" in poller._statuses
        assert "test2" not in poller._statuses
    
    @pytest.mark.asyncio
    async def test_reload_servers_keeps_existing_statuses(self, test_servers):
        """Test that reload_servers keeps statuses for servers that remain."""
        poller = Poller(test_servers)
        
        # Add status for first server
        poller._statuses["test1"] = ServerStatus(id="test1", cpu=30.0, channels=[])
        
        # Reload with same servers
        await poller.reload_servers(test_servers)
        
        assert "test1" in poller._statuses
        assert poller._statuses["test1"].cpu == 30.0
    
    @pytest.mark.asyncio
    async def test_reload_servers_respects_max_servers(self, test_servers):
        """Test that reload_servers respects MAX_SERVERS limit."""
        with patch("app.services.poller.settings") as mock_settings:
            mock_settings.MAX_SERVERS = 1
            mock_settings.HTTPX_TIMEOUT_SECONDS = 5
            mock_settings.POLL_CONCURRENCY = 10
            
            poller = Poller([])
            await poller.reload_servers(test_servers)
            
            assert len(poller.servers) == 1
    
    @pytest.mark.asyncio
    async def test_reload_servers_with_empty_list(self, test_servers):
        """Test reloading with empty server list."""
        poller = Poller(test_servers)
        
        # Add statuses
        poller._statuses["test1"] = ServerStatus(id="test1", cpu=30.0, channels=[])
        
        # Reload with empty list
        await poller.reload_servers([])
        
        assert len(poller.servers) == 0
        assert len(poller._statuses) == 0
    
    @pytest.mark.asyncio
    async def test_reload_servers_thread_safe(self, test_servers):
        """Test that reload_servers uses lock for thread safety."""
        poller = Poller(test_servers)
        
        # Mock lock to verify it's used
        original_lock = poller._lock
        mock_lock = AsyncMock()
        mock_lock.__aenter__ = AsyncMock()
        mock_lock.__aexit__ = AsyncMock()
        poller._lock = mock_lock
        
        await poller.reload_servers(test_servers)
        
        assert mock_lock.__aenter__.called
        assert mock_lock.__aexit__.called
