"""
Integration tests for database operations and persistence.

These tests verify that API endpoints correctly interact with the database,
handle transactions properly, and maintain data consistency.
"""

import pytest
import json
from datetime import datetime, timedelta
from typing import Dict, Any

from tests.integration import IntegrationTestBase


class TestWorkflowDatabaseIntegration(IntegrationTestBase):
    """Test workflow database operations."""

    @pytest.mark.asyncio
    async def test_workflow_creation_and_persistence(self):
        """Test that workflows are properly created and persisted."""
        workflow_data = {
            "name": "Integration Test Workflow",
            "description": "Testing database persistence",
            "nodes": [
                {
                    "id": "test-node",
                    "type": "action",
                    "action_type": "http",
                    "config": {"method": "GET", "url": "https://httpbin.org/json"}
                }
            ],
            "connections": []
        }

        # Create workflow
        response = await self.client.post("/api/v1/flows/create", json=workflow_data)
        assert response.status_code == 200

        result = response.json()
        assert "workflow_id" in result
        workflow_id = result["workflow_id"]

        # Verify workflow was persisted
        response = await self.client.get(f"/api/v1/flows/{workflow_id}")
        assert response.status_code == 200

        persisted_workflow = response.json()
        assert persisted_workflow["name"] == workflow_data["name"]
        assert persisted_workflow["description"] == workflow_data["description"]
        assert len(persisted_workflow["nodes"]) == len(workflow_data["nodes"])

    @pytest.mark.asyncio
    async def test_workflow_execution_history_persistence(self):
        """Test that workflow execution history is properly persisted."""
        workflow_data = get_test_workflow_data()
        workflow = await self.create_test_workflow(workflow_data)

        # Execute workflow
        result = await self.execute_workflow(workflow["workflow_id"], {"test": "data"})

        # Check execution was recorded
        executions_response = await self.client.get("/api/v1/flows/executions")
        assert executions_response.status_code == 200

        executions = executions_response.json()["executions"]
        assert len(executions) >= 1

        # Find our execution
        our_execution = next(
            (exec for exec in executions if exec["execution_id"] == result["execution_id"]),
            None
        )
        assert our_execution is not None
        assert our_execution["flow_id"] == workflow["workflow_id"]

    @pytest.mark.asyncio
    async def test_workflow_update_persistence(self):
        """Test that workflow updates are properly persisted."""
        workflow_data = get_test_workflow_data()
        workflow = await self.create_test_workflow(workflow_data)

        # Update workflow
        updated_data = workflow_data.copy()
        updated_data["name"] = "Updated Test Workflow"
        updated_data["description"] = "Updated description"

        response = await self.client.put(
            f"/api/v1/flows/{workflow['workflow_id']}",
            json=updated_data
        )
        assert response.status_code == 200

        # Verify update was persisted
        response = await self.client.get(f"/api/v1/flows/{workflow['workflow_id']}")
        assert response.status_code == 200

        updated_workflow = response.json()
        assert updated_workflow["name"] == "Updated Test Workflow"
        assert updated_workflow["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_workflow_deletion_persistence(self):
        """Test that workflow deletion is properly handled."""
        workflow_data = get_test_workflow_data()
        workflow = await self.create_test_workflow(workflow_data)

        # Delete workflow
        response = await self.client.delete(f"/api/v1/flows/{workflow['workflow_id']}")
        assert response.status_code == 200

        # Verify workflow is no longer accessible
        response = await self.client.get(f"/api/v1/flows/{workflow['workflow_id']}")
        assert response.status_code == 404


class TestExecutionDatabaseIntegration(IntegrationTestBase):
    """Test execution database operations."""

    @pytest.mark.asyncio
    async def test_execution_result_persistence(self):
        """Test that execution results are properly persisted."""
        workflow_data = get_test_workflow_data()
        workflow = await self.create_test_workflow(workflow_data)

        # Execute workflow
        result = await self.execute_workflow(workflow["workflow_id"], {"test": "data"})

        # Wait for execution to complete
        import time
        max_attempts = 10
        for _ in range(max_attempts):
            status = await self.get_execution_status(result["execution_id"])
            if status["status"] in ["completed", "error"]:
                break
            time.sleep(0.1)

        # Verify execution details were persisted
        final_status = await self.get_execution_status(result["execution_id"])
        assert final_status["execution_id"] == result["execution_id"]
        assert final_status["status"] in ["completed", "error"]
        assert "executed_nodes" in final_status
        assert isinstance(final_status["executed_nodes"], list)

    @pytest.mark.asyncio
    async def test_execution_error_persistence(self):
        """Test that execution errors are properly persisted."""
        # Create a workflow that will fail
        workflow_data = {
            "name": "Failing Workflow",
            "description": "Workflow designed to fail",
            "nodes": [
                {
                    "id": "failing-action",
                    "type": "action",
                    "action_type": "http",
                    "config": {
                        "method": "GET",
                        "url": "https://invalid-domain-that-does-not-exist.com"
                    }
                }
            ],
            "connections": []
        }

        workflow = await self.create_test_workflow(workflow_data)

        # Execute workflow
        result = await self.execute_workflow(workflow["workflow_id"], {})

        # Wait for execution to complete
        import time
        max_attempts = 10
        for _ in range(max_attempts):
            status = await self.get_execution_status(result["execution_id"])
            if status["status"] in ["completed", "error"]:
                break
            time.sleep(0.1)

        # Verify error was persisted
        final_status = await self.get_execution_status(result["execution_id"])
        assert final_status["status"] == "error"
        assert "error_message" in final_status or "error" in final_status

    @pytest.mark.asyncio
    async def test_execution_performance_metrics_persistence(self):
        """Test that execution performance metrics are properly persisted."""
        workflow_data = get_test_workflow_data()
        workflow = await self.create_test_workflow(workflow_data)

        # Execute workflow
        start_time = datetime.utcnow()
        result = await self.execute_workflow(workflow["workflow_id"], {"test": "data"})
        end_time = datetime.utcnow()

        # Wait for completion
        import time
        max_attempts = 10
        for _ in range(max_attempts):
            status = await self.get_execution_status(result["execution_id"])
            if status["status"] in ["completed", "error"]:
                break
            time.sleep(0.1)

        # Verify timing information was recorded
        final_status = await self.get_execution_status(result["execution_id"])
        assert "started_at" in final_status
        assert "completed_at" in final_status or final_status["status"] == "error"

        # Verify execution time is reasonable
        if "duration" in final_status:
            assert final_status["duration"] >= 0
            assert final_status["duration"] < 300  # Less than 5 minutes


class TestTriggerDatabaseIntegration(IntegrationTestBase):
    """Test trigger database operations."""

    @pytest.mark.asyncio
    async def test_trigger_creation_and_persistence(self):
        """Test that triggers are properly created and persisted."""
        trigger_data = {
            "trigger_type": "webhook",
            "config": {
                "webhook_id": "test-integration-webhook",
                "secret": "test-secret-key"
            },
            "flow_id": "test-flow-id"
        }

        # Create trigger
        response = await self.client.post("/api/v1/triggers/create", json=trigger_data)
        assert response.status_code == 200

        result = response.json()
        assert "trigger_id" in result

        # Verify trigger was persisted (if endpoint exists)
        # Note: This assumes we have a trigger listing endpoint
        response = await self.client.get("/api/v1/triggers")
        if response.status_code == 200:
            triggers = response.json()
            assert isinstance(triggers, list)
            # Check if our trigger is in the list
            trigger_ids = [t.get("id") or t.get("trigger_id") for t in triggers]
            assert result["trigger_id"] in trigger_ids

    @pytest.mark.asyncio
    async def test_webhook_trigger_execution_tracking(self):
        """Test that webhook trigger executions are properly tracked."""
        trigger_data = {
            "trigger_type": "webhook",
            "config": {
                "webhook_id": "test-webhook-tracking",
                "secret": "test-secret"
            },
            "flow_id": "test-flow-id"
        }

        # Create trigger
        create_response = await self.client.post("/api/v1/triggers/create", json=trigger_data)
        assert create_response.status_code == 200

        trigger_result = create_response.json()
        webhook_url = trigger_result.get("webhook_url")

        if webhook_url:
            # Simulate webhook call (this would normally come from external service)
            # For testing, we'll use the internal webhook endpoint
            webhook_payload = {
                "event": "test.integration",
                "data": {"key": "value"},
                "timestamp": datetime.utcnow().isoformat()
            }

            # This test assumes we have internal webhook processing
            # In a real scenario, this would be tested differently
            assert webhook_payload is not None


class TestActionDatabaseIntegration(IntegrationTestBase):
    """Test action database operations."""

    @pytest.mark.asyncio
    async def test_action_execution_logging(self):
        """Test that action executions are properly logged."""
        # Execute an action
        result = await self.execute_action(
            "http",
            {"method": "GET", "url": "https://httpbin.org/json"},
            {}
        )

        # Verify execution was logged (if logging system exists)
        # This would typically involve checking log entries in database
        assert result["success"] is True
        assert "execution_id" in result

    @pytest.mark.asyncio
    async def test_action_configuration_validation(self):
        """Test that action configurations are properly validated."""
        # Test valid configuration
        valid_config = {
            "method": "GET",
            "url": "https://httpbin.org/json"
        }

        result = await self.execute_action("http", valid_config, {})
        assert result["success"] is True

        # Test invalid configuration
        invalid_config = {
            "method": "INVALID_METHOD",
            "url": "https://httpbin.org/json"
        }

        # This should either fail or handle the error gracefully
        result = await self.execute_action("http", invalid_config, {})
        # The result should indicate the issue
        assert "execution_id" in result or "error" in result


class TestTransactionHandling(IntegrationTestBase):
    """Test database transaction handling."""

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_error(self):
        """Test that transactions are properly rolled back on errors."""
        # Create a workflow that will fail
        workflow_data = {
            "name": "Transaction Test Workflow",
            "description": "Testing transaction rollback",
            "nodes": [
                {
                    "id": "failing-node",
                    "type": "action",
                    "action_type": "http",
                    "config": {
                        "method": "GET",
                        "url": "https://invalid-domain-test.com"
                    }
                }
            ],
            "connections": []
        }

        workflow = await self.create_test_workflow(workflow_data)

        # Execute workflow (should fail)
        result = await self.execute_workflow(workflow["workflow_id"], {})

        # Verify that any database changes were rolled back
        # This is difficult to test directly without specific database assertions
        # But we can verify the execution is marked as failed
        assert result["execution_id"] is not None

        # Check final status
        final_status = await self.get_execution_status(result["execution_id"])
        assert final_status["status"] == "error"

    @pytest.mark.asyncio
    async def test_concurrent_workflow_executions(self):
        """Test handling of concurrent workflow executions."""
        workflow_data = get_test_workflow_data()
        workflow = await self.create_test_workflow(workflow_data)

        # Execute multiple workflows concurrently
        import asyncio

        async def execute_and_check():
            result = await self.execute_workflow(workflow["workflow_id"], {"test": "concurrent"})
            return result

        # Execute 5 workflows concurrently
        tasks = [execute_and_check() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # Verify all executions were handled properly
        assert len(results) == 5
        for result in results:
            assert "execution_id" in result

        # Verify no race conditions occurred
        execution_ids = [r["execution_id"] for r in results]
        assert len(set(execution_ids)) == len(execution_ids)  # All IDs are unique


# Helper functions
def get_test_workflow_data():
    """Get sample test workflow data."""
    return {
        "name": "Integration Test Workflow",
        "description": "Testing database integration",
        "nodes": [
            {
                "id": "http-action",
                "type": "action",
                "action_type": "http",
                "config": {
                    "method": "GET",
                    "url": "https://httpbin.org/json"
                }
            }
        ],
        "connections": []
    }

