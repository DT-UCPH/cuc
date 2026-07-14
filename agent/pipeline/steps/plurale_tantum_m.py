"""Normalize lexeme-final '-m' plurale-tantum noun analyses."""

from __future__ import annotations

import re
from typing import Optional

from pipeline.steps.analysis_utils import normalize_surface, reconstruct_surface_from_analysis
from pipeline.steps.base import RefinementStep, TabletRow
from pipeline.steps.dulat_gate import DulatMorphGate

_TOKEN_RE = re.compile(r"^(.*?)(?:\s*\(([IVX]+)\))?$")
_LEMMA_LETTER_RE = re.compile(r"[^A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]")
_UNSPLIT_FINAL_M_RE = re.compile(r"^(?P<stem>.+?)m(?P<hom>\([IVX]+\))?/$")
_SPLIT_FINAL_M_RE = re.compile(r"^(?P<base>.+?)(?P<hom>\([IVX]+\))?/m$")
_LEXICAL_M_NO_SPLIT_RE = re.compile(r"^(?P<base>.+?\(m)(?P<hom>\([IVX]+\))?/$")
_FALSE_POSITIVE_SPLIT_M_RE = re.compile(r"^(?P<stem>.+?)\(m(?P<hom>\([IVX]+\))?/m$")
_FALSE_POSITIVE_TRUNCATED_SPLIT_M_RE = re.compile(r"^(?P<stem>.+?)(?P<hom>\([IVX]+\))/m$")
_PL_TANT_RE = re.compile(
    r"(?:\bpl\.?\s*tant\b|\bplur(?:ale)?\.?\s*tant(?:um|u)?\b)\.?\??",
    flags=re.IGNORECASE,
)
_SUFFIX_SEGMENTS = ("hm", "hn", "km", "kn", "ny", "nm", "nn", "h", "k", "n", "y")


def _split_semicolon(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(";")]


def _split_comma(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(",")]


def _split_head_tail(analysis_variant: str) -> tuple[str, str]:
    value = (analysis_variant or "").strip()
    if not value:
        return "", ""
    cut = len(value)
    for marker in ("+", "~"):
        idx = value.find(marker)
        if idx != -1:
            cut = min(cut, idx)
    if cut >= len(value):
        return value, ""
    return value[:cut], value[cut:]


def _declared_lemma_letters(dulat_token: str) -> str:
    token = (dulat_token or "").strip()
    if not token or token.startswith("/") or token == "?":
        return ""
    if "," in token:
        token = token.split(",", 1)[0].strip()
    match = _TOKEN_RE.match(token)
    lemma = (match.group(1) if match else token).strip()
    return _LEMMA_LETTER_RE.sub("", normalize_surface(lemma)).lower()


def _host_surface(surface: str, tail: str) -> str:
    surface_norm = normalize_surface(surface)
    if not tail:
        return surface_norm
    tail_norm = normalize_surface(reconstruct_surface_from_analysis(tail))
    if tail_norm and surface_norm.endswith(tail_norm):
        return surface_norm[: -len(tail_norm)]
    return surface_norm


def _has_plurale_tantum_marker(value: str) -> bool:
    return _PL_TANT_RE.search(value or "") is not None


def _inject_plurale_tantum_marker(pos_variant: str) -> str:
    value = (pos_variant or "").strip()
    if not value or _has_plurale_tantum_marker(value):
        return value
    match = re.search(r"n\.\s*(?:[mf]\.)?", value, flags=re.IGNORECASE)
    if not match:
        return value
    return value[: match.end()] + " pl. tant." + value[match.end() :]


def _remove_plurale_tantum_marker(pos_variant: str) -> str:
    value = (pos_variant or "").strip()
    if not value:
        return value
    stripped = _PL_TANT_RE.sub("", value)
    if stripped == value:
        return value
    stripped = re.sub(r"\s+,", ",", stripped)
    stripped = re.sub(r",\s*", ", ", stripped)
    stripped = re.sub(r"\s{2,}", " ", stripped)
    return stripped.strip()


def _analysis_visible_letters(value: str) -> str:
    return normalize_surface(reconstruct_surface_from_analysis(value)).lower()


def _slot_key(token: str) -> str:
    return normalize_surface((token or "").strip()).lower()


