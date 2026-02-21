# EvoMemory

**Lightweight, local, human-like memory engine for AI agents.**

Built for old hardware (like 2011 Dell old) and even extremely well made memory system for scaling on new gen, zero cloud, zero heavy runtimes.  
Uses **FAISS + SQLite** with strategic forgetting, graph lattice recall, branching clones, and creative "dissonant" mode.

Perfect for personal agents, co-founders, or any local LLM bot that needs real memory without paying OpenAI or burning CPU.

## Features

- **Strategic forgetting** — half-life decay based on emotional valence + importance
- **Lattice recall** — similarity search + graph traversal (2nd/3rd degree connections)
- **Dissonant mode** — return least-similar memories for creative/strategic thinking
- **Cloning** — create branching realities with intentional corruption
- **CPU-light** — runs great on 4-core old desktops (<20% idle)
- **Pure Python** — only `faiss-cpu`, `fastembed`, `numpy`

- Full Documentation
See the examples/ folder and docstrings in evomemory/core.py.
License
MIT — free for commercial and personal use. See LICENSE.

Made with ❤️ for local agents that deserve real memory.



## Installation

```bash
pip install evomemory

****Quick Start****

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



