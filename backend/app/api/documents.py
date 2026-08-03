import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from app.core.config import get_settings
from app.rag.chunking import chunk_text, parse_file
from app.rag.embeddings import embed_texts

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(user_id: str, doc_type: str, file: UploadFile):
    if doc_type not in ("company_policy", "regulation"):
        raise HTTPException(400, "doc_type must be 'company_policy' or 'regulation'")

    suffix = Path(file.filename or "upload").suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    text = parse_file(tmp_path)
    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(400, f"Could not extract any text from {file.filename}")

    embeddings = embed_texts(chunks)
    metadatas = [{"filename": file.filename} for _ in chunks]
    settings = get_settings()

    if not settings.supabase_url:
        from app.rag.local_store import add_chunks

        document_id = add_chunks(
            doc_type=doc_type, contents=chunks, embeddings=embeddings, metadatas=metadatas, user_id=user_id
        )
        return {"document_id": document_id, "chunks_indexed": len(chunks)}

    from app.core.supabase_client import get_supabase

    supabase = get_supabase()
    doc_row = (
        supabase.table("documents")
        .insert({"user_id": user_id, "filename": file.filename, "doc_type": doc_type})
        .execute()
    )
    document_id = doc_row.data[0]["id"]

    rows = [
        {"document_id": document_id, "content": chunk, "embedding": embedding, "metadata": meta}
        for chunk, embedding, meta in zip(chunks, embeddings, metadatas)
    ]
    supabase.table("document_chunks").insert(rows).execute()

    return {"document_id": document_id, "chunks_indexed": len(rows)}
