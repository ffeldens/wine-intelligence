"""Adega pessoal (F3): monta N garrafas distribuídas por objetivo, dentro do
orçamento TOTAL, só com o catálogo da TDP.

Mix do PRD: 40% consumo diário · 30% ocasiões · 20% guarda · 10% experimentação.
Cada bucket ranqueia o pool com um critério próprio; a seleção é gulosa e respeita
o orçamento total (subtotal acumulado nunca ultrapassa o teto).
"""

import logging
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.models import Wine
from app.services.profile import infer_user_profile
from app.services.recommender import (
    _producer_quality, _cost_benefit, _axis_sim, _wine_pub, _perfil_pub, ascii_upper,
)

logger = logging.getLogger(__name__)

# (chave, fração, rótulo público)
MIX = [
    ("consumo_diario", 0.40, "Consumo diário"),
    ("ocasioes", 0.30, "Ocasiões especiais"),
    ("guarda", 0.20, "Guarda"),
    ("experimentacao", 0.10, "Experimentação"),
]


def _allocate(n: int) -> dict[str, int]:
    """Distribui n garrafas pelo mix; sobras vão pros maiores pesos, em ordem."""
    counts = {k: int(n * frac) for k, frac, _ in MIX}
    i = 0
    while sum(counts.values()) < n:
        counts[MIX[i % len(MIX)][0]] += 1
        i += 1
    return counts


def _bucket_score(bucket: str, sensorial: float, produtor: float,
                  custo: float, wine: Wine) -> float:
    prof = wine.sensory_profile or {}
    guarda = float(prof.get("guarda", 5)) / 10.0
    if bucket == "consumo_diario":      # acessível, pronto pra beber
        return 0.45 * sensorial + 0.35 * custo + 0.20 * (1 - guarda)
    if bucket == "ocasioes":            # impressiona (produtor/nota)
        return 0.45 * sensorial + 0.45 * produtor + 0.10 * custo
    if bucket == "guarda":              # estrutura pra envelhecer
        return 0.45 * sensorial + 0.35 * guarda + 0.20 * produtor
    if bucket == "experimentacao":      # diverso (fora do radar, tratado na seleção)
        return 0.60 * sensorial + 0.40 * custo
    return sensorial


def build_cellar(db: Session, preferencias: str, favoritos: list[str] | None = None,
                 orcamento_total: float = 500.0, garrafas: int = 6,
                 tipo: str | None = None, pais: str | None = None) -> dict:
    perfil = infer_user_profile(preferencias, favoritos)
    uvec = perfil["embedding"]
    user_prof = perfil.get("sensory_profile")

    dist = Wine.embedding.cosine_distance(uvec)
    q = select(Wine, dist.label("dist")).where(
        Wine.embedding.isnot(None), Wine.estoque > 0, Wine.preco <= orcamento_total
    )
    if tipo:
        q = q.where(func.lower(Wine.tipo) == tipo.lower())
    if pais:
        q = q.where(func.upper(Wine.pais) == ascii_upper(pais))
    q = q.order_by(dist).limit(80)
    rows = db.execute(q).all()
    if not rows:
        return {"perfil_usuario": _perfil_pub(perfil), "adega": [],
                "aviso": "Nenhum vinho cabe no orçamento/filtro."}

    precos = [r[0].preco for r in rows if r[0].preco]
    preco_medio = sum(precos) / len(precos) if precos else 100.0

    pool = []
    for wine, dist_val in rows:
        emb = max(0.0, min(1.0, 1.0 - float(dist_val)))
        ax = _axis_sim(user_prof, wine.sensory_profile)
        sensorial = emb if ax is None else 0.6 * emb + 0.4 * ax
        pool.append({
            "wine": wine, "sensorial": sensorial,
            "produtor": _producer_quality(wine),
            "custo": _cost_benefit(sensorial, wine.preco, preco_medio),
        })

    counts = _allocate(garrafas)
    mencionado = (" ".join(perfil.get("regioes_ou_uvas") or [])).lower()
    chosen_ids: set[str] = set()
    total = 0.0
    adega = []

    def _take(cand: dict) -> None:
        nonlocal total
        w = cand["wine"]
        chosen_ids.add(str(w.id))
        total += w.preco or 0.0

    for key, _frac, label in MIX:
        need = counts[key]
        ranked = sorted(
            pool, key=lambda c: _bucket_score(key, c["sensorial"], c["produtor"], c["custo"], c["wine"]),
            reverse=True,
        )
        picks = []
        # Passe 1: para experimentação, tenta só o que está fora do radar
        for c in ranked:
            if need <= 0:
                break
            w = c["wine"]
            if str(w.id) in chosen_ids or total + (w.preco or 0) > orcamento_total:
                continue
            if key == "experimentacao":
                pais_l = (w.pais or "").lower()
                if pais_l and pais_l in mencionado:
                    continue
            _take(c)
            picks.append({"wine": _wine_pub(w), "compatibilidade": round(c["sensorial"] * 100),
                          "preco": w.preco})
            need -= 1
        # Passe 2 (fallback): completa o bucket ignorando a regra de radar
        if need > 0:
            for c in ranked:
                if need <= 0:
                    break
                w = c["wine"]
                if str(w.id) in chosen_ids or total + (w.preco or 0) > orcamento_total:
                    continue
                _take(c)
                picks.append({"wine": _wine_pub(w), "compatibilidade": round(c["sensorial"] * 100),
                              "preco": w.preco})
                need -= 1
        subtotal = round(sum(p["preco"] or 0 for p in picks), 2)
        adega.append({"objetivo": key, "titulo": label, "garrafas": picks, "subtotal": subtotal})

    return {
        "perfil_usuario": _perfil_pub(perfil),
        "orcamento_total": orcamento_total,
        "total": round(total, 2),
        "restante": round(orcamento_total - total, 2),
        "garrafas_alvo": garrafas,
        "garrafas_selecionadas": len(chosen_ids),
        "adega": adega,
    }
