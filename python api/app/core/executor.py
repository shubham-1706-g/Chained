"""Node Executor Module

This module handles the execution of individual workflow nodes.
It provides the logic for running triggers, actions, and operations
within the workflow engine.
"""

import asyncio
import time
from typing import Dict, Any, Optional, Callable, Awaitable
from enum import Enum

from .context import ExecutionContext, NodeExecutionResult


class NodeType(Enum):
    """Enumeration of supported node types."""
    TRIGGER = "trigger"
    ACTION = "action"
    OPERATION = "operation"


class NodeExecutionError(Exception):
    """Raised when a node execution fails."""
    def __init__(self, node_id: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.node_id = node_id
        self.message = message
        self.details = details or {}
        super().__init__(f"Node {node_id} execution failed: {message}")


class NodeExecutor:
    """Executes individual workflow nodes.

    This class handles the execution of different types of nodes
    (triggers, actions, operations) within a workflow.
    """

    def __init__(self):
        self.node_handlers: Dict[NodeType, Callable] = {}
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default node execution handlers."""
        self.node_handlers[NodeType.ACTION] = self._execute_action_node
        self.node_handlers[NodeType.OPERATION] = self._execute_operation_node
        self.node_handlers[NodeType.TRIGGER] = self._execute_trigger_node

    def register_handler(self, node_type: NodeType, handler: Callable) -> None:
        """Register a custom handler for a node type."""
        self.node_handlers[node_type] = handler

    async def execute_node(
        self,
        node_data: Dict[str, Any],
        context: ExecutionContext,
        node_registry: Optional[Dict[str, Any]] = None
    ) -> NodeExecutionResult:
        """Execute a workflow node.

        Args:
            node_data: The node configuration and metadata
            context: The execution context
            node_registry: Registry of available node implementations

        Returns:
            NodeExecutionResult containing the execution outcome

        Raises:
            NodeExecutionError: If node execution fails
        """
        node_id = node_data.get("id", "unknown")
        node_type_str = node_data.get("type", "").lower()

        try:
            # Validate node data
            if not self._validate_node_data(node_data):
                raise NodeExecutionError(
                    node_id,
                    "Invalid node data structure",
                    {"node_data": node_data}
                )

            # Determine node type
            try:
                node_type = NodeType(node_type_str)
            except ValueError:
                raise NodeExecutionError(
                    node_id,
                    f"Unknown node type: {node_type_str}",
                    {"supported_types": [t.value for t in NodeType]}
                )

            # Get handler for node type
            handler = self.node_handlers.get(node_type)
            if not handler:
                raise NodeExecutionError(
                    node_id,
                    f"No handler registered for node type: {node_type.value}"
                )

            # Set current node in context
            context.current_node_id = node_id

            # Execute the node
            start_time = time.time()
            result = await handler(node_data, context, node_registry)
            execution_time = time.time() - start_time

            # Create execution result
            execution_result = NodeExecutionResult(
                node_id=node_id,
                success=True,
                output=result,
                execution_time=execution_time
            )

            # Add to context
            context.add_node_output(node_id, result, execution_time)

            return execution_result

        except NodeExecutionError:
            raise
        except Exception as e:
            error_msg = f"Unexpected error during node execution: {str(e)}"
            execution_result = NodeExecutionResult(
                node_id=node_id,
                success=False,
                error=error_msg,
                execution_time=time.time() - time.time()  # This will be 0, but we set it anyway
            )
            raise NodeExecutionError(node_id, error_msg, {"original_error": str(e)}) from e

    def _validate_node_data(self, node_data: Dict[str, Any]) -> bool:
        """Validate the structure of node data."""
        required_fields = ["id", "type"]
        return all(field in node_data for field in required_fields)

    async def _execute_action_node(
        self,
        node_data: Dict[str, Any],
        context: ExecutionContext,
        node_registry: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute an action node."""
        action_name = node_data.get("action", "")
        config = node_data.get("config", {})
        input_data = node_data.get("input", {})

        if not node_registry or action_name not in node_registry:
            raise NodeExecutionError(
                node_data["id"],
                f"Action '{action_name}' not found in registry"
            )

        action_instance = node_registry[action_name]
        return await action_instance.execute(input_data, context)

    async def _execute_operation_node(
        self,
        node_data: Dict[str, Any],
        context: ExecutionContext,
        node_registry: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute an operation node."""
        operation_name = node_data.get("operation", "")
        config = node_data.get("config", {})
        input_data = node_data.get("input", {})

        if not node_registry or operation_name not in node_registry:
            raise NodeExecutionError(
                node_data["id"],
                f"Operation '{operation_name}' not found in registry"
            )

        operation_instance = node_registry[operation_name]
        return await operation_instance.execute(input_data, context)

    async def _execute_trigger_node(
        self,
        node_data: Dict[str, Any],
        context: ExecutionContext,
        node_registry: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a trigger node."""
        trigger_name = node_data.get("trigger", "")
        config = node_data.get("config", {})

        if not node_registry or trigger_name not in node_registry:
            raise NodeExecutionError(
                node_data["id"],
                f"Trigger '{trigger_name}' not found in registry"
            )

        trigger_instance = node_registry[trigger_name]

        # For triggers, we typically return trigger configuration
        # The actual triggering happens through event listeners
        return {
            "trigger_type": trigger_name,
            "config": config,
            "status": "configured"
        }
