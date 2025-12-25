"""
Integration tests for API endpoints.

Tests all API endpoints using FastAPI TestClient with mocked dependencies.
"""
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import Server, ServerStatus, Channel


@pytest.fixture
def client():
    """Create a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_poller(test_servers):
    """Create a mock Poller instance."""
    mock = Mock()
    mock.servers = test_servers
    mock.get_status = Mock(return_value=None)
    mock.get_all = Mock(return_value=[])
    mock.reload_servers = AsyncMock()
    return mock


@pytest.fixture
def setup_app_with_mock_poller(mock_poller):
    """Setup app with mock poller."""
    app.state.poller = mock_poller
    yield
    # Cleanup
    if hasattr(app.state, "poller"):
        delattr(app.state, "poller")


class TestGetServers:
    """Tests for GET /api/servers endpoint."""
    
    def test_get_servers_returns_list(self, client, setup_app_with_mock_poller, mock_poller):
        """Test that GET /api/servers returns a list of servers."""
        response = client.get("/api/servers")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
    
    def test_get_servers_returns_server_details(self, client, setup_app_with_mock_poller, mock_poller):
        """Test that server details are correctly returned."""
        response = client.get("/api/servers")
        
        data = response.json()
        server = data[0]
        assert "id" in server
        assert "name" in server
        assert "host" in server
        assert "port" in server
        assert server["id"] == "test1"
        assert server["name"] == "Test Server 1"
    
    def test_get_servers_empty_list(self, client):
        """Test GET /api/servers with no servers."""
        mock_poller = Mock()
        mock_poller.servers = []
        app.state.poller = mock_poller
        
        response = client.get("/api/servers")
        
        assert response.status_code == 200
        assert response.json() == []
        
        delattr(app.state, "poller")


class TestGetServerStatus:
    """Tests for GET /api/servers/{server_id}/status endpoint."""
    
    def test_get_server_status_success(self, client, setup_app_with_mock_poller, mock_poller, test_servers):
        """Test successful server status retrieval."""
        channels = [Channel(id="1", name="Channel 1", status="running")]
        status = ServerStatus(id="test1", cpu=45.5, channels=channels)
        mock_poller.get_status.return_value = status
        
        response = client.get("/api/servers/test1/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test1"
        assert data["cpu"] == 45.5
        assert len(data["channels"]) == 1
        assert data["channels"][0]["id"] == "1"
    
    def test_get_server_status_not_found_server(self, client, setup_app_with_mock_poller, mock_poller):
        """Test status request for non-existent server."""
        response = client.get("/api/servers/nonexistent/status")
        
        assert response.status_code == 404
        assert "server not found" in response.json()["detail"]
    
    def test_get_server_status_no_status_available(self, client, setup_app_with_mock_poller, mock_poller):
        """Test status request when status is not yet available."""
        mock_poller.get_status.return_value = None
        
        response = client.get("/api/servers/test1/status")
        
        assert response.status_code == 404
        assert "status not found" in response.json()["detail"]
    
    def test_get_server_status_with_empty_channels(self, client, setup_app_with_mock_poller, mock_poller):
        """Test status with empty channels list."""
        status = ServerStatus(id="test1", cpu=0.0, channels=[])
        mock_poller.get_status.return_value = status
        
        response = client.get("/api/servers/test1/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["channels"] == []
    
    def test_get_server_status_with_multiple_channels(self, client, setup_app_with_mock_poller, mock_poller):
        """Test status with multiple channels."""
        channels = [
            Channel(id="1", name="Channel 1", status="running"),
            Channel(id="2", name="Channel 2", status="stopped"),
            Channel(id="3", name="Channel 3", status="error")
        ]
        status = ServerStatus(id="test1", cpu=60.0, channels=channels)
        mock_poller.get_status.return_value = status
        
        response = client.get("/api/servers/test1/status")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["channels"]) == 3


class TestRestartChannel:
    """Tests for POST /api/servers/{server_id}/channels/{channel_id}/restart endpoint."""
    
    def test_restart_channel_success(self, client, setup_app_with_mock_poller, mock_poller):
        """Test successful channel restart."""
        restart_result = {
            "server_id": "test1",
            "channel_id": "1",
            "stop": {"ok": True, "msg": "Stopped"},
            "start": {"ok": True, "msg": "Started"}
        }
        
        with patch("app.api.servers.restart_channel") as mock_restart:
            mock_restart.return_value = restart_result
            
            response = client.post("/api/servers/test1/channels/1/restart")
            
            assert response.status_code == 200
            data = response.json()
            assert data["server_id"] == "test1"
            assert data["channel_id"] == "1"
            assert data["stop"]["ok"] is True
            assert data["start"]["ok"] is True
    
    def test_restart_channel_server_not_found(self, client, setup_app_with_mock_poller, mock_poller):
        """Test restart for non-existent server."""
        response = client.post("/api/servers/nonexistent/channels/1/restart")
        
        assert response.status_code == 404
        assert "server not found" in response.json()["detail"]
    
    def test_restart_channel_invalid_channel_id_format(self, client, setup_app_with_mock_poller, mock_poller):
        """Test restart with invalid channel_id format."""
        # Invalid: starts with special character
        response = client.post("/api/servers/test1/channels/-invalid/restart")
        assert response.status_code == 400
        assert "Invalid channel_id format" in response.json()["detail"]
        
        # Invalid: contains spaces
        response = client.post("/api/servers/test1/channels/invalid%20id/restart")
        assert response.status_code == 400
    
    def test_restart_channel_valid_channel_id_formats(self, client, setup_app_with_mock_poller, mock_poller):
        """Test restart with various valid channel_id formats."""
        valid_ids = ["1", "ch1", "channel_1", "CH-1", "abc123"]
        
        restart_result = {
            "server_id": "test1",
            "channel_id": "test",
            "stop": {"ok": True, "msg": "OK"},
            "start": {"ok": True, "msg": "OK"}
        }
        
        with patch("app.api.servers.restart_channel") as mock_restart:
            mock_restart.return_value = restart_result
            
            for channel_id in valid_ids:
                response = client.post(f"/api/servers/test1/channels/{channel_id}/restart")
                assert response.status_code == 200, f"Failed for channel_id: {channel_id}"
    
    def test_restart_channel_with_authentication_disabled(self, client, setup_app_with_mock_poller, mock_poller):
        """Test restart without API key when authentication is disabled."""
        restart_result = {
            "server_id": "test1",
            "channel_id": "1",
            "stop": {"ok": True, "msg": "OK"},
            "start": {"ok": True, "msg": "OK"}
        }
        
        with patch("app.api.servers.restart_channel") as mock_restart:
            with patch("app.security.settings") as mock_settings:
                mock_settings.API_KEY_ENABLED = False
                mock_restart.return_value = restart_result
                
                response = client.post("/api/servers/test1/channels/1/restart")
                assert response.status_code == 200
    
    def test_restart_channel_with_authentication_enabled_no_key(self, client, setup_app_with_mock_poller, mock_poller):
        """Test restart without API key when authentication is enabled."""
        with patch("app.security.settings") as mock_settings:
            mock_settings.API_KEY_ENABLED = True
            mock_settings.API_KEY = "secret"
            
            response = client.post("/api/servers/test1/channels/1/restart")
            assert response.status_code == 401
            assert "Missing API Key" in response.json()["detail"]
    
    def test_restart_channel_with_authentication_enabled_valid_key(self, client, setup_app_with_mock_poller, mock_poller):
        """Test restart with valid API key when authentication is enabled."""
        restart_result = {
            "server_id": "test1",
            "channel_id": "1",
            "stop": {"ok": True, "msg": "OK"},
            "start": {"ok": True, "msg": "OK"}
        }
        
        with patch("app.api.servers.restart_channel") as mock_restart:
            with patch("app.security.settings") as mock_settings:
                mock_settings.API_KEY_ENABLED = True
                mock_settings.API_KEY = "valid_key"
                mock_restart.return_value = restart_result
                
                response = client.post(
                    "/api/servers/test1/channels/1/restart",
                    headers={"X-API-Key": "valid_key"}
                )
                assert response.status_code == 200


class TestReloadServers:
    """Tests for POST /api/servers/reload endpoint."""
    
    def test_reload_servers_success(self, client, setup_app_with_mock_poller, mock_poller, tmp_path):
        """Test successful server configuration reload."""
        # Create temporary config file
        config_file = tmp_path / "servers.json"
        servers_data = [
            {"id": "srv1", "name": "Server 1", "host": "localhost", "port": 8888}
        ]
        config_file.write_text(json.dumps(servers_data))
        
        with patch("app.api.servers.settings") as mock_settings:
            with patch("app.security.settings") as mock_sec_settings:
                mock_settings.SERVERS_CONFIG_PATH = str(config_file)
                mock_sec_settings.API_KEY_ENABLED = False
                
                response = client.post("/api/servers/reload")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "Reloaded 1 servers" in data["message"]
                assert len(data["servers"]) == 1
                mock_poller.reload_servers.assert_called_once()
    
    def test_reload_servers_empty_config(self, client, setup_app_with_mock_poller, mock_poller, tmp_path):
        """Test reload with empty configuration file."""
        config_file = tmp_path / "servers.json"
        config_file.write_text("[]")
        
        with patch("app.api.servers.settings") as mock_settings:
            with patch("app.security.settings") as mock_sec_settings:
                mock_settings.SERVERS_CONFIG_PATH = str(config_file)
                mock_sec_settings.API_KEY_ENABLED = False
                
                response = client.post("/api/servers/reload")
                
                assert response.status_code == 500
                assert "Failed to load servers" in response.json()["detail"]
    
    def test_reload_servers_invalid_json(self, client, setup_app_with_mock_poller, mock_poller, tmp_path):
        """Test reload with invalid JSON in configuration file."""
        config_file = tmp_path / "servers.json"
        config_file.write_text("invalid json")
        
        with patch("app.api.servers.settings") as mock_settings:
            with patch("app.security.settings") as mock_sec_settings:
                mock_settings.SERVERS_CONFIG_PATH = str(config_file)
                mock_sec_settings.API_KEY_ENABLED = False
                
                response = client.post("/api/servers/reload")
                
                assert response.status_code == 500
    
    def test_reload_servers_with_authentication_disabled(self, client, setup_app_with_mock_poller, mock_poller, tmp_path):
        """Test reload without API key when authentication is disabled."""
        config_file = tmp_path / "servers.json"
        config_file.write_text('[{"id":"s1","host":"localhost","port":8888}]')
        
        with patch("app.api.servers.settings") as mock_settings:
            with patch("app.security.settings") as mock_sec_settings:
                mock_settings.SERVERS_CONFIG_PATH = str(config_file)
                mock_sec_settings.API_KEY_ENABLED = False
                
                response = client.post("/api/servers/reload")
                assert response.status_code == 200
    
    def test_reload_servers_with_authentication_enabled_no_key(self, client, setup_app_with_mock_poller, mock_poller):
        """Test reload without API key when authentication is enabled."""
        with patch("app.security.settings") as mock_settings:
            mock_settings.API_KEY_ENABLED = True
            mock_settings.API_KEY = "secret"
            
            response = client.post("/api/servers/reload")
            assert response.status_code == 401
            assert "Missing API Key" in response.json()["detail"]
    
    def test_reload_servers_with_authentication_enabled_valid_key(self, client, setup_app_with_mock_poller, mock_poller, tmp_path):
        """Test reload with valid API key when authentication is enabled."""
        config_file = tmp_path / "servers.json"
        config_file.write_text('[{"id":"s1","host":"localhost","port":8888}]')
        
        with patch("app.api.servers.settings") as mock_settings:
            with patch("app.security.settings") as mock_sec_settings:
                mock_settings.SERVERS_CONFIG_PATH = str(config_file)
                mock_sec_settings.API_KEY_ENABLED = True
                mock_sec_settings.API_KEY = "valid_key"
                
                response = client.post(
                    "/api/servers/reload",
                    headers={"X-API-Key": "valid_key"}
                )
                assert response.status_code == 200
    
    def test_reload_servers_no_poller(self, client, tmp_path):
        """Test reload when poller is not available."""
        # Remove poller from app state
        if hasattr(app.state, "poller"):
            delattr(app.state, "poller")
        
        config_file = tmp_path / "servers.json"
        config_file.write_text('[{"id":"s1","host":"localhost","port":8888}]')
        
        with patch("app.api.servers.settings") as mock_settings:
            with patch("app.security.settings") as mock_sec_settings:
                mock_settings.SERVERS_CONFIG_PATH = str(config_file)
                mock_sec_settings.API_KEY_ENABLED = False
                
                # Manually set poller to None
                app.state.poller = None
                
                response = client.post("/api/servers/reload")
                assert response.status_code == 500
                assert "Poller not available" in response.json()["detail"]


class TestRootEndpoint:
    """Tests for root / endpoint."""
    
    def test_root_returns_html(self, client):
        """Test that root endpoint returns HTML page."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
