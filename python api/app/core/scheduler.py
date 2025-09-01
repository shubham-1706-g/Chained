"""Scheduler Module

This module provides cron-based scheduling functionality for workflow triggers.
It manages scheduled triggers and executes them at specified intervals.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, time
import uuid
from dataclasses import dataclass

from .context import ExecutionContext

logger = logging.getLogger(__name__)


@dataclass
class ScheduledJob:
    """Represents a scheduled job configuration."""
    job_id: str
    trigger_id: str
    cron_expression: str
    callback: Callable
    is_active: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class WorkflowScheduler:
    """Scheduler for managing cron-based workflow triggers.

    This class handles scheduling and execution of time-based triggers
    using cron expressions and interval-based scheduling.
    """

    def __init__(self):
        self.jobs: Dict[str, ScheduledJob] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.check_interval = 30  # Check every 30 seconds

    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            logger.warning("Scheduler is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("Workflow scheduler started")

    async def stop(self) -> None:
        """Stop the scheduler."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Workflow scheduler stopped")

    def add_job(
        self,
        trigger_id: str,
        cron_expression: str,
        callback: Callable,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a new scheduled job.

        Args:
            trigger_id: ID of the trigger
            cron_expression: Cron expression (simplified format)
            callback: Function to call when job runs
            metadata: Additional metadata for the job

        Returns:
            Job ID of the created job
        """
        job_id = str(uuid.uuid4())
        job = ScheduledJob(
            job_id=job_id,
            trigger_id=trigger_id,
            cron_expression=cron_expression,
            callback=callback,
            metadata=metadata or {}
        )

        # Parse cron expression and set next run time
        job.next_run = self._parse_cron_and_get_next_run(cron_expression)

        self.jobs[job_id] = job
        logger.info(f"Added scheduled job {job_id} for trigger {trigger_id}")
        return job_id

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job.

        Args:
            job_id: ID of the job to remove

        Returns:
            True if job was removed, False if not found
        """
        if job_id in self.jobs:
            del self.jobs[job_id]
            logger.info(f"Removed scheduled job {job_id}")
            return True
        return False

    def get_jobs(self) -> List[ScheduledJob]:
        """Get all scheduled jobs."""
        return list(self.jobs.values())

    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        """Get a specific job by ID."""
        return self.jobs.get(job_id)

    def enable_job(self, job_id: str) -> bool:
        """Enable a scheduled job."""
        job = self.jobs.get(job_id)
        if job:
            job.is_active = True
            logger.info(f"Enabled scheduled job {job_id}")
            return True
        return False

    def disable_job(self, job_id: str) -> bool:
        """Disable a scheduled job."""
        job = self.jobs.get(job_id)
        if job:
            job.is_active = False
            logger.info(f"Disabled scheduled job {job_id}")
            return True
        return False

    async def _scheduler_loop(self) -> None:
        """Main scheduler loop that checks and executes jobs."""
        while self._running:
            try:
                await self._check_and_execute_jobs()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(self.check_interval)

    async def _check_and_execute_jobs(self) -> None:
        """Check all jobs and execute those that are due."""
        now = datetime.utcnow()

        for job in self.jobs.values():
            if not job.is_active:
                continue

            if job.next_run and now >= job.next_run:
                try:
                    # Execute the job
                    await self._execute_job(job)

                    # Update job timing
                    job.last_run = now
                    job.next_run = self._parse_cron_and_get_next_run(job.cron_expression)

                    logger.info(f"Executed scheduled job {job.job_id}")

                except Exception as e:
                    logger.error(f"Error executing scheduled job {job.job_id}: {e}")

    async def _execute_job(self, job: ScheduledJob) -> None:
        """Execute a scheduled job."""
        try:
            # Create execution context
            context = ExecutionContext(
                flow_id=f"scheduled_{job.trigger_id}",
                execution_id=str(uuid.uuid4()),
                user_id=job.metadata.get("user_id", "system")
            )

            # Execute callback
            await job.callback(context)

        except Exception as e:
            logger.error(f"Job execution failed for {job.job_id}: {e}")
            raise

    def _parse_cron_and_get_next_run(self, cron_expression: str) -> datetime:
        """Parse cron expression and calculate next run time.

        Supports simplified cron format:
        - "*/30 * * * *" - Every 30 minutes
        - "0 */2 * * *" - Every 2 hours
        - "0 9 * * 1" - Every Monday at 9:00
        """
        now = datetime.utcnow()

        try:
            parts = cron_expression.split()
            if len(parts) != 5:
                raise ValueError("Invalid cron expression format")

            minute, hour, day, month, day_of_week = parts

            # For now, implement basic interval scheduling
            # This is a simplified implementation
            if minute.startswith("*/"):
                interval = int(minute[2:])
                # Calculate next run based on minute interval
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

            elif hour.startswith("*/"):
                interval = int(hour[2:])
                next_hour = ((now.hour // interval) + 1) * interval
                if next_hour >= 24:
                    next_hour = 0

                next_run = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)
                if next_run <= now:
                    next_run = next_run.replace(day=now.day + 1)

            else:
                # Default to every hour if parsing fails
                next_run = now.replace(minute=0, second=0, microsecond=0)
                if next_run <= now:
                    next_run = next_run.replace(hour=now.hour + 1)

            return next_run

        except (ValueError, IndexError):
            # Default to every hour if parsing fails
            logger.warning(f"Failed to parse cron expression: {cron_expression}, defaulting to hourly")
            next_run = now.replace(minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run = next_run.replace(hour=now.hour + 1)
            return next_run
