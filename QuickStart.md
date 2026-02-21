from evomemory import EvoMemory

mem = EvoMemory("myagent")

# Add memories
mem.add("Q1 revenue target is $47k", mem_type="goal", importance=0.95, valence=0.8)
mem.add("Client prefers bullet-point proposals", mem_type="profile", importance=0.9)

# Normal recall
results = mem.search("revenue target", k=5)

# Rich context (lattice)
context = mem.get_rich_context("revenue target", depth=2)

# Creative ideas
ideas = mem.search("revenue target", k=5, mode="dissonant")

# Strategic forgetting (run periodically)
mem.decay_and_prune()

# Clone with variation
clone = mem.clone("myagent_v2", corruption_rate=0.12)
