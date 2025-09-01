"""Actions API Routes

This module contains FastAPI routes for action management.
Provides endpoints for executing actions, testing configurations, and managing action lifecycle.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ...core.engine import WorkflowEngine
from ...core.context import ExecutionContext
from ...actions.http_action import HTTPAction
from ...actions.ai.openai_action import OpenAIAction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/actions", tags=["actions"])


# Pydantic models for request/response
class ActionExecutionRequest(BaseModel):
    """Request model for action execution."""
    action_type: str = Field(..., description="Type of action to execute")
    config: Dict[str, Any] = Field(..., description="Action configuration")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for the action")
    user_id: str = Field(..., description="ID of the user executing the action")


class ActionExecutionResponse(BaseModel):
    """Response model for action execution."""
    success: bool
    action_type: str
    execution_time: Optional[float]
    result: Dict[str, Any]
    error: Optional[str]


class ActionTestRequest(BaseModel):
    """Request model for action testing."""
    action_type: str = Field(..., description="Type of action to test")
    config: Dict[str, Any] = Field(..., description="Action configuration")


class ActionTestResponse(BaseModel):
    """Response model for action testing."""
    valid: bool
    connection_test: bool
    action_schema: Dict[str, Any]
    error: Optional[str]
    message: str


# Action registry
ACTION_CLASSES = {
    "http": HTTPAction,
    "openai": OpenAIAction
}


# Dependency injection
def get_workflow_engine() -> WorkflowEngine:
    """Get workflow engine instance."""
    from ...core.engine import WorkflowEngine
    engine = WorkflowEngine()
    return engine


@router.post("/execute", response_model=ActionExecutionResponse)
async def execute_action(
    request: ActionExecutionRequest,
    engine: WorkflowEngine = Depends(get_workflow_engine)
) -> ActionExecutionResponse:
    """Execute an action directly."""
    try:
        action_type = request.action_type
        config = request.config
        input_data = request.input_data

        # Get action class
        if action_type not in ACTION_CLASSES:
            available_actions = list(ACTION_CLASSES.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Unknown action type: {action_type}. Available: {available_actions}"
            )

        action_class = ACTION_CLASSES[action_type]

        # Create action instance
        action_instance = action_class(config)

        # Validate configuration
        await action_instance.validate_config()

        # Register action with engine
        engine.register_action(action_type, action_class)

        # Create execution context
        context = ExecutionContext(
            flow_id=f"direct_action_{action_type}",
            execution_id=f"action_{request.user_id}",
            user_id=request.user_id
        )

        # Execute the action
        import time
        start_time = time.time()
        result = await action_instance.execute(input_data, context)
        execution_time = time.time() - start_time

        return ActionExecutionResponse(
            success=True,
            action_type=action_type,
            execution_time=execution_time,
            result=result,
            error=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing action: {e}")
        return ActionExecutionResponse(
            success=False,
            action_type=request.action_type,
            execution_time=None,
            result={},
            error=str(e)
        )


@router.post("/test", response_model=ActionTestResponse)
async def test_action_config(
    request: ActionTestRequest
) -> ActionTestResponse:
    """Test an action configuration."""
    try:
        action_type = request.action_type
        config = request.config

        if action_type not in ACTION_CLASSES:
            available_actions = list(ACTION_CLASSES.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Unknown action type: {action_type}. Available: {available_actions}"
            )

        action_class = ACTION_CLASSES[action_type]
        action_instance = action_class(config)

        # Validate configuration
        await action_instance.validate_config()

        # Test connection
        connection_test = await action_instance.test_connection()

        return ActionTestResponse(
            valid=True,
            connection_test=connection_test,
            action_schema=action_instance.get_schema(),
            error=None,
            message=f"{action_type.title()} action configuration is valid"
        )

    except ValueError as e:
        return ActionTestResponse(
            valid=False,
            connection_test=False,
            action_schema={},
            error=str(e),
            message=f"{action_type.title()} action configuration is invalid"
        )
    except Exception as e:
        logger.error(f"Error testing action config: {e}")
        return ActionTestResponse(
            valid=False,
            connection_test=False,
            action_schema={},
            error="Internal server error",
            message="Failed to test action configuration"
        )


@router.get("/types")
async def get_action_types() -> Dict[str, Any]:
    """Get available action types and their configurations."""
    try:
        action_info = {}

        for action_type, action_class in ACTION_CLASSES.items():
            # Create a dummy instance to get schema information
            dummy_config = {"user_id": "test"}
            try:
                dummy_instance = action_class(dummy_config)
                action_info[action_type] = {
                    "description": f"{action_type.title()} action",
                    "config_schema": dummy_instance.get_schema()
                }
            except:
                # If we can't create a dummy instance, provide basic info
                action_info[action_type] = {
                    "description": f"{action_type.title()} action",
                    "config_schema": {"type": "object", "properties": {}}
                }

        return {
            "actions": action_info,
            "total": len(action_info)
        }

    except Exception as e:
        logger.error(f"Error getting action types: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/http/test-request")
async def test_http_request(
    config: Dict[str, Any],
    test_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Test an HTTP request configuration."""
    try:
        http_action = HTTPAction(config)

        # Validate config
        await http_action.validate_config()

        # Test connection
        connection_ok = await http_action.test_connection()

        # If test data provided, make a test request
        if test_data:
            from ...core.context import ExecutionContext
            context = ExecutionContext(
                flow_id="http_test",
                execution_id="test_request",
                user_id="test_user"
            )

            test_result = await http_action.execute(test_data, context)
            return {
                "config_valid": True,
                "connection_test": connection_ok,
                "test_request_made": True,
                "test_result": test_result
            }

        return {
            "config_valid": True,
            "connection_test": connection_ok,
            "test_request_made": False,
            "message": "HTTP configuration is valid"
        }

    except Exception as e:
        logger.error(f"Error testing HTTP request: {e}")
        return {
            "config_valid": False,
            "connection_test": False,
            "test_request_made": False,
            "error": str(e)
        }


