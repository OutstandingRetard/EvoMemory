"""Core EvoMemory implementation."""

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class Memory:
    """A single memory entry."""

    content: Any
    importance: float = 1.0
    tags: list = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)


class EvoMemory:
    """Lightweight, local, human-like memory engine for AI agents.

    Memories are first stored in short-term memory.  When short-term memory
    exceeds *max_short_term*, important memories (importance >
    *consolidation_threshold*) are promoted to long-term storage; the rest are
    discarded.
    """

    def __init__(
        self,
        max_short_term: int = 10,
        decay_rate: float = 0.1,
        consolidation_threshold: float = 0.5,
    ) -> None:
        """Initialise EvoMemory.

        Args:
            max_short_term: Maximum number of memories kept in short-term
                storage before consolidation is triggered.
            decay_rate: Fractional importance lost per hour during
                :meth:`decay`.  Must be >= 0.
            consolidation_threshold: Minimum importance score for a memory to
                be promoted to long-term storage during consolidation.  Must
                be between 0.0 and 1.0.
        """
        if max_short_term < 1:
            raise ValueError("max_short_term must be at least 1")
        if decay_rate < 0:
            raise ValueError("decay_rate must be non-negative")
        if not 0.0 <= consolidation_threshold <= 1.0:
            raise ValueError("consolidation_threshold must be between 0.0 and 1.0")

        self.max_short_term = max_short_term
        self.decay_rate = decay_rate
        self.consolidation_threshold = consolidation_threshold
        self._short_term: list[Memory] = []
        self._long_term: list[Memory] = []
        self._last_decay_time: float = time.time()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def remember(
        self,
        content: Any,
        importance: float = 1.0,
        tags: Optional[list] = None,
    ) -> Memory:
        """Store a new memory.

        Args:
            content: Anything worth remembering.
            importance: Score between 0.0 and 1.0.  Higher values survive
                consolidation and decay longer.
            tags: Optional labels for later retrieval.

        Returns:
            The :class:`Memory` object that was created.
        """
        memory = Memory(
            content=content,
            importance=max(0.0, min(1.0, importance)),
            tags=list(tags) if tags else [],
        )
        self._short_term.append(memory)
        self._consolidate()
        return memory

    def recall(
        self,
        query: Optional[str] = None,
        tags: Optional[list] = None,
        limit: Optional[int] = None,
    ) -> list[Memory]:
        """Retrieve memories, optionally filtered by content or tags.

        Args:
            query: Case-insensitive substring to match against
                ``str(memory.content)``.
            tags: Return only memories that share at least one tag.
            limit: Cap the number of results returned (most-recent first).

        Returns:
            List of matching :class:`Memory` objects.
        """
        results: list[Memory] = []
        for mem in self._short_term + self._long_term:
            if query is not None and query.lower() not in str(mem.content).lower():
                continue
            if tags is not None and not any(t in mem.tags for t in tags):
                continue
            mem.access_count += 1
            mem.last_accessed = time.time()
            results.append(mem)

        if limit is not None:
            results = results[-limit:]
        return results

    def forget(self, memory: Memory) -> bool:
        """Explicitly remove a memory.

        Args:
            memory: The :class:`Memory` instance to remove.

        Returns:
            ``True`` if the memory was found and removed, ``False`` otherwise.
        """
        for store in (self._short_term, self._long_term):
            if memory in store:
                store.remove(memory)
                return True
        return False

    def consolidate(self) -> None:
        """Manually trigger short-term → long-term consolidation."""
        self._consolidate(force=True)

    def decay(self) -> None:
        """Apply time-based importance decay and remove exhausted memories.

        Decay is applied only for the time elapsed since the last call to this
        method (or since construction), so repeated calls do not accelerate
        the decay rate.
        """
        now = time.time()
        elapsed_hours = (now - self._last_decay_time) / 3600
        self._last_decay_time = now
        for store in (self._short_term, self._long_term):
            to_remove: list[Memory] = []
            for mem in store:
                mem.importance = max(
                    0.0, mem.importance - self.decay_rate * elapsed_hours
                )
                if mem.importance == 0.0:
                    to_remove.append(mem)
            for mem in to_remove:
                store.remove(mem)

    def save(self, path: str) -> None:
        """Persist memories to a JSON file.

        Args:
            path: Destination file path.
        """
        data = {
            "short_term": [asdict(m) for m in self._short_term],
            "long_term": [asdict(m) for m in self._long_term],
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

    def load(self, path: str) -> None:
        """Load memories from a JSON file, replacing any existing memories.

        Args:
            path: Source file path previously created by :meth:`save`.
        """
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        self._short_term = [Memory(**m) for m in data.get("short_term", [])]
        self._long_term = [Memory(**m) for m in data.get("long_term", [])]

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def short_term(self) -> list[Memory]:
        """Read-only view of short-term memories."""
        return list(self._short_term)

    @property
    def long_term(self) -> list[Memory]:
        """Read-only view of long-term memories."""
        return list(self._long_term)

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._short_term) + len(self._long_term)

    def __repr__(self) -> str:
        return (
            f"EvoMemory(short_term={len(self._short_term)}, "
            f"long_term={len(self._long_term)})"
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _consolidate(self, force: bool = False) -> None:
        """Move overflow short-term memories to long-term or discard them."""
        if len(self._short_term) <= self.max_short_term and not force:
            return

        self._short_term.sort(key=lambda m: m.importance, reverse=True)
        overflow = self._short_term[self.max_short_term:]
        for mem in overflow:
            if mem.importance > self.consolidation_threshold:
                self._long_term.append(mem)
        self._short_term = self._short_term[: self.max_short_term]
