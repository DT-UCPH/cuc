"""Enrich verb POS with DULAT form-level morphology (prefc./suffc./ptcpl. etc.)."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Set, Tuple

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

_ENTRY_HOM_RE = re.compile(r"^(.*)\s+\(([IVX]+)\)$")
_TOKEN_RE = re.compile(r"^(.*?)(?:\s*\(([IVX]+)\))?$")
_VB_POS_HEAD_RE = re.compile(r"^\s*vb\.?\b", flags=re.IGNORECASE)
_VERBAL_NOUN_POS_RE = re.compile(r"\bvb\.\s*n\.", flags=re.IGNORECASE)

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
    "Lpass",
    "Špass",
    "Nt",
)
_STEM_RANK = {stem: idx for idx, stem in enumerate(STEM_ORDER)}
_STEM_TOKEN_RE = re.compile(
    r"\b(gpass|dpass|lpass|špass|gt|dt|lt|nt|td|tl|št|g|d|l|n|r|š)\b",
    flags=re.IGNORECASE,
)
_STEM_CANON = {
    "g": "G",
    "gt": "Gt",
    "n": "N",
    "d": "D",
    "td": "tD",
    "dt": "Dt",
    "l": "L",
    "tl": "tL",
    "lt": "Lt",
    "r": "R",
    "š": "Š",
    "št": "Št",
    "gpass": "Gpass",
    "dpass": "Dpass",
    "lpass": "Lpass",
    "špass": "Špass",
    "nt": "Nt",
}

_FORM_PREFC_RE = re.compile(r"\b(?:prefc?|cprf)\b", flags=re.IGNORECASE)
_FORM_SUFFC_RE = re.compile(r"\b(?:suffc?|csuff)\b", flags=re.IGNORECASE)
_FORM_IMPV_RE = re.compile(r"\bimpv\b", flags=re.IGNORECASE)
_FORM_INF_RE = re.compile(r"\binf\b", flags=re.IGNORECASE)
_FORM_PTC_RE = re.compile(r"\bptc(?:pl)?\b", flags=re.IGNORECASE)
_FORM_ACT_RE = re.compile(r"\bact\b", flags=re.IGNORECASE)
_FORM_PASS_RE = re.compile(r"\bpass\b", flags=re.IGNORECASE)

_MASC_RE = re.compile(r"\bm\.", flags=re.IGNORECASE)
_FEM_RE = re.compile(r"\bf\.", flags=re.IGNORECASE)
_SING_RE = re.compile(r"(?:\bsg\.|\bsing(?:ular)?)(?=$|\s|,|;)", flags=re.IGNORECASE)
_PLUR_RE = re.compile(r"(?:\bpl\.|\bplur(?:al)?)(?=$|\s|,|;)", flags=re.IGNORECASE)
_DUAL_RE = re.compile(r"(?:\bdu\.|\bdual)(?=$|\s|,|;)", flags=re.IGNORECASE)

FORM_ORDER = ("prefc.", "suffc.", "impv.", "inf.", "act. ptcpl.", "pass. ptcpl.", "ptcpl.")
_FORM_RANK = {label: idx for idx, label in enumerate(FORM_ORDER)}
_GENDER_RANK = {"": 0, "m.": 1, "f.": 2}
_NUMBER_RANK = {"": 0, "sg.": 1, "pl.": 2, "du.": 3}


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";")]


def _split_comma(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(",")]


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


def _is_target_pos(pos_text: str) -> bool:
    lower = (pos_text or "").lower()
    if not _VB_POS_HEAD_RE.search(lower):
        return False
    if _VERBAL_NOUN_POS_RE.search(lower):
        return False
    return True


def _extract_existing_stems(pos_text: str) -> set[str]:
    token = (pos_text or "").strip()
    if not token:
        return set()
    out: set[str] = set()
    for part in re.split(r"\s*/\s*", token):
        for match in _STEM_TOKEN_RE.findall((part or "").lower()):
            stem = _STEM_CANON.get(match.lower())
            if stem:
                out.add(stem)
    return out


def _extract_stems_from_morphology(morphology: str) -> set[str]:
    out: set[str] = set()
    for match in _STEM_TOKEN_RE.findall((morphology or "").lower()):
        stem = _STEM_CANON.get(match.lower())
        if stem:
            out.add(stem)
    return out


def _extract_form_labels(morphology: str) -> list[str]:
    text = (morphology or "").lower()
    labels: list[str] = []
    if _FORM_PREFC_RE.search(text):
        labels.append("prefc.")
    if _FORM_SUFFC_RE.search(text):
        labels.append("suffc.")
    if _FORM_IMPV_RE.search(text):
        labels.append("impv.")
    if _FORM_INF_RE.search(text):
        labels.append("inf.")
    if _FORM_PTC_RE.search(text):
        has_act = _FORM_ACT_RE.search(text) is not None
        has_pass = _FORM_PASS_RE.search(text) is not None
        if has_act:
            labels.append("act. ptcpl.")
        if has_pass:
            labels.append("pass. ptcpl.")
        if not has_act and not has_pass:
            labels.append("ptcpl.")
    if not labels:
        return [""]
    return _dedupe(labels)


def _extract_gender_labels(morphology: str) -> list[str]:
    text = (morphology or "").lower()
    out: list[str] = []
    if _MASC_RE.search(text):
        out.append("m.")
    if _FEM_RE.search(text):
        out.append("f.")
    if not out:
        return [""]
    return _dedupe(out)


def _extract_number_labels(morphology: str) -> list[str]:
    text = (morphology or "").lower()
    out: list[str] = []
    if _SING_RE.search(text):
        out.append("sg.")
    if _PLUR_RE.search(text):
        out.append("pl.")
    if _DUAL_RE.search(text):
        out.append("du.")
    if not out:
        return [""]
    return _dedupe(out)


def _sorted_stems(stems: Iterable[str]) -> list[str]:
    return sorted(set(stems), key=lambda stem: (_STEM_RANK.get(stem, 999), stem))


def _dedupe(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    for raw in values:
        item = (raw or "").strip()
        if not item:
            continue
        if item in out:
            continue
        out.append(item)
    return out


def _surface_candidates(surface: str, analysis_variant: str) -> list[str]:
    out: list[str] = []
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

    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in out:
        key = _normalize_form(candidate)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


@dataclass(frozen=True)
class VerbFormOption:
    stem: str
    form: str
    gender: str
    number: str

    def render(self) -> str:
        parts = ["vb", self.stem]
        if self.form:
            parts.append(self.form)
        if self.gender:
            parts.append(self.gender)
        if self.number:
            parts.append(self.number)
        return " ".join(part for part in parts if part).strip()


@dataclass(frozen=True)
class VerbFormMorphIndex:
    """Index exact form morphologies for verbal DULAT entries."""

    entry_ids_by_lemma_hom: Dict[Tuple[str, str], Set[int]]
    entry_ids_by_lemma: Dict[str, Set[int]]
    morphs_by_surface_entry: Dict[Tuple[str, int], Set[str]]
    morphs_by_surface: Dict[str, Set[str]]

    @classmethod
    def from_sqlite(cls, db_path: Path) -> "VerbFormMorphIndex":
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

        morphs_by_surface_entry: Dict[Tuple[str, int], Set[str]] = {}
        morphs_by_surface: Dict[str, Set[str]] = {}
        for entry_id, text, morphology in cur.execute(
            "SELECT entry_id, text, morphology FROM forms"
        ):
            entry_id_int = int(entry_id)
            if entry_id_int not in verb_entry_ids:
                continue
            morph = (morphology or "").strip().lower()
            if not morph:
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
                morphs_by_surface_entry.setdefault((form_norm, entry_id_int), set()).add(morph)
                morphs_by_surface.setdefault(form_norm, set()).add(morph)

        conn.close()
        return cls(
            entry_ids_by_lemma_hom=entry_ids_by_lemma_hom,
            entry_ids_by_lemma=entry_ids_by_lemma,
            morphs_by_surface_entry=morphs_by_surface_entry,
            morphs_by_surface=morphs_by_surface,
        )

    def morphologies_for(self, surface: str, dulat_token: str) -> set[str]:
        surface_norm = _normalize_form(surface or "")
        if not surface_norm:
            return set()

        token_lemma, token_homonym = _parse_declared_token(dulat_token)
        token_lemma_norm = _normalize_lookup(token_lemma)

        out: set[str] = set()
        if token_lemma_norm:
            if token_homonym:
                entry_ids = self.entry_ids_by_lemma_hom.get(
                    (token_lemma_norm, token_homonym), set()
                )
            else:
                entry_ids = self.entry_ids_by_lemma.get(token_lemma_norm, set())
            for entry_id in entry_ids:
                out.update(self.morphs_by_surface_entry.get((surface_norm, entry_id), set()))

        if out:
            return out
        return set(self.morphs_by_surface.get(surface_norm, set()))


class VerbFormMorphPosFixer(RefinementStep):
    """Expand verb POS variants with exact DULAT form-level morphology."""

    def __init__(
        self,
        dulat_db: Path,
        form_index: Optional[VerbFormMorphIndex] = None,
    ) -> None:
        self._index = form_index or VerbFormMorphIndex.from_sqlite(dulat_db)

    @property
    def name(self) -> str:
        return "verb-form-morph-pos"

    def refine_row(self, row: TabletRow) -> TabletRow:
        pos_variants = _split_semicolon(row.pos)
        if not pos_variants:
            return row

        analysis_variants = _split_semicolon(row.analysis)
        dulat_variants = _split_semicolon(row.dulat)
        changed = False
        out_pos: list[str] = []

        for idx, pos_variant in enumerate(pos_variants):
            current_pos = (pos_variant or "").strip()
            if not _is_target_pos(current_pos):
                out_pos.append(current_pos)
                continue

            analysis_variant = analysis_variants[idx] if idx < len(analysis_variants) else ""
            dulat_variant = dulat_variants[idx] if idx < len(dulat_variants) else ""
            dulat_head = _split_comma(dulat_variant)[0] if dulat_variant else ""
            morphologies: set[str] = set()
            for candidate in _surface_candidates(
                surface=row.surface, analysis_variant=analysis_variant
            ):
                morphologies = self._index.morphologies_for(
                    surface=candidate, dulat_token=dulat_head
                )
                if morphologies:
                    break
            rewritten = self._rewrite_variant(current_pos=current_pos, morphologies=morphologies)
            out_pos.append(rewritten)
            if rewritten != current_pos:
                changed = True

        if not changed:
            return row

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=row.analysis,
            dulat=row.dulat,
            pos="; ".join(out_pos),
            gloss=row.gloss,
            comment=row.comment,
        )

    def _rewrite_variant(self, current_pos: str, morphologies: set[str]) -> str:
        if not morphologies:
            return current_pos

        existing_stems = _extract_existing_stems(current_pos)
        options: list[VerbFormOption] = []
        for morph in morphologies:
            options.extend(
                _options_from_morphology(morphology=morph, existing_stems=existing_stems)
            )
        if not options:
            return current_pos

        rendered = _render_options(options)
        return rendered or current_pos


def _options_from_morphology(morphology: str, existing_stems: set[str]) -> list[VerbFormOption]:
    stems = _extract_stems_from_morphology(morphology)
    if stems and existing_stems:
        overlap = stems & existing_stems
        if not overlap:
            return []
        stems = overlap
    if not stems:
        stems = set(existing_stems)
    if not stems:
        return []

    forms = _extract_form_labels(morphology)
    genders = _extract_gender_labels(morphology)
    numbers = _extract_number_labels(morphology)

    out: list[VerbFormOption] = []
    for stem in _sorted_stems(stems):
        for form in forms:
            for gender in genders:
                for number in numbers:
                    out.append(VerbFormOption(stem=stem, form=form, gender=gender, number=number))
    return out


def _render_options(options: list[VerbFormOption]) -> str:
    rendered = {option.render(): option for option in options if option.render()}
    ordered = sorted(
        rendered.items(),
        key=lambda item: (
            _STEM_RANK.get(item[1].stem, 999),
            _FORM_RANK.get(item[1].form, 999),
            _GENDER_RANK.get(item[1].gender, 999),
            _NUMBER_RANK.get(item[1].number, 999),
            item[0],
        ),
    )
    return " / ".join(label for label, _ in ordered)
