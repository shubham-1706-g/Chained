"""HTTP Request Action

This module implements an action for making HTTP requests to external APIs
and web services. It supports all standard HTTP methods with full configuration
options for headers, authentication, timeouts, and response handling.
"""

import logging
from typing import Any, Dict, Optional, Union
import json

from ..base import HttpAction
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class HTTPRequestAction(HttpAction):
    """Action for making HTTP requests to external APIs.

    This action supports:
    - All HTTP methods (GET, POST, PUT, DELETE, PATCH, etc.)
    - Custom headers and authentication
    - Request body with various content types
    - Response parsing and validation
    - Error handling and retries
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.method = config.get("method", "GET").upper()
        self.endpoint = config.get("endpoint", "")
        self.request_body = config.get("body", {})
        self.query_params = config.get("query_params", {})
        self.request_headers = config.get("request_headers", {})
        self.content_type = config.get("content_type", "application/json")
        self.response_type = config.get("response_type", "json")  # json, text, xml, binary
        self.timeout = config.get("timeout", 30)
        self.follow_redirects = config.get("follow_redirects", True)
        self.verify_ssl = config.get("verify_ssl", True)
        self.auth_type = config.get("auth_type", "none")  # none, basic, bearer, api_key, oauth2
        self.auth_config = config.get("auth_config", {})
        self.retry_count = config.get("retry_count", 0)
        self.retry_delay = config.get("retry_delay", 1.0)
        self.response_validation = config.get("response_validation", {})

    async def validate_config(self) -> bool:
        """Validate HTTP request action configuration."""
        await super().validate_config()

        if not self.endpoint:
            raise ValueError("endpoint is required for HTTP request action")

        valid_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "CONNECT", "TRACE"]
        if self.method not in valid_methods:
            raise ValueError(f"Invalid HTTP method: {self.method}. Must be one of {valid_methods}")

        if self.response_type not in ["json", "text", "xml", "binary"]:
            raise ValueError("response_type must be 'json', 'text', 'xml', or 'binary'")

        if self.auth_type not in ["none", "basic", "bearer", "api_key", "oauth2"]:
            raise ValueError("Invalid auth_type. Must be 'none', 'basic', 'bearer', 'api_key', or 'oauth2'")

        if self.retry_count < 0:
            raise ValueError("retry_count must be non-negative")

        if self.retry_delay <= 0:
            raise ValueError("retry_delay must be positive")

        return True

    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the HTTP request."""
        import asyncio
        import aiohttp

        try:
            # Prepare request parameters
            url = self._build_url(input_data)
            headers = self._prepare_headers(input_data)
            body = self._prepare_body(input_data)

            # Execute request with retries
            for attempt in range(self.retry_count + 1):
                try:
                    result = await self._make_request(url, headers, body, input_data)

                    # Validate response if configured
                    if self.response_validation:
                        self._validate_response(result)

                    return result

                except Exception as e:
                    if attempt < self.retry_count:
                        logger.warning(f"Request attempt {attempt + 1} failed: {e}. Retrying in {self.retry_delay}s...")
                        await asyncio.sleep(self.retry_delay)
                    else:
                        raise

        except Exception as e:
            logger.error(f"HTTP request failed after {self.retry_count + 1} attempts: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": self.method,
                "url": url if 'url' in locals() else self._build_url(input_data)
            }

    async def _make_request(
        self,
        url: str,
        headers: Dict[str, str],
        body: Any,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make the actual HTTP request."""
        import aiohttp
        import time

        start_time = time.time()

        async with aiohttp.ClientSession() as session:
            # Prepare request parameters
            request_kwargs = {
                "url": url,
                "headers": headers,
                "timeout": aiohttp.ClientTimeout(total=self.timeout),
                "allow_redirects": self.follow_redirects,
                "verify_ssl": self.verify_ssl
            }

            # Add body for non-GET requests
            if self.method != "GET" and body is not None:
                if isinstance(body, dict):
                    request_kwargs["json"] = body
                elif isinstance(body, str):
                    request_kwargs["data"] = body
                else:
                    request_kwargs["data"] = body

            # Add query parameters
            if self.query_params:
                request_kwargs["params"] = self.query_params

            # Make the request
            async with session.request(self.method, **request_kwargs) as response:
                response_time = time.time() - start_time

                # Parse response based on type
                response_data = await self._parse_response(response)

                result = {
                    "success": response.status < 400,
                    "status_code": response.status,
                    "headers": dict(response.headers),
                    "url": str(response.url),
                    "method": self.method,
                    "response_time": response_time,
                    "data": response_data
                }

                if not result["success"]:
                    logger.warning(f"HTTP request failed with status {response.status}")

                return result

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
        if "Content-Type" not in headers and self.content_type:
            headers["Content-Type"] = self.content_type

        # Add authentication headers
        auth_headers = self._get_auth_headers()
        headers.update(auth_headers)

        # Add any dynamic headers from input
        dynamic_headers = input_data.get("headers", {})
        if isinstance(dynamic_headers, dict):
            headers.update(dynamic_headers)

        return headers

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers based on auth type."""
        headers = {}

        if self.auth_type == "basic":
            import base64
            username = self.auth_config.get("username", "")
            password = self.auth_config.get("password", "")
            auth_string = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {auth_string}"

        elif self.auth_type == "bearer":
            token = self.auth_config.get("token", "")
            headers["Authorization"] = f"Bearer {token}"

        elif self.auth_type == "api_key":
            key_name = self.auth_config.get("key_name", "X-API-Key")
            key_value = self.auth_config.get("key_value", "")
            headers[key_name] = key_value

        elif self.auth_type == "oauth2":
            token = self.auth_config.get("access_token", "")
            token_type = self.auth_config.get("token_type", "Bearer")
            headers["Authorization"] = f"{token_type} {token}"

        return headers

    def _prepare_body(self, input_data: Dict[str, Any]) -> Any:
        """Prepare request body."""
        body = self.request_body.copy() if self.request_body else {}

        # Merge with input data
        input_body = input_data.get("body")
        if input_body:
            if isinstance(input_body, dict) and isinstance(body, dict):
                body.update(input_body)
            else:
                return input_body

        # Return None for GET/HEAD requests
        if self.method in ["GET", "HEAD"]:
            return None

        return body if body else None

    async def _parse_response(self, response) -> Any:
        """Parse the HTTP response based on type."""
        try:
            content_type = response.headers.get("Content-Type", "").lower()

            if self.response_type == "json" or "application/json" in content_type:
                return await response.json()
            elif self.response_type == "text" or "text/" in content_type:
                return await response.text()
            elif self.response_type == "xml" or "xml" in content_type:
                return await response.text()
            elif self.response_type == "binary":
                return await response.read()
            else:
                # Default to text
                return await response.text()

        except Exception as e:
            logger.warning(f"Failed to parse response: {e}")
            return await response.text()

    def _validate_response(self, result: Dict[str, Any]) -> None:
        """Validate response against configured rules."""
        validation = self.response_validation

        # Check status code
        if "status_code" in validation:
            expected_status = validation["status_code"]
            if isinstance(expected_status, list):
                if result["status_code"] not in expected_status:
                    raise ValueError(f"Unexpected status code: {result['status_code']}. Expected: {expected_status}")
            elif result["status_code"] != expected_status:
                raise ValueError(f"Unexpected status code: {result['status_code']}. Expected: {expected_status}")

        # Check response structure
        if "required_fields" in validation and result["success"]:
            data = result.get("data", {})
            required_fields = validation["required_fields"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Required field missing in response: {field}")

    async def test_connection(self) -> bool:
        """Test HTTP connection by making a test request."""
        try:
            import aiohttp

            # Use a simple GET request to test connectivity
            test_url = self.base_url or "https://httpbin.org/get"
            headers = self._get_auth_headers()

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

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action input."""
        schema = {
            "type": "object",
            "properties": {
                "body": {
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
            }
        }

        # Add URL parameter placeholders
        if "{" in self.endpoint:
            import re
            params = re.findall(r"\{([^}]+)\}", self.endpoint)
            for param in params:
                schema["properties"][param] = {
                    "type": "string",
                    "description": f"URL parameter: {param}"
                }

        return schema

    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action output."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "status_code": {"type": "integer"},
                "headers": {"type": "object"},
                "url": {"type": "string"},
                "method": {"type": "string"},
                "response_time": {"type": "number"},
                "data": {
                    "description": "Response data (format depends on response_type)"
                },
                "error": {"type": "string"}
            },
            "required": ["success", "status_code"]
        }
