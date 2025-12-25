"""
Pytest configuration and shared fixtures.

This module provides shared test fixtures and configuration for all tests.
"""
import asyncio
import json
import os
from typing import List
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from app.models import Server


@pytest.fixture
def test_servers() -> List[Server]:
    """Provide a list of test servers."""
    return [
        Server(id="test1", name="Test Server 1", host="localhost", port=8888),
        Server(id="test2", name="Test Server 2", host="127.0.0.1", port=8889),
    ]


@pytest.fixture
def mock_servers_config(tmp_path, test_servers):
    """Create a temporary server configuration file."""
    config_file = tmp_path / "servers.json"
    servers_data = [s.dict() for s in test_servers]
    config_file.write_text(json.dumps(servers_data, indent=2))
    return str(config_file)


@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "OK"
    mock_response.json.return_value = {
        "cpu": [30.0, 40.0],
        "channels": [
            {"id": "1", "name": "Channel 1", "status": "running"},
            {"id": "2", "name": "Channel 2", "status": "stopped"}
        ]
    }
    return mock_response


@pytest.fixture
def mock_httpx_client(mock_httpx_response):
    """Create a mock httpx.AsyncClient."""
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_httpx_response
    mock_client.aclose.return_value = None
    return mock_client


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
