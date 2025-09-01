"""
Unit tests for all trigger classes in FlowForge Python API.

This module contains comprehensive unit tests for:
- Webhook Triggers
- Schedule Triggers
- File Watch Triggers
- Notion Triggers (Database)
- Telegram Triggers (Message)
- Calendar Triggers (Event)
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import tempfile
import os


from app.triggers.webhook import WebhookTrigger
from app.triggers.schedule import ScheduleTrigger
from app.triggers.file_watch import FileWatchTrigger
from app.triggers.notion.database_trigger import NotionDatabaseTrigger
from app.triggers.telegram.message_trigger import TelegramMessageTrigger
from app.triggers.calendar.event_trigger import CalendarEventTrigger


class TestWebhookTrigger:
    """Test webhook trigger functionality."""

    @pytest.fixture
    def webhook_config(self):
        """Create webhook trigger configuration."""
        return {
            "webhook_id": "test-webhook-123",
            "secret": "webhook-secret",
            "validate_signature": True,
            "allowed_ips": ["192.168.1.1"]
        }

    @pytest.mark.asyncio
    async def test_webhook_trigger_setup_success(self, webhook_config):
        """Test successful webhook trigger setup."""
        trigger = WebhookTrigger(webhook_config)

        # Mock setup should complete without errors
        await trigger.setup()
        assert trigger.is_active is False

    @pytest.mark.asyncio
    async def test_webhook_trigger_start_with_callback(self, webhook_config):
        """Test webhook trigger start with callback."""
        trigger = WebhookTrigger(webhook_config)
        await trigger.setup()

        callback_called = False
        callback_data = None

        async def test_callback(data):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = data

        # Mock the start method to simulate webhook reception
        with patch.object(trigger, '_process_webhook_request') as mock_process:
            mock_process.return_value = {"event": "test", "payload": {"key": "value"}}

            await trigger.start(test_callback)
            assert trigger.is_active is True

            # Simulate webhook payload processing
            await mock_process({"body": '{"test": "data"}', "headers": {}})

    @pytest.mark.asyncio
    async def test_webhook_trigger_stop(self, webhook_config):
        """Test webhook trigger stop functionality."""
        trigger = WebhookTrigger(webhook_config)
        await trigger.setup()

        # Start trigger
        async def dummy_callback(data):
            pass

        await trigger.start(dummy_callback)
        assert trigger.is_active is True

        # Stop trigger
        await trigger.stop()
        assert trigger.is_active is False


class TestScheduleTrigger:
    """Test schedule trigger functionality."""

    @pytest.fixture
    def schedule_config(self):
        """Create schedule trigger configuration."""
        return {
            "schedule_type": "cron",
            "cron_expression": "0 */2 * * *",  # Every 2 hours
            "timezone": "UTC",
            "max_executions": 10
        }

    @pytest.mark.asyncio
    async def test_schedule_trigger_setup_success(self, schedule_config):
        """Test successful schedule trigger setup."""
        trigger = ScheduleTrigger(schedule_config)
        await trigger.setup()
        assert trigger.is_active is False

    @pytest.mark.asyncio
    async def test_schedule_trigger_start_with_callback(self, schedule_config):
        """Test schedule trigger start with callback."""
        trigger = ScheduleTrigger(schedule_config)
        await trigger.setup()

        callback_called = False
        callback_data = None

        async def test_callback(data):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = data

        # Mock the scheduling to avoid waiting
        with patch('schedule.every') as mock_every:
            mock_job = MagicMock()
            mock_every.return_value = mock_job

            await trigger.start(test_callback)
            assert trigger.is_active is True

            # Simulate job execution
            await trigger._execute_scheduled_task()
            assert callback_called is True
            assert "timestamp" in callback_data

    @pytest.mark.asyncio
    async def test_schedule_trigger_stop(self, schedule_config):
        """Test schedule trigger stop functionality."""
        trigger = ScheduleTrigger(schedule_config)
        await trigger.setup()

        async def dummy_callback(data):
            pass

        await trigger.start(dummy_callback)
        assert trigger.is_active is True

        await trigger.stop()
        assert trigger.is_active is False

    @pytest.mark.asyncio
    async def test_schedule_trigger_cron_parsing(self, schedule_config):
        """Test cron expression parsing."""
        trigger = ScheduleTrigger(schedule_config)
        await trigger.setup()

        # Test valid cron expression
        assert trigger._parse_cron_expression("0 * * * *") is not None

        # Test invalid cron expression
        with pytest.raises(ValueError):
            trigger._parse_cron_expression("invalid")

    @pytest.mark.asyncio
    async def test_schedule_trigger_time_calculation(self, schedule_config):
        """Test next execution time calculation."""
        trigger = ScheduleTrigger(schedule_config)

        # Test immediate execution
        immediate_config = schedule_config.copy()
        immediate_config["cron_expression"] = "* * * * *"  # Every minute

        trigger_immediate = ScheduleTrigger(immediate_config)
        next_time = trigger_immediate._get_next_execution_time()

        assert next_time is not None
        assert isinstance(next_time, datetime)


class TestFileWatchTrigger:
    """Test file watch trigger functionality."""

    @pytest.fixture
    def file_watch_config(self):
        """Create file watch trigger configuration."""
        return {
            "watch_path": "/tmp/watch",
            "file_pattern": "*.txt",
            "watch_events": ["created", "modified"],
            "recursive": True,
            "ignore_patterns": ["*.tmp"]
        }

    @pytest.mark.asyncio
    async def test_file_watch_trigger_setup_success(self, file_watch_config):
        """Test successful file watch trigger setup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = file_watch_config.copy()
            config["watch_path"] = temp_dir

            trigger = FileWatchTrigger(config)
            await trigger.setup()
            assert trigger.is_active is False

    @pytest.mark.asyncio
    async def test_file_watch_trigger_start_with_callback(self, file_watch_config):
        """Test file watch trigger start with callback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = file_watch_config.copy()
            config["watch_path"] = temp_dir

            trigger = FileWatchTrigger(config)
            await trigger.setup()

            callback_called = False
            callback_data = None

            async def test_callback(data):
                nonlocal callback_called, callback_data
                callback_called = True
                callback_data = data

            # Mock the file watching
            with patch('watchdog.observers.Observer') as mock_observer:
                mock_observer_instance = MagicMock()
                mock_observer.return_value = mock_observer_instance

                await trigger.start(test_callback)
                assert trigger.is_active is True

                # Simulate file event
                await trigger._on_file_event(
                    MagicMock(
                        src_path=os.path.join(temp_dir, "test.txt"),
                        event_type="created"
                    )
                )

                assert callback_called is True
                assert "file_path" in callback_data
                assert callback_data["event_type"] == "created"

    @pytest.mark.asyncio
    async def test_file_watch_trigger_pattern_matching(self, file_watch_config):
        """Test file pattern matching."""
        trigger = FileWatchTrigger(file_watch_config)

        # Test matching patterns
        assert trigger._matches_pattern("test.txt", "*.txt") is True
        assert trigger._matches_pattern("test.log", "*.txt") is False

        # Test ignore patterns
        assert trigger._should_ignore("test.tmp", ["*.tmp"]) is True
        assert trigger._should_ignore("test.txt", ["*.tmp"]) is False

    @pytest.mark.asyncio
    async def test_file_watch_trigger_stop(self, file_watch_config):
        """Test file watch trigger stop functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = file_watch_config.copy()
            config["watch_path"] = temp_dir

            trigger = FileWatchTrigger(config)
            await trigger.setup()

            async def dummy_callback(data):
                pass

            await trigger.start(dummy_callback)
            assert trigger.is_active is True

            await trigger.stop()
            assert trigger.is_active is False


