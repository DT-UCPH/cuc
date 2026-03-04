"""Morphology.py-backed candidate generation for non-vocalized parsing."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from functools import lru_cache

from linter import morphology as ug_morphology
from pipeline.steps.analysis_utils import reconstruct_surface_from_analysis


@dataclass(frozen=True)
class PatternRow:
    stem: str
    conjugation: str
    form: str


@dataclass(frozen=True)
class VerbalCandidate:
    analysis: str
    person: str
    gender: str
    number: str
    stem: str
    conjugation: str


_LETTER_RE = re.compile(r"[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]")
_VERB_TOKEN_RE = re.compile(r"^/([^/]+)/")
_FORM_RE = re.compile(r"^(?P<person>[123])(?P<gender>[mfc])(?P<number>[sdp])$")
_VERBAL_STEMS = {
    "G",
    "Gt",
    "Gpass.",
    "N",
    "D",
    "Dpass.",
    "tD",
    "Dt",
    "L",
    "Lt",
    "tL",
    "Lpass.",
    "R",
    "Š",
    "Špass.",
    "Št",
}
_CONJ_MAP = {
    "pref.": "prefc.",
    "suffc.": "suffc.",
    "impv.": "impv.",
    "inf.": "inf.",
    "ptcpl.": "ptcpl.",
}
_STEM_MARKER_SUFFIX = {
    "D": ":d",
    "Dpass.": ":d",
    "Dt": ":d",
    "L": ":l",
    "Lt": ":l",
    "tL": ":l",
    "R": ":r",
}


@lru_cache(maxsize=1)
def load_verbal_pattern_rows() -> tuple[PatternRow, ...]:
    out: list[PatternRow] = []
    for name, value in vars(ug_morphology).items():
        if not name.startswith("pattern_") or not isinstance(value, str):
            continue
        reader = csv.reader(io.StringIO(value), delimiter="\t")
        rows = [row for row in reader if any((cell or "").strip() for cell in row)]
        if len(rows) < 2:
            continue
        headers = [cell.strip() for cell in rows[0]]
        for row in rows[1:]:
            cells = [cell.strip() for cell in row]
            if len(cells) < len(headers):
                continue
            record = dict(zip(headers, cells, strict=False))
            pos = record.get("pos", "")
            stem = record.get("stem", "")
            conjugation = record.get("conjugation", "")
            form = record.get("form", "")
            if not pos.startswith("vb") or stem not in _VERBAL_STEMS or not conjugation:
                continue
            out.append(
                PatternRow(
                    stem=stem,
                    conjugation=_CONJ_MAP.get(conjugation, conjugation),
                    form=form,
                )
            )
    return tuple(out)


def generate_verbal_candidates(
    *,
    surface: str,
    dulat: str,
    stem: str,
    conjugation: str,
) -> list[VerbalCandidate]:
    root = _extract_root_letters(dulat)
    if len(root) != 3:
        return []
    candidates: list[VerbalCandidate] = []
    for pattern in load_verbal_pattern_rows():
        if pattern.stem != stem or pattern.conjugation != conjugation:
            continue
        features = _decode_form(pattern.form)
        if features is None:
            continue
        analysis = _build_analysis(
            root=root,
            stem=stem,
            conjugation=conjugation,
            form=pattern.form,
        )
        if not analysis:
            continue
        if reconstruct_surface_from_analysis(analysis) != surface:
            continue
        person, gender, number = features
        candidates.append(
            VerbalCandidate(
                analysis=analysis,
                person=person,
                gender=gender,
                number=number,
                stem=stem,
                conjugation=conjugation,
            )
        )
    deduped: list[VerbalCandidate] = []
    seen: set[tuple[str, str, str, str]] = set()
    for candidate in candidates:
        key = (candidate.analysis, candidate.person, candidate.gender, candidate.number)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _extract_root_letters(dulat: str) -> tuple[str, ...]:
    match = _VERB_TOKEN_RE.search(dulat or "")
    if not match:
        return tuple()
    token = match.group(1)
    return tuple(letter for letter in token if _LETTER_RE.match(letter))


def _decode_form(form: str) -> tuple[str, str, str] | None:
    match = _FORM_RE.match((form or "").strip())
    if not match:
        return None
    person = match.group("person")
    gender_map = {"m": "m.", "f": "f.", "c": "c."}
    number_map = {"s": "sg.", "d": "du.", "p": "pl."}
    return (
        person,
        gender_map.get(match.group("gender"), ""),
        number_map.get(match.group("number"), ""),
    )


def _build_analysis(
    *,
    root: tuple[str, str, str],
    stem: str,
    conjugation: str,
    form: str,
) -> str:
    body = _build_body(root=root, stem=stem)
    if not body:
        return ""
    if conjugation == "prefc.":
        return _build_prefixed_analysis(body=body, form=form)
    if conjugation == "suffc.":
        return _build_suffix_analysis(body=body, form=form)
    if conjugation == "impv.":
        return body
    if conjugation == "inf.":
        return f"!!{body}/"
    if conjugation == "ptcpl.":
        return f"{body}/"
    return ""


def _build_body(*, root: tuple[str, str, str], stem: str) -> str:
    r1, r2, r3 = root
    third = _third_radical_segment(root)
    if stem == "G":
        return f"{r1}{r2}{third}["
    if stem == "D":
        return f"{r1}{r2}{third}[{_STEM_MARKER_SUFFIX['D']}"
    if stem == "Gt":
        return f"{r1}]t]{r2}{third}["
    if stem == "Dt":
        return f"]t]{r1}{r2}{third}[{_STEM_MARKER_SUFFIX['Dt']}"
    if stem == "Š":
        return f"]š]{r1}{r2}{third}["
    return ""


def _third_radical_segment(root: tuple[str, str, str]) -> str:
    third = root[2]
    if third in {"y", "w", "ʔ"}:
        return f"({third}"
    return third


def _build_prefixed_analysis(*, body: str, form: str) -> str:
    if form == "3ms":
        return f"!y!{body}"
    if form == "3fs":
        return f"!t!{body}"
    if form == "2ms":
        return f"!t=!{body}"
    if form == "2fs":
        return f"!t==!{body}"
    if form == "1cs":
        return f"!(ʔ&a!{body}"
    if form == "3md":
        return f"!t!{body}"
    if form == "3mp":
        return f"!t!{body}:w"
    if form == "2mp":
        return f"!t===!{body}"
    return ""


def _build_suffix_analysis(*, body: str, form: str) -> str:
    if body.endswith("["):
        base = body[:-1]
        marker = "["
    elif "[" in body:
        base, tail = body.split("[", 1)
        marker = f"[{tail}"
    else:
        base = body
        marker = "["
    if form == "3ms":
        return f"{base}{marker}"
    if form == "3mp":
        return f"{base}{marker}:w"
    if form == "2ms":
        return f"{base}{marker}t="
    if form == "2fs":
        return f"{base}{marker}t=="
    if form == "1cs":
        return f"{base}{marker}t"
    return ""
