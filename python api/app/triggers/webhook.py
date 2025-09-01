"""Webhook Trigger

This module implements a webhook trigger that listens for HTTP requests
and triggers workflow executions based on incoming webhook data.
"""

import asyncio
import logging
import json
from typing import Any, Dict, Optional, Callable, Awaitable
from datetime import datetime

from .base import EventTrigger
from ..core.context import ExecutionContext

logger = logging.getLogger(__name__)


class WebhookTrigger(EventTrigger):
    """Webhook trigger that listens for HTTP webhook requests.

    This trigger creates an HTTP endpoint that can receive webhook
    requests from external services and trigger workflow executions.
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.webhook_url = config.get("webhook_url", "")
        self.secret_token = config.get("secret_token", "")
        self.http_method = config.get("method", "POST").upper()
        self.port = config.get("port", 8080)
        self.host = config.get("host", "localhost")
        self.server = None
        self.site = None

    async def validate_config(self) -> bool:
        """Validate webhook trigger configuration."""
        if not self.webhook_url:
            raise ValueError("webhook_url is required for webhook trigger")

        if self.http_method not in ["GET", "POST", "PUT", "PATCH"]:
            raise ValueError(f"Unsupported HTTP method: {self.http_method}")

        if not isinstance(self.port, int) or self.port < 1 or self.port > 65535:
            raise ValueError("port must be a valid port number (1-65535)")

        return True

    async def setup(self) -> None:
        """Set up the webhook HTTP server."""
        try:
            from aiohttp import web

            app = web.Application()
            app.router.add_route(
                self.http_method,
                self.webhook_url,
                self._handle_webhook_request
            )

            # Add health check endpoint
            app.router.add_get("/health", self._handle_health_check)

            self.server = web.AppRunner(app)
            await self.server.setup()

            self.site = web.TCPSite(self.server, self.host, self.port)
            await self.site.start()

            logger.info(f"Webhook server started on {self.host}:{self.port}{self.webhook_url}")

        except ImportError:
            raise RuntimeError("aiohttp is required for webhook trigger")
        except Exception as e:
            logger.error(f"Failed to setup webhook server: {e}")
            raise

    async def start(self, callback: Callable[[ExecutionContext], Awaitable[None]]) -> None:
        """Start the webhook trigger."""
        self.is_running = True
        self._callback = callback
        logger.info(f"Webhook trigger {self.trigger_id} started")

        # The webhook server is already running from setup()
        # We just need to keep the trigger alive
        while self.is_running:
            await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop the webhook trigger and cleanup server."""
        self.is_running = False

        if self.site:
            await self.site.stop()

        if self.server:
            await self.server.cleanup()

        logger.info(f"Webhook trigger {self.trigger_id} stopped")

    async def test_connection(self) -> bool:
        """Test webhook connectivity by making a test request."""
        try:
            import aiohttp

            test_url = f"http://{self.host}:{self.port}{self.webhook_url}"
            test_data = {"test": True, "timestamp": datetime.utcnow().isoformat()}

            async with aiohttp.ClientSession() as session:
                async with session.request(
                    self.http_method,
                    test_url,
                    json=test_data,
                    headers=self._get_headers()
                ) as response:
                    return response.status < 400
        except Exception as e:
            logger.error(f"Webhook connection test failed: {e}")
            return False

    async def _handle_webhook_request(self, request) -> Any:
        """Handle incoming webhook requests."""
        try:
            # Validate request
            if not await self._validate_request(request):
                return self._create_error_response(401, "Unauthorized")

            # Parse request data
            data = await self._parse_request_data(request)

            # Check if data matches filters
            if not self.matches_filters(data):
                logger.info("Webhook data filtered out")
                return self._create_success_response({"status": "filtered"})

            # Create execution context
            context = ExecutionContext(
                flow_id=f"webhook_{self.trigger_id}",
                execution_id=f"webhook_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                user_id=self.config.get("user_id", "webhook_user")
            )

            # Add webhook data to context
            context.set_variable("webhook_data", data)
            context.set_variable("webhook_headers", dict(request.headers))
            context.set_variable("webhook_method", request.method)
            context.set_variable("webhook_url", str(request.url))

            logger.info(f"Webhook trigger {self.trigger_id} received valid request")

            # Trigger workflow execution asynchronously
            asyncio.create_task(self.trigger_workflow(self._callback))

            return self._create_success_response({"status": "accepted"})

        except Exception as e:
            logger.error(f"Error handling webhook request: {e}")
            return self._create_error_response(500, "Internal server error")

    async def _handle_health_check(self, request) -> Any:
        """Handle health check requests."""
        return self._create_success_response({
            "status": "healthy",
            "trigger_id": self.trigger_id,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def _validate_request(self, request) -> bool:
        """Validate incoming webhook request."""
        # Check secret token if configured
        if self.secret_token:
            auth_header = request.headers.get("Authorization", "")
            expected_token = f"Bearer {self.secret_token}"

            if auth_header != expected_token:
                provided_token = request.headers.get("X-Webhook-Secret", "")
                if provided_token != self.secret_token:
                    return False

        return True

    async def _parse_request_data(self, request) -> Dict[str, Any]:
        """Parse request data based on content type."""
        try:
            content_type = request.headers.get("Content-Type", "").lower()

            if "application/json" in content_type:
                return await request.json()
            elif "application/x-www-form-urlencoded" in content_type:
                data = await request.post()
                return dict(data)
            elif "text/plain" in content_type:
                text = await request.text()
                return {"text": text}
            else:
                # Try to parse as JSON first, fallback to text
                try:
                    return await request.json()
                except:
                    text = await request.text()
                    return {"raw": text}

        except Exception as e:
            logger.warning(f"Failed to parse request data: {e}")
            return {"error": "Failed to parse request data"}

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for webhook requests."""
        headers = {"Content-Type": "application/json"}
        if self.secret_token:
            headers["Authorization"] = f"Bearer {self.secret_token}"
        return headers

    def _create_success_response(self, data: Dict[str, Any]) -> Any:
        """Create a successful response."""
        try:
            from aiohttp import web
            return web.json_response(data, status=200)
        except ImportError:
            return {"status": "success", "data": data}

    def _create_error_response(self, status: int, message: str) -> Any:
        """Create an error response."""
        try:
            from aiohttp import web
            return web.json_response({"error": message}, status=status)
        except ImportError:
            return {"status": "error", "message": message}
