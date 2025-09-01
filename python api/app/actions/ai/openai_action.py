"""OpenAI Action

This module implements an OpenAI action that can interact with
OpenAI's API for text generation, completion, and other AI tasks.
"""

import logging
from typing import Any, Dict, Optional, List
import json

from ..base import ApiAction
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class OpenAIAction(ApiAction):
    """OpenAI action for AI-powered text generation and completion.

    This action integrates with OpenAI's API to provide AI capabilities
    such as text completion, chat, and other language model tasks.
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "gpt-4")
        self.system_prompt = config.get("system_prompt", "")
        self.max_tokens = config.get("max_tokens", 1000)
        self.temperature = config.get("temperature", 0.7)
        self.api_base_url = config.get("api_base_url", "https://api.openai.com/v1")
        self.task_type = config.get("task_type", "completion")  # completion, chat, edit, etc.

    async def validate_config(self) -> bool:
        """Validate OpenAI action configuration."""
        await super().validate_config()

        if not self.api_key:
            raise ValueError("api_key is required for OpenAI action")

        valid_models = [
            "gpt-4", "gpt-4-turbo-preview", "gpt-4-vision-preview",
            "gpt-3.5-turbo", "gpt-3.5-turbo-16k",
            "text-davinci-003", "text-curie-001", "text-babbage-001", "text-ada-001"
        ]

        if self.model not in valid_models:
            logger.warning(f"Model {self.model} may not be valid. Valid models: {valid_models}")

        if not isinstance(self.max_tokens, int) or self.max_tokens < 1 or self.max_tokens > 4000:
            raise ValueError("max_tokens must be an integer between 1 and 4000")

        if not isinstance(self.temperature, (int, float)) or not (0 <= self.temperature <= 2):
            raise ValueError("temperature must be a number between 0 and 2")

        valid_task_types = ["completion", "chat", "edit", "embedding"]
        if self.task_type not in valid_task_types:
            raise ValueError(f"task_type must be one of: {valid_task_types}")

        return True

    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the OpenAI API request."""
        try:
            if self.task_type == "chat":
                return await self._execute_chat_completion(input_data)
            elif self.task_type == "completion":
                return await self._execute_text_completion(input_data)
            elif self.task_type == "edit":
                return await self._execute_edit(input_data)
            elif self.task_type == "embedding":
                return await self._execute_embedding(input_data)
            else:
                raise ValueError(f"Unsupported task type: {self.task_type}")

        except Exception as e:
            error_msg = f"OpenAI API request failed: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "data": None
            }

    async def _execute_chat_completion(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a chat completion request."""
        try:
            import aiohttp

            user_message = input_data.get("message", input_data.get("prompt", ""))
            if not user_message:
                raise ValueError("message or prompt is required for chat completion")

            messages = []

            # Add system message if configured
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})

            # Add conversation history if provided
            conversation_history = input_data.get("conversation_history", [])
            messages.extend(conversation_history)

            # Add user message
            messages.append({"role": "user", "content": user_message})

            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }

            # Add optional parameters
            for param in ["top_p", "presence_penalty", "frequency_penalty", "stop"]:
                if param in input_data:
                    payload[param] = input_data[param]

            headers = self.get_auth_headers()
            headers["Content-Type"] = "application/json"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"OpenAI API error: {error_data}")

                    result = await response.json()

                    choice = result["choices"][0]
                    return {
                        "success": True,
                        "response": choice["message"]["content"],
                        "finish_reason": choice["finish_reason"],
                        "usage": result.get("usage", {}),
                        "model": result.get("model"),
                        "raw_response": result
                    }

        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise

    async def _execute_text_completion(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a text completion request."""
        try:
            import aiohttp

            prompt = input_data.get("prompt", "")
            if not prompt:
                raise ValueError("prompt is required for text completion")

            payload = {
                "model": self.model,
                "prompt": prompt,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }

            # Add optional parameters
            for param in ["top_p", "presence_penalty", "frequency_penalty", "stop", "echo", "best_of"]:
                if param in input_data:
                    payload[param] = input_data[param]

            headers = self.get_auth_headers()
            headers["Content-Type"] = "application/json"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"OpenAI API error: {error_data}")

                    result = await response.json()

                    choice = result["choices"][0]
                    return {
                        "success": True,
                        "response": choice["text"],
                        "finish_reason": choice["finish_reason"],
                        "usage": result.get("usage", {}),
                        "model": result.get("model"),
                        "raw_response": result
                    }

        except Exception as e:
            logger.error(f"Text completion failed: {e}")
            raise

    async def _execute_edit(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an edit request."""
        try:
            import aiohttp

            input_text = input_data.get("input", "")
            instruction = input_data.get("instruction", "")

            if not input_text or not instruction:
                raise ValueError("input and instruction are required for edit")

            payload = {
                "model": self.model,
                "input": input_text,
                "instruction": instruction,
                "temperature": self.temperature
            }

            headers = self.get_auth_headers()
            headers["Content-Type"] = "application/json"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/edits",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"OpenAI API error: {error_data}")

                    result = await response.json()

                    choice = result["choices"][0]
                    return {
                        "success": True,
                        "response": choice["text"],
                        "usage": result.get("usage", {}),
                        "raw_response": result
                    }

        except Exception as e:
            logger.error(f"Edit request failed: {e}")
            raise

    async def _execute_embedding(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an embedding request."""
        try:
            import aiohttp

            input_text = input_data.get("input", "")
            if not input_text:
                raise ValueError("input is required for embedding")

            # Handle both single strings and lists
            if isinstance(input_text, str):
                input_text = [input_text]

            payload = {
                "model": self.model,
                "input": input_text
            }

            headers = self.get_auth_headers()
            headers["Content-Type"] = "application/json"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/embeddings",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"OpenAI API error: {error_data}")

                    result = await response.json()

                    return {
                        "success": True,
                        "embeddings": [item["embedding"] for item in result["data"]],
                        "usage": result.get("usage", {}),
                        "model": result.get("model"),
                        "raw_response": result
                    }

        except Exception as e:
            logger.error(f"Embedding request failed: {e}")
            raise

    async def test_connection(self) -> bool:
        """Test OpenAI API connection."""
        try:
            import aiohttp

            headers = self.get_auth_headers()
            headers["Content-Type"] = "application/json"

            # Simple test request to list models
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200

        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action input."""
        if self.task_type == "chat":
            return {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "The message to send to the chat model"},
                    "conversation_history": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string", "enum": ["user", "assistant", "system"]},
                                "content": {"type": "string"}
                            }
                        },
                        "description": "Previous conversation messages"
                    }
                },
                "required": ["message"]
            }
        elif self.task_type == "completion":
            return {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "The prompt for text completion"}
                },
                "required": ["prompt"]
            }
        elif self.task_type == "embedding":
            return {
                "type": "object",
                "properties": {
                    "input": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}}
                        ],
                        "description": "Text(s) to generate embeddings for"
                    }
                },
                "required": ["input"]
            }

        return {"type": "object", "properties": {}}

    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action output."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "response": {"type": "string"},
                "finish_reason": {"type": "string"},
                "usage": {"type": "object"},
                "model": {"type": "string"},
                "embeddings": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}},
                "error": {"type": "string"},
                "raw_response": {"type": "object"}
            },
            "required": ["success"]
        }
