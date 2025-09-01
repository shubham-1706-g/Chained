"""File Watch Trigger

This module implements a file watch trigger that monitors file system
changes and triggers workflow executions when files are created, modified, or deleted.
"""

import asyncio
import logging
import os
from typing import Any, Dict, Optional, Callable, Awaitable, Set
from datetime import datetime
import time

from .base import EventTrigger
from ..core.context import ExecutionContext

logger = logging.getLogger(__name__)


class FileWatchTrigger(EventTrigger):
    """File watch trigger that monitors file system changes.

    This trigger watches specified directories for file changes
    and triggers workflow executions based on file events.
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.watch_paths = config.get("watch_paths", [])
        self.watch_events = config.get("events", ["created", "modified"])
        self.recursive = config.get("recursive", True)
        self.file_patterns = config.get("file_patterns", ["*"])
        self.ignore_patterns = config.get("ignore_patterns", [])
        self.poll_interval = config.get("poll_interval", 5)  # seconds
        self._file_states: Dict[str, float] = {}  # file_path -> modification_time
        self._watched_files: Set[str] = set()

    async def validate_config(self) -> bool:
        """Validate file watch trigger configuration."""
        if not self.watch_paths:
            raise ValueError("watch_paths is required for file watch trigger")

        if not isinstance(self.watch_paths, list):
            raise ValueError("watch_paths must be a list of directory paths")

        for path in self.watch_paths:
            if not os.path.exists(path):
                raise ValueError(f"Watch path does not exist: {path}")
            if not os.path.isdir(path):
                raise ValueError(f"Watch path must be a directory: {path}")

        if not isinstance(self.watch_events, list):
            raise ValueError("events must be a list")

        valid_events = ["created", "modified", "deleted"]
        for event in self.watch_events:
            if event not in valid_events:
                raise ValueError(f"Invalid event type: {event}. Must be one of {valid_events}")

        return True

    async def setup(self) -> None:
        """Set up the file watch trigger."""
        # Initialize file states
        await self._scan_initial_files()
        logger.info(f"File watch trigger {self.trigger_id} setup complete. Watching {len(self._watched_files)} files")

    async def start(self, callback: Callable[[ExecutionContext], Awaitable[None]]) -> None:
        """Start the file watch trigger."""
        self.is_running = True
        self._callback = callback

        logger.info(f"File watch trigger {self.trigger_id} started. Monitoring {len(self.watch_paths)} paths")

        while self.is_running:
            try:
                events = await self._check_for_changes()
                for event in events:
                    await self._handle_file_event(event)

                await asyncio.sleep(self.poll_interval)

            except Exception as e:
                logger.error(f"Error in file watch loop: {e}")
                await asyncio.sleep(self.poll_interval)

    async def stop(self) -> None:
        """Stop the file watch trigger."""
        self.is_running = False
        self._file_states.clear()
        self._watched_files.clear()
        logger.info(f"File watch trigger {self.trigger_id} stopped")

    async def test_connection(self) -> bool:
        """Test file watch trigger by checking if watch paths are accessible."""
        try:
            for path in self.watch_paths:
                if not os.path.exists(path):
                    return False
                if not os.access(path, os.R_OK):
                    return False
            return True
        except Exception as e:
            logger.error(f"File watch connection test failed: {e}")
            return False

    async def _scan_initial_files(self) -> None:
        """Scan initial files and record their states."""
        for watch_path in self.watch_paths:
            await self._scan_directory(watch_path)

    async def _scan_directory(self, directory: str) -> None:
        """Recursively scan a directory and record file states."""
        try:
            for root, dirs, files in os.walk(directory):
                # Check ignore patterns for directories
                if self._should_ignore(root):
                    continue

                for file in files:
                    file_path = os.path.join(root, file)

                    if self._should_ignore(file_path):
                        continue

                    if self._matches_patterns(file_path):
                        try:
                            stat = os.stat(file_path)
                            self._file_states[file_path] = stat.st_mtime
                            self._watched_files.add(file_path)
                        except OSError as e:
                            logger.warning(f"Could not stat file {file_path}: {e}")

                # Don't recurse if recursive is False
                if not self.recursive:
                    break

        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")

    async def _check_for_changes(self) -> list:
        """Check for file system changes and return list of events."""
        events = []
        current_files = set()

        for watch_path in self.watch_paths:
            await self._check_directory_changes(watch_path, events, current_files)

        # Check for deleted files
        deleted_files = self._watched_files - current_files
        for file_path in deleted_files:
            if "deleted" in self.watch_events:
                events.append({
                    "event": "deleted",
                    "file_path": file_path,
                    "timestamp": datetime.utcnow().isoformat()
                })
            # Remove from watched files
            if file_path in self._file_states:
                del self._file_states[file_path]

        # Update watched files
        self._watched_files = current_files

        return events

    async def _check_directory_changes(self, directory: str, events: list, current_files: set) -> None:
        """Check a directory for changes."""
        try:
            for root, dirs, files in os.walk(directory):
                if self._should_ignore(root):
                    continue

                for file in files:
                    file_path = os.path.join(root, file)

                    if self._should_ignore(file_path):
                        continue

                    if not self._matches_patterns(file_path):
                        continue

                    current_files.add(file_path)

                    try:
                        stat = os.stat(file_path)
                        current_mtime = stat.st_mtime
                        previous_mtime = self._file_states.get(file_path)

                        if previous_mtime is None:
                            # New file
                            if "created" in self.watch_events:
                                events.append({
                                    "event": "created",
                                    "file_path": file_path,
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "file_size": stat.st_size
                                })
                        elif current_mtime > previous_mtime:
                            # Modified file
                            if "modified" in self.watch_events:
                                events.append({
                                    "event": "modified",
                                    "file_path": file_path,
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "file_size": stat.st_size,
                                    "previous_mtime": previous_mtime
                                })

                        # Update file state
                        self._file_states[file_path] = current_mtime

                    except OSError as e:
                        logger.warning(f"Could not check file {file_path}: {e}")

                if not self.recursive:
                    break

        except Exception as e:
            logger.error(f"Error checking directory {directory}: {e}")

    async def _handle_file_event(self, event: Dict[str, Any]) -> None:
        """Handle a file event by triggering workflow execution."""
        try:
            # Check if event matches filters
            if not self.matches_filters(event):
                logger.debug(f"File event filtered out: {event}")
                return

            # Create execution context
            context = ExecutionContext(
                flow_id=f"file_watch_{self.trigger_id}",
                execution_id=f"file_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                user_id=self.config.get("user_id", "file_watcher")
            )

            # Add file event data to context
            context.set_variable("file_event", event)
            context.set_variable("file_path", event["file_path"])
            context.set_variable("event_type", event["event"])
            context.set_variable("event_timestamp", event["timestamp"])

            # Add file metadata if available
            if event["event"] in ["created", "modified"]:
                try:
                    stat = os.stat(event["file_path"])
                    context.set_variable("file_size", stat.st_size)
                    context.set_variable("file_modified", stat.st_mtime)
                except OSError:
                    pass

            logger.info(f"File watch trigger {self.trigger_id} detected {event['event']}: {event['file_path']}")

            # Trigger workflow execution
            await self.trigger_workflow(self._callback)

        except Exception as e:
            logger.error(f"Error handling file event: {e}")

    def _matches_patterns(self, file_path: str) -> bool:
        """Check if file path matches the configured patterns."""
        import fnmatch

        filename = os.path.basename(file_path)

        # Check include patterns
        for pattern in self.file_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True

        return False

    def _should_ignore(self, path: str) -> bool:
        """Check if path should be ignored based on ignore patterns."""
        import fnmatch

        # Check ignore patterns
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(os.path.basename(path), pattern):
                return True

        # Ignore common system files
        basename = os.path.basename(path)
        if basename.startswith('.') or basename in ['Thumbs.db', 'Desktop.ini']:
            return True

        return False
