"""
Unit tests for core components in FlowForge Python API.

This module contains comprehensive unit tests for:
- Workflow Engine
- Node Executor
- Execution Context
- Task Scheduler
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.core.engine import WorkflowEngine
from app.core.executor import NodeExecutor
from app.core.context import ExecutionContext
from app.core.scheduler import TaskScheduler


class TestExecutionContext:
    """Test execution context functionality."""

    def test_execution_context_creation(self):
        """Test execution context creation with required fields."""
        context = ExecutionContext(
            flow_id="test-flow-123",
            execution_id="exec-456",
            variables={"input": "value"},
            previous_outputs=[],
            user_id="user-789"
        )

        assert context.flow_id == "test-flow-123"
        assert context.execution_id == "exec-456"
        assert context.variables == {"input": "value"}
        assert context.previous_outputs == []
        assert context.user_id == "user-789"
        assert isinstance(context.start_time, datetime)

    def test_execution_context_variable_operations(self):
        """Test execution context variable operations."""
        context = ExecutionContext(
            flow_id="test-flow",
            execution_id="test-exec",
            variables={"initial": "value"},
            previous_outputs=[],
            user_id="test-user"
        )

        # Test variable setting
        context.set_variable("new_var", "new_value")
        assert context.variables["new_var"] == "new_value"

        # Test variable getting
        assert context.get_variable("initial") == "value"
        assert context.get_variable("nonexistent", "default") == "default"

        # Test variable updating
        context.update_variables({"updated": "value", "another": "var"})
        assert context.variables["updated"] == "value"
        assert context.variables["another"] == "var"

    def test_execution_context_output_operations(self):
        """Test execution context output operations."""
        context = ExecutionContext(
            flow_id="test-flow",
            execution_id="test-exec",
            variables={},
            previous_outputs=[],
            user_id="test-user"
        )

        # Test adding output
        output1 = {"node_id": "node1", "result": "success"}
        context.add_output(output1)
        assert len(context.previous_outputs) == 1
        assert context.previous_outputs[0] == output1

        # Test getting outputs by node
        context.add_output({"node_id": "node2", "result": "success2"})
        node1_outputs = context.get_outputs_by_node("node1")
        assert len(node1_outputs) == 1
        assert node1_outputs[0]["result"] == "success"

        # Test getting latest output
        latest = context.get_latest_output()
        assert latest["node_id"] == "node2"

    def test_execution_context_status_operations(self):
        """Test execution context status operations."""
        context = ExecutionContext(
            flow_id="test-flow",
            execution_id="test-exec",
            variables={},
            previous_outputs=[],
            user_id="test-user"
        )

        # Test initial status
        assert context.status == "running"

        # Test status updates
        context.update_status("completed")
        assert context.status == "completed"

        # Test error handling
        context.set_error("Test error")
        assert context.status == "error"
        assert context.error_message == "Test error"

    def test_execution_context_duration_calculation(self):
        """Test execution context duration calculation."""
        context = ExecutionContext(
            flow_id="test-flow",
            execution_id="test-exec",
            variables={},
            previous_outputs=[],
            user_id="test-user"
        )

        # Mock start time to be 5 seconds ago
        context.start_time = datetime.utcnow() - timedelta(seconds=5)

        duration = context.get_duration()
        assert duration >= 5.0
        assert isinstance(duration, float)


class TestNodeExecutor:
    """Test node executor functionality."""

    @pytest.fixture
    def execution_context(self):
        """Create a mock execution context."""
        return ExecutionContext(
            flow_id="test-flow",
            execution_id="test-exec",
            variables={"test": "value"},
            previous_outputs=[],
            user_id="test-user"
        )

    @pytest.mark.asyncio
    async def test_node_executor_creation(self, execution_context):
        """Test node executor creation."""
        executor = NodeExecutor()

        # Test with valid node definition
        node_def = {
            "id": "test-node",
            "type": "action",
            "action_type": "http",
            "config": {"method": "GET", "url": "https://api.example.com"}
        }

        with patch("app.core.executor.HTTPAction") as mock_action:
            mock_action_instance = MagicMock()
            mock_action_instance.execute.return_value = {"success": True}
            mock_action.return_value = mock_action_instance

            result = await executor.execute_node(node_def, execution_context)

            assert result["success"] is True
            assert result["node_id"] == "test-node"
            mock_action_instance.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_node_executor_invalid_node_type(self, execution_context):
        """Test node executor with invalid node type."""
        executor = NodeExecutor()

        node_def = {
            "id": "test-node",
            "type": "invalid_type",
            "config": {}
        }

        result = await executor.execute_node(node_def, execution_context)

        assert result["success"] is False
        assert "Invalid node type" in result["error"]

    @pytest.mark.asyncio
    async def test_node_executor_action_execution_error(self, execution_context):
        """Test node executor action execution error handling."""
        executor = NodeExecutor()

        node_def = {
            "id": "test-node",
            "type": "action",
            "action_type": "http",
            "config": {"method": "GET", "url": "https://api.example.com"}
        }

        with patch("app.core.executor.HTTPAction") as mock_action:
            mock_action_instance = MagicMock()
            mock_action_instance.execute.side_effect = Exception("Connection failed")
            mock_action.return_value = mock_action_instance

            result = await executor.execute_node(node_def, execution_context)

            assert result["success"] is False
            assert "Connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_node_executor_unsupported_action_type(self, execution_context):
        """Test node executor with unsupported action type."""
        executor = NodeExecutor()

        node_def = {
            "id": "test-node",
            "type": "action",
            "action_type": "unsupported_action",
            "config": {}
        }

        result = await executor.execute_node(node_def, execution_context)

        assert result["success"] is False
        assert "Unsupported action type" in result["error"]

    @pytest.mark.asyncio
    async def test_node_executor_with_dependencies(self, execution_context):
        """Test node executor with dependency resolution."""
        executor = NodeExecutor()

        # Add previous output to context
        execution_context.add_output({
            "node_id": "prev-node",
            "result": {"data": "previous_result"}
        })

        node_def = {
            "id": "test-node",
            "type": "action",
            "action_type": "http",
            "config": {"method": "POST", "url": "https://api.example.com"},
            "dependencies": ["prev-node"]
        }

        with patch("app.core.executor.HTTPAction") as mock_action:
            mock_action_instance = MagicMock()
            mock_action_instance.execute.return_value = {"success": True}
            mock_action.return_value = mock_action_instance

            result = await executor.execute_node(node_def, execution_context)

            assert result["success"] is True
            # Verify dependencies were resolved in the execution context
            assert len(execution_context.previous_outputs) == 2


class TestWorkflowEngine:
    """Test workflow engine functionality."""

    @pytest.fixture
    def execution_context(self):
        """Create a mock execution context."""
        return ExecutionContext(
            flow_id="test-flow",
            execution_id="test-exec",
            variables={"input": "value"},
            previous_outputs=[],
            user_id="test-user"
        )

    @pytest.mark.asyncio
    async def test_workflow_engine_creation(self):
        """Test workflow engine creation and registration."""
        engine = WorkflowEngine()

        # Test initial state
        assert len(engine.triggers) == 0
        assert len(engine.actions) == 0
        assert len(engine.operations) == 0

    @pytest.mark.asyncio
    async def test_workflow_engine_execute_flow_simple(self, execution_context):
        """Test workflow engine executing a simple flow."""
        engine = WorkflowEngine()

        flow_data = {
            "nodes": [
                {
                    "id": "node1",
                    "type": "action",
                    "action_type": "http",
                    "config": {"method": "GET", "url": "https://api.example.com"}
                }
            ],
            "connections": []
        }

        with patch("app.core.engine.HTTPAction") as mock_action:
            mock_action_instance = MagicMock()
            mock_action_instance.execute.return_value = {"success": True, "result": "test"}
            mock_action.return_value = mock_action_instance

            result = await engine.execute_flow(flow_data, execution_context)

            assert result["success"] is True
            assert result["flow_id"] == "test-flow"
            assert len(result["executed_nodes"]) == 1

    @pytest.mark.asyncio
    async def test_workflow_engine_execute_flow_with_connections(self, execution_context):
        """Test workflow engine executing a flow with node connections."""
        engine = WorkflowEngine()

        flow_data = {
            "nodes": [
                {
                    "id": "http-node",
                    "type": "action",
                    "action_type": "http",
                    "config": {"method": "GET", "url": "https://api.example.com"}
                },
                {
                    "id": "transform-node",
                    "type": "action",
                    "action_type": "data_transform",
                    "config": {"transform_type": "json_to_csv"},
                    "dependencies": ["http-node"]
                }
            ],
            "connections": [
                {"from": "http-node", "to": "transform-node"}
            ]
        }

        with patch("app.core.engine.HTTPAction") as mock_http_action, \
             patch("app.core.engine.DataTransformAction") as mock_transform_action:

            mock_http_instance = MagicMock()
            mock_http_instance.execute.return_value = {"success": True, "data": {"key": "value"}}
            mock_http_action.return_value = mock_http_instance

            mock_transform_instance = MagicMock()
            mock_transform_instance.execute.return_value = {"success": True, "transformed": "data"}
            mock_transform_action.return_value = mock_transform_instance

            result = await engine.execute_flow(flow_data, execution_context)

            assert result["success"] is True
            assert len(result["executed_nodes"]) == 2
            # Verify execution order (dependencies respected)
            assert result["executed_nodes"][0]["node_id"] == "http-node"
            assert result["executed_nodes"][1]["node_id"] == "transform-node"

    @pytest.mark.asyncio
    async def test_workflow_engine_execute_flow_error_handling(self, execution_context):
        """Test workflow engine error handling during execution."""
        engine = WorkflowEngine()

        flow_data = {
            "nodes": [
                {
                    "id": "failing-node",
                    "type": "action",
                    "action_type": "http",
                    "config": {"method": "GET", "url": "https://api.example.com"}
                }
            ],
            "connections": []
        }

        with patch("app.core.engine.HTTPAction") as mock_action:
            mock_action_instance = MagicMock()
            mock_action_instance.execute.side_effect = Exception("Network error")
            mock_action.return_value = mock_action_instance

            result = await engine.execute_flow(flow_data, execution_context)

            assert result["success"] is False
            assert "Network error" in result["error"]
            assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_workflow_engine_validate_flow(self):
        """Test workflow engine flow validation."""
        engine = WorkflowEngine()

        # Valid flow
        valid_flow = {
            "nodes": [
                {
                    "id": "node1",
                    "type": "action",
                    "action_type": "http",
                    "config": {"method": "GET", "url": "https://api.example.com"}
                }
            ],
            "connections": []
        }

        is_valid, errors = engine.validate_flow(valid_flow)
        assert is_valid is True
        assert len(errors) == 0

        # Invalid flow - missing required fields
        invalid_flow = {
            "nodes": [
                {"id": "node1", "type": "action"}  # Missing action_type
            ],
            "connections": []
        }

        is_valid, errors = engine.validate_flow(invalid_flow)
        assert is_valid is False
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_workflow_engine_register_components(self):
        """Test workflow engine component registration."""
        engine = WorkflowEngine()

        # Mock action class
        mock_action_class = MagicMock()
        mock_action_class.__name__ = "TestAction"

        engine.register_action("test_action", mock_action_class)
        assert "test_action" in engine.actions
        assert engine.actions["test_action"] == mock_action_class

        # Mock trigger class
        mock_trigger_class = MagicMock()
        mock_trigger_class.__name__ = "TestTrigger"

        engine.register_trigger("test_trigger", mock_trigger_class)
        assert "test_trigger" in engine.triggers
        assert engine.triggers["test_trigger"] == mock_trigger_class


class TestTaskScheduler:
    """Test task scheduler functionality."""

    @pytest.fixture
    def scheduler(self):
        """Create a task scheduler instance."""
        return TaskScheduler()

    @pytest.mark.asyncio
    async def test_task_scheduler_creation(self, scheduler):
        """Test task scheduler creation."""
        assert len(scheduler.scheduled_tasks) == 0
        assert scheduler.is_running is False

    @pytest.mark.asyncio
    async def test_task_scheduler_add_task(self, scheduler):
        """Test adding a scheduled task."""
        async def test_task():
            return "task executed"

        task_id = scheduler.add_task(
            task_func=test_task,
            schedule_type="cron",
            cron_expression="0 * * * *",  # Every hour
            task_name="test_task"
        )

        assert task_id in scheduler.scheduled_tasks
        assert scheduler.scheduled_tasks[task_id]["name"] == "test_task"
        assert scheduler.scheduled_tasks[task_id]["schedule_type"] == "cron"

    @pytest.mark.asyncio
    async def test_task_scheduler_remove_task(self, scheduler):
        """Test removing a scheduled task."""
        async def test_task():
            return "task executed"

        task_id = scheduler.add_task(
            task_func=test_task,
            schedule_type="interval",
            interval_seconds=60,
            task_name="test_task"
        )

        assert task_id in scheduler.scheduled_tasks

        # Remove task
        result = scheduler.remove_task(task_id)
        assert result is True
        assert task_id not in scheduler.scheduled_tasks

        # Try to remove non-existent task
        result = scheduler.remove_task("non-existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_task_scheduler_start_stop(self, scheduler):
        """Test scheduler start and stop functionality."""
        assert scheduler.is_running is False

        # Start scheduler
        await scheduler.start()
        assert scheduler.is_running is True

        # Stop scheduler
        await scheduler.stop()
        assert scheduler.is_running is False

    @pytest.mark.asyncio
    async def test_task_scheduler_execute_task(self, scheduler):
        """Test task execution."""
        execution_count = 0

        async def test_task():
            nonlocal execution_count
            execution_count += 1
            return f"executed {execution_count}"

        task_id = scheduler.add_task(
            task_func=test_task,
            schedule_type="interval",
            interval_seconds=1,
            task_name="counter_task"
        )

        # Execute task manually
        result = await scheduler._execute_task(task_id)
        assert result == "executed 1"
        assert execution_count == 1

    @pytest.mark.asyncio
    async def test_task_scheduler_task_validation(self, scheduler):
        """Test task validation."""
        # Valid task
        is_valid, errors = scheduler._validate_task_config({
            "schedule_type": "cron",
            "cron_expression": "0 * * * *",
            "task_name": "valid_task"
        })
        assert is_valid is True
        assert len(errors) == 0

        # Invalid task - missing required fields
        is_valid, errors = scheduler._validate_task_config({
            "schedule_type": "cron"
            # Missing cron_expression and task_name
        })
        assert is_valid is False
        assert len(errors) > 0

        # Invalid cron expression
        is_valid, errors = scheduler._validate_task_config({
            "schedule_type": "cron",
            "cron_expression": "invalid",
            "task_name": "invalid_task"
        })
        assert is_valid is False
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_task_scheduler_get_task_status(self, scheduler):
        """Test getting task status."""
        async def test_task():
            return "completed"

        task_id = scheduler.add_task(
            task_func=test_task,
            schedule_type="interval",
            interval_seconds=60,
            task_name="status_test"
        )

        status = scheduler.get_task_status(task_id)
        assert status is not None
        assert status["task_id"] == task_id
        assert status["name"] == "status_test"
        assert status["is_active"] is True

        # Test non-existent task
        status = scheduler.get_task_status("non-existent")
        assert status is None

    @pytest.mark.asyncio
    async def test_task_scheduler_list_tasks(self, scheduler):
        """Test listing all tasks."""
        async def task1():
            return "task1"

        async def task2():
            return "task2"

        # Add multiple tasks
        task_id1 = scheduler.add_task(task1, "interval", 60, "task1")
        task_id2 = scheduler.add_task(task2, "interval", 30, "task2")

        tasks = scheduler.list_tasks()
        assert len(tasks) == 2

        task_names = [task["name"] for task in tasks]
        assert "task1" in task_names
        assert "task2" in task_names


if __name__ == "__main__":
    pytest.main([__file__])
