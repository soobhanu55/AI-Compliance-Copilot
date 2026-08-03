"""JSON + cosine-similarity fallback vector store, used when SUPABASE_URL is not configured.

Lets the RAG pipeline (data indexing + retrieval) be developed and tested end to end before a
Supabase project exists. Swap to Supabase/pgvector for real multi-user deployment — this store
has no auth/RLS and loads the entire index into memory on every query.
"""

import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.models.schemas import DocumentChunk

INDEX_PATH = Path(__file__).resolve().parents[3] / "data_pipeline" / "local_index" / "chunks.json"
REPORTS_PATH = Path(__file__).resolve().parents[3] / "data_pipeline" / "local_index" / "reports.json"


def _load() -> list[dict]:
    if not INDEX_PATH.exists():
        return []
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def _save(records: list[dict]) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(records), encoding="utf-8")


def add_chunks(
    doc_type: str,
    contents: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
    user_id: str | None = None,
    document_id: str | None = None,
) -> str:
    document_id = document_id or str(uuid.uuid4())
    records = _load()
    for content, embedding, metadata in zip(contents, embeddings, metadatas):
        records.append(
            {
                "id": str(uuid.uuid4()),
                "document_id": document_id,
                "doc_type": doc_type,
                "user_id": user_id,
                "content": content,
                "embedding": embedding,
                "metadata": metadata,
            }
        )
    _save(records)
    return document_id


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b + 1e-8)


def search(
    query_embedding: list[float],
    top_k: int,
    user_id: str | None = None,
    doc_type: str | None = None,
) -> list[DocumentChunk]:
    records = _load()
    if doc_type:
        records = [r for r in records if r["doc_type"] == doc_type]
    if user_id:
        records = [r for r in records if r["doc_type"] == "regulation" or r["user_id"] == user_id]
    if not records:
        return []

    scored = [(r, _cosine(r["embedding"], query_embedding)) for r in records]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    top = scored[:top_k]
    return [
        DocumentChunk(id=r["id"], document_id=r["document_id"], content=r["content"], metadata=r["metadata"], score=score)
        for r, score in top
    ]


def _load_reports() -> list[dict]:
    if not REPORTS_PATH.exists():
        return []
    return json.loads(REPORTS_PATH.read_text(encoding="utf-8"))


def save_report(user_id: str, company_profile: dict, report_content: dict) -> dict:
    reports = _load_reports()
    row = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "company_profile": company_profile,
        "report_content": report_content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    reports.append(row)
    REPORTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORTS_PATH.write_text(json.dumps(reports), encoding="utf-8")
    return row


def get_report(report_id: str) -> dict | None:
    return next((r for r in _load_reports() if r["id"] == report_id), None)
