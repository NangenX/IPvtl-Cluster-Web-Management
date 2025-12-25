"""
Unit tests for logging configuration module.

Tests logging setup, log level configuration, and logger creation.
"""
import logging
import pytest
from unittest.mock import patch, MagicMock

from app.logging_config import setup_logging, get_logger


class TestSetupLogging:
    """Tests for the setup_logging function."""
    
    def test_setup_logging_default_level(self):
        """Test that setup_logging configures logging with default INFO level."""
        with patch("app.logging_config.settings") as mock_settings:
            mock_settings.LOG_LEVEL = "info"
            setup_logging()
            
            root_logger = logging.getLogger()
            assert root_logger.level == logging.INFO
    
    def test_setup_logging_debug_level(self):
        """Test that setup_logging configures DEBUG log level."""
        with patch("app.logging_config.settings") as mock_settings:
            mock_settings.LOG_LEVEL = "debug"
            setup_logging()
            
            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG
    
    def test_setup_logging_warning_level(self):
        """Test that setup_logging configures WARNING log level."""
        with patch("app.logging_config.settings") as mock_settings:
            mock_settings.LOG_LEVEL = "warning"
            setup_logging()
            
            root_logger = logging.getLogger()
            assert root_logger.level == logging.WARNING
    
    def test_setup_logging_error_level(self):
        """Test that setup_logging configures ERROR log level."""
        with patch("app.logging_config.settings") as mock_settings:
            mock_settings.LOG_LEVEL = "error"
            setup_logging()
            
            root_logger = logging.getLogger()
            assert root_logger.level == logging.ERROR
    
    def test_setup_logging_critical_level(self):
        """Test that setup_logging configures CRITICAL log level."""
        with patch("app.logging_config.settings") as mock_settings:
            mock_settings.LOG_LEVEL = "critical"
            setup_logging()
            
            root_logger = logging.getLogger()
            assert root_logger.level == logging.CRITICAL
    
    def test_setup_logging_case_insensitive(self):
        """Test that log level is case-insensitive."""
        test_cases = [
            ("INFO", logging.INFO),
            ("Info", logging.INFO),
            ("DEBUG", logging.DEBUG),
            ("Debug", logging.DEBUG),
        ]
        
        for level_str, expected_level in test_cases:
            with patch("app.logging_config.settings") as mock_settings:
                mock_settings.LOG_LEVEL = level_str
                setup_logging()
                
                root_logger = logging.getLogger()
                assert root_logger.level == expected_level
    
    def test_setup_logging_invalid_level_defaults_to_info(self):
        """Test that invalid log level defaults to INFO."""
        with patch("app.logging_config.settings") as mock_settings:
            mock_settings.LOG_LEVEL = "invalid_level"
            setup_logging()
            
            root_logger = logging.getLogger()
            assert root_logger.level == logging.INFO
    
    def test_setup_logging_httpx_logger_set_to_warning(self):
        """Test that httpx logger is set to WARNING to reduce noise."""
        with patch("app.logging_config.settings") as mock_settings:
            mock_settings.LOG_LEVEL = "debug"
            setup_logging()
            
            httpx_logger = logging.getLogger("httpx")
            assert httpx_logger.level == logging.WARNING
    
    def test_setup_logging_configures_handler(self):
        """Test that setup_logging configures at least one handler."""
        with patch("app.logging_config.settings") as mock_settings:
            mock_settings.LOG_LEVEL = "info"
            setup_logging()
            
            root_logger = logging.getLogger()
            assert len(root_logger.handlers) > 0
    
    def test_setup_logging_log_format(self):
        """Test that logging format includes expected components."""
        with patch("app.logging_config.settings") as mock_settings:
            mock_settings.LOG_LEVEL = "info"
            setup_logging()
            
            root_logger = logging.getLogger()
            # Check that handler exists and has a formatter
            if root_logger.handlers:
                handler = root_logger.handlers[0]
                formatter = handler.formatter
                assert formatter is not None
                # Format should include these components
                format_str = formatter._fmt
                assert "%(asctime)s" in format_str
                assert "%(name)s" in format_str
                assert "%(levelname)s" in format_str
                assert "%(message)s" in format_str


class TestGetLogger:
    """Tests for the get_logger function."""
    
    def test_get_logger_returns_logger_instance(self):
        """Test that get_logger returns a logging.Logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
    
    def test_get_logger_with_module_name(self):
        """Test that get_logger creates logger with correct name."""
        logger = get_logger("app.services.poller")
        assert logger.name == "app.services.poller"
    
    def test_get_logger_different_names_return_different_loggers(self):
        """Test that different names return different logger instances."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        assert logger1 is not logger2
        assert logger1.name != logger2.name
    
    def test_get_logger_same_name_returns_same_logger(self):
        """Test that same name returns the same logger instance."""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")
        assert logger1 is logger2
    
    def test_get_logger_can_log_messages(self):
        """Test that logger returned by get_logger can log messages."""
        logger = get_logger("test")
        # Should not raise any exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
    
    def test_get_logger_empty_name(self):
        """Test get_logger with empty string name."""
        logger = get_logger("")
        assert isinstance(logger, logging.Logger)
    
    def test_get_logger_with_special_characters(self):
        """Test get_logger with special characters in name."""
        logger = get_logger("app.module-name_123")
        assert logger.name == "app.module-name_123"
    
    def test_get_logger_inherits_root_configuration(self):
        """Test that logger inherits root logger configuration."""
        with patch("app.logging_config.settings") as mock_settings:
            mock_settings.LOG_LEVEL = "debug"
            setup_logging()
            
            logger = get_logger("test_module")
            # Should inherit DEBUG level from root
            root_logger = logging.getLogger()
            assert root_logger.level == logging.DEBUG
