"""Calendar Event Trigger

This module implements triggers for calendar event changes including
new events, updated events, upcoming events, and event reminders.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Callable, Awaitable
from datetime import datetime, timedelta

from ..base import EventTrigger
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class CalendarEventTrigger(EventTrigger):
    """Trigger for calendar event changes.

    This trigger monitors calendars for:
    - New events created
    - Existing events updated
    - Upcoming events (reminders)
    - Events starting soon
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.provider = config.get("provider", "google")  # google, outlook, ical
        self.calendar_id = config.get("calendar_id", "primary")
        self.event_types = config.get("event_types", ["created", "updated"])  # created, updated, upcoming, starting
        self.poll_interval = config.get("poll_interval", 300)  # 5 minutes default
        self.lookahead_hours = config.get("lookahead_hours", 24)  # Look ahead for upcoming events
        self.reminder_minutes = config.get("reminder_minutes", [15, 60])  # When to trigger reminders
        self.api_credentials = config.get("api_credentials", {})

        # Provider-specific URLs
        if self.provider == "google":
            self.api_base_url = "https://www.googleapis.com/calendar/v3"
        elif self.provider == "outlook":
            self.api_base_url = "https://graph.microsoft.com/v1.0/me/events"
        else:
            self.api_base_url = config.get("api_base_url", "")

        self.last_sync_token = None
        self.processed_events = set()

    async def validate_config(self) -> bool:
        """Validate calendar event trigger configuration."""
        valid_providers = ["google", "outlook", "ical", "api"]
        if self.provider not in valid_providers:
            raise ValueError(f"Invalid provider: {self.provider}. Must be one of {valid_providers}")

        valid_event_types = ["created", "updated", "upcoming", "starting"]
        for event_type in self.event_types:
            if event_type not in valid_event_types:
                raise ValueError(f"Invalid event type: {event_type}. Must be one of {valid_event_types}")

        if self.poll_interval < 60:
            raise ValueError("poll_interval must be at least 60 seconds")

        if self.provider in ["google", "outlook"] and not self.api_credentials:
            raise ValueError(f"api_credentials required for {self.provider} provider")

        return True

    async def setup(self) -> None:
        """Set up the calendar event trigger."""
        # Test connection and get initial calendar state
        try:
            calendar_info = await self._get_calendar_info()
            self.calendar_name = calendar_info.get("summary", "Unknown Calendar")
            logger.info(f"Monitoring calendar: {self.calendar_name}")
        except Exception as e:
            logger.warning(f"Could not get calendar info during setup: {e}")

    async def start(self, callback: Callable[[ExecutionContext], Awaitable[None]]) -> None:
        """Start monitoring calendar events."""
        self.is_running = True
        self._callback = callback

        logger.info(f"Calendar event trigger started for {self.provider} calendar: {self.calendar_id}")

        # Initial check
        await self._check_for_events()

        while self.is_running:
            try:
                await asyncio.sleep(self.poll_interval)
                if self.is_running:  # Check again after sleep
                    await self._check_for_events()
            except Exception as e:
                logger.error(f"Error in calendar monitoring loop: {e}")
                await asyncio.sleep(self.poll_interval)

    async def stop(self) -> None:
        """Stop the calendar event trigger."""
        self.is_running = False
        logger.info(f"Calendar event trigger stopped for calendar: {self.calendar_id}")

    async def test_connection(self) -> bool:
        """Test calendar provider connection."""
        try:
            await self._get_calendar_info()
            return True
        except Exception as e:
            logger.error(f"Calendar connection test failed: {e}")
            return False

    async def _check_for_events(self) -> None:
        """Check for calendar events and trigger workflows."""
        try:
            current_time = datetime.utcnow()

            # Check for different event types
            if "created" in self.event_types or "updated" in self.event_types:
                await self._check_recent_events(current_time)

            if "upcoming" in self.event_types:
                await self._check_upcoming_events(current_time)

            if "starting" in self.event_types:
                await self._check_starting_events(current_time)

        except Exception as e:
            logger.error(f"Error checking calendar events: {e}")

    async def _check_recent_events(self, current_time: datetime) -> None:
        """Check for recently created or updated events."""
        try:
            # Get events from the last poll interval plus some buffer
            start_time = current_time - timedelta(seconds=self.poll_interval + 60)

            events = await self._get_events(start_time.isoformat(), current_time.isoformat())

            for event in events.get("events", []):
                event_id = event.get("id")
                updated_time = event.get("updated")

                if not event_id or event_id in self.processed_events:
                    continue

                # Check if this is a new or recently updated event
                if updated_time:
                    updated_dt = datetime.fromisoformat(updated_time.replace('Z', '+00:00'))

                    # If updated within our polling window, it's likely new/updated
                    if (current_time - updated_dt).total_seconds() < self.poll_interval + 60:
                        event_type = "created" if event.get("created") == updated_time else "updated"

                        if event_type in self.event_types:
                            await self._trigger_event(event_type, event, current_time)
                            self.processed_events.add(event_id)

        except Exception as e:
            logger.error(f"Error checking recent events: {e}")

    async def _check_upcoming_events(self, current_time: datetime) -> None:
        """Check for upcoming events that need reminders."""
        try:
            # Look ahead for upcoming events
            end_time = current_time + timedelta(hours=self.lookahead_hours)
            events = await self._get_events(current_time.isoformat(), end_time.isoformat())

            for event in events.get("events", []):
                event_id = event.get("id")
                start_time = event.get("start", {}).get("dateTime")

                if not start_time or not event_id:
                    continue

                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                time_until_start = start_dt - current_time

                # Check if we should send reminders
                for reminder_minutes in self.reminder_minutes:
                    reminder_time = start_dt - timedelta(minutes=reminder_minutes)

                    # If current time is around the reminder time
                    if abs((current_time - reminder_time).total_seconds()) < 60:  # Within 1 minute
                        reminder_key = f"{event_id}_reminder_{reminder_minutes}"
                        if reminder_key not in self.processed_events:
                            await self._trigger_event("upcoming", event, current_time, reminder_minutes)
                            self.processed_events.add(reminder_key)

        except Exception as e:
            logger.error(f"Error checking upcoming events: {e}")

    async def _check_starting_events(self, current_time: datetime) -> None:
        """Check for events that are starting soon."""
        try:
            # Look for events starting within the next few minutes
            end_time = current_time + timedelta(minutes=5)
            events = await self._get_events(current_time.isoformat(), end_time.isoformat())

            for event in events.get("events", []):
                event_id = event.get("id")
                start_time = event.get("start", {}).get("dateTime")

                if not start_time or not event_id:
                    continue

                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                time_until_start = start_dt - current_time

                # If event starts within 1 minute and we haven't triggered it yet
                if 0 <= time_until_start.total_seconds() <= 60:
                    trigger_key = f"{event_id}_starting"
                    if trigger_key not in self.processed_events:
                        await self._trigger_event("starting", event, current_time)
                        self.processed_events.add(trigger_key)

        except Exception as e:
            logger.error(f"Error checking starting events: {e}")

    async def _trigger_event(self, event_type: str, event: Dict[str, Any], trigger_time: datetime, reminder_minutes: Optional[int] = None) -> None:
        """Trigger a workflow event for a calendar event."""
        try:
            # Create execution context
            context = ExecutionContext(
                flow_id=f"calendar_{self.calendar_id}",
                execution_id=f"calendar_{event_type}_{event.get('id')}_{int(trigger_time.timestamp())}",
                user_id=self.config.get("user_id", "calendar_trigger")
            )

            # Add event data to context
            context.set_variable("calendar_event", {
                "type": event_type,
                "calendar_id": self.calendar_id,
                "calendar_name": getattr(self, 'calendar_name', 'Unknown'),
                "event_id": event.get("id"),
                "summary": event.get("summary"),
                "description": event.get("description"),
                "start": event.get("start"),
                "end": event.get("end"),
                "location": event.get("location"),
                "attendees": event.get("attendees", []),
                "status": event.get("status"),
                "html_link": event.get("htmlLink"),
                "created": event.get("created"),
                "updated": event.get("updated"),
                "reminder_minutes": reminder_minutes,
                "trigger_time": trigger_time.isoformat()
            })

            logger.info(f"Calendar event trigger fired: {event_type} for event '{event.get('summary')}'")

            # Trigger workflow execution
            await self.trigger_workflow(self._callback)

        except Exception as e:
            logger.error(f"Error triggering calendar event: {e}")

    async def _get_events(self, start_time: str, end_time: str) -> Dict[str, Any]:
        """Get calendar events within a time range."""
        try:
            if self.provider == "google":
                return await self._get_google_events(start_time, end_time)
            elif self.provider == "outlook":
                return await self._get_outlook_events(start_time, end_time)
            else:
                return {"events": []}

        except Exception as e:
            logger.error(f"Error getting calendar events: {e}")
            return {"events": []}

    async def _get_google_events(self, start_time: str, end_time: str) -> Dict[str, Any]:
        """Get Google Calendar events."""
        try:
            import aiohttp

            access_token = self.api_credentials.get("access_token")
            if not access_token:
                return {"events": []}

            url = f"{self.api_base_url}/calendars/{self.calendar_id}/events"
            params = {
                "timeMin": start_time,
                "timeMax": end_time,
                "singleEvents": "true",
                "orderBy": "startTime"
            }

            headers = {"Authorization": f"Bearer {access_token}"}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        logger.error(f"Google Calendar API error: {error_data}")
                        return {"events": []}

                    result = await response.json()
                    return {
                        "events": result.get("items", []),
                        "count": len(result.get("items", []))
                    }

        except ImportError:
            logger.error("aiohttp is required for Google Calendar API requests")
            return {"events": []}
        except Exception as e:
            logger.error(f"Google Calendar event retrieval failed: {e}")
            return {"events": []}

    async def _get_outlook_events(self, start_time: str, end_time: str) -> Dict[str, Any]:
        """Get Outlook Calendar events."""
        # Placeholder implementation
        logger.warning("Outlook Calendar integration not yet implemented")
        return {"events": []}

    async def _get_calendar_info(self) -> Dict[str, Any]:
        """Get calendar information."""
        try:
            if self.provider == "google":
                return await self._get_google_calendar_info()
            else:
                return {"summary": "Unknown Calendar"}

        except Exception as e:
            logger.error(f"Error getting calendar info: {e}")
            return {"summary": "Unknown Calendar"}

    async def _get_google_calendar_info(self) -> Dict[str, Any]:
        """Get Google Calendar information."""
        try:
            import aiohttp

            access_token = self.api_credentials.get("access_token")
            if not access_token:
                raise ValueError("Access token required")

            url = f"{self.api_base_url}/calendars/{self.calendar_id}"
            headers = {"Authorization": f"Bearer {access_token}"}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:

                    if response.status != 200:
                        error_data = await response.json()
                        raise Exception(f"Google Calendar API error: {error_data}")

                    return await response.json()

        except ImportError:
            raise Exception("aiohttp is required for Google Calendar API requests")
        except Exception as e:
            logger.error(f"Google Calendar info retrieval failed: {e}")
            raise
