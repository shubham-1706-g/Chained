"""AI Agent Structured Output Action

This module implements an action for generating structured outputs from AI models
including JSON, XML, and other structured formats with validation.
"""

import logging
import json
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional, List
import re

from ..base import BaseAction
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class StructuredOutputAction(BaseAction):
    """Action for generating structured outputs from AI models.

    This action supports:
    - JSON output generation with schema validation
    - XML output generation
    - Structured data extraction from text
    - Output validation and formatting
    - Multiple AI provider integration
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.ai_provider = config.get("ai_provider", "openai")  # openai, claude, gemini
        self.model = config.get("model", "gpt-4")
        self.output_format = config.get("output_format", "json")  # json, xml, yaml
        self.output_schema = config.get("output_schema", {})
        self.system_prompt = config.get("system_prompt", "")
        self.max_tokens = config.get("max_tokens", 2000)
        self.temperature = config.get("temperature", 0.1)  # Lower temperature for structured output
        self.api_credentials = config.get("api_credentials", {})

    async def validate_config(self) -> bool:
        """Validate structured output action configuration."""
        valid_providers = ["openai", "claude", "gemini"]
        if self.ai_provider not in valid_providers:
            raise ValueError(f"Invalid AI provider: {self.ai_provider}. Must be one of {valid_providers}")

        valid_formats = ["json", "xml", "yaml", "csv"]
        if self.output_format not in valid_formats:
            raise ValueError(f"Invalid output format: {self.output_format}. Must be one of {valid_formats}")

        if self.output_format == "json" and not self.output_schema:
            logger.warning("Output schema recommended for JSON format")

        return True

    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the structured output generation."""
        try:
            prompt = input_data.get("prompt", "")
            if not prompt:
                raise ValueError("prompt is required for structured output generation")

            # Generate structured output based on provider
            if self.ai_provider == "openai":
                raw_output = await self._generate_openai_output(prompt)
            elif self.ai_provider == "claude":
                raw_output = await self._generate_claude_output(prompt)
            elif self.ai_provider == "gemini":
                raw_output = await self._generate_gemini_output(prompt)
            else:
                raise ValueError(f"Unsupported AI provider: {self.ai_provider}")

            # Parse and validate the output
            parsed_output = await self._parse_and_validate_output(raw_output)

            return {
                "success": True,
                "ai_provider": self.ai_provider,
                "output_format": self.output_format,
                "structured_output": parsed_output,
                "raw_output": raw_output
            }

        except Exception as e:
            logger.error(f"Structured output generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "ai_provider": self.ai_provider,
                "output_format": self.output_format
            }

    async def _generate_openai_output(self, prompt: str) -> str:
        """Generate structured output using OpenAI."""
        try:
            import aiohttp

            # Prepare the prompt with format instructions
            formatted_prompt = self._prepare_prompt(prompt)

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_prompt or "You are a helpful assistant that generates structured output."},
                    {"role": "user", "content": formatted_prompt}
                ],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }

            # Add JSON mode for OpenAI if JSON format
            if self.output_format == "json" and "gpt-4" in self.model:
                payload["response_format"] = {"type": "json_object"}

            headers = {
                "Authorization": f"Bearer {self.api_credentials.get('api_key', '')}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"OpenAI API error: {error_data}")

                    result = await response.json()
                    return result["choices"][0]["message"]["content"]

        except ImportError:
            raise Exception("aiohttp is required for OpenAI API requests")
        except Exception as e:
            logger.error(f"OpenAI structured output generation failed: {e}")
            raise

    async def _generate_claude_output(self, prompt: str) -> str:
        """Generate structured output using Claude."""
        try:
            import aiohttp

            formatted_prompt = self._prepare_prompt(prompt)

            payload = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [{"role": "user", "content": formatted_prompt}]
            }

            headers = {
                "x-api-key": self.api_credentials.get("api_key", ""),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Claude API error: {error_data}")

                    result = await response.json()
                    return result["content"][0]["text"]

        except ImportError:
            raise Exception("aiohttp is required for Claude API requests")
        except Exception as e:
            logger.error(f"Claude structured output generation failed: {e}")
            raise

    async def _generate_gemini_output(self, prompt: str) -> str:
        """Generate structured output using Gemini."""
        try:
            import aiohttp

            formatted_prompt = self._prepare_prompt(prompt)

            payload = {
                "contents": [{
                    "parts": [{"text": formatted_prompt}]
                }],
                "generation_config": {
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens
                }
            }

            if self.system_instruction:
                payload["system_instruction"] = {"parts": [{"text": self.system_instruction}]}

            async with aiohttp.ClientSession() as session:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_credentials.get('api_key', '')}"

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
                        return result["candidates"][0]["content"]["parts"][0]["text"]
                    else:
                        raise Exception("No content generated by Gemini")

        except ImportError:
            raise Exception("aiohttp is required for Gemini API requests")
        except Exception as e:
            logger.error(f"Gemini structured output generation failed: {e}")
            raise

    def _prepare_prompt(self, user_prompt: str) -> str:
        """Prepare the prompt with format instructions."""
        base_prompt = user_prompt

        if self.output_format == "json":
            format_instruction = f"""
Generate a JSON response following this schema:
{json.dumps(self.output_schema, indent=2)}

Return ONLY valid JSON, no additional text or explanations.
"""
            base_prompt += format_instruction

        elif self.output_format == "xml":
            format_instruction = """
Generate an XML response. Return ONLY valid XML, no additional text.
"""
            base_prompt += format_instruction

        elif self.output_format == "yaml":
            format_instruction = """
Generate a YAML response. Return ONLY valid YAML, no additional text.
"""
            base_prompt += format_instruction

        return base_prompt

    async def _parse_and_validate_output(self, raw_output: str) -> Any:
        """Parse and validate the AI-generated output."""
        try:
            if self.output_format == "json":
                return await self._parse_json_output(raw_output)
            elif self.output_format == "xml":
                return self._parse_xml_output(raw_output)
            elif self.output_format == "yaml":
                return self._parse_yaml_output(raw_output)
            elif self.output_format == "csv":
                return self._parse_csv_output(raw_output)
            else:
                return raw_output

        except Exception as e:
            logger.warning(f"Output parsing failed: {e}. Returning raw output.")
            return raw_output

    async def _parse_json_output(self, raw_output: str) -> Dict[str, Any]:
        """Parse and validate JSON output."""
        try:
            # Extract JSON from the response (AI might add extra text)
            json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
            else:
                parsed = json.loads(raw_output)

            # Validate against schema if provided
            if self.output_schema:
                await self._validate_json_schema(parsed, self.output_schema)

            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            raise Exception(f"Invalid JSON output: {str(e)}")

    def _parse_xml_output(self, raw_output: str) -> str:
        """Parse and validate XML output."""
        try:
            # Extract XML from the response
            xml_match = re.search(r'<.*>.*</.*>', raw_output, re.DOTALL)
            if xml_match:
                xml_str = xml_match.group()
                # Basic XML validation
                ET.fromstring(xml_str)
                return xml_str
            else:
                return raw_output

        except ET.ParseError as e:
            logger.error(f"XML parsing failed: {e}")
            raise Exception(f"Invalid XML output: {str(e)}")

    def _parse_yaml_output(self, raw_output: str) -> Any:
        """Parse YAML output."""
        try:
            import yaml
            return yaml.safe_load(raw_output)
        except ImportError:
            logger.warning("PyYAML not available, returning raw output")
            return raw_output
        except Exception as e:
            logger.error(f"YAML parsing failed: {e}")
            raise Exception(f"Invalid YAML output: {str(e)}")

    def _parse_csv_output(self, raw_output: str) -> List[Dict[str, Any]]:
        """Parse CSV output."""
        try:
            import csv
            import io

            # Parse CSV from string
            reader = csv.DictReader(io.StringIO(raw_output))
            return list(reader)

        except Exception as e:
            logger.error(f"CSV parsing failed: {e}")
            raise Exception(f"Invalid CSV output: {str(e)}")

    async def _validate_json_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """Validate JSON data against schema."""
        try:
            # Basic schema validation
            if "type" in schema and schema["type"] == "object":
                required_fields = schema.get("required", [])
                for field in required_fields:
                    if field not in data:
                        raise Exception(f"Required field missing: {field}")

                properties = schema.get("properties", {})
                for field, field_schema in properties.items():
                    if field in data:
                        field_type = field_schema.get("type")
                        if field_type and not self._validate_field_type(data[field], field_type):
                            raise Exception(f"Field {field} has invalid type. Expected {field_type}")

        except Exception as e:
            logger.warning(f"Schema validation failed: {e}")
            # Don't raise - just log the warning

    def _validate_field_type(self, value: Any, expected_type: str) -> bool:
        """Validate field type."""
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "number":
            return isinstance(value, (int, float))
        elif expected_type == "integer":
            return isinstance(value, int)
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        else:
            return True  # Unknown type, accept

    async def test_connection(self) -> bool:
        """Test AI provider connection."""
        try:
            if self.ai_provider == "openai":
                return await self._test_openai_connection()
            elif self.ai_provider == "claude":
                return await self._test_claude_connection()
            elif self.ai_provider == "gemini":
                return await self._test_gemini_connection()
            else:
                return False

        except Exception as e:
            logger.error(f"AI provider connection test failed: {e}")
            return False

    async def _test_openai_connection(self) -> bool:
        """Test OpenAI connection."""
        try:
            import aiohttp

            headers = {
                "Authorization": f"Bearer {self.api_credentials.get('api_key', '')}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.openai.com/v1/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200

        except Exception:
            return False

    async def _test_claude_connection(self) -> bool:
        """Test Claude connection."""
        try:
            import aiohttp

            headers = {
                "x-api-key": self.api_credentials.get("api_key", ""),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json={
                        "model": self.model,
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "Hello"}]
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200

        except Exception:
            return False

    async def _test_gemini_connection(self) -> bool:
        """Test Gemini connection."""
        try:
            import aiohttp

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
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_credentials.get('api_key', '')}"

                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200

        except Exception:
            return False

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action input."""
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The prompt for generating structured output"
                }
            },
            "required": ["prompt"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action output."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "ai_provider": {"type": "string"},
                "output_format": {"type": "string"},
                "structured_output": {
                    "description": "The parsed and validated structured output"
                },
                "raw_output": {
                    "type": "string",
                    "description": "The raw output from the AI model"
                },
                "error": {"type": "string"}
            },
            "required": ["success", "ai_provider", "output_format"]
        }
