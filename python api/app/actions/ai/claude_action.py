"""Claude AI Action

This module implements an action for interacting with Anthropic's Claude AI model.
It supports text generation, conversation, and various AI tasks using Claude.
"""

import logging
from typing import Any, Dict, Optional, List
import json

from ..base import ApiAction
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class ClaudeAction(ApiAction):
    """Action for Anthropic Claude AI integration.

    This action supports:
    - Text generation and completion
    - Conversational AI
    - Code generation and explanation
    - Analysis and summarization
    - Custom prompts and system messages
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "claude-3-sonnet-20240229")
        self.system_prompt = config.get("system_prompt", "")
        self.max_tokens = config.get("max_tokens", 1000)
        self.temperature = config.get("temperature", 0.7)
        self.api_base_url = config.get("api_base_url", "https://api.anthropic.com")
        self.task_type = config.get("task_type", "completion")  # completion, conversation, analysis
        self.anthropic_version = config.get("anthropic_version", "2023-06-01")

    async def validate_config(self) -> bool:
        """Validate Claude action configuration."""
        await super().validate_config()

        if not self.api_key:
            raise ValueError("api_key is required for Claude action")

        valid_models = [
            "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20240620", "claude-2.1", "claude-2.0", "claude-instant-1.2"
        ]

        if self.model not in valid_models:
            logger.warning(f"Model {self.model} may not be valid. Valid models: {valid_models}")

        if not isinstance(self.max_tokens, int) or self.max_tokens < 1 or self.max_tokens > 4096:
            raise ValueError("max_tokens must be an integer between 1 and 4096")

        if not isinstance(self.temperature, (int, float)) or not (0 <= self.temperature <= 1):
            raise ValueError("temperature must be a number between 0 and 1")

        valid_task_types = ["completion", "conversation", "analysis", "code", "summary"]
        if self.task_type not in valid_task_types:
            raise ValueError(f"task_type must be one of: {valid_task_types}")

        return True

    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the Claude AI request."""
        try:
            if self.task_type == "conversation":
                return await self._execute_conversation(input_data)
            elif self.task_type == "completion":
                return await self._execute_completion(input_data)
            elif self.task_type == "analysis":
                return await self._execute_analysis(input_data)
            elif self.task_type == "code":
                return await self._execute_code_task(input_data)
            elif self.task_type == "summary":
                return await self._execute_summary(input_data)
            else:
                raise ValueError(f"Unsupported task type: {self.task_type}")

        except Exception as e:
            logger.error(f"Claude API request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "model": self.model,
                "task_type": self.task_type
            }

    async def _execute_conversation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a conversational AI request."""
        try:
            import aiohttp

            user_message = input_data.get("message", input_data.get("prompt", ""))
            if not user_message:
                raise ValueError("message or prompt is required for conversation")

            messages = []

            # Add system message if configured
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})

            # Add conversation history if provided
            conversation_history = input_data.get("conversation_history", [])
            for msg in conversation_history:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    # Convert from OpenAI format to Claude format if needed
                    if msg["role"] == "assistant":
                        msg["role"] = "assistant"
                    messages.append(msg)

            # Add user message
            messages.append({"role": "user", "content": user_message})

            payload = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": messages
            }

            # Add optional parameters
            for param in ["top_p", "top_k", "stop_sequences"]:
                if param in input_data:
                    payload[param] = input_data[param]

            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": self.anthropic_version,
                "content-type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Claude API error: {error_data}")

                    result = await response.json()

                    return {
                        "success": True,
                        "response": result["content"][0]["text"] if result.get("content") else "",
                        "finish_reason": result.get("stop_reason"),
                        "usage": result.get("usage", {}),
                        "model": result.get("model"),
                        "role": "assistant",
                        "raw_response": result
                    }

        except ImportError:
            raise Exception("aiohttp is required for Claude API requests")
        except Exception as e:
            logger.error(f"Conversation execution failed: {e}")
            raise

    async def _execute_completion(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a text completion request."""
        try:
            import aiohttp

            prompt = input_data.get("prompt", "")
            if not prompt:
                raise ValueError("prompt is required for completion")

            payload = {
                "model": self.model,
                "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                "max_tokens_to_sample": self.max_tokens,
                "temperature": self.temperature
            }

            # Add optional parameters
            for param in ["top_p", "top_k", "stop_sequences"]:
                if param in input_data:
                    payload[param] = input_data[param]

            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": self.anthropic_version,
                "content-type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/v1/complete",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Claude API error: {error_data}")

                    result = await response.json()

                    return {
                        "success": True,
                        "response": result.get("completion", ""),
                        "finish_reason": result.get("stop_reason"),
                        "usage": {"input_tokens": result.get("input_tokens", 0), "output_tokens": result.get("output_tokens", 0)},
                        "model": self.model,
                        "raw_response": result
                    }

        except ImportError:
            raise Exception("aiohttp is required for Claude API requests")
        except Exception as e:
            logger.error(f"Completion execution failed: {e}")
            raise

    async def _execute_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an analysis task."""
        try:
            content = input_data.get("content", "")
            analysis_type = input_data.get("analysis_type", "general")

            if not content:
                raise ValueError("content is required for analysis")

            # Create analysis prompt based on type
            if analysis_type == "sentiment":
                prompt = f"Analyze the sentiment of this text and provide a sentiment score from -1 (very negative) to 1 (very positive), plus a brief explanation: {content}"
            elif analysis_type == "summary":
                prompt = f"Provide a concise summary of the following text: {content}"
            elif analysis_type == "keywords":
                prompt = f"Extract the main keywords and key phrases from this text: {content}"
            elif analysis_type == "topics":
                prompt = f"Identify the main topics discussed in this text: {content}"
            else:
                prompt = f"Analyze this text and provide insights: {content}"

            analysis_input = {"prompt": prompt}
            return await self._execute_completion(analysis_input)

        except Exception as e:
            logger.error(f"Analysis execution failed: {e}")
            raise

    async def _execute_code_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a code-related task."""
        try:
            code_content = input_data.get("code", "")
            task_type = input_data.get("task_type", "explain")

            if not code_content:
                raise ValueError("code is required for code tasks")

            # Create code task prompt
            if task_type == "explain":
                prompt = f"Explain what this code does: {code_content}"
            elif task_type == "review":
                prompt = f"Review this code and suggest improvements: {code_content}"
            elif task_type == "optimize":
                prompt = f"Optimize this code for better performance: {code_content}"
            elif task_type == "debug":
                prompt = f"Debug this code and identify potential issues: {code_content}"
            else:
                prompt = f"Analyze this code: {code_content}"

            code_input = {"prompt": prompt}
            return await self._execute_completion(code_input)

        except Exception as e:
            logger.error(f"Code task execution failed: {e}")
            raise

    async def _execute_summary(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a summarization task."""
        try:
            content = input_data.get("content", "")
            summary_length = input_data.get("length", "medium")

            if not content:
                raise ValueError("content is required for summarization")

            length_guide = {
                "short": "brief 2-3 sentence",
                "medium": "concise paragraph",
                "long": "detailed multi-paragraph"
            }

            prompt = f"Provide a {length_guide.get(summary_length, 'concise')} summary of the following text: {content}"

            summary_input = {"prompt": prompt}
            return await self._execute_completion(summary_input)

        except Exception as e:
            logger.error(f"Summary execution failed: {e}")
            raise

    async def test_connection(self) -> bool:
        """Test Claude API connection."""
        try:
            import aiohttp

            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": self.anthropic_version,
                "content-type": "application/json"
            }

            # Simple test request
            payload = {
                "model": self.model,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Hello"}]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200

        except Exception as e:
            logger.error(f"Claude connection test failed: {e}")
            return False

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action input."""
        if self.task_type == "conversation":
            return {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "The message to send to Claude"},
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
        elif self.task_type == "analysis":
            return {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Content to analyze"},
                    "analysis_type": {
                        "type": "string",
                        "enum": ["sentiment", "summary", "keywords", "topics", "general"],
                        "default": "general",
                        "description": "Type of analysis to perform"
                    }
                },
                "required": ["content"]
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
                "role": {"type": "string"},
                "error": {"type": "string"},
                "raw_response": {"type": "object"}
            },
            "required": ["success"]
        }
