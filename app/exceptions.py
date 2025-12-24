"""
Custom exception classes for the application.

These exceptions provide more specific error handling and better debugging
information throughout the application.
"""


class IPvtlException(Exception):
    """Base exception class for all IPvtl-related errors."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ServerNotFoundException(IPvtlException):
    """Raised when a requested server is not found in configuration."""
    
    def __init__(self, server_id: str):
        self.server_id = server_id
        super().__init__(f"Server not found: {server_id}")


class ChannelOperationException(IPvtlException):
    """Raised when a channel operation (start/stop/restart) fails."""
    
    def __init__(self, server_id: str, channel_id: str, operation: str, reason: str):
        self.server_id = server_id
        self.channel_id = channel_id
        self.operation = operation
        self.reason = reason
        super().__init__(
            f"Channel operation '{operation}' failed for channel {channel_id} "
            f"on server {server_id}: {reason}"
        )
