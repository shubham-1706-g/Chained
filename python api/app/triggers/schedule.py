"""Schedule Trigger

This module implements a schedule trigger that executes workflows
at specified time intervals using cron expressions.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Callable, Awaitable
from datetime import datetime, time
import schedule as schedule_lib

from .base import ScheduledTrigger
from ..core.context import ExecutionContext

logger = logging.getLogger(__name__)


class ScheduleTrigger(ScheduledTrigger):
    """Schedule trigger that executes workflows at specified times.

    This trigger uses cron expressions or simple interval scheduling
    to trigger workflow executions on a regular basis.
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.schedule_config = config.get("schedule", "*/30 * * * *")
        self.timezone = config.get("timezone", "UTC")
        self.enabled = config.get("enabled", True)
        self._scheduler = None

    async def validate_config(self) -> bool:
        """Validate schedule trigger configuration."""
        await super().validate_config()

        if not self.schedule_config:
            raise ValueError("schedule is required for schedule trigger")

        # Basic cron validation (simplified)
        if not self._is_valid_cron(self.schedule_config):
            raise ValueError(f"Invalid cron expression: {self.schedule_config}")

        return True

    async def setup(self) -> None:
        """Set up the schedule trigger."""
        try:
            import schedule as schedule_lib
            self._scheduler = schedule_lib
        except ImportError:
            raise RuntimeError("schedule library is required for schedule trigger")

        logger.info(f"Schedule trigger {self.trigger_id} setup complete")

    async def start(self, callback: Callable[[ExecutionContext], Awaitable[None]]) -> None:
        """Start the schedule trigger."""
        if not self.enabled:
            logger.info(f"Schedule trigger {self.trigger_id} is disabled")
            return

        self.is_running = True
        self._callback = callback

        # Parse and set up the schedule
        await self._setup_schedule()

        logger.info(f"Schedule trigger {self.trigger_id} started with schedule: {self.schedule_config}")

        # Run the scheduler loop
        while self.is_running:
            try:
                self._scheduler.run_pending()
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in schedule loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    async def stop(self) -> None:
        """Stop the schedule trigger."""
        self.is_running = False

        if self._scheduler:
            # Clear all jobs for this trigger
            self._scheduler.clear()

        logger.info(f"Schedule trigger {self.trigger_id} stopped")

    async def test_connection(self) -> bool:
        """Test schedule trigger (always returns True for schedule triggers)."""
        return True

    async def _setup_schedule(self) -> None:
        """Set up the schedule based on the cron expression."""
        try:
            # Parse the cron expression and set up the schedule
            cron_parts = self.schedule_config.split()

            if len(cron_parts) == 5:
                minute, hour, day, month, day_of_week = cron_parts

                # Handle different cron patterns
                if minute == "*" and hour == "*" and day == "*" and month == "*" and day_of_week == "*":
                    # Every minute
                    self._scheduler.every().minute.do(self._create_job_wrapper())
                elif minute.startswith("*/"):
                    # Every N minutes
                    interval = int(minute[2:])
                    self._scheduler.every(interval).minutes.do(self._create_job_wrapper())
                elif hour.startswith("*/"):
                    # Every N hours
                    interval = int(hour[2:])
                    self._scheduler.every(interval).hours.do(self._create_job_wrapper())
                elif day_of_week != "*":
                    # Specific days of week
                    days = self._parse_days_of_week(day_of_week)
                    for day in days:
                        job = self._scheduler.every().week
                        if day == "monday":
                            job.monday
                        elif day == "tuesday":
                            job.tuesday
                        elif day == "wednesday":
                            job.wednesday
                        elif day == "thursday":
                            job.thursday
                        elif day == "friday":
                            job.friday
                        elif day == "saturday":
                            job.saturday
                        elif day == "sunday":
                            job.sunday
                        job.do(self._create_job_wrapper())
                else:
                    # Default to every 30 minutes
                    logger.warning(f"Complex cron expression not fully supported: {self.schedule_config}")
                    self._scheduler.every(30).minutes.do(self._create_job_wrapper())
            else:
                raise ValueError(f"Invalid cron expression format: {self.schedule_config}")

        except Exception as e:
            logger.error(f"Failed to setup schedule: {e}")
            # Fallback to every 30 minutes
            self._scheduler.every(30).minutes.do(self._create_job_wrapper())

    def _create_job_wrapper(self) -> callable:
        """Create a wrapper function for the scheduled job."""
        async def job_wrapper():
            try:
                await self._execute_scheduled_job()
            except Exception as e:
                logger.error(f"Scheduled job execution failed: {e}")

        return job_wrapper

    async def _execute_scheduled_job(self) -> None:
        """Execute the scheduled job."""
        try:
            # Create execution context
            context = ExecutionContext(
                flow_id=f"schedule_{self.trigger_id}",
                execution_id=f"schedule_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                user_id=self.config.get("user_id", "scheduler")
            )

            # Add schedule metadata to context
            context.set_variable("schedule_trigger", True)
            context.set_variable("schedule_config", self.schedule_config)
            context.set_variable("scheduled_time", datetime.utcnow().isoformat())

            logger.info(f"Schedule trigger {self.trigger_id} executing at {datetime.utcnow()}")

            # Trigger workflow execution
            await self.trigger_workflow(self._callback)

        except Exception as e:
            logger.error(f"Error executing scheduled job: {e}")
            raise

    def _is_valid_cron(self, cron_expression: str) -> bool:
        """Basic validation for cron expressions."""
        try:
            parts = cron_expression.split()
            if len(parts) != 5:
                return False

            # Basic validation - could be enhanced
            for part in parts:
                if part not in ["*", "*/1", "*/5", "*/10", "*/15", "*/30", "0", "1", "2", "3", "4", "5", "6"]:
                    if not (part.isdigit() and 0 <= int(part) <= 59):
                        return False

            return True
        except:
            return False

    def _parse_days_of_week(self, day_of_week: str) -> list:
        """Parse day of week specification from cron."""
        day_map = {
            "0": "sunday",
            "1": "monday",
            "2": "tuesday",
            "3": "wednesday",
            "4": "thursday",
            "5": "friday",
            "6": "saturday",
            "7": "sunday"  # Some systems use 7 for Sunday
        }

        days = []
        if day_of_week == "*":
            return list(day_map.values())[:-1]  # Exclude duplicate Sunday

        for day in day_of_week.split(","):
            if day in day_map:
                days.append(day_map[day])

        return days if days else ["monday"]  # Default fallback

    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled run time."""
        if not self._scheduler:
            return None

        # This is a simplified implementation
        # In a real implementation, you'd need to check the actual scheduled jobs
        now = datetime.utcnow()

        try:
            cron_parts = self.schedule_config.split()
            if len(cron_parts) == 5:
                minute, hour, day, month, day_of_week = cron_parts

                if minute.startswith("*/"):
                    interval = int(minute[2:])
                    # Calculate next minute interval
                    current_minute = now.minute
                    next_minute = ((current_minute // interval) + 1) * interval
                    if next_minute >= 60:
                        next_minute = 0
                        next_hour = (now.hour + 1) % 24
                    else:
                        next_hour = now.hour

                    next_run = now.replace(hour=next_hour, minute=next_minute, second=0, microsecond=0)
                    if next_run <= now:
                        next_run = next_run.replace(hour=(next_hour + 1) % 24)

                    return next_run
        except:
            pass

        return None
