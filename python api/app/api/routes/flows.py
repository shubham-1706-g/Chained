"""Flows API Routes

This module contains FastAPI routes for workflow execution and management.
Provides endpoints for executing flows, checking execution status, and managing workflow lifecycle.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
import uuid

from ...core.engine import WorkflowEngine, WorkflowExecutionError
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flows", tags=["flows"])


# Pydantic models for request/response
class FlowExecutionRequest(BaseModel):
    """Request model for flow execution."""
    flow_id: str = Field(..., description="Unique identifier for the flow")
    user_id: str = Field(..., description="ID of the user executing the flow")
    execution_id: Optional[str] = Field(None, description="Optional custom execution ID")
    input_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Input data for the flow")
    flow_data: Optional[Dict[str, Any]] = Field(None, description="Complete flow definition")


class FlowExecutionResponse(BaseModel):
    """Response model for flow execution."""
    execution_id: str
    flow_id: str
    user_id: str
    status: str
    start_time: str
    message: str


class ExecutionStatusResponse(BaseModel):
    """Response model for execution status."""
    execution_id: str
    flow_id: str
    user_id: str
    status: str
    start_time: Optional[str]
    end_time: Optional[str]
    error_message: Optional[str]
    variables: Dict[str, Any]
    node_execution_times: Dict[str, float]


class ExecutionHistoryResponse(BaseModel):
    """Response model for execution history."""
    executions: list[ExecutionStatusResponse]
    total: int
    page: int
    page_size: int


# Dependency injection
def get_workflow_engine() -> WorkflowEngine:
    """Get workflow engine instance.

    In a real application, this would be properly injected
    through a dependency injection framework.
    """
    # This is a simplified version - in production, you'd have
    # proper dependency injection and singleton management
    from ...core.engine import WorkflowEngine
    engine = WorkflowEngine()
    # In production, you'd initialize this once and reuse
    return engine


@router.post("/execute", response_model=FlowExecutionResponse)
async def execute_flow(
    request: FlowExecutionRequest,
    background_tasks: BackgroundTasks,
    engine: WorkflowEngine = Depends(get_workflow_engine)
) -> FlowExecutionResponse:
    """Execute a workflow.

    Triggers the execution of a workflow in the background and returns
    immediately with execution details.
    """
    try:
        # For now, we'll need flow_data to be provided
        # In production, you'd fetch this from a database
        if not request.flow_data:
            raise HTTPException(
                status_code=400,
                detail="flow_data is required for execution"
            )

        # Add input data to flow data
        flow_data = request.flow_data.copy()
        if request.input_data:
            flow_data["input_data"] = request.input_data

        # Execute the flow asynchronously
        background_tasks.add_task(
            _execute_flow_background,
            engine,
            flow_data,
            request.user_id,
            request.execution_id
        )

        execution_id = request.execution_id or str(uuid.uuid4())

        return FlowExecutionResponse(
            execution_id=execution_id,
            flow_id=request.flow_id,
            user_id=request.user_id,
            status="running",
            start_time="",  # Will be set when execution actually starts
            message="Flow execution started"
        )

    except WorkflowExecutionError as e:
        logger.error(f"Flow execution failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during flow execution: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/execution/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(
    execution_id: str,
    engine: WorkflowEngine = Depends(get_workflow_engine)
) -> ExecutionStatusResponse:
    """Get the status of a workflow execution."""
    try:
        context = engine.get_execution_context(execution_id)
        if not context:
            raise HTTPException(status_code=404, detail="Execution not found")

        return ExecutionStatusResponse(
            execution_id=context.execution_id,
            flow_id=context.flow_id,
            user_id=context.user_id,
            status=context.status,
            start_time=context.start_time.isoformat() if context.start_time else None,
            end_time=context.end_time.isoformat() if context.end_time else None,
            error_message=context.error_message,
            variables=context.variables,
            node_execution_times=context.node_execution_times
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/execution/{execution_id}")
async def cancel_execution(
    execution_id: str,
    engine: WorkflowEngine = Depends(get_workflow_engine)
) -> Dict[str, str]:
    """Cancel a running workflow execution."""
    try:
        success = engine.cancel_execution(execution_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Execution not found or not running"
            )

        return {"message": f"Execution {execution_id} cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling execution: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/executions", response_model=ExecutionHistoryResponse)
async def get_execution_history(
    flow_id: Optional[str] = None,
    user_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    engine: WorkflowEngine = Depends(get_workflow_engine)
) -> ExecutionHistoryResponse:
    """Get execution history with optional filtering."""
    try:
        if page < 1:
            raise HTTPException(status_code=400, detail="Page must be >= 1")
        if page_size < 1 or page_size > 100:
            raise HTTPException(status_code=400, detail="Page size must be between 1 and 100")

        # Get execution history
        history = engine.get_execution_history(
            flow_id=flow_id,
            user_id=user_id,
            limit=page_size * page
        )

        # Paginate results
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_history = history[start_idx:end_idx]

        # Convert to response format
        executions = []
        for context in paginated_history:
            executions.append(ExecutionStatusResponse(
                execution_id=context.execution_id,
                flow_id=context.flow_id,
                user_id=context.user_id,
                status=context.status,
                start_time=context.start_time.isoformat() if context.start_time else None,
                end_time=context.end_time.isoformat() if context.end_time else None,
                error_message=context.error_message,
                variables=context.variables,
                node_execution_times=context.node_execution_times
            ))

        return ExecutionHistoryResponse(
            executions=executions,
            total=len(history),
            page=page,
            page_size=page_size
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting execution history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/validate")
async def validate_flow(
    flow_data: Dict[str, Any],
    engine: WorkflowEngine = Depends(get_workflow_engine)
) -> Dict[str, Any]:
    """Validate a flow definition without executing it."""
    try:
        # This is a simplified validation
        # In production, you'd have more comprehensive validation

        if "nodes" not in flow_data:
            raise HTTPException(status_code=400, detail="Flow must contain 'nodes'")

        if "edges" not in flow_data:
            raise HTTPException(status_code=400, detail="Flow must contain 'edges'")

        nodes = flow_data["nodes"]
        if not isinstance(nodes, list) or not nodes:
            raise HTTPException(status_code=400, detail="Flow must contain at least one node")

        # Validate each node
        for node in nodes:
            if not isinstance(node, dict):
                raise HTTPException(status_code=400, detail="Each node must be a dictionary")

            required_fields = ["id", "type"]
            for field in required_fields:
                if field not in node:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Node missing required field: {field}"
                    )

        return {
            "valid": True,
            "message": "Flow validation successful",
            "node_count": len(nodes),
            "edge_count": len(flow_data.get("edges", []))
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating flow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def _execute_flow_background(
    engine: WorkflowEngine,
    flow_data: Dict[str, Any],
    user_id: str,
    execution_id: Optional[str] = None
) -> None:
    """Execute a flow in the background."""
    try:
        # Extract execution inputs
        input_data = flow_data.pop("input_data", {})

        # Execute the flow
        context = await engine.execute_flow(
            flow_data=flow_data,
            user_id=user_id,
            execution_id=execution_id
        )

        logger.info(f"Background flow execution completed: {context.execution_id}")

    except Exception as e:
        logger.error(f"Background flow execution failed: {e}")
        # In production, you'd want to update the execution status in a database
        # and possibly send notifications
