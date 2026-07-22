"""AI Provider — Claude (primário) com OpenAI de fallback.

Portado do salesclub-intel, já com o parser robusto (extrai texto de TODOS os
blocos de texto — sonnet-5 pode retornar bloco não-texto antes) + fallback.
"""

import logging
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class AIResponse:
    content: str
    provider: str
    input_tokens: int
    output_tokens: int
    was_truncated: bool = False


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=10))
def _call_anthropic(system_prompt: str, user_prompt: str, model: str | None = None,
                    max_tokens: int = 8000) -> AIResponse:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=model or settings.ai_model_anthropic,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    text_parts = [
        (getattr(b, "text", "") or "")
        for b in (response.content or [])
        if getattr(b, "type", None) == "text"
    ]
    content = "".join(text_parts).strip()
    if not content:
        blocks = [getattr(b, "type", None) for b in (response.content or [])]
        logger.warning(f"Anthropic sem texto (stop={response.stop_reason}, blocos={blocks}).")
        raise ValueError("Anthropic response has no text content")

    return AIResponse(
        content=content,
        provider="anthropic",
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        was_truncated=response.stop_reason == "max_tokens",
    )


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=10))
def _call_openai(system_prompt: str, user_prompt: str, max_tokens: int = 8000) -> AIResponse:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.ai_model_openai,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    content = response.choices[0].message.content
    if not content:
        raise ValueError("OpenAI response has no content")

    return AIResponse(
        content=content,
        provider="openai",
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
        was_truncated=response.choices[0].finish_reason == "length",
    )


def generate_with_fallback(system_prompt: str, user_prompt: str,
                           model: str | None = None, max_tokens: int = 8000) -> AIResponse:
    """Chama o provedor primário; cai pro secundário em falha."""
    primary = settings.ai_primary_provider
    try:
        if primary == "anthropic":
            return _call_anthropic(system_prompt, user_prompt, model=model, max_tokens=max_tokens)
        return _call_openai(system_prompt, user_prompt, max_tokens=max_tokens)
    except Exception as e:
        logger.warning(f"Provedor primário ({primary}) falhou: {e}. Tentando fallback...")

    try:
        if primary == "anthropic":
            return _call_openai(system_prompt, user_prompt, max_tokens=max_tokens)
        return _call_anthropic(system_prompt, user_prompt, model=model, max_tokens=max_tokens)
    except Exception as e:
        logger.error(f"Ambos os provedores falharam: {e}")
        raise RuntimeError(f"Falha em ambos os provedores de IA: {e}")
