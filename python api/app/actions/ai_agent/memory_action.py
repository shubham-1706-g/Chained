"""AI Agent Memory Action

This module implements an action for AI agent memory management including
storing, retrieving, and managing conversation memory and context.
"""

import logging
import json
import hashlib
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta

from ..base import BaseAction
from ...core.context import ExecutionContext

logger = logging.getLogger(__name__)


class MemoryAction(BaseAction):
    """Action for AI agent memory management.

    This action supports:
    - Storing conversation memory
    - Retrieving relevant memories
    - Memory consolidation and summarization
    - Memory search and filtering
    - Memory cleanup and pruning
    """

    def __init__(self, config: Dict[str, Any], connection_id: Optional[str] = None):
        super().__init__(config, connection_id)
        self.operation = config.get("operation", "store")  # store, retrieve, search, cleanup
        self.memory_store = config.get("memory_store", {})  # In-memory store (use database in production)
        self.max_memories = config.get("max_memories", 1000)
        self.memory_ttl_days = config.get("memory_ttl_days", 30)
        self.vector_search = config.get("vector_search", False)  # Enable vector similarity search
        self.embedding_model = config.get("embedding_model", "text-embedding-ada-002")

    async def validate_config(self) -> bool:
        """Validate memory action configuration."""
        valid_operations = ["store", "retrieve", "search", "cleanup", "summarize"]
        if self.operation not in valid_operations:
            raise ValueError(f"Invalid operation: {self.operation}. Must be one of {valid_operations}")

        if self.max_memories <= 0:
            raise ValueError("max_memories must be positive")

        if self.memory_ttl_days <= 0:
            raise ValueError("memory_ttl_days must be positive")

        return True

    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> Dict[str, Any]:
        """Execute the memory operation."""
        try:
            if self.operation == "store":
                result = await self._store_memory(input_data)
            elif self.operation == "retrieve":
                result = await self._retrieve_memory(input_data)
            elif self.operation == "search":
                result = await self._search_memory(input_data)
            elif self.operation == "cleanup":
                result = await self._cleanup_memory(input_data)
            elif self.operation == "summarize":
                result = await self._summarize_memory(input_data)
            else:
                raise ValueError(f"Unsupported operation: {self.operation}")

            return {
                "success": True,
                "operation": self.operation,
                "result": result
            }

        except Exception as e:
            logger.error(f"Memory operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": self.operation
            }

    async def _store_memory(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store a memory item."""
        try:
            content = input_data.get("content", "")
            memory_type = input_data.get("memory_type", "conversation")  # conversation, fact, task, preference
            tags = input_data.get("tags", [])
            metadata = input_data.get("metadata", {})
            user_id = input_data.get("user_id", "default")
            session_id = input_data.get("session_id", "")

            if not content:
                raise ValueError("content is required for memory storage")

            # Create memory item
            memory_item = {
                "id": self._generate_memory_id(content, user_id),
                "content": content,
                "memory_type": memory_type,
                "tags": tags,
                "metadata": metadata,
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "importance": input_data.get("importance", 1),  # 1-10 scale
                "access_count": 0,
                "last_accessed": datetime.utcnow().isoformat()
            }

            # Generate embedding for vector search if enabled
            if self.vector_search:
                memory_item["embedding"] = await self._generate_embedding(content)

            # Store memory
            await self._store_memory_item(memory_item)

            # Cleanup old memories if needed
            await self._cleanup_old_memories(user_id)

            return {
                "memory_id": memory_item["id"],
                "stored": True,
                "memory_count": len(self._get_user_memories(user_id))
            }

        except Exception as e:
            logger.error(f"Memory storage failed: {e}")
            raise

    async def _retrieve_memory(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve relevant memories."""
        try:
            user_id = input_data.get("user_id", "default")
            query = input_data.get("query", "")
            limit = input_data.get("limit", 10)
            memory_type = input_data.get("memory_type")
            tags = input_data.get("tags", [])

            user_memories = self._get_user_memories(user_id)

            # Filter by memory type
            if memory_type:
                user_memories = [m for m in user_memories if m.get("memory_type") == memory_type]

            # Filter by tags
            if tags:
                user_memories = [m for m in user_memories if any(tag in m.get("tags", []) for tag in tags)]

            # Sort by relevance and recency
            if query and self.vector_search:
                # Use vector similarity for ranking
                user_memories = await self._rank_by_similarity(user_memories, query)
            else:
                # Sort by timestamp and importance
                user_memories.sort(key=lambda x: (x.get("importance", 1), x.get("timestamp", "")), reverse=True)

            # Limit results
            relevant_memories = user_memories[:limit]

            # Update access counts
            for memory in relevant_memories:
                memory["access_count"] += 1
                memory["last_accessed"] = datetime.utcnow().isoformat()

            return {
                "memories": relevant_memories,
                "count": len(relevant_memories),
                "total_available": len(user_memories)
            }

        except Exception as e:
            logger.error(f"Memory retrieval failed: {e}")
            raise

    async def _search_memory(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Search memories with advanced filtering."""
        try:
            user_id = input_data.get("user_id", "default")
            search_query = input_data.get("search_query", "")
            filters = input_data.get("filters", {})
            sort_by = input_data.get("sort_by", "timestamp")  # timestamp, importance, access_count
            sort_order = input_data.get("sort_order", "desc")  # asc, desc
            limit = input_data.get("limit", 50)

            user_memories = self._get_user_memories(user_id)

            # Apply filters
            filtered_memories = self._apply_memory_filters(user_memories, filters)

            # Apply search query
            if search_query:
                filtered_memories = await self._search_memories(filtered_memories, search_query)

            # Sort results
            filtered_memories = self._sort_memories(filtered_memories, sort_by, sort_order)

            # Limit results
            search_results = filtered_memories[:limit]

            return {
                "results": search_results,
                "count": len(search_results),
                "total_filtered": len(filtered_memories),
                "search_query": search_query,
                "filters_applied": filters
            }

        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            raise

    async def _cleanup_memory(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up old or irrelevant memories."""
        try:
            user_id = input_data.get("user_id", "default")
            cleanup_type = input_data.get("cleanup_type", "expired")  # expired, low_importance, duplicates
            max_age_days = input_data.get("max_age_days", self.memory_ttl_days)
            min_importance = input_data.get("min_importance", 1)

            user_memories = self._get_user_memories(user_id)
            original_count = len(user_memories)

            if cleanup_type == "expired":
                user_memories = self._cleanup_expired_memories(user_memories, max_age_days)
            elif cleanup_type == "low_importance":
                user_memories = self._cleanup_low_importance_memories(user_memories, min_importance)
            elif cleanup_type == "duplicates":
                user_memories = await self._cleanup_duplicate_memories(user_memories)

            # Update memory store
            if user_id not in self.memory_store:
                self.memory_store[user_id] = {}

            for memory in user_memories:
                self.memory_store[user_id][memory["id"]] = memory

            return {
                "cleanup_type": cleanup_type,
                "original_count": original_count,
                "remaining_count": len(user_memories),
                "removed_count": original_count - len(user_memories)
            }

        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
            raise

    async def _summarize_memory(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize memories for context."""
        try:
            user_id = input_data.get("user_id", "default")
            summary_type = input_data.get("summary_type", "recent")  # recent, topics, patterns
            time_window_days = input_data.get("time_window_days", 7)

            user_memories = self._get_user_memories(user_id)

            # Filter by time window
            cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
            recent_memories = [
                m for m in user_memories
                if datetime.fromisoformat(m.get("timestamp", "")) > cutoff_date
            ]

            if summary_type == "recent":
                summary = await self._summarize_recent_activity(recent_memories)
            elif summary_type == "topics":
                summary = await self._summarize_topics(recent_memories)
            elif summary_type == "patterns":
                summary = await self._summarize_patterns(recent_memories)
            else:
                summary = "No summary available"

            return {
                "summary": summary,
                "summary_type": summary_type,
                "time_window_days": time_window_days,
                "memories_analyzed": len(recent_memories)
            }

        except Exception as e:
            logger.error(f"Memory summarization failed: {e}")
            raise

    def _generate_memory_id(self, content: str, user_id: str) -> str:
        """Generate a unique memory ID."""
        content_hash = hashlib.md5(f"{user_id}:{content}".encode()).hexdigest()[:8]
        timestamp = str(int(datetime.utcnow().timestamp()))
        return f"mem_{timestamp}_{content_hash}"

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate text embedding for vector search."""
        # Placeholder - implement actual embedding generation
        # In production, use OpenAI, Cohere, or other embedding services
        return [0.0] * 384  # Return dummy embedding

    async def _store_memory_item(self, memory_item: Dict[str, Any]) -> None:
        """Store a memory item in the memory store."""
        user_id = memory_item["user_id"]

        if user_id not in self.memory_store:
            self.memory_store[user_id] = {}

        self.memory_store[user_id][memory_item["id"]] = memory_item

    def _get_user_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all memories for a user."""
        if user_id not in self.memory_store:
            return []

        return list(self.memory_store[user_id].values())

    async def _rank_by_similarity(self, memories: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Rank memories by similarity to query."""
        # Placeholder - implement actual vector similarity search
        # In production, use cosine similarity with embeddings
        return sorted(memories, key=lambda x: x.get("importance", 1), reverse=True)

    def _apply_memory_filters(self, memories: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to memories."""
        filtered = memories

        if "memory_type" in filters:
            filtered = [m for m in filtered if m.get("memory_type") == filters["memory_type"]]

        if "tags" in filters:
            filter_tags = filters["tags"]
            filtered = [m for m in filtered if any(tag in m.get("tags", []) for tag in filter_tags)]

        if "importance_min" in filters:
            min_importance = filters["importance_min"]
            filtered = [m for m in filtered if m.get("importance", 1) >= min_importance]

        if "date_from" in filters:
            from_date = datetime.fromisoformat(filters["date_from"])
            filtered = [m for m in filtered if datetime.fromisoformat(m.get("timestamp", "")) >= from_date]

        return filtered

    async def _search_memories(self, memories: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Search memories by text content."""
        query_lower = query.lower()
        matching_memories = []

        for memory in memories:
            content = memory.get("content", "").lower()
            tags = [tag.lower() for tag in memory.get("tags", [])]

            # Check content and tags for query terms
            if query_lower in content or any(query_lower in tag for tag in tags):
                matching_memories.append(memory)

        return matching_memories

    def _sort_memories(self, memories: List[Dict[str, Any]], sort_by: str, sort_order: str) -> List[Dict[str, Any]]:
        """Sort memories by specified field."""
        reverse = sort_order == "desc"

        if sort_by == "timestamp":
            memories.sort(key=lambda x: x.get("timestamp", ""), reverse=reverse)
        elif sort_by == "importance":
            memories.sort(key=lambda x: x.get("importance", 1), reverse=reverse)
        elif sort_by == "access_count":
            memories.sort(key=lambda x: x.get("access_count", 0), reverse=reverse)

        return memories

    async def _cleanup_old_memories(self, user_id: str) -> None:
        """Clean up old memories to maintain memory limits."""
        user_memories = self._get_user_memories(user_id)

        if len(user_memories) > self.max_memories:
            # Sort by importance and timestamp, keep the most important/recent
            user_memories.sort(key=lambda x: (x.get("importance", 1), x.get("timestamp", "")), reverse=True)
            keep_memories = user_memories[:self.max_memories]

            # Update memory store
            self.memory_store[user_id] = {m["id"]: m for m in keep_memories}

    def _cleanup_expired_memories(self, memories: List[Dict[str, Any]], max_age_days: int) -> List[Dict[str, Any]]:
        """Remove expired memories."""
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)

        return [
            m for m in memories
            if datetime.fromisoformat(m.get("timestamp", "")) > cutoff_date
        ]

    def _cleanup_low_importance_memories(self, memories: List[Dict[str, Any]], min_importance: int) -> List[Dict[str, Any]]:
        """Remove low importance memories."""
        return [m for m in memories if m.get("importance", 1) >= min_importance]

    async def _cleanup_duplicate_memories(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate memories."""
        seen_content = set()
        unique_memories = []

        for memory in memories:
            content_hash = hashlib.md5(memory.get("content", "").encode()).hexdigest()

            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_memories.append(memory)

        return unique_memories

    async def _summarize_recent_activity(self, memories: List[Dict[str, Any]]) -> str:
        """Summarize recent activity from memories."""
        if not memories:
            return "No recent activity to summarize."

        # Group by memory type
        type_counts = {}
        recent_items = []

        for memory in memories[:20]:  # Limit to recent 20 items
            mem_type = memory.get("memory_type", "general")
            type_counts[mem_type] = type_counts.get(mem_type, 0) + 1

            if len(recent_items) < 5:
                recent_items.append(memory.get("content", "")[:100] + "...")

        summary = f"Recent activity includes {len(memories)} memories. "
        summary += f"Types: {', '.join([f'{k}: {v}' for k, v in type_counts.items()])}. "
        if recent_items:
            summary += f"Recent items: {'; '.join(recent_items)}"

        return summary

    async def _summarize_topics(self, memories: List[Dict[str, Any]]) -> str:
        """Summarize topics from memories."""
        # Simple topic extraction based on tags
        all_tags = []
        for memory in memories:
            all_tags.extend(memory.get("tags", []))

        if not all_tags:
            return "No topics identified from memories."

        # Count tag frequencies
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return f"Main topics: {', '.join([f'{tag} ({count})' for tag, count in top_tags])}"

    async def _summarize_patterns(self, memories: List[Dict[str, Any]]) -> str:
        """Summarize patterns from memories."""
        if not memories:
            return "No patterns identified."

        # Analyze memory types and frequencies
        type_distribution = {}
        time_distribution = {}

        for memory in memories:
            mem_type = memory.get("memory_type", "general")
            type_distribution[mem_type] = type_distribution.get(mem_type, 0) + 1

            # Group by hour of day
            timestamp = memory.get("timestamp", "")
            if timestamp:
                try:
                    hour = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).hour
                    time_distribution[hour] = time_distribution.get(hour, 0) + 1
                except:
                    pass

        patterns = []

        # Memory type patterns
        if type_distribution:
            main_type = max(type_distribution.items(), key=lambda x: x[1])
            patterns.append(f"Primarily {main_type[0]} memories ({main_type[1]} total)")

        # Time patterns
        if time_distribution:
            peak_hour = max(time_distribution.items(), key=lambda x: x[1])
            patterns.append(f"Most active around hour {peak_hour[0]}")

        return "Patterns: " + "; ".join(patterns) if patterns else "No clear patterns identified."

    async def test_connection(self) -> bool:
        """Test memory action (no external connections needed)."""
        return True

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action input."""
        if self.operation == "store":
            return {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The memory content to store"
                    },
                    "memory_type": {
                        "type": "string",
                        "enum": ["conversation", "fact", "task", "preference"],
                        "default": "conversation",
                        "description": "Type of memory"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for the memory"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "User ID for the memory"
                    },
                    "importance": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 1,
                        "description": "Importance level (1-10)"
                    }
                },
                "required": ["content"]
            }
        elif self.operation == "retrieve":
            return {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID to retrieve memories for"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for memory retrieval"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "Maximum number of memories to retrieve"
                    }
                },
                "required": ["user_id"]
            }

        return {"type": "object", "properties": {}}

    def get_output_schema(self) -> Dict[str, Any]:
        """Get JSON schema for action output."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "operation": {"type": "string"},
                "result": {
                    "description": "Operation result (structure depends on operation)"
                },
                "error": {"type": "string"}
            },
            "required": ["success", "operation"]
        }
