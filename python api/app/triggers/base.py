"""Base Trigger Classes

This module defines the base classes and interfaces for implementing
workflow triggers in the automation platform.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, Awaitable
from datetime import datetime
import uuid

from ..core.context import ExecutionContext

logger = logging.getLogger(__name__)


class BaseTrigger(ABC):
    """Base class for all workflow triggers.

    This abstract class defines the interface that all trigger implementations
    must follow. Triggers are responsible for monitoring external events
    and initiating workflow executions when conditions are met.
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        """Initialize the trigger.

        Args:
            config: Configuration dictionary for the trigger
            connection_id: Optional connection ID for authenticated services
        """
        self.config = config
        self.connection_id = connection_id
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.trigger_id = str(uuid.uuid4())
        self.last_triggered: Optional[datetime] = None

    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate the trigger configuration.

        Returns:
            True if configuration is valid, False otherwise

        Raises:
            ValueError: If configuration is invalid with details
        """
        pass

    @abstractmethod
    async def setup(self) -> None:
        """Set up the trigger resources and connections.

        This method is called once when the trigger is initialized.
        It should establish any necessary connections, authenticate,
        and prepare for monitoring.

        Raises:
            ConnectionError: If setup fails due to connection issues
            AuthenticationError: If authentication fails
        """
        pass

    @abstractmethod
    async def start(self, callback: Callable[[ExecutionContext], Awaitable[None]]) -> None:
        """Start the trigger and begin monitoring for events.

        Args:
            callback: Function to call when trigger conditions are met.
                     Should accept an ExecutionContext parameter.

        This method should start the monitoring loop and call the callback
        whenever the trigger condition is satisfied.
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the trigger and clean up resources.

        This method should gracefully stop monitoring and release
        any resources acquired during setup.
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the connection to the trigger's data source.

        Returns:
            True if connection is successful, False otherwise

        This method is used for health checks and configuration validation.
        """
        pass

    async def trigger_workflow(self, callback: Callable[[ExecutionContext], Awaitable[None]]) -> None:
        """Trigger a workflow execution.

        Args:
            callback: The callback function to execute the workflow
        """
        try:
            # Create execution context
            context = ExecutionContext(
                flow_id=f"trigger_{self.trigger_id}",
                execution_id=str(uuid.uuid4()),
                user_id=self.config.get("user_id", "system")
            )

            # Add trigger metadata to context
            context.set_variable("trigger_type", self.__class__.__name__)
            context.set_variable("trigger_config", self.config)
            context.set_variable("trigger_timestamp", datetime.utcnow().isoformat())

            self.last_triggered = datetime.utcnow()

            logger.info(f"Trigger {self.trigger_id} firing workflow execution")

            # Execute callback
            await callback(context)

        except Exception as e:
            logger.error(f"Error triggering workflow in {self.trigger_id}: {e}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the trigger.

        Returns:
            Dictionary containing status information
        """
        return {
            "trigger_id": self.trigger_id,
            "is_running": self.is_running,
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
            "config": {k: v for k, v in self.config.items() if k != "credentials"},  # Exclude sensitive data
            "connection_id": self.connection_id
        }

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update the trigger configuration.

        Args:
            new_config: New configuration dictionary
        """
        self.config.update(new_config)
        logger.info(f"Updated configuration for trigger {self.trigger_id}")


class ScheduledTrigger(BaseTrigger):
    """Base class for time-based triggers.

    This class extends BaseTrigger with scheduling capabilities
    for triggers that should fire at regular intervals or specific times.
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.schedule_config = config.get("schedule", "*/30 * * * *")  # Default: every 30 minutes

    async def validate_config(self) -> bool:
        """Validate schedule configuration."""
        if "schedule" not in self.config:
            raise ValueError("Schedule configuration is required for scheduled triggers")

        schedule = self.config["schedule"]
        if not isinstance(schedule, str):
            raise ValueError("Schedule must be a cron expression string")

        return True


class EventTrigger(BaseTrigger):
    """Base class for event-driven triggers.

    This class extends BaseTrigger for triggers that respond to
    external events like webhooks, file changes, or message events.
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.event_filters = config.get("filters", {})

    async def validate_config(self) -> bool:
        """Validate event filter configuration."""
        if "filters" in self.config:
            filters = self.config["filters"]
            if not isinstance(filters, dict):
                raise ValueError("Event filters must be a dictionary")

        return True

    def matches_filters(self, event_data: Dict[str, Any]) -> bool:
        """Check if event data matches the configured filters.

        Args:
            event_data: The event data to check against filters

        Returns:
            True if event matches all filters, False otherwise
        """
        if not self.event_filters:
            return True  # No filters means accept all events

        for filter_key, filter_value in self.event_filters.items():
            if filter_key not in event_data:
                return False

            event_value = event_data[filter_key]
            if isinstance(filter_value, list):
                if event_value not in filter_value:
                    return False
            elif event_value != filter_value:
                return False

        return True
