"""Split mixed verb form POS options by analysis encoding conventions.

Conventions:
- finite forms (prefc./suffc./impv.) -> `[...]`
- infinitive (inf.) -> `!!...[/`
- participles (ptcpl.) -> `...[/`
"""

from __future__ import annotations

import re

from pipeline.steps.analysis_utils import normalize_surface, reconstruct_surface_from_analysis
from pipeline.steps.base import RefinementStep, TabletRow

_VB_POS_HEAD_RE = re.compile(r"^\s*vb\.?\b", flags=re.IGNORECASE)
_VERBAL_NOUN_POS_RE = re.compile(r"\bvb\.\s*n\.", flags=re.IGNORECASE)
_FORM_INFINITE_RE = re.compile(r"\binf\.", flags=re.IGNORECASE)
_FORM_PTCP_RE = re.compile(
    r"(?:\bact\.\s*ptcpl\.|\bpass\.\s*ptcpl\.|\bptcpl\.)",
    flags=re.IGNORECASE,
)
_FORM_FINITE_RE = re.compile(r"(?:\bprefc\.|\bsuffc\.|\bimpv\.)", flags=re.IGNORECASE)
_LETTER_RE = re.compile(r"[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]")
_I_ALEPH_DULAT_RE = re.compile(r"^\s*/ʔ-")
_I_ALEPH_SURFACE_VOWELS = frozenset({"a", "i", "u", "ả", "ỉ", "ủ"})
_ROOT_TOKEN_RE = re.compile(r"^/([^/]+)/")


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";")]