class TestNotionDatabaseTrigger:
    """Test Notion database trigger functionality."""

    @pytest.fixture
    def notion_config(self):
        """Create Notion database trigger configuration."""
        return {
            "api_key": "test-api-key",
            "database_id": "test-database-id",
            "poll_interval": 30,
            "filter_conditions": {"property": "Status", "select": {"equals": "Active"}}
        }

    @pytest.mark.asyncio
    async def test_notion_trigger_setup_success(self, notion_config):
        """Test successful Notion trigger setup."""
        with patch("notion_client.Client") as mock_client:
            mock_notion = MagicMock()
            mock_client.return_value = mock_notion

            trigger = NotionDatabaseTrigger(notion_config)
            await trigger.setup()

            assert trigger.is_active is False
            mock_client.assert_called_once_with(auth=notion_config["api_key"])

    @pytest.mark.asyncio
    async def test_notion_trigger_start_with_callback(self, notion_config):
        """Test Notion trigger start with callback."""
        with patch("notion_client.Client") as mock_client:
            mock_notion = MagicMock()
            mock_client.return_value = mock_notion

            # Mock database query response
            mock_response = {
                "results": [
                    {
                        "id": "page-1",
                        "last_edited_time": "2024-01-15T10:00:00Z",
                        "properties": {"Name": {"title": [{"text": {"content": "New Item"}}]}}
                    }
                ]
            }
            mock_notion.databases.query.return_value = mock_response

            trigger = NotionDatabaseTrigger(notion_config)
            await trigger.setup()

            callback_called = False
            callback_data = None

            async def test_callback(data):
                nonlocal callback_called, callback_data
                callback_called = True
                callback_data = data

            await trigger.start(test_callback)
            assert trigger.is_active is True

            # Simulate polling
            await trigger._poll_database()

            assert callback_called is True
            assert "new_items" in callback_data
            assert len(callback_data["new_items"]) == 1

    @pytest.mark.asyncio
    async def test_notion_trigger_filter_processing(self, notion_config):
        """Test Notion trigger filter processing."""
        trigger = NotionDatabaseTrigger(notion_config)

        # Test filter condition parsing
        filter_conditions = {"property": "Status", "select": {"equals": "Active"}}
        parsed_filter = trigger._parse_filter_conditions(filter_conditions)

        assert parsed_filter is not None
        assert "filter" in parsed_filter

    @pytest.mark.asyncio
    async def test_notion_trigger_stop(self, notion_config):
        """Test Notion trigger stop functionality."""
        with patch("notion_client.Client") as mock_client:
            mock_notion = MagicMock()
            mock_client.return_value = mock_notion

            trigger = NotionDatabaseTrigger(notion_config)
            await trigger.setup()

            async def dummy_callback(data):
                pass

            await trigger.start(dummy_callback)
            assert trigger.is_active is True

            await trigger.stop()
            assert trigger.is_active is False


