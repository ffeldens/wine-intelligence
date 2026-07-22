"""Modelos do banco — catálogo de vinhos com perfil sensorial + embedding."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from app.database import Base
from app.config import get_settings

settings = get_settings()


class Wine(Base):
    """Um rótulo do catálogo da TDP.

    Campos do PRD + derivados no ingest (via LLM/embeddings):
      - sensory_profile: JSON {acidez, corpo, mineralidade, madeira, fruta,
        persistencia, complexidade, guarda} em escala 0-10.
      - embedding: vetor da descrição + perfil (busca de similaridade).
    """
    __tablename__ = "wines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Campos vindos da planilha (fonte)
    sku = Column(String(120), index=True)
    nome = Column(String(400), nullable=False)
    produtor = Column(String(300))
    importadora = Column(String(300))
    regiao = Column(String(200), index=True)
    pais = Column(String(120), index=True)
    safra = Column(String(20))
    preco = Column(Float, index=True)
    tipo = Column(String(80), index=True)   # tinto, branco, espumante, rosé...
    cor = Column(String(80))
    uva = Column(String(300))
    descricao = Column(Text)
    notas = Column(Text)
    estoque = Column(Integer, default=0)
    imagem = Column(String(1000))
    link = Column(String(1000))

    # Derivados (ingest)
    sensory_profile = Column(JSONB)
    embedding = Column(Vector(settings.embedding_dim))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
