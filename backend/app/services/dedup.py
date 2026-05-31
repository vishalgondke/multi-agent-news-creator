"""Content de-duplication helpers."""
from __future__ import annotations

import hashlib
import re


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[^a-z0-9 ]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def content_hash(title: str, url: str) -> str:
    """Stable dedup key from normalized title + host."""
    host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
    basis = f"{normalize(title)}|{host}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()
