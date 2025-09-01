"""Notion Database Trigger

This module implements triggers for Notion database events including
new item creation, item updates, and database changes.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Callable, Awaitable
from datetime import datetime

from ..base import EventTrigger
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class NotionDatabaseTrigger(EventTrigger):
    """Trigger for Notion database events.

    This trigger monitors Notion databases for:
    - New items created in databases
    - Existing items updated
    - Items matching specific criteria
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.api_key = config.get("api_key", "")
        self.database_id = config.get("database_id", "")
        self.event_types = config.get("event_types", ["item_created"])  # item_created, item_updated
        self.poll_interval = config.get("poll_interval", 30)  # seconds
        self.api_base_url = "https://api.notion.com/v1"
        self.last_check_time = None

    async def validate_config(self) -> bool:
        """Validate Notion database trigger configuration."""
        if not self.api_key:
            raise ValueError("api_key is required for Notion database trigger")

        if not self.database_id:
            raise ValueError("database_id is required for database monitoring")

        valid_event_types = ["item_created", "item_updated"]
        for event_type in self.event_types:
            if event_type not in valid_event_types:
                raise ValueError(f"Invalid event type: {event_type}. Must be one of {valid_event_types}")

        if self.poll_interval < 10:
            raise ValueError("poll_interval must be at least 10 seconds")

        return True

    async def setup(self) -> None:
        """Set up the Notion database trigger."""
        # Get initial database state
        try:
            database_info = await self._get_database_info()
            self.database_title = database_info.get("title", "Unknown Database")
            logger.info(f"Monitoring Notion database: {self.database_title}")
        except Exception as e:
            logger.warning(f"Could not get database info during setup: {e}")

    async def start(self, callback: Callable[[ExecutionContext], Awaitable[None]]) -> None:
        """Start monitoring the Notion database."""
        self.is_running = True
        self._callback = callback

        logger.info(f"Notion database trigger started for database: {self.database_id}")

        # Initial check to get baseline
        await self._check_for_changes()

        while self.is_running:
            try:
                await asyncio.sleep(self.poll_interval)
                if self.is_running:  # Check again after sleep
                    await self._check_for_changes()
            except Exception as e:
                logger.error(f"Error in database monitoring loop: {e}")
                await asyncio.sleep(self.poll_interval)

    async def stop(self) -> None:
        """Stop the database trigger."""
        self.is_running = False
        logger.info(f"Notion database trigger stopped for database: {self.database_id}")

    async def test_connection(self) -> bool:
        """Test Notion API connection."""
        try:
            await self._get_database_info()
            return True
        except Exception as e:
            logger.error(f"Notion database connection test failed: {e}")
            return False

    async def _check_for_changes(self) -> None:
        """Check for changes in the database."""
        try:
            # Query database for recent items
            query_result = await self._query_database()

            if not query_result.get("results"):
                return

            current_time = datetime.utcnow()

            for item in query_result["results"]:
                await self._process_database_item(item, current_time)

            # Update last check time
            self.last_check_time = current_time

        except Exception as e:
            logger.error(f"Error checking database changes: {e}")

    async def _process_database_item(self, item: Dict[str, Any], check_time: datetime) -> None:
        """Process a database item and trigger events if needed."""
        try:
            item_id = item.get("id")
            created_time = item.get("created_time")
            last_edited_time = item.get("last_edited_time")

            if not item_id:
                return

            # Convert times to datetime objects
            created_dt = datetime.fromisoformat(created_time.replace('Z', '+00:00')) if created_time else None
            edited_dt = datetime.fromisoformat(last_edited_time.replace('Z', '+00:00')) if last_edited_time else None

            # Check for new item
            if "item_created" in self.event_types and created_dt and self.last_check_time:
                if created_dt > self.last_check_time:
                    await self._trigger_event("item_created", item, created_dt)

            # Check for updated item
            elif "item_updated" in self.event_types and edited_dt and self.last_check_time:
                if edited_dt > self.last_check_time:
                    await self._trigger_event("item_updated", item, edited_dt)

        except Exception as e:
            logger.error(f"Error processing database item {item.get('id', 'unknown')}: {e}")

    async def _trigger_event(self, event_type: str, item: Dict[str, Any], event_time: datetime) -> None:
        """Trigger a workflow event for a database item."""
        try:
            # Check if event matches filters
            if not self.matches_filters(item):
                logger.debug(f"Database item filtered out: {item.get('id')}")
                return

            # Create execution context
            context = ExecutionContext(
                flow_id=f"notion_db_{self.database_id}",
                execution_id=f"notion_{event_type}_{item.get('id')}_{int(event_time.timestamp())}",
                user_id=self.config.get("user_id", "notion_trigger")
            )

            # Add event data to context
            context.set_variable("notion_event", {
                "type": event_type,
                "database_id": self.database_id,
                "database_title": getattr(self, 'database_title', 'Unknown'),
                "item_id": item.get("id"),
                "item_url": item.get("url"),
                "properties": item.get("properties", {}),
                "created_time": item.get("created_time"),
                "last_edited_time": item.get("last_edited_time"),
                "event_time": event_time.isoformat()
            })

            logger.info(f"Notion database trigger fired: {event_type} for item {item.get('id')}")

            # Trigger workflow execution
            await self.trigger_workflow(self._callback)

        except Exception as e:
            logger.error(f"Error triggering Notion database event: {e}")

    async def _get_database_info(self) -> Dict[str, Any]:
        """Get database metadata."""
        try:
            import aiohttp

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/databases/{self.database_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Notion API error: {error_data}")

                    return await response.json()

        except ImportError:
            raise Exception("aiohttp is required for Notion API requests")
        except Exception as e:
            logger.error(f"Database info retrieval failed: {e}")
            raise

    async def _query_database(self) -> Dict[str, Any]:
        """Query the database for recent items."""
        try:
            import aiohttp

            # Query parameters to get recent items
            query_params = {
                "sorts": [{"timestamp": "last_edited_time", "direction": "descending"}],
                "page_size": 100  # Get more items to catch recent changes
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/databases/{self.database_id}/query",
                    headers=headers,
                    json=query_params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Notion API error: {error_data}")

                    return await response.json()

        except ImportError:
            raise Exception("aiohttp is required for Notion API requests")
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise
