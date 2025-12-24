"""
Unit tests for data models.

Tests the Pydantic models for Server, Channel, and ServerStatus,
including field validation, default values, and serialization.
"""
import pytest
from pydantic import ValidationError

from app.models import Channel, Server, ServerStatus


class TestChannel:
    """Tests for the Channel model."""
    
    def test_channel_with_all_fields(self):
        """Test creating a Channel with all fields."""
        channel = Channel(id="1", name="Test Channel", status="running")
        assert channel.id == "1"
        assert channel.name == "Test Channel"
        assert channel.status == "running"
    
    def test_channel_with_minimal_fields(self):
        """Test creating a Channel with only required fields."""
        channel = Channel(id="1")
        assert channel.id == "1"
        assert channel.name is None
        assert channel.status is None
    
    def test_channel_dict_serialization(self):
        """Test Channel serialization to dict."""
        channel = Channel(id="1", name="Test", status="running")
        data = channel.dict()
        assert data == {
            "id": "1",
            "name": "Test",
            "status": "running"
        }
    
    def test_channel_requires_id(self):
        """Test that Channel requires an id field."""
        with pytest.raises(ValidationError) as exc_info:
            Channel()
        assert "id" in str(exc_info.value)


class TestServer:
    """Tests for the Server model."""
    
    def test_server_with_all_fields(self):
        """Test creating a Server with all fields."""
        server = Server(
            id="srv1",
            name="Test Server",
            host="localhost",
            port=8888,
            channels=["1", "2", "3"]
        )
        assert server.id == "srv1"
        assert server.name == "Test Server"
        assert server.host == "localhost"
        assert server.port == 8888
        assert server.channels == ["1", "2", "3"]
    
    def test_server_with_minimal_fields(self):
        """Test creating a Server with only required fields."""
        server = Server(id="srv1", host="localhost")
        assert server.id == "srv1"
        assert server.host == "localhost"
        assert server.name is None
        assert server.port is None
        assert server.channels == []
    
    def test_server_default_channels_empty_list(self):
        """Test that channels default to empty list."""
        server = Server(id="srv1", host="localhost")
        assert server.channels == []
        assert isinstance(server.channels, list)
    
    def test_server_dict_serialization(self):
        """Test Server serialization to dict."""
        server = Server(id="srv1", host="localhost", port=8888)
        data = server.dict()
        assert data == {
            "id": "srv1",
            "name": None,
            "host": "localhost",
            "port": 8888,
            "channels": []
        }
    
    def test_server_requires_id(self):
        """Test that Server requires an id field."""
        with pytest.raises(ValidationError) as exc_info:
            Server(host="localhost")
        assert "id" in str(exc_info.value)
    
    def test_server_requires_host(self):
        """Test that Server requires a host field."""
        with pytest.raises(ValidationError) as exc_info:
            Server(id="srv1")
        assert "host" in str(exc_info.value)
    
    def test_server_port_validation(self):
        """Test Server port field accepts integers."""
        server = Server(id="srv1", host="localhost", port=9999)
        assert server.port == 9999
        assert isinstance(server.port, int)


class TestServerStatus:
    """Tests for the ServerStatus model."""
    
    def test_server_status_with_all_fields(self):
        """Test creating a ServerStatus with all fields."""
        channels = [
            Channel(id="1", name="Channel 1", status="running"),
            Channel(id="2", name="Channel 2", status="stopped")
        ]
        status = ServerStatus(id="srv1", cpu=45.5, channels=channels)
        assert status.id == "srv1"
        assert status.cpu == 45.5
        assert len(status.channels) == 2
        assert status.channels[0].id == "1"
        assert status.channels[1].id == "2"
    
    def test_server_status_with_minimal_fields(self):
        """Test creating a ServerStatus with only required fields."""
        status = ServerStatus(id="srv1")
        assert status.id == "srv1"
        assert status.cpu is None
        assert status.channels == []
    
    def test_server_status_default_values(self):
        """Test ServerStatus default values."""
        status = ServerStatus(id="srv1")
        assert status.cpu is None
        assert status.channels == []
        assert isinstance(status.channels, list)
    
    def test_server_status_cpu_float(self):
        """Test that CPU can be a float value."""
        status = ServerStatus(id="srv1", cpu=35.7)
        assert status.cpu == 35.7
        assert isinstance(status.cpu, float)
    
    def test_server_status_cpu_int_converted_to_float(self):
        """Test that CPU integer is accepted."""
        status = ServerStatus(id="srv1", cpu=50)
        assert status.cpu == 50
    
    def test_server_status_dict_serialization(self):
        """Test ServerStatus serialization to dict."""
        channels = [Channel(id="1", status="running")]
        status = ServerStatus(id="srv1", cpu=30.0, channels=channels)
        data = status.dict()
        assert data["id"] == "srv1"
        assert data["cpu"] == 30.0
        assert len(data["channels"]) == 1
        assert data["channels"][0]["id"] == "1"
    
    def test_server_status_requires_id(self):
        """Test that ServerStatus requires an id field."""
        with pytest.raises(ValidationError) as exc_info:
            ServerStatus()
        assert "id" in str(exc_info.value)
    
    def test_server_status_empty_channels_list(self):
        """Test ServerStatus with empty channels list."""
        status = ServerStatus(id="srv1", cpu=0.0, channels=[])
        assert status.channels == []
        assert len(status.channels) == 0
