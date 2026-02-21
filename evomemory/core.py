import os
import json
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
import numpy as np
import faiss
from fastembed import TextEmbedding

class EvoMemory:
    """
    Lightweight, local, evolving memory system for AI agents.
    Features strategic forgetting, graph lattice, clones, and creative mode.
    """
    def __init__(self, agent_name: str = "agent", base_dir: str = "./memories"):
        self.agent_name = agent_name.lower().replace(" ", "_")
        self.dir = Path(base_dir) / self.agent_name
        self.dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.dir / "memory.db"
        self.index_path = self.dir / "faiss.index"

        self.dim = 384
        self.embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

        self.index = self._load_or_create_index()
        self.conn = self._init_db()

    def _load_or_create_index(self):
        if self.index_path.exists():
            return faiss.read_index(str(self.index_path))
        index = faiss.IndexFlatIP(self.dim)
        return index

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY,
                vector_id INTEGER,
                content TEXT,
                summary TEXT,
                type TEXT DEFAULT 'general',
                timestamp TEXT,
                last_access TEXT,
                importance REAL DEFAULT 0.5,
                valence REAL DEFAULT 0.0,
                access_count INTEGER DEFAULT 0,
                tags TEXT
            );
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY,
                source_id INTEGER,
                target_id INTEGER,
                rel_type TEXT,
                strength REAL DEFAULT 1.0,
                timestamp TEXT
            );
        """)
        conn.commit()
        return conn

    def _embed(self, text: str):
        emb = np.array(list(self.embedder.embed([text]))[0]).astype('float32')
        faiss.normalize_L2(emb.reshape(1, -1))
        return emb

    def _save(self):
        faiss.write_index(self.index, str(self.index_path))
        self.conn.commit()

    def add(self, content: str, mem_type: str = "general", tags: list = None,
            summary: str = None, importance: float = 0.7, valence: float = 0.0):
        if tags is None:
            tags = []
        if summary is None:
            summary = content[:300] + "..." if len(content) > 300 else content

        vec = self._embed(content)
        vector_id = self.index.ntotal
        self.index.add(vec.reshape(1, -1))

        now = datetime.now().isoformat()
        tags_str = json.dumps(tags)

        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO nodes (vector_id, content, summary, type, timestamp, last_access,
                               importance, valence, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (vector_id, content, summary, mem_type, now, now, importance, valence, tags_str))
        node_id = cur.lastrowid
        self._save()
        return node_id

    def search(self, query: str, k: int = 5, min_importance: float = 0.2, mode: str = "similar"):
        qvec = self._embed(query)
        D, I = self.index.search(qvec.reshape(1, -1), k * 3)

        cur = self.conn.cursor()
        placeholders = ','.join('?' for _ in I[0])
        cur.execute(f"""
            SELECT id, vector_id, content, summary, type, importance, valence, tags
            FROM nodes WHERE vector_id IN ({placeholders}) AND importance >= ?
            ORDER BY importance DESC
        """, tuple(I[0]) + (min_importance,))
        rows = cur.fetchall()

        results = []
        for row in rows:
            vec_id = row['vector_id']
            idx = np.where(I[0] == vec_id)[0]
            if len(idx) == 0:
                continue
            score = float(D[0][idx[0]])
            if mode == "dissonant":
                score = -score
            results.append({
                "node_id": row['id'],
                "content": row['content'],
                "summary": row['summary'],
                "score": score,
                "importance": row['importance'],
                "valence": row['valence'],
                "type": row['type']
            })

        results.sort(key=lambda x: x['score'], reverse=(mode == "similar"))
        return results[:k]

    def add_relation(self, source_id: int, target_id: int, rel_type: str, strength: float = 1.0):
        now = datetime.now().isoformat()
        self.conn.execute("""
            INSERT INTO edges (source_id, target_id, rel_type, strength, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (source_id, target_id, rel_type, strength, now))
        self._save()

    def get_rich_context(self, query: str, k: int = 5, depth: int = 2):
        primary = self.search(query, k, mode="similar")
        context = primary[:]
        for item in primary:
            cur = self.conn.cursor()
            cur.execute("""
                SELECT n.content, n.summary, e.rel_type
                FROM edges e JOIN nodes n ON n.id = e.target_id
                WHERE e.source_id = ? LIMIT ?
            """, (item["node_id"], depth * 3))
            for row in cur.fetchall():
                context.append({
                    "content": row['content'],
                    "summary": row['summary'],
                    "relation": row['rel_type'],
                    "score": item["score"] * 0.7
                })
        return context[:k*2]

    def decay_and_prune(self):
        now = datetime.now()
        cur = self.conn.cursor()
        cur.execute("SELECT id, timestamp, valence, importance FROM nodes")
        for row in cur.fetchall():
            age_days = (now - datetime.fromisoformat(row['timestamp'])).days
            half_life = 30 + (row['valence'] * 20)
            decay = 0.5 ** (age_days / half_life)
            new_imp = row['importance'] * decay
            cur.execute("UPDATE nodes SET importance = ? WHERE id = ?", (new_imp, row['id']))

        cur.execute("DELETE FROM nodes WHERE importance < 0.15")
        cur.execute("DELETE FROM edges WHERE source_id NOT IN (SELECT id FROM nodes) OR target_id NOT IN (SELECT id FROM nodes)")
        self.conn.commit()
        self._rebuild_index()

    def _rebuild_index(self):
        cur = self.conn.cursor()
        cur.execute("SELECT vector_id FROM nodes ORDER BY vector_id")
        active_ids = [r['vector_id'] for r in cur.fetchall()]
        if not active_ids:
            self.index.reset()
            return
        new_index = faiss.IndexFlatIP(self.dim)
        self.index = new_index
        self._save()

    def clone(self, new_name: str, corruption_rate: float = 0.15):
        new_mem = EvoMemory(new_name, self.dir.parent)
        shutil.copytree(self.dir, new_mem.dir, dirs_exist_ok=True)

        cur = new_mem.conn.cursor()
        cur.execute("SELECT id FROM edges")
        for row in cur.fetchall():
            if np.random.rand() < corruption_rate:
                cur.execute("UPDATE edges SET strength = strength * 0.3 WHERE id = ?", (row['id'],))
            if np.random.rand() < corruption_rate * 0.5:
                cur.execute("DELETE FROM edges WHERE id = ?", (row['id'],))
        cur.execute("UPDATE nodes SET valence = valence + (RANDOM() * 0.4 - 0.2)")
        new_mem.conn.commit()
        new_mem._save()
        return new_mem

    def close(self):
        self.decay_and_prune()
        self._save()
        self.conn.close()
