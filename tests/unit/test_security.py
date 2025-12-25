"""
Unit tests for security and authentication module.

Tests API Key authentication mechanism including enabled/disabled states,
valid/invalid keys, and missing keys.
"""
import pytest
from unittest.mock import patch
from fastapi import HTTPException

from app.security import verify_api_key


class TestVerifyApiKey:
    """Tests for the verify_api_key function."""
    
    @pytest.mark.asyncio
    async def test_api_key_disabled_allows_request(self):
        """Test that requests are allowed when API_KEY_ENABLED is False."""
        with patch("app.security.settings") as mock_settings:
            mock_settings.API_KEY_ENABLED = False
            mock_settings.API_KEY = "secret"
            
            # Should return True regardless of api_key value
            result = await verify_api_key(api_key=None)
            assert result is True
            
            result = await verify_api_key(api_key="wrong_key")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_api_key_enabled_missing_key_raises_401(self):
        """Test that missing API key raises 401 when authentication is enabled."""
        with patch("app.security.settings") as mock_settings:
            mock_settings.API_KEY_ENABLED = True
            mock_settings.API_KEY = "correct_key"
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(api_key=None)
            
            assert exc_info.value.status_code == 401
            assert "Missing API Key" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_api_key_enabled_empty_key_raises_401(self):
        """Test that empty API key raises 401 when authentication is enabled."""
        with patch("app.security.settings") as mock_settings:
            mock_settings.API_KEY_ENABLED = True
            mock_settings.API_KEY = "correct_key"
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(api_key="")
            
            assert exc_info.value.status_code == 401
            assert "Missing API Key" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_api_key_enabled_invalid_key_raises_401(self):
        """Test that invalid API key raises 401 when authentication is enabled."""
        with patch("app.security.settings") as mock_settings:
            mock_settings.API_KEY_ENABLED = True
            mock_settings.API_KEY = "correct_key"
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(api_key="wrong_key")
            
            assert exc_info.value.status_code == 401
            assert "Invalid API Key" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_api_key_enabled_valid_key_returns_true(self):
        """Test that valid API key returns True when authentication is enabled."""
        with patch("app.security.settings") as mock_settings:
            mock_settings.API_KEY_ENABLED = True
            mock_settings.API_KEY = "correct_key"
            
            result = await verify_api_key(api_key="correct_key")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_api_key_case_sensitive(self):
        """Test that API key comparison is case-sensitive."""
        with patch("app.security.settings") as mock_settings:
            mock_settings.API_KEY_ENABLED = True
            mock_settings.API_KEY = "SecretKey123"
            
            # Correct case should work
            result = await verify_api_key(api_key="SecretKey123")
            assert result is True
            
            # Different case should fail
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(api_key="secretkey123")
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_api_key_whitespace_not_stripped(self):
        """Test that whitespace in API key is significant."""
        with patch("app.security.settings") as mock_settings:
            mock_settings.API_KEY_ENABLED = True
            mock_settings.API_KEY = "key123"
            
            # Key with trailing space should fail
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(api_key="key123 ")
            assert exc_info.value.status_code == 401
            
            # Key with leading space should fail
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(api_key=" key123")
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_api_key_special_characters(self):
        """Test API key with special characters."""
        special_key = "key!@#$%^&*()_+-=[]{}|;':,.<>?/"
        with patch("app.security.settings") as mock_settings:
            mock_settings.API_KEY_ENABLED = True
            mock_settings.API_KEY = special_key
            
            result = await verify_api_key(api_key=special_key)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_api_key_long_key(self):
        """Test API key with long string."""
        long_key = "a" * 1000
        with patch("app.security.settings") as mock_settings:
            mock_settings.API_KEY_ENABLED = True
            mock_settings.API_KEY = long_key
            
            result = await verify_api_key(api_key=long_key)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_api_key_empty_configured_key(self):
        """Test behavior when configured API_KEY is empty."""
        with patch("app.security.settings") as mock_settings:
            mock_settings.API_KEY_ENABLED = True
            mock_settings.API_KEY = ""
            
            # Empty key should be treated as invalid
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(api_key=None)
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_multiple_requests_with_same_key(self):
        """Test that the same valid key works for multiple requests."""
        with patch("app.security.settings") as mock_settings:
            mock_settings.API_KEY_ENABLED = True
            mock_settings.API_KEY = "test_key"
            
            # Multiple calls with same key should all succeed
            for _ in range(5):
                result = await verify_api_key(api_key="test_key")
                assert result is True
    
    @pytest.mark.asyncio
    async def test_switching_authentication_state(self):
        """Test switching between enabled and disabled authentication."""
        with patch("app.security.settings") as mock_settings:
            mock_settings.API_KEY = "secret"
            
            # Disabled state
            mock_settings.API_KEY_ENABLED = False
            result = await verify_api_key(api_key=None)
            assert result is True
            
            # Enabled state
            mock_settings.API_KEY_ENABLED = True
            with pytest.raises(HTTPException):
                await verify_api_key(api_key=None)
