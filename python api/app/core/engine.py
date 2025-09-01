"""Workflow Engine Module

This module contains the main WorkflowEngine class that orchestrates
the execution of workflows, manages triggers and actions, and coordinates
all components of the automation platform.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import uuid

from .context import ExecutionContext
from .executor import NodeExecutor, NodeExecutionError
from .scheduler import WorkflowScheduler

logger = logging.getLogger(__name__)


class WorkflowExecutionError(Exception):
    """Raised when a workflow execution fails."""
    def __init__(self, flow_id: str, execution_id: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.flow_id = flow_id
        self.execution_id = execution_id
        self.message = message
        self.details = details or {}
        super().__init__(f"Workflow {flow_id} execution {execution_id} failed: {message}")


class WorkflowEngine:
    """Main workflow execution engine.

    This class orchestrates the execution of workflows by managing
    triggers, actions, and the flow of execution between nodes.
    """

    def __init__(self):
        self.triggers: Dict[str, Any] = {}
        self.actions: Dict[str, Any] = {}
        self.operations: Dict[str, Any] = {}

        self.executor = NodeExecutor()
        self.scheduler = WorkflowScheduler()

        self.active_executions: Dict[str, ExecutionContext] = {}
        self.execution_history: List[ExecutionContext] = []

        # Callbacks for external notifications
        self.execution_callbacks: List[Callable] = []

    async def initialize(self) -> None:
        """Initialize the workflow engine and start background services."""
        await self.scheduler.start()
        logger.info("Workflow engine initialized")

    async def shutdown(self) -> None:
        """Shutdown the workflow engine and cleanup resources."""
        await self.scheduler.stop()

        # Cancel any active executions
        for execution_id, context in self.active_executions.items():
            if context.status == "running":
                context.mark_cancelled()
                logger.info(f"Cancelled active execution {execution_id}")

        logger.info("Workflow engine shutdown complete")

    def register_trigger(self, trigger_name: str, trigger_class: Any) -> None:
        """Register a trigger class."""
        self.triggers[trigger_name] = trigger_class
        logger.info(f"Registered trigger: {trigger_name}")

    def register_action(self, action_name: str, action_class: Any) -> None:
        """Register an action class."""
        self.actions[action_name] = action_class
        logger.info(f"Registered action: {action_name}")

    def register_operation(self, operation_name: str, operation_class: Any) -> None:
        """Register an operation class."""
        self.operations[operation_name] = operation_class
        logger.info(f"Registered operation: {operation_name}")

    def add_execution_callback(self, callback: Callable) -> None:
        """Add a callback for execution events."""
        self.execution_callbacks.append(callback)

    async def execute_flow(
        self,
        flow_data: Dict[str, Any],
        user_id: str,
        execution_id: Optional[str] = None
    ) -> ExecutionContext:
        """Execute a complete workflow.

        Args:
            flow_data: The workflow definition containing nodes and edges
            user_id: ID of the user executing the flow
            execution_id: Optional execution ID, generated if not provided

        Returns:
            ExecutionContext with the execution results

        Raises:
            WorkflowExecutionError: If workflow execution fails
        """
        flow_id = flow_data.get("id", "unknown_flow")
        execution_id = execution_id or str(uuid.uuid4())

        # Create execution context
        context = ExecutionContext(
            flow_id=flow_id,
            execution_id=execution_id,
            user_id=user_id,
            status="running"
        )

        # Add to active executions
        self.active_executions[execution_id] = context

        try:
            # Notify callbacks
            await self._notify_execution_callbacks("started", context)

            # Validate flow structure
            self._validate_flow_structure(flow_data)

            # Execute the workflow
            await self._execute_workflow_nodes(flow_data, context)

            # Mark as completed
            context.mark_completed()
            logger.info(f"Workflow {flow_id} execution {execution_id} completed successfully")

        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            context.mark_failed(error_msg)
            logger.error(f"Workflow {flow_id} execution {execution_id} failed: {e}")

            # Re-raise as WorkflowExecutionError
            raise WorkflowExecutionError(
                flow_id, execution_id, error_msg,
                {"original_error": str(e), "context": context.to_dict()}
            ) from e

        finally:
            # Move to history and notify
            self.execution_history.append(context)
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]

            await self._notify_execution_callbacks("completed", context)

        return context

    async def execute_node(
        self,
        node_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute a single workflow node.

        Args:
            node_data: The node configuration
            context: The execution context

        Returns:
            Node execution result

        Raises:
            NodeExecutionError: If node execution fails
        """
        node_type = node_data.get("type", "").lower()

        # Get appropriate registry based on node type
        registry = None
        if node_type == "action":
            registry = self.actions
        elif node_type == "trigger":
            registry = self.triggers
        elif node_type == "operation":
            registry = self.operations

        # Execute the node
        result = await self.executor.execute_node(node_data, context, registry)
        return result.output

    def get_execution_context(self, execution_id: str) -> Optional[ExecutionContext]:
        """Get an execution context by ID."""
        return self.active_executions.get(execution_id)

    def get_execution_history(
        self,
        flow_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[ExecutionContext]:
        """Get execution history with optional filtering."""
        history = self.execution_history

        if flow_id:
            history = [ctx for ctx in history if ctx.flow_id == flow_id]

        if user_id:
            history = [ctx for ctx in history if ctx.user_id == user_id]

        return history[-limit:]

    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        context = self.active_executions.get(execution_id)
        if context and context.status == "running":
            context.mark_cancelled()
            logger.info(f"Cancelled execution {execution_id}")
            return True
        return False

    def _validate_flow_structure(self, flow_data: Dict[str, Any]) -> None:
        """Validate the structure of flow data."""
        if "nodes" not in flow_data:
            raise ValueError("Flow data must contain 'nodes'")

        if "edges" not in flow_data:
            raise ValueError("Flow data must contain 'edges'")

        nodes = flow_data["nodes"]
        if not isinstance(nodes, list) or not nodes:
            raise ValueError("Flow must contain at least one node")

        # Validate each node has required fields
        for node in nodes:
            if not isinstance(node, dict):
                raise ValueError("Each node must be a dictionary")

            required_fields = ["id", "type"]
            for field in required_fields:
                if field not in node:
                    raise ValueError(f"Node missing required field: {field}")

    async def _execute_workflow_nodes(
        self,
        flow_data: Dict[str, Any],
        context: ExecutionContext
    ) -> None:
        """Execute all nodes in the workflow according to their connections."""
        nodes = {node["id"]: node for node in flow_data["nodes"]}
        edges = flow_data["edges"]

        # For now, implement simple sequential execution
        # TODO: Implement proper DAG-based execution with parallel processing

        executed_nodes = set()
        max_iterations = len(nodes)  # Prevent infinite loops

        for _ in range(max_iterations):
            # Find nodes that can be executed (all dependencies satisfied)
            executable_nodes = self._find_executable_nodes(nodes, edges, executed_nodes)

            if not executable_nodes:
                break

            # Execute nodes (in parallel for now)
            tasks = []
            for node_id in executable_nodes:
                task = self.execute_node(nodes[node_id], context)
                tasks.append(task)

            # Wait for all nodes to complete
            if tasks:
                await asyncio.gather(*tasks)

            # Mark nodes as executed
            executed_nodes.update(executable_nodes)

        # Check if all nodes were executed
        if len(executed_nodes) != len(nodes):
            raise WorkflowExecutionError(
                context.flow_id, context.execution_id,
                "Not all nodes could be executed - possible circular dependency or unreachable nodes"
            )

    def _find_executable_nodes(
        self,
        nodes: Dict[str, Dict[str, Any]],
        edges: List[Dict[str, Any]],
        executed_nodes: set
    ) -> List[str]:
        """Find nodes that can be executed (all dependencies satisfied)."""
        executable = []

        for node_id, node_data in nodes.items():
            if node_id in executed_nodes:
                continue

            # Check if all incoming edges are satisfied
            dependencies_satisfied = True

            for edge in edges:
                if edge.get("target") == node_id:
                    source_node = edge.get("source")
                    if source_node and source_node not in executed_nodes:
                        dependencies_satisfied = False
                        break

            if dependencies_satisfied:
                executable.append(node_id)

        return executable

    async def _notify_execution_callbacks(self, event: str, context: ExecutionContext) -> None:
        """Notify all execution callbacks of an event."""
        for callback in self.execution_callbacks:
            try:
                await callback(event, context)
            except Exception as e:
                logger.error(f"Error in execution callback: {e}")

    # Trigger management methods
    async def start_trigger(self, trigger_name: str, config: Dict[str, Any]) -> str:
        """Start a trigger with the given configuration."""
        if trigger_name not in self.triggers:
            raise ValueError(f"Trigger '{trigger_name}' not registered")

        trigger_class = self.triggers[trigger_name]
        trigger_instance = trigger_class(config)

        # Create callback for when trigger fires
        async def trigger_callback(context: ExecutionContext):
            await self._handle_trigger_event(trigger_name, context)

        await trigger_instance.start(trigger_callback)

        # For scheduled triggers, add to scheduler
        if hasattr(trigger_instance, 'schedule_config'):
            job_id = self.scheduler.add_job(
                trigger_id=f"{trigger_name}_{id(trigger_instance)}",
                cron_expression=trigger_instance.schedule_config,
                callback=trigger_callback,
                metadata={"trigger_name": trigger_name, "config": config}
            )
            return job_id

        return f"{trigger_name}_{id(trigger_instance)}"

    async def _handle_trigger_event(self, trigger_name: str, context: ExecutionContext) -> None:
        """Handle when a trigger fires."""
        logger.info(f"Trigger {trigger_name} fired for flow {context.flow_id}")

        # This would typically start a workflow execution
        # For now, just log the event
        await self._notify_execution_callbacks("trigger_fired", context)
