"""Inferência do perfil sensorial do usuário a partir de preferências livres.

Claude (Sonnet 5) lê as preferências + favoritos e produz:
  - um perfil sensorial (8 eixos 0-10),
  - a descrição do "vinho ideal" (na mesma linguagem do embedding dos vinhos),
  - dicas estruturadas (tipos/regiões/uvas preferidas, o que evitar),
  - uma inferência de estilo (ex.: "70% perfil Chablis / 30% Meursault").

A descrição do vinho ideal é embeddada (OpenAI) → vetor do usuário, comparado
por similaridade (pgvector) contra os embeddings dos vinhos do catálogo.
"""

import logging
from app.services.ai_provider import generate_with_fallback
from app.services.embeddings import embed_text
from app.services.json_utils import parse_llm_json
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_EIXOS = ["acidez", "corpo", "mineralidade", "madeira", "fruta",
          "persistencia", "complexidade", "guarda"]

_SYSTEM = """Você é um sommelier especialista. A partir das preferências livres de
um cliente (e vinhos favoritos, se houver), infira o PERFIL SENSORIAL do paladar
dele e descreva o vinho ideal. Baseie-se em enologia real (ex.: "Chablis" → alta
acidez, mineralidade calcária, madeira baixa, Chardonnay de clima frio; "Barolo"
→ tânico, alta guarda, Nebbiolo). Responda SOMENTE com JSON válido, sem markdown."""


def _prompt(preferencias: str, favoritos: list[str]) -> str:
    fav = f"\nVinhos/rótulos favoritos: {', '.join(favoritos)}" if favoritos else ""
    return f"""Preferências do cliente: {preferencias}{fav}

Retorne este JSON EXATO:
{{
  "resumo": "1-2 frases descrevendo o paladar do cliente",
  "inferencia": "aproximação de estilo, ex.: '70% perfil Chablis / 30% Meursault'",
  "vinho_ideal": "descrição rica do vinho ideal (uva, tipo, região, notas, estilo) — usada p/ busca por similaridade",
  "tipos_preferidos": ["branco", "espumante"],
  "regioes_ou_uvas": ["Chardonnay", "Borgonha", "clima frio"],
  "evitar": ["muito amadeirado", "tânico pesado"],
  "sensory_profile": {{
    "acidez": 0-10, "corpo": 0-10, "mineralidade": 0-10, "madeira": 0-10,
    "fruta": 0-10, "persistencia": 0-10, "complexidade": 0-10, "guarda": 0-10
  }}
}}
Apenas o JSON."""


def infer_profile_from_llm(system: str, prompt: str, fallback_ideal: str) -> dict:
    """Núcleo reutilizável: chama o LLM (2 tentativas, temp 0, parse tolerante),
    normaliza o perfil sensorial e gera o embedding do vinho ideal. Usado tanto
    pelo perfil do usuário quanto pela harmonização por prato."""
    data, last_err = None, None
    for tentativa in range(2):  # JSON do LLM é não-determinístico → 2 chances
        resp = generate_with_fallback(
            system, prompt, model=settings.ai_model_anthropic,
            max_tokens=900, temperature=0,
        )
        try:
            data = parse_llm_json(resp.content)
            break
        except ValueError as e:
            last_err = e
            logger.warning(f"Perfil: JSON inválido (tentativa {tentativa + 1}): {e}")
    if data is None:
        raise ValueError(f"Não consegui inferir o perfil (JSON inválido do LLM): {last_err}")

    prof = data.get("sensory_profile", {}) or {}
    data["sensory_profile"] = {
        k: max(0.0, min(10.0, float(prof.get(k, 5) or 5))) for k in _EIXOS
    }
    ideal = data.get("vinho_ideal") or fallback_ideal
    perfil_txt = ", ".join(f"{k} {v}" for k, v in data["sensory_profile"].items())
    # Mesmo formato do embedding_text dos vinhos → espaço vetorial coerente
    data["embedding"] = embed_text(f"{ideal}. Perfil sensorial (0-10): {perfil_txt}.")
    return data


def infer_user_profile(preferencias: str, favoritos: list[str] | None = None) -> dict:
    """Infere o perfil do cliente e o vetor de similaridade (embedding)."""
    return infer_profile_from_llm(_SYSTEM, _prompt(preferencias, favoritos or []), preferencias)
