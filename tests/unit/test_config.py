"""
Unit tests for configuration module.

Tests configuration loading, default values, and environment variable overrides.
"""
import os
import pytest

from app.config import Settings, get_settings


class TestSettings:
    """Tests for the Settings configuration class."""
    
    def test_default_values(self):
        """Test that default configuration values are correctly set."""
        settings = Settings()
        assert settings.POLL_INTERVAL == 10
        assert settings.MAX_SERVERS == 100
        assert settings.POLL_CONCURRENCY == 10
        assert settings.HTTPX_TIMEOUT_SECONDS == 5
        assert settings.RESTART_STOP_TIMEOUT_SECONDS == 10
        assert settings.RESTART_START_TIMEOUT_SECONDS == 10
        assert settings.RESTART_DELAY_SECONDS == 0.5
        assert settings.SERVERS_CONFIG_PATH == "servers/servers.json"
        assert settings.LOG_LEVEL == "info"
        assert settings.API_KEY_ENABLED is False
        assert settings.API_KEY == ""
    
    def test_environment_variable_override_poll_interval(self, monkeypatch):
        """Test that POLL_INTERVAL can be overridden by environment variable."""
        monkeypatch.setenv("POLL_INTERVAL", "30")
        settings = Settings()
        assert settings.POLL_INTERVAL == 30
    
    def test_environment_variable_override_max_servers(self, monkeypatch):
        """Test that MAX_SERVERS can be overridden by environment variable."""
        monkeypatch.setenv("MAX_SERVERS", "50")
        settings = Settings()
        assert settings.MAX_SERVERS == 50
    
    def test_environment_variable_override_poll_concurrency(self, monkeypatch):
        """Test that POLL_CONCURRENCY can be overridden by environment variable."""
        monkeypatch.setenv("POLL_CONCURRENCY", "20")
        settings = Settings()
        assert settings.POLL_CONCURRENCY == 20
    
    def test_environment_variable_override_log_level(self, monkeypatch):
        """Test that LOG_LEVEL can be overridden by environment variable."""
        monkeypatch.setenv("LOG_LEVEL", "debug")
        settings = Settings()
        assert settings.LOG_LEVEL == "debug"
    
    def test_environment_variable_override_api_key_enabled(self, monkeypatch):
        """Test that API_KEY_ENABLED can be overridden by environment variable."""
        monkeypatch.setenv("API_KEY_ENABLED", "true")
        settings = Settings()
        assert settings.API_KEY_ENABLED is True
    
    def test_environment_variable_override_api_key(self, monkeypatch):
        """Test that API_KEY can be overridden by environment variable."""
        monkeypatch.setenv("API_KEY", "secret-key-123")
        settings = Settings()
        assert settings.API_KEY == "secret-key-123"
    
    def test_environment_variable_override_servers_config_path(self, monkeypatch):
        """Test that SERVERS_CONFIG_PATH can be overridden by environment variable."""
        monkeypatch.setenv("SERVERS_CONFIG_PATH", "config/servers.json")
        settings = Settings()
        assert settings.SERVERS_CONFIG_PATH == "config/servers.json"
    
    def test_environment_variable_override_timeout(self, monkeypatch):
        """Test that timeout settings can be overridden by environment variables."""
        monkeypatch.setenv("HTTPX_TIMEOUT_SECONDS", "15")
        monkeypatch.setenv("RESTART_STOP_TIMEOUT_SECONDS", "20")
        monkeypatch.setenv("RESTART_START_TIMEOUT_SECONDS", "25")
        settings = Settings()
        assert settings.HTTPX_TIMEOUT_SECONDS == 15
        assert settings.RESTART_STOP_TIMEOUT_SECONDS == 20
        assert settings.RESTART_START_TIMEOUT_SECONDS == 25
    
    def test_environment_variable_override_restart_delay(self, monkeypatch):
        """Test that RESTART_DELAY_SECONDS can be overridden by environment variable."""
        monkeypatch.setenv("RESTART_DELAY_SECONDS", "2.0")
        settings = Settings()
        assert settings.RESTART_DELAY_SECONDS == 2.0
    
    def test_get_settings_returns_settings_instance(self):
        """Test that get_settings returns a Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)
    
    def test_multiple_settings_instances_independent(self, monkeypatch):
        """Test that multiple Settings instances can have different values."""
        # First instance with default
        settings1 = Settings()
        default_interval = settings1.POLL_INTERVAL
        
        # Set environment variable
        monkeypatch.setenv("POLL_INTERVAL", "60")
        
        # Second instance with overridden value
        settings2 = Settings()
        assert settings2.POLL_INTERVAL == 60
        assert settings1.POLL_INTERVAL == default_interval
    
    def test_boolean_environment_variable_parsing(self, monkeypatch):
        """Test that boolean environment variables are parsed correctly."""
        # Test various true values
        for true_value in ["true", "True", "TRUE", "1", "yes"]:
            monkeypatch.setenv("API_KEY_ENABLED", true_value)
            settings = Settings()
            assert settings.API_KEY_ENABLED is True
        
        # Test false values
        for false_value in ["false", "False", "FALSE", "0", "no"]:
            monkeypatch.setenv("API_KEY_ENABLED", false_value)
            settings = Settings()
            assert settings.API_KEY_ENABLED is False
    
    def test_integer_validation(self, monkeypatch):
        """Test that integer fields validate input."""
        monkeypatch.setenv("POLL_INTERVAL", "not_a_number")
        with pytest.raises(Exception):  # Pydantic will raise ValidationError
            Settings()
    
    def test_float_validation(self, monkeypatch):
        """Test that float fields validate input."""
        monkeypatch.setenv("RESTART_DELAY_SECONDS", "not_a_number")
        with pytest.raises(Exception):  # Pydantic will raise ValidationError
            Settings()
