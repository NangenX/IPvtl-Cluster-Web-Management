"""
Unit tests for the manager service.

Tests channel management operations including stop, start, and restart
with various success and failure scenarios.
"""
import asyncio
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from app.models import Server
from app.services import manager


class TestStopChannel:
    """Tests for the stop_channel function."""
    
    @pytest.mark.asyncio
    async def test_stop_channel_success(self):
        """Test successful channel stop operation."""
        server = Server(id="srv1", host="localhost", port=8888)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Channel stopped"
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            success, message = await manager.stop_channel(server, "1")
            
            assert success is True
            assert message == "Channel stopped"
            mock_client.get.assert_called_once_with("http://localhost:8888/channel1?stop")
    
    @pytest.mark.asyncio
    async def test_stop_channel_failure_non_200(self):
        """Test channel stop with non-200 response."""
        server = Server(id="srv1", host="localhost", port=8888)
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            success, message = await manager.stop_channel(server, "1")
            
            assert success is False
            assert message == "Internal Server Error"
    
    @pytest.mark.asyncio
    async def test_stop_channel_timeout(self):
        """Test channel stop with timeout exception."""
        server = Server(id="srv1", host="localhost", port=8888)
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            success, message = await manager.stop_channel(server, "1")
            
            assert success is False
            assert "Timeout" in message
    
    @pytest.mark.asyncio
    async def test_stop_channel_http_error(self):
        """Test channel stop with HTTP error."""
        server = Server(id="srv1", host="localhost", port=8888)
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.HTTPError("Connection failed")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            success, message = await manager.stop_channel(server, "1")
            
            assert success is False
            assert "HTTP Error" in message
    
    @pytest.mark.asyncio
    async def test_stop_channel_generic_exception(self):
        """Test channel stop with generic exception."""
        server = Server(id="srv1", host="localhost", port=8888)
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("Unexpected error")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            success, message = await manager.stop_channel(server, "1")
            
            assert success is False
            assert "Unexpected error" in message
    
    @pytest.mark.asyncio
    async def test_stop_channel_uses_correct_url(self):
        """Test that stop_channel constructs correct URL."""
        server = Server(id="srv1", host="192.168.1.100", port=9000)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            await manager.stop_channel(server, "5")
            
            mock_client.get.assert_called_once_with("http://192.168.1.100:9000/channel5?stop")
    
    @pytest.mark.asyncio
    async def test_stop_channel_default_port(self):
        """Test stop_channel with server having no port (defaults to 80)."""
        server = Server(id="srv1", host="localhost", port=None)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            await manager.stop_channel(server, "1")
            
            mock_client.get.assert_called_once_with("http://localhost:80/channel1?stop")
    
    @pytest.mark.asyncio
    async def test_stop_channel_respects_timeout_setting(self):
        """Test that stop_channel uses configured timeout."""
        server = Server(id="srv1", host="localhost", port=8888)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        
        with patch("app.services.manager.settings") as mock_settings:
            mock_settings.RESTART_STOP_TIMEOUT_SECONDS = 20
            
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get.return_value = mock_response
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client_class.return_value = mock_client
                
                await manager.stop_channel(server, "1")
                
                # Verify AsyncClient was created with correct timeout
                mock_client_class.assert_called_once_with(timeout=20)


class TestStartChannel:
    """Tests for the start_channel function."""
    
    @pytest.mark.asyncio
    async def test_start_channel_success(self):
        """Test successful channel start operation."""
        server = Server(id="srv1", host="localhost", port=8888)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Channel started"
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            success, message = await manager.start_channel(server, "1")
            
            assert success is True
            assert message == "Channel started"
            mock_client.get.assert_called_once_with("http://localhost:8888/channel1?start")
    
    @pytest.mark.asyncio
    async def test_start_channel_failure_non_200(self):
        """Test channel start with non-200 response."""
        server = Server(id="srv1", host="localhost", port=8888)
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Channel not found"
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            success, message = await manager.start_channel(server, "1")
            
            assert success is False
            assert message == "Channel not found"
    
    @pytest.mark.asyncio
    async def test_start_channel_timeout(self):
        """Test channel start with timeout exception."""
        server = Server(id="srv1", host="localhost", port=8888)
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Timeout")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            success, message = await manager.start_channel(server, "1")
            
            assert success is False
            assert "Timeout" in message
    
    @pytest.mark.asyncio
    async def test_start_channel_http_error(self):
        """Test channel start with HTTP error."""
        server = Server(id="srv1", host="localhost", port=8888)
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.HTTPError("Connection refused")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            success, message = await manager.start_channel(server, "1")
            
            assert success is False
            assert "HTTP Error" in message
    
    @pytest.mark.asyncio
    async def test_start_channel_generic_exception(self):
        """Test channel start with generic exception."""
        server = Server(id="srv1", host="localhost", port=8888)
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("Network error")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            success, message = await manager.start_channel(server, "1")
            
            assert success is False
            assert "Network error" in message
    
    @pytest.mark.asyncio
    async def test_start_channel_uses_correct_url(self):
        """Test that start_channel constructs correct URL."""
        server = Server(id="srv1", host="10.0.0.5", port=7777)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client
            
            await manager.start_channel(server, "3")
            
            mock_client.get.assert_called_once_with("http://10.0.0.5:7777/channel3?start")
    
    @pytest.mark.asyncio
    async def test_start_channel_respects_timeout_setting(self):
        """Test that start_channel uses configured timeout."""
        server = Server(id="srv1", host="localhost", port=8888)
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        
        with patch("app.services.manager.settings") as mock_settings:
            mock_settings.RESTART_START_TIMEOUT_SECONDS = 25
            
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.get.return_value = mock_response
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client_class.return_value = mock_client
                
                await manager.start_channel(server, "1")
                
                # Verify AsyncClient was created with correct timeout
                mock_client_class.assert_called_once_with(timeout=25)