class TestTelegramMessageTrigger:
    """Test Telegram message trigger functionality."""

    @pytest.fixture
    def telegram_config(self):
        """Create Telegram message trigger configuration."""
        return {
            "bot_token": "test-bot-token",
            "allowed_chat_ids": ["123456789", "-1001234567890"],
            "message_types": ["text", "photo"],
            "poll_interval": 1
        }

    @pytest.mark.asyncio
    async def test_telegram_trigger_setup_success(self, telegram_config):
        """Test successful Telegram trigger setup."""
        with patch("telegram.Bot") as mock_bot:
            mock_bot_instance = MagicMock()
            mock_bot.return_value = mock_bot_instance

            trigger = TelegramMessageTrigger(telegram_config)
            await trigger.setup()

            assert trigger.is_active is False
            mock_bot.assert_called_once_with(token=telegram_config["bot_token"])

    @pytest.mark.asyncio
    async def test_telegram_trigger_start_with_callback(self, telegram_config):
        """Test Telegram trigger start with callback."""
        with patch("telegram.Bot") as mock_bot:
            mock_bot_instance = MagicMock()
            mock_bot_instance.get_updates.return_value = [
                MagicMock(
                    message=MagicMock(
                        message_id=1,
                        chat=MagicMock(id=123456789),
                        text="Hello from Telegram!",
                        from_user=MagicMock(username="testuser")
                    )
                )
            ]
            mock_bot.return_value = mock_bot_instance

            trigger = TelegramMessageTrigger(telegram_config)
            await trigger.setup()

            callback_called = False
            callback_data = None

            async def test_callback(data):
                nonlocal callback_called, callback_data
                callback_called = True
                callback_data = data

            await trigger.start(test_callback)
            assert trigger.is_active is True

            # Simulate message polling
            await trigger._poll_messages()

            assert callback_called is True
            assert "message" in callback_data
            assert callback_data["message"]["text"] == "Hello from Telegram!"

    @pytest.mark.asyncio
    async def test_telegram_trigger_chat_filtering(self, telegram_config):
        """Test Telegram trigger chat ID filtering."""
        trigger = TelegramMessageTrigger(telegram_config)

        # Test allowed chat
        assert trigger._is_chat_allowed(123456789) is True

        # Test disallowed chat
        assert trigger._is_chat_allowed(999999999) is False

    @pytest.mark.asyncio
    async def test_telegram_trigger_stop(self, telegram_config):
        """Test Telegram trigger stop functionality."""
        with patch("telegram.Bot") as mock_bot:
            mock_bot_instance = MagicMock()
            mock_bot.return_value = mock_bot_instance

            trigger = TelegramMessageTrigger(telegram_config)
            await trigger.setup()

            async def dummy_callback(data):
                pass

            await trigger.start(dummy_callback)
            assert trigger.is_active is True

            await trigger.stop()
            assert trigger.is_active is False


