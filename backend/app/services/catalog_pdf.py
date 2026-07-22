"""Extrai as fichas ricas do catálogo PDF da TDP e as indexa por SKU.

Cada rótulo no PDF traz o mesmo código (SKU) do xlsx + descrição real, uva,
tipo, local, amadurecimento, harmonização e pontuações. Casamos por SKU:
preço/safra vêm do xlsx; a ficha rica vem daqui (grounding do enrichment).
"""

import re
import logging

logger = logging.getLogger(__name__)

_SKU_RE = re.compile(r"\b(\d{6})\b")


def extract_pdf_text(pdf_path: str) -> str:
    import pypdf

    reader = pypdf.PdfReader(pdf_path)
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def build_sku_blocks(full_text: str) -> dict[str, str]:
    """Mapeia cada SKU (6 dígitos) ao seu bloco de texto (até o próximo SKU)."""
    matches = list(_SKU_RE.finditer(full_text))
    blocks: dict[str, str] = {}
    for i, m in enumerate(matches):
        sku = m.group(1)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else min(start + 1200, len(full_text))
        block = full_text[start:end].strip()
        # mantém o bloco mais informativo se o SKU se repetir
        if sku not in blocks or len(block) > len(blocks[sku]):
            blocks[sku] = block[:1600]
    logger.info(f"PDF: {len(blocks)} blocos por SKU extraídos")
    return blocks


def load_pdf_index(pdf_path: str) -> dict[str, str]:
    """Conveniência: extrai texto + indexa por SKU."""
    return build_sku_blocks(extract_pdf_text(pdf_path))
