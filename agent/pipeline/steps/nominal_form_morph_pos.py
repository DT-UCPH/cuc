"""Refine nominal/adjectival POS from exact DULAT form morphology."""

from __future__ import annotations

import re
from typing import Optional

from pipeline.steps.base import RefinementStep, TabletRow
from pipeline.steps.dulat_gate import DulatMorphGate

_MASC_RE = re.compile(r"m\.", flags=re.IGNORECASE)
_FEM_RE = re.compile(r"f\.", flags=re.IGNORECASE)
_DUAL_POS_RE = re.compile(r"du\.", flags=re.IGNORECASE)
_PLURAL_POS_RE = re.compile(r"(?:pl\.|plur(?:al)?)", flags=re.IGNORECASE)
_SINGULAR_POS_RE = re.compile(r"(?:sg\.|sing(?:ular)?)", flags=re.IGNORECASE)
_CONSTRUCT_POS_RE = re.compile(r"\bcst(?:r)?\.?", flags=re.IGNORECASE)
_NUMBER_TOKEN_RE = re.compile(
    r"(?<!\w)(?:sg\.|sing(?:ular)?|pl\.|plur(?:al)?|du\.)(?=$|[\s,;/])",
    flags=re.IGNORECASE,
)
_FEM_SING_ANALYSIS_RE = re.compile(r"/t(?=\s*$|[+~])")
_FEM_PL_ANALYSIS_RE = re.compile(r"/t=(?=\s*$|[+~])")


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";")]


def _split_comma(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(",")]


def _has_feminine_marker(morphologies: set[str]) -> bool:
    for morph in morphologies:
        parts = _split_comma((morph or "").lower())
        if any(part == "f." for part in parts):
            return True
    return False


def _has_dual_marker(morphologies: set[str]) -> bool:
    for morph in morphologies:
        parts = _split_comma((morph or "").lower())
        if any(part in {"du.", "dual"} for part in parts):
            return True
    return False


def _has_singular_marker(morphologies: set[str]) -> bool:
    for morph in morphologies:
        parts = _split_comma((morph or "").lower())
        if any(part in {"sg.", "sing", "singular"} for part in parts):
            return True
    return False


def _has_plural_marker(morphologies: set[str]) -> bool:
    for morph in morphologies:
        parts = _split_comma((morph or "").lower())
        if any(part in {"pl.", "plur", "plural"} for part in parts):
            return True
    return False


def _has_construct_marker(morphologies: set[str]) -> bool:
    for morph in morphologies:
        parts = _split_comma((morph or "").lower())
        if any(part in {"cstr.", "cstr", "cst.", "cst"} for part in parts):
            return True
    return False


def _number_options_from_morphologies(morphologies: set[str]) -> list[str]:
    out: set[str] = set()
    for morph in morphologies:
        text = (morph or "").lower()
        if not text:
            continue
        if _has_singular_marker({text}):
            out.add("sg.")
        if _has_plural_marker({text}):
            out.add("pl.")
        if _has_dual_marker({text}):
            out.add("du.")
    order = ["sg.", "pl.", "du."]
    return [marker for marker in order if marker in out]


def _construct_by_number_from_morphologies(morphologies: set[str]) -> dict[str, bool]:
    out: dict[str, bool] = {}
    for morph in morphologies:
        text = (morph or "").lower()
        if not text:
            continue
        is_construct = _has_construct_marker({text})
        if not is_construct:
            continue
        if _has_singular_marker({text}):
            out["sg."] = True
        if _has_plural_marker({text}):
            out["pl."] = True
        if _has_dual_marker({text}):
            out["du."] = True
    return out


def _pos_gender(head: str) -> str:
    lower = (head or "").lower()
    if "f." in lower:
        return "f."
    if "m." in lower:
        return "m."
    return ""


