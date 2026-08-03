from fastapi import APIRouter

from app.models.schemas import ChatRequest, ChatResponse, Citation
from app.rag.retriever import retrieve

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _build_answer(request: ChatRequest, citations: list[Citation]) -> str:
    # Extractive, not generative — no LLM API key is configured in this environment. Quotes
    # the top retrieved clause directly rather than fabricating natural-language synthesis.
    # Honestly disclosed instead of faked: source text is English regardless of `language`,
    # since no translation is wired up either.
    if not citations:
        return "No matching regulation text was found for this question."

    top = citations[0]
    note = ""
    if request.language == "de":
        note = " (Hinweis: automatische Übersetzung ist noch nicht angebunden — Zitat auf Englisch.)"

    return (
        f"The most relevant provision found is {top.regulation} {top.article}: "
        f'"{top.excerpt.strip()}"{note} See the additional citations below for related context.'
    )


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    chunks = retrieve(request.message, user_id=request.user_id, top_k=6)

    citations = [
        Citation(
            regulation=c.metadata.get("regulation", "unknown"),
            article=c.metadata.get("article", "unknown"),
            chunk_id=c.id,
            excerpt=c.content[:200],
        )
        for c in chunks
    ]

    return ChatResponse(answer=_build_answer(request, citations), citations=citations)
