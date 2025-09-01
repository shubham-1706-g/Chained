"""Parse Email Action

This module implements an action for parsing and extracting data from email content.
It can handle various email formats and extract structured data from email bodies,
headers, and attachments.
"""

import logging
import re
import json
from typing import Any, Dict, Optional, List, Union
from email import message_from_string
from email.header import decode_header
import base64

from ..base import BaseAction
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class ParseEmailAction(BaseAction):
    """Action for parsing and extracting data from email content.

    This action can parse raw email content and extract:
    - Email headers (subject, from, to, date, etc.)
    - Email body (text and HTML content)
    - Attachments and their metadata
    - Structured data from email content using patterns
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.extract_headers = config.get("extract_headers", True)
        self.extract_body = config.get("extract_body", True)
        self.extract_attachments = config.get("extract_attachments", False)
        self.body_format = config.get("body_format", "both")  # text, html, both
        self.patterns = config.get("patterns", {})  # Regex patterns for data extraction
        self.max_attachment_size = config.get("max_attachment_size", 10 * 1024 * 1024)  # 10MB

    async def validate_config(self) -> bool:
        """Validate email parsing action configuration."""
        if self.extract_attachments and self.max_attachment_size <= 0:
            raise ValueError("max_attachment_size must be positive when extracting attachments")

        if self.body_format not in ["text", "html", "both"]:
            raise ValueError("body_format must be 'text', 'html', or 'both'")

        return True

    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the email parsing action."""
        try:
            raw_email = input_data.get("raw_email", "")
            email_source = input_data.get("email_source", "raw")  # raw, imap, api

            if not raw_email:
                raise ValueError("raw_email is required for parsing")

            # Parse the email
            parsed_data = await self._parse_email(raw_email)

            # Extract structured data using patterns
            if self.patterns:
                structured_data = self._extract_structured_data(parsed_data)
                parsed_data["structured_data"] = structured_data

            return {
                "success": True,
                "parsed_data": parsed_data,
                "source": email_source
            }

        except Exception as e:
            logger.error(f"Email parsing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "parsed_data": None
            }

    async def _parse_email(self, raw_email: str) -> Dict[str, Any]:
        """Parse raw email content into structured data."""
        try:
            # Parse email message
            msg = message_from_string(raw_email)

            result = {}

            # Extract headers
            if self.extract_headers:
                result["headers"] = self._extract_headers(msg)

            # Extract body
            if self.extract_body:
                result["body"] = self._extract_body(msg)

            # Extract attachments
            if self.extract_attachments:
                result["attachments"] = self._extract_attachments(msg)

            # Extract basic metadata
            result["metadata"] = {
                "message_id": msg.get("Message-ID", "").strip("<>"),
                "date": msg.get("Date", ""),
                "size": len(raw_email),
                "has_attachments": self._has_attachments(msg)
            }

            return result

        except Exception as e:
            logger.error(f"Email parsing error: {e}")
            raise

    def _extract_headers(self, msg) -> Dict[str, Any]:
        """Extract email headers."""
        headers = {}

        # Standard headers
        header_fields = [
            "Subject", "From", "To", "Cc", "Bcc", "Reply-To",
            "Date", "Message-ID", "In-Reply-To", "References",
            "Content-Type", "User-Agent", "X-Mailer"
        ]

        for field in header_fields:
            value = msg.get(field, "")
            if value:
                headers[field.lower().replace("-", "_")] = self._decode_header(value)

        # Extract additional custom headers
        for header_name, header_value in msg.items():
            if header_name not in header_fields:
                headers[header_name.lower().replace("-", "_")] = self._decode_header(header_value)

        return headers

    def _extract_body(self, msg) -> Dict[str, Any]:
        """Extract email body content."""
        body = {}

        if msg.is_multipart():
            # Handle multipart messages
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Skip attachments
                if "attachment" in content_disposition:
                    continue

                if content_type == "text/plain" and (self.body_format in ["text", "both"]):
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        body["text"] = payload.decode(charset, errors="replace")

                elif content_type == "text/html" and (self.body_format in ["html", "both"]):
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        body["html"] = payload.decode(charset, errors="replace")
        else:
            # Handle simple messages
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                if msg.get_content_type() == "text/html" and self.body_format in ["html", "both"]:
                    body["html"] = payload.decode(charset, errors="replace")
                elif self.body_format in ["text", "both"]:
                    body["text"] = payload.decode(charset, errors="replace")

        return body

    def _extract_attachments(self, msg) -> List[Dict[str, Any]]:
        """Extract email attachments."""
        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        # Decode filename if necessary
                        filename = self._decode_header(filename)

                        # Get attachment size
                        payload = part.get_payload(decode=True)
                        if payload and len(payload) <= self.max_attachment_size:
                            attachments.append({
                                "filename": filename,
                                "content_type": part.get_content_type(),
                                "size": len(payload),
                                "content": base64.b64encode(payload).decode("utf-8")
                            })

        return attachments

    def _has_attachments(self, msg) -> bool:
        """Check if email has attachments."""
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                if "attachment" in content_disposition:
                    return True
        return False

    def _decode_header(self, header_value: str) -> str:
        """Decode email header with proper encoding handling."""
        try:
            decoded_parts = decode_header(header_value)
            decoded_string = ""

            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    decoded_string += part.decode(encoding or "utf-8", errors="replace")
                else:
                    decoded_string += str(part)

            return decoded_string
        except Exception:
            return header_value

    def _extract_structured_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data using regex patterns."""
        structured_data = {}

        # Get text content for pattern matching
        text_content = ""
        if "body" in parsed_data:
            if "text" in parsed_data["body"]:
                text_content += parsed_data["body"]["text"]
            if "html" in parsed_data["body"]:
                # Remove HTML tags for pattern matching
                html_content = re.sub(r"<[^>]+>", "", parsed_data["body"]["html"])
                text_content += " " + html_content

        # Apply patterns
        for field_name, pattern_config in self.patterns.items():
            if isinstance(pattern_config, str):
                # Simple pattern
                pattern = pattern_config
                flags = 0
            elif isinstance(pattern_config, dict):
                pattern = pattern_config.get("pattern", "")
                flags = pattern_config.get("flags", 0)
            else:
                continue

            try:
                compiled_pattern = re.compile(pattern, flags)
                match = compiled_pattern.search(text_content)

                if match:
                    if match.groups():
                        structured_data[field_name] = match.groups()[0] if len(match.groups()) == 1 else list(match.groups())
                    else:
                        structured_data[field_name] = match.group()
            except re.error as e:
                logger.warning(f"Invalid regex pattern for {field_name}: {e}")

        return structured_data

    async def test_connection(self) -> bool:
        """Test email parsing action (no external connections needed)."""
        return True

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action input."""
        return {
            "type": "object",
            "properties": {
                "raw_email": {
                    "type": "string",
                    "description": "Raw email content to parse"
                },
                "email_source": {
                    "type": "string",
                    "enum": ["raw", "imap", "api"],
                    "default": "raw",
                    "description": "Source of the email content"
                }
            },
            "required": ["raw_email"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action output."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "parsed_data": {
                    "type": "object",
                    "properties": {
                        "headers": {"type": "object"},
                        "body": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "html": {"type": "string"}
                            }
                        },
                        "attachments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "filename": {"type": "string"},
                                    "content_type": {"type": "string"},
                                    "size": {"type": "integer"},
                                    "content": {"type": "string"}
                                }
                            }
                        },
                        "metadata": {"type": "object"},
                        "structured_data": {"type": "object"}
                    }
                },
                "source": {"type": "string"},
                "error": {"type": "string"}
            },
            "required": ["success"]
        }
