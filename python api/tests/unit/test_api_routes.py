"""
Unit tests for API routes in FlowForge Python API.

This module contains comprehensive unit tests for:
- Actions API routes
- Flows API routes
- Triggers API routes
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
from typing import Dict, Any

from main import app
from app.core.context import ExecutionContext


class TestActionsAPIRoutes:
    """Test actions API routes."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def async_client(self):
        """Create async test client."""
        return AsyncClient(app=app, base_url="http://testserver")

    @pytest.mark.asyncio
    async def test_execute_action_success(self, async_client):
        """Test successful action execution via API."""
        action_data = {
            "action_type": "http",
            "config": {
                "method": "GET",
                "url": "https://api.example.com/test"
            },
            "input_data": {"param": "value"}
        }

        with patch("app.api.routes.actions.HTTPAction") as mock_action:
            mock_instance = AsyncMock()
            mock_instance.execute.return_value = {
                "success": True,
                "status_code": 200,
                "response": {"data": "test"}
            }
            mock_instance.test_connection.return_value = True
            mock_action.return_value = mock_instance

            response = await async_client.post("/api/v1/actions/execute", json=action_data)

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["result"]["status_code"] == 200

    @pytest.mark.asyncio
    async def test_execute_action_invalid_type(self, async_client):
        """Test action execution with invalid action type."""
        action_data = {
            "action_type": "invalid_action_type",
            "config": {},
            "input_data": {}
        }

        response = await async_client.post("/api/v1/actions/execute", json=action_data)

        assert response.status_code == 400
        response_data = response.json()
        assert response_data["detail"]["error"] == "Unsupported action type: invalid_action_type"

    @pytest.mark.asyncio
    async def test_execute_action_execution_error(self, async_client):
        """Test action execution with execution error."""
        action_data = {
            "action_type": "http",
            "config": {"method": "GET", "url": "https://api.example.com"},
            "input_data": {}
        }

        with patch("app.api.routes.actions.HTTPAction") as mock_action:
            mock_instance = AsyncMock()
            mock_instance.execute.side_effect = Exception("Connection timeout")
            mock_instance.test_connection.return_value = True
            mock_action.return_value = mock_instance

            response = await async_client.post("/api/v1/actions/execute", json=action_data)

            assert response.status_code == 500
            response_data = response.json()
            assert response_data["detail"]["error"] == "Connection timeout"

    @pytest.mark.asyncio
    async def test_test_action_success(self, async_client):
        """Test action configuration testing via API."""
        test_data = {
            "action_type": "http",
            "config": {
                "method": "GET",
                "url": "https://api.example.com/test"
            }
        }

        with patch("app.api.routes.actions.HTTPAction") as mock_action:
            mock_instance = AsyncMock()
            mock_instance.validate_config.return_value = True
            mock_instance.test_connection.return_value = True
            mock_instance.get_schema.return_value = {"type": "object", "properties": {}}
            mock_action.return_value = mock_instance

            response = await async_client.post("/api/v1/actions/test", json=test_data)

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["valid"] is True
            assert response_data["connection_test"] is True
            assert response_data["action_schema"] == {"type": "object", "properties": {}}

    @pytest.mark.asyncio
    async def test_test_action_invalid_config(self, async_client):
        """Test action configuration testing with invalid config."""
        test_data = {
            "action_type": "http",
            "config": {"method": "INVALID_METHOD"}  # Invalid method
        }

        with patch("app.api.routes.actions.HTTPAction") as mock_action:
            mock_instance = AsyncMock()
            mock_instance.validate_config.return_value = False
            mock_instance.test_connection.return_value = False
            mock_action.return_value = mock_instance

            response = await async_client.post("/api/v1/actions/test", json=test_data)

            assert response.status_code == 200  # Test endpoint returns 200 with validation results
            response_data = response.json()
            assert response_data["valid"] is False
            assert response_data["connection_test"] is False

    @pytest.mark.asyncio
    async def test_get_action_types(self, async_client):
        """Test getting available action types."""
        response = await async_client.get("/api/v1/actions/types")

        assert response.status_code == 200
        response_data = response.json()

        # Verify response structure
        assert "action_types" in response_data
        assert "categories" in response_data

        # Verify expected action types are present
        action_types = response_data["action_types"]
        assert "http" in action_types
        assert "openai" in action_types
        assert "send_email" in action_types

        # Verify categories structure
        categories = response_data["categories"]
        assert "ai" in categories
        assert "communication" in categories
        assert "productivity" in categories

    @pytest.mark.asyncio
    async def test_get_action_schema(self, async_client):
        """Test getting action schema."""
        with patch("app.api.routes.actions.HTTPAction") as mock_action:
            mock_instance = AsyncMock()
            mock_instance.get_schema.return_value = {
                "type": "object",
                "properties": {
                    "method": {"type": "string", "enum": ["GET", "POST"]},
                    "url": {"type": "string"}
                },
                "required": ["method", "url"]
            }
            mock_action.return_value = mock_instance

            response = await async_client.get("/api/v1/actions/http/schema")

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["action_type"] == "http"
            assert "schema" in response_data
            assert response_data["schema"]["type"] == "object"

    @pytest.mark.asyncio
    async def test_get_action_schema_invalid_type(self, async_client):
        """Test getting schema for invalid action type."""
        response = await async_client.get("/api/v1/actions/invalid_type/schema")

        assert response.status_code == 400
        response_data = response.json()
        assert response_data["detail"]["error"] == "Unsupported action type: invalid_type"


