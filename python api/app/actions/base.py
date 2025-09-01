"""Base Action Classes

This module defines the base classes and interfaces for implementing
workflow actions in the automation platform.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime
import time

from ..core.context import ExecutionContext

logger = logging.getLogger(__name__)


class ActionError(Exception):
    """Raised when an action execution fails."""
    def __init__(self, action_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.action_name = action_name
        self.message = message
        self.details = details or {}
        super().__init__(f"Action {action_name} failed: {message}")


class ValidationError(ActionError):
    """Raised when action configuration validation fails."""
    pass


class BaseAction(ABC):
    """Base class for all workflow actions.

    This abstract class defines the interface that all action implementations
    must follow. Actions are responsible for executing specific tasks
    within a workflow, such as API calls, data processing, or integrations.
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        """Initialize the action.

        Args:
            config: Configuration dictionary for the action
            connection_id: Optional connection ID for authenticated services
        """
        self.config = config
        self.connection_id = connection_id
        self.action_name = self.__class__.__name__

    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate the action configuration.

        Returns:
            True if configuration is valid, False otherwise

        Raises:
            ValidationError: If configuration is invalid with details
        """
        pass

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the action.

        Args:
            input_data: Input data for the action execution
            context: Execution context containing workflow state and variables

        Returns:
            Dictionary containing the action execution results

        Raises:
            ActionError: If action execution fails
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the connection to external services.

        Returns:
            True if connection test passes, False otherwise

        Raises:
            ConnectionError: If connection test fails
        """
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for the action's input and output.

        Returns:
            Dictionary containing input and output schemas
        """
        return {
            "input": self.get_input_schema(),
            "output": self.get_output_schema(),
            "config": self.get_config_schema()
        }

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action input.

        Returns:
            JSON schema dictionary for input validation
        """
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action output.

        Returns:
            JSON schema dictionary for output documentation
        """
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "data": {"type": "object"},
                "error": {"type": "string"}
            }
        }

    def get_config_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action configuration.

        Returns:
            JSON schema dictionary for configuration validation
        """
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    async def _execute_with_timing(
        self,
        execution_func: callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute an action function with timing measurement.

        Args:
            execution_func: The function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Execution result with timing information
        """
        start_time = time.time()

        try:
            result = await execution_func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Add timing metadata
            if isinstance(result, dict):
                result["_execution_time"] = execution_time
                result["_timestamp"] = datetime.utcnow().isoformat()

            logger.info(f"Action {self.action_name} executed successfully in {execution_time:.2f}s")
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Action {self.action_name} failed after {execution_time:.2f}s: {e}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the action.

        Returns:
            Dictionary containing status information
        """
        return {
            "action_name": self.action_name,
            "config": {k: v for k, v in self.config.items() if not k.lower().endswith("key")},  # Exclude sensitive keys
            "connection_id": self.connection_id,
            "schema": self.get_schema()
        }


class HttpAction(BaseAction):
    """Base class for HTTP-based actions.

    This class extends BaseAction with HTTP-specific functionality
    for actions that make HTTP requests to external services.
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.base_url = config.get("base_url", "")
        self.timeout = config.get("timeout", 30)
        self.headers = config.get("headers", {})

    async def validate_config(self) -> bool:
        """Validate HTTP action configuration."""
        if not self.base_url:
            raise ValidationError("base_url", "Base URL is required for HTTP actions")

        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.base_url)
            if not parsed.scheme or not parsed.netloc:
                raise ValidationError("base_url", "Invalid URL format")
        except Exception as e:
            raise ValidationError("base_url", f"URL validation failed: {e}")

        return True

    async def test_connection(self) -> bool:
        """Test HTTP connection to the configured endpoint."""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    return response.status < 400
        except Exception as e:
            logger.error(f"HTTP connection test failed: {e}")
            return False


class ApiAction(BaseAction):
    """Base class for API integration actions.

    This class extends BaseAction for actions that integrate with
    specific APIs (like OpenAI, Slack, etc.) with authentication.
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.api_key = config.get("api_key", "")
        self.api_base_url = config.get("api_base_url", "")
        self.auth_method = config.get("auth_method", "bearer")

    async def validate_config(self) -> bool:
        """Validate API action configuration."""
        if not self.api_key:
            raise ValidationError("api_key", "API key is required for API actions")

        if self.auth_method not in ["bearer", "basic", "api_key", "oauth2"]:
            raise ValidationError("auth_method", "Invalid authentication method")

        return True

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests.

        Returns:
            Dictionary of authentication headers
        """
        if self.auth_method == "bearer":
            return {"Authorization": f"Bearer {self.api_key}"}
        elif self.auth_method == "api_key":
            return {"X-API-Key": self.api_key}
        else:
            # For basic auth or oauth2, additional setup would be needed
            return {}

    async def test_connection(self) -> bool:
        """Test API connection."""
        try:
            import aiohttp

            headers = self.get_auth_headers()
            headers.update({"Content-Type": "application/json"})

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/health" if self.api_base_url else "https://httpbin.org/get",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status < 400
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False
