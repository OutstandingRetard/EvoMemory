# EvoMemory

**Lightweight, local, human-like memory engine for AI agents.**

Built for old hardware (like 2011 Dell OptiPlex), zero cloud, zero heavy runtimes.  
Uses **FAISS + SQLite** with strategic forgetting, graph lattice recall, branching clones, and creative "dissonant" mode.

Perfect for personal agents, co-founders, or any local LLM bot that needs real memory without paying OpenAI or burning CPU.

## Features

- **Strategic forgetting** — half-life decay based on emotional valence + importance
- **Lattice recall** — similarity search + graph traversal (2nd/3rd degree connections)
- **Dissonant mode** — return least-similar memories for creative/strategic thinking
- **Cloning** — create branching realities with intentional corruption
- **CPU-light** — runs great on 4-core old desktops (<20% idle)
- **Pure Python** — only `faiss-cpu`, `fastembed`, `numpy`

## Installation

```bash
pip install evomemory
