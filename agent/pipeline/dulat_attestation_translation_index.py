"""Reference-level DULAT attestation translations for conservative tie-breaking."""

from __future__ import annotations

import json
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
class QuoteTranslationEvidence:
    article: str
    translation: str


@dataclass(frozen=True)
class DulatAttestationTranslationIndex:
    """Translations keyed by DULAT lemma/homonym plus reference."""

    translations_by_key_ref: Dict[Tuple[str, str, str], tuple[str, ...]] = field(
        default_factory=dict
    )
    translations_by_surface_ref: Dict[Tuple[str, str], tuple[str, ...]] = field(
        default_factory=dict
    )
    evidence_by_key_ref: Dict[Tuple[str, str, str], tuple[QuoteTranslationEvidence, ...]] = field(
        default_factory=dict
    )
    evidence_by_surface_ref: Dict[Tuple[str, str], tuple[QuoteTranslationEvidence, ...]] = field(
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
        evidence_by_key_ref: Dict[Tuple[str, str, str], list[QuoteTranslationEvidence]] = {}
        evidence_by_surface_ref: Dict[Tuple[str, str], list[QuoteTranslationEvidence]] = {}
        sense_definitions_by_entry_ref: Dict[Tuple[int, str], list[str]] = {}
        sense_definitions_by_entry_ref_stem: Dict[Tuple[int, str, str], list[str]] = {}
        conn = sqlite3.connect(dulat_db)
        try:
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(attestations)")
            attestation_columns = {row[1] for row in cur.fetchall()}
            cur.execute("PRAGMA table_info(entries)")
            entry_columns = {row[1] for row in cur.fetchall()}
            has_sense_definition = "sense_definition" in attestation_columns
            has_stem_name = "stem_name" in attestation_columns
            has_ug = "ug" in attestation_columns
            has_entry_data = "data" in entry_columns
            cur.execute(
                """
                SELECT
                  e.lemma,
                  COALESCE(e.homonym, ''),
                  e.lemma,
                  COALESCE(e.homonym, ''),
                  a.translation,
                  a.citation
                FROM entries e
                JOIN attestations a ON a.entry_id = e.entry_id
                WHERE a.translation IS NOT NULL AND TRIM(a.translation) != ''
                """
            )
            for (
                lemma_raw,
                hom_raw,
                article_lemma_raw,
                article_hom_raw,
                translation_raw,
                citation_raw,
            ) in cur.fetchall():
                lemma = normalize_lemma(lemma_raw or "")
                if not lemma:
                    continue
                homonym = (hom_raw or "").strip()
                translation = (translation_raw or "").strip()
                if not translation:
                    continue
                evidence = QuoteTranslationEvidence(
                    article=_entry_label(article_lemma_raw or "", article_hom_raw or ""),
                    translation=translation,
                )
                for ref_key in _reference_keys(citation_raw or ""):
                    key = (lemma, homonym, ref_key)
                    bucket = translations_by_key_ref.setdefault(key, [])
                    if translation not in bucket:
                        bucket.append(translation)
                    evidence_bucket = evidence_by_key_ref.setdefault(key, [])
                    if evidence not in evidence_bucket:
                        evidence_bucket.append(evidence)
                    for surface in _quote_surfaces(lemma_raw or ""):
                        surface_bucket = translations_by_surface_ref.setdefault(
                            (surface, ref_key), []
                        )
                        if translation not in surface_bucket:
                            surface_bucket.append(translation)
                        surface_evidence_bucket = evidence_by_surface_ref.setdefault(
                            (surface, ref_key), []
                        )
                        if evidence not in surface_evidence_bucket:
                            surface_evidence_bucket.append(evidence)

            if has_ug:
                cur.execute(
                    """
                    SELECT
                      e.lemma,
                      COALESCE(e.homonym, ''),
                      a.ug,
                      a.translation,
                      a.citation
                    FROM attestations a
                    JOIN entries e ON e.entry_id = a.entry_id
                    WHERE a.translation IS NOT NULL
                      AND TRIM(a.translation) != ''
                      AND a.ug IS NOT NULL
                      AND TRIM(a.ug) != ''
                    """
                )
                for (
                    article_lemma_raw,
                    article_hom_raw,
                    ug_raw,
                    translation_raw,
                    citation_raw,
                ) in cur.fetchall():
                    translation = (translation_raw or "").strip()
                    if not translation:
                        continue
                    evidence = QuoteTranslationEvidence(
                        article=_entry_label(article_lemma_raw or "", article_hom_raw or ""),
                        translation=translation,
                    )
                    surfaces = _quote_surfaces(ug_raw or "")
                    if not surfaces:
                        continue
                    for ref_key in _reference_keys(citation_raw or ""):
                        for surface in surfaces:
                            bucket = translations_by_surface_ref.setdefault((surface, ref_key), [])
                            if translation not in bucket:
                                bucket.append(translation)
                            evidence_bucket = evidence_by_surface_ref.setdefault(
                                (surface, ref_key), []
                            )
                            if evidence not in evidence_bucket:
                                evidence_bucket.append(evidence)

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

            if has_entry_data:
                cur.execute(
                    """
                    SELECT entry_id, data
                    FROM entries
                    WHERE data IS NOT NULL AND TRIM(data) != ''
                    """
                )
                for entry_id_raw, data_raw in cur.fetchall():
                    try:
                        entry_id = int(entry_id_raw)
                    except (TypeError, ValueError):
                        continue
                    if not data_raw:
                        continue
                    try:
                        entry = json.loads(data_raw)
                    except (TypeError, ValueError, json.JSONDecodeError):
                        continue
                    _merge_hierarchical_sense_labels(
                        entry_id=entry_id,
                        entry=entry,
                        by_entry_ref=sense_definitions_by_entry_ref,
                        by_entry_ref_stem=sense_definitions_by_entry_ref_stem,
                    )
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
            evidence_by_key_ref={key: tuple(values) for key, values in evidence_by_key_ref.items()},
            evidence_by_surface_ref={
                key: tuple(values) for key, values in evidence_by_surface_ref.items()
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
        return tuple(
            evidence.translation
            for evidence in self.translation_evidence_for_variant_token(variant_token, section_ref)
        )

    def translation_evidence_for_variant_token(
        self,
        variant_token: str,
        section_ref: str,
    ) -> tuple[QuoteTranslationEvidence, ...]:
        lemma, homonym = parse_dulat_head_token(variant_token)
        if not lemma:
            return ()
        evidence_out: list[QuoteTranslationEvidence] = []
        for ref_key in _reference_keys(section_ref):
            values = self.evidence_by_key_ref.get((lemma, homonym, ref_key), ())
            for value in values:
                if value not in evidence_out:
                    evidence_out.append(value)
        return tuple(evidence_out)

    def translations_for_surface_at_reference(
        self,
        surface: str,
        section_ref: str,
    ) -> tuple[str, ...]:
        return tuple(
            evidence.translation
            for evidence in self.translation_evidence_for_surface_at_reference(surface, section_ref)
        )

    def translation_evidence_for_surface_at_reference(
        self,
        surface: str,
        section_ref: str,
    ) -> tuple[QuoteTranslationEvidence, ...]:
        normalized_surface = normalize_lemma(surface or "")
        if not normalized_surface:
            return ()
        evidence_out: list[QuoteTranslationEvidence] = []
        for ref_key in _reference_keys(section_ref):
            values = self.evidence_by_surface_ref.get((normalized_surface, ref_key), ())
            for value in values:
                if value not in evidence_out:
                    evidence_out.append(value)
        return tuple(evidence_out)

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


def _append_unique(bucket: list[str], value: str) -> None:
    if value and value not in bucket:
        bucket.append(value)


def _is_numeric_sense_number(value: str) -> bool:
    return bool(re.fullmatch(r"\d+", (value or "").strip()))


def _is_letter_sense_number(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z]", (value or "").strip()))


def _translation_texts(entry: dict) -> list[str]:
    out: list[str] = []
    for item in entry.get("translations_structured") or []:
        if not isinstance(item, dict):
            continue
        text = _HTML_TAG_RE.sub(" ", str(item.get("text") or ""))
        text = re.sub(r"\s+", " ", text).strip().strip(" ;,:")
        if text and text not in out:
            out.append(text)
    return out


def _preferred_top_label(
    translations: list[str],
    number: str,
    definition: str,
) -> str:
    if definition:
        return definition.strip()
    if _is_numeric_sense_number(number):
        index = int(number) - 1
        if 0 <= index < len(translations):
            return translations[index]
    if translations:
        return translations[0]
    return definition.strip()


def _format_hierarchical_sense_label(
    *,
    top_number: str,
    top_label: str,
    leaf_number: str,
    leaf_definition: str,
) -> str:
    top_clean = re.sub(r"\s+", " ", _HTML_TAG_RE.sub(" ", top_label or "")).strip(" ;,:")
    leaf_clean = re.sub(
        r"\s+",
        " ",
        _HTML_TAG_RE.sub(" ", leaf_definition or ""),
    ).strip(" ;,:")
    if _is_letter_sense_number(leaf_number) and top_clean:
        return f"{top_number}) {top_clean} {leaf_number}) {leaf_clean}".strip()
    if _is_numeric_sense_number(leaf_number):
        return f"{leaf_number}) {top_clean or leaf_clean}".strip()
    return leaf_clean or top_clean


def _merge_hierarchical_sense_labels(
    *,
    entry_id: int,
    entry: dict,
    by_entry_ref: Dict[Tuple[int, str], list[str]],
    by_entry_ref_stem: Dict[Tuple[int, str, str], list[str]],
) -> None:
    translations = _translation_texts(entry)
    for stem in entry.get("stems_structured") or []:
        if not isinstance(stem, dict):
            continue
        stem_name = _normalize_stem_name(stem.get("name", "") or "")
        active_top_number = ""
        active_top_label = ""
        inferred_first_top_number = "1" if translations else ""
        inferred_first_top_label = translations[0] if translations else ""
        for sense in stem.get("senses") or []:
            if not isinstance(sense, dict):
                continue
            sense_number = str(sense.get("number") or "").strip()
            definition = str(sense.get("definition") or "").strip()
            if _is_numeric_sense_number(sense_number):
                active_top_number = sense_number
                active_top_label = _preferred_top_label(translations, sense_number, definition)
            elif not active_top_number and inferred_first_top_number:
                active_top_number = inferred_first_top_number
                active_top_label = inferred_first_top_label

            full_label = _format_hierarchical_sense_label(
                top_number=active_top_number or inferred_first_top_number,
                top_label=active_top_label or inferred_first_top_label,
                leaf_number=sense_number,
                leaf_definition=definition,
            )
            if not full_label:
                continue

            for example in sense.get("examples") or []:
                if not isinstance(example, dict):
                    continue
                citation = str(example.get("citation") or "").strip()
                if not citation:
                    continue
                for ref_key in _reference_keys(citation):
                    ref_bucket = by_entry_ref.setdefault((entry_id, ref_key), [])
                    if full_label not in ref_bucket:
                        ref_bucket.insert(0, full_label)
                    if stem_name:
                        stem_bucket = by_entry_ref_stem.setdefault(
                            (entry_id, ref_key, stem_name), []
                        )
                        if full_label not in stem_bucket:
                            stem_bucket.insert(0, full_label)


def _entry_label(lemma_raw: str, homonym_raw: str) -> str:
    lemma = (lemma_raw or "").strip()
    homonym = (homonym_raw or "").strip()
    if not lemma:
        return ""
    if homonym:
        return f"{lemma} ({homonym})"
    return lemma


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
