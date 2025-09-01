"""Telegram Chat Action

This module implements actions for Telegram chat operations including
sending messages, responding to chats, getting chat information, and continuing conversations.
"""

import logging
from typing import Any, Dict, Optional, List
import json

from ..base import ApiAction
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class TelegramChatAction(ApiAction):
    """Action for Telegram chat operations.

    This action supports:
    - Sending messages to chats
    - Responding to incoming messages
    - Getting chat information
    - Continuing conversations
    - Managing chat settings
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.bot_token = config.get("bot_token", "")
        self.operation = config.get("operation", "send")  # send, respond, get, continue, edit
        self.chat_id = config.get("chat_id", "")
        self.api_base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def validate_config(self) -> bool:
        """Validate Telegram chat action configuration."""
        if not self.bot_token:
            raise ValueError("bot_token is required for Telegram chat action")

        if not self.chat_id and self.operation in ["send", "respond", "continue", "edit"]:
            raise ValueError("chat_id is required for chat operations")

        valid_operations = ["send", "respond", "get", "continue", "edit", "delete"]
        if self.operation not in valid_operations:
            raise ValueError(f"Invalid operation: {self.operation}. Must be one of {valid_operations}")

        return True

    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the Telegram chat operation."""
        try:
            if self.operation == "send":
                result = await self._send_message(input_data)
            elif self.operation == "respond":
                result = await self._respond_to_message(input_data)
            elif self.operation == "get":
                result = await self._get_chat_info(input_data)
            elif self.operation == "continue":
                result = await self._continue_conversation(input_data)
            elif self.operation == "edit":
                result = await self._edit_message(input_data)
            elif self.operation == "delete":
                result = await self._delete_message(input_data)
            else:
                raise ValueError(f"Unsupported operation: {self.operation}")

            return {
                "success": True,
                "operation": self.operation,
                "chat_id": self.chat_id,
                "result": result
            }

        except Exception as e:
            logger.error(f"Telegram chat operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": self.operation,
                "chat_id": self.chat_id
            }

    async def _send_message(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message to a Telegram chat."""
        try:
            import aiohttp

            text = input_data.get("text", "")
            if not text:
                raise ValueError("text is required for sending message")

            payload = {
                "chat_id": self.chat_id,
                "text": text
            }

            # Add optional parameters
            if "parse_mode" in input_data:
                payload["parse_mode"] = input_data["parse_mode"]

            if "reply_to_message_id" in input_data:
                payload["reply_to_message_id"] = input_data["reply_to_message_id"]

            if "disable_web_page_preview" in input_data:
                payload["disable_web_page_preview"] = input_data["disable_web_page_preview"]

            # Handle different message types
            if "photo" in input_data:
                return await self._send_photo(input_data)
            elif "document" in input_data:
                return await self._send_document(input_data)
            elif "audio" in input_data:
                return await self._send_audio(input_data)
            elif "video" in input_data:
                return await self._send_video(input_data)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/sendMessage",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Telegram API error: {error_data}")

                    result = await response.json()

                    if result.get("ok"):
                        message = result.get("result", {})
                        return {
                            "message_id": message.get("message_id"),
                            "date": message.get("date"),
                            "text": message.get("text"),
                            "from_user": message.get("from", {}).get("username"),
                            "chat_type": message.get("chat", {}).get("type")
                        }
                    else:
                        raise Exception(f"Telegram API returned not ok: {result}")

        except ImportError:
            raise Exception("aiohttp is required for Telegram API requests")
        except Exception as e:
            logger.error(f"Message send failed: {e}")
            raise

    async def _respond_to_message(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Respond to an incoming message."""
        try:
            # Get the original message information
            original_message = input_data.get("original_message", {})
            response_text = input_data.get("response_text", "")

            if not original_message:
                raise ValueError("original_message is required for respond operation")

            if not response_text:
                raise ValueError("response_text is required for respond operation")

            # Extract chat_id from original message if not set
            chat_id = original_message.get("chat", {}).get("id", self.chat_id)

            respond_input = {
                "text": response_text,
                "reply_to_message_id": original_message.get("message_id"),
                "parse_mode": input_data.get("parse_mode", "HTML")
            }

            # Temporarily set chat_id
            original_chat_id = self.chat_id
            self.chat_id = str(chat_id)

            try:
                result = await self._send_message(respond_input)
                return result
            finally:
                self.chat_id = original_chat_id

        except Exception as e:
            logger.error(f"Message response failed: {e}")
            raise

    async def _get_chat_info(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about a Telegram chat."""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/getChat?chat_id={self.chat_id}",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Telegram API error: {error_data}")

                    result = await response.json()

                    if result.get("ok"):
                        chat = result.get("result", {})
                        return {
                            "id": chat.get("id"),
                            "type": chat.get("type"),
                            "title": chat.get("title"),
                            "username": chat.get("username"),
                            "first_name": chat.get("first_name"),
                            "last_name": chat.get("last_name"),
                            "description": chat.get("description"),
                            "member_count": chat.get("member_count")
                        }
                    else:
                        raise Exception(f"Telegram API returned not ok: {result}")

        except ImportError:
            raise Exception("aiohttp is required for Telegram API requests")
        except Exception as e:
            logger.error(f"Chat info retrieval failed: {e}")
            raise

    async def _continue_conversation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Continue an ongoing conversation."""
        try:
            conversation_history = input_data.get("conversation_history", [])
            new_message = input_data.get("new_message", "")

            if not conversation_history:
                raise ValueError("conversation_history is required for continue operation")

            if not new_message:
                raise ValueError("new_message is required for continue operation")

            # This is a simplified implementation
            # In a real implementation, you might use AI to generate contextual responses

            # For now, just send the new message
            continue_input = {
                "text": new_message,
                "parse_mode": input_data.get("parse_mode", "HTML")
            }

            return await self._send_message(continue_input)

        except Exception as e:
            logger.error(f"Conversation continuation failed: {e}")
            raise

    async def _edit_message(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Edit an existing message."""
        try:
            import aiohttp

            message_id = input_data.get("message_id")
            new_text = input_data.get("new_text", "")

            if not message_id:
                raise ValueError("message_id is required for edit operation")

            if not new_text:
                raise ValueError("new_text is required for edit operation")

            payload = {
                "chat_id": self.chat_id,
                "message_id": message_id,
                "text": new_text
            }

            if "parse_mode" in input_data:
                payload["parse_mode"] = input_data["parse_mode"]

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/editMessageText",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Telegram API error: {error_data}")

                    result = await response.json()

                    if result.get("ok"):
                        message = result.get("result", {})
                        return {
                            "message_id": message.get("message_id"),
                            "date": message.get("date"),
                            "text": message.get("text"),
                            "edit_date": message.get("edit_date")
                        }
                    else:
                        raise Exception(f"Telegram API returned not ok: {result}")

        except ImportError:
            raise Exception("aiohttp is required for Telegram API requests")
        except Exception as e:
            logger.error(f"Message edit failed: {e}")
            raise

    async def _delete_message(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a message from chat."""
        try:
            import aiohttp

            message_id = input_data.get("message_id")

            if not message_id:
                raise ValueError("message_id is required for delete operation")

            payload = {
                "chat_id": self.chat_id,
                "message_id": message_id
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/deleteMessage",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Telegram API error: {error_data}")

                    result = await response.json()

                    return {
                        "deleted": result.get("ok", False),
                        "message_id": message_id
                    }

        except ImportError:
            raise Exception("aiohttp is required for Telegram API requests")
        except Exception as e:
            logger.error(f"Message deletion failed: {e}")
            raise

    async def _send_photo(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a photo message."""
        # Implementation for sending photos would require multipart/form-data
        # This is a placeholder for the full implementation
        raise NotImplementedError("Photo sending not yet implemented")

    async def _send_document(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a document message."""
        # Implementation for sending documents would require multipart/form-data
        raise NotImplementedError("Document sending not yet implemented")

    async def _send_audio(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send an audio message."""
        raise NotImplementedError("Audio sending not yet implemented")

    async def _send_video(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a video message."""
        raise NotImplementedError("Video sending not yet implemented")

    async def test_connection(self) -> bool:
        """Test Telegram bot connection."""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/getMe",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("ok", False)
                    return False

        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            return False

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action input."""
        if self.operation == "send":
            return {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Message text to send"
                    },
                    "parse_mode": {
                        "type": "string",
                        "enum": ["Markdown", "HTML"],
                        "description": "Text parsing mode"
                    },
                    "reply_to_message_id": {
                        "type": "integer",
                        "description": "ID of message to reply to"
                    }
                },
                "required": ["text"]
            }
        elif self.operation == "respond":
            return {
                "type": "object",
                "properties": {
                    "original_message": {
                        "type": "object",
                        "description": "Original message object from Telegram"
                    },
                    "response_text": {
                        "type": "string",
                        "description": "Response text"
                    }
                },
                "required": ["original_message", "response_text"]
            }

        return {"type": "object", "properties": {}}

    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action output."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "operation": {"type": "string"},
                "chat_id": {"type": "string"},
                "result": {
                    "description": "Operation result (structure depends on operation)"
                },
                "error": {"type": "string"}
            },
            "required": ["success", "operation"]
        }
