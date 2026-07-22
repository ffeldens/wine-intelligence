# Wine Intelligence — Sommelier IA (TDP Wines)

Sommelier virtual AI-native: entende o paladar da pessoa, o objetivo da compra e
as restrições comerciais para montar uma seleção personalizada usando **exclusivamente
o catálogo da TDP Wines**. Recomendação híbrida: filtro estruturado → similaridade
vetorial (pgvector) → LLM interpreta preferências e justifica.

## Stack

- **Backend:** FastAPI (Python 3.12)
- **Banco:** PostgreSQL + **pgvector** (Docker)
- **IA:** Claude Sonnet 5 (primário) + OpenAI gpt-4o (fallback) — via `app/services/ai_provider.py`
- **Embeddings:** OpenAI `text-embedding-3-small`
- **Frontend:** Vite + React + Tailwind (F4)
- Padrão herdado do `salesclub-intel`; deploy Docker na VPS (subdomínio `sommelier.mudacao.com.br`).

## Arquitetura da recomendação (PRD)

1. **Filtrar** (SQL): tipo, faixa de preço, estoque, objetivo.
2. **Rankear:** perfil sensorial do usuário (LLM) → embedding → similaridade pgvector →
   score 40% sensorial · 25% produtor · 15% custo-benefício · 10% orçamento · 10% diversidade.
3. **LLM explica:** justifica, compara, alternativas e "descobertas inteligentes".

## Rodar local

```bash
cp backend/.env.example backend/.env   # preencher ANTHROPIC/OPENAI keys
DB_PASSWORD=uma_senha docker compose up -d --build
curl http://localhost:8002/api/health
```

## Status (MVP faseado)

- [x] **F0 — Fundação:** scaffold FastAPI + Postgres/pgvector + ai_provider + embeddings + modelo `Wine`.
- [ ] **F1 — Ingestão:** planilha TDP → `wines` + perfil sensorial (LLM) + embeddings.
- [ ] **F2 — Motor:** perfil do usuário → similaridade → score híbrido.
- [ ] **F3 — Explicabilidade + descobertas** + adega pessoal.
- [ ] **F4 — Frontend** (wizard + resultados + radar).
- [ ] **F5 — Deploy** (VPS + Caddy).

Escopo do MVP: **single-tenant TDP**, casos **Descoberta + Adega pessoal**.
