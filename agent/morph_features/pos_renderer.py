"""Render POS strings from structured feature bundles."""

from __future__ import annotations

from morph_features.types import FeatureBundle


def render_pos(bundle: FeatureBundle, *, fallback: str = "") -> str:
    if bundle.part_of_speech != "vb":
        return fallback
    parts = ["vb"]
    if bundle.stem:
        parts.append(bundle.stem)
    if bundle.conjugation_or_form:
        parts.append(bundle.conjugation_or_form)
    if bundle.person:
        parts.append(bundle.person)
    if bundle.gender:
        parts.append(bundle.gender)
    if bundle.number:
        parts.append(bundle.number)
    return " ".join(part for part in parts if part).strip() or fallback
