"""Read exact-surface DULAT morphology for completion steps."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pipeline.config.dulat_form_morph_overrides import override_dulat_form_morphology
from pipeline.config.dulat_form_text_overrides import expand_dulat_form_texts
from pipeline.steps.dulat_gate import DulatMorphGate

LOOKUP_NORMALIZE = str.maketrans(
    {
        "ʿ": "ʕ",
        "ˤ": "ʕ",
        "ả": "a",
        "ỉ": "i",
        "ủ": "u",
    }
)
_TOKEN_RE = re.compile(r"^(.*?)(?:\s*\(([IVX]+)\))?$")
_FORM_PREFC_RE = re.compile(r"\b(?:prefc?|cprf)\b", re.IGNORECASE)
_FORM_SUFFC_RE = re.compile(r"\b(?:suffc|csuff)\b", re.IGNORECASE)
_FORM_SUFF_SHORT_RE = re.compile(r"\bsuff\.", re.IGNORECASE)
_FORM_WITH_SUFFIX_RE = re.compile(r"\bwith\s+suff\.", re.IGNORECASE)
_FORM_IMPV_RE = re.compile(r"\bimpv\b", re.IGNORECASE)
_FORM_INF_RE = re.compile(r"\binf\b", re.IGNORECASE)
_FORM_PTC_RE = re.compile(r"\bptc(?:pl)?\b", re.IGNORECASE)
_FORM_ACT_RE = re.compile(r"\bact\b", re.IGNORECASE)
_FORM_PASS_RE = re.compile(r"\bpass\b", re.IGNORECASE)
_NUMBER_RE = re.compile(r"\b(sg\.?|pl\.?|du\.?|dual|singular|plural)\b", re.IGNORECASE)
_STATE_RE = re.compile(r"\b(cstr\.?|cst\.?|abs\.?|suff\.)\b", re.IGNORECASE)
_CASE_RE = re.compile(r"\b(nom\.?|gen\.?|acc\.?|gen\., acc\.)\b", re.IGNORECASE)
_GENDER_RE = re.compile(r"\b(m\.?|f\.?|c\. n\.)\b", re.IGNORECASE)


@dataclass(frozen=True)
class DulatSurfaceFeatures:
    morphologies: tuple[str, ...]
    forms: tuple[str, ...]
    genders: tuple[str, ...]
    numbers: tuple[str, ...]
    states: tuple[str, ...]
    cases: tuple[str, ...]


class DulatFeatureReader:
    """Structured access to exact-surface DULAT morphology."""

    def __init__(self, db_path: Path | None = None, gate: DulatMorphGate | None = None) -> None:
        self._db_path = db_path or Path()
        self._gate = gate or DulatMorphGate(self._db_path)
        self._surface_index = (
            self._load_surface_index(self._db_path) if self._db_path.exists() else {}
        )

    def read_surface_features(
        self, surface: str, dulat: str, pos: str = ""
    ) -> DulatSurfaceFeatures:
        gate_morphologies = set(self._gate.surface_morphologies(dulat, surface))
        index_morphologies = set(self._lookup_index(surface, dulat))
        morphologies = tuple(sorted(gate_morphologies | index_morphologies))
        forms = self._collect_forms(morphologies)
        genders = self._collect(morphologies, _GENDER_RE)
        numbers = self._collect(morphologies, _NUMBER_RE)
        states = self._collect(morphologies, _STATE_RE)
        cases = self._collect(morphologies, _CASE_RE)
        return DulatSurfaceFeatures(
            morphologies=morphologies,
            forms=forms,
            genders=genders,
            numbers=numbers,
            states=states,
            cases=cases,
        )

    def _lookup_index(self, surface: str, dulat: str) -> set[str]:
        lemma, hom = self._parse_declared_token(dulat)
        if not lemma or lemma == "?":
            return set()
        key = (self._normalize(lemma), hom, self._normalize_form(surface))
        return set(self._surface_index.get(key, set()))

    def _load_surface_index(self, db_path: Path) -> dict[tuple[str, str, str], set[str]]:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        entry_index: dict[int, tuple[str, str]] = {}
        for entry_id, lemma, homonym in cur.execute("SELECT entry_id, lemma, homonym FROM entries"):
            parsed_lemma, parsed_homonym = self._parse_lemma_homonym(lemma or "", homonym or "")
            entry_index[int(entry_id)] = (self._normalize(parsed_lemma), parsed_homonym)

        out: dict[tuple[str, str, str], set[str]] = {}
        for entry_id, text, morphology in cur.execute(
            "SELECT entry_id, text, morphology FROM forms"
        ):
            key_head = entry_index.get(int(entry_id))
            if not key_head:
                continue
            lemma, hom = key_head
            morph = override_dulat_form_morphology(
                lemma=lemma,
                homonym=hom,
                form_text=text or "",
                morphology=(morphology or "").strip(),
            )
            for variant in expand_dulat_form_texts(lemma=lemma, homonym=hom, form_text=text or ""):
                form_key = self._normalize_form(variant)
                if not form_key:
                    continue
                out.setdefault((lemma, hom, form_key), set()).add((morph or "").strip().lower())

        conn.close()
        return out

    @staticmethod
    def _collect(morphologies: Iterable[str], pattern: re.Pattern[str]) -> tuple[str, ...]:
        out: list[str] = []
        for morph in morphologies:
            for match in pattern.findall(morph or ""):
                value = (match or "").strip().lower()
                if value and value not in out:
                    out.append(value)
        return tuple(out)

    @staticmethod
    def _collect_forms(morphologies: Iterable[str]) -> tuple[str, ...]:
        labels: list[str] = []
        for morph in morphologies:
            text = (morph or "").lower()
            has_prefc = _FORM_PREFC_RE.search(text) is not None
            has_suffc = _FORM_SUFFC_RE.search(text) is not None
            has_bare_suff = _FORM_SUFF_SHORT_RE.search(text) is not None
            if has_prefc:
                labels.append("prefc.")
            if has_suffc or (has_bare_suff and not _FORM_WITH_SUFFIX_RE.search(text)):
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
        out: list[str] = []
        for label in labels:
            if label not in out:
                out.append(label)
        return tuple(out)

    @staticmethod
    def _normalize(text: str) -> str:
        return (text or "").translate(LOOKUP_NORMALIZE).strip()

    @classmethod
    def _normalize_form(cls, text: str) -> str:
        normalized = cls._normalize(text).lower()
        return "".join(ch for ch in normalized if ch.isalpha())

    @classmethod
    def _parse_lemma_homonym(cls, lemma: str, homonym: str) -> tuple[str, str]:
        token = (lemma or "").strip()
        hom = (homonym or "").strip()
        if token and not hom:
            match = re.match(r"^(.*)\s+\(([IVX]+)\)$", token)
            if match:
                return match.group(1).strip(), (match.group(2) or "").strip()
        return token, hom

    @classmethod
    def _parse_declared_token(cls, token: str) -> tuple[str, str]:
        head = (token or "").split(",", 1)[0].strip()
        if not head or head == "?":
            return "", ""
        match = _TOKEN_RE.match(head)
        if not match:
            return head, ""
        return (match.group(1) or "").strip(), (match.group(2) or "").strip()
