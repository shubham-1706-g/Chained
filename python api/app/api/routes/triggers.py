"""Triggers API Routes

This module contains FastAPI routes for trigger management.
Provides endpoints for creating, configuring, and managing workflow triggers.
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from ...core.engine import WorkflowEngine
from ...triggers.webhook import WebhookTrigger
from ...triggers.schedule import ScheduleTrigger
from ...triggers.file_watch import FileWatchTrigger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/triggers", tags=["triggers"])


# Pydantic models for request/response
class TriggerConfig(BaseModel):
    """Configuration for a trigger."""
    trigger_type: str = Field(..., description="Type of trigger (webhook, schedule, file_watch)")
    config: Dict[str, Any] = Field(..., description="Trigger-specific configuration")
    user_id: str = Field(..., description="ID of the user creating the trigger")


class TriggerResponse(BaseModel):
    """Response model for trigger operations."""
    trigger_id: str
    trigger_type: str
    status: str
    config: Dict[str, Any]
    message: str


class TriggerStatus(BaseModel):
    """Status information for a trigger."""
    trigger_id: str
    trigger_type: str
    is_running: bool
    last_triggered: Optional[str]
    config: Dict[str, Any]
    connection_id: Optional[str]


# Trigger registry
TRIGGER_CLASSES = {
    "webhook": WebhookTrigger,
    "schedule": ScheduleTrigger,
    "file_watch": FileWatchTrigger
}


# Dependency injection
def get_workflow_engine() -> WorkflowEngine:
    """Get workflow engine instance."""
    from ...core.engine import WorkflowEngine
    engine = WorkflowEngine()
    return engine


@router.post("/create", response_model=TriggerResponse)
async def create_trigger(
    trigger_config: TriggerConfig,
    background_tasks: BackgroundTasks,
    engine: WorkflowEngine = Depends(get_workflow_engine)
) -> TriggerResponse:
    """Create and start a new trigger."""
    try:
        trigger_type = trigger_config.trigger_type
        config = trigger_config.config
        user_id = trigger_config.user_id

        # Add user_id to config if not present
        config["user_id"] = user_id

        # Get trigger class
        if trigger_type not in TRIGGER_CLASSES:
            available_triggers = list(TRIGGER_CLASSES.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Unknown trigger type: {trigger_type}. Available: {available_triggers}"
            )

        trigger_class = TRIGGER_CLASSES[trigger_type]

        # Create trigger instance
        trigger_instance = trigger_class(config)

        # Validate configuration
        await trigger_instance.validate_config()

        # Register trigger with engine
        engine.register_trigger(trigger_type, trigger_class)

        # Start the trigger in background
        background_tasks.add_task(
            _start_trigger_background,
            engine,
            trigger_type,
            config
        )

        return TriggerResponse(
            trigger_id=f"{trigger_type}_{trigger_instance.trigger_id}",
            trigger_type=trigger_type,
            status="starting",
            config={k: v for k, v in config.items() if k != "credentials"},  # Exclude sensitive data
            message=f"{trigger_type.title()} trigger created and starting"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating trigger: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/test/{trigger_type}")
async def test_trigger_config(
    trigger_type: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Test a trigger configuration without starting it."""
    try:
        if trigger_type not in TRIGGER_CLASSES:
            available_triggers = list(TRIGGER_CLASSES.keys())
            raise HTTPException(
                status_code=400,
                detail=f"Unknown trigger type: {trigger_type}. Available: {available_triggers}"
            )

        trigger_class = TRIGGER_CLASSES[trigger_type]
        trigger_instance = trigger_class(config)

        # Validate configuration
        await trigger_instance.validate_config()

        # Test connection/setup
        test_result = await trigger_instance.test_connection()

        return {
            "valid": True,
            "connection_test": test_result,
            "message": f"{trigger_type.title()} trigger configuration is valid",
            "config_summary": trigger_instance.get_status()
        }

    except ValueError as e:
        return {
            "valid": False,
            "connection_test": False,
            "error": str(e),
            "message": f"{trigger_type.title()} trigger configuration is invalid"
        }
    except Exception as e:
        logger.error(f"Error testing trigger config: {e}")
        return {
            "valid": False,
            "connection_test": False,
            "error": "Internal server error",
            "message": "Failed to test trigger configuration"
        }


