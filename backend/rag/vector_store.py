from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List
import os

import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from openai import OpenAI

from config.settings import get_settings

logger = logging.getLogger(__name__)
_COLLECTION_NAME = "stock_research_reports"
_PERSIST_DIR = Path(__file__).parent.parent / "data" / "chromadb"
_client: chromadb.PersistentClient | None = None
_collection: chromadb.Collection | None = None


class _OpenAIEmbedder(EmbeddingFunction):
    """Custom embedding function that calls the OpenAI API directly.
    Avoids the NoneType iteration bug in chromadb's built-in wrapper (>=1.5)."""

    def __init__(self,api_base:str, api_key: str, model: str = "text-embedding-3-small"):
        self._client = OpenAI(base_url=api_base,api_key=api_key)
        self._model = model

    def __call__(self, input: Documents) -> Embeddings:  # type: ignore[override]
        response = self._client.embeddings.create(model=self._model, input=list(input))
        return [item.embedding for item in response.data]


def _get_collection() -> chromadb.Collection:
    """Lazily initialise the ChromaDB client and collection."""
    global _client, _collection
    if _collection is not None:
        return _collection

    settings = get_settings()
    _PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("[RAG] Initialising ChromaDB PersistentClient at: %s", _PERSIST_DIR)
    _client = chromadb.PersistentClient(path=str(_PERSIST_DIR))

    api_base = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    logger.info("[RAG] Building embedder | base_url=%s | api_key_set=%s", api_base, bool(api_key))
    embedding_fn = _OpenAIEmbedder(api_base=api_base, api_key=api_key)

    _collection = _client.get_or_create_collection(
        name=_COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )
    logger.info("[RAG] ChromaDB collection '%s' ready at %s", _COLLECTION_NAME, _PERSIST_DIR)
    return _collection

def embed_report(report: str, ticker: str, metadata: dict | None = None) -> str:
    """Store a completed research report as an embedding in ChromaDB."""
    logger.info("[RAG] embed_report called | ticker=%s | report_len=%d", ticker, len(report))
    collection = _get_collection()
    doc_id = f"{ticker.upper()}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
    meta = {
        "ticker": ticker.upper(),
        "stored_at": datetime.now(timezone.utc).isoformat(),
        **(metadata or {}),
    }
    logger.info("[RAG] Calling collection.add | doc_id=%s", doc_id)
    collection.add(documents=[report], ids=[doc_id], metadatas=[meta])
    logger.info("[RAG] Report stored successfully | ticker=%s | doc_id=%s", ticker, doc_id)
    return doc_id

def retrieve_similar(ticker: str, query: str, k: int = 3) -> list[str]:
    """Fetch top-k semantically similar past analyses for a given ticker."""
    logger.info("[RAG] retrieve_similar called | ticker=%s | k=%d", ticker, k)
    collection = _get_collection()
    count = collection.count()
    logger.info("[RAG] Collection total doc count=%d", count)
    if count == 0:
        logger.info("[RAG] Collection empty — no prior context available")
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(k, count),
        where={"ticker": ticker.upper()},
    )
    raw_docs = results.get("documents", [[]])
    logger.info("[RAG] Raw query results | documents type=%s value=%s", type(raw_docs), raw_docs)
    docs: list[str] = (raw_docs[0] or []) if raw_docs else []
    logger.info("[RAG] Retrieved %d prior analyses for %s", len(docs), ticker.upper())
    return docs
    