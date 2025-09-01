"""Gemini AI Action

This module implements an action for interacting with Google's Gemini AI model.
It supports text generation, conversation, and various AI tasks using Gemini.
"""

import logging
from typing import Any, Dict, Optional, List
import json
import base64

from ..base import ApiAction
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class GeminiAction(ApiAction):
    """Action for Google Gemini AI integration.

    This action supports:
    - Text generation and completion
    - Multi-modal conversations (text and images)
    - Code generation and explanation
    - Analysis and summarization
    - Custom prompts and system instructions
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "gemini-pro")
        self.system_instruction = config.get("system_instruction", "")
        self.max_tokens = config.get("max_tokens", 1000)
        self.temperature = config.get("temperature", 0.7)
        self.api_base_url = config.get("api_base_url", "https://generativelanguage.googleapis.com")
        self.task_type = config.get("task_type", "completion")  # completion, conversation, analysis, vision
        self.safety_settings = config.get("safety_settings", [])

    async def validate_config(self) -> bool:
        """Validate Gemini action configuration."""
        await super().validate_config()

        if not self.api_key:
            raise ValueError("api_key is required for Gemini action")

        valid_models = [
            "gemini-pro", "gemini-pro-vision", "gemini-1.5-pro", "gemini-1.5-flash",
            "gemini-1.0-pro", "gemini-pro-vision"
        ]

        if self.model not in valid_models:
            logger.warning(f"Model {self.model} may not be valid. Valid models: {valid_models}")

        if not isinstance(self.max_tokens, int) or self.max_tokens < 1 or self.max_tokens > 8192:
            raise ValueError("max_tokens must be an integer between 1 and 8192")

        if not isinstance(self.temperature, (int, float)) or not (0 <= self.temperature <= 2):
            raise ValueError("temperature must be a number between 0 and 2")

        valid_task_types = ["completion", "conversation", "analysis", "vision", "code", "summary"]
        if self.task_type not in valid_task_types:
            raise ValueError(f"task_type must be one of: {valid_task_types}")

        return True

    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the Gemini AI request."""
        try:
            if self.task_type == "conversation":
                return await self._execute_conversation(input_data)
            elif self.task_type == "completion":
                return await self._execute_completion(input_data)
            elif self.task_type == "analysis":
                return await self._execute_analysis(input_data)
            elif self.task_type == "vision":
                return await self._execute_vision(input_data)
            elif self.task_type == "code":
                return await self._execute_code_task(input_data)
            elif self.task_type == "summary":
                return await self._execute_summary(input_data)
            else:
                raise ValueError(f"Unsupported task type: {self.task_type}")

        except Exception as e:
            logger.error(f"Gemini API request failed: {e}")
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

            # Prepare request payload
            payload = {
                "contents": [{
                    "parts": [{"text": user_message}]
                }]
            }

            # Add system instruction if configured
            if self.system_instruction:
                payload["system_instruction"] = {"parts": [{"text": self.system_instruction}]}

            # Add generation config
            payload["generation_config"] = {
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens
            }

            # Add safety settings if configured
            if self.safety_settings:
                payload["safety_settings"] = self.safety_settings

            # Add conversation history if provided
            conversation_history = input_data.get("conversation_history", [])
            if conversation_history:
                # Convert history to Gemini format
                history_parts = []
                for msg in conversation_history:
                    if isinstance(msg, dict) and "role" in msg and "content" in msg:
                        role = "user" if msg["role"] == "user" else "model"
                        history_parts.append({
                            "role": role,
                            "parts": [{"text": msg["content"]}]
                        })

                if history_parts:
                    payload["contents"] = history_parts + payload["contents"]

            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/v1beta/models/{self.model}:generateContent?key={self.api_key}"

                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Gemini API error: {error_data}")

                    result = await response.json()

                    if "candidates" in result and result["candidates"]:
                        candidate = result["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            response_text = candidate["content"]["parts"][0].get("text", "")

                            return {
                                "success": True,
                                "response": response_text,
                                "finish_reason": candidate.get("finish_reason"),
                                "usage": result.get("usage_metadata", {}),
                                "model": self.model,
                                "role": "model",
                                "raw_response": result
                            }

                    return {
                        "success": False,
                        "error": "No response generated",
                        "raw_response": result
                    }

        except ImportError:
            raise Exception("aiohttp is required for Gemini API requests")
        except Exception as e:
            logger.error(f"Conversation execution failed: {e}")
            raise

    async def _execute_completion(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a text completion request."""
        # For Gemini, completion is similar to conversation
        return await self._execute_conversation(input_data)

    async def _execute_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an analysis task."""
        try:
            content = input_data.get("content", "")
            analysis_type = input_data.get("analysis_type", "general")

            if not content:
                raise ValueError("content is required for analysis")

            # Create analysis prompt based on type
            prompts = {
                "sentiment": f"Analyze the sentiment of this text and provide a sentiment score from -1 (very negative) to 1 (very positive), plus a brief explanation: {content}",
                "summary": f"Provide a concise summary of the following text: {content}",
                "keywords": f"Extract the main keywords and key phrases from this text: {content}",
                "topics": f"Identify the main topics discussed in this text: {content}",
                "general": f"Analyze this text and provide insights: {content}"
            }

            analysis_prompt = prompts.get(analysis_type, prompts["general"])
            analysis_input = {"message": analysis_prompt}

            return await self._execute_conversation(analysis_input)

        except Exception as e:
            logger.error(f"Analysis execution failed: {e}")
            raise

    async def _execute_vision(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a vision analysis task."""
        try:
            import aiohttp

            image_data = input_data.get("image", "")
            prompt = input_data.get("prompt", "Describe this image")

            if not image_data:
                raise ValueError("image is required for vision tasks")

            # Prepare image data
            if isinstance(image_data, str) and image_data.startswith("data:"):
                # Base64 encoded image with data URL
                header, base64_data = image_data.split(",", 1)
                mime_type = header.split(";")[0].split(":")[1]
            elif isinstance(image_data, str):
                # Assume base64 encoded image
                base64_data = image_data
                mime_type = "image/jpeg"
            else:
                raise ValueError("Invalid image data format")

            # Prepare request payload for vision model
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64_data
                            }
                        }
                    ]
                }]
            }

            # Add generation config
            payload["generation_config"] = {
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens
            }

            async with aiohttp.ClientSession() as session:
                # Use vision model
                vision_model = self.model if "vision" in self.model else "gemini-pro-vision"
                url = f"{self.api_base_url}/v1beta/models/{vision_model}:generateContent?key={self.api_key}"

                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Gemini Vision API error: {error_data}")

                    result = await response.json()

                    if "candidates" in result and result["candidates"]:
                        candidate = result["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            response_text = candidate["content"]["parts"][0].get("text", "")

                            return {
                                "success": True,
                                "response": response_text,
                                "finish_reason": candidate.get("finish_reason"),
                                "usage": result.get("usage_metadata", {}),
                                "model": vision_model,
                                "task_type": "vision",
                                "raw_response": result
                            }

                    return {
                        "success": False,
                        "error": "No vision response generated",
                        "raw_response": result
                    }

        except ImportError:
            raise Exception("aiohttp is required for Gemini Vision API requests")
        except Exception as e:
            logger.error(f"Vision execution failed: {e}")
            raise

    async def _execute_code_task(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a code-related task."""
        try:
            code_content = input_data.get("code", "")
            task_type = input_data.get("task_type", "explain")

            if not code_content:
                raise ValueError("code is required for code tasks")

            # Create code task prompt
            prompts = {
                "explain": f"Explain what this code does: {code_content}",
                "review": f"Review this code and suggest improvements: {code_content}",
                "optimize": f"Optimize this code for better performance: {code_content}",
                "debug": f"Debug this code and identify potential issues: {code_content}",
                "generate": f"Generate code based on this description: {code_content}"
            }

            code_prompt = prompts.get(task_type, prompts["explain"])
            code_input = {"message": code_prompt}

            return await self._execute_conversation(code_input)

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

            summary_input = {"message": prompt}
            return await self._execute_conversation(summary_input)

        except Exception as e:
            logger.error(f"Summary execution failed: {e}")
            raise

    async def test_connection(self) -> bool:
        """Test Gemini API connection."""
        try:
            import aiohttp

            # Simple test request
            payload = {
                "contents": [{
                    "parts": [{"text": "Hello"}]
                }],
                "generation_config": {
                    "temperature": 0.7,
                    "max_output_tokens": 10
                }
            }

            async with aiohttp.ClientSession() as session:
                url = f"{self.api_base_url}/v1beta/models/{self.model}:generateContent?key={self.api_key}"

                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200

        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action input."""
        if self.task_type == "conversation":
            return {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "The message to send to Gemini"},
                    "conversation_history": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string", "enum": ["user", "model", "system"]},
                                "content": {"type": "string"}
                            }
                        },
                        "description": "Previous conversation messages"
                    }
                },
                "required": ["message"]
            }
        elif self.task_type == "vision":
            return {
                "type": "object",
                "properties": {
                    "image": {"type": "string", "description": "Base64 encoded image or data URL"},
                    "prompt": {"type": "string", "description": "Prompt for image analysis"}
                },
                "required": ["image"]
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
                "task_type": {"type": "string"},
                "error": {"type": "string"},
                "raw_response": {"type": "object"}
            },
            "required": ["success"]
        }
