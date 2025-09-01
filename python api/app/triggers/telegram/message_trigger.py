"""Telegram Message Trigger

This module implements triggers for Telegram message events including
new messages, chat updates, and bot interactions.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Callable, Awaitable
from datetime import datetime

from ..base import EventTrigger
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class TelegramMessageTrigger(EventTrigger):
    """Trigger for Telegram message events.

    This trigger monitors Telegram chats for:
    - New messages in chats
    - Messages matching specific patterns
    - Commands sent to the bot
    - Chat member updates
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.bot_token = config.get("bot_token", "")
        self.chat_ids = config.get("chat_ids", [])  # List of chat IDs to monitor
        self.event_types = config.get("event_types", ["message"])  # message, command, callback_query
        self.message_filters = config.get("message_filters", {})  # Text patterns, commands, etc.
        self.poll_interval = config.get("poll_interval", 5)  # seconds
        self.api_base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.last_update_id = 0

    async def validate_config(self) -> bool:
        """Validate Telegram message trigger configuration."""
        if not self.bot_token:
            raise ValueError("bot_token is required for Telegram message trigger")

        if not self.chat_ids and self.event_types != ["webhook"]:
            logger.warning("No chat_ids specified - will monitor all chats the bot has access to")

        valid_event_types = ["message", "command", "callback_query", "webhook"]
        for event_type in self.event_types:
            if event_type not in valid_event_types:
                raise ValueError(f"Invalid event type: {event_type}. Must be one of {valid_event_types}")

        if self.poll_interval < 1:
            raise ValueError("poll_interval must be at least 1 second")

        return True

    async def setup(self) -> None:
        """Set up the Telegram message trigger."""
        # Test bot connection and get bot info
        try:
            bot_info = await self._get_bot_info()
            self.bot_username = bot_info.get("username", "")
            logger.info(f"Telegram trigger setup for bot: @{self.bot_username}")
        except Exception as e:
            logger.warning(f"Could not get bot info during setup: {e}")

    async def start(self, callback: Callable[[ExecutionContext], Awaitable[None]]) -> None:
        """Start monitoring Telegram messages."""
        self.is_running = True
        self._callback = callback

        logger.info(f"Telegram message trigger started for bot: @{getattr(self, 'bot_username', 'unknown')}")

        if "webhook" in self.event_types:
            # Webhook mode - would need webhook URL setup
            logger.info("Telegram trigger running in webhook mode")
            # Webhook implementation would go here
        else:
            # Polling mode
            while self.is_running:
                try:
                    await self._check_for_updates()
                    await asyncio.sleep(self.poll_interval)
                except Exception as e:
                    logger.error(f"Error in message monitoring loop: {e}")
                    await asyncio.sleep(self.poll_interval)

    async def stop(self) -> None:
        """Stop the message trigger."""
        self.is_running = False
        logger.info("Telegram message trigger stopped")

    async def test_connection(self) -> bool:
        """Test Telegram bot connection."""
        try:
            await self._get_bot_info()
            return True
        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            return False

    async def _check_for_updates(self) -> None:
        """Check for new Telegram updates."""
        try:
            updates = await self._get_updates()

            if not updates.get("result"):
                return

            for update in updates["result"]:
                await self._process_update(update)

                # Update last processed update ID
                if update.get("update_id", 0) > self.last_update_id:
                    self.last_update_id = update["update_id"]

        except Exception as e:
            logger.error(f"Error checking for updates: {e}")

    async def _process_update(self, update: Dict[str, Any]) -> None:
        """Process a Telegram update."""
        try:
            update_id = update.get("update_id", 0)

            # Handle different update types
            if "message" in update and "message" in self.event_types:
                await self._process_message(update["message"])

            elif "callback_query" in update and "callback_query" in self.event_types:
                await self._process_callback_query(update["callback_query"])

            elif "inline_query" in update:
                # Handle inline queries if needed
                pass

        except Exception as e:
            logger.error(f"Error processing update {update_id}: {e}")

    async def _process_message(self, message: Dict[str, Any]) -> None:
        """Process a Telegram message."""
        try:
            chat_id = message.get("chat", {}).get("id")
            message_text = message.get("text", "")
            message_type = self._get_message_type(message)

            # Check if we should monitor this chat
            if self.chat_ids and str(chat_id) not in [str(cid) for cid in self.chat_ids]:
                return

            # Check message filters
            if not self._matches_message_filters(message):
                return

            # Determine event type
            event_type = "message"
            if message_text.startswith("/") and "command" in self.event_types:
                event_type = "command"
            elif "reply_to_message" in message:
                event_type = "reply"

            # Create execution context
            context = ExecutionContext(
                flow_id=f"telegram_chat_{chat_id}",
                execution_id=f"telegram_msg_{message.get('message_id')}_{int(datetime.utcnow().timestamp())}",
                user_id=self.config.get("user_id", "telegram_trigger")
            )

            # Add message data to context
            context.set_variable("telegram_event", {
                "type": event_type,
                "message_type": message_type,
                "chat_id": chat_id,
                "chat_type": message.get("chat", {}).get("type"),
                "message_id": message.get("message_id"),
                "text": message_text,
                "from_user": message.get("from", {}),
                "date": message.get("date"),
                "reply_to": message.get("reply_to_message"),
                "entities": message.get("entities", []),
                "event_time": datetime.utcnow().isoformat()
            })

            logger.info(f"Telegram message trigger fired: {event_type} in chat {chat_id}")

            # Trigger workflow execution
            await self.trigger_workflow(self._callback)

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _process_callback_query(self, callback_query: Dict[str, Any]) -> None:
        """Process a Telegram callback query."""
        try:
            chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
            data = callback_query.get("data", "")

            # Check if we should monitor this chat
            if self.chat_ids and str(chat_id) not in [str(cid) for cid in self.chat_ids]:
                return

            # Create execution context
            context = ExecutionContext(
                flow_id=f"telegram_callback_{chat_id}",
                execution_id=f"telegram_cb_{callback_query.get('id')}_{int(datetime.utcnow().timestamp())}",
                user_id=self.config.get("user_id", "telegram_trigger")
            )

            # Add callback data to context
            context.set_variable("telegram_event", {
                "type": "callback_query",
                "callback_id": callback_query.get("id"),
                "chat_id": chat_id,
                "from_user": callback_query.get("from", {}),
                "message": callback_query.get("message"),
                "data": data,
                "event_time": datetime.utcnow().isoformat()
            })

            logger.info(f"Telegram callback trigger fired for chat {chat_id}")

            # Trigger workflow execution
            await self.trigger_workflow(self._callback)

        except Exception as e:
            logger.error(f"Error processing callback query: {e}")

    def _get_message_type(self, message: Dict[str, Any]) -> str:
        """Determine the type of message."""
        if "text" in message:
            return "text"
        elif "photo" in message:
            return "photo"
        elif "document" in message:
            return "document"
        elif "audio" in message:
            return "audio"
        elif "video" in message:
            return "video"
        elif "sticker" in message:
            return "sticker"
        elif "animation" in message:
            return "animation"
        else:
            return "unknown"

    def _matches_message_filters(self, message: Dict[str, Any]) -> bool:
        """Check if message matches configured filters."""
        try:
            text = message.get("text", "")
            chat_type = message.get("chat", {}).get("type", "")

            # Check text patterns
            if "text_patterns" in self.message_filters:
                patterns = self.message_filters["text_patterns"]
                if not any(pattern.lower() in text.lower() for pattern in patterns):
                    return False

            # Check commands
            if "commands" in self.message_filters:
                commands = self.message_filters["commands"]
                if text.startswith("/"):
                    command = text.split()[0][1:]  # Remove /
                    if command not in commands:
                        return False

            # Check chat types
            if "chat_types" in self.message_filters:
                allowed_types = self.message_filters["chat_types"]
                if chat_type not in allowed_types:
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking message filters: {e}")
            return False

    async def _get_updates(self) -> Dict[str, Any]:
        """Get updates from Telegram."""
        try:
            import aiohttp

            params = {"timeout": 30}
            if self.last_update_id > 0:
                params["offset"] = self.last_update_id + 1

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/getUpdates",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=35)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Telegram API error: {error_data}")

                    return await response.json()

        except ImportError:
            raise Exception("aiohttp is required for Telegram API requests")
        except Exception as e:
            logger.error(f"Failed to get updates: {e}")
            raise

    async def _get_bot_info(self) -> Dict[str, Any]:
        """Get bot information."""
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/getMe",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Telegram API error: {error_data}")

                    result = await response.json()

                    if result.get("ok"):
                        return result.get("result", {})
                    else:
                        raise Exception(f"Telegram API returned not ok: {result}")

        except ImportError:
            raise Exception("aiohttp is required for Telegram API requests")
        except Exception as e:
            logger.error(f"Failed to get bot info: {e}")
            raise
