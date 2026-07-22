"""Parsing tolerante de JSON vindo de LLM.

Corrige os erros mais comuns que quebram json.loads: cercas markdown (```json),
comentários, vírgula final e ranges tipo `0-10` que o modelo às vezes copia do
template em vez de escolher um número.
"""

import json
import re


def _sanitize(s: str) -> str:
    s = re.sub(r"//[^\n]*", "", s)                 # comentários de linha
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)     # comentários de bloco
    s = re.sub(r":\s*(\d+)\s*-\s*\d+", r": \1", s)  # "x": 0-10 → "x": 0
    s = re.sub(r",(\s*[}\]])", r"\1", s)            # vírgula final antes de } ou ]
    return s


def parse_llm_json(content: str) -> dict:
    """Extrai e faz o parse do primeiro objeto JSON do texto. Levanta ValueError
    se nem a versão saneada for válida (o chamador pode então re-tentar o LLM)."""
    s = (content or "").strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*", "", s).strip()
        s = re.sub(r"```$", "", s).strip()
    m = re.search(r"\{.*\}", s, re.S)
    if m:
        s = m.group(0)
    for candidate in (s, _sanitize(s)):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError("Resposta do LLM não é JSON válido")
