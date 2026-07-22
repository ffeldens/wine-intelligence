"""Enriquecimento de cada vinho via LLM.

Quando há a FICHA REAL do catálogo PDF (casada por SKU), o LLM EXTRAI dela
(uva, tipo, harmonização, notas, pontuações) e ancora o perfil sensorial nas
notas reais de degustação. Sem ficha, infere da descrição codificada do xlsx.

Modelo barato (Haiku) para rodar nos 161 vinhos com baixo custo.
"""

import logging
from app.services.ai_provider import generate_with_fallback
from app.services.embeddings import embed_text
from app.services.json_utils import parse_llm_json
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_SYSTEM = """Você é enólogo e sommelier. Recebe um vinho da TDP Wines. Se houver
FICHA DO CATÁLOGO, EXTRAIA dela os dados reais (uva, tipo, harmonização, notas,
pontuações) — não invente. Ancore o PERFIL SENSORIAL (0-10) nas notas reais de
degustação. Sem ficha, infira da descrição codificada (TTO=tinto, BCO=branco,
ESPUMANTE). Responda SOMENTE com JSON válido, sem markdown."""


def _build_prompt(w: dict, pdf_block: str | None) -> str:
    ficha = f"\n\nFICHA DO CATÁLOGO (fonte real — extraia daqui):\n\"\"\"\n{pdf_block}\n\"\"\"" if pdf_block else ""
    return f"""Vinho (tabela de preços):
- Descrição (código): {w.get('descricao_raw','')}
- Produtor: {w.get('produtor','')} | Região: {w.get('regiao','')} | País: {w.get('pais','')}
- Classificação TDP: {w.get('classificacao','')} | Safra: {w.get('safra','')} | Preço: R$ {w.get('preco','')}{ficha}

Retorne este JSON EXATO:
{{
  "nome": "nome legível do vinho (limpo, sem 6x750ML)",
  "uva": "uva(s) principal(is), com % se houver na ficha",
  "tipo": "tinto|branco|rosé|espumante|fortificado|sobremesa",
  "cor": "cor/estilo curto",
  "descricao_rica": "2-3 frases da ficha real (perfil, notas). Se não houver ficha, descreva com honestidade.",
  "harmonizacao": "harmonizações (da ficha; senão vazio)",
  "pontuacoes": "pontuações/críticos se houver na ficha (ex.: 93 James Suckling); senão vazio",
  "sensory_profile": {{
    "acidez": 0-10, "corpo": 0-10, "mineralidade": 0-10, "madeira": 0-10,
    "fruta": 0-10, "persistencia": 0-10, "complexidade": 0-10, "guarda": 0-10
  }}
}}
Perfil ancorado nas notas reais (ou na typicidade da uva/região). Apenas o JSON."""


def enrich_wine(w: dict, pdf_block: str | None = None) -> dict:
    resp = generate_with_fallback(
        _SYSTEM, _build_prompt(w, pdf_block),
        model=settings.ai_model_anthropic_cheap, max_tokens=900, temperature=0,
    )
    data = parse_llm_json(resp.content)
    prof = data.get("sensory_profile", {}) or {}
    eixos = ["acidez", "corpo", "mineralidade", "madeira", "fruta",
             "persistencia", "complexidade", "guarda"]
    data["sensory_profile"] = {
        k: max(0, min(10, float(prof.get(k, 5) or 5))) for k in eixos
    }
    # harmonizacao/pontuacoes podem vir como lista/dict → normaliza p/ string
    def _to_str(v) -> str:
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        if isinstance(v, dict):
            return "; ".join(f"{k}: {vv}" for k, vv in v.items())
        return str(v) if v is not None else ""

    data["harmonizacao"] = _to_str(data.get("harmonizacao"))
    data["pontuacoes"] = _to_str(data.get("pontuacoes"))[:500]
    return data


def embedding_text(w: dict, enriched: dict) -> str:
    p = enriched.get("sensory_profile", {})
    perfil = ", ".join(f"{k} {v}" for k, v in p.items())
    return (
        f"{enriched.get('nome','')}. Uva: {enriched.get('uva','')}. "
        f"Tipo: {enriched.get('tipo','')}. Região: {w.get('regiao','')}, {w.get('pais','')}. "
        f"Produtor: {w.get('produtor','')}. {enriched.get('descricao_rica','')} "
        f"Harmonização: {enriched.get('harmonizacao','')}. "
        f"Perfil sensorial (0-10): {perfil}."
    )


def embed_wine(w: dict, enriched: dict) -> list[float]:
    return embed_text(embedding_text(w, enriched))
