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
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_UGARITIC_QUOTE_TOKEN_RE = re.compile(r"[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]+")


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
    translations_by_surface_ref: Dict[Tuple[str, str], tuple[str, ...]] = field(
        default_factory=dict
    )
    sense_definitions_by_entry_ref: Dict[Tuple[int, str], tuple[str, ...]] = field(
        default_factory=dict
    )
    sense_definitions_by_entry_ref_stem: Dict[Tuple[int, str, str], tuple[str, ...]] = field(
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
        translations_by_surface_ref: Dict[Tuple[str, str], list[str]] = {}
        sense_definitions_by_entry_ref: Dict[Tuple[int, str], list[str]] = {}
        sense_definitions_by_entry_ref_stem: Dict[Tuple[int, str, str], list[str]] = {}
        conn = sqlite3.connect(dulat_db)
        try:
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(attestations)")
            attestation_columns = {row[1] for row in cur.fetchall()}
            has_sense_definition = "sense_definition" in attestation_columns
            has_stem_name = "stem_name" in attestation_columns
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
                    for surface in _quote_surfaces(lemma_raw or ""):
                        surface_bucket = translations_by_surface_ref.setdefault(
                            (surface, ref_key), []
                        )
                        if translation not in surface_bucket:
                            surface_bucket.append(translation)

            cur.execute(
                """
                SELECT
                  a.ug,
                  a.translation,
                  a.citation
                FROM attestations a
                WHERE a.translation IS NOT NULL
                  AND TRIM(a.translation) != ''
                  AND a.ug IS NOT NULL
                  AND TRIM(a.ug) != ''
                """
            )
            for ug_raw, translation_raw, citation_raw in cur.fetchall():
                translation = (translation_raw or "").strip()
                if not translation:
                    continue
                surfaces = _quote_surfaces(ug_raw or "")
                if not surfaces:
                    continue
                for ref_key in _reference_keys(citation_raw or ""):
                    for surface in surfaces:
                        bucket = translations_by_surface_ref.setdefault((surface, ref_key), [])
                        if translation not in bucket:
                            bucket.append(translation)

            if has_sense_definition:
                stem_expr = "a.stem_name" if has_stem_name else "''"
                cur.execute(
                    f"""
                    SELECT
                      a.entry_id,
                      a.sense_definition,
                      a.citation,
                      COALESCE({stem_expr}, '')
                    FROM attestations a
                    WHERE a.sense_definition IS NOT NULL
                      AND TRIM(a.sense_definition) != ''
                    """
                )
                for entry_id_raw, definition_raw, citation_raw, stem_name_raw in cur.fetchall():
                    try:
                        entry_id = int(entry_id_raw)
                    except (TypeError, ValueError):
                        continue
                    definition = (definition_raw or "").strip()
                    if not definition:
                        continue
                    stem_name = _normalize_stem_name(stem_name_raw or "")
                    for ref_key in _reference_keys(citation_raw or ""):
                        ref_bucket = sense_definitions_by_entry_ref.setdefault(
                            (entry_id, ref_key), []
                        )
                        if definition not in ref_bucket:
                            ref_bucket.append(definition)
                        if stem_name:
                            stem_bucket = sense_definitions_by_entry_ref_stem.setdefault(
                                (entry_id, ref_key, stem_name), []
                            )
                            if definition not in stem_bucket:
                                stem_bucket.append(definition)
        except sqlite3.Error:
            return cls.empty()
        finally:
            conn.close()

        return cls(
            translations_by_key_ref={
                key: tuple(values) for key, values in translations_by_key_ref.items()
            },
            translations_by_surface_ref={
                key: tuple(values) for key, values in translations_by_surface_ref.items()
            },
            sense_definitions_by_entry_ref={
                key: tuple(values) for key, values in sense_definitions_by_entry_ref.items()
            },
            sense_definitions_by_entry_ref_stem={
                key: tuple(values) for key, values in sense_definitions_by_entry_ref_stem.items()
            },
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

    def translations_for_surface_at_reference(
        self,
        surface: str,
        section_ref: str,
    ) -> tuple[str, ...]:
        normalized_surface = normalize_lemma(surface or "")
        if not normalized_surface:
            return ()
        translations: list[str] = []
        for ref_key in _reference_keys(section_ref):
            values = self.translations_by_surface_ref.get((normalized_surface, ref_key), ())
            for value in values:
                if value not in translations:
                    translations.append(value)
        return tuple(translations)

    def sense_definitions_for_entry(
        self,
        entry_id: int,
        section_ref: str,
        stem_name: str = "",
    ) -> tuple[str, ...]:
        ref_keys = _reference_keys(section_ref)
        if not ref_keys:
            return ()
        out: list[str] = []
        normalized_stem = _normalize_stem_name(stem_name)
        if normalized_stem:
            for stem_key in _stem_lookup_keys(normalized_stem):
                for ref_key in ref_keys:
                    values = self.sense_definitions_by_entry_ref_stem.get(
                        (int(entry_id), ref_key, stem_key), ()
                    )
                    for value in values:
                        if value not in out:
                            out.append(value)
            if out:
                return tuple(out)
        for ref_key in ref_keys:
            values = self.sense_definitions_by_entry_ref.get((int(entry_id), ref_key), ())
            for value in values:
                if value not in out:
                    out.append(value)
        return tuple(out)


def _normalize_stem_name(stem_name: str) -> str:
    return (stem_name or "").strip().rstrip(".")


def _stem_lookup_keys(stem_name: str) -> tuple[str, ...]:
    normalized = _normalize_stem_name(stem_name)
    if not normalized:
        return ()
    keys = [normalized]
    if normalized == "Dpass":
        keys.append("D")
    elif normalized == "Gpass":
        keys.append("G")
    elif normalized in {"Dt", "tD"}:
        keys.append("D")
    elif normalized in {"Gt", "tG"}:
        keys.append("G")
    return tuple(dict.fromkeys(keys))


def _quote_surfaces(text: str) -> tuple[str, ...]:
    stripped = _HTML_TAG_RE.sub(" ", text or "")
    tokens = [
        normalize_lemma(match.group(0))
        for match in _UGARITIC_QUOTE_TOKEN_RE.finditer(stripped)
    ]
    return tuple(dict.fromkeys(token for token in tokens if token))