@router.post("/openai/test-api")
async def test_openai_api(
    config: Dict[str, Any],
    test_message: Optional[str] = "Hello, test message"
) -> Dict[str, Any]:
    """Test OpenAI API configuration."""
    try:
        openai_action = OpenAIAction(config)

        # Validate config
        await openai_action.validate_config()

        # Test connection
        connection_ok = await openai_action.test_connection()

        # If test message provided, make a test request
        if test_message:
            from ...core.context import ExecutionContext
            context = ExecutionContext(
                flow_id="openai_test",
                execution_id="test_api",
                user_id="test_user"
            )

            test_input = {"message": test_message}
            test_result = await openai_action.execute(test_input, context)

            return {
                "config_valid": True,
                "connection_test": connection_ok,
                "test_request_made": True,
                "test_result": {
                    "success": test_result.get("success"),
                    "response_length": len(test_result.get("response", "")),
                    "model": test_result.get("model"),
                    "usage": test_result.get("usage")
                }
            }

        return {
            "config_valid": True,
            "connection_test": connection_ok,
            "test_request_made": False,
            "message": "OpenAI configuration is valid"
        }

    except Exception as e:
        logger.error(f"Error testing OpenAI API: {e}")
        return {
            "config_valid": False,
            "connection_test": False,
            "test_request_made": False,
            "error": str(e)
        }


@router.get("/http/methods")
async def get_http_methods() -> Dict[str, List[str]]:
    """Get available HTTP methods."""
    return {
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
        "description": "Supported HTTP methods for HTTP actions"
    }


@router.get("/openai/models")
async def get_openai_models() -> Dict[str, Any]:
    """Get available OpenAI models."""
    return {
        "chat_models": [
            "gpt-4", "gpt-4-turbo-preview", "gpt-4-vision-preview",
            "gpt-3.5-turbo", "gpt-3.5-turbo-16k"
        ],
        "completion_models": [
            "text-davinci-003", "text-curie-001", "text-babbage-001", "text-ada-001"
        ],
        "embedding_models": [
            "text-embedding-ada-002"
        ],
        "task_types": ["chat", "completion", "edit", "embedding"]
    }
