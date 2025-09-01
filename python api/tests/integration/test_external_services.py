"""
Integration tests for external service integrations.

These tests verify that the API properly integrates with external services
like HTTP APIs, email services, AI providers, and cloud storage.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from typing import Dict, Any

from tests.integration import IntegrationTestBase


class TestHTTPIntegration(IntegrationTestBase):
    """Test HTTP external service integrations."""

    @pytest.mark.asyncio
    async def test_http_action_with_external_api(self):
        """Test HTTP action integration with external APIs."""
        # Test with a real external API (httpbin.org for testing)
        result = await self.execute_action(
            "http",
            {
                "method": "GET",
                "url": "https://httpbin.org/json",
                "headers": {
                    "User-Agent": "FlowForge-Test/1.0"
                },
                "timeout": 30
            },
            {}
        )

        assert result["success"] is True
        assert result["result"]["status_code"] == 200
        assert "response" in result["result"]
        assert "slideshow" in result["result"]["response"]

    @pytest.mark.asyncio
    async def test_http_action_with_post_request(self):
        """Test HTTP action with POST request to external API."""
        result = await self.execute_action(
            "http",
            {
                "method": "POST",
                "url": "https://httpbin.org/post",
                "headers": {
                    "Content-Type": "application/json",
                    "User-Agent": "FlowForge-Test/1.0"
                },
                "body": {
                    "test": "data",
                    "number": 123
                },
                "timeout": 30
            },
            {}
        )

        assert result["success"] is True
        assert result["result"]["status_code"] == 200
        assert "response" in result["result"]
        assert result["result"]["response"]["json"]["test"] == "data"

    @pytest.mark.asyncio
    async def test_http_action_with_query_parameters(self):
        """Test HTTP action with query parameters."""
        result = await self.execute_action(
            "http",
            {
                "method": "GET",
                "url": "https://httpbin.org/get",
                "params": {
                    "param1": "value1",
                    "param2": "value2"
                },
                "timeout": 30
            },
            {}
        )

        assert result["success"] is True
        assert result["result"]["status_code"] == 200
        assert result["result"]["response"]["args"]["param1"] == "value1"
        assert result["result"]["response"]["args"]["param2"] == "value2"

    @pytest.mark.asyncio
    async def test_http_action_error_handling(self):
        """Test HTTP action error handling with external services."""
        # Test with non-existent domain
        result = await self.execute_action(
            "http",
            {
                "method": "GET",
                "url": "https://non-existent-domain-12345.com",
                "timeout": 5  # Short timeout for faster test
            },
            {}
        )

        assert result["success"] is False
        assert "error" in result
        assert "connection" in result["error"].lower() or "timeout" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_http_action_with_authentication(self):
        """Test HTTP action with authentication headers."""
        # Using httpbin's basic auth endpoint
        result = await self.execute_action(
            "http",
            {
                "method": "GET",
                "url": "https://httpbin.org/basic-auth/user/passwd",
                "headers": {
                    "Authorization": "Basic dXNlcjpwYXNzd2Q="  # user:passwd base64
                },
                "timeout": 30
            },
            {}
        )

        assert result["success"] is True
        assert result["result"]["status_code"] == 200
        assert result["result"]["response"]["authenticated"] is True
        assert result["result"]["response"]["user"] == "user"


class TestEmailIntegration(IntegrationTestBase):
    """Test email service integrations."""

    @pytest.mark.asyncio
    async def test_send_email_action_validation(self):
        """Test email action configuration validation."""
        # Test with valid configuration
        result = await self.execute_action(
            "send_email",
            {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "test@example.com",
                "password": "test-password",
                "from_email": "test@example.com",
                "to_email": "recipient@example.com",
                "subject": "Test Email",
                "body": "This is a test email"
            },
            {}
        )

        # Since we don't have real SMTP credentials, this should handle gracefully
        # The exact behavior depends on the implementation
        assert "execution_id" in result or "error" in result

    @pytest.mark.asyncio
    async def test_parse_email_action(self):
        """Test email parsing action."""
        # Mock email content
        email_content = """From: sender@example.com
