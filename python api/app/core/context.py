"""Execution Context Module

This module defines the execution context and state management for workflow execution.
The ExecutionContext tracks the state of a workflow execution including variables,
previous outputs, and execution metadata.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class ExecutionContext:
    """Execution context for workflow runs.

    Tracks the state and metadata of a single workflow execution,
    including variables, outputs, and execution information.
    """
    flow_id: str
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    variables: Dict[str, Any] = field(default_factory=dict)
    previous_outputs: List[Dict[str, Any]] = field(default_factory=list)
    current_node_id: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed, cancelled
    error_message: Optional[str] = None
    node_execution_times: Dict[str, float] = field(default_factory=dict)

    def set_variable(self, key: str, value: Any) -> None:
        """Set a workflow variable."""
        self.variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get a workflow variable with optional default value."""
        return self.variables.get(key, default)

    def add_node_output(self, node_id: str, output: Dict[str, Any], execution_time: float = 0.0) -> None:
        """Add output from a node execution."""
        output_entry = {
            "node_id": node_id,
            "output": output,
            "timestamp": datetime.utcnow().isoformat(),
            "execution_time": execution_time
        }
        self.previous_outputs.append(output_entry)
        self.node_execution_times[node_id] = execution_time

    def get_last_output(self, node_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the last output, optionally filtered by node_id."""
        if node_id:
            for output in reversed(self.previous_outputs):
                if output["node_id"] == node_id:
                    return output
            return None
        return self.previous_outputs[-1] if self.previous_outputs else None

    def get_node_outputs(self, node_id: str) -> List[Dict[str, Any]]:
        """Get all outputs from a specific node."""
        return [output for output in self.previous_outputs if output["node_id"] == node_id]

    def mark_completed(self) -> None:
        """Mark the execution as completed."""
        self.status = "completed"
        self.end_time = datetime.utcnow()

    def mark_failed(self, error_message: str) -> None:
        """Mark the execution as failed with an error message."""
        self.status = "failed"
        self.error_message = error_message
        self.end_time = datetime.utcnow()

    def mark_cancelled(self) -> None:
        """Mark the execution as cancelled."""
        self.status = "cancelled"
        self.end_time = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for serialization."""
        return {
            "flow_id": self.flow_id,
            "execution_id": self.execution_id,
            "user_id": self.user_id,
            "variables": self.variables,
            "previous_outputs": self.previous_outputs,
            "current_node_id": self.current_node_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "error_message": self.error_message,
            "node_execution_times": self.node_execution_times
        }


@dataclass
class NodeExecutionResult:
    """Result of a single node execution."""
    node_id: str
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "node_id": self.node_id,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat()
        }
