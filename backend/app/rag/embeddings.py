"""Embedding backend abstraction.

Default: `intfloat/multilingual-e5-large` (local, free, strong on German legal/business text).
Alternative: OpenAI `text-embedding-3-large` — set EMBEDDING_PROVIDER=openai in .env.
"""

from functools import lru_cache

from app.core.config import get_settings


@lru_cache
def _e5_model():
    from sentence_transformers import SentenceTransformer

    settings = get_settings()
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    settings = get_settings()

    if settings.embedding_provider == "openai":
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        # e5 models expect a "query: " / "passage: " prefix; OpenAI does not.
        response = client.embeddings.create(model="text-embedding-3-large", input=texts)
        return [item.embedding for item in response.data]

    model = _e5_model()
    prefixed = [f"passage: {t}" for t in texts]
    return model.encode(prefixed, normalize_embeddings=True).tolist()


def embed_query(text: str) -> list[float]:
    settings = get_settings()
    if settings.embedding_provider == "openai":
        return embed_texts([text])[0]

    model = _e5_model()
    return model.encode([f"query: {text}"], normalize_embeddings=True).tolist()[0]
