"""
Unit tests for custom exception classes.

Tests the custom exception hierarchy and error message formatting.
"""
import pytest

from app.exceptions import (
    IPvtlException,
    ServerNotFoundException,
    ChannelOperationException
)


class TestIPvtlException:
    """Tests for the base IPvtlException class."""
    
    def test_exception_creation_with_message(self):
        """Test creating an IPvtlException with a message."""
        exc = IPvtlException("Test error message")
        assert exc.message == "Test error message"
        assert str(exc) == "Test error message"
    
    def test_exception_inheritance(self):
        """Test that IPvtlException inherits from Exception."""
        exc = IPvtlException("Test")
        assert isinstance(exc, Exception)
        assert isinstance(exc, IPvtlException)
    
    def test_exception_can_be_raised(self):
        """Test that IPvtlException can be raised and caught."""
        with pytest.raises(IPvtlException) as exc_info:
            raise IPvtlException("Test error")
        assert exc_info.value.message == "Test error"
    
    def test_exception_message_attribute(self):
        """Test that exception has message attribute."""
        exc = IPvtlException("Custom message")
        assert hasattr(exc, "message")
        assert exc.message == "Custom message"


class TestServerNotFoundException:
    """Tests for the ServerNotFoundException class."""
    
    def test_exception_creation_with_server_id(self):
        """Test creating a ServerNotFoundException with server_id."""
        exc = ServerNotFoundException("server123")
        assert exc.server_id == "server123"
        assert "Server not found: server123" in str(exc)
    
    def test_exception_inheritance(self):
        """Test that ServerNotFoundException inherits from IPvtlException."""
        exc = ServerNotFoundException("server123")
        assert isinstance(exc, IPvtlException)
        assert isinstance(exc, Exception)
    
    def test_exception_message_format(self):
        """Test that the error message follows the expected format."""
        exc = ServerNotFoundException("test_server")
        expected_message = "Server not found: test_server"
        assert exc.message == expected_message
        assert str(exc) == expected_message
    
    def test_exception_can_be_raised(self):
        """Test that ServerNotFoundException can be raised and caught."""
        with pytest.raises(ServerNotFoundException) as exc_info:
            raise ServerNotFoundException("missing_server")
        assert exc_info.value.server_id == "missing_server"
        assert "missing_server" in str(exc_info.value)
    
    def test_exception_server_id_attribute(self):
        """Test that exception has server_id attribute."""
        exc = ServerNotFoundException("srv1")
        assert hasattr(exc, "server_id")
        assert exc.server_id == "srv1"
    
    def test_exception_with_different_server_ids(self):
        """Test exception with various server ID formats."""
        test_ids = ["server1", "srv-123", "test_server", "SERVER_ABC"]
        for server_id in test_ids:
            exc = ServerNotFoundException(server_id)
            assert exc.server_id == server_id
            assert server_id in str(exc)


class TestChannelOperationException:
    """Tests for the ChannelOperationException class."""
    
    def test_exception_creation_with_all_parameters(self):
        """Test creating a ChannelOperationException with all parameters."""
        exc = ChannelOperationException(
            server_id="srv1",
            channel_id="ch1",
            operation="restart",
            reason="Timeout"
        )
        assert exc.server_id == "srv1"
        assert exc.channel_id == "ch1"
        assert exc.operation == "restart"
        assert exc.reason == "Timeout"
    
    def test_exception_inheritance(self):
        """Test that ChannelOperationException inherits from IPvtlException."""
        exc = ChannelOperationException("srv1", "ch1", "stop", "Error")
        assert isinstance(exc, IPvtlException)
        assert isinstance(exc, Exception)
    
    def test_exception_message_format(self):
        """Test that the error message follows the expected format."""
        exc = ChannelOperationException(
            server_id="server1",
            channel_id="channel2",
            operation="start",
            reason="Connection refused"
        )
        expected = (
            "Channel operation 'start' failed for channel channel2 "
            "on server server1: Connection refused"
        )
        assert exc.message == expected
        assert str(exc) == expected
    
    def test_exception_can_be_raised(self):
        """Test that ChannelOperationException can be raised and caught."""
        with pytest.raises(ChannelOperationException) as exc_info:
            raise ChannelOperationException(
                "srv1", "ch1", "restart", "Test reason"
            )
        assert exc_info.value.server_id == "srv1"
        assert exc_info.value.channel_id == "ch1"
        assert exc_info.value.operation == "restart"
        assert exc_info.value.reason == "Test reason"
    
    def test_exception_attributes(self):
        """Test that exception has all expected attributes."""
        exc = ChannelOperationException("srv1", "ch1", "stop", "Error")
        assert hasattr(exc, "server_id")
        assert hasattr(exc, "channel_id")
        assert hasattr(exc, "operation")
        assert hasattr(exc, "reason")
    
    def test_exception_with_stop_operation(self):
        """Test exception for stop operation."""
        exc = ChannelOperationException(
            "srv1", "ch1", "stop", "HTTP 500"
        )
        assert "stop" in str(exc)
        assert exc.operation == "stop"
    
    def test_exception_with_start_operation(self):
        """Test exception for start operation."""
        exc = ChannelOperationException(
            "srv1", "ch1", "start", "Timeout"
        )
        assert "start" in str(exc)
        assert exc.operation == "start"
    
    def test_exception_with_restart_operation(self):
        """Test exception for restart operation."""
        exc = ChannelOperationException(
            "srv1", "ch1", "restart", "Failed"
        )
        assert "restart" in str(exc)
        assert exc.operation == "restart"
    
    def test_exception_message_contains_all_info(self):
        """Test that message contains all relevant information."""
        exc = ChannelOperationException(
            "test_server", "test_channel", "test_op", "test_reason"
        )
        message = str(exc)
        assert "test_server" in message
        assert "test_channel" in message
        assert "test_op" in message
        assert "test_reason" in message
