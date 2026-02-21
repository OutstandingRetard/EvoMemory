"""Basic usage example for EvoMemory."""

from evomemory import EvoMemory

# Create a memory engine
mem = EvoMemory()

# Store some memories
mem.store("The user prefers concise answers.")
mem.store("The user is working on a Python project.")
mem.store("The user mentioned they like coffee.")

print(f"Total memories: {len(mem)}")

# Retrieve memories relevant to a query
results = mem.retrieve("Python project", n=2)
print("\nTop results for 'Python project':")
for r in results:
    print(f"  [{r.id[:8]}] {r.content}")

# Retrieve the most recent memories (no query)
recent = mem.retrieve(n=2)
print("\nMost recent memories:")
for r in recent:
    print(f"  [{r.id[:8]}] {r.content}")

# Forget a specific memory
first_id = mem.store("Temporary note.")
print(f"\nStored temporary note with id={first_id[:8]}")
forgotten = mem.forget(first_id)
print(f"Forgotten: {forgotten}, memories left: {len(mem)}")

# Clear everything
mem.clear()
print(f"\nAfter clear: {mem}")
