"""Enrich verb POS payloads with DULAT stem labels from exact surface forms."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

from pipeline.config.dulat_form_text_overrides import expand_dulat_form_texts
from pipeline.steps.analysis_utils import reconstruct_surface_from_analysis
from pipeline.steps.base import RefinementStep, TabletRow

LOOKUP_NORMALIZE = str.maketrans(
    {
        "ʿ": "ʕ",
        "ˤ": "ʕ",
        "ả": "a",
        "ỉ": "i",
        "ủ": "u",
    }
)

STEM_ORDER = (
    "G",
    "Gt",
    "N",
    "D",
    "tD",
    "Dt",
    "L",
    "tL",
    "Lt",
    "R",
    "Š",
    "Št",
    "Gpass",
    "Dpass",
    "Špass",
    "Nt",
)
_STEM_SET = set(STEM_ORDER)
_STEM_RE = re.compile(r"\b(Gt|Dt|Lt|Nt|tD|tL|Št|Gpass|Dpass|Špass|G|D|L|N|R|Š)\b")
_ENTRY_HOM_RE = re.compile(r"^(.*)\s+\(([IVX]+)\)$")
_TOKEN_RE = re.compile(r"^(.*?)(?:\s*\(([IVX]+)\))?$")
_VERBAL_NOUN_POS_RE = re.compile(r"\bvb\.\s*n\.", flags=re.IGNORECASE)
_VB_POS_STEM_RE = re.compile(
    r"\bvb\.?\s+(?:Gt|Dt|Lt|Nt|tD|tL|Št|Gpass|Dpass|Špass|G|D|L|N|R|Š)"
    r"(?:/(?:Gt|Dt|Lt|Nt|tD|tL|Št|Gpass|Dpass|Špass|G|D|L|N|R|Š))*\b",
    flags=re.IGNORECASE,
)
_VB_POS_HEAD_RE = re.compile(r"^\s*vb\.?\b", flags=re.IGNORECASE)


def _extract_stems(morph: str) -> set[str]:
    return {stem for stem in _STEM_RE.findall(morph or "") if stem}


def _normalize_lookup(text: str) -> str:
    return (text or "").translate(LOOKUP_NORMALIZE).strip()


def _normalize_form(text: str) -> str:
    normalized = _normalize_lookup(text).lower()
    return "".join(ch for ch in normalized if ch.isalpha())


def _parse_lemma_homonym(lemma: str, homonym: str) -> Tuple[str, str]:
    token = (lemma or "").strip()
    hom = (homonym or "").strip()
    if token and not hom:
        match = _ENTRY_HOM_RE.match(token)
        if match:
            return match.group(1).strip(), (match.group(2) or "").strip()
    return token, hom


def _parse_declared_token(token: str) -> Tuple[str, str]:
    # Keep the host token when suffix payload tails are still present.
    head = (token or "").split(",", 1)[0].strip()
    if not head or head == "?":
        return "", ""
    match = _TOKEN_RE.match(head)
    if not match:
        return head, ""
    return (match.group(1) or "").strip(), (match.group(2) or "").strip()


def _sorted_stems(stems: Iterable[str]) -> List[str]:
    ranking = {stem: idx for idx, stem in enumerate(STEM_ORDER)}
    return sorted(set(stems), key=lambda stem: (ranking.get(stem, 999), stem))


def _surface_candidates(surface: str, analysis_variant: str) -> List[str]:
    out: List[str] = []
    raw_surface = (surface or "").strip()
    if raw_surface:
        out.append(raw_surface)

    analysis = (analysis_variant or "").strip()
    if analysis and ("+" in analysis or "~" in analysis):
        head = re.split(r"[+~]", analysis, maxsplit=1)[0].strip()
        if head and head != analysis:
            reconstructed = reconstruct_surface_from_analysis(head)
            if reconstructed:
                out.append(reconstructed)

    deduped: List[str] = []
    seen: set[str] = set()
    for candidate in out:
        key = _normalize_form(candidate)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


@dataclass(frozen=True)
class VerbStemIndex:
    """Index exact surface+entry stem attestations for verb lemmas."""

    entry_ids_by_lemma_hom: Dict[Tuple[str, str], Set[int]]
    entry_ids_by_lemma: Dict[str, Set[int]]
    stems_by_surface_entry: Dict[Tuple[str, int], Set[str]]
    stems_by_surface: Dict[str, Set[str]]

    @classmethod
    def from_sqlite(cls, db_path: Path) -> "VerbStemIndex":
        if not db_path.exists():
            return cls({}, {}, {}, {})

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        verb_entry_ids: set[int] = set()
        entry_ids_by_lemma_hom: Dict[Tuple[str, str], Set[int]] = {}
        entry_ids_by_lemma: Dict[str, Set[int]] = {}
        entry_lemma_hom_by_id: Dict[int, Tuple[str, str]] = {}

        for entry_id, lemma, homonym, pos in cur.execute(
            "SELECT entry_id, lemma, homonym, pos FROM entries"
        ):
            pos_text = (pos or "").lower()
            if "vb" not in pos_text:
                continue
            if _VERBAL_NOUN_POS_RE.search(pos_text):
                continue

            parsed_lemma, parsed_homonym = _parse_lemma_homonym(lemma or "", homonym or "")
            lemma_norm = _normalize_lookup(parsed_lemma)
            if not lemma_norm:
                continue

            entry_id_int = int(entry_id)
            verb_entry_ids.add(entry_id_int)
            entry_lemma_hom_by_id[entry_id_int] = (parsed_lemma, parsed_homonym)
            key = (lemma_norm, parsed_homonym)
            entry_ids_by_lemma_hom.setdefault(key, set()).add(entry_id_int)
            entry_ids_by_lemma.setdefault(lemma_norm, set()).add(entry_id_int)

        stems_by_surface_entry: Dict[Tuple[str, int], Set[str]] = {}
        stems_by_surface: Dict[str, Set[str]] = {}
        for entry_id, text, morphology in cur.execute(
            "SELECT entry_id, text, morphology FROM forms"
        ):
            entry_id_int = int(entry_id)
            if entry_id_int not in verb_entry_ids:
                continue
            stems = _extract_stems(morphology or "")
            if not stems:
                continue
            lemma_hom = entry_lemma_hom_by_id.get(entry_id_int)
            if not lemma_hom:
                continue
            parsed_lemma, parsed_homonym = lemma_hom
            for form_variant in expand_dulat_form_texts(
                lemma=parsed_lemma,
                homonym=parsed_homonym,
                form_text=text or "",
            ):
                form_norm = _normalize_form(form_variant)
                if not form_norm:
                    continue
                stems_by_surface_entry.setdefault((form_norm, entry_id_int), set()).update(stems)
                stems_by_surface.setdefault(form_norm, set()).update(stems)

        conn.close()
        return cls(
            entry_ids_by_lemma_hom=entry_ids_by_lemma_hom,
            entry_ids_by_lemma=entry_ids_by_lemma,
            stems_by_surface_entry=stems_by_surface_entry,
            stems_by_surface=stems_by_surface,
        )

    def stems_for(self, surface: str, dulat_token: str) -> List[str]:
        surface_norm = _normalize_form(surface or "")
        if not surface_norm:
            return []

        token_lemma, token_homonym = _parse_declared_token(dulat_token)
        token_lemma_norm = _normalize_lookup(token_lemma)

        matched_stems: set[str] = set()
        if token_lemma_norm:
            if token_homonym:
                entry_ids = self.entry_ids_by_lemma_hom.get(
                    (token_lemma_norm, token_homonym), set()
                )
            else:
                entry_ids = self.entry_ids_by_lemma.get(token_lemma_norm, set())
            for entry_id in entry_ids:
                matched_stems.update(
                    self.stems_by_surface_entry.get((surface_norm, entry_id), set())
                )

        if not matched_stems:
            matched_stems.update(self.stems_by_surface.get(surface_norm, set()))

        return _sorted_stems(stem for stem in matched_stems if stem in _STEM_SET)


class VerbPosStemFixer(RefinementStep):
    """Append DULAT stem labels to verb POS values in column 5."""

    def __init__(self, dulat_db: Path, stem_index: VerbStemIndex | None = None) -> None:
        self._stem_index = stem_index or VerbStemIndex.from_sqlite(dulat_db)

    @property
    def name(self) -> str:
        return "verb-pos-stem"

    def refine_row(self, row: TabletRow) -> TabletRow:
        pos_text = (row.pos or "").strip()
        if not self._is_target_pos(pos_text):
            return row
        if _VB_POS_STEM_RE.search(pos_text):
            return row

        stems: List[str] = []
        for candidate in _surface_candidates(surface=row.surface, analysis_variant=row.analysis):
            stems = self._stem_index.stems_for(surface=candidate, dulat_token=row.dulat)
            if stems:
                break
        if not stems:
            return row

        stem_payload = "/".join(stems)
        new_pos = re.sub(
            r"\bvb\.?\b",
            lambda match: f"{match.group(0)} {stem_payload}",
            pos_text,
            count=1,
            flags=re.IGNORECASE,
        )
        if new_pos == pos_text:
            return row

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=row.analysis,
            dulat=row.dulat,
            pos=new_pos,
            gloss=row.gloss,
            comment=row.comment,
        )

    def _is_target_pos(self, pos_text: str) -> bool:
        lower = pos_text.lower()
        if not _VB_POS_HEAD_RE.search(lower):
            return False
        if _VERBAL_NOUN_POS_RE.search(lower):
            return False
        return True
