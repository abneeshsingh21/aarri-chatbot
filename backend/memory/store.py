# backend/memory/store.py
import os
import json
import numpy as np
import faiss
import sqlite3

from sentence_transformers import SentenceTransformer
from typing import List, Tuple

BASE = os.path.dirname(__file__)
SQLITE_FILE = os.path.join(BASE, "..", "aarii_memory_meta.sqlite")
INDEX_FILE = os.path.join(BASE, "faiss_index.index")

MODEL_NAME = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
# Lazy-load model on first use to avoid startup delays
emb_model = None
EMBED_DIM = 384  # all-MiniLM-L6-v2 default dimension


def _get_embedding_model():
    """Lazy-load the embedding model on first use."""
    global emb_model
    if emb_model is None:
        emb_model = SentenceTransformer(MODEL_NAME)
    return emb_model


def _conn():
    c = sqlite3.connect(SQLITE_FILE, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    c = _conn()
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS memory (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT,
      text TEXT,
      meta TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    c.execute(
        """
    CREATE TABLE IF NOT EXISTS mapping (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      faiss_index INTEGER UNIQUE,
      memory_row_id INTEGER UNIQUE,
      session_id TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    c.commit()
    c.close()


def _load_index():
    if os.path.exists(INDEX_FILE):
        return faiss.read_index(INDEX_FILE)

    # use normalized vectors -> IndexFlatIP works with normalized embeddings
    idx = faiss.IndexFlatIP(EMBED_DIM)
    return idx


def _save_index(idx):
    faiss.write_index(idx, INDEX_FILE)


def _normalize(vecs: np.ndarray):
    # vecs: (n, d)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms


def add_memory(session_id: str, text: str, meta: dict = None):
    """Insert memory into DB and FAISS; return memory_row_id."""
    init_db()
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO memory (session_id, text, meta) VALUES (?, ?, ?)",
        (session_id, text, json.dumps(meta or {})),
    )
    rowid = cur.lastrowid
    conn.commit()
    conn.close()

    # embed and add to FAISS
    model = _get_embedding_model()
    vec = model.encode([text])
    arr = np.array(vec, dtype="float32")
    vec = _normalize(arr)

    idx = _load_index()
    before = idx.ntotal
    idx.add(vec)
    # new faiss index is 'before' (0-based)
    faiss_idx = before
    _save_index(idx)

    # store mapping
    conn = _conn()
    cur = conn.cursor()
    sql = (
        "INSERT INTO mapping (faiss_index, memory_row_id, session_id) "
        "VALUES (?, ?, ?)"
    )
    cur.execute(sql, (faiss_idx, rowid, session_id))
    conn.commit()
    conn.close()
    return rowid


def query_memory(
    query: str,
    top_k: int = 5,
) -> List[Tuple[int, float, str, dict]]:
    """Returns list of tuples (memory_row_id, score, text, meta)."""
    init_db()
    idx = _load_index()
    if idx.ntotal == 0:
        return []
    model = _get_embedding_model()
    q = model.encode([query])
    arr = np.array(q, dtype="float32")
    q = _normalize(arr)
    distances, indexes = idx.search(q, top_k)
    ids = indexes[0].tolist()
    scores = distances[0].tolist()
    results = []
    conn = _conn()
    cur = conn.cursor()
    for faiss_idx, score in zip(ids, scores):
        if faiss_idx < 0:
            continue
        # lookup memory_row_id from mapping
        cur.execute(
            "SELECT memory_row_id FROM mapping WHERE faiss_index = ?",
            (faiss_idx,),
        )
        r = cur.fetchone()
        if not r:
            continue
        mem_id = r["memory_row_id"]
        cur.execute(
            "SELECT id, text, meta FROM memory WHERE id = ?",
            (mem_id,),
        )
        row = cur.fetchone()
        if row:
            meta = json.loads(row["meta"] or "{}")
            results.append((row["id"], float(score), row["text"], meta))
    conn.close()
    return results
