"""
Unit tests for all action classes in FlowForge Python API.

This module contains comprehensive unit tests for:
- HTTP Actions (Request, Webhook Response)
- AI Actions (OpenAI, Claude, Gemini)
- Email Actions (Send Email, Parse Email)
- Data Actions (Transform, Filter, Aggregate)
- Storage Actions (Google Drive, S3 Upload)
- Notion Actions (Database, Page)
- Telegram Actions (Chat)
- Calendar Actions (Event)
- AI Agent Actions (Structured Output, Memory)
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from app.actions.http.request import HTTPAction
from app.actions.http.webhook_response import WebhookResponseAction
from app.actions.ai.openai_action import OpenAIAction
from app.actions.ai.claude_action import ClaudeAction
from app.actions.ai.gemini_action import GeminiAction
from app.actions.email.send_email import SendEmailAction
from app.actions.email.parse_email import ParseEmailAction
from app.actions.data.transform import DataTransformAction
from app.actions.data.filter import DataFilterAction
from app.actions.data.aggregate import DataAggregateAction
from app.actions.storage.google_drive import GoogleDriveAction
from app.actions.storage.s3_upload import S3UploadAction
from app.actions.notion.database_action import NotionDatabaseAction
from app.actions.notion.page_action import NotionPageAction
from app.actions.telegram.chat_action import TelegramChatAction
from app.actions.calendar.event_action import CalendarEventAction
from app.actions.ai_agent.structured_output import StructuredOutputAction
from app.actions.ai_agent.memory_action import MemoryAction
from app.core.context import ExecutionContext


class TestHTTPActions:
    """Test HTTP-related actions."""

    @pytest.fixture
    def execution_context(self):
        """Create a mock execution context."""
        return ExecutionContext(
            flow_id="test-flow",
            execution_id="test-exec",
            variables={"test": "value"},
            previous_outputs=[],
            user_id="test-user"
        )

    @pytest.mark.asyncio
    async def test_http_action_success(self, execution_context):
        """Test successful HTTP request action."""
        config = {
            "method": "GET",
            "url": "https://api.example.com/test",
            "headers": {"Authorization": "Bearer token"}
        }

        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = '{"success": true}'
            mock_response.json.return_value = {"success": True}

            mock_session.return_value.__aenter__.return_value.request.return_value = mock_response

            action = HTTPAction(config)
            result = await action.execute({}, execution_context)

            assert result["status_code"] == 200
            assert result["response"] == {"success": True}
            assert "headers" in result

    @pytest.mark.asyncio
    async def test_http_action_error_handling(self, execution_context):
        """Test HTTP action error handling."""
        config = {"method": "GET", "url": "https://api.example.com/test"}

        with patch("aiohttp.ClientSession") as mock_session:
            mock_session.return_value.__aenter__.return_value.request.side_effect = Exception("Connection failed")

            action = HTTPAction(config)
            result = await action.execute({}, execution_context)

            assert result["error"] == "Connection failed"
            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_webhook_response_action(self, execution_context):
        """Test webhook response action."""
        config = {"status_code": 201, "content_type": "application/json"}
        input_data = {"message": "success", "data": {"id": 123}}

        action = WebhookResponseAction(config)
        result = await action.execute(input_data, execution_context)

        assert result["status_code"] == 201
        assert result["content_type"] == "application/json"
        assert result["body"] == input_data


class TestAIActions:
    """Test AI-related actions."""

    @pytest.fixture
    def execution_context(self):
        return ExecutionContext(
            flow_id="test-flow",
            execution_id="test-exec",
            variables={},
            previous_outputs=[],
            user_id="test-user"
        )

    @pytest.mark.asyncio
    async def test_openai_action_success(self, execution_context):
        """Test successful OpenAI action."""
        config = {
            "api_key": "test-key",
            "model": "gpt-4",
            "system_prompt": "You are a helpful assistant"
        }
        input_data = {"prompt": "Hello, world!"}

        with patch("openai.ChatCompletion.acreate") as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hello! How can I help you?"
            mock_response.usage = MagicMock()
            mock_response.usage.dict.return_value = {"tokens": 10}
            mock_create.return_value = mock_response

            action = OpenAIAction(config)
            result = await action.execute(input_data, execution_context)

            assert result["response"] == "Hello! How can I help you?"
            assert result["usage"] == {"tokens": 10}
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_openai_action_missing_api_key(self, execution_context):
        """Test OpenAI action with missing API key."""
        config = {"model": "gpt-4"}
        input_data = {"prompt": "test"}

        action = OpenAIAction(config)
        result = await action.execute(input_data, execution_context)

        assert result["error"] == "OpenAI API key not configured"
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_claude_action_success(self, execution_context):
        """Test successful Claude action."""
        config = {
            "api_key": "test-key",
            "model": "claude-3-sonnet",
            "max_tokens": 1000
        }
        input_data = {"prompt": "Explain quantum computing"}

        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = "Quantum computing uses quantum mechanics..."
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            action = ClaudeAction(config)
            result = await action.execute(input_data, execution_context)

            assert result["response"] == "Quantum computing uses quantum mechanics..."
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_gemini_action_success(self, execution_context):
        """Test successful Gemini action."""
        config = {
            "api_key": "test-key",
            "model": "gemini-pro"
        }
        input_data = {"prompt": "What is machine learning?"}

        with patch("google.generativeai.GenerativeModel") as mock_model:
            mock_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Machine learning is a subset of AI..."
            mock_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_instance

            action = GeminiAction(config)
            result = await action.execute(input_data, execution_context)

            assert result["response"] == "Machine learning is a subset of AI..."
            assert result["success"] is True


class TestEmailActions:
    """Test email-related actions."""

    @pytest.fixture
    def execution_context(self):
        return ExecutionContext(
            flow_id="test-flow",
            execution_id="test-exec",
            variables={},
            previous_outputs=[],
            user_id="test-user"
        )

    @pytest.mark.asyncio
    async def test_send_email_action_success(self, execution_context):
        """Test successful email sending."""
        config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "test@example.com",
            "password": "test-password"
        }
        input_data = {
            "to": "recipient@example.com",
            "subject": "Test Email",
            "body": "This is a test email"
        }

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            action = SendEmailAction(config)
            result = await action.execute(input_data, execution_context)

            assert result["success"] is True
            assert result["message"] == "Email sent successfully"
            mock_server.sendmail.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_missing_config(self, execution_context):
        """Test email action with missing configuration."""
        config = {}
        input_data = {"to": "test@example.com", "subject": "Test"}

        action = SendEmailAction(config)
        result = await action.execute(input_data, execution_context)

        assert result["success"] is False
        assert "SMTP configuration missing" in result["error"]

    @pytest.mark.asyncio
    async def test_parse_email_action_success(self, execution_context):
        """Test successful email parsing."""
        config = {"extract_attachments": True}
        input_data = {
            "raw_email": "From: sender@example.com\nSubject: Test\n\nEmail body content"
        }

        action = ParseEmailAction(config)
        result = await action.execute(input_data, execution_context)

        assert result["success"] is True
        assert result["sender"] == "sender@example.com"
        assert result["subject"] == "Test"
        assert result["body"] == "Email body content"


class TestDataActions:
    """Test data processing actions."""

    @pytest.fixture
    def execution_context(self):
        return ExecutionContext(
            flow_id="test-flow",
            execution_id="test-exec",
            variables={},
            previous_outputs=[],
            user_id="test-user"
        )

    @pytest.mark.asyncio
    async def test_data_transform_action_success(self, execution_context):
        """Test successful data transformation."""
        config = {
            "transform_type": "json_to_csv",
            "field_mapping": {"name": "full_name", "age": "user_age"}
        }
        input_data = {
            "data": [
                {"name": "John", "age": 30},
                {"name": "Jane", "age": 25}
            ]
        }

        action = DataTransformAction(config)
        result = await action.execute(input_data, execution_context)

        assert result["success"] is True
        assert "transformed_data" in result
        assert len(result["transformed_data"]) == 2

    @pytest.mark.asyncio
    async def test_data_filter_action_success(self, execution_context):
        """Test successful data filtering."""
        config = {
            "filter_condition": "age > 25",
            "field_name": "age"
        }
        input_data = {
            "data": [
                {"name": "John", "age": 30},
                {"name": "Jane", "age": 25},
                {"name": "Bob", "age": 35}
            ]
        }

        action = DataFilterAction(config)
        result = await action.execute(input_data, execution_context)

        assert result["success"] is True
        assert len(result["filtered_data"]) == 2
        assert all(item["age"] > 25 for item in result["filtered_data"])

    @pytest.mark.asyncio
    async def test_data_aggregate_action_success(self, execution_context):
        """Test successful data aggregation."""
        config = {
            "group_by": "department",
            "aggregations": [{"field": "salary", "function": "sum"}]
        }
        input_data = {
            "data": [
                {"department": "Engineering", "salary": 80000},
                {"department": "Engineering", "salary": 90000},
                {"department": "Sales", "salary": 60000}
            ]
        }

        action = DataAggregateAction(config)
        result = await action.execute(input_data, execution_context)

        assert result["success"] is True
        assert "aggregated_data" in result
        assert result["aggregated_data"]["Engineering"]["salary_sum"] == 170000


class TestStorageActions:
    """Test storage-related actions."""

    @pytest.fixture
    def execution_context(self):
        return ExecutionContext(
            flow_id="test-flow",
            execution_id="test-exec",
            variables={},
            previous_outputs=[],
            user_id="test-user"
        )

    @pytest.mark.asyncio
    async def test_google_drive_upload_success(self, execution_context):
        """Test successful Google Drive upload."""
        config = {
            "credentials": {"type": "service_account"},
            "folder_id": "test-folder-id"
        }
        input_data = {
            "file_path": "/path/to/file.txt",
            "file_name": "test.txt",
            "mime_type": "text/plain"
        }

        with patch("googleapiclient.discovery.build") as mock_build:
            mock_service = MagicMock()
            mock_file = MagicMock()
            mock_file.execute.return_value = {"id": "file-id-123"}
            mock_service.files.return_value.create.return_value = mock_file
            mock_build.return_value = mock_service

            action = GoogleDriveAction(config)
            result = await action.execute(input_data, execution_context)

            assert result["success"] is True
            assert result["file_id"] == "file-id-123"

    @pytest.mark.asyncio
    async def test_s3_upload_success(self, execution_context):
        """Test successful S3 upload."""
        config = {
            "aws_access_key_id": "test-key",
            "aws_secret_access_key": "test-secret",
            "region_name": "us-east-1",
            "bucket_name": "test-bucket"
        }
        input_data = {
            "file_path": "/path/to/file.txt",
            "key": "uploads/file.txt"
        }

        with patch("boto3.client") as mock_client:
            mock_s3 = MagicMock()
            mock_client.return_value = mock_s3

            action = S3UploadAction(config)
            result = await action.execute(input_data, execution_context)

            assert result["success"] is True
            assert result["bucket"] == "test-bucket"
            mock_s3.upload_file.assert_called_once()


class TestNotionActions:
    """Test Notion-related actions."""

    @pytest.fixture
    def execution_context(self):
        return ExecutionContext(
            flow_id="test-flow",
            execution_id="test-exec",
            variables={},
            previous_outputs=[],
            user_id="test-user"
        )

    @pytest.mark.asyncio
    async def test_notion_database_query_success(self, execution_context):
        """Test successful Notion database query."""
        config = {
            "api_key": "test-key",
            "database_id": "test-db-id"
        }
        input_data = {
            "filter": {"property": "Status", "select": {"equals": "Active"}}
        }

        with patch("notion_client.Client") as mock_client:
            mock_notion = MagicMock()
            mock_response = {
                "results": [
                    {"id": "page-1", "properties": {"Name": {"title": [{"text": {"content": "Test Page"}}]}}}
                ]
            }
            mock_notion.databases.query.return_value = mock_response
            mock_client.return_value = mock_notion

            action = NotionDatabaseAction(config)
            result = await action.execute(input_data, execution_context)

            assert result["success"] is True
            assert len(result["results"]) == 1

    @pytest.mark.asyncio
    async def test_notion_page_create_success(self, execution_context):
        """Test successful Notion page creation."""
        config = {
            "api_key": "test-key",
            "database_id": "test-db-id"
        }
        input_data = {
            "properties": {
                "Name": {"title": [{"text": {"content": "New Page"}}]},
                "Status": {"select": {"name": "Active"}}
            }
        }

        with patch("notion_client.Client") as mock_client:
            mock_notion = MagicMock()
            mock_response = {"id": "new-page-id", "url": "https://notion.so/new-page"}
            mock_notion.pages.create.return_value = mock_response
            mock_client.return_value = mock_notion

            action = NotionPageAction(config)
            result = await action.execute(input_data, execution_context)

            assert result["success"] is True
            assert result["page_id"] == "new-page-id"


class TestTelegramActions:
    """Test Telegram-related actions."""

    @pytest.fixture
    def execution_context(self):
        return ExecutionContext(
            flow_id="test-flow",
            execution_id="test-exec",
            variables={},
            previous_outputs=[],
            user_id="test-user"
        )

    @pytest.mark.asyncio
    async def test_telegram_chat_send_success(self, execution_context):
        """Test successful Telegram chat message."""
        config = {
            "bot_token": "test-token",
            "chat_id": "123456789"
        }
        input_data = {
            "text": "Hello from FlowForge!",
            "parse_mode": "Markdown"
        }

        with patch("telegram.Bot") as mock_bot:
            mock_bot_instance = MagicMock()
            mock_bot.return_value = mock_bot_instance

            action = TelegramChatAction(config)
            result = await action.execute(input_data, execution_context)

            assert result["success"] is True
            assert result["message"] == "Message sent successfully"
            mock_bot_instance.send_message.assert_called_once()


class TestCalendarActions:
    """Test calendar-related actions."""

    @pytest.fixture
    def execution_context(self):
        return ExecutionContext(
            flow_id="test-flow",
            execution_id="test-exec",
            variables={},
            previous_outputs=[],
            user_id="test-user"
        )

    @pytest.mark.asyncio
    async def test_calendar_event_create_success(self, execution_context):
        """Test successful calendar event creation."""
        config = {
            "calendar_id": "primary",
            "credentials": {"type": "service_account"}
        }
        input_data = {
            "summary": "Team Meeting",
            "description": "Weekly team sync",
            "start_time": "2024-01-15T10:00:00Z",
            "end_time": "2024-01-15T11:00:00Z"
        }

        with patch("googleapiclient.discovery.build") as mock_build:
            mock_service = MagicMock()
            mock_event = MagicMock()
            mock_event.execute.return_value = {
                "id": "event-id-123",
                "htmlLink": "https://calendar.google.com/event-link"
            }
            mock_service.events.return_value.insert.return_value = mock_event
            mock_build.return_value = mock_service

            action = CalendarEventAction(config)
            result = await action.execute(input_data, execution_context)

            assert result["success"] is True
            assert result["event_id"] == "event-id-123"


class TestAIAgentActions:
    """Test AI agent-related actions."""

    @pytest.fixture
    def execution_context(self):
        return ExecutionContext(
            flow_id="test-flow",
            execution_id="test-exec",
            variables={},
            previous_outputs=[],
            user_id="test-user"
        )

    @pytest.mark.asyncio
    async def test_structured_output_success(self, execution_context):
        """Test successful structured output generation."""
        config = {
            "api_key": "test-key",
            "model": "gpt-4",
            "output_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                },
                "required": ["name", "age"]
            }
        }
        input_data = {
            "prompt": "Extract information about John Doe who is 30 years old"
        }

        with patch("openai.ChatCompletion.acreate") as mock_create:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"name": "John Doe", "age": 30}'
            mock_create.return_value = mock_response

            action = StructuredOutputAction(config)
            result = await action.execute(input_data, execution_context)

            assert result["success"] is True
            assert result["structured_data"]["name"] == "John Doe"
            assert result["structured_data"]["age"] == 30

    @pytest.mark.asyncio
    async def test_memory_store_success(self, execution_context):
        """Test successful memory storage."""
        config = {
            "memory_type": "conversation",
            "ttl_seconds": 3600
        }
        input_data = {
            "key": "user_preference",
            "value": {"theme": "dark", "language": "en"},
            "metadata": {"user_id": "123", "session_id": "abc"}
        }

        with patch("redis.Redis") as mock_redis:
            mock_client = MagicMock()
            mock_redis.return_value = mock_client

            action = MemoryAction(config)
            result = await action.execute(input_data, execution_context)

            assert result["success"] is True
            assert result["message"] == "Memory stored successfully"
            mock_client.setex.assert_called_once()


# Test configuration validation
class TestActionValidation:
    """Test action configuration validation."""

    def test_http_action_validation(self):
        """Test HTTP action configuration validation."""
        # Valid config
        valid_config = {
            "method": "GET",
            "url": "https://api.example.com/test"
        }
        action = HTTPAction(valid_config)
        assert action.validate_config() is True

        # Invalid config - missing URL
        invalid_config = {"method": "GET"}
        action = HTTPAction(invalid_config)
        assert action.validate_config() is False

    def test_openai_action_validation(self):
        """Test OpenAI action configuration validation."""
        # Valid config
        valid_config = {
            "api_key": "test-key",
            "model": "gpt-4"
        }
        action = OpenAIAction(valid_config)
        assert action.validate_config() is True

        # Invalid config - missing API key
        invalid_config = {"model": "gpt-4"}
        action = OpenAIAction(invalid_config)
        assert action.validate_config() is False

    def test_email_action_validation(self):
        """Test email action configuration validation."""
        # Valid config
        valid_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "test@example.com",
            "password": "password"
        }
        action = SendEmailAction(valid_config)
        assert action.validate_config() is True

        # Invalid config - missing required fields
        invalid_config = {"smtp_server": "smtp.gmail.com"}
        action = SendEmailAction(invalid_config)
        assert action.validate_config() is False


if __name__ == "__main__":
    pytest.main([__file__])
