"""Rotas de recomendação (F2) + browse do catálogo."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Wine
from app.services.recommender import recommend, _wine_pub

router = APIRouter()


class RecommendRequest(BaseModel):
    preferencias: str = Field(..., description="Preferências livres do cliente (obrigatório)")
    favoritos: list[str] | None = Field(None, description="Rótulos favoritos, se houver")
    tipo: str | None = Field(None, description="Filtro: tinto|branco|rosé|espumante...")
    pais: str | None = Field(None, description="Filtro por país")
    orcamento: float | None = Field(None, description="Teto de preço por garrafa (R$)")
    qtd: int = Field(3, ge=1, le=12, description="Quantidade de indicações")
    objetivo: str | None = Field(None, description="descoberta|presente|guarda|consumo_diario")


@router.post("/recommend")
def post_recommend(req: RecommendRequest, db: Session = Depends(get_db)):
    """Motor de descoberta: perfil inferido + seleção rankeada com justificativa."""
    return recommend(
        db, preferencias=req.preferencias, favoritos=req.favoritos,
        tipo=req.tipo, pais=req.pais, orcamento=req.orcamento,
        qtd=req.qtd, objetivo=req.objetivo,
    )


@router.get("/wines")
def list_wines(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    tipo: str | None = None,
    pais: str | None = None,
):
    """Lista o catálogo (para o frontend e testes)."""
    q = select(Wine).where(Wine.embedding.isnot(None))
    if tipo:
        q = q.where(func.lower(Wine.tipo) == tipo.lower())
    if pais:
        q = q.where(func.lower(Wine.pais) == pais.lower())
    q = q.order_by(Wine.preco.desc()).limit(limit)
    wines = db.execute(q).scalars().all()
    return {"total": len(wines), "wines": [_wine_pub(w) for w in wines]}


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    """Resumo do catálogo ingerido."""
    total = db.execute(select(func.count(Wine.id))).scalar()
    com_emb = db.execute(
        select(func.count(Wine.id)).where(Wine.embedding.isnot(None))
    ).scalar()
    por_pais = db.execute(
        select(Wine.pais, func.count(Wine.id)).group_by(Wine.pais).order_by(func.count(Wine.id).desc())
    ).all()
    return {
        "total": total,
        "com_embedding": com_emb,
        "por_pais": {p or "?": n for p, n in por_pais},
    }
