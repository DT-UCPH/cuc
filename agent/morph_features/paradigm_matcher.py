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
_DEFAULT_FORM_INVENTORY = {
    "prefc.": ("3ms", "3fs", "2ms", "2fs", "1cs", "3md", "3mp", "2mp"),
    "suffc.": ("3ms", "3mp", "2ms", "2fs", "1cs"),
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
    for form in _candidate_forms(stem=stem, conjugation=conjugation):
        features = _decode_form(form)
        if features is None:
            continue
        for analysis in _build_analyses(
            root=root,
            stem=stem,
            conjugation=conjugation,
            form=form,
        ):
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


def _candidate_forms(*, stem: str, conjugation: str) -> tuple[str, ...]:
    forms = [
        pattern.form
        for pattern in load_verbal_pattern_rows()
        if pattern.stem == stem and pattern.conjugation == conjugation
    ]
    if len(set(forms)) < 2:
        forms.extend(_DEFAULT_FORM_INVENTORY.get(conjugation, ()))
    out: list[str] = []
    for form in forms:
        if form and form not in out:
            out.append(form)
    return tuple(out)


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


def _build_analyses(
    *,
    root: tuple[str, str, str],
    stem: str,
    conjugation: str,
    form: str,
) -> tuple[str, ...]:
    analyses: list[str] = []
    for body in _build_body_variants(root=root, stem=stem, conjugation=conjugation):
        if not body:
            continue
        analysis = _build_analysis_from_body(body=body, conjugation=conjugation, form=form)
        if analysis and analysis not in analyses:
            analyses.append(analysis)
    return tuple(analyses)


def _build_analysis_from_body(
    *,
    body: str,
    conjugation: str,
    form: str,
) -> str:
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


def _build_body_variants(
    *,
    root: tuple[str, str, str],
    stem: str,
    conjugation: str,
) -> tuple[str, ...]:
    r2 = root[1]
    out: list[str] = []
    for r1 in _first_radical_variants(root[0], conjugation):
        for r3 in _third_radical_variants(root[2]):
            if stem == "G":
                body = f"{r1}{r2}{r3}["
            elif stem == "D":
                body = f"{r1}{r2}{r3}[{_STEM_MARKER_SUFFIX['D']}"
            elif stem == "Gt":
                body = f"{r1}]t]{r2}{r3}["
            elif stem == "Dt":
                body = f"]t]{r1}{r2}{r3}[{_STEM_MARKER_SUFFIX['Dt']}"
            elif stem == "Š":
                body = f"]š]{r1}{r2}{r3}["
            else:
                body = ""
            if body and body not in out:
                out.append(body)
    return tuple(out)


def _first_radical_variants(first: str, conjugation: str) -> tuple[str, ...]:
    if first not in {"y", "w"} or conjugation != "prefc.":
        return (first,)
    return (first, f"({first}")


def _third_radical_variants(third: str) -> tuple[str, ...]:
    if third not in {"y", "w", "ʔ"}:
        return (third,)
    return (third, f"({third}")


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
