"""Basic usage example for EvoMemory."""

from evomemory import EvoMemory

# Create a memory engine with a short-term capacity of 5 memories
mem = EvoMemory(max_short_term=5)

# Store some memories with varying importance
mem.remember("The sky is blue", importance=0.4, tags=["fact", "nature"])
mem.remember("User prefers dark mode", importance=0.9, tags=["preference", "ui"])
mem.remember("Meeting at 3 pm tomorrow", importance=0.8, tags=["calendar"])
mem.remember("Favourite colour is green", importance=0.7, tags=["preference"])
mem.remember("Python is great", importance=0.6, tags=["fact", "tech"])

print("After 5 memories:")
print(mem)  # EvoMemory(short_term=5, long_term=0)

# Adding a 6th triggers consolidation: lowest-importance memories are
# promoted to long-term if important enough, or discarded otherwise.
mem.remember("User dislikes Comic Sans", importance=0.85, tags=["preference", "ui"])

print("\nAfter 6th memory (consolidation triggered):")
print(mem)

# Recall all memories matching a query
print("\nRecall 'preference' tag:")
for m in mem.recall(tags=["preference"]):
    print(f"  [{m.importance:.2f}] {m.content}")

# Recall with a substring query
print("\nRecall memories mentioning 'dark':")
for m in mem.recall(query="dark"):
    print(f"  [{m.importance:.2f}] {m.content}")

# Persist to disk and reload
mem.save("/tmp/evomemory_demo.json")
fresh = EvoMemory()
fresh.load("/tmp/evomemory_demo.json")
print(f"\nReloaded: {fresh}")
