"""Dependency Injection Module

This module provides dependency injection and service management for the FlowForge API.
It handles the creation and lifecycle management of core services and components.
"""

import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from fastapi import Request, HTTPException, Depends

from ..core.engine import WorkflowEngine
from ..core.executor import NodeExecutor
from ..core.scheduler import WorkflowScheduler

logger = logging.getLogger(__name__)


# Global service instances (in production, use proper DI framework)
_services: Optional[Dict[str, Any]] = None


@asynccontextmanager
async def lifespan(app):
    """Application lifespan context manager."""
    # Startup
    await startup_event()
    yield
    # Shutdown
    await shutdown_event()


async def startup_event():
    """Initialize services on application startup."""
    global _services

    try:
        logger.info("Initializing FlowForge services...")

        # Initialize core services
        workflow_engine = WorkflowEngine()
        node_executor = NodeExecutor()
        scheduler = WorkflowScheduler()

        # Initialize the workflow engine
        await workflow_engine.initialize()

        # Register sample triggers and actions
        await _register_sample_components(workflow_engine)

        # Store services globally
        _services = {
            "workflow_engine": workflow_engine,
            "node_executor": node_executor,
            "scheduler": scheduler
        }

        logger.info("FlowForge services initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


async def shutdown_event():
    """Cleanup services on application shutdown."""
    global _services

    if _services:
        try:
            logger.info("Shutting down FlowForge services...")

            # Shutdown workflow engine
            if "workflow_engine" in _services:
                await _services["workflow_engine"].shutdown()

            # Shutdown scheduler
            if "scheduler" in _services:
                await _services["scheduler"].stop()

            logger.info("FlowForge services shutdown complete")

        except Exception as e:
            logger.error(f"Error during service shutdown: {e}")
        finally:
            _services = None


async def _register_sample_components(engine: WorkflowEngine):
    """Register sample triggers and actions with the engine."""
    try:
        # Import trigger components
        from ..triggers.webhook import WebhookTrigger
        from ..triggers.schedule import ScheduleTrigger
        from ..triggers.file_watch import FileWatchTrigger
        from ..triggers.notion.database_trigger import NotionDatabaseTrigger
        from ..triggers.telegram.message_trigger import TelegramMessageTrigger
        from ..triggers.calendar.event_trigger import CalendarEventTrigger

        # Import action components
        from ..actions.http_action import HTTPAction
        from ..actions.ai.openai_action import OpenAIAction
        from ..actions.ai.claude_action import ClaudeAction
        from ..actions.ai.gemini_action import GeminiAction
        from ..actions.email.send_email import SendEmailAction
        from ..actions.email.parse_email import ParseEmailAction
        from ..actions.notion.database_action import NotionDatabaseAction
        from ..actions.notion.page_action import NotionPageAction
        from ..actions.telegram.chat_action import TelegramChatAction
        from ..actions.calendar.event_action import CalendarEventAction
        from ..actions.storage.google_drive import GoogleDriveAction
        from ..actions.storage.s3_upload import S3UploadAction
        from ..actions.data.transform import DataTransformAction
        from ..actions.data.filter import DataFilterAction
        from ..actions.data.aggregate import DataAggregateAction
        from ..actions.ai_agent.structured_output import StructuredOutputAction
        from ..actions.ai_agent.memory_action import MemoryAction

        # Register triggers
        engine.register_trigger("webhook", WebhookTrigger)
        engine.register_trigger("schedule", ScheduleTrigger)
        engine.register_trigger("file_watch", FileWatchTrigger)
        engine.register_trigger("notion_database", NotionDatabaseTrigger)
        engine.register_trigger("telegram_message", TelegramMessageTrigger)
        engine.register_trigger("calendar_event", CalendarEventTrigger)

        # Register actions
        # HTTP and web actions
        engine.register_action("http", HTTPAction)
        engine.register_action("webhook_response", HTTPAction)  # Can reuse HTTP action

        # AI actions
        engine.register_action("openai", OpenAIAction)
        engine.register_action("claude", ClaudeAction)
        engine.register_action("gemini", GeminiAction)

        # Email actions
        engine.register_action("send_email", SendEmailAction)
        engine.register_action("parse_email", ParseEmailAction)

        # Notion actions
        engine.register_action("notion_database", NotionDatabaseAction)
        engine.register_action("notion_page", NotionPageAction)

        # Telegram actions
        engine.register_action("telegram_chat", TelegramChatAction)

        # Calendar actions
        engine.register_action("calendar_event", CalendarEventAction)

        # Storage actions
        engine.register_action("google_drive", GoogleDriveAction)
        engine.register_action("s3_upload", S3UploadAction)

        # Data processing actions
        engine.register_action("data_transform", DataTransformAction)
        engine.register_action("data_filter", DataFilterAction)
        engine.register_action("data_aggregate", DataAggregateAction)

        # AI Agent actions
        engine.register_action("structured_output", StructuredOutputAction)
        engine.register_action("memory", MemoryAction)

        logger.info("All components registered successfully")

    except Exception as e:
        logger.error(f"Failed to register sample components: {e}")
        # Don't raise - allow application to start even if some components fail to register


def get_workflow_engine() -> WorkflowEngine:
    """Get the workflow engine instance."""
    if not _services or "workflow_engine" not in _services:
        raise HTTPException(
            status_code=503,
            detail="Workflow engine not available"
        )
    return _services["workflow_engine"]


def get_node_executor() -> NodeExecutor:
    """Get the node executor instance."""
    if not _services or "node_executor" not in _services:
        raise HTTPException(
            status_code=503,
            detail="Node executor not available"
        )
    return _services["node_executor"]


def get_scheduler() -> WorkflowScheduler:
    """Get the scheduler instance."""
    if not _services or "scheduler" not in _services:
        raise HTTPException(
            status_code=503,
            detail="Scheduler not available"
        )
    return _services["scheduler"]


async def get_service_health() -> Dict[str, Any]:
    """Get health status of all services."""
    health_status = {
        "overall": "healthy",
        "services": {},
        "timestamp": None  # Will be set by calling endpoint
    }

    if not _services:
        health_status["overall"] = "unhealthy"
        health_status["error"] = "Services not initialized"
        return health_status

    try:
        # Check workflow engine
        engine = _services.get("workflow_engine")
        if engine:
            # Test engine health by checking if it's initialized
            health_status["services"]["workflow_engine"] = "healthy"
        else:
            health_status["services"]["workflow_engine"] = "unhealthy"
            health_status["overall"] = "unhealthy"

        # Check scheduler
        scheduler = _services.get("scheduler")
        if scheduler:
            health_status["services"]["scheduler"] = "healthy"
        else:
            health_status["services"]["scheduler"] = "unhealthy"
            health_status["overall"] = "unhealthy"

        # Check executor
        executor = _services.get("node_executor")
        if executor:
            health_status["services"]["node_executor"] = "healthy"
        else:
            health_status["services"]["node_executor"] = "unhealthy"
            health_status["overall"] = "unhealthy"

    except Exception as e:
        logger.error(f"Error checking service health: {e}")
        health_status["overall"] = "unhealthy"
        health_status["error"] = str(e)

    return health_status


# Request-scoped dependencies
async def get_request_context(request: Request) -> Dict[str, Any]:
    """Extract context information from the request."""
    return {
        "user_id": request.headers.get("X-User-ID", "anonymous"),
        "request_id": request.headers.get("X-Request-ID", "unknown"),
        "user_agent": request.headers.get("User-Agent", "unknown"),
        "client_ip": request.client.host if request.client else "unknown"
    }


# Authentication dependencies (placeholder for future implementation)
async def get_current_user(request: Request) -> str:
    """Get current user from request (placeholder)."""
    # In a real implementation, this would validate JWT tokens
    # and extract user information
    user_id = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not user_id:
        user_id = request.headers.get("X-User-ID", "anonymous")
    return user_id


async def require_authenticated_user(current_user: str = Depends(get_current_user)) -> str:
    """Require an authenticated user."""
    if current_user == "anonymous":
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    return current_user


# Rate limiting dependencies (placeholder for future implementation)
class RateLimiter:
    """Simple rate limiter (placeholder for production implementation)."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}

    async def check_rate_limit(self, key: str) -> bool:
        """Check if request is within rate limits."""
        # This is a very simple implementation
        # In production, you'd use Redis or similar for distributed rate limiting
        import time
        current_time = int(time.time() / 60)  # Current minute

        if key not in self.requests:
            self.requests[key] = []

        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time >= current_time - 1
        ]

        # Check limit
        if len(self.requests[key]) >= self.requests_per_minute:
            return False

        # Add current request
        self.requests[key].append(current_time)
        return True


_rate_limiter = RateLimiter()


async def check_rate_limit(
    request: Request,
    user_id: str = Depends(get_current_user)
) -> None:
    """Check rate limit for the request."""
    client_key = f"{user_id}_{request.client.host if request.client else 'unknown'}"

    if not await _rate_limiter.check_rate_limit(client_key):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )


# Validation dependencies
def validate_flow_data(flow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate flow data structure."""
    if not isinstance(flow_data, dict):
        raise HTTPException(status_code=400, detail="Flow data must be a dictionary")

    required_fields = ["nodes", "edges"]
    for field in required_fields:
        if field not in flow_data:
            raise HTTPException(
                status_code=400,
                detail=f"Flow data must contain '{field}'"
            )

    return flow_data


def validate_node_data(node_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate individual node data."""
    if not isinstance(node_data, dict):
        raise HTTPException(status_code=400, detail="Node data must be a dictionary")

    required_fields = ["id", "type"]
    for field in required_fields:
        if field not in node_data:
            raise HTTPException(
                status_code=400,
                detail=f"Node data must contain '{field}'"
            )

    return node_data
