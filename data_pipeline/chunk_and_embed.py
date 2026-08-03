"""Embed structured regulation articles and load them into Supabase.

Input: a `*_articles.json` file shaped like:
    {"regulation": "AI Act", "celex": "32024R1689", "source_url": "...",
     "articles": [{"heading": "Article 1", "title": "Subject matter", "body": "..."}, ...]}

These files are produced by loading the EUR-Lex consolidated-text page in a real browser
(EUR-Lex sits behind bot-detection that blocks plain HTTP fetches) and walking the DOM for
`.oj-ti-art` / `.oj-sti-art` paragraphs, which mark true article headings — this avoids
splitting on every inline cross-reference like "in accordance with Article 6".

Usage:
    python chunk_and_embed.py --file regulations/ai_act_articles.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import get_settings
from app.rag.embeddings import embed_texts

MAX_CHARS_PER_CHUNK = 4000  # split unusually long articles further; most articles fit in one


def _split_long_body(body: str, max_chars: int) -> list[str]:
    if len(body) <= max_chars:
        return [body]
    paragraphs = body.split("\n")
    chunks, current = [], ""
    for para in paragraphs:
        if len(current) + len(para) + 1 > max_chars and current:
            chunks.append(current)
            current = para
        else:
            current = f"{current}\n{para}" if current else para
    if current:
        chunks.append(current)
    return chunks


def load_regulation(articles_path: Path):
    data = json.loads(articles_path.read_text(encoding="utf-8"))
    regulation_name = data["regulation"]

    contents: list[str] = []
    metadata: list[dict] = []
    for article in data["articles"]:
        # Strip EUR-Lex's amending-legislation "inserted article" marker (U+2018) — legally
        # meaningful in the directive text, just noise for a citation label.
        heading = article["heading"].replace("\xa0", " ").lstrip("‘")
        title = article.get("title", "").rstrip("`")
        body = article["body"]

        for i, piece in enumerate(_split_long_body(body, MAX_CHARS_PER_CHUNK)):
            contents.append(f"{heading} — {title}\n{piece}" if title else f"{heading}\n{piece}")
            metadata.append(
                {
                    "regulation": regulation_name,
                    "article": heading,
                    "article_title": title,
                    "part": i,
                }
            )

    if not contents:
        print(f"No articles found in {articles_path}")
        return

    embeddings = embed_texts(contents)
    settings = get_settings()

    if not settings.supabase_url:
        from app.rag.local_store import add_chunks

        add_chunks(doc_type="regulation", contents=contents, embeddings=embeddings, metadatas=metadata)
        print(f"[local store] Indexed {len(contents)} chunks from {regulation_name} ({articles_path.name})")
        return

    from app.core.supabase_client import get_supabase

    supabase = get_supabase()
    doc_row = (
        supabase.table("documents")
        .insert({"user_id": None, "filename": articles_path.name, "doc_type": "regulation"})
        .execute()
    )
    document_id = doc_row.data[0]["id"]

    rows = [
        {"document_id": document_id, "content": content, "embedding": embedding, "metadata": meta}
        for content, embedding, meta in zip(contents, embeddings, metadata)
    ]
    supabase.table("document_chunks").insert(rows).execute()
    print(f"[supabase] Indexed {len(rows)} chunks from {regulation_name} ({articles_path.name})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, type=Path)
    args = parser.parse_args()

    load_regulation(args.file)
