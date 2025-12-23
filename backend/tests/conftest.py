"""
Pytest configuration and fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncio
from typing import AsyncGenerator

from main import app
from database import Base, get_db
from config import settings


@pytest.fixture
def client() -> TestClient:
    """Create test client for API requests."""
    return TestClient(app)


@pytest.fixture
async def test_device_data():
    """Sample device data for testing."""
    return {
        "name": "Test Camera 1",
        "description": "Test camera description",
        "rtsp_url": "rtsp://test.example.com/stream",
        "location": "Test Location"
    }


@pytest.fixture
async def test_stream_data():
    """Sample stream data for testing."""
    return {
        "name": "Test Stream",
        "visibility": "private"
    }


# Phase markers for incremental testing
def pytest_collection_modifyitems(config, items):
    """Add phase markers to tests based on filename prefix."""
    for item in items:
        # Mark tests based on filename patterns
        if "test_phase1" in item.nodeid:
            item.add_marker(pytest.mark.phase1)
        elif "test_phase2" in item.nodeid:
            item.add_marker(pytest.mark.phase2)
        elif "test_phase3" in item.nodeid:
            item.add_marker(pytest.mark.phase3)
        elif "test_phase4" in item.nodeid:
            item.add_marker(pytest.mark.phase4)
        else:
            # Default to phase 1
            item.add_marker(pytest.mark.phase1)