def _split_slash_options(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s*/\s*", (value or "").strip()) if part.strip()]


def _is_target_pos(value: str) -> bool:
    text = (value or "").strip()
    if not _VB_POS_HEAD_RE.search(text):
        return False
    if _VERBAL_NOUN_POS_RE.search(text):
        return False
    return True


def _requires_infinitive_encoding(pos_option: str) -> bool:
    text = (pos_option or "").strip()
    return bool(_FORM_INFINITE_RE.search(text))


def _requires_participle_encoding(pos_option: str) -> bool:
    text = (pos_option or "").strip()
    return bool(_FORM_PTCP_RE.search(text))


def _requires_finite_encoding(pos_option: str) -> bool:
    text = (pos_option or "").strip()
    return bool(_FORM_FINITE_RE.search(text))


def _strip_infinitive_marker(text: str) -> str:
    value = (text or "").strip()
    if value.startswith("!!"):
        return value[2:]
    return value


def _strip_finite_preformative(text: str) -> str:
    value = (text or "").strip()
    if not value.startswith("!"):
        return value
    closing = value.find("!", 1)
    if closing == -1:
        return value
    return value[closing + 1 :]


def _promote_leading_reconstructed_letter(text: str) -> str:
    value = (text or "").strip()
    if value.startswith("(ʔ"):
        return value
    if len(value) >= 2 and value.startswith("(") and _LETTER_RE.match(value[1]):
        return value[1:]
    return value


def _surface_matches_analysis(surface: str, analysis: str) -> bool:
    return normalize_surface(reconstruct_surface_from_analysis(analysis)) == normalize_surface(
        surface
    )


def _target_matches_analysis(target: str, analysis: str) -> bool:
    return normalize_surface(reconstruct_surface_from_analysis(analysis)) == normalize_surface(
        target
    )


def _extract_homonym_marker(text: str) -> str:
    match = re.search(r"\(([IVX]+)\)(?=\[)", (text or "").strip())
    return match.group(0) if match else ""


def _replace_host_with_surface(surface: str, analysis: str) -> str:
    text = (analysis or "").strip()
    bracket_idx = text.find("[")
    if bracket_idx == -1:
        return surface
    homonym = _extract_homonym_marker(text)
    suffix = text[bracket_idx:]
    return f"{surface}{homonym}{suffix}"


def _is_i_aleph_root(dulat: str) -> bool:
    return bool(_I_ALEPH_DULAT_RE.match((dulat or "").strip()))


def _visible_surface_vowel(surface: str) -> str:
    text = (surface or "").strip()
    if not text:
        return ""
    return text[0]


def _surface_tail_matches_analysis(surface: str, analysis: str) -> bool:
    text = (surface or "").strip()
    if len(text) < 2:
        return False
    return _target_matches_analysis(text[1:], analysis)


def _variant_root_radicals(dulat_var: str) -> tuple[str, str, str] | None:
    token = (dulat_var or "").strip()
    if not token:
        return None
    if "," in token:
        token = token.split(",", 1)[0].strip()
    match = _ROOT_TOKEN_RE.match(token)
    if not match:
        return None
    parts = [part.strip() for part in match.group(1).split("-") if part.strip()]
    if len(parts) != 3:
        return None
    if not all(_LETTER_RE.search(part) for part in parts):
        return None
    return parts[0], parts[1], parts[2]


def _restore_weak_final_nonfinite_core(surface: str, core: str, dulat: str) -> str | None:
    radicals = _variant_root_radicals(dulat)
    if radicals is None:
        return None
    _first, _second, third = radicals
    if third not in {"y", "w"}:
        return None

    for text in _nonfinite_core_variants(core):
        bracket_idx = text.find("[")
        if bracket_idx == -1:
            continue
        prefix = text[:bracket_idx]
        suffix = text[bracket_idx:]

        homonym = ""
        match = re.search(r"\(([IVX]+)\)$", prefix)
        if match:
            homonym = match.group(0)
            host = prefix[: match.start()]
        else:
            host = prefix

        if host.endswith(third) or f"({third}" in host:
            continue

        candidate = f"{host}({third}{homonym}{suffix}"
        if _target_matches_analysis(surface, candidate):
            return candidate

    return None


def _nonfinite_core_variants(core: str) -> list[str]:
    text = (core or "").strip()
    if not text:
        return []
    variants = [text]
    bracket_idx = text.find("[")
    if bracket_idx != -1 and bracket_idx < len(text) - 1:
        truncated = text[: bracket_idx + 1]
        if truncated not in variants:
            variants.append(truncated)
    return variants


def _i_aleph_surface_targets(surface: str) -> list[str]:
    text = (surface or "").strip()
    if not text:
        return []
    targets = [text]
    if text.startswith("m") and len(text) > 1:
        targets.append(text[1:])
    return targets


def _restore_i_aleph_nonfinite_core(surface: str, core: str, dulat: str) -> str | None:
    if not _is_i_aleph_root(dulat):
        return None

    for text in _nonfinite_core_variants(core):
        for target in _i_aleph_surface_targets(surface):
            if text.startswith("(ʔ") and _target_matches_analysis(target, text):
                return text

            if text.startswith("ʔ&"):
                candidate = f"({text}"
                if _target_matches_analysis(target, candidate):
                    return candidate

            vowel = _visible_surface_vowel(target)
            if vowel and vowel in _I_ALEPH_SURFACE_VOWELS:
                if text.startswith("ʔ"):
                    bare_aleph_candidate = f"(ʔ&{vowel}{text[1:]}"
                    if _target_matches_analysis(target, bare_aleph_candidate):
                        return bare_aleph_candidate

                full_candidate = f"(ʔ&{text}"
                if _target_matches_analysis(target, full_candidate):
                    return full_candidate

                if _surface_tail_matches_analysis(target, text):
                    tail_candidate = f"(ʔ&{vowel}{text}"
                    if _target_matches_analysis(target, tail_candidate):
                        return tail_candidate

    return None


def _canonicalize_nonfinite_core(surface: str, analysis: str, dulat: str) -> str:
    stripped = _strip_infinitive_marker(analysis)
    stripped = _strip_finite_preformative(stripped)

    aleph_restored = _restore_i_aleph_nonfinite_core(surface, stripped, dulat)
    if aleph_restored is not None:
        return aleph_restored

    weak_final_restored = _restore_weak_final_nonfinite_core(surface, stripped, dulat)
    if weak_final_restored is not None:
        return weak_final_restored

    stripped = _promote_leading_reconstructed_letter(stripped)
    if _surface_matches_analysis(surface, stripped):
        return stripped
    fallback = _replace_host_with_surface(surface, stripped)
    if _surface_matches_analysis(surface, fallback):
        return fallback
    return stripped


def _to_nonfinite_encoding(surface: str, analysis: str, dulat: str) -> str:
    text = _canonicalize_nonfinite_core(surface, analysis, dulat)
    if "[/" in text:
        return text
    if "[" not in text:
        return text
    return text.replace("[", "[/", 1)


def _to_infinitive_encoding(surface: str, analysis: str, dulat: str) -> str:
    text = _to_nonfinite_encoding(surface, analysis, dulat)
    if text.startswith("!!"):
        return text
    return f"!!{text}"


def _to_participle_encoding(surface: str, analysis: str, dulat: str) -> str:
    text = _to_nonfinite_encoding(surface, analysis, dulat)
    text = _strip_infinitive_marker(text)
    return text


def _to_finite_encoding(analysis: str) -> str:
    text = (analysis or "").strip()
    if "[/" in text:
        text = text.replace("[/", "[", 1)
    text = _strip_infinitive_marker(text)
    return text


def _join_options(options: list[str]) -> str:
    return " / ".join(options)


class VerbFormEncodingSplitFixer(RefinementStep):
    """Ensure POS form options align with `[` vs `[/` verbal analysis encoding."""

    @property
    def name(self) -> str:
        return "verb-form-encoding-split"

    def refine_row(self, row: TabletRow) -> TabletRow:
        analysis_variants = _split_semicolon(row.analysis)
        dulat_variants = _split_semicolon(row.dulat)
        pos_variants = _split_semicolon(row.pos)
        gloss_variants = _split_semicolon(row.gloss)

        if not analysis_variants or not pos_variants:
            return row

        changed = False
        out_analysis: list[str] = []
        out_dulat: list[str] = []
        out_pos: list[str] = []
        out_gloss: list[str] = []

        for idx, analysis in enumerate(analysis_variants):
            dulat = (
                dulat_variants[idx]
                if idx < len(dulat_variants)
                else (dulat_variants[0] if dulat_variants else "")
            )
            pos = (
                pos_variants[idx]
                if idx < len(pos_variants)
                else (pos_variants[0] if pos_variants else "")
            )
            gloss = (
                gloss_variants[idx]
                if idx < len(gloss_variants)
                else (gloss_variants[0] if gloss_variants else "")
            )

            if not _is_target_pos(pos):
                out_analysis.append(analysis)
                out_dulat.append(dulat)
                out_pos.append(pos)
                out_gloss.append(gloss)
                continue

            options = _split_slash_options(pos)
            if len(options) <= 1:
                normalized_analysis = analysis
                if options and _requires_infinitive_encoding(options[0]):
                    converted = _to_infinitive_encoding(row.surface, analysis, dulat)
                    if converted != analysis:
                        changed = True
                    normalized_analysis = converted
                elif options and _requires_participle_encoding(options[0]):
                    converted = _to_participle_encoding(row.surface, analysis, dulat)
                    if converted != analysis:
                        changed = True
                    normalized_analysis = converted
                elif options and _requires_finite_encoding(options[0]):
                    converted = _to_finite_encoding(analysis)
                    if converted != analysis:
                        changed = True
                    normalized_analysis = converted

                out_analysis.append(normalized_analysis)
                out_dulat.append(dulat)
                out_pos.append(pos)
                out_gloss.append(gloss)
                continue

            finite_options: list[str] = []
            infinitive_options: list[str] = []
            participle_options: list[str] = []
            neutral_options: list[str] = []
            for option in options:
                finite = _requires_finite_encoding(option)
                infinitive = _requires_infinitive_encoding(option)
                participle = _requires_participle_encoding(option)
                if finite and not infinitive and not participle:
                    finite_options.append(option)
                elif infinitive and not finite and not participle:
                    infinitive_options.append(option)
                elif participle and not finite and not infinitive:
                    participle_options.append(option)
                elif finite or infinitive or participle:
                    neutral_options.append(option)
                else:
                    neutral_options.append(option)

            has_finite = bool(finite_options)
            has_infinitive = bool(infinitive_options)
            has_participle = bool(participle_options)
            active_groups = sum((has_finite, has_infinitive, has_participle))

            # No mixed form classes -> keep row-level variant and normalize encoding if needed.
            if active_groups <= 1:
                normalized_analysis = analysis
                normalized_pos = pos
                if has_infinitive:
                    normalized_pos = _join_options(infinitive_options + neutral_options)
                    converted = _to_infinitive_encoding(row.surface, analysis, dulat)
                    if converted != analysis:
                        changed = True
                    normalized_analysis = converted
                elif has_participle:
                    normalized_pos = _join_options(participle_options + neutral_options)
                    converted = _to_participle_encoding(row.surface, analysis, dulat)
                    if converted != analysis:
                        changed = True
                    normalized_analysis = converted
                elif has_finite:
                    normalized_pos = _join_options(finite_options + neutral_options)
                    converted = _to_finite_encoding(analysis)
                    if converted != analysis:
                        changed = True
                    normalized_analysis = converted

                out_analysis.append(normalized_analysis)
                out_dulat.append(dulat)
                out_pos.append(normalized_pos)
                out_gloss.append(gloss)
                continue

            # Mixed form classes -> split into aligned variants.
            finite_pos = _join_options(finite_options + neutral_options)
            infinitive_pos = _join_options(infinitive_options + neutral_options)
            participle_pos = _join_options(participle_options + neutral_options)
            finite_analysis = _to_finite_encoding(analysis)
            infinitive_analysis = _to_infinitive_encoding(row.surface, analysis, dulat)
            participle_analysis = _to_participle_encoding(row.surface, analysis, dulat)

            if has_finite:
                out_analysis.append(finite_analysis)
                out_dulat.append(dulat)
                out_pos.append(finite_pos)
                out_gloss.append(gloss)

            if has_infinitive:
                out_analysis.append(infinitive_analysis)
                out_dulat.append(dulat)
                out_pos.append(infinitive_pos)
                out_gloss.append(gloss)

            if has_participle:
                out_analysis.append(participle_analysis)
                out_dulat.append(dulat)
                out_pos.append(participle_pos)
                out_gloss.append(gloss)

            changed = True

        deduped: list[tuple[str, str, str, str]] = []
        for item in zip(out_analysis, out_dulat, out_pos, out_gloss):
            if item in deduped:
                changed = True
                continue
            deduped.append(item)

        final_analysis = "; ".join(item[0] for item in deduped)
        final_dulat = "; ".join(item[1] for item in deduped)
        final_pos = "; ".join(item[2] for item in deduped)
        final_gloss = "; ".join(item[3] for item in deduped)

        if (
            not changed
            and final_analysis == row.analysis
            and final_dulat == row.dulat
            and final_pos == row.pos
            and final_gloss == row.gloss
        ):
            return row

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=final_analysis,
            dulat=final_dulat,
            pos=final_pos,
            gloss=final_gloss,
            comment=row.comment,
        )