class NominalFormMorphPosFixer(RefinementStep):
    """Set POS gender/number markers from exact DULAT form morphology."""

    def __init__(self, gate: Optional[DulatMorphGate] = None) -> None:
        self._gate = gate

    @property
    def name(self) -> str:
        return "nominal-form-morph-pos"

    def refine_row(self, row: TabletRow) -> TabletRow:
        if self._gate is None:
            return row

        pos_variants = _split_semicolon(row.pos)
        if not pos_variants:
            return row

        analysis_variants = _split_semicolon(row.analysis)
        dulat_variants = _split_semicolon(row.dulat)
        out_pos: list[str] = []
        changed = False

        for idx, pos_variant in enumerate(pos_variants):
            analysis_variant = analysis_variants[idx] if idx < len(analysis_variants) else ""
            dulat_variant = dulat_variants[idx] if idx < len(dulat_variants) else ""
            dulat_head = _split_comma(dulat_variant)[0] if dulat_variant else ""
            rewritten = self._rewrite_pos(
                analysis_variant=analysis_variant,
                pos_variant=pos_variant,
                dulat_head=dulat_head,
                surface=row.surface,
            )
            out_pos.append(rewritten)
            if rewritten != pos_variant:
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

    def _rewrite_pos(
        self,
        analysis_variant: str,
        pos_variant: str,
        dulat_head: str,
        surface: str,
    ) -> str:
        value = (pos_variant or "").strip()
        if not value:
            return value

        parts = _split_comma(value)
        if not parts:
            return value
        head = parts[0].strip()
        head_lower = head.lower()
        if not (
            head_lower.startswith("n.")
            or head_lower.startswith("adj.")
            or head_lower.startswith("num.")
        ):
            return value

        morphologies = self._gate.surface_morphologies(dulat_head, surface=surface)
        if not morphologies:
            return _with_number_from_feminine_split(value, analysis_variant)

        token_genders = set()
        token_gender_getter = getattr(self._gate, "token_genders", None)
        if callable(token_gender_getter):
            token_genders = set(token_gender_getter(dulat_head))

        has_fem = _has_feminine_marker(morphologies)
        has_dual = _has_dual_marker(morphologies)
        has_singular = _has_singular_marker(morphologies)
        has_plural = _has_plural_marker(morphologies)
        number_options = _number_options_from_morphologies(morphologies)
        construct_by_number = _construct_by_number_from_morphologies(morphologies)
        dual_unambiguous = has_dual and not has_singular and not has_plural
        if (
            not has_fem
            and not has_dual
            and not has_singular
            and not has_plural
            and not token_genders
        ):
            return value

        rewritten_head = head
        if has_fem and "f." not in rewritten_head.lower():
            if _MASC_RE.search(rewritten_head):
                rewritten_head = _MASC_RE.sub("f.", rewritten_head)
            else:
                rewritten_head = f"{rewritten_head} f."
        elif not has_fem:
            # Prevent false fem reassignments from suffixal forms like "suff.".
            # If DULAT token gender is unambiguous masculine, normalize `n. f.` -> `n. m.`.
            if token_genders == {"m."} and _pos_gender(rewritten_head) == "f.":
                rewritten_head = _FEM_RE.sub("m.", rewritten_head)

        # Add dual marker only when dual is not competing with explicit sg/pl
        # for the same exact surface form.
        if dual_unambiguous and "du." not in rewritten_head.lower():
            rewritten_head = f"{rewritten_head} du."
        elif not dual_unambiguous and "du." in rewritten_head.lower() and len(number_options) <= 1:
            rewritten_head = _DUAL_POS_RE.sub("", rewritten_head)
            rewritten_head = re.sub(r"\s{2,}", " ", rewritten_head).strip()

        if rewritten_head == head:
            out = value
        elif len(parts) == 1:
            out = rewritten_head
        else:
            out = ", ".join([rewritten_head, *parts[1:]])

        out = _with_ambiguous_number_options(
            out,
            analysis_variant,
            number_options,
            construct_by_number=construct_by_number,
        )
        return _with_number_from_feminine_split(out, analysis_variant)


