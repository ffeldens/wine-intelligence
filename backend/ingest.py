"""Ingestão do catálogo TDP: planilha → enriquecimento (LLM) → embedding → DB.

Uso (na VPS, dentro do container):
    docker exec -it wine-backend python ingest.py /app/data/catalogo.xlsx
    # opcional: --limit N (teste), --reembed (recomputa tudo)

Idempotente: upsert por SKU. Cada vinho: enrich (Haiku) + embed (OpenAI).
"""

import sys
import logging
from app.database import SessionLocal, Base, engine, ensure_pgvector
from app.models.models import Wine
from app.services.catalog_import import parse_catalog
from app.services.enrichment import enrich_wine, embed_wine

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("ingest")


def run(xlsx_path: str, limit: int | None = None, reembed: bool = False):
    ensure_pgvector()
    Base.metadata.create_all(bind=engine)

    wines = parse_catalog(xlsx_path)
    if limit:
        wines = wines[:limit]
    logger.info(f"{len(wines)} vinhos para ingerir")

    db = SessionLocal()
    ok, fail = 0, 0
    try:
        for i, w in enumerate(wines, 1):
            try:
                existing = db.query(Wine).filter(Wine.sku == w["sku"]).first()
                if existing and existing.embedding is not None and not reembed:
                    continue  # já ingerido

                enriched = enrich_wine(w)
                emb = embed_wine(w, enriched)

                obj = existing or Wine(sku=w["sku"])
                obj.nome = enriched.get("nome") or w["descricao_raw"]
                obj.produtor = w.get("produtor")
                obj.importadora = "TDP Wines"
                obj.regiao = w.get("regiao")
                obj.pais = w.get("pais")
                obj.safra = w.get("safra")
                obj.preco = w.get("preco")
                obj.tipo = enriched.get("tipo")
                obj.cor = enriched.get("cor")
                obj.uva = enriched.get("uva")
                obj.descricao = enriched.get("descricao_rica")
                obj.notas = f"Classificação TDP: {w.get('classificacao','')} · Cód.barras: {w.get('codigo_barras','')} · {w.get('embalagem','')}x{w.get('volume','')}"
                obj.estoque = 1  # planilha não traz estoque real; assume disponível
                obj.sensory_profile = enriched.get("sensory_profile")
                obj.embedding = emb

                if not existing:
                    db.add(obj)
                db.commit()
                ok += 1
                if i % 20 == 0:
                    logger.info(f"{i}/{len(wines)}…")
            except Exception as e:
                db.rollback()
                fail += 1
                logger.warning(f"Falha no SKU {w.get('sku')}: {e}")
        logger.info(f"OK · ingeridos/atualizados: {ok} · falhas: {fail} · total no catálogo: {db.query(Wine).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("uso: python ingest.py <caminho.xlsx> [--limit N] [--reembed]")
        raise SystemExit(1)
    path = sys.argv[1]
    lim = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    run(path, limit=lim, reembed="--reembed" in sys.argv)
