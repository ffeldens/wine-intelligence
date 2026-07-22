"""Enriquecimento de cada vinho via LLM: a partir da descrição codificada +
produtor/região/país/classificação, infere nome limpo, uva, tipo, cor, uma
descrição rica e o PERFIL SENSORIAL (8 eixos 0-10). Depois gera o embedding.

Modelo barato (Haiku) para rodar nos 161 vinhos com baixo custo.
"""

import json
import re
import logging
from app.services.ai_provider import generate_with_fallback
from app.services.embeddings import embed_text
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_SYSTEM = """Você é um enólogo e sommelier. Recebe um vinho vindo de uma tabela de
preços (descrição CODIFICADA, ex.: "VIN AFR MOUNTAIN VINEYARDS SAUVIGNON BLANC BCO 6x750ML").
Extraia e infira os dados estruturados. Códigos: TTO=tinto, BCO=branco, RSE/ROSE=rosé,
ESPUMANTE/ESP=espumante. NÃO invente um nome comercial pomposo — apenas limpe o código
para um nome legível. Infira uva, tipo e o PERFIL SENSORIAL a partir da uva + região +
país + produtor + classificação (typicidade). Responda SOMENTE com JSON válido, sem markdown."""


def _build_prompt(w: dict) -> str:
    return f"""Vinho:
- Descrição (codificada): {w.get('descricao_raw','')}
- Produtor: {w.get('produtor','')}
- Região: {w.get('regiao','')}
- País: {w.get('pais','')}
- Classificação comercial (TDP): {w.get('classificacao','')}
- Safra: {w.get('safra','')}
- Preço: R$ {w.get('preco','')}

Retorne este JSON EXATO:
{{
  "nome": "nome legível do vinho (limpe o código, sem 6x750ML)",
  "uva": "uva(s) principal(is)",
  "tipo": "tinto|branco|rosé|espumante|fortificado|sobremesa",
  "cor": "cor/estilo curto",
  "descricao_rica": "1-2 frases descritivas em português, honestas (perfil, ocasião)",
  "sensory_profile": {{
    "acidez": 0-10, "corpo": 0-10, "mineralidade": 0-10, "madeira": 0-10,
    "fruta": 0-10, "persistencia": 0-10, "complexidade": 0-10, "guarda": 0-10
  }}
}}
Escala 0-10 baseada na typicidade da uva/região. Apenas o JSON."""


def enrich_wine(w: dict) -> dict:
    """Retorna {nome, uva, tipo, cor, descricao_rica, sensory_profile}."""
    resp = generate_with_fallback(
        _SYSTEM, _build_prompt(w),
        model=settings.ai_model_anthropic_cheap, max_tokens=800,
    )
    content = resp.content.strip()
    m = re.search(r"\{.*\}", content, re.S)
    data = json.loads(m.group(0) if m else content)
    # normaliza o perfil (garante 8 chaves numéricas 0-10)
    prof = data.get("sensory_profile", {}) or {}
    eixos = ["acidez", "corpo", "mineralidade", "madeira", "fruta",
             "persistencia", "complexidade", "guarda"]
    data["sensory_profile"] = {
        k: max(0, min(10, float(prof.get(k, 5) or 5))) for k in eixos
    }
    return data


def embedding_text(w: dict, enriched: dict) -> str:
    """Texto que vira o embedding (para similaridade de perfil)."""
    p = enriched.get("sensory_profile", {})
    perfil = ", ".join(f"{k} {v}" for k, v in p.items())
    return (
        f"{enriched.get('nome','')}. Uva: {enriched.get('uva','')}. "
        f"Tipo: {enriched.get('tipo','')}. Região: {w.get('regiao','')}, {w.get('pais','')}. "
        f"Produtor: {w.get('produtor','')}. {enriched.get('descricao_rica','')} "
        f"Perfil sensorial (0-10): {perfil}."
    )


def embed_wine(w: dict, enriched: dict) -> list[float]:
    return embed_text(embedding_text(w, enriched))