class TestCalendarEventTrigger:
    """Test calendar event trigger functionality."""

    @pytest.fixture
    def calendar_config(self):
        """Create calendar event trigger configuration."""
        return {
            "calendar_id": "primary",
            "credentials": {"type": "service_account"},
            "poll_interval": 60,
            "event_types": ["created", "updated"],
            "time_window_minutes": 30
        }

    @pytest.mark.asyncio
    async def test_calendar_trigger_setup_success(self, calendar_config):
        """Test successful calendar trigger setup."""
        with patch("googleapiclient.discovery.build") as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service

            trigger = CalendarEventTrigger(calendar_config)
            await trigger.setup()

            assert trigger.is_active is False
            mock_build.assert_called_once()

    @pytest.mark.asyncio
    async def test_calendar_trigger_start_with_callback(self, calendar_config):
        """Test calendar trigger start with callback."""
        with patch("googleapiclient.discovery.build") as mock_build:
            mock_service = MagicMock()
            mock_events = MagicMock()
            mock_events.execute.return_value = {
                "items": [
                    {
                        "id": "event-1",
                        "summary": "New Meeting",
                        "start": {"dateTime": "2024-01-15T10:00:00Z"},
                        "end": {"dateTime": "2024-01-15T11:00:00Z"},
                        "created": "2024-01-15T09:00:00Z"
                    }
                ]
            }
            mock_service.events.return_value.list.return_value = mock_events
            mock_build.return_value = mock_service

            trigger = CalendarEventTrigger(calendar_config)
            await trigger.setup()

            callback_called = False
            callback_data = None

            async def test_callback(data):
                nonlocal callback_called, callback_data
                callback_called = True
                callback_data = data

            await trigger.start(test_callback)
            assert trigger.is_active is True

            # Simulate event polling
            await trigger._poll_events()

            assert callback_called is True
            assert "new_events" in callback_data
            assert len(callback_data["new_events"]) == 1

    @pytest.mark.asyncio
    async def test_calendar_trigger_event_filtering(self, calendar_config):
        """Test calendar trigger event filtering."""
        trigger = CalendarEventTrigger(calendar_config)

        # Test event within time window
        recent_event = {
            "created": datetime.utcnow().isoformat() + "Z",
            "summary": "Recent Event"
        }
        assert trigger._is_event_recent(recent_event) is True

        # Test event outside time window
        old_event = {
            "created": (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z",
            "summary": "Old Event"
        }
        assert trigger._is_event_recent(old_event) is False

    @pytest.mark.asyncio
    async def test_calendar_trigger_stop(self, calendar_config):
        """Test calendar trigger stop functionality."""
        with patch("googleapiclient.discovery.build") as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service

            trigger = CalendarEventTrigger(calendar_config)
            await trigger.setup()

            async def dummy_callback(data):
                pass

            await trigger.start(dummy_callback)
            assert trigger.is_active is True

            await trigger.stop()
            assert trigger.is_active is False


class TestTriggerValidation:
    """Test trigger configuration validation."""

    def test_webhook_trigger_validation(self):
        """Test webhook trigger configuration validation."""
        # Valid config
        valid_config = {
            "webhook_id": "test-webhook",
            "secret": "secret-key"
        }
        trigger = WebhookTrigger(valid_config)
        assert trigger._validate_config() is True

        # Invalid config - missing webhook_id
        invalid_config = {"secret": "secret-key"}
        trigger = WebhookTrigger(invalid_config)
        assert trigger._validate_config() is False

    def test_schedule_trigger_validation(self):
        """Test schedule trigger configuration validation."""
        # Valid config
        valid_config = {
            "schedule_type": "cron",
            "cron_expression": "0 * * * *"
        }
        trigger = ScheduleTrigger(valid_config)
        assert trigger._validate_config() is True

        # Invalid config - invalid cron
        invalid_config = {
            "schedule_type": "cron",
            "cron_expression": "invalid"
        }
        trigger = ScheduleTrigger(invalid_config)
        assert trigger._validate_config() is False

    def test_file_watch_trigger_validation(self):
        """Test file watch trigger configuration validation."""
        # Valid config
        with tempfile.TemporaryDirectory() as temp_dir:
            valid_config = {
                "watch_path": temp_dir,
                "file_pattern": "*.txt"
            }
            trigger = FileWatchTrigger(valid_config)
            assert trigger._validate_config() is True

        # Invalid config - non-existent path
        invalid_config = {
            "watch_path": "/non/existent/path",
            "file_pattern": "*.txt"
        }
        trigger = FileWatchTrigger(invalid_config)
        assert trigger._validate_config() is False

    def test_notion_trigger_validation(self):
        """Test Notion trigger configuration validation."""
        # Valid config
        valid_config = {
            "api_key": "test-key",
            "database_id": "test-db-id"
        }
        trigger = NotionDatabaseTrigger(valid_config)
        assert trigger._validate_config() is True

        # Invalid config - missing API key
        invalid_config = {"database_id": "test-db-id"}
        trigger = NotionDatabaseTrigger(invalid_config)
        assert trigger._validate_config() is False

    def test_telegram_trigger_validation(self):
        """Test Telegram trigger configuration validation."""
        # Valid config
        valid_config = {
            "bot_token": "test-token",
            "allowed_chat_ids": ["123456789"]
        }
        trigger = TelegramMessageTrigger(valid_config)
        assert trigger._validate_config() is True

        # Invalid config - missing bot token
        invalid_config = {"allowed_chat_ids": ["123456789"]}
        trigger = TelegramMessageTrigger(invalid_config)
        assert trigger._validate_config() is False

    def test_calendar_trigger_validation(self):
        """Test calendar trigger configuration validation."""
        # Valid config
        valid_config = {
            "calendar_id": "primary",
            "credentials": {"type": "service_account"}
        }
        trigger = CalendarEventTrigger(valid_config)
        assert trigger._validate_config() is True

        # Invalid config - missing credentials
        invalid_config = {"calendar_id": "primary"}
        trigger = CalendarEventTrigger(invalid_config)
        assert trigger._validate_config() is False


if __name__ == "__main__":
    pytest.main([__file__])