@router.get("/types")
async def get_trigger_types() -> Dict[str, Any]:
    """Get available trigger types and their configurations."""
    try:
        trigger_info = {}

        for trigger_type, trigger_class in TRIGGER_CLASSES.items():
            # Create a dummy instance to get schema information
            dummy_config = {"user_id": "test"}
            try:
                dummy_instance = trigger_class(dummy_config)
                trigger_info[trigger_type] = {
                    "description": f"{trigger_type.title()} trigger",
                    "config_schema": dummy_instance.get_schema()
                }
            except:
                # If we can't create a dummy instance, provide basic info
                trigger_info[trigger_type] = {
                    "description": f"{trigger_type.title()} trigger",
                    "config_schema": {"type": "object", "properties": {}}
                }

        return {
            "triggers": trigger_info,
            "total": len(trigger_info)
        }

    except Exception as e:
        logger.error(f"Error getting trigger types: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/webhook/{webhook_id}/status")
async def get_webhook_trigger_status(
    webhook_id: str,
    engine: WorkflowEngine = Depends(get_workflow_engine)
) -> Dict[str, Any]:
    """Get the status of a specific webhook trigger."""
    try:
        # This is a simplified implementation
        # In production, you'd maintain a registry of active triggers
        return {
            "webhook_id": webhook_id,
            "status": "unknown",
            "message": "Trigger status tracking not fully implemented",
            "note": "This endpoint is a placeholder for future implementation"
        }

    except Exception as e:
        logger.error(f"Error getting webhook status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/webhook/{webhook_id}")
async def delete_webhook_trigger(
    webhook_id: str,
    engine: WorkflowEngine = Depends(get_workflow_engine)
) -> Dict[str, str]:
    """Delete a webhook trigger."""
    try:
        # This is a simplified implementation
        # In production, you'd properly stop and cleanup the trigger
        return {
            "message": f"Webhook trigger {webhook_id} deletion not fully implemented",
            "note": "This endpoint is a placeholder for future implementation"
        }

    except Exception as e:
        logger.error(f"Error deleting webhook trigger: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/schedule/next-run")
async def get_schedule_trigger_next_run(
    trigger_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate the next run time for a schedule trigger configuration."""
    try:
        if "schedule" not in trigger_config:
            raise HTTPException(status_code=400, detail="schedule configuration required")

        schedule_trigger = ScheduleTrigger(trigger_config)
        next_run = schedule_trigger.get_next_run_time()

        return {
            "next_run": next_run.isoformat() if next_run else None,
            "schedule": trigger_config["schedule"],
            "timezone": trigger_config.get("timezone", "UTC")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating next run: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/file-watch/scan")
async def scan_file_watch_paths(
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Scan file watch paths and return current file information."""
    try:
        if "watch_paths" not in config:
            raise HTTPException(status_code=400, detail="watch_paths required")

        file_trigger = FileWatchTrigger(config)

        # Get file states (this would normally be done during setup)
        file_states = {}
        for path in config["watch_paths"]:
            # This is a simplified version
            file_states[path] = {
                "exists": file_trigger._test_path_exists(path),
                "file_count": "unknown"  # Would need to implement proper scanning
            }

        return {
            "scan_complete": True,
            "paths_scanned": config["watch_paths"],
            "file_states": file_states,
            "message": "File watch scan completed"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning file watch paths: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def _start_trigger_background(
    engine: WorkflowEngine,
    trigger_type: str,
    config: Dict[str, Any]
) -> None:
    """Start a trigger in the background."""
    try:
        # Start the trigger
        trigger_id = await engine.start_trigger(trigger_type, config)
        logger.info(f"Trigger {trigger_type} started with ID: {trigger_id}")

    except Exception as e:
        logger.error(f"Error starting trigger {trigger_type}: {e}")
        # In production, you'd want to update trigger status and send notifications