class TestRestartChannel:
    """Tests for the restart_channel function."""
    
    @pytest.mark.asyncio
    async def test_restart_channel_success(self):
        """Test successful channel restart operation."""
        server = Server(id="srv1", host="localhost", port=8888)
        
        with patch("app.services.manager.stop_channel") as mock_stop:
            with patch("app.services.manager.start_channel") as mock_start:
                with patch("asyncio.sleep") as mock_sleep:
                    mock_stop.return_value = (True, "Stopped")
                    mock_start.return_value = (True, "Started")
                    
                    result = await manager.restart_channel(server, "1")
                    
                    assert result["server_id"] == "srv1"
                    assert result["channel_id"] == "1"
                    assert result["stop"]["ok"] is True
                    assert result["stop"]["msg"] == "Stopped"
                    assert result["start"]["ok"] is True
                    assert result["start"]["msg"] == "Started"
                    
                    mock_stop.assert_called_once_with(server, "1")
                    mock_start.assert_called_once_with(server, "1")
                    mock_sleep.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_restart_channel_stop_fails(self):
        """Test restart when stop operation fails."""
        server = Server(id="srv1", host="localhost", port=8888)
        
        with patch("app.services.manager.stop_channel") as mock_stop:
            with patch("app.services.manager.start_channel") as mock_start:
                with patch("asyncio.sleep"):
                    mock_stop.return_value = (False, "Stop failed")
                    mock_start.return_value = (True, "Started")
                    
                    result = await manager.restart_channel(server, "1")
                    
                    assert result["stop"]["ok"] is False
                    assert result["stop"]["msg"] == "Stop failed"
                    assert result["start"]["ok"] is True
                    # Start should still be called even if stop fails
                    mock_start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_restart_channel_start_fails(self):
        """Test restart when start operation fails."""
        server = Server(id="srv1", host="localhost", port=8888)
        
        with patch("app.services.manager.stop_channel") as mock_stop:
            with patch("app.services.manager.start_channel") as mock_start:
                with patch("asyncio.sleep"):
                    mock_stop.return_value = (True, "Stopped")
                    mock_start.return_value = (False, "Start failed")
                    
                    result = await manager.restart_channel(server, "1")
                    
                    assert result["stop"]["ok"] is True
                    assert result["start"]["ok"] is False
                    assert result["start"]["msg"] == "Start failed"
    
    @pytest.mark.asyncio
    async def test_restart_channel_both_fail(self):
        """Test restart when both stop and start fail."""
        server = Server(id="srv1", host="localhost", port=8888)
        
        with patch("app.services.manager.stop_channel") as mock_stop:
            with patch("app.services.manager.start_channel") as mock_start:
                with patch("asyncio.sleep"):
                    mock_stop.return_value = (False, "Stop failed")
                    mock_start.return_value = (False, "Start failed")
                    
                    result = await manager.restart_channel(server, "1")
                    
                    assert result["stop"]["ok"] is False
                    assert result["start"]["ok"] is False
    
    @pytest.mark.asyncio
    async def test_restart_channel_delay(self):
        """Test that restart has delay between stop and start."""
        server = Server(id="srv1", host="localhost", port=8888)
        
        with patch("app.services.manager.stop_channel") as mock_stop:
            with patch("app.services.manager.start_channel") as mock_start:
                with patch("asyncio.sleep") as mock_sleep:
                    with patch("app.services.manager.settings") as mock_settings:
                        mock_settings.RESTART_DELAY_SECONDS = 1.5
                        mock_stop.return_value = (True, "Stopped")
                        mock_start.return_value = (True, "Started")
                        
                        await manager.restart_channel(server, "1")
                        
                        mock_sleep.assert_called_once_with(1.5)
    
    @pytest.mark.asyncio
    async def test_restart_channel_order(self):
        """Test that restart calls stop before start."""
        server = Server(id="srv1", host="localhost", port=8888)
        call_order = []
        
        async def mock_stop_func(srv, ch):
            call_order.append("stop")
            return (True, "Stopped")
        
        async def mock_start_func(srv, ch):
            call_order.append("start")
            return (True, "Started")
        
        with patch("app.services.manager.stop_channel", side_effect=mock_stop_func):
            with patch("app.services.manager.start_channel", side_effect=mock_start_func):
                with patch("asyncio.sleep"):
                    await manager.restart_channel(server, "1")
                    
                    assert call_order == ["stop", "start"]
    
    @pytest.mark.asyncio
    async def test_restart_channel_result_structure(self):
        """Test that restart returns correct result structure."""
        server = Server(id="srv1", host="localhost", port=8888)
        
        with patch("app.services.manager.stop_channel") as mock_stop:
            with patch("app.services.manager.start_channel") as mock_start:
                with patch("asyncio.sleep"):
                    mock_stop.return_value = (True, "Stopped")
                    mock_start.return_value = (True, "Started")
                    
                    result = await manager.restart_channel(server, "5")
                    
                    # Verify structure
                    assert "server_id" in result
                    assert "channel_id" in result
                    assert "stop" in result
                    assert "start" in result
                    assert "ok" in result["stop"]
                    assert "msg" in result["stop"]
                    assert "ok" in result["start"]
                    assert "msg" in result["start"]
                    
                    assert result["channel_id"] == "5"
