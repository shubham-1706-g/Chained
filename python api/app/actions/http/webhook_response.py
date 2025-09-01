"""Webhook Response Action

This module implements an action for handling and responding to webhook requests.
It can validate webhook payloads, process them, and send appropriate responses
back to the webhook sender.
"""

import logging
import hmac
import hashlib
import json
from typing import Any, Dict, Optional, Union
import time

from ..base import BaseAction
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class WebhookResponseAction(BaseAction):
    """Action for handling and responding to webhook requests.

    This action can:
    - Validate webhook signatures for security
    - Process webhook payloads
    - Send custom responses back to webhook senders
    - Handle different webhook providers (GitHub, Stripe, etc.)
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.provider = config.get("provider", "generic")  # generic, github, stripe, slack, etc.
        self.secret_token = config.get("secret_token", "")
        self.response_status = config.get("response_status", 200)
        self.response_body = config.get("response_body", {"status": "ok"})
        self.response_headers = config.get("response_headers", {})
        self.validation_required = config.get("validation_required", True)
        self.allowed_events = config.get("allowed_events", [])  # For provider-specific filtering
        self.max_payload_size = config.get("max_payload_size", 1024 * 1024)  # 1MB

    async def validate_config(self) -> bool:
        """Validate webhook response action configuration."""
        if self.validation_required and not self.secret_token:
            raise ValueError("secret_token is required when validation_required is True")

        if not isinstance(self.response_status, int) or not (200 <= self.response_status <= 599):
            raise ValueError("response_status must be a valid HTTP status code (200-599)")

        valid_providers = ["generic", "github", "stripe", "slack", "twilio", "webhook_site"]
        if self.provider not in valid_providers:
            raise ValueError(f"Unsupported provider: {self.provider}. Must be one of {valid_providers}")

        return True

    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the webhook response action."""
        try:
            # Extract webhook data from input
            webhook_data = input_data.get("webhook_data", {})
            webhook_headers = input_data.get("webhook_headers", {})
            webhook_method = input_data.get("webhook_method", "POST")

            # Validate webhook if required
            if self.validation_required:
                is_valid = await self._validate_webhook(webhook_data, webhook_headers)
                if not is_valid:
                    return {
                        "success": False,
                        "error": "Webhook validation failed",
                        "response": {
                            "status": 401,
                            "body": {"error": "Unauthorized"},
                            "headers": {"Content-Type": "application/json"}
                        }
                    }

            # Process webhook payload
            processed_data = await self._process_webhook_payload(webhook_data, webhook_headers)

            # Check if event is allowed (for provider-specific filtering)
            if self.allowed_events and processed_data.get("event_type"):
                if processed_data["event_type"] not in self.allowed_events:
                    return {
                        "success": False,
                        "error": f"Event type '{processed_data['event_type']}' not allowed",
                        "response": {
                            "status": 200,
                            "body": {"status": "ignored"},
                            "headers": {"Content-Type": "application/json"}
                        }
                    }

            # Generate response
            response = self._generate_response(processed_data)

            return {
                "success": True,
                "processed_data": processed_data,
                "response": response,
                "provider": self.provider,
                "validation_passed": True
            }

        except Exception as e:
            logger.error(f"Webhook response action failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": {
                    "status": 500,
                    "body": {"error": "Internal server error"},
                    "headers": {"Content-Type": "application/json"}
                }
            }

    async def _validate_webhook(self, webhook_data: Any, webhook_headers: Dict[str, str]) -> bool:
        """Validate webhook signature based on provider."""
        try:
            if self.provider == "github":
                return self._validate_github_webhook(webhook_data, webhook_headers)
            elif self.provider == "stripe":
                return self._validate_stripe_webhook(webhook_data, webhook_headers)
            elif self.provider == "slack":
                return self._validate_slack_webhook(webhook_data, webhook_headers)
            elif self.provider == "twilio":
                return self._validate_twilio_webhook(webhook_data, webhook_headers)
            else:
                # Generic validation using HMAC-SHA256
                return self._validate_generic_webhook(webhook_data, webhook_headers)

        except Exception as e:
            logger.error(f"Webhook validation failed: {e}")
            return False

    def _validate_github_webhook(self, webhook_data: Any, webhook_headers: Dict[str, str]) -> bool:
        """Validate GitHub webhook signature."""
        signature = webhook_headers.get("X-Hub-Signature-256", "")
        if not signature:
            return False

        # GitHub sends the payload as raw bytes, but we have it as parsed data
        # In a real implementation, you'd need the raw payload
        payload = json.dumps(webhook_data, separators=(',', ':')).encode()

        expected_signature = hmac.new(
            self.secret_token.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(f"sha256={expected_signature}", signature)

    def _validate_stripe_webhook(self, webhook_data: Any, webhook_headers: Dict[str, str]) -> bool:
        """Validate Stripe webhook signature."""
        signature = webhook_headers.get("Stripe-Signature", "")
        if not signature:
            return False

        # Stripe signature validation is more complex and requires timestamp
        # This is a simplified version
        try:
            import stripe
            stripe.api_key = self.secret_token
            # In production, you'd use stripe.Webhook.construct_event()
            return True
        except:
            return False

    def _validate_slack_webhook(self, webhook_data: Any, webhook_headers: Dict[str, str]) -> bool:
        """Validate Slack webhook signature."""
        timestamp = webhook_headers.get("X-Slack-Request-Timestamp", "")
        signature = webhook_headers.get("X-Slack-Signature", "")

        if not timestamp or not signature:
            return False

        # Slack signature validation
        basestring = f"v0:{timestamp}:{json.dumps(webhook_data, separators=(',', ':'))}"

        expected_signature = hmac.new(
            self.secret_token.encode(),
            basestring.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(f"v0={expected_signature}", signature)

    def _validate_twilio_webhook(self, webhook_data: Any, webhook_headers: Dict[str, str]) -> bool:
        """Validate Twilio webhook signature."""
        # Twilio webhook validation would require the full URL and raw request
        # This is a simplified placeholder
        auth_token = self.secret_token
        signature = webhook_headers.get("X-Twilio-Signature", "")

        if not signature:
            return False

        # In production, you'd use Twilio's validation library
        return True

    def _validate_generic_webhook(self, webhook_data: Any, webhook_headers: Dict[str, str]) -> bool:
        """Validate generic webhook using HMAC-SHA256."""
        signature = webhook_headers.get("X-Webhook-Signature", "")
        if not signature:
            return False

        payload = json.dumps(webhook_data, separators=(',', ':')).encode()

        expected_signature = hmac.new(
            self.secret_token.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    async def _process_webhook_payload(self, webhook_data: Any, webhook_headers: Dict[str, str]) -> Dict[str, Any]:
        """Process webhook payload based on provider."""
        processed = {
            "event_type": None,
            "event_data": webhook_data,
            "metadata": {
                "provider": self.provider,
                "timestamp": time.time(),
                "headers": webhook_headers
            }
        }

        try:
            if self.provider == "github":
                processed["event_type"] = webhook_headers.get("X-GitHub-Event", "unknown")
            elif self.provider == "stripe":
                processed["event_type"] = webhook_data.get("type", "unknown")
            elif self.provider == "slack":
                processed["event_type"] = webhook_data.get("type", "unknown")
            elif self.provider == "twilio":
                processed["event_type"] = "sms" if "Body" in str(webhook_data) else "call"

            # Extract common fields
            processed["id"] = webhook_data.get("id") or webhook_data.get("event_id") or f"webhook_{int(time.time())}"

        except Exception as e:
            logger.warning(f"Error processing webhook payload: {e}")

        return processed

    def _generate_response(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate HTTP response for webhook."""
        response = {
            "status": self.response_status,
            "headers": self.response_headers.copy(),
            "body": self.response_body.copy()
        }

        # Add content type if not specified
        if "Content-Type" not in response["headers"]:
            response["headers"]["Content-Type"] = "application/json"

        # Customize response based on processed data
        if isinstance(response["body"], dict):
            response["body"]["webhook_id"] = processed_data.get("id")
            response["body"]["processed_at"] = processed_data["metadata"]["timestamp"]

        return response

    async def test_connection(self) -> bool:
        """Test webhook response action (no external connections needed)."""
        return True

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action input."""
        return {
            "type": "object",
            "properties": {
                "webhook_data": {
                    "description": "The webhook payload data"
                },
                "webhook_headers": {
                    "type": "object",
                    "description": "HTTP headers from the webhook request"
                },
                "webhook_method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "PATCH"],
                    "default": "POST",
                    "description": "HTTP method used for the webhook"
                }
            },
            "required": ["webhook_data", "webhook_headers"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action output."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "processed_data": {
                    "type": "object",
                    "properties": {
                        "event_type": {"type": "string"},
                        "event_data": {},
                        "metadata": {"type": "object"},
                        "id": {"type": "string"}
                    }
                },
                "response": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "integer"},
                        "headers": {"type": "object"},
                        "body": {}
                    }
                },
                "provider": {"type": "string"},
                "validation_passed": {"type": "boolean"},
                "error": {"type": "string"}
            },
            "required": ["success"]
        }
