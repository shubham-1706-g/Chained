"""Notion Page Action

This module implements actions for Notion page operations including
creating pages, updating page content, and retrieving page information.
"""

import logging
from typing import Any, Dict, Optional, List
import json

from ..base import ApiAction
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class NotionPageAction(ApiAction):
    """Action for Notion page operations.

    This action supports:
    - Creating new pages
    - Updating existing page content and properties
    - Retrieving page content and metadata
    - Appending content to pages
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.api_key = config.get("api_key", "")
        self.page_id = config.get("page_id", "")
        self.parent_id = config.get("parent_id", "")  # Parent page or database ID
        self.operation = config.get("operation", "create")  # create, update, get, append
        self.api_base_url = "https://api.notion.com/v1"

    async def validate_config(self) -> bool:
        """Validate Notion page action configuration."""
        if not self.api_key:
            raise ValueError("api_key is required for Notion page action")

        if not self.page_id and self.operation in ["update", "append", "get"]:
            raise ValueError("page_id is required for page operations")

        if not self.parent_id and self.operation == "create":
            raise ValueError("parent_id is required for page creation")

        valid_operations = ["create", "update", "get", "append"]
        if self.operation not in valid_operations:
            raise ValueError(f"Invalid operation: {self.operation}. Must be one of {valid_operations}")

        return True

    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the Notion page operation."""
        try:
            if self.operation == "create":
                result = await self._create_page(input_data)
            elif self.operation == "update":
                result = await self._update_page(input_data)
            elif self.operation == "get":
                result = await self._get_page(input_data)
            elif self.operation == "append":
                result = await self._append_to_page(input_data)
            else:
                raise ValueError(f"Unsupported operation: {self.operation}")

            return {
                "success": True,
                "operation": self.operation,
                "page_id": self.page_id,
                "result": result
            }

        except Exception as e:
            logger.error(f"Notion page operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": self.operation,
                "page_id": self.page_id
            }

    async def _create_page(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Notion page."""
        try:
            import aiohttp

            # Determine parent type (database or page)
            parent_type = input_data.get("parent_type", "database")  # database or page

            if parent_type == "database":
                parent = {"database_id": self.parent_id}
                properties = input_data.get("properties", {})
            else:  # page
                parent = {"page_id": self.parent_id}
                properties = input_data.get("properties", {})

            payload = {
                "parent": parent,
                "properties": properties
            }

            # Add content blocks if provided
            if "children" in input_data:
                payload["children"] = input_data["children"]

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
                        "properties": result.get("properties", {}),
                        "parent_type": parent_type
                    }

        except ImportError:
            raise Exception("aiohttp is required for Notion API requests")
        except Exception as e:
            logger.error(f"Page creation failed: {e}")
            raise

    async def _update_page(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing Notion page."""
        try:
            import aiohttp

            payload = {}

            # Update properties if provided
            if "properties" in input_data:
                payload["properties"] = input_data["properties"]

            # Update cover or icon if provided
            if "cover" in input_data:
                payload["cover"] = input_data["cover"]
            if "icon" in input_data:
                payload["icon"] = input_data["icon"]

            if not payload:
                raise ValueError("properties, cover, or icon must be provided for update")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }

            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{self.api_base_url}/pages/{self.page_id}",
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
            logger.error(f"Page update failed: {e}")
            raise

    async def _get_page(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve a Notion page with its content."""
        try:
            import aiohttp

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/pages/{self.page_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Notion API error: {error_data}")

                    page_result = await response.json()

                    # Also get page content (blocks)
                    async with session.get(
                        f"{self.api_base_url}/blocks/{self.page_id}/children",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as blocks_response:

                        blocks_result = await blocks_response.json() if blocks_response.status == 200 else {"results": []}

                        return {
                            "page_id": page_result.get("id"),
                            "url": page_result.get("url"),
                            "title": page_result.get("properties", {}).get("title", {}).get("title", [{}])[0].get("plain_text", ""),
                            "properties": page_result.get("properties", {}),
                            "created_time": page_result.get("created_time"),
                            "last_edited_time": page_result.get("last_edited_time"),
                            "blocks": blocks_result.get("results", []),
                            "block_count": len(blocks_result.get("results", []))
                        }

        except ImportError:
            raise Exception("aiohttp is required for Notion API requests")
        except Exception as e:
            logger.error(f"Page retrieval failed: {e}")
            raise

    async def _append_to_page(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Append content blocks to an existing page."""
        try:
            import aiohttp

            children = input_data.get("children", [])
            if not children:
                raise ValueError("children is required for append operation")

            payload = {"children": children}

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }

            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{self.api_base_url}/blocks/{self.page_id}/children",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Notion API error: {error_data}")

                    result = await response.json()

                    return {
                        "page_id": self.page_id,
                        "blocks_added": len(children),
                        "results": result.get("results", [])
                    }

        except ImportError:
            raise Exception("aiohttp is required for Notion API requests")
        except Exception as e:
            logger.error(f"Page append failed: {e}")
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
                    "parent_type": {
                        "type": "string",
                        "enum": ["database", "page"],
                        "default": "database",
                        "description": "Type of parent (database or page)"
                    },
                    "properties": {
                        "type": "object",
                        "description": "Page properties"
                    },
                    "children": {
                        "type": "array",
                        "description": "Content blocks for the page"
                    }
                },
                "required": ["properties"]
            }
        elif self.operation == "append":
            return {
                "type": "object",
                "properties": {
                    "children": {
                        "type": "array",
                        "description": "Content blocks to append"
                    }
                },
                "required": ["children"]
            }

        return {"type": "object", "properties": {}}

    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action output."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "operation": {"type": "string"},
                "page_id": {"type": "string"},
                "result": {
                    "description": "Operation result (structure depends on operation)"
                },
                "error": {"type": "string"}
            },
            "required": ["success", "operation"]
        }
