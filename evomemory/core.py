"""Core EvoMemory implementation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Memory:
    """A single stored memory."""

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0


class EvoMemory:
    """Lightweight, local, human-like memory engine for AI agents.

    Memories are stored in-process (no external services required).
    Retrieval uses simple keyword overlap scoring so the engine stays
    dependency-free and easy to embed in any Python project.
    """

    def __init__(self) -> None:
        self._memories: dict[str, Memory] = {}

    # ------------------------------------------------------------------
    # Writing
    # ------------------------------------------------------------------

    def store(self, content: str, metadata: dict[str, Any] | None = None) -> str:
        """Store a new memory and return its unique ID."""
        memory = Memory(content=content, metadata=metadata or {})
        self._memories[memory.id] = memory
        return memory.id

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def retrieve(self, query: str | None = None, n: int = 5) -> list[Memory]:
        """Return up to *n* memories.

        When *query* is provided the results are ranked by keyword overlap
        (case-insensitive).  When omitted the most recently stored memories
        are returned first.
        """
        memories = list(self._memories.values())
        if query:
            memories.sort(key=lambda m: self._score(m, query), reverse=True)
        else:
            memories.sort(key=lambda m: m.created_at, reverse=True)
        top = memories[:n]
        # Track access
        now = datetime.now()
        for m in top:
            m.accessed_at = now
            m.access_count += 1
        return top

    def get(self, memory_id: str) -> Memory | None:
        """Return a single memory by ID, or *None* if not found."""
        memory = self._memories.get(memory_id)
        if memory is not None:
            memory.accessed_at = datetime.now()
            memory.access_count += 1
        return memory

    # ------------------------------------------------------------------
    # Forgetting
    # ------------------------------------------------------------------

    def forget(self, memory_id: str) -> bool:
        """Remove a memory by ID.  Returns *True* if it existed."""
        return self._memories.pop(memory_id, None) is not None

    def clear(self) -> None:
        """Remove all stored memories."""
        self._memories.clear()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _score(self, memory: Memory, query: str) -> int:
        """Count overlapping words between *query* and *memory.content*."""
        query_words = set(query.lower().split())
        content_words = set(memory.content.lower().split())
        return len(query_words & content_words)

    def __len__(self) -> int:
        return len(self._memories)

    def __repr__(self) -> str:
        return f"EvoMemory(memories={len(self)})"
