"""Motor de recomendação híbrido (F2).

Etapas (PRD):
  1. Filtro estruturado (SQL): tipo, país, orçamento, estoque > 0.
  2. Similaridade sensorial (pgvector): perfil do usuário × embedding dos vinhos.
  3. Score híbrido: 40% sensorial · 25% produtor · 15% custo-benefício ·
     10% adequação ao orçamento · 10% diversidade.
  4. Seleção gulosa top-N (a diversidade recalcula a cada escolha) + justificativa
     do sommelier (LLM) ancorada nos dados reais do vinho.
"""

import json
import re
import math
import logging
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.models import Wine
from app.services.profile import infer_user_profile
from app.services.ai_provider import generate_with_fallback
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Pesos do score (algoritmo do PRD)
W_SENSORIAL, W_PRODUTOR, W_CUSTO, W_ORCAMENTO, W_DIVERSIDADE = 0.40, 0.25, 0.15, 0.10, 0.10
CANDIDATOS = 40  # top-K por similaridade que entram no ranqueamento fino

_EIXOS = ["acidez", "corpo", "mineralidade", "madeira", "fruta",
          "persistencia", "complexidade", "guarda"]
_MAX_DIST = math.sqrt(len(_EIXOS) * 100)  # distância euclidiana máxima nos 8 eixos (0-10)


def _axis_sim(user_prof: dict | None, wine_prof: dict | None) -> float | None:
    """Similaridade direta entre os 8 eixos sensoriais (0..1). Faz a aversão a
    um eixo específico (ex.: madeira) morder o score, além do embedding."""
    if not user_prof or not wine_prof:
        return None
    d2 = sum((float(user_prof.get(k, 5)) - float(wine_prof.get(k, 5))) ** 2 for k in _EIXOS)
    return max(0.0, 1.0 - math.sqrt(d2) / _MAX_DIST)


def _producer_quality(w: Wine) -> float:
    """0..1 a partir das pontuações (James Suckling/Decanter). Sem rating → neutro."""
    nums = [int(n) for n in re.findall(r"\b(8\d|9\d|100)\b", w.pontuacoes or "")]
    if nums:
        return max(0.0, min(1.0, (max(nums) - 85) / 12))  # 85→0 · 97+→1
    return 0.55  # sem nota crítica: levemente abaixo do neutro


def _cost_benefit(sensorial: float, preco: float | None, preco_medio: float) -> float:
    """Valor sensorial por real, normalizado em torno do preço médio do conjunto."""
    if not preco or preco <= 0:
        return 0.5
    ratio = preco / preco_medio
    return max(0.0, min(1.0, sensorial / max(0.4, ratio)))


def _budget_fit(preco: float | None, orcamento: float | None) -> float:
    if not orcamento:
        return 0.7  # sem orçamento declarado → neutro-positivo
    if not preco:
        return 0.5
    if preco <= orcamento:
        return 1.0
    return max(0.0, 1.0 - (preco - orcamento) / orcamento)  # 100% acima → 0


def _perfil_pub(p: dict) -> dict:
    return {
        "resumo": p.get("resumo"),
        "inferencia": p.get("inferencia"),
        "sensory_profile": p.get("sensory_profile"),
        "tipos_preferidos": p.get("tipos_preferidos"),
        "regioes_ou_uvas": p.get("regioes_ou_uvas"),
        "evitar": p.get("evitar"),
    }


def _wine_pub(w: Wine) -> dict:
    return {
        "id": str(w.id), "sku": w.sku, "nome": w.nome, "produtor": w.produtor,
        "regiao": w.regiao, "pais": w.pais, "safra": w.safra, "preco": w.preco,
        "tipo": w.tipo, "cor": w.cor, "uva": w.uva, "descricao": w.descricao,
        "harmonizacao": w.harmonizacao, "pontuacoes": w.pontuacoes,
        "sensory_profile": w.sensory_profile,
    }


def _item_pub(c: dict) -> dict:
    return {
        "wine": _wine_pub(c["wine"]),
        "compatibilidade": round(c["sensorial"] * 100),
        "score": round(c["score"], 4),
        "componentes": {
            "sensorial": round(c["sensorial"], 3),
            "produtor": round(c["produtor"], 3),
            "custo_beneficio": round(c["custo"], 3),
            "orcamento": round(c["orcamento"], 3),
            "diversidade": round(c.get("diversidade", 1.0), 3),
        },
    }


def _justify(perfil: dict, itens: list[dict]) -> None:
    """Preenche it['justificativa'] com a fala do sommelier (grounded)."""
    if not itens:
        return
    linhas = "\n".join(
        f"[{i+1}] {it['wine']['nome']} · {it['wine']['uva']} · {it['wine']['tipo']} · "
        f"{it['wine']['regiao']}/{it['wine']['pais']} · R$ {it['wine']['preco']} · "
        f"compat {it['compatibilidade']}% · notas: {(it['wine']['descricao'] or '')[:240]} · "
        f"harmoniza: {(it['wine']['harmonizacao'] or '')[:160]} · rating: {it['wine']['pontuacoes'] or '-'}"
        for i, it in enumerate(itens)
    )
    n = len(itens)
    system = (
        "Você é o sommelier da TDP Wines. Justifique cada indicação em 1-2 frases, "
        "conectando o vinho ao paladar do cliente. Use SOMENTE os dados fornecidos "
        "(não invente notas nem prêmios). Responda em JSON com UMA chave por índice, "
        "de \"1\" a \"" + str(n) + "\", sem pular nenhuma."
    )
    user = (
        f"Perfil do cliente: {perfil.get('resumo')} ({perfil.get('inferencia')}).\n"
        f"Vinhos selecionados (justifique TODOS os {n}):\n{linhas}\n\nRetorne só o JSON."
    )
    try:
        resp = generate_with_fallback(system, user, model=settings.ai_model_anthropic, max_tokens=1500)
        m = re.search(r"\{.*\}", resp.content, re.S)
        just = json.loads(m.group(0)) if m else {}
        for i, it in enumerate(itens):
            it["justificativa"] = just.get(str(i + 1), "")
    except Exception as e:
        logger.warning(f"Falha ao gerar justificativas: {e}")
        for it in itens:
            it.setdefault("justificativa", "")


