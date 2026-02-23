"""Apply onomastic gloss overrides and canonical ʾ/ʿ transliteration."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from pipeline.steps.base import RefinementStep, TabletRow
from pipeline.steps.onomastic_overrides import OnomasticOverrideStore

_ONOMASTIC_POS_TAGS = ("DN", "PN", "TN", "MN", "GN")
_ONOMASTIC_CHAR_MAP = str.maketrans(
    {
        "ʔ": "ʾ",
        "ˀ": "ʾ",
        "ʕ": "ʿ",
        "ˁ": "ʿ",
    }
)


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";")]


def _split_comma(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(",")]


def _join_comma(values: list[str]) -> str:
    return ", ".join(value.strip() for value in values)


def _join_semicolon(values: list[str]) -> str:
    return "; ".join(value.strip() for value in values)


class OnomasticGlossOverrideFixer(RefinementStep):
    """Override name glosses from a centralized source file."""

    def __init__(
        self,
        overrides_path: Path | None = None,
        overrides: Dict[str, str] | None = None,
    ) -> None:
        self._overrides_path = overrides_path or Path("data/onomastic_gloss_overrides.tsv")
        if overrides is not None:
            self._store = OnomasticOverrideStore.from_gloss_map(overrides)
        else:
            self._store = OnomasticOverrideStore.from_tsv(self._overrides_path)

    @property
    def name(self) -> str:
        return "onomastic-gloss-override"

    def refine_row(self, row: TabletRow) -> TabletRow:
        dulat_variants = _split_semicolon(row.dulat)
        pos_variants = _split_semicolon(row.pos)
        gloss_variants = _split_semicolon(row.gloss)
        if not gloss_variants:
            return row

        n = len(gloss_variants)
        if len(dulat_variants) != n or len(pos_variants) != n:
            transformed = self._apply_variant_override(
                dulat_variant=row.dulat.strip(),
                pos_variant=row.pos.strip(),
                gloss_variant=row.gloss.strip(),
            )
            if transformed == row.gloss.strip():
                return row
            return TabletRow(
                line_id=row.line_id,
                surface=row.surface,
                analysis=row.analysis,
                dulat=row.dulat,
                pos=row.pos,
                gloss=transformed,
                comment=row.comment,
            )

        out_gloss: list[str] = []
        changed = False
        for i in range(n):
            transformed = self._apply_variant_override(
                dulat_variant=dulat_variants[i],
                pos_variant=pos_variants[i],
                gloss_variant=gloss_variants[i],
            )
            out_gloss.append(transformed)
            if transformed != gloss_variants[i]:
                changed = True

        if not changed:
            return row
        new_gloss = _join_semicolon(out_gloss)
        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=row.analysis,
            dulat=row.dulat,
            pos=row.pos,
            gloss=new_gloss,
            comment=row.comment,
        )

    def _apply_variant_override(
        self, dulat_variant: str, pos_variant: str, gloss_variant: str
    ) -> str:
        dulat_variant = dulat_variant.strip()
        pos_variant = pos_variant.strip()
        gloss_variant = gloss_variant.strip()
        onomastic_variant = self._is_onomastic_pos(pos_variant)
        override_gloss = self._store.get_gloss(dulat_variant)
        if override_gloss and onomastic_variant:
            return override_gloss

        dulat_slots = _split_comma(dulat_variant)
        pos_slots = _split_comma(pos_variant)
        slot_count = max(len(dulat_slots), len(pos_slots))
        if slot_count <= 1:
            if onomastic_variant:
                return self._normalize_onomastic_chars(gloss_variant)
            return gloss_variant

        gloss_slots = _split_comma(gloss_variant)
        if len(gloss_slots) != slot_count:
            # Conservative fallback: if slot alignment is uncertain, only apply
            # whole-variant normalization for clear onomastic POS values.
            if onomastic_variant:
                return self._normalize_onomastic_chars(gloss_variant)
            return gloss_variant

        changed = False
        for i in range(slot_count):
            d_slot = dulat_slots[i].strip() if i < len(dulat_slots) else ""
            p_slot = pos_slots[i].strip() if i < len(pos_slots) else ""
            g_slot = gloss_slots[i].strip()

            onomastic_slot = self._is_onomastic_pos(p_slot)
            override_slot = self._store.get_gloss(d_slot)
            if override_slot and onomastic_slot:
                new_slot = override_slot
            elif onomastic_slot:
                new_slot = self._normalize_onomastic_chars(g_slot)
            else:
                new_slot = g_slot
            if new_slot != g_slot:
                changed = True
            gloss_slots[i] = new_slot

        if not changed:
            return gloss_variant
        return _join_comma(gloss_slots)

    def _normalize_onomastic_chars(self, gloss: str) -> str:
        return (gloss or "").translate(_ONOMASTIC_CHAR_MAP)

    def _is_onomastic_pos(self, pos: str) -> bool:
        token = (pos or "").upper()
        return any(tag in token for tag in _ONOMASTIC_POS_TAGS)
