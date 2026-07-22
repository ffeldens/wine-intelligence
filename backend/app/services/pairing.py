"""Harmonização por prato (F5+): dado um prato, o sommelier infere o vinho ideal
para acompanhar e recomenda rótulos do catálogo que casam.

Reaproveita o motor: o prato vira um "perfil-alvo" (mesmo shape do perfil do
usuário) → similaridade pgvector → score → justificativa de harmonização.
"""

from sqlalchemy.orm import Session
from app.services.profile import infer_profile_from_llm
from app.services.recommender import recommend

_SYSTEM = """Você é sommelier especialista em harmonização. Dado um PRATO, descreva
o VINHO IDEAL para acompanhá-lo e o perfil sensorial que o prato pede. Considere
peso do prato, gordura, acidez, doçura, tempero e técnica de preparo (grelhado,
frito, cru, braseado). Responda SOMENTE com JSON válido, sem markdown."""


def _prompt(prato: str) -> str:
    return f"""Prato a harmonizar: {prato}

Retorne este JSON EXATO:
{{
  "resumo": "1-2 frases: o que o prato pede no vinho e por quê",
  "inferencia": "estilo sugerido, ex.: 'Branco mineral de boa acidez ou tinto leve e fresco'",
  "vinho_ideal": "descrição rica do vinho ideal p/ acompanhar (uva, tipo, corpo, acidez, notas) — usada p/ busca por similaridade",
  "tipos_preferidos": ["branco", "espumante"],
  "regioes_ou_uvas": ["Chardonnay", "clima frio"],
  "evitar": ["tânico pesado", "muito amadeirado"],
  "sensory_profile": {{
    "acidez": 0-10, "corpo": 0-10, "mineralidade": 0-10, "madeira": 0-10,
    "fruta": 0-10, "persistencia": 0-10, "complexidade": 0-10, "guarda": 0-10
  }}
}}
Perfil sensorial = do VINHO IDEAL para o prato. Apenas o JSON."""


def infer_dish_profile(prato: str) -> dict:
    """Perfil-alvo do vinho ideal para o prato (mesmo shape do perfil do usuário)."""
    return infer_profile_from_llm(_SYSTEM, _prompt(prato), prato)


def pair_with_dish(db: Session, prato: str, tipo: str | None = None,
                   pais: str | None = None, orcamento: float | None = None,
                   qtd: int = 3) -> dict:
    perfil = infer_dish_profile(prato)
    return recommend(
        db, preferencias=prato, perfil=perfil, tipo=tipo, pais=pais,
        orcamento=orcamento, qtd=qtd, contexto="prato",
    )
