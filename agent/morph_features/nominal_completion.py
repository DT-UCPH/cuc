"""Deterministic nominal morphology completion from analysis + DULAT features."""

from __future__ import annotations

import re

from morph_features.dulat_feature_reader import DulatFeatureReader
from morph_features.feature_bundle_builder import build_nominal_bundle
from morph_features.pos_renderer import render_pos
from morph_features.types import CompletedVariant
from pipeline.steps.base import TabletRow

_NAME_CLASSES = ("DN", "PN", "RN", "TN", "GN", "MN")
_GENDER_RE = re.compile(r"(?<!\w)(m\.|f\.)(?!\w)")
_CASE_RE = re.compile(r"(?<!\w)(nom\.|gen\.|acc\.|acc\.\?)(?!\w)")


class NominalFeatureCompleter:
    """Complete and split nominal rows conservatively."""

    def __init__(self, feature_reader: DulatFeatureReader) -> None:
        self._reader = feature_reader

    def complete_row(self, row: TabletRow) -> list[CompletedVariant]:
        base_pos = self._base_pos(row.pos)
        if not base_pos:
            return [self._variant(row, base_pos="")]

        features = self._reader.read_surface_features(row.surface, row.dulat, row.pos)
        bundles: list[CompletedVariant] = []
        morphologies = features.morphologies or ("",)
        for morphology in morphologies:
            bundle = build_nominal_bundle(
                part_of_speech=base_pos,
                gender=self._infer_gender(row, morphology),
                number=self._infer_number(row, morphology, base_pos),
                state=self._infer_state(row, morphology),
                case=self._infer_case(row, morphology),
                source="analysis+dulat" if morphology else "analysis",
                confidence="high" if morphology else "medium",
                has_suffix="+" in (row.analysis or ""),
                suffix_person=self._suffix_person(row.analysis),
            )
            bundles.append(
                CompletedVariant(
                    analysis=row.analysis,
                    dulat=row.dulat,
                    gloss=row.gloss,
                    comment=row.comment,
                    features=bundle,
                )
            )

        deduped: list[CompletedVariant] = []
        seen: set[str] = set()
        for variant in bundles:
            rendered = render_pos(variant.features, fallback=row.pos)
            key = rendered
            if key in seen:
                continue
            seen.add(key)
            deduped.append(variant)
        return deduped or [self._variant(row, base_pos=base_pos)]

    @staticmethod
    def _variant(row: TabletRow, *, base_pos: str) -> CompletedVariant:
        bundle = build_nominal_bundle(part_of_speech=base_pos or row.pos, source="existing")
        return CompletedVariant(
            analysis=row.analysis,
            dulat=row.dulat,
            gloss=row.gloss,
            comment=row.comment,
            features=bundle,
        )

    @staticmethod
    def _base_pos(pos_text: str) -> str:
        text = (pos_text or "").strip()
        if text.startswith("n."):
            return "n."
        if text.startswith("adj."):
            return "adj."
        for name_class in _NAME_CLASSES:
            if name_class in text:
                return text.split()[0]
        return ""

    @staticmethod
    def _infer_gender(row: TabletRow, morphology: str) -> str:
        if "/t=" in (row.analysis or "") or "/t" in (row.analysis or ""):
            return "f."
        match = _GENDER_RE.search(morphology or "")
        if match:
            return match.group(1)
        match = _GENDER_RE.search(row.pos or "")
        return match.group(1) if match else ""

    @staticmethod
    def _infer_number(row: TabletRow, morphology: str, base_pos: str) -> str:
        morph = (morphology or "").lower()
        analysis = row.analysis or ""
        if "/tm" in analysis:
            return "du."
        if "/t=" in analysis or analysis.endswith("/m"):
            return "pl."
        if "du." in morph or "dual" in morph:
            return "du."
        if "pl." in morph or "plural" in morph:
            return "pl."
        if "sg." in morph or "singular" in morph:
            return "sg."
        if " pl. " in f" {row.pos} ":
            return "pl."
        if " sg. " in f" {row.pos} ":
            return "sg."
        if " du. " in f" {row.pos} ":
            return "du."
        if any(name_class in base_pos for name_class in _NAME_CLASSES):
            return "sg."
        return ""

    @staticmethod
    def _infer_state(row: TabletRow, morphology: str) -> str:
        morph = (morphology or "").lower()
        if "+" in (row.analysis or ""):
            return "cstr."
        if "cstr." in morph or "cst." in morph:
            return "cstr."
        if "abs." in morph:
            return "abs."
        return ""

    @staticmethod
    def _infer_case(row: TabletRow, morphology: str) -> str:
        match = _CASE_RE.search(morphology or "")
        if match:
            return match.group(1)
        match = _CASE_RE.search(row.pos or "")
        return match.group(1) if match else ""

    @staticmethod
    def _suffix_person(analysis: str) -> str:
        payload = (analysis or "").split("+", 1)
        if len(payload) < 2:
            return ""
        suffix = payload[1]
        if suffix.startswith(("k", "nk")):
            return "2"
        if suffix.startswith(("h", "nh", "nn")):
            return "3"
        if suffix.startswith(("y", "ny", "n=")):
            return "1"
        return ""


def rewrite_row(row: TabletRow, completer: NominalFeatureCompleter) -> TabletRow:
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
