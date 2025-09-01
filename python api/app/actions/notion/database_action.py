"""Notion Database Action

This module implements actions for Notion database operations including
creating items, querying databases, and updating database entries.
"""

import logging
from typing import Any, Dict, Optional, List
import json

from ..base import ApiAction
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class NotionDatabaseAction(ApiAction):
    """Action for Notion database operations.

    This action supports:
    - Creating new database items/pages
    - Querying database contents with filters
    - Updating existing database items
    - Retrieving database metadata
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.api_key = config.get("api_key", "")
        self.database_id = config.get("database_id", "")
        self.operation = config.get("operation", "create")  # create, query, update, get
        self.api_base_url = "https://api.notion.com/v1"

    async def validate_config(self) -> bool:
        """Validate Notion database action configuration."""
        if not self.api_key:
            raise ValueError("api_key is required for Notion database action")

        if not self.database_id and self.operation in ["create", "query", "update"]:
            raise ValueError("database_id is required for database operations")

        valid_operations = ["create", "query", "update", "get"]
        if self.operation not in valid_operations:
            raise ValueError(f"Invalid operation: {self.operation}. Must be one of {valid_operations}")

        return True

    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the Notion database operation."""
        try:
            if self.operation == "create":
                result = await self._create_database_item(input_data)
            elif self.operation == "query":
                result = await self._query_database(input_data)
            elif self.operation == "update":
                result = await self._update_database_item(input_data)
            elif self.operation == "get":
                result = await self._get_database_info()
            else:
                raise ValueError(f"Unsupported operation: {self.operation}")

            return {
                "success": True,
                "operation": self.operation,
                "database_id": self.database_id,
                "result": result
            }

        except Exception as e:
            logger.error(f"Notion database operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": self.operation,
                "database_id": self.database_id
            }

    async def _create_database_item(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new item in the Notion database."""
        try:
            import aiohttp

            # Prepare the request payload
            properties = input_data.get("properties", {})
            children = input_data.get("children", [])

            payload = {
                "parent": {"database_id": self.database_id},
                "properties": properties
            }

            if children:
                payload["children"] = children

            # Add cover or icon if provided
            if "cover" in input_data:
                payload["cover"] = input_data["cover"]
            if "icon" in input_data:
                payload["icon"] = input_data["icon"]

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/pages",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Notion API error: {error_data}")

                    result = await response.json()

                    return {
                        "page_id": result.get("id"),
                        "url": result.get("url"),
                        "created_time": result.get("created_time"),
                        "last_edited_time": result.get("last_edited_time"),
                        "properties": result.get("properties", {})
                    }

        except ImportError:
            raise Exception("aiohttp is required for Notion API requests")
        except Exception as e:
            logger.error(f"Database item creation failed: {e}")
            raise

    async def _query_database(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Query the Notion database with optional filters."""
        try:
            import aiohttp

            # Prepare query parameters
            query_params = {}

            # Add filter if provided
            if "filter" in input_data:
                query_params["filter"] = input_data["filter"]

            # Add sorts if provided
            if "sorts" in input_data:
                query_params["sorts"] = input_data["sorts"]

            # Add pagination
            if "start_cursor" in input_data:
                query_params["start_cursor"] = input_data["start_cursor"]

            page_size = input_data.get("page_size", 100)
            query_params["page_size"] = min(page_size, 100)  # Notion API limit

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

                    result = await response.json()

                    return {
                        "results": result.get("results", []),
                        "has_more": result.get("has_more", False),
                        "next_cursor": result.get("next_cursor"),
                        "count": len(result.get("results", []))
                    }

        except ImportError:
            raise Exception("aiohttp is required for Notion API requests")
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise

    async def _update_database_item(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing database item."""
        try:
            import aiohttp

            page_id = input_data.get("page_id")
            if not page_id:
                raise ValueError("page_id is required for update operation")

            # Prepare update payload
            payload = {}

            if "properties" in input_data:
                payload["properties"] = input_data["properties"]

            if "children" in input_data:
                payload["children"] = input_data["children"]

            if not payload:
                raise ValueError("properties or children must be provided for update")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }

            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{self.api_base_url}/pages/{page_id}",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Notion API error: {error_data}")

                    result = await response.json()

                    return {
                        "page_id": result.get("id"),
                        "url": result.get("url"),
                        "last_edited_time": result.get("last_edited_time"),
                        "properties": result.get("properties", {})
                    }

        except ImportError:
            raise Exception("aiohttp is required for Notion API requests")
        except Exception as e:
            logger.error(f"Database item update failed: {e}")
            raise

    async def _get_database_info(self) -> Dict[str, Any]:
        """Get database metadata and schema."""
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

                    result = await response.json()

                    return {
                        "id": result.get("id"),
                        "title": result.get("title", [{}])[0].get("plain_text", ""),
                        "description": result.get("description", []),
                        "properties": result.get("properties", {}),
                        "url": result.get("url"),
                        "created_time": result.get("created_time"),
                        "last_edited_time": result.get("last_edited_time")
                    }

        except ImportError:
            raise Exception("aiohttp is required for Notion API requests")
        except Exception as e:
            logger.error(f"Database info retrieval failed: {e}")
            raise

    async def test_connection(self) -> bool:
        """Test Notion API connection."""
        try:
            import aiohttp

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/users/me",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200

        except Exception as e:
            logger.error(f"Notion connection test failed: {e}")
            return False

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action input."""
        if self.operation == "create":
            return {
                "type": "object",
                "properties": {
                    "properties": {
                        "type": "object",
                        "description": "Database properties to set"
                    },
                    "children": {
                        "type": "array",
                        "description": "Page content blocks"
                    },
                    "cover": {
                        "type": "object",
                        "description": "Page cover image"
                    },
                    "icon": {
                        "type": "object",
                        "description": "Page icon"
                    }
                },
                "required": ["properties"]
            }
        elif self.operation == "query":
            return {
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "object",
                        "description": "Query filter conditions"
                    },
                    "sorts": {
                        "type": "array",
                        "description": "Sort specifications"
                    },
                    "page_size": {
                        "type": "integer",
                        "default": 100,
                        "description": "Number of results per page"
                    }
                }
            }
        elif self.operation == "update":
            return {
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "ID of the page to update"
                    },
                    "properties": {
                        "type": "object",
                        "description": "Properties to update"
                    }
                },
                "required": ["page_id"]
            }

        return {"type": "object", "properties": {}}

    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action output."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "operation": {"type": "string"},
                "database_id": {"type": "string"},
                "result": {
                    "description": "Operation result (structure depends on operation)"
                },
                "error": {"type": "string"}
            },
            "required": ["success", "operation"]
        }
