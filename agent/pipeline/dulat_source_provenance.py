"""Provenance lookup for non-DULAT records stored in the DULAT cache."""

from __future__ import annotations

import html
import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from pipeline.dulat_attestation_index import normalize_lemma

_HOMONYM_RE = re.compile(r"^(.*?)(?:\s*\(([IV]+)\))?$")
_FIELD_SEPARATOR_RE = re.compile(r"[;,]")


def _entry_key(lemma: str, homonym: str) -> tuple[str, str]:
    return (lemma.strip(), homonym.strip())


def _normalized_entry_key(lemma: str, homonym: str) -> tuple[str, str]:
    return (normalize_lemma(lemma), homonym.strip())


def _parse_declared_entry(token: str) -> tuple[str, str]:
    value = (token or "").strip()
    if not value or value == "?":
        return "", ""
    match = _HOMONYM_RE.match(value)
    if not match:
        return value, ""
    return (match.group(1) or "").strip(), (match.group(2) or "").strip()


def _source_label(payload: dict[str, object]) -> str:
    article_source = str(payload.get("article_source") or "").strip()
    if article_source:
        return article_source
    source_created = str(payload.get("source_created") or "").strip()
    return source_created.upper()


def _normalize_gloss(value: str) -> str:
    text = html.unescape(value or "")
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass(frozen=True)
class DulatSourceProvenanceIndex:
    """Resolve col4 references to records imported from another lexicon."""

    exact_sources: dict[tuple[str, str], str]
    normalized_sources: dict[tuple[str, str], str]
    exact_gloss_sources: dict[tuple[tuple[str, str], str], str]
    normalized_gloss_sources: dict[tuple[tuple[str, str], str], str]
    exact_keys: frozenset[tuple[str, str]]

    @classmethod
    def empty(cls) -> "DulatSourceProvenanceIndex":
        return cls({}, {}, {}, {}, frozenset())

    @classmethod
    def from_sqlite(cls, db_path: Path) -> "DulatSourceProvenanceIndex":
        exact_all: dict[tuple[str, str], set[str]] = {}
        normalized_all: dict[tuple[str, str], set[str]] = {}
        exact_gloss_all: dict[tuple[tuple[str, str], str], set[str]] = {}
        normalized_gloss_all: dict[tuple[tuple[str, str], str], set[str]] = {}

        conn = sqlite3.connect(str(db_path))
        try:
            glosses_by_id: dict[int, list[str]] = {}
            try:
                translation_rows = conn.execute(
                    "SELECT entry_id, text FROM translations ORDER BY entry_id, rowid"
                )
                for entry_id, text_raw in translation_rows:
                    gloss = _normalize_gloss(str(text_raw or ""))
                    if gloss:
                        glosses_by_id.setdefault(int(entry_id), []).append(gloss)
            except sqlite3.OperationalError:
                pass
            try:
                rows = conn.execute(
                    "SELECT entry_id, lemma, COALESCE(homonym, ''), "
                    "COALESCE(data, '') FROM entries"
                )
            except sqlite3.OperationalError:
                return cls.empty()
            for entry_id, lemma_raw, homonym_raw, data_raw in rows:
                lemma = str(lemma_raw or "").strip()
                homonym = str(homonym_raw or "").strip()
                if not lemma:
                    continue
                try:
                    payload = json.loads(data_raw or "{}")
                except (TypeError, json.JSONDecodeError):
                    payload = {}
                if not isinstance(payload, dict):
                    payload = {}

                source = ""
                if payload.get("source_created") or payload.get("article_source"):
                    source = _source_label(payload)
                marker = source or "__ORIGINAL_DULAT__"
                exact_all.setdefault(_entry_key(lemma, homonym), set()).add(marker)
                normalized_all.setdefault(
                    _normalized_entry_key(lemma, homonym), set()
                ).add(marker)
                for gloss in glosses_by_id.get(int(entry_id), []):
                    exact_gloss_all.setdefault(
                        (_entry_key(lemma, homonym), gloss), set()
                    ).add(marker)
                    normalized_gloss_all.setdefault(
                        (_normalized_entry_key(lemma, homonym), gloss), set()
                    ).add(marker)
        finally:
            conn.close()

        def unambiguous_sources(
            values: dict[tuple[str, str], set[str]],
        ) -> dict[tuple[str, str], str]:
            return {
                key: next(iter(markers))
                for key, markers in values.items()
                if len(markers) == 1 and "__ORIGINAL_DULAT__" not in markers
            }

        return cls(
            exact_sources=unambiguous_sources(exact_all),
            normalized_sources=unambiguous_sources(normalized_all),
            exact_gloss_sources=unambiguous_sources(exact_gloss_all),
            normalized_gloss_sources=unambiguous_sources(normalized_gloss_all),
            exact_keys=frozenset(exact_all),
        )

    def sources_for_field(self, dulat_field: str, gloss: str = "") -> tuple[str, ...]:
        """Return source labels for unambiguous non-DULAT references in col4."""
        sources: set[str] = set()
        normalized_gloss = _normalize_gloss(gloss)
        for raw_token in _FIELD_SEPARATOR_RE.split(dulat_field or ""):
            lemma, homonym = _parse_declared_entry(raw_token)
            if not lemma:
                continue
            source = self.exact_sources.get(_entry_key(lemma, homonym))
            if not source and normalized_gloss:
                source = self.exact_gloss_sources.get(
                    (_entry_key(lemma, homonym), normalized_gloss)
                )
            exact_key = _entry_key(lemma, homonym)
            if not source and exact_key not in self.exact_keys:
                normalized_key = _normalized_entry_key(lemma, homonym)
                source = self.normalized_sources.get(normalized_key)
                if not source and normalized_gloss:
                    source = self.normalized_gloss_sources.get(
                        (normalized_key, normalized_gloss)
                    )
            if source:
                sources.add(source)
        return tuple(sorted(sources))


def provenance_comment(source: str) -> str:
    """Return the stable user-facing provenance annotation."""
    if source == "EUPT/LUPT":
        return "LUPT lemma"
    return f"{source} lemma"


def append_provenance_comments(
    existing: str,
    sources: tuple[str, ...],
) -> str:
    """Append missing provenance notes without disturbing reviewed comments."""
    comment = (existing or "").strip()
    for source in sources:
        legacy = f"DULAT DB source: {source} (not original DULAT)."
        comment = comment.replace(legacy, provenance_comment(source))
    additions = [provenance_comment(source) for source in sources]
    additions = [note for note in additions if note not in comment]
    if not additions:
        return comment
    suffix = " | ".join(additions)
    return f"{comment} | {suffix}" if comment else suffix
