"""Indexes DULAT form-note metadata for refinement steps and linters."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Set, Tuple

from pipeline.config.dulat_form_text_overrides import expand_dulat_form_texts

_LOOKUP_NORMALIZE = str.maketrans(
    {
        "ʿ": "ʕ",
        "ˤ": "ʕ",
        "ả": "a",
        "ỉ": "i",
        "ủ": "u",
    }
)
_TOKEN_RE = re.compile(r"^(.*?)(?:\s*\(([IVX]+)\))?$")
_ENCLITIC_M_RE = re.compile(r"\bencl\.\s*(?:<i>)?\s*-m\b", flags=re.IGNORECASE)


@dataclass(frozen=True)
class DulatFormNoteIndex:
    """Surface-indexed DULAT form-note facts keyed by lemma/homonym."""

    enclitic_m_surfaces: Dict[Tuple[str, str], Set[str]]

    @classmethod
    def from_sqlite(cls, db_path: Path) -> "DulatFormNoteIndex":
        if not db_path.exists():
            return cls(enclitic_m_surfaces={})

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        entry_index: Dict[int, Tuple[str, str]] = {}
        for entry_id, lemma, homonym in cur.execute("SELECT entry_id, lemma, homonym FROM entries"):
            lemma_raw = (lemma or "").strip()
            hom = (homonym or "").strip()
            if lemma_raw and not hom:
                match = re.match(r"^(.*)\s+\(([IVX]+)\)$", lemma_raw)
                if match:
                    lemma_raw = match.group(1).strip()
                    hom = match.group(2)
            entry_index[int(entry_id)] = (_normalize_token(lemma_raw), hom)

        enclitic_m_surfaces: Dict[Tuple[str, str], Set[str]] = {}
        for entry_id, text, notes in cur.execute(
            "SELECT entry_id, text, notes FROM forms WHERE text IS NOT NULL AND trim(text) != ''"
        ):
            if not _has_enclitic_m(notes or ""):
                continue
            key = entry_index.get(int(entry_id))
            if not key:
                continue
            lemma_norm, hom = key
            for form_variant in expand_dulat_form_texts(
                lemma=lemma_norm,
                homonym=hom,
                form_text=text or "",
            ):
                surface = _normalize_surface(form_variant)
                if not surface:
                    continue
                enclitic_m_surfaces.setdefault((lemma_norm, hom), set()).add(surface)

        conn.close()
        return cls(enclitic_m_surfaces=enclitic_m_surfaces)

    def has_enclitic_m(self, *, surface: str, dulat_token: str) -> bool:
        lemma, hom = _parse_declared_token(dulat_token)
        if not lemma or lemma == "?":
            return False
        lemma_norm = _normalize_token(lemma)
        surface_norm = _normalize_surface(surface)
        if not lemma_norm or not surface_norm:
            return False

        if hom:
            return surface_norm in self.enclitic_m_surfaces.get((lemma_norm, hom), set())

        return any(
            key_lemma == lemma_norm and surface_norm in surfaces
            for (key_lemma, _key_hom), surfaces in self.enclitic_m_surfaces.items()
        )


def _normalize_token(value: str) -> str:
    return (value or "").strip().translate(_LOOKUP_NORMALIZE).lower()


def _normalize_surface(value: str) -> str:
    return _normalize_token(value)


def _parse_declared_token(token: str) -> tuple[str, str]:
    raw = (token or "").strip()
    if not raw:
        return "", ""
    if raw.startswith("/"):
        return raw, ""
    match = _TOKEN_RE.match(raw)
    if not match:
        return raw, ""
    lemma = (match.group(1) or "").strip()
    hom = (match.group(2) or "").strip().upper()
    return lemma, hom


def _has_enclitic_m(notes: str) -> bool:
    return bool(_ENCLITIC_M_RE.search(notes or ""))
