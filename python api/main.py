"""FlowForge Python API

Main application entry point for the FlowForge automation platform.
This API provides workflow execution, trigger management, and action orchestration.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import uvicorn

# Import application components
from app.api.routes import flows, triggers, actions
from app.api.dependencies import lifespan, get_service_health

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application with lifespan management
app = FastAPI(
    title="FlowForge Python API",
    description="Python API for FlowForge automation platform with workflow execution, triggers, and actions",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware with production-ready configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend and Node.js API
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(flows.router)
app.include_router(triggers.router)
app.include_router(actions.router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "FlowForge Python API is running",
        "version": "1.0.0",
        "documentation": "/docs",
        "components": {
            "flows": "Workflow execution and management",
            "triggers": "Event-driven trigger management",
            "actions": "Action execution and testing"
        }
    }


# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "FlowForge Python API",
        "version": "1.0.0"
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with service status"""
    health_status = await get_service_health()
    health_status["timestamp"] = datetime.utcnow().isoformat()

    # Set HTTP status code based on health
    status_code = 200 if health_status["overall"] == "healthy" else 503

    return JSONResponse(
        content=health_status,
        status_code=status_code
    )


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent error format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "path": str(request.url),
                "method": request.method
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "path": str(request.url),
                "method": request.method
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("FlowForge Python API starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("FlowForge Python API shutting down...")


# API information endpoint
@app.get("/api/v1/info")
async def api_info():
    """Get API information and available endpoints"""
    return {
        "name": "FlowForge Python API",
        "version": "1.0.0",
        "description": "Backend API for workflow automation platform",
        "endpoints": {
            "flows": {
                "execute": "POST /flows/execute",
                "status": "GET /flows/execution/{execution_id}",
                "history": "GET /flows/executions",
                "validate": "POST /flows/validate"
            },
            "triggers": {
                "create": "POST /triggers/create",
                "test": "POST /triggers/test/{trigger_type}",
                "types": "GET /triggers/types",
                "webhook_status": "GET /triggers/webhook/{webhook_id}/status"
            },
            "actions": {
                "execute": "POST /actions/execute",
                "test": "POST /actions/test",
                "types": "GET /actions/types"
            }
        },
        "available_actions": {
            "ai": ["openai", "claude", "gemini", "structured_output"],
            "communication": ["telegram_chat", "send_email", "parse_email"],
            "productivity": ["notion_database", "notion_page", "calendar_event"],
            "storage": ["google_drive", "s3_upload"],
            "data_processing": ["data_transform", "data_filter", "data_aggregate"],
            "web": ["http", "webhook_response"],
            "ai_agent": ["memory"]
        },
        "available_triggers": {
            "web": ["webhook"],
            "time": ["schedule"],
            "filesystem": ["file_watch"],
            "productivity": ["notion_database", "calendar_event"],
            "communication": ["telegram_message"]
        },
        "components": {
            "engine": "Workflow execution engine",
            "scheduler": "Time-based trigger scheduler",
            "executor": "Node execution handler",
            "memory": "AI agent memory system"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

