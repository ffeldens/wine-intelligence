"""Wine Intelligence — API FastAPI (Sommelier IA da TDP Wines)."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import Base, engine, ensure_pgvector

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🍷 Wine Intelligence subindo...")
    # Garante pgvector + cria as tabelas (import tardio p/ registrar os modelos)
    ensure_pgvector()
    from app.models import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Banco pronto (pgvector + tabelas)")
    yield
    logger.info("Wine Intelligence encerrando.")


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": settings.app_name}


# Rotas
from app.api import recommend_routes  # noqa: E402
app.include_router(recommend_routes.router, prefix="/api")