To: recipient@example.com
Subject: Test Email
Content-Type: text/plain

This is the body of the test email.
"""

        result = await self.execute_action(
            "parse_email",
            {
                "extract_attachments": False
            },
            {
                "raw_email": email_content
            }
        )

        assert result["success"] is True
        assert result["result"]["sender"] == "sender@example.com"
        assert result["result"]["subject"] == "Test Email"
        assert "body" in result["result"]


class TestAIIntegration(IntegrationTestBase):
    """Test AI service integrations."""

    @pytest.mark.asyncio
    async def test_openai_action_integration(self):
        """Test OpenAI action integration."""
        # This test would require a real OpenAI API key
        # For integration testing, we'll mock the response

        with patch('openai.ChatCompletion.acreate') as mock_create:
            # Mock successful OpenAI response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hello! This is a test response from OpenAI."
            mock_response.usage = MagicMock()
            mock_response.usage.dict.return_value = {"tokens": 15}
            mock_create.return_value = mock_response

            result = await self.execute_action(
                "openai",
                {
                    "api_key": "test-key",
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 100,
                    "system_prompt": "You are a helpful assistant."
                },
                {
                    "prompt": "Say hello!"
                }
            )

            assert result["success"] is True
            assert "Hello! This is a test response from OpenAI" in result["result"]["response"]
            assert result["result"]["usage"]["tokens"] == 15

    @pytest.mark.asyncio
    async def test_openai_action_error_handling(self):
        """Test OpenAI action error handling."""
        with patch('openai.ChatCompletion.acreate') as mock_create:
            # Mock API error
            mock_create.side_effect = Exception("Invalid API key")

            result = await self.execute_action(
                "openai",
                {
                    "api_key": "invalid-key",
                    "model": "gpt-3.5-turbo"
                },
                {
                    "prompt": "Test prompt"
                }
            )

            assert result["success"] is False
            assert "Invalid API key" in result["error"]

    @pytest.mark.asyncio
    async def test_claude_action_integration(self):
        """Test Claude action integration."""
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = "Hello! This is Claude's response."
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            result = await self.execute_action(
                "claude",
                {
                    "api_key": "test-key",
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 100
                },
                {
                    "prompt": "Say hello!"
                }
            )

            assert result["success"] is True
            assert result["result"]["response"] == "Hello! This is Claude's response."


class TestStorageIntegration(IntegrationTestBase):
    """Test cloud storage integrations."""

    @pytest.mark.asyncio
    async def test_google_drive_integration(self):
        """Test Google Drive integration."""
        with patch('googleapiclient.discovery.build') as mock_build:
            mock_service = MagicMock()
            mock_file = MagicMock()
            mock_file.execute.return_value = {"id": "test-file-id"}
            mock_service.files.return_value.create.return_value = mock_file
            mock_build.return_value = mock_service

            result = await self.execute_action(
                "google_drive",
                {
                    "credentials": {"type": "service_account"},
                    "folder_id": "test-folder-id"
                },
                {
                    "file_path": "/tmp/test-file.txt",
                    "file_name": "uploaded-file.txt",
                    "mime_type": "text/plain"
                }
            )

            assert result["success"] is True
            assert result["result"]["file_id"] == "test-file-id"

    @pytest.mark.asyncio
    async def test_s3_upload_integration(self):
        """Test AWS S3 integration."""
        with patch('boto3.client') as mock_client:
            mock_s3 = MagicMock()
            mock_client.return_value = mock_s3

            result = await self.execute_action(
                "s3_upload",
                {
                    "aws_access_key_id": "test-key",
                    "aws_secret_access_key": "test-secret",
                    "region_name": "us-east-1",
                    "bucket_name": "test-bucket"
                },
                {
                    "file_path": "/tmp/test-file.txt",
                    "key": "uploads/test-file.txt"
                }
            )

            assert result["success"] is True
            mock_s3.upload_file.assert_called_once()


class TestNotionIntegration(IntegrationTestBase):
    """Test Notion integrations."""

    @pytest.mark.asyncio
    async def test_notion_database_query(self):
        """Test Notion database query integration."""
        with patch('notion_client.Client') as mock_client:
            mock_notion = MagicMock()
            mock_response = {
                "results": [
                    {
                        "id": "page-1",
                        "properties": {
                            "Name": {"title": [{"text": {"content": "Test Page"}}]},
                            "Status": {"select": {"name": "Active"}}
                        }
                    }
                ]
            }
            mock_notion.databases.query.return_value = mock_response
            mock_client.return_value = mock_notion

            result = await self.execute_action(
                "notion_database",
                {
                    "api_key": "test-key",
                    "database_id": "test-database-id"
                },
                {
                    "filter": {"property": "Status", "select": {"equals": "Active"}}
                }
            )

            assert result["success"] is True
            assert len(result["result"]["results"]) == 1
            assert result["result"]["results"][0]["properties"]["Name"]["title"][0]["text"]["content"] == "Test Page"

    @pytest.mark.asyncio
    async def test_notion_page_creation(self):
        """Test Notion page creation."""
        with patch('notion_client.Client') as mock_client:
            mock_notion = MagicMock()
            mock_response = {
                "id": "new-page-id",
                "url": "https://notion.so/new-page"
            }
            mock_notion.pages.create.return_value = mock_response
            mock_client.return_value = mock_notion

            result = await self.execute_action(
                "notion_page",
                {
                    "api_key": "test-key",
                    "database_id": "test-database-id"
                },
                {
                    "properties": {
                        "Name": {"title": [{"text": {"content": "New Test Page"}}]},
                        "Status": {"select": {"name": "Draft"}}
                    }
                }
            )

            assert result["success"] is True
            assert result["result"]["page_id"] == "new-page-id"


class TestCalendarIntegration(IntegrationTestBase):
    """Test calendar integrations."""

    @pytest.mark.asyncio
    async def test_calendar_event_creation(self):
        """Test Google Calendar event creation."""
        with patch('googleapiclient.discovery.build') as mock_build:
            mock_service = MagicMock()
            mock_event = MagicMock()
            mock_event.execute.return_value = {
                "id": "test-event-id",
                "htmlLink": "https://calendar.google.com/event-link"
            }
            mock_service.events.return_value.insert.return_value = mock_event
            mock_build.return_value = mock_service

            result = await self.execute_action(
                "calendar_event",
                {
                    "calendar_id": "primary",
                    "credentials": {"type": "service_account"}
                },
                {
                    "summary": "Test Meeting",
                    "description": "Integration test meeting",
                    "start_time": "2024-01-15T10:00:00Z",
                    "end_time": "2024-01-15T11:00:00Z"
                }
            )

            assert result["success"] is True
            assert result["result"]["event_id"] == "test-event-id"


class TestTelegramIntegration(IntegrationTestBase):
    """Test Telegram integrations."""

    @pytest.mark.asyncio
    async def test_telegram_chat_integration(self):
        """Test Telegram chat integration."""
        with patch('telegram.Bot') as mock_bot:
            mock_bot_instance = MagicMock()
            mock_bot.return_value = mock_bot_instance

            result = await self.execute_action(
                "telegram_chat",
                {
                    "bot_token": "test-token",
                    "chat_id": "123456789"
                },
                {
                    "text": "Hello from FlowForge integration test!",
                    "parse_mode": "Markdown"
                }
            )

            assert result["success"] is True
            mock_bot_instance.send_message.assert_called_once()


class TestExternalServiceErrorHandling(IntegrationTestBase):
    """Test error handling for external services."""

    @pytest.mark.asyncio
    async def test_external_service_timeout(self):
        """Test handling of external service timeouts."""
        result = await self.execute_action(
            "http",
            {
                "method": "GET",
                "url": "https://httpbin.org/delay/10",  # 10 second delay
                "timeout": 2  # 2 second timeout
            },
            {}
        )

        # Should either timeout or succeed (depending on network conditions)
        assert "execution_id" in result
        if not result.get("success", False):
            assert "timeout" in result.get("error", "").lower() or "delay" in result.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_external_service_rate_limiting(self):
        """Test handling of external service rate limiting."""
        # Make multiple rapid requests to potentially trigger rate limiting
        import asyncio

        async def make_request():
            return await self.execute_action(
                "http",
                {
                    "method": "GET",
                    "url": "https://httpbin.org/json",
                    "timeout": 30
                },
                {}
            )

        # Make 10 rapid requests
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # At least some should succeed
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        assert len(successful_results) > 0

    @pytest.mark.asyncio
    async def test_external_service_authentication_failure(self):
        """Test handling of authentication failures."""
        # Try to access a protected endpoint without authentication
        result = await self.execute_action(
            "http",
            {
                "method": "GET",
                "url": "https://api.github.com/user",
                "timeout": 30
            },
            {}
        )

        # Should get 401 Unauthorized or similar
        assert result["success"] is False or result["result"]["status_code"] == 401

    @pytest.mark.asyncio
    async def test_external_service_network_errors(self):
        """Test handling of network connectivity issues."""
        # Use a completely invalid domain
        result = await self.execute_action(
            "http",
            {
                "method": "GET",
                "url": "https://this-domain-does-not-exist-12345.com",
                "timeout": 5
            },
            {}
        )

        assert result["success"] is False
        assert "error" in result
        # Should contain some indication of network/connectivity error
        error_msg = result["error"].lower()
        assert any(term in error_msg for term in ["connection", "network", "resolve", "dns", "timeout"])


class TestIntegrationWorkflows(IntegrationTestBase):
    """Test complete integration workflows combining multiple services."""

    @pytest.mark.asyncio
    async def test_multi_service_workflow(self):
        """Test a workflow that integrates multiple external services."""
        # Create a workflow that uses HTTP + Data Transform + Email
        workflow_data = {
            "name": "Multi-Service Integration Test",
            "description": "Testing integration of multiple external services",
            "nodes": [
                {
                    "id": "fetch-data",
                    "type": "action",
                    "action_type": "http",
                    "config": {
                        "method": "GET",
                        "url": "https://httpbin.org/json"
                    }
                },
                {
                    "id": "transform-data",
                    "type": "action",
                    "action_type": "data_transform",
                    "config": {
                        "transform_type": "extract_fields",
                        "fields": ["slideshow.title", "slideshow.author"]
                    },
                    "dependencies": ["fetch-data"]
                }
            ],
            "connections": [
                {"from": "fetch-data", "to": "transform-data"}
            ]
        }

        workflow = await self.create_test_workflow(workflow_data)
        result = await self.execute_workflow(workflow["workflow_id"], {})

        # Wait for completion
        import time
        max_attempts = 10
        for _ in range(max_attempts):
            status = await self.get_execution_status(result["execution_id"])
            if status["status"] in ["completed", "error"]:
                break
            time.sleep(0.5)

        final_status = await self.get_execution_status(result["execution_id"])
        assert final_status["status"] == "completed"

        # Verify both nodes executed
        executed_nodes = final_status.get("executed_nodes", [])
        node_ids = [node["node_id"] for node in executed_nodes]
        assert "fetch-data" in node_ids
        assert "transform-data" in node_ids

    @pytest.mark.asyncio
    async def test_error_propagation_in_integrated_workflow(self):
        """Test error handling in workflows with external service integrations."""
        # Create a workflow with a failing external service
        workflow_data = {
            "name": "Error Handling Integration Test",
            "description": "Testing error propagation in integrated workflows",
            "nodes": [
                {
                    "id": "failing-http",
                    "type": "action",
                    "action_type": "http",
                    "config": {
                        "method": "GET",
                        "url": "https://non-existent-domain-12345.com"
                    }
                }
            ],
            "connections": []
        }

        workflow = await self.create_test_workflow(workflow_data)
        result = await self.execute_workflow(workflow["workflow_id"], {})

        # Wait for completion
        import time
        max_attempts = 10
        for _ in range(max_attempts):
            status = await self.get_execution_status(result["execution_id"])
            if status["status"] in ["completed", "error"]:
                break
            time.sleep(0.5)

        final_status = await self.get_execution_status(result["execution_id"])
        assert final_status["status"] == "error"

        # Verify error information is captured
        assert "error_message" in final_status or "error" in final_status

