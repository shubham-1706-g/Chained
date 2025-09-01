"""Calendar Event Action

This module implements actions for calendar event operations including
creating events, updating events, retrieving events, and managing calendar entries.
"""

import logging
from typing import Any, Dict, Optional, List
import json
from datetime import datetime, timedelta

from ..base import ApiAction
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class CalendarEventAction(ApiAction):
    """Action for calendar event operations.

    This action supports:
    - Creating new calendar events
    - Updating existing events
    - Retrieving events by date range
    - Deleting events
    - Managing event attendees and reminders
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.provider = config.get("provider", "google")  # google, outlook, ical, api
        self.calendar_id = config.get("calendar_id", "primary")
        self.operation = config.get("operation", "create")  # create, update, get, delete, list
        self.api_credentials = config.get("api_credentials", {})

        # Provider-specific configurations
        if self.provider == "google":
            self.api_base_url = "https://www.googleapis.com/calendar/v3"
        elif self.provider == "outlook":
            self.api_base_url = "https://graph.microsoft.com/v1.0/me/events"
        else:
            self.api_base_url = config.get("api_base_url", "")

    async def validate_config(self) -> bool:
        """Validate calendar event action configuration."""
        valid_providers = ["google", "outlook", "ical", "api"]
        if self.provider not in valid_providers:
            raise ValueError(f"Invalid provider: {self.provider}. Must be one of {valid_providers}")

        valid_operations = ["create", "update", "get", "delete", "list"]
        if self.operation not in valid_operations:
            raise ValueError(f"Invalid operation: {self.operation}. Must be one of {valid_operations}")

        if self.provider in ["google", "outlook"] and not self.api_credentials:
            raise ValueError(f"api_credentials required for {self.provider} provider")

        return True

    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the calendar event operation."""
        try:
            if self.operation == "create":
                result = await self._create_event(input_data)
            elif self.operation == "update":
                result = await self._update_event(input_data)
            elif self.operation == "get":
                result = await self._get_event(input_data)
            elif self.operation == "delete":
                result = await self._delete_event(input_data)
            elif self.operation == "list":
                result = await self._list_events(input_data)
            else:
                raise ValueError(f"Unsupported operation: {self.operation}")

            return {
                "success": True,
                "operation": self.operation,
                "provider": self.provider,
                "calendar_id": self.calendar_id,
                "result": result
            }

        except Exception as e:
            logger.error(f"Calendar event operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": self.operation,
                "provider": self.provider,
                "calendar_id": self.calendar_id
            }

    async def _create_event(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new calendar event."""
        try:
            # Prepare event data
            event_data = self._prepare_event_data(input_data)

            if self.provider == "google":
                return await self._create_google_event(event_data)
            elif self.provider == "outlook":
                return await self._create_outlook_event(event_data)
            else:
                raise ValueError(f"Event creation not supported for provider: {self.provider}")

        except Exception as e:
            logger.error(f"Event creation failed: {e}")
            raise

    async def _update_event(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing calendar event."""
        try:
            event_id = input_data.get("event_id")
            if not event_id:
                raise ValueError("event_id is required for update operation")

            # Prepare update data
            update_data = self._prepare_event_data(input_data)

            if self.provider == "google":
                return await self._update_google_event(event_id, update_data)
            elif self.provider == "outlook":
                return await self._update_outlook_event(event_id, update_data)
            else:
                raise ValueError(f"Event update not supported for provider: {self.provider}")

        except Exception as e:
            logger.error(f"Event update failed: {e}")
            raise

    async def _get_event(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific calendar event."""
        try:
            event_id = input_data.get("event_id")
            if not event_id:
                raise ValueError("event_id is required for get operation")

            if self.provider == "google":
                return await self._get_google_event(event_id)
            elif self.provider == "outlook":
                return await self._get_outlook_event(event_id)
            else:
                raise ValueError(f"Event retrieval not supported for provider: {self.provider}")

        except Exception as e:
            logger.error(f"Event retrieval failed: {e}")
            raise

    async def _delete_event(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a calendar event."""
        try:
            event_id = input_data.get("event_id")
            if not event_id:
                raise ValueError("event_id is required for delete operation")

            if self.provider == "google":
                return await self._delete_google_event(event_id)
            elif self.provider == "outlook":
                return await self._delete_outlook_event(event_id)
            else:
                raise ValueError(f"Event deletion not supported for provider: {self.provider}")

        except Exception as e:
            logger.error(f"Event deletion failed: {e}")
            raise

    async def _list_events(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """List calendar events within a date range."""
        try:
            # Set default date range if not provided
            start_date = input_data.get("start_date", datetime.utcnow().isoformat())
            end_date = input_data.get("end_date")

            if not end_date:
                # Default to 30 days from start
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_dt = start_dt + timedelta(days=30)
                end_date = end_dt.isoformat()

            if self.provider == "google":
                return await self._list_google_events(start_date, end_date, input_data)
            elif self.provider == "outlook":
                return await self._list_outlook_events(start_date, end_date, input_data)
            else:
                raise ValueError(f"Event listing not supported for provider: {self.provider}")

        except Exception as e:
            logger.error(f"Event listing failed: {e}")
            raise

    def _prepare_event_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare event data for API submission."""
        event_data = {
            "summary": input_data.get("title", input_data.get("summary", "New Event")),
            "description": input_data.get("description", ""),
            "start": self._prepare_datetime(input_data.get("start_time", input_data.get("start"))),
            "end": self._prepare_datetime(input_data.get("end_time", input_data.get("end"))),
        }

        # Add optional fields
        if "location" in input_data:
            event_data["location"] = input_data["location"]

        if "attendees" in input_data:
            event_data["attendees"] = input_data["attendees"]

        if "reminders" in input_data:
            event_data["reminders"] = input_data["reminders"]

        if "recurrence" in input_data:
            event_data["recurrence"] = input_data["recurrence"]

        return event_data

    def _prepare_datetime(self, datetime_str: str) -> Dict[str, str]:
        """Prepare datetime for calendar API format."""
        if isinstance(datetime_str, dict):
            return datetime_str

        try:
            # Try to parse as ISO format
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return {
                "dateTime": dt.isoformat(),
                "timeZone": "UTC"
            }
        except:
            # If parsing fails, assume it's already in correct format
            return {"dateTime": datetime_str, "timeZone": "UTC"}

    # Google Calendar implementations
    async def _create_google_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create event in Google Calendar."""
        try:
            import aiohttp

            url = f"{self.api_base_url}/calendars/{self.calendar_id}/events"
            access_token = self.api_credentials.get("access_token")

            if not access_token:
                raise ValueError("Access token required for Google Calendar")

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    json=event_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status not in [200, 201]:
                        error_data = await response.json()
                        raise Exception(f"Google Calendar API error: {error_data}")

                    result = await response.json()

                    return {
                        "event_id": result.get("id"),
                        "html_link": result.get("htmlLink"),
                        "status": result.get("status"),
                        "created": result.get("created"),
                        "updated": result.get("updated")
                    }

        except ImportError:
            raise Exception("aiohttp is required for Google Calendar API requests")
        except Exception as e:
            logger.error(f"Google Calendar event creation failed: {e}")
            raise

    async def _list_google_events(self, start_date: str, end_date: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """List Google Calendar events."""
        try:
            import aiohttp

            url = f"{self.api_base_url}/calendars/{self.calendar_id}/events"
            access_token = self.api_credentials.get("access_token")

            params = {
                "timeMin": start_date,
                "timeMax": end_date,
                "singleEvents": "true",
                "orderBy": "startTime"
            }

            if "query" in input_data:
                params["q"] = input_data["query"]

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
                        raise Exception(f"Google Calendar API error: {error_data}")

                    result = await response.json()

                    events = []
                    for event in result.get("items", []):
                        events.append({
                            "id": event.get("id"),
                            "summary": event.get("summary"),
                            "start": event.get("start"),
                            "end": event.get("end"),
                            "status": event.get("status"),
                            "html_link": event.get("htmlLink")
                        })

                    return {
                        "events": events,
                        "count": len(events),
                        "next_page_token": result.get("nextPageToken")
                    }

        except ImportError:
            raise Exception("aiohttp is required for Google Calendar API requests")
        except Exception as e:
            logger.error(f"Google Calendar event listing failed: {e}")
            raise

    async def _get_google_event(self, event_id: str) -> Dict[str, Any]:
        """Get a specific Google Calendar event."""
        # Implementation would be similar to list but for single event
        raise NotImplementedError("Google Calendar event retrieval not yet implemented")

    async def _update_google_event(self, event_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a Google Calendar event."""
        # Implementation would use PUT request
        raise NotImplementedError("Google Calendar event update not yet implemented")

    async def _delete_google_event(self, event_id: str) -> Dict[str, Any]:
        """Delete a Google Calendar event."""
        # Implementation would use DELETE request
        raise NotImplementedError("Google Calendar event deletion not yet implemented")

    # Outlook Calendar implementations (placeholders)
    async def _create_outlook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create event in Outlook Calendar."""
        raise NotImplementedError("Outlook Calendar integration not yet implemented")

    async def _list_outlook_events(self, start_date: str, end_date: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """List Outlook Calendar events."""
        raise NotImplementedError("Outlook Calendar integration not yet implemented")

    async def _get_outlook_event(self, event_id: str) -> Dict[str, Any]:
        """Get a specific Outlook Calendar event."""
        raise NotImplementedError("Outlook Calendar integration not yet implemented")

    async def _update_outlook_event(self, event_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an Outlook Calendar event."""
        raise NotImplementedError("Outlook Calendar integration not yet implemented")

    async def _delete_outlook_event(self, event_id: str) -> Dict[str, Any]:
        """Delete an Outlook Calendar event."""
        raise NotImplementedError("Outlook Calendar integration not yet implemented")

    async def test_connection(self) -> bool:
        """Test calendar provider connection."""
        try:
            if self.provider == "google":
                return await self._test_google_connection()
            elif self.provider == "outlook":
                return await self._test_outlook_connection()
            else:
                return True  # For other providers, assume connection is OK

        except Exception as e:
            logger.error(f"Calendar connection test failed: {e}")
            return False

    async def _test_google_connection(self) -> bool:
        """Test Google Calendar connection."""
        try:
            import aiohttp

            access_token = self.api_credentials.get("access_token")
            if not access_token:
                return False

            url = f"{self.api_base_url}/calendars/{self.calendar_id}"
            headers = {"Authorization": f"Bearer {access_token}"}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200

        except Exception:
            return False

    async def _test_outlook_connection(self) -> bool:
        """Test Outlook Calendar connection."""
        # Placeholder implementation
        return False

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action input."""
        if self.operation == "create":
            return {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Event title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Event description"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Event start time (ISO format)"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "Event end time (ISO format)"
                    },
                    "location": {
                        "type": "string",
                        "description": "Event location"
                    },
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Event attendees"
                    }
                },
                "required": ["title", "start_time", "end_time"]
            }
        elif self.operation == "list":
            return {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date for event listing"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date for event listing"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for events"
                    }
                }
            }

        return {"type": "object", "properties": {}}

    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action output."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "operation": {"type": "string"},
                "provider": {"type": "string"},
                "calendar_id": {"type": "string"},
                "result": {
                    "description": "Operation result (structure depends on operation)"
                },
                "error": {"type": "string"}
            },
            "required": ["success", "operation", "provider"]
        }
