"""DULAT attestation-frequency index used for option ranking."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Set, Tuple

ALEPH_NORMALIZE = str.maketrans(
    {
        "ả": "a",
        "ỉ": "i",
        "ủ": "u",
        "ʿ": "ʕ",
        "ˤ": "ʕ",
    }
)

_DULAT_TOKEN_RE = re.compile(r"^(.*?)(?:\s*\(([IV]+)\))?$")
_REF_PREFIX_RE = re.compile(r"^(?:KTU|CAT)\s+", flags=re.IGNORECASE)


def normalize_lemma(lemma: str) -> str:
    """Normalize lemma for robust lookup."""
    return (lemma or "").strip().translate(ALEPH_NORMALIZE)


def parse_dulat_head_token(variant_token: str) -> Tuple[str, str]:
    """Parse first DULAT head token from a variant string."""
    token = (variant_token or "").strip()
    if not token or token == "?":
        return "", ""
    head = token.split(",", 1)[0].strip()
    m = _DULAT_TOKEN_RE.match(head)
    if not m:
        return normalize_lemma(head), ""
    lemma = normalize_lemma(m.group(1) or "")
    hom = (m.group(2) or "").strip()
    return lemma, hom


def normalize_reference_label(reference: str) -> str:
    """Normalize KTU/CAT reference labels for stable comparison."""
    text = (reference or "").strip().replace("–", "-")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*:\s*", ":", text)
    text = re.sub(r"\s*-\s*", "-", text)
    text = _REF_PREFIX_RE.sub("", text)
    return text.strip()


@dataclass(frozen=True)
class DulatAttestationIndex:
    """Attestation counts keyed by DULAT lemma/homonym."""

    counts_by_key: Dict[Tuple[str, str], int]
    max_count_by_lemma: Dict[str, int]
    refs_by_key: Dict[Tuple[str, str], Set[str]] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> "DulatAttestationIndex":
        return cls(counts_by_key={}, max_count_by_lemma={}, refs_by_key={})

    @classmethod
    def from_sqlite(cls, dulat_db: Path) -> "DulatAttestationIndex":
        if not Path(dulat_db).exists():
            return cls.empty()

        counts_by_key: Dict[Tuple[str, str], int] = {}
        max_count_by_lemma: Dict[str, int] = {}
        refs_by_key: Dict[Tuple[str, str], Set[str]] = {}

        conn = sqlite3.connect(dulat_db)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                  e.lemma,
                  COALESCE(e.homonym, ''),
                  COUNT(a.rowid) AS attestation_count
                FROM entries e
                LEFT JOIN attestations a ON a.entry_id = e.entry_id
                GROUP BY e.entry_id
                """
            )
            for lemma_raw, hom_raw, count_raw in cur.fetchall():
                lemma = normalize_lemma(lemma_raw or "")
                if not lemma:
                    continue
                hom = (hom_raw or "").strip()
                count = int(count_raw or 0)
                counts_by_key[(lemma, hom)] = count
                prev = max_count_by_lemma.get(lemma, -1)
                if count > prev:
                    max_count_by_lemma[lemma] = count

            cur.execute(
                """
                SELECT
                  e.lemma,
                  COALESCE(e.homonym, ''),
                  a.citation
                FROM entries e
                LEFT JOIN attestations a ON a.entry_id = e.entry_id
                """
            )
            for lemma_raw, hom_raw, citation_raw in cur.fetchall():
                lemma = normalize_lemma(lemma_raw or "")
                if not lemma:
                    continue
                citation = normalize_reference_label(citation_raw or "")
                if not citation:
                    continue
                hom = (hom_raw or "").strip()
                refs_by_key.setdefault((lemma, hom), set()).add(citation)
        except sqlite3.Error:
            return cls.empty()
        finally:
            conn.close()

        return cls(
            counts_by_key=counts_by_key,
            max_count_by_lemma=max_count_by_lemma,
            refs_by_key=refs_by_key,
        )

    def count_for_variant_token(self, variant_token: str) -> int:
        """Resolve attestation count for a DULAT variant token."""
        lemma, hom = parse_dulat_head_token(variant_token)
        if not lemma:
            return -1
        if hom:
            return self.counts_by_key.get((lemma, hom), -1)
        if (lemma, "") in self.counts_by_key:
            return self.counts_by_key[(lemma, "")]
        return self.max_count_by_lemma.get(lemma, -1)

    def has_reference_for_variant_token(self, variant_token: str, section_ref: str) -> bool:
        """Check whether the token is attested at the current section reference."""
        lemma, hom = parse_dulat_head_token(variant_token)
        if not lemma:
            return False
        ref_key = normalize_reference_label(section_ref)
        if not ref_key:
            return False

        if hom:
            return ref_key in self.refs_by_key.get((lemma, hom), set())
        if ref_key in self.refs_by_key.get((lemma, ""), set()):
            return True
        for (lemma_key, _hom), refs in self.refs_by_key.items():
            if lemma_key != lemma:
                continue
            if ref_key in refs:
                return True
        return False
