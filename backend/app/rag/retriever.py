"""Vector retrieval over company docs + regulation corpus.

Uses Supabase/pgvector when SUPABASE_URL is configured; otherwise falls back to the local
JSON store (app.rag.local_store) so the pipeline can be developed without a live project.
"""

from app.core.config import get_settings
from app.models.schemas import DocumentChunk
from app.rag.embeddings import embed_query


def retrieve(
    query: str,
    user_id: str,
    doc_type: str | None = None,
    top_k: int = 8,
) -> list[DocumentChunk]:
    embedding = embed_query(query)
    settings = get_settings()

    if not settings.supabase_url:
        from app.rag.local_store import search

        return search(embedding, top_k, user_id=user_id, doc_type=doc_type)

    from app.core.supabase_client import get_supabase

    # Calls a Postgres RPC function `match_document_chunks` (create via Supabase SQL editor):
    #
    #   create or replace function match_document_chunks(
    #     query_embedding vector(1024), match_count int, filter_user_id uuid, filter_doc_type text
    #   ) returns setof document_chunks language sql stable as $$
    #     select dc.* from document_chunks dc
    #     join documents d on d.id = dc.document_id
    #     where (d.user_id = filter_user_id or d.doc_type = 'regulation')
    #       and (filter_doc_type is null or d.doc_type = filter_doc_type)
    #     order by dc.embedding <=> query_embedding
    #     limit match_count;
    #   $$;
    supabase = get_supabase()
    response = supabase.rpc(
        "match_document_chunks",
        {
            "query_embedding": embedding,
            "match_count": top_k,
            "filter_user_id": user_id,
            "filter_doc_type": doc_type,
        },
    ).execute()

    return [DocumentChunk(**row) for row in response.data]