def _with_number_from_feminine_split(pos_value: str, analysis_variant: str) -> str:
    """Inject missing sg./pl. markers when analysis explicitly uses /t or /t=."""
    value = (pos_value or "").strip()
    analysis = (analysis_variant or "").strip()
    if not value or not analysis:
        return value

    if _FEM_PL_ANALYSIS_RE.search(analysis):
        return _ensure_number_marker(value, target="pl")
    if _FEM_SING_ANALYSIS_RE.search(analysis):
        return _ensure_number_marker(value, target="sg")
    return value


def _ensure_number_marker(pos_value: str, target: str) -> str:
    value = (pos_value or "").strip()
    if not value:
        return value

    head, sep, rest = value.partition(",")
    head_text = head.strip()
    if _DUAL_POS_RE.search(head_text):
        return value
    if _PLURAL_POS_RE.search(head_text):
        return value
    if _SINGULAR_POS_RE.search(head_text):
        return value

    if target == "pl":
        head_text = f"{head_text} pl."
    elif target == "sg":
        head_text = f"{head_text} sg."
    else:
        return value

    if not sep:
        return head_text
    return f"{head_text}, {rest.strip()}"


def _with_ambiguous_number_options(
    pos_value: str,
    analysis_variant: str,
    number_options: list[str],
    construct_by_number: Optional[dict[str, bool]] = None,
) -> str:
    """Render POS number alternatives when DULAT form number is ambiguous."""
    value = (pos_value or "").strip()
    if not value:
        return value
    if len(number_options) <= 1:
        return value
    # Feminine split endings already encode sg/pl in analysis; keep explicit mapping
    # to _with_number_from_feminine_split instead of generating ambiguous lists here.
    analysis = (analysis_variant or "").strip()
    if _FEM_PL_ANALYSIS_RE.search(analysis) or _FEM_SING_ANALYSIS_RE.search(analysis):
        return value

    head, sep, rest = value.partition(",")
    head_options = [part.strip() for part in re.split(r"\s*/\s*", head) if part.strip()]
    if not head_options:
        head_options = [head.strip()]

    base_options = _dedupe([_strip_number_marker(part) for part in head_options])
    base_options = [part for part in base_options if part]
    if not base_options:
        return value

    # Keep behavior conservative for genuinely different POS bases.
    if len(base_options) > 1:
        deduped_head = " / ".join(_dedupe(head_options))
        if not sep:
            return deduped_head
        return f"{deduped_head}, {rest.strip()}"

    base = base_options[0]
    construct_by_number = dict(construct_by_number or {})
    rendered: list[str] = []
    for marker in number_options:
        option = f"{base} {marker}".strip()
        if marker == "pl." and construct_by_number.get(marker):
            option = _append_construct_marker(option)
        rendered.append(option)
    rendered = _dedupe(rendered)
    new_head = " / ".join(rendered)
    if not sep:
        return new_head
    return f"{new_head}, {rest.strip()}"


def _strip_number_marker(text: str) -> str:
    value = (text or "").strip()
    if not value:
        return value
    value = _NUMBER_TOKEN_RE.sub("", value)
    value = _CONSTRUCT_POS_RE.sub("", value)
    value = re.sub(r"\s{2,}", " ", value).strip()
    return value


def _normalize_construct_pos(value: str) -> str:
    return _CONSTRUCT_POS_RE.sub("cstr.", value or "")


def _append_construct_marker(value: str) -> str:
    text = _normalize_construct_pos((value or "").strip())
    if not text:
        return text
    if _CONSTRUCT_POS_RE.search(text):
        return text
    return f"{text} cstr."


def _dedupe(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        item = (value or "").strip()
        if not item:
            continue
        if item in out:
            continue
        out.append(item)
    return out
