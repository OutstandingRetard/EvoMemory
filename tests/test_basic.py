"""Basic tests for EvoMemory."""

import pytest

from evomemory import EvoMemory, Memory


def test_store_returns_id():
    mem = EvoMemory()
    memory_id = mem.store("hello world")
    assert isinstance(memory_id, str)
    assert len(memory_id) > 0


def test_len_increases_on_store():
    mem = EvoMemory()
    assert len(mem) == 0
    mem.store("first")
    assert len(mem) == 1
    mem.store("second")
    assert len(mem) == 2


def test_retrieve_returns_memory_objects():
    mem = EvoMemory()
    mem.store("cats are fluffy animals")
    results = mem.retrieve("cats")
    assert len(results) == 1
    assert isinstance(results[0], Memory)


def test_retrieve_with_query_ranks_by_relevance():
    mem = EvoMemory()
    mem.store("I love Python programming")
    mem.store("coffee is great in the morning")
    results = mem.retrieve("Python programming", n=2)
    assert results[0].content == "I love Python programming"


def test_retrieve_without_query_returns_recent_first():
    mem = EvoMemory()
    mem.store("first memory")
    mem.store("second memory")
    mem.store("third memory")
    results = mem.retrieve(n=3)
    assert results[0].content == "third memory"


def test_retrieve_respects_n_limit():
    mem = EvoMemory()
    for i in range(10):
        mem.store(f"memory {i}")
    results = mem.retrieve(n=3)
    assert len(results) == 3


def test_get_existing_memory():
    mem = EvoMemory()
    memory_id = mem.store("some content")
    memory = mem.get(memory_id)
    assert memory is not None
    assert memory.content == "some content"


def test_get_missing_memory_returns_none():
    mem = EvoMemory()
    assert mem.get("nonexistent-id") is None


def test_forget_removes_memory():
    mem = EvoMemory()
    memory_id = mem.store("to be forgotten")
    assert mem.forget(memory_id) is True
    assert len(mem) == 0
    assert mem.get(memory_id) is None


def test_forget_missing_memory_returns_false():
    mem = EvoMemory()
    assert mem.forget("nonexistent-id") is False


def test_clear_removes_all():
    mem = EvoMemory()
    mem.store("one")
    mem.store("two")
    mem.clear()
    assert len(mem) == 0


def test_store_with_metadata():
    mem = EvoMemory()
    memory_id = mem.store("event happened", metadata={"source": "user", "priority": 1})
    memory = mem.get(memory_id)
    assert memory.metadata["source"] == "user"
    assert memory.metadata["priority"] == 1


def test_access_count_increments_on_retrieve():
    mem = EvoMemory()
    memory_id = mem.store("track me")
    mem.retrieve("track")
    memory = mem.get(memory_id)
    assert memory.access_count >= 1


def test_repr():
    mem = EvoMemory()
    mem.store("x")
    assert "EvoMemory" in repr(mem)
    assert "1" in repr(mem)
