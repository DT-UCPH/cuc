"""Deterministic verbal morphology completion from analysis + DULAT features."""

from __future__ import annotations

import re
from typing import Sequence

from morph_features.analysis_decoder import (
    decode_analysis,
    explicit_prefix_features,
    explicit_suffix_conjugation_features,
)
from morph_features.dulat_feature_reader import DulatFeatureReader
from morph_features.feature_bundle_builder import build_verbal_bundle
from morph_features.paradigm_matcher import generate_verbal_candidates
from morph_features.pos_renderer import render_pos
from morph_features.types import CompletedVariant
from pipeline.steps.analysis_utils import normalize_surface, reconstruct_surface_from_analysis
from pipeline.steps.base import TabletRow

_STEM_POS_RE = re.compile(r"\b(Gt|Dt|Lt|Nt|tD|tL|Št|Gpass|Dpass|Špass|G|D|L|N|R|Š)\b")
_FORM_ORDER = {
    "prefc.": 0,
    "suffc.": 1,
    "impv.": 2,
    "inf.": 3,
    "act. ptcpl.": 4,
    "pass. ptcpl.": 5,
    "ptcpl.": 6,
}
_VERB_ROOT_RE = re.compile(r"^/([^/]+)/")


class VerbalFeatureCompleter:
    """Complete and split verbal rows conservatively."""

    def __init__(self, feature_reader: DulatFeatureReader) -> None:
        self._reader = feature_reader

    def complete_row(self, row: TabletRow) -> list[CompletedVariant]:
        if "vb" not in (row.pos or "").lower():
            return [self._variant(row.analysis, row.dulat, row.pos, row.gloss, row.comment)]

        features = self._reader.read_surface_features(row.surface, row.dulat, row.pos)
        stems = self._extract_stems(row.pos)
        forms = self._extract_forms(row.pos, features.forms)
        if not stems:
            stems = [""]
        if not forms:
            return [self._variant(row.analysis, row.dulat, row.pos, row.gloss, row.comment)]

        variants: list[CompletedVariant] = []
        for form in forms:
            stem = stems[0]
            candidates = self._pattern_candidates(
                row=row,
                stem=stem,
                form=form,
            )
            if candidates:
                variants.extend(candidates)
                continue
            analysis_variant = self._analysis_for_form(row, form, stem)
            decoded = decode_analysis(analysis_variant)
            person, gender, number = self._features_for_form(form, decoded)
            state, case = self._state_case_for_form(form=form, analysis=analysis_variant)
            variants.append(
                CompletedVariant(
                    analysis=analysis_variant,
                    dulat=row.dulat,
                    gloss=row.gloss,
                    comment=row.comment,
                    features=build_verbal_bundle(
                        stem=stems[0],
                        form=form,
                        person=person,
                        gender=gender,
                        number=number,
                        state=state,
                        case=case,
                        source="analysis+dulat",
                        confidence="high" if person or gender or number else "medium",
                        has_enclitic=decoded.has_enclitic,
                        enclitic_type=decoded.enclitic_marker,
                    ),
                )
            )

        deduped: list[CompletedVariant] = []
        seen: set[tuple[str, str]] = set()
        for variant in variants:
            rendered = render_pos(variant.features, fallback=row.pos)
            key = (variant.analysis, rendered)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(variant)
        return deduped or [self._variant(row.analysis, row.dulat, row.pos, row.gloss, row.comment)]

    def _variant(
        self, analysis: str, dulat: str, pos: str, gloss: str, comment: str
    ) -> CompletedVariant:
        form = self._extract_forms(pos, ())[0] if self._extract_forms(pos, ()) else ""
        state, case = self._state_case_for_form(form=form, analysis=analysis)
        bundle = build_verbal_bundle(
            stem=self._extract_stems(pos)[0] if self._extract_stems(pos) else "",
            form=form,
            state=state,
            case=case,
            source="existing",
        )
        return CompletedVariant(
            analysis=analysis, dulat=dulat, gloss=gloss, comment=comment, features=bundle
        )

    @staticmethod
    def _extract_stems(pos_text: str) -> list[str]:
        out: list[str] = []
        for match in _STEM_POS_RE.findall(pos_text or ""):
            if match not in out:
                out.append(match)
        return out

    @staticmethod
    def _extract_forms(pos_text: str, fallback_forms: Sequence[str]) -> list[str]:
        explicit_forms = [label for label in _FORM_ORDER if label in (pos_text or "")]
        if "act. ptcpl." in explicit_forms and "ptcpl." in explicit_forms:
            explicit_forms.remove("ptcpl.")
        if "pass. ptcpl." in explicit_forms and "ptcpl." in explicit_forms:
            explicit_forms.remove("ptcpl.")
        fallback = [label for label in fallback_forms if label in _FORM_ORDER]
        fallback = list(dict.fromkeys(fallback))
        if explicit_forms:
            if fallback:
                constrained = [label for label in explicit_forms if label in fallback]
                if constrained:
                    return constrained
                return fallback
            return explicit_forms
        if fallback:
            return fallback
        return []

    @staticmethod
    def _analysis_for_form(row: TabletRow, form: str, stem: str) -> str:
        analysis = (row.analysis or "").strip()
        if form == "suffc." and analysis.startswith("!"):
            surface = reconstruct_surface_from_analysis(analysis)
            suffix = VerbalFeatureCompleter._analysis_suffix_marker(analysis)
            return VerbalFeatureCompleter._suffix_fallback_analysis(
                surface=surface,
                dulat=row.dulat,
                stem=stem,
                suffix=suffix,
            )
        return analysis

    @staticmethod
    def _suffix_fallback_analysis(*, surface: str, dulat: str, stem: str, suffix: str) -> str:
        visible = (surface or "").strip()
        root = VerbalFeatureCompleter._dulat_root_letters(dulat)

        if stem == "N":
            if visible.startswith("n"):
                host = f"]n]{visible[1:]}"
            else:
                host = f"(]n]{visible}"
            return f"{host}[{suffix}" if suffix else f"{host}["

        if root:
            normalized_visible = normalize_surface(visible)
            normalized_root = normalize_surface(root)
            if normalized_visible.endswith(normalized_root) and len(normalized_visible) > len(
                normalized_root
            ):
                prefix_len = len(normalized_visible) - len(normalized_root)
                host = f"&{visible[:prefix_len]}{visible[prefix_len:]}"
                return f"{host}[{suffix}" if suffix else f"{host}["

        return f"{visible}[{suffix}" if suffix else f"{visible}["

    @staticmethod
    def _dulat_root_letters(dulat: str) -> str:
        token = (dulat or "").strip()
        if "," in token:
            token = token.split(",", 1)[0].strip()
        match = _VERB_ROOT_RE.match(token)
        if match is None:
            return ""
        body = match.group(1)
        body = re.sub(r"\([^)]*\)", "", body)
        return body.replace("-", "")

    @staticmethod
    def _analysis_suffix_marker(analysis: str) -> str:
        if "[" not in analysis:
            return ""
        payload = analysis.split("[", 1)[1]
        if not payload:
            return ""
        keep = []
        for prefix in (":d", ":l", ":r", ":pass"):
            if payload.startswith(prefix):
                keep.append(prefix)
        if "~" in payload:
            keep.append(payload[payload.index("~") :])
        return "".join(keep)

    @staticmethod
    def _features_for_form(form: str, decoded) -> tuple[str, str, str]:
        if form == "prefc.":
            return explicit_prefix_features(decoded)
        if form == "suffc.":
            return explicit_suffix_conjugation_features(decoded)
        if form == "impv.":
            person, gender, number = explicit_prefix_features(decoded)
            if person or gender or number:
                return person, gender, number
            return ("2", "", "")
        if form in {"act. ptcpl.", "pass. ptcpl.", "ptcpl."}:
            return ("", "m.", "sg.")
        return ("", "", "")

    def _pattern_candidates(
        self,
        *,
        row: TabletRow,
        stem: str,
        form: str,
    ) -> list[CompletedVariant]:
        analysis_variant = self._analysis_for_form(row, form, stem)
        decoded = decode_analysis(analysis_variant)
        explicit = self._features_for_form(form, decoded)
        state, case = self._state_case_for_form(form=form, analysis=analysis_variant)
        candidates = generate_verbal_candidates(
            surface=row.surface,
            dulat=row.dulat,
            stem=stem,
            conjugation=form,
        )
        if any(explicit) and not self._should_expand_under_specified_suffix_row(
            form=form,
            decoded=decoded,
            analysis=analysis_variant,
            candidates=candidates,
        ):
            return []
        variants: list[CompletedVariant] = []
        for candidate in candidates:
            variants.append(
                CompletedVariant(
                    analysis=candidate.analysis,
                    dulat=row.dulat,
                    gloss=row.gloss,
                    comment=row.comment,
                    features=build_verbal_bundle(
                        stem=stem,
                        form=form,
                        person=candidate.person,
                        gender=candidate.gender,
                        number=candidate.number,
                        state=state,
                        case=case,
                        source="morphology-pattern",
                        confidence="medium",
                    ),
                )
            )
        return variants

    @staticmethod
    def _should_expand_under_specified_suffix_row(
        *,
        form: str,
        decoded,
        analysis: str,
        candidates: list,
    ) -> bool:
        if form != "suffc.":
            return False
        if decoded.visible_suffix:
            return False
        if not candidates:
            return False
        return all(candidate.analysis != analysis for candidate in candidates)

    @staticmethod
    def _state_case_for_form(*, form: str, analysis: str) -> tuple[str, str]:
        if "ptcpl." not in (form or ""):
            return "", ""
        if "+" in (analysis or ""):
            return "cstr.", "nom."
        return "abs.", "nom."


def rewrite_row(row: TabletRow, completer: VerbalFeatureCompleter) -> TabletRow:
    if "vb" not in (row.pos or "").lower():
        return row
    variants = completer.complete_row(row)
    if len(variants) == 1:
        variant = variants[0]
        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=variant.analysis,
            dulat=variant.dulat,
            pos=render_pos(variant.features, fallback=row.pos),
            gloss=variant.gloss,
            comment=variant.comment,
        )
    return TabletRow(
        line_id=row.line_id,
        surface=row.surface,
        analysis="; ".join(variant.analysis for variant in variants),
        dulat="; ".join(variant.dulat for variant in variants),
        pos="; ".join(render_pos(variant.features, fallback=row.pos) for variant in variants),
        gloss="; ".join(variant.gloss for variant in variants),
        comment="; ".join(variant.comment for variant in variants),
    )
