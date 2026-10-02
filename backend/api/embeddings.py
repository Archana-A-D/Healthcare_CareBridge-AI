"""Gemini vector embeddings and cosine retrieval for page-aware RAG."""

import json
import hashlib
import logging
import math
import os
from urllib.request import Request, urlopen

from django.core.cache import cache


logger = logging.getLogger("carebridge.ai")
MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
DIMENSIONS = 256
BATCH_SIZE = 64
MAX_CHUNKS = 256


def _post(payload, operation):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    request = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:{operation}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST",
    )
    timeout = max(5, min(int(os.getenv("GEMINI_REQUEST_TIMEOUT_SECONDS", "20")), 60))
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _unit_vector(values):
    vector = [float(value) for value in values]
    norm = math.sqrt(sum(value * value for value in vector))
    if not norm:
        return []
    return [value / norm for value in vector]


def embed_document_chunks(chunks, correlation_id=""):
    """Add normalized retrieval-document vectors in bounded batches.

    Failure is non-fatal: the caller retains page chunks and lexical retrieval.
    """
    if not chunks or len(chunks) > MAX_CHUNKS or not os.getenv("GEMINI_API_KEY"):
        return False
    try:
        for offset in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[offset:offset + BATCH_SIZE]
            payload = {
                "requests": [
                    {
                        "model": f"models/{MODEL}",
                        "content": {"parts": [{"text": item["text"][:6000]}]},
                        "embedContentConfig": {
                            "taskType": "RETRIEVAL_DOCUMENT",
                            "outputDimensionality": DIMENSIONS,
                        },
                    }
                    for item in batch
                ]
            }
            result = _post(payload, "batchEmbedContents")
            vectors = result.get("embeddings", [])
            if len(vectors) != len(batch):
                raise RuntimeError("Embedding service returned an incomplete batch.")
            for item, embedding in zip(batch, vectors):
                item["embedding"] = _unit_vector(embedding.get("values", []))
            usage = result.get("usageMetadata", {})
            if usage:
                _record_embedding_usage(correlation_id, usage)
        return True
    except Exception:
        logger.exception("Document embeddings unavailable; falling back to lexical retrieval", extra={"correlation_id": correlation_id})
        for chunk in chunks:
            chunk.pop("embedding", None)
        return False


def embed_query(question, correlation_id=""):
    if not os.getenv("GEMINI_API_KEY"):
        return None
    bounded_question = question[:2000]
    cache_key = "carebridge:query-embedding:" + hashlib.sha256(
        f"{MODEL}\0{bounded_question}".encode("utf-8")
    ).hexdigest()
    try:
        cached = cache.get(cache_key)
        if (
            isinstance(cached, list)
            and len(cached) == DIMENSIONS
            and all(isinstance(value, (int, float)) and math.isfinite(value) for value in cached)
        ):
            return _unit_vector(cached) or None
    except Exception:
        logger.warning("Query-embedding cache unavailable; requesting a fresh vector", extra={"correlation_id": correlation_id})
    try:
        result = _post(
            {
                "model": f"models/{MODEL}",
                "content": {"parts": [{"text": bounded_question}]},
                "embedContentConfig": {"taskType": "RETRIEVAL_QUERY", "outputDimensionality": DIMENSIONS},
            },
            "embedContent",
        )
        usage = result.get("usageMetadata", {})
        if usage:
            _record_embedding_usage(correlation_id, usage)
        vector = _unit_vector(result.get("embedding", {}).get("values", [])) or None
        if vector:
            ttl = max(0, int(os.getenv("QUERY_EMBEDDING_CACHE_TTL_SECONDS", "3600")))
            if ttl:
                try:
                    cache.set(cache_key, vector, timeout=ttl)
                except Exception:
                    logger.warning("Could not cache query embedding", extra={"correlation_id": correlation_id})
        return vector
    except Exception:
        logger.exception("Query embedding unavailable; falling back to lexical retrieval", extra={"correlation_id": correlation_id})
        return None


def rank_by_cosine(chunks, query_vector, limit=5):
    if not query_vector:
        return []
    candidates = [item for item in chunks if item.get("embedding") and len(item["embedding"]) == len(query_vector)]
    if not candidates:
        return []
    ranked = sorted(
        candidates,
        key=lambda item: sum(float(left) * float(right) for left, right in zip(item["embedding"], query_vector)),
        reverse=True,
    )
    return ranked[:limit]


def _record_embedding_usage(correlation_id, usage):
    # Keep embedding input tokens visible in the same per-query usage/cost ledger.
    from .views import _save_usage

    _save_usage(correlation_id, "embedding", MODEL, {
        "promptTokenCount": usage.get("promptTokenCount", 0),
        "candidatesTokenCount": 0,
    })
