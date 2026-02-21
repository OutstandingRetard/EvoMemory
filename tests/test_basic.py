"""Basic tests for EvoMemory."""

import json
import os
import tempfile

import pytest

from evomemory import EvoMemory, Memory

TWO_HOURS_IN_SECONDS = 7200


# ---------------------------------------------------------------------------
# Memory dataclass
# ---------------------------------------------------------------------------


def test_memory_defaults():
    m = Memory(content="hello")
    assert m.content == "hello"
    assert 0.0 <= m.importance <= 1.0
    assert m.tags == []
    assert m.access_count == 0


# ---------------------------------------------------------------------------
# EvoMemory – construction
# ---------------------------------------------------------------------------


def test_evomemory_default_construction():
    em = EvoMemory()
    assert em.max_short_term == 10
    assert len(em) == 0


def test_evomemory_invalid_max_short_term():
    with pytest.raises(ValueError):
        EvoMemory(max_short_term=0)


def test_evomemory_invalid_decay_rate():
    with pytest.raises(ValueError):
        EvoMemory(decay_rate=-0.1)


def test_evomemory_invalid_consolidation_threshold():
    with pytest.raises(ValueError):
        EvoMemory(consolidation_threshold=1.5)


# ---------------------------------------------------------------------------
# remember
# ---------------------------------------------------------------------------


def test_remember_adds_to_short_term():
    em = EvoMemory()
    em.remember("test memory")
    assert len(em.short_term) == 1
    assert em.short_term[0].content == "test memory"


def test_remember_returns_memory_object():
    em = EvoMemory()
    m = em.remember("hello", importance=0.8, tags=["greeting"])
    assert isinstance(m, Memory)
    assert m.content == "hello"
    assert m.importance == 0.8
    assert m.tags == ["greeting"]


def test_remember_clamps_importance():
    em = EvoMemory()
    m = em.remember("too important", importance=2.0)
    assert m.importance == 1.0
    m2 = em.remember("negative", importance=-1.0)
    assert m2.importance == 0.0


# ---------------------------------------------------------------------------
# recall
# ---------------------------------------------------------------------------


def test_recall_returns_all_when_no_filter():
    em = EvoMemory()
    em.remember("alpha")
    em.remember("beta")
    results = em.recall()
    assert len(results) == 2


def test_recall_query_case_insensitive():
    em = EvoMemory()
    em.remember("The Sky is Blue")
    results = em.recall(query="sky")
    assert len(results) == 1


def test_recall_by_tag():
    em = EvoMemory()
    em.remember("fact one", tags=["science"])
    em.remember("fact two", tags=["history"])
    results = em.recall(tags=["science"])
    assert len(results) == 1
    assert results[0].content == "fact one"


def test_recall_limit():
    em = EvoMemory()
    for i in range(5):
        em.remember(f"memory {i}")
    results = em.recall(limit=3)
    assert len(results) == 3


def test_recall_increments_access_count():
    em = EvoMemory()
    m = em.remember("trackable")
    em.recall(query="trackable")
    assert m.access_count == 1


# ---------------------------------------------------------------------------
# forget
# ---------------------------------------------------------------------------


def test_forget_removes_memory():
    em = EvoMemory()
    m = em.remember("to forget")
    assert em.forget(m) is True
    assert len(em) == 0


def test_forget_returns_false_for_unknown():
    em = EvoMemory()
    orphan = Memory(content="orphan")
    assert em.forget(orphan) is False


# ---------------------------------------------------------------------------
# consolidation
# ---------------------------------------------------------------------------


def test_consolidation_on_overflow():
    em = EvoMemory(max_short_term=3)
    em.remember("low", importance=0.2)
    em.remember("medium", importance=0.6)
    em.remember("high", importance=0.9)
    # Adding a 4th triggers consolidation
    em.remember("another high", importance=0.8)
    assert len(em.short_term) <= em.max_short_term


def test_important_memories_promoted_to_long_term():
    em = EvoMemory(max_short_term=2)
    em.remember("low importance", importance=0.1)
    em.remember("high importance", importance=0.9)
    # Trigger consolidation with a third memory
    em.remember("trigger", importance=0.6)
    # High-importance memory should end up somewhere
    all_contents = [m.content for m in em.short_term + em.long_term]
    assert "high importance" in all_contents


def test_manual_consolidate():
    em = EvoMemory(max_short_term=5)
    for i in range(3):
        em.remember(f"memory {i}", importance=0.8)
    em.consolidate()
    assert len(em.short_term) <= em.max_short_term


# ---------------------------------------------------------------------------
# decay
# ---------------------------------------------------------------------------


def test_decay_reduces_importance():
    em = EvoMemory(decay_rate=1.0)
    m = em.remember("fading", importance=1.0)
    # Wind back the last-decay clock so it appears 2 hours have elapsed
    em._last_decay_time -= TWO_HOURS_IN_SECONDS
    em.decay()
    assert m.importance < 1.0 or m not in em.short_term


def test_decay_removes_zero_importance_memories():
    em = EvoMemory(decay_rate=10.0)
    m = em.remember("forgotten", importance=0.1)
    em._last_decay_time -= TWO_HOURS_IN_SECONDS  # 2 hours ago
    em.decay()
    assert m not in em.short_term


# ---------------------------------------------------------------------------
# save / load
# ---------------------------------------------------------------------------


def test_save_and_load(tmp_path):
    em = EvoMemory()
    em.remember("persistent", importance=0.9, tags=["save"])
    path = str(tmp_path / "memories.json")
    em.save(path)

    fresh = EvoMemory()
    fresh.load(path)
    assert len(fresh) == 1
    assert fresh.short_term[0].content == "persistent"
    assert fresh.short_term[0].tags == ["save"]


def test_save_creates_valid_json(tmp_path):
    em = EvoMemory()
    em.remember("check json")
    path = str(tmp_path / "check.json")
    em.save(path)
    with open(path) as fh:
        data = json.load(fh)
    assert "short_term" in data
    assert "long_term" in data


# ---------------------------------------------------------------------------
# __repr__ and __len__
# ---------------------------------------------------------------------------


def test_repr():
    em = EvoMemory()
    em.remember("x")
    r = repr(em)
    assert "EvoMemory" in r
    assert "short_term=1" in r


def test_len():
    em = EvoMemory()
    assert len(em) == 0
    em.remember("a")
    em.remember("b")
    assert len(em) == 2
