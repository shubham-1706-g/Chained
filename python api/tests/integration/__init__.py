"""
Integration tests for FlowForge Python API.

This package contains comprehensive integration tests that verify:
- API endpoints with mocked database services
- External service integrations
- Authentication and authorization flows
- Error handling and edge cases
- Transaction handling and rollback scenarios
- Performance under load

Integration tests are slower than unit tests but provide more confidence
in the system's behavior when components are integrated together.
"""

import asyncio
import os
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.core.config import get_settings
from app.core.database import get_db_session


# Test configuration
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test_flowforge")
TEST_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_engine():
    """Create test database engine."""
    from sqlalchemy.ext.asyncio import create_async_engine
    from app.core.database import Base

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine):
    """Create test database session."""
    async_session = sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()  # Rollback any changes


@pytest.fixture
async def client(test_db_session):
    """Create test client with database session."""

    async def override_get_db():
        yield test_db_session

    # Override the database dependency
    app.dependency_overrides[get_db_session] = override_get_db

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
async def authenticated_client(client):
    """Create authenticated test client."""
    # Mock authentication for testing
    from app.core.auth import create_access_token

    # This would normally be done with proper authentication
    # For now, we'll assume the client is authenticated
    yield client


@asynccontextmanager
async def mock_external_service(service_name: str, responses: Dict[str, Any]):
    """Context manager for mocking external services."""
    import aiohttp
    from unittest.mock import patch, AsyncMock

    async def mock_request(*args, **kwargs):
        # Return predefined response based on URL or other criteria
        return responses.get(service_name, {"status": 200, "data": {}})

    with patch.object(aiohttp.ClientSession, 'request', side_effect=mock_request):
        yield


class IntegrationTestBase:
    """Base class for integration tests with common utilities."""

    @pytest.fixture(autouse=True)
    async def setup_method(self, client, test_db_session):
        """Setup method run before each test."""
        self.client = client
        self.db_session = test_db_session

    async def create_test_workflow(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to create a test workflow."""
        response = await self.client.post("/api/v1/flows/create", json=workflow_data)
        assert response.status_code == 200
        return response.json()

    async def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to execute a workflow."""
        response = await self.client.post(
            "/api/v1/flows/execute",
            json={
                "workflow_id": workflow_id,
                "input_data": input_data
            }
        )
        assert response.status_code == 200
        return response.json()

    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Helper method to get execution status."""
        response = await self.client.get(f"/api/v1/flows/execution/{execution_id}")
        assert response.status_code == 200
        return response.json()

    async def create_test_trigger(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to create a test trigger."""
        response = await self.client.post("/api/v1/triggers/create", json=trigger_data)
        assert response.status_code == 200
        return response.json()

    async def execute_action(self, action_type: str, config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to execute an action."""
        response = await self.client.post(
            "/api/v1/actions/execute",
            json={
                "action_type": action_type,
                "config": config,
                "input_data": input_data
            }
        )
        assert response.status_code == 200
        return response.json()


# Test configuration helpers
def get_test_config() -> Dict[str, Any]:
    """Get test configuration."""
    return {
        "api_key": "test-api-key",
        "database_url": TEST_DATABASE_URL,
        "redis_url": TEST_REDIS_URL,
        "debug": True,
        "test_mode": True
    }


def get_test_workflow_data() -> Dict[str, Any]:
    """Get sample test workflow data."""
    return {
        "name": "Test Workflow",
        "description": "Integration test workflow",
        "nodes": [
            {
                "id": "trigger-node",
                "type": "trigger",
                "trigger_type": "webhook",
                "config": {"webhook_id": "test-webhook"}
            },
            {
                "id": "action-node",
                "type": "action",
                "action_type": "http",
                "config": {
                    "method": "GET",
                    "url": "https://httpbin.org/json"
                }
            }
        ],
        "connections": [
            {"from": "trigger-node", "to": "action-node"}
        ]
    }


def get_test_action_config(action_type: str) -> Dict[str, Any]:
    """Get test configuration for different action types."""
    configs = {
        "http": {
            "method": "GET",
            "url": "https://httpbin.org/json",
            "timeout": 30
        },
        "openai": {
            "api_key": "test-key",
            "model": "gpt-3.5-turbo",
            "max_tokens": 100
        },
        "send_email": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "test@example.com",
            "password": "test-password",
            "from_email": "test@example.com",
            "to_email": "recipient@example.com",
            "subject": "Test Email",
            "body": "Test message"
        }
    }
    return configs.get(action_type, {})


def get_test_trigger_config(trigger_type: str) -> Dict[str, Any]:
    """Get test configuration for different trigger types."""
    configs = {
        "webhook": {
            "webhook_id": "test-webhook",
            "secret": "test-secret"
        },
        "schedule": {
            "schedule_type": "cron",
            "cron_expression": "0 */2 * * *"
        },
        "file_watch": {
            "watch_path": "/tmp/test",
            "file_pattern": "*.txt"
        }
    }
    return configs.get(trigger_type, {})

