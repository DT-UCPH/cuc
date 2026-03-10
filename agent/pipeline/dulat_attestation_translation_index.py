"""Reference-level DULAT attestation translations for conservative tie-breaking."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Tuple

from pipeline.dulat_attestation_index import (
    normalize_lemma,
    normalize_reference_label,
    parse_dulat_head_token,
)

_LETTER_REF_RE = re.compile(r"^(\d+\.\d+)\s+(\d+)$")
_SINGLE_COLUMN_REF_RE = re.compile(r"^(\d+\.\d+)\s+I:(\d+)$")


def _reference_keys(reference: str) -> tuple[str, ...]:
    normalized = normalize_reference_label(reference)
    if not normalized:
        return ()
    keys = {normalized}
    letter_match = _LETTER_REF_RE.match(normalized)
    if letter_match:
        keys.add(f"{letter_match.group(1)}:{letter_match.group(2)}")
    single_column_match = _SINGLE_COLUMN_REF_RE.match(normalized)
    if single_column_match:
        keys.add(f"{single_column_match.group(1)}:{single_column_match.group(2)}")
    return tuple(sorted(keys))


@dataclass(frozen=True)
class DulatAttestationTranslationIndex:
    """Translations keyed by DULAT lemma/homonym plus reference."""

    translations_by_key_ref: Dict[Tuple[str, str, str], tuple[str, ...]] = field(
        default_factory=dict
    )

    @classmethod
    def empty(cls) -> "DulatAttestationTranslationIndex":
        return cls()

    @classmethod
    def from_sqlite(cls, dulat_db: Path) -> "DulatAttestationTranslationIndex":
        if not Path(dulat_db).exists():
            return cls.empty()

        translations_by_key_ref: Dict[Tuple[str, str, str], list[str]] = {}
        conn = sqlite3.connect(dulat_db)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                  e.lemma,
                  COALESCE(e.homonym, ''),
                  a.translation,
                  a.citation
                FROM entries e
                JOIN attestations a ON a.entry_id = e.entry_id
                WHERE a.translation IS NOT NULL AND TRIM(a.translation) != ''
                """
            )
            for lemma_raw, hom_raw, translation_raw, citation_raw in cur.fetchall():
                lemma = normalize_lemma(lemma_raw or "")
                if not lemma:
                    continue
                homonym = (hom_raw or "").strip()
                translation = (translation_raw or "").strip()
                if not translation:
                    continue
                for ref_key in _reference_keys(citation_raw or ""):
                    key = (lemma, homonym, ref_key)
                    bucket = translations_by_key_ref.setdefault(key, [])
                    if translation not in bucket:
                        bucket.append(translation)
        except sqlite3.Error:
            return cls.empty()
        finally:
            conn.close()

        return cls(
            translations_by_key_ref={
                key: tuple(values) for key, values in translations_by_key_ref.items()
            }
        )

    def translations_for_variant_token(
        self,
        variant_token: str,
        section_ref: str,
    ) -> tuple[str, ...]:
        lemma, homonym = parse_dulat_head_token(variant_token)
        if not lemma:
            return ()
        translations: list[str] = []
        for ref_key in _reference_keys(section_ref):
            values = self.translations_by_key_ref.get((lemma, homonym, ref_key), ())
            for value in values:
                if value not in translations:
                    translations.append(value)
        return tuple(translations)
