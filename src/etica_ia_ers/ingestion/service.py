from __future__ import annotations

import hashlib
from pathlib import Path

from etica_ia_ers.domain import Document


def build_text_document(path: str | Path, document_id: str) -> Document:
    source = Path(path)
    content = source.read_text(encoding="utf-8")
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()

    return Document(
        id=document_id,
        nombre_original=source.name,
        formato_origen=source.suffix.removeprefix(".").upper() or "TXT",
        contenido_extraido=content,
        hash_contenido=digest,
    )