class TestFlowsAPIRoutes:
    """Test flows API routes."""

    @pytest.fixture
    def async_client(self):
        """Create async test client."""
        return AsyncClient(app=app, base_url="http://testserver")

    @pytest.mark.asyncio
    async def test_execute_flow_success(self, async_client):
        """Test successful flow execution via API."""
        flow_data = {
            "flow_data": {
                "nodes": [
                    {
                        "id": "http-node",
                        "type": "action",
                        "action_type": "http",
                        "config": {"method": "GET", "url": "https://api.example.com"}
                    }
                ],
                "connections": []
            },
            "input_variables": {"input": "value"}
        }

        with patch("app.api.routes.flows.workflow_engine.execute_flow") as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "flow_id": "test-flow",
                "execution_id": "exec-123",
                "executed_nodes": [{"node_id": "http-node", "result": {"success": True}}],
                "duration": 1.5
            }

            response = await async_client.post("/api/v1/flows/execute", json=flow_data)

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["flow_id"] == "test-flow"
            assert response_data["execution_id"] == "exec-123"

    @pytest.mark.asyncio
    async def test_execute_flow_validation_error(self, async_client):
        """Test flow execution with validation error."""
        flow_data = {
            "flow_data": {
                "nodes": [{"id": "node1", "type": "invalid_type"}],
                "connections": []
            }
        }

        response = await async_client.post("/api/v1/flows/execute", json=flow_data)

        assert response.status_code == 400
        response_data = response.json()
        assert "validation_errors" in response_data["detail"]

    @pytest.mark.asyncio
    async def test_get_execution_status(self, async_client):
        """Test getting execution status."""
        execution_id = "exec-123"

        with patch("app.api.routes.flows.execution_store.get_execution") as mock_get:
            mock_get.return_value = {
                "execution_id": execution_id,
                "status": "completed",
                "result": {"success": True},
                "duration": 2.5
            }

            response = await async_client.get(f"/api/v1/flows/execution/{execution_id}")

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["execution_id"] == execution_id
            assert response_data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_execution_status_not_found(self, async_client):
        """Test getting status for non-existent execution."""
        execution_id = "non-existent-exec"

        with patch("app.api.routes.flows.execution_store.get_execution") as mock_get:
            mock_get.return_value = None

            response = await async_client.get(f"/api/v1/flows/execution/{execution_id}")

            assert response.status_code == 404
            response_data = response.json()
            assert response_data["detail"]["error"] == f"Execution {execution_id} not found"

    @pytest.mark.asyncio
    async def test_get_execution_history(self, async_client):
        """Test getting execution history."""
        with patch("app.api.routes.flows.execution_store.get_executions") as mock_get:
            mock_get.return_value = [
                {
                    "execution_id": "exec-1",
                    "flow_id": "flow-1",
                    "status": "completed",
                    "start_time": "2024-01-15T10:00:00Z",
                    "duration": 1.5
                },
                {
                    "execution_id": "exec-2",
                    "flow_id": "flow-2",
                    "status": "running",
                    "start_time": "2024-01-15T10:30:00Z",
                    "duration": None
                }
            ]

            response = await async_client.get("/api/v1/flows/executions")

            assert response.status_code == 200
            response_data = response.json()
            assert len(response_data["executions"]) == 2
            assert response_data["total_count"] == 2

    @pytest.mark.asyncio
    async def test_validate_flow_success(self, async_client):
        """Test successful flow validation."""
        flow_data = {
            "nodes": [
                {
                    "id": "http-node",
                    "type": "action",
                    "action_type": "http",
                    "config": {"method": "GET", "url": "https://api.example.com"}
                }
            ],
            "connections": []
        }

        with patch("app.api.routes.flows.workflow_engine.validate_flow") as mock_validate:
            mock_validate.return_value = (True, [])

            response = await async_client.post("/api/v1/flows/validate", json=flow_data)

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["valid"] is True
            assert len(response_data["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_flow_with_errors(self, async_client):
        """Test flow validation with errors."""
        flow_data = {
            "nodes": [{"id": "node1", "type": "invalid_type"}],
            "connections": []
        }

        with patch("app.api.routes.flows.workflow_engine.validate_flow") as mock_validate:
            mock_validate.return_value = (False, ["Invalid node type", "Missing required fields"])

            response = await async_client.post("/api/v1/flows/validate", json=flow_data)

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["valid"] is False
            assert len(response_data["errors"]) == 2


class TestTriggersAPIRoutes:
    """Test triggers API routes."""

    @pytest.fixture
    def async_client(self):
        """Create async test client."""
        return AsyncClient(app=app, base_url="http://testserver")

    @pytest.mark.asyncio
    async def test_create_trigger_success(self, async_client):
        """Test successful trigger creation."""
        trigger_data = {
            "trigger_type": "webhook",
            "config": {
                "webhook_id": "test-webhook",
                "secret": "webhook-secret"
            },
            "flow_id": "test-flow"
        }

        with patch("app.api.routes.triggers.WebhookTrigger") as mock_trigger:
            mock_instance = AsyncMock()
            mock_instance.setup.return_value = None
            mock_trigger.return_value = mock_instance

            response = await async_client.post("/api/v1/triggers/create", json=trigger_data)

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["trigger_type"] == "webhook"

    @pytest.mark.asyncio
    async def test_create_trigger_invalid_type(self, async_client):
        """Test trigger creation with invalid type."""
        trigger_data = {
            "trigger_type": "invalid_trigger_type",
            "config": {},
            "flow_id": "test-flow"
        }

        response = await async_client.post("/api/v1/triggers/create", json=trigger_data)

        assert response.status_code == 400
        response_data = response.json()
        assert response_data["detail"]["error"] == "Unsupported trigger type: invalid_trigger_type"

    @pytest.mark.asyncio
    async def test_test_trigger_success(self, async_client):
        """Test successful trigger testing."""
        test_data = {
            "trigger_type": "webhook",
            "config": {
                "webhook_id": "test-webhook",
                "secret": "webhook-secret"
            }
        }

        with patch("app.api.routes.triggers.WebhookTrigger") as mock_trigger:
            mock_instance = AsyncMock()
            mock_instance.setup.return_value = None
            mock_instance.start.return_value = None
            mock_trigger.return_value = mock_instance

            response = await async_client.post("/api/v1/triggers/test/webhook", json=test_data)

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            assert response_data["message"] == "Webhook trigger test successful"

    @pytest.mark.asyncio
    async def test_test_trigger_setup_failure(self, async_client):
        """Test trigger testing with setup failure."""
        test_data = {
            "trigger_type": "webhook",
            "config": {"webhook_id": "test-webhook"}
        }

        with patch("app.api.routes.triggers.WebhookTrigger") as mock_trigger:
            mock_instance = AsyncMock()
            mock_instance.setup.side_effect = Exception("Setup failed")
            mock_trigger.return_value = mock_instance

            response = await async_client.post("/api/v1/triggers/test/webhook", json=test_data)

            assert response.status_code == 400
            response_data = response.json()
            assert response_data["success"] is False
            assert "Setup failed" in response_data["error"]

    @pytest.mark.asyncio
    async def test_get_trigger_types(self, async_client):
        """Test getting available trigger types."""
        response = await async_client.get("/api/v1/triggers/types")

        assert response.status_code == 200
        response_data = response.json()

        # Verify response structure
        assert "trigger_types" in response_data
        assert "categories" in response_data

        # Verify expected trigger types are present
        trigger_types = response_data["trigger_types"]
        assert "webhook" in trigger_types
        assert "schedule" in trigger_types
        assert "file_watch" in trigger_types

        # Verify categories structure
        categories = response_data["categories"]
        assert "web" in categories
        assert "time" in categories
        assert "filesystem" in categories

    @pytest.mark.asyncio
    async def test_get_webhook_status(self, async_client):
        """Test getting webhook status."""
        webhook_id = "test-webhook-123"

        with patch("app.api.routes.triggers.trigger_manager.get_webhook_status") as mock_get:
            mock_get.return_value = {
                "webhook_id": webhook_id,
                "is_active": True,
                "total_requests": 42,
                "last_request": "2024-01-15T10:30:00Z"
            }

            response = await async_client.get(f"/api/v1/triggers/webhook/{webhook_id}/status")

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["webhook_id"] == webhook_id
            assert response_data["is_active"] is True
            assert response_data["total_requests"] == 42

    @pytest.mark.asyncio
    async def test_get_webhook_status_not_found(self, async_client):
        """Test getting status for non-existent webhook."""
        webhook_id = "non-existent-webhook"

        with patch("app.api.routes.triggers.trigger_manager.get_webhook_status") as mock_get:
            mock_get.return_value = None

            response = await async_client.get(f"/api/v1/triggers/webhook/{webhook_id}/status")

            assert response.status_code == 404
            response_data = response.json()
            assert response_data["detail"]["error"] == f"Webhook {webhook_id} not found"


class TestAPIErrorHandling:
    """Test API error handling."""

    @pytest.fixture
    def async_client(self):
        """Create async test client."""
        return AsyncClient(app=app, base_url="http://testserver")

    @pytest.mark.asyncio
    async def test_invalid_json_payload(self, async_client):
        """Test handling of invalid JSON payload."""
        response = await async_client.post(
            "/api/v1/actions/execute",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422  # FastAPI validation error

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, async_client):
        """Test handling of missing required fields."""
        incomplete_data = {"action_type": "http"}  # Missing config

        response = await async_client.post("/api/v1/actions/execute", json=incomplete_data)

        assert response.status_code == 422  # FastAPI validation error

    @pytest.mark.asyncio
    async def test_method_not_allowed(self, async_client):
        """Test handling of method not allowed."""
        response = await async_client.patch("/api/v1/actions/execute")

        assert response.status_code == 405  # Method not allowed

    @pytest.mark.asyncio
    async def test_endpoint_not_found(self, async_client):
        """Test handling of non-existent endpoint."""
        response = await async_client.get("/api/v1/nonexistent/endpoint")

        assert response.status_code == 404  # Not found


class TestAPIRateLimiting:
    """Test API rate limiting (if implemented)."""

    @pytest.fixture
    def async_client(self):
        """Create async test client."""
        return AsyncClient(app=app, base_url="http://testserver")

    @pytest.mark.asyncio
    async def test_concurrent_requests_handling(self, async_client):
        """Test handling of concurrent requests."""
        # This test would need to be expanded based on actual rate limiting implementation
        action_data = {
            "action_type": "http",
            "config": {"method": "GET", "url": "https://api.example.com"},
            "input_data": {}
        }

        with patch("app.api.routes.actions.HTTPAction") as mock_action:
            mock_instance = AsyncMock()
            mock_instance.execute.return_value = {"success": True}
            mock_instance.test_connection.return_value = True
            mock_action.return_value = mock_instance

            # Make multiple concurrent requests
            tasks = []
            for i in range(5):
                task = async_client.post("/api/v1/actions/execute", json=action_data)
                tasks.append(task)

            responses = await asyncio.gather(*tasks)

            # All requests should succeed
            for response in responses:
                assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])

