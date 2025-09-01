"""HTTP Action

This module implements an HTTP action that can make HTTP requests
to external APIs and services as part of workflow execution.
"""

import logging
from typing import Any, Dict, Optional
import json

from .base import HttpAction
from ..core.context import ExecutionContext

logger = logging.getLogger(__name__)


class HTTPAction(HttpAction):
    """HTTP action for making HTTP requests to external services.

    This action can make GET, POST, PUT, PATCH, DELETE requests
    with custom headers, body, and authentication.
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.method = config.get("method", "GET").upper()
        self.endpoint = config.get("endpoint", "")
        self.request_body = config.get("body", {})
        self.query_params = config.get("query_params", {})
        self.request_headers = config.get("request_headers", {})
        self.timeout = config.get("timeout", 30)
        self.follow_redirects = config.get("follow_redirects", True)
        self.verify_ssl = config.get("verify_ssl", True)

    async def validate_config(self) -> bool:
        """Validate HTTP action configuration."""
        await super().validate_config()

        if not self.endpoint:
            raise ValueError("endpoint is required for HTTP action")

        valid_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
        if self.method not in valid_methods:
            raise ValueError(f"Invalid HTTP method: {self.method}. Must be one of {valid_methods}")

        if not isinstance(self.timeout, (int, float)) or self.timeout <= 0:
            raise ValueError("timeout must be a positive number")

        return True

    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the HTTP request."""
        try:
            import aiohttp

            # Build the full URL
            url = self._build_url(input_data)

            # Prepare headers
            headers = self._prepare_headers(input_data)

            # Prepare request body
            body = self._prepare_body(input_data)

            # Make the request
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=self.method,
                    url=url,
                    headers=headers,
                    json=body if isinstance(body, dict) else None,
                    data=body if isinstance(body, str) else None,
                    params=self.query_params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    allow_redirects=self.follow_redirects,
                    verify_ssl=self.verify_ssl
                ) as response:

                    # Parse response
                    response_data = await self._parse_response(response)

                    result = {
                        "success": response.status < 400,
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "url": str(response.url),
                        "method": self.method,
                        "response_time": response_data.get("_response_time", 0),
                        "data": response_data
                    }

                    if not result["success"]:
                        logger.warning(f"HTTP request failed with status {response.status}: {response_data}")

                    return result

        except Exception as e:
            error_msg = f"HTTP request failed: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "status_code": None,
                "data": None
            }

    async def test_connection(self) -> bool:
        """Test HTTP connection by making a simple request."""
        try:
            import aiohttp

            # Use a simple GET request to test connectivity
            test_url = self.base_url or "https://httpbin.org/get"

            headers = self.headers.copy()
            headers.update({"User-Agent": "FlowForge-HTTP-Action-Test"})

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    test_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status < 400

        except Exception as e:
            logger.error(f"HTTP connection test failed: {e}")
            return False

    def _build_url(self, input_data: Dict[str, Any]) -> str:
        """Build the complete URL for the request."""
        base_url = self.base_url.rstrip('/')
        endpoint = self.endpoint.lstrip('/')

        url = f"{base_url}/{endpoint}"

        # Replace URL parameters from input data
        if input_data:
            for key, value in input_data.items():
                if f"{{{key}}}" in url:
                    url = url.replace(f"{{{key}}}", str(value))

        return url

    def _prepare_headers(self, input_data: Dict[str, Any]) -> Dict[str, str]:
        """Prepare request headers."""
        headers = self.headers.copy()
        headers.update(self.request_headers)

        # Add content type if not specified
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"

        # Add any dynamic headers from input
        dynamic_headers = input_data.get("headers", {})
        if isinstance(dynamic_headers, dict):
            headers.update(dynamic_headers)

        return headers

    def _prepare_body(self, input_data: Dict[str, Any]) -> Any:
        """Prepare request body."""
        body = self.request_body.copy() if self.request_body else {}

        # Merge with input data
        if input_data and "body" in input_data:
            input_body = input_data["body"]
            if isinstance(input_body, dict):
                body.update(input_body)
            else:
                return input_body  # Raw body

        # Return None for GET/HEAD requests
        if self.method in ["GET", "HEAD"]:
            return None

        return body

    async def _parse_response(self, response) -> Dict[str, Any]:
        """Parse the HTTP response."""
        try:
            import time
            start_time = time.time()

            content_type = response.headers.get("Content-Type", "").lower()

            if "application/json" in content_type:
                data = await response.json()
            elif "text/" in content_type or "xml" in content_type:
                text = await response.text()
                data = {"text": text}
            else:
                # Binary or unknown content type
                data = await response.read()
                data = {"raw": data.hex() if isinstance(data, bytes) else str(data)}

            response_time = time.time() - start_time
            data["_response_time"] = response_time

            return data

        except Exception as e:
            logger.warning(f"Failed to parse response: {e}")
            return {"error": "Failed to parse response", "raw_text": await response.text()}

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action input."""
        return {
            "type": "object",
            "properties": {
                "body": {
                    "type": "object",
                    "description": "Request body data (merged with configured body)"
                },
                "headers": {
                    "type": "object",
                    "description": "Additional headers to include in the request"
                },
                "query_params": {
                    "type": "object",
                    "description": "Query parameters to include in the URL"
                }
            },
            "additionalProperties": True
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action output."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "status_code": {"type": ["integer", "null"]},
                "headers": {"type": "object"},
                "url": {"type": "string"},
                "method": {"type": "string"},
                "response_time": {"type": "number"},
                "data": {"type": "object"},
                "error": {"type": "string"}
            },
            "required": ["success", "status_code"]
        }

    def get_config_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action configuration."""
        return {
            "type": "object",
            "properties": {
                "base_url": {
                    "type": "string",
                    "description": "Base URL for the API"
                },
                "endpoint": {
                    "type": "string",
                    "description": "API endpoint path"
                },
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
                    "default": "GET"
                },
                "headers": {
                    "type": "object",
                    "description": "Default headers to include"
                },
                "body": {
                    "type": "object",
                    "description": "Default request body"
                },
                "timeout": {
                    "type": "number",
                    "default": 30,
                    "minimum": 1
                },
                "follow_redirects": {
                    "type": "boolean",
                    "default": true
                },
                "verify_ssl": {
                    "type": "boolean",
                    "default": true
                }
            },
            "required": ["base_url", "endpoint"]
        }