def _inject_surface_y_before_terminal_m(head: str, host_surface_norm: str) -> str:
    if "&y" in head:
        return head
    if not head.endswith("/m"):
        return head
    if "(m" not in head:
        return head

    reconstructed = _analysis_visible_letters(head)
    if reconstructed == host_surface_norm:
        return head
    if not reconstructed:
        return head
    if not host_surface_norm.endswith("ym"):
        return head
    if reconstructed[:-1] + "y" + reconstructed[-1] != host_surface_norm:
        return head

    idx = head.rfind("(m")
    if idx == -1:
        return head
    return head[:idx] + "&y" + head[idx:]


class PluraleTantumMFixer(RefinementStep):
    """Normalize final '-m' plurale-tantum noun analyses and POS labels."""

    def __init__(self, gate: Optional[DulatMorphGate] = None) -> None:
        self._gate = gate

    @property
    def name(self) -> str:
        return "plurale-tantum-m"

    def refine_row(self, row: TabletRow) -> TabletRow:
        analysis_variants = _split_semicolon(row.analysis)
        if not analysis_variants:
            return row
        pos_variants = _split_semicolon(row.pos)
        dulat_variants = _split_semicolon(row.dulat)

        changed = False
        out_analysis: list[str] = []
        out_pos: list[str] = []
        slots_to_strip_pl_tant: set[str] = set()

        for idx, analysis_variant in enumerate(analysis_variants):
            pos_variant = pos_variants[idx] if idx < len(pos_variants) else ""
            dulat_variant = dulat_variants[idx] if idx < len(dulat_variants) else ""
            dulat_slot = _split_comma(dulat_variant)[0] if dulat_variant else ""
            pos_head = _split_comma(pos_variant)[0] if pos_variant else ""
            slot_key = _slot_key(dulat_slot)

            new_analysis = analysis_variant
            new_pos = pos_variant
            if self._is_target_variant(pos_head=pos_head, dulat_slot=dulat_slot):
                new_analysis = self._rewrite_variant(
                    analysis_variant=analysis_variant,
                    dulat_slot=dulat_slot,
                    surface=row.surface,
                )
                new_pos = _inject_plurale_tantum_marker(pos_variant)
            else:
                new_analysis, repaired = self._repair_non_plurale_tantum_variant(
                    analysis_variant=analysis_variant,
                    dulat_slot=dulat_slot,
                    pos_head=pos_head,
                    surface=row.surface,
                )
                if repaired and slot_key:
                    slots_to_strip_pl_tant.add(slot_key)
                if slot_key and self._should_strip_false_plurale_tantum_marker(
                    pos_variant=pos_variant,
                    pos_head=pos_head,
                    dulat_slot=dulat_slot,
                ):
                    slots_to_strip_pl_tant.add(slot_key)

            if new_analysis != analysis_variant or new_pos != pos_variant:
                changed = True
            out_analysis.append(new_analysis)
            out_pos.append(new_pos)

        if slots_to_strip_pl_tant:
            for idx, pos_variant in enumerate(out_pos):
                dulat_variant = dulat_variants[idx] if idx < len(dulat_variants) else ""
                dulat_slot = _split_comma(dulat_variant)[0] if dulat_variant else ""
                if _slot_key(dulat_slot) not in slots_to_strip_pl_tant:
                    continue
                stripped = _remove_plurale_tantum_marker(pos_variant)
                if stripped != pos_variant:
                    out_pos[idx] = stripped
                    changed = True

        if not changed:
            return row

        # Keep untouched POS variants if col5 has more variants than col3.
        if len(pos_variants) > len(out_pos):
            out_pos.extend(pos_variants[len(out_pos) :])

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis="; ".join(out_analysis),
            dulat=row.dulat,
            pos="; ".join(out_pos),
            gloss=row.gloss,
            comment=row.comment,
        )

    def _is_target_variant(self, pos_head: str, dulat_slot: str) -> bool:
        if not self._is_target_noun_pos(pos_head):
            return False
        if not _declared_lemma_letters(dulat_slot).endswith("m"):
            return False
        if self._gate is None or not hasattr(self._gate, "is_plurale_tantum_noun_token"):
            return False
        if not dulat_slot or dulat_slot == "?":
            return False
        return bool(self._gate.is_plurale_tantum_noun_token(dulat_slot))

    def _is_target_noun_pos(self, pos_head: str) -> bool:
        first = (pos_head or "").strip().lower()
        if not first.startswith("n."):
            return False
        if "num" in first:
            return False
        return True

    def _repair_non_plurale_tantum_variant(
        self,
        analysis_variant: str,
        dulat_slot: str,
        pos_head: str,
        surface: str,
    ) -> tuple[str, bool]:
        value = (analysis_variant or "").strip()
        if not value or value == "?" or "[" in value:
            return value, False
        if self._gate is None:
            return value, False
        if not self._is_target_noun_pos(pos_head):
            return value, False
        lemma_letters = _declared_lemma_letters(dulat_slot)
        if not lemma_letters.endswith("m"):
            return value, False
        if self._gate.is_plurale_tantum_noun_token(dulat_slot):
            return value, False

        head, tail = _split_head_tail(value)
        match = _FALSE_POSITIVE_SPLIT_M_RE.match(head)
        if match:
            stem = match.group("stem")
            hom = match.group("hom") or ""
            restored = f"{stem}m{hom}/" + tail
            restored_surface = normalize_surface(
                reconstruct_surface_from_analysis(restored)
            ).lower()
            if restored_surface == normalize_surface(surface).lower():
                return restored, True

        truncated = _FALSE_POSITIVE_TRUNCATED_SPLIT_M_RE.match(head)
        if not truncated:
            return value, False

        stem = truncated.group("stem")
        hom = truncated.group("hom") or ""
        restored = f"{stem}m{hom}/m" + tail
        restored_surface = normalize_surface(reconstruct_surface_from_analysis(restored)).lower()
        if restored_surface != normalize_surface(surface).lower():
            return value, False
        return restored, True

    def _should_strip_false_plurale_tantum_marker(
        self,
        pos_variant: str,
        pos_head: str,
        dulat_slot: str,
    ) -> bool:
        if not _has_plurale_tantum_marker(pos_variant):
            return False
        if not self._is_target_noun_pos(pos_head):
            return False
        if not _declared_lemma_letters(dulat_slot).endswith("m"):
            return False
        if self._gate is None or not hasattr(self._gate, "is_plurale_tantum_noun_token"):
            return False
        if not dulat_slot or dulat_slot == "?":
            return False
        return not bool(self._gate.is_plurale_tantum_noun_token(dulat_slot))

    def _rewrite_variant(self, analysis_variant: str, dulat_slot: str, surface: str) -> str:
        value = (analysis_variant or "").strip()
        if not value or value == "?":
            return value
        if "[" in value:
            return value

        lemma_letters = _declared_lemma_letters(dulat_slot)
        if not lemma_letters.endswith("m"):
            return value

        if self._gate is None or not self._gate.is_plural_token(dulat_slot):
            return value

        head, tail = _split_head_tail(value)
        if not head:
            return value

        surface_norm = normalize_surface(surface)
        if tail and _analysis_visible_letters(head) == surface_norm.lower():
            tail = ""

        host_surface_norm = _host_surface(surface=surface, tail=tail).lower()
        normalized_head = self._normalize_head_for_host(
            head=head,
            host_surface_norm=host_surface_norm,
            lemma_letters=lemma_letters,
        )
        candidate = normalized_head + tail
        candidate_surface = normalize_surface(reconstruct_surface_from_analysis(candidate)).lower()
        original_surface = normalize_surface(reconstruct_surface_from_analysis(value)).lower()
        if tail:
            normalized_tail = self._normalize_tail_for_surface(
                normalized_head=normalized_head,
                tail=tail,
                surface_norm=surface_norm.lower(),
            )
            if normalized_tail is not None:
                return normalized_head + normalized_tail
        if not tail:
            inferred_suffix = self._infer_missing_suffix(
                normalized_head=normalized_head,
                candidate_surface=candidate_surface,
                surface_norm=surface_norm.lower(),
            )
            if inferred_suffix is not None:
                return inferred_suffix
        if candidate_surface == surface_norm.lower():
            return candidate
        if original_surface == surface_norm.lower():
            return value
        return value

    def _normalize_tail_for_surface(
        self,
        normalized_head: str,
        tail: str,
        surface_norm: str,
    ) -> Optional[str]:
        if not tail.startswith("+n") or len(tail) <= 2:
            return None
        alt_tail = "+" + tail[2:]
        candidate = normalized_head + alt_tail
        reconstructed = normalize_surface(reconstruct_surface_from_analysis(candidate)).lower()
        if reconstructed == surface_norm:
            return alt_tail
        return None

    def _infer_missing_suffix(
        self,
        normalized_head: str,
        candidate_surface: str,
        surface_norm: str,
    ) -> Optional[str]:
        for seg in _SUFFIX_SEGMENTS:
            if len(surface_norm) <= len(seg):
                continue
            if not surface_norm.endswith(seg):
                continue
            if candidate_surface + seg != surface_norm:
                continue
            candidate = f"{normalized_head}+{seg}"
            reconstructed = normalize_surface(reconstruct_surface_from_analysis(candidate)).lower()
            if reconstructed == surface_norm:
                return candidate
        return None

    def _normalize_head_for_host(
        self, head: str, host_surface_norm: str, lemma_letters: str
    ) -> str:
        if host_surface_norm.endswith("m"):
            normalized_head = self._normalize_head_when_host_has_terminal_m(
                head=head,
                host_surface_norm=host_surface_norm,
                lemma_letters=lemma_letters,
            )
            return _inject_surface_y_before_terminal_m(
                head=normalized_head,
                host_surface_norm=host_surface_norm,
            )
        return self._normalize_head_when_host_drops_terminal_m(
            head=head,
            host_surface_norm=host_surface_norm,
            lemma_letters=lemma_letters,
        )

    def _normalize_head_when_host_has_terminal_m(
        self, head: str, host_surface_norm: str, lemma_letters: str
    ) -> str:
        lexical_unsplit = _LEXICAL_M_NO_SPLIT_RE.match(head)
        if lexical_unsplit:
            base = lexical_unsplit.group("base")
            hom = lexical_unsplit.group("hom") or ""
            return f"{base}{hom}/m"

        unsplit = _UNSPLIT_FINAL_M_RE.match(head)
        if unsplit:
            stem = unsplit.group("stem")
            hom = unsplit.group("hom") or ""
            return f"{stem}(m{hom}/m"

        split = _SPLIT_FINAL_M_RE.match(head)
        if not split:
            return head

        base = split.group("base")
        hom = split.group("hom") or ""
        if "(m" in base:
            return f"{base}{hom}/m"

        base_surface = _analysis_visible_letters(base)
        head_surface = _analysis_visible_letters(head)
        lemma_len = len(lemma_letters)
        missing_case = head_surface == host_surface_norm and len(base_surface) == max(
            0, lemma_len - 1
        )
        overshoot_case = head_surface == host_surface_norm + "m" and base_surface.endswith("m")
        allograph_case = (
            bool(head_surface)
            and len(base_surface) == max(0, lemma_len - 1)
            and head_surface[:-1] + "y" + head_surface[-1] == host_surface_norm
        )
        should_rewrite = missing_case or overshoot_case or allograph_case

        if not should_rewrite:
            return head

        stem = base[:-1] if overshoot_case and base.endswith("m") else base
        return f"{stem}(m{hom}/m"

    def _normalize_head_when_host_drops_terminal_m(
        self, head: str, host_surface_norm: str, lemma_letters: str
    ) -> str:
        lexical_unsplit = _LEXICAL_M_NO_SPLIT_RE.match(head)
        if lexical_unsplit:
            return head

        unsplit = _UNSPLIT_FINAL_M_RE.match(head)
        if unsplit:
            stem = unsplit.group("stem")
            hom = unsplit.group("hom") or ""
            return f"{stem}(m{hom}/"

        split = _SPLIT_FINAL_M_RE.match(head)
        if not split:
            return head

        base = split.group("base")
        hom = split.group("hom") or ""
        if "(m" in base:
            return f"{base}{hom}/"

        base_surface = _analysis_visible_letters(base)
        head_surface = _analysis_visible_letters(head)
        base_len_matches_lemma = len(base_surface) == max(0, len(lemma_letters) - 1)
        missing_case = base_len_matches_lemma
        overshoot_case = (
            head_surface == host_surface_norm + "m"
            and base_surface.endswith("m")
            and len(base_surface) >= len(host_surface_norm)
        )
        if not (missing_case or overshoot_case):
            return head

        stem = base[:-1] if overshoot_case and base.endswith("m") else base
        return f"{stem}(m{hom}/"