def _descobertas(leftovers: list[dict], perfil: dict, k: int = 2) -> list[dict]:
    """Rótulos que o cliente NÃO citou (país/uva fora do radar) mas casam com o
    paladar — o diferencial "descoberta inteligente" do PRD."""
    mencionado = (" ".join(perfil.get("regioes_ou_uvas") or [])).lower()
    cand: list[tuple[dict, str]] = []
    for c in leftovers:
        w = c["wine"]
        pais = (w.pais or "").lower()
        primeira_uva = (w.uva or "").split(",")[0].lower().strip()
        pais_novo = bool(pais) and pais not in mencionado
        uva_nova = bool(primeira_uva) and primeira_uva not in mencionado
        if pais_novo or uva_nova:
            motivo = (w.pais or "").title() if pais_novo else (w.uva or "").split(",")[0].strip()
            cand.append((c, motivo))
    cand.sort(key=lambda t: t[0]["sensorial"], reverse=True)
    return [
        {
            "wine": _wine_pub(c["wine"]),
            "compatibilidade": round(c["sensorial"] * 100),
            "motivo": f"Fora do seu radar ({motivo}), mas casa com seu paladar.",
        }
        for c, motivo in cand[:k]
    ]


def recommend(db: Session, preferencias: str, favoritos: list[str] | None = None,
              tipo: str | None = None, pais: str | None = None,
              orcamento: float | None = None, qtd: int = 3,
              objetivo: str | None = None, explicar: bool = True) -> dict:
    """Recomendação híbrida: retorna perfil inferido + seleção rankeada."""
    perfil = infer_user_profile(preferencias, favoritos)
    uvec = perfil["embedding"]
    user_prof = perfil.get("sensory_profile")

    # 1. Filtro estruturado
    dist = Wine.embedding.cosine_distance(uvec)
    q = select(Wine, dist.label("dist")).where(
        Wine.embedding.isnot(None), Wine.estoque > 0
    )
    if tipo:
        q = q.where(func.lower(Wine.tipo) == tipo.lower())
    if pais:
        q = q.where(func.lower(Wine.pais) == pais.lower())
    if orcamento:
        q = q.where(Wine.preco <= orcamento * 1.25)  # margem p/ upsell próximo

    # 2. Similaridade sensorial (pgvector) — top-K candidatos
    q = q.order_by(dist).limit(CANDIDATOS)
    rows = db.execute(q).all()
    if not rows:
        return {"perfil_usuario": _perfil_pub(perfil), "selecao": [],
                "aviso": "Nenhum vinho do catálogo casou com o filtro. Afrouxe o orçamento/tipo."}

    precos = [r[0].preco for r in rows if r[0].preco]
    preco_medio = sum(precos) / len(precos) if precos else 100.0

    scored = []
    for wine, dist_val in rows:
        emb_sim = max(0.0, min(1.0, 1.0 - float(dist_val)))  # cosine dist → similaridade
        ax = _axis_sim(user_prof, wine.sensory_profile)
        # embedding (semântico) + eixos sensoriais (crava aversões, ex.: madeira)
        sensorial = emb_sim if ax is None else 0.6 * emb_sim + 0.4 * ax
        produtor = _producer_quality(wine)
        custo = _cost_benefit(sensorial, wine.preco, preco_medio)
        orc = _budget_fit(wine.preco, orcamento)
        base = (W_SENSORIAL * sensorial + W_PRODUTOR * produtor
                + W_CUSTO * custo + W_ORCAMENTO * orc)
        scored.append({"wine": wine, "sensorial": sensorial, "produtor": produtor,
                       "custo": custo, "orcamento": orc, "base": base})

    # 3. Seleção gulosa: a diversidade recompensa variar país/tipo/uva já escolhidos
    selecionados: list[dict] = []
    usados = {"pais": set(), "tipo": set(), "uva": set()}
    while scored and len(selecionados) < qtd:
        for c in scored:
            w = c["wine"]
            div = 1.0
            if w.pais in usados["pais"]:
                div -= 0.4
            if w.tipo in usados["tipo"]:
                div -= 0.3
            if (w.uva or "") in usados["uva"]:
                div -= 0.3
            c["diversidade"] = max(0.0, div)
            c["score"] = c["base"] + W_DIVERSIDADE * c["diversidade"]
        scored.sort(key=lambda c: c["score"], reverse=True)
        best = scored.pop(0)
        selecionados.append(best)
        w = best["wine"]
        usados["pais"].add(w.pais)
        usados["tipo"].add(w.tipo)
        usados["uva"].add(w.uva or "")

    itens = [_item_pub(c) for c in selecionados]
    if explicar:
        _justify(perfil, itens)

    return {
        "perfil_usuario": _perfil_pub(perfil),
        "selecao": itens,
        "descobertas": _descobertas(scored, perfil),  # scored = candidatos não escolhidos
    }
