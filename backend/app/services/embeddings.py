"""Embeddings via OpenAI (text-embedding-3). Usado para o perfil sensorial
dos vinhos e do usuário (busca de similaridade no pgvector)."""

import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def embed_text(text: str) -> list[float]:
    """Retorna o vetor de embedding de um texto."""
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    resp = client.embeddings.create(
        model=settings.embedding_model,
        input=text.replace("\n", " ").strip()[:8000],
    )
    return resp.data[0].embedding


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embeddings em lote (até ~2048 itens por chamada na OpenAI)."""
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    cleaned = [t.replace("\n", " ").strip()[:8000] for t in texts]
    resp = client.embeddings.create(model=settings.embedding_model, input=cleaned)
    return [d.embedding for d in resp.data]
