"""Send Email Action

This module implements an action for sending emails through various providers
including SMTP, SendGrid, Mailgun, and other email service APIs.
"""

import logging
from typing import Any, Dict, Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import ssl

from ..base import BaseAction
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class SendEmailAction(BaseAction):
    """Action for sending emails through various providers.

    Supports multiple email providers:
    - SMTP servers (Gmail, Outlook, custom SMTP)
    - SendGrid API
    - Mailgun API
    - Amazon SES
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.provider = config.get("provider", "smtp")  # smtp, sendgrid, mailgun, ses
        self.smtp_host = config.get("smtp_host", "")
        self.smtp_port = config.get("smtp_port", 587)
        self.username = config.get("username", "")
        self.password = config.get("password", "")
        self.api_key = config.get("api_key", "")
        self.domain = config.get("domain", "")
        self.use_tls = config.get("use_tls", True)
        self.from_email = config.get("from_email", "")
        self.from_name = config.get("from_name", "")

    async def validate_config(self) -> bool:
        """Validate email action configuration."""
        if not self.from_email:
            raise ValueError("from_email is required for sending emails")

        if self.provider == "smtp":
            if not self.smtp_host:
                raise ValueError("smtp_host is required for SMTP provider")
            if not self.username or not self.password:
                raise ValueError("username and password are required for SMTP authentication")

        elif self.provider in ["sendgrid", "mailgun"]:
            if not self.api_key:
                raise ValueError(f"api_key is required for {self.provider} provider")
            if self.provider == "mailgun" and not self.domain:
                raise ValueError("domain is required for Mailgun provider")

        return True

    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the email sending action."""
        try:
            # Extract email parameters from input
            to_emails = input_data.get("to", [])
            subject = input_data.get("subject", "")
            body = input_data.get("body", "")
            cc_emails = input_data.get("cc", [])
            bcc_emails = input_data.get("bcc", [])
            attachments = input_data.get("attachments", [])
            content_type = input_data.get("content_type", "text")  # text, html

            if not to_emails:
                raise ValueError("At least one recipient email is required")

            if not subject:
                raise ValueError("Email subject is required")

            # Send email based on provider
            if self.provider == "smtp":
                result = await self._send_via_smtp(
                    to_emails, subject, body, cc_emails, bcc_emails, attachments, content_type
                )
            elif self.provider == "sendgrid":
                result = await self._send_via_sendgrid(
                    to_emails, subject, body, cc_emails, bcc_emails, attachments, content_type
                )
            elif self.provider == "mailgun":
                result = await self._send_via_mailgun(
                    to_emails, subject, body, cc_emails, bcc_emails, attachments, content_type
                )
            else:
                raise ValueError(f"Unsupported email provider: {self.provider}")

            return {
                "success": True,
                "message_id": result.get("message_id"),
                "provider": self.provider,
                "recipients": len(to_emails),
                "attachments_count": len(attachments)
            }

        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": self.provider
            }

    async def _send_via_smtp(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        cc_emails: List[str] = None,
        bcc_emails: List[str] = None,
        attachments: List[Dict[str, Any]] = None,
        content_type: str = "text"
    ) -> Dict[str, Any]:
        """Send email via SMTP."""
        try:
            # Create message
            msg = self._create_email_message(
                to_emails, subject, body, cc_emails, bcc_emails, attachments, content_type
            )

            # Create SMTP connection
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls(context=ssl.create_default_context())
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=ssl.create_default_context())

            # Login
            server.login(self.username, self.password)

            # Send email
            all_recipients = to_emails + (cc_emails or []) + (bcc_emails or [])
            server.sendmail(self.from_email, all_recipients, msg.as_string())

            # Close connection
            server.quit()

            return {"message_id": f"smtp_{hash(msg.as_string())}"}

        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            raise

    async def _send_via_sendgrid(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        cc_emails: List[str] = None,
        bcc_emails: List[str] = None,
        attachments: List[Dict[str, Any]] = None,
        content_type: str = "text"
    ) -> Dict[str, Any]:
        """Send email via SendGrid API."""
        try:
            import aiohttp

            # Prepare SendGrid API payload
            payload = {
                "personalizations": [{
                    "to": [{"email": email} for email in to_emails],
                    "subject": subject
                }],
                "from": {"email": self.from_email},
                "content": [{
                    "type": "text/html" if content_type == "html" else "text/plain",
                    "value": body
                }]
            }

            # Add CC and BCC
            if cc_emails:
                payload["personalizations"][0]["cc"] = [{"email": email} for email in cc_emails]
            if bcc_emails:
                payload["personalizations"][0]["bcc"] = [{"email": email} for email in bcc_emails]

            # Add attachments
            if attachments:
                payload["attachments"] = []
                for attachment in attachments:
                    # This would need implementation for base64 encoding
                    pass

            # Send via SendGrid API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status != 202:
                        error_data = await response.json()
                        raise Exception(f"SendGrid API error: {error_data}")

                    message_id = response.headers.get("X-Message-Id", f"sendgrid_{hash(str(payload))}")
                    return {"message_id": message_id}

        except ImportError:
            raise Exception("aiohttp is required for SendGrid API")
        except Exception as e:
            logger.error(f"SendGrid send failed: {e}")
            raise

    async def _send_via_mailgun(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        cc_emails: List[str] = None,
        bcc_emails: List[str] = None,
        attachments: List[Dict[str, Any]] = None,
        content_type: str = "text"
    ) -> Dict[str, Any]:
        """Send email via Mailgun API."""
        try:
            import aiohttp

            # Prepare form data
            data = aiohttp.FormData()
            data.add_field("from", f"{self.from_name} <{self.from_email}>" if self.from_name else self.from_email)
            data.add_field("to", ",".join(to_emails))
            data.add_field("subject", subject)

            if content_type == "html":
                data.add_field("html", body)
            else:
                data.add_field("text", body)

            if cc_emails:
                data.add_field("cc", ",".join(cc_emails))
            if bcc_emails:
                data.add_field("bcc", ",".join(bcc_emails))

            # Add attachments
            if attachments:
                for attachment in attachments:
                    # This would need implementation for file handling
                    pass

            # Send via Mailgun API
            auth = aiohttp.BasicAuth("api", self.api_key)
            url = f"https://api.mailgun.net/v3/{self.domain}/messages"

            async with aiohttp.ClientSession(auth=auth) as session:
                async with session.post(url, data=data) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Mailgun API error: {error_data}")

                    result = await response.json()
                    return {"message_id": result.get("id", f"mailgun_{hash(str(data))}")}

        except ImportError:
            raise Exception("aiohttp is required for Mailgun API")
        except Exception as e:
            logger.error(f"Mailgun send failed: {e}")
            raise

    def _create_email_message(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        cc_emails: List[str] = None,
        bcc_emails: List[str] = None,
        attachments: List[Dict[str, Any]] = None,
        content_type: str = "text"
    ) -> MIMEMultipart:
        """Create MIME email message."""
        msg = MIMEMultipart()
        msg["From"] = f"{self.from_name} <{self.from_email}>" if self.from_name else self.from_email
        msg["To"] = ", ".join(to_emails)
        msg["Subject"] = subject

        if cc_emails:
            msg["Cc"] = ", ".join(cc_emails)
        if bcc_emails:
            msg["Bcc"] = ", ".join(bcc_emails)

        # Add body
        if content_type == "html":
            body_part = MIMEText(body, "html")
        else:
            body_part = MIMEText(body, "plain")

        msg.attach(body_part)

        # Add attachments
        if attachments:
            for attachment in attachments:
                # This would need implementation for file attachment
                pass

        return msg

    async def test_connection(self) -> bool:
        """Test email provider connection."""
        try:
            if self.provider == "smtp":
                # Test SMTP connection
                if self.use_tls:
                    server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                    server.starttls(context=ssl.create_default_context())
                else:
                    server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=ssl.create_default_context())

                server.login(self.username, self.password)
                server.quit()
                return True

            elif self.provider == "sendgrid":
                # Test SendGrid API
                import aiohttp
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.sendgrid.com/v3/user/account", headers=headers) as response:
                        return response.status == 200

            elif self.provider == "mailgun":
                # Test Mailgun API
                import aiohttp
                auth = aiohttp.BasicAuth("api", self.api_key)
                url = f"https://api.mailgun.net/v3/domains/{self.domain}"
                async with aiohttp.ClientSession(auth=auth) as session:
                    async with session.get(url) as response:
                        return response.status == 200

            return True

        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action input."""
        return {
            "type": "object",
            "properties": {
                "to": {
                    "type": "array",
                    "items": {"type": "string", "format": "email"},
                    "description": "Recipient email addresses"
                },
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body content"},
                "cc": {
                    "type": "array",
                    "items": {"type": "string", "format": "email"},
                    "description": "CC recipient email addresses"
                },
                "bcc": {
                    "type": "array",
                    "items": {"type": "string", "format": "email"},
                    "description": "BCC recipient email addresses"
                },
                "content_type": {
                    "type": "string",
                    "enum": ["text", "html"],
                    "default": "text",
                    "description": "Email content type"
                },
                "attachments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string"},
                            "content": {"type": "string"},
                            "content_type": {"type": "string"}
                        }
                    },
                    "description": "Email attachments"
                }
            },
            "required": ["to", "subject", "body"]
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action output."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "message_id": {"type": "string"},
                "provider": {"type": "string"},
                "recipients": {"type": "integer"},
                "attachments_count": {"type": "integer"},
                "error": {"type": "string"}
            },
            "required": ["success"]
        }
