"""Rewrite DULAT note-backed enclitic `-m` forms to `~m` encoding."""

from __future__ import annotations

import re
from pathlib import Path

from pipeline.config.dulat_form_note_index import DulatFormNoteIndex
from pipeline.steps.analysis_utils import normalize_surface, reconstruct_surface_from_analysis
from pipeline.steps.base import (
    RefinementStep,
    StepResult,
    TabletRow,
    is_separator_line,
    is_unresolved,
    normalize_separator_row,
    parse_tsv_line,
)
from pipeline.steps.dulat_gate import DulatMorphGate
from pipeline.steps.verb_form_encoding_split import (
    _requires_finite_encoding,
    _requires_infinitive_encoding,
    _requires_participle_encoding,
    _split_slash_options,
    _to_finite_encoding,
    _to_infinitive_encoding,
    _to_participle_encoding,
)

_NUMBER_TOKEN_RE = re.compile(r"(?:sg\.|pl\.|du\.)", flags=re.IGNORECASE)
_NOUNISH_HEAD_RE = re.compile(r"^\s*(?:n\.|adj\.|num\.)", flags=re.IGNORECASE)


class DulatEncliticMFixer(RefinementStep):
    """Apply `~m` when an exact DULAT form note marks enclitic `-m`."""

    def __init__(
        self,
        dulat_db: Path,
        note_index: DulatFormNoteIndex | None = None,
        gate: DulatMorphGate | None = None,
    ) -> None:
        self._note_index = note_index or DulatFormNoteIndex.from_sqlite(dulat_db)
        self._gate = gate or DulatMorphGate(dulat_db)

    @property
    def name(self) -> str:
        return "dulat-enclitic-m"

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        out_lines: list[str] = []
        group_rows: list[TabletRow] = []
        group_raws: list[str] = []
        group_key: tuple[str, str] | None = None
        rows_processed = 0
        rows_changed = 0

        def flush_group() -> None:
            nonlocal group_rows, group_raws, group_key, rows_changed
            if not group_rows:
                return
            refined_rows = self._refine_group(group_rows)
            refined_lines = [row.to_tsv() for row in refined_rows]
            if refined_lines != group_raws:
                rows_changed += max(len(refined_lines), len(group_raws))
            out_lines.extend(refined_lines)
            group_rows = []
            group_raws = []
            group_key = None

        for raw in lines:
            if not raw.strip():
                flush_group()
                out_lines.append(raw)
                continue
            if is_separator_line(raw):
                flush_group()
                out_lines.append(normalize_separator_row(raw))
                continue

            row = parse_tsv_line(raw)
            if row is None:
                flush_group()
                out_lines.append(raw)
                continue

            rows_processed += 1
            if is_unresolved(row):
                flush_group()
                out_lines.append(raw)
                continue

            key = (row.line_id.strip(), row.surface.strip())
            if group_key is None or key == group_key:
                group_key = key
                group_rows.append(row)
                group_raws.append(raw)
                continue

            flush_group()
            group_key = key
            group_rows.append(row)
            group_raws.append(raw)

        flush_group()
        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)

    def refine_row(self, row: TabletRow) -> TabletRow:
        refined_rows = self._refine_group([row])
        if len(refined_rows) == 1:
            return refined_rows[0]
        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis="; ".join(item.analysis for item in refined_rows),
            dulat="; ".join(item.dulat for item in refined_rows),
            pos="; ".join(item.pos for item in refined_rows),
            gloss="; ".join(item.gloss for item in refined_rows),
            comment=row.comment,
        )

    def _refine_group(self, rows: list[TabletRow]) -> list[TabletRow]:
        if not rows:
            return rows
        surface = rows[0].surface.strip()
        if not surface or not surface.endswith("m"):
            return rows

        existing_enclitic_variants = {
            (row.dulat.strip(), row.gloss.strip()) for row in rows if "~m" in (row.analysis or "")
        }
        seen: set[tuple[str, str, str, str]] = set()
        out_rows: list[TabletRow] = []

        for row in rows:
            analysis = row.analysis.strip()
            dulat = row.dulat.strip()
            pos = row.pos.strip()
            gloss = row.gloss.strip()

            note_morphologies = self._note_index.enclitic_m_morphologies_for_surface(
                surface=surface,
                dulat_token=dulat,
            )
            all_morphologies = self._gate.surface_morphologies(dulat, surface=surface)
            has_note_backing = bool(note_morphologies)
            plain_morphologies = {
                morph.lower().strip()
                for morph in all_morphologies
                if morph.lower().strip() not in note_morphologies
            }
            has_plain_variant = bool(plain_morphologies)

            if not has_note_backing:
                _append_group_row(out_rows, seen, row)
                continue

            enclitic_analysis = _to_enclitic_m_analysis(
                surface=surface,
                analysis=analysis,
                dulat=dulat,
                pos=pos,
            )
            enclitic_pos = _rewrite_pos_for_enclitic_variant(pos, note_morphologies)

            if has_plain_variant:
                if (
                    "~m" not in analysis
                    and (dulat, gloss) not in existing_enclitic_variants
                    and _should_add_synthetic_enclitic_variant(
                        pos=pos,
                        plain_morphologies=plain_morphologies,
                        note_morphologies=note_morphologies,
                    )
                ):
                    _append_group_row(
                        out_rows,
                        seen,
                        TabletRow(
                            line_id=row.line_id,
                            surface=row.surface,
                            analysis=enclitic_analysis,
                            dulat=dulat,
                            pos=enclitic_pos,
                            gloss=gloss,
                            comment=row.comment,
                        ),
                    )
                    existing_enclitic_variants.add((dulat, gloss))
                _append_group_row(out_rows, seen, row)
                continue

            _append_group_row(
                out_rows,
                seen,
                TabletRow(
                    line_id=row.line_id,
                    surface=row.surface,
                    analysis=enclitic_analysis,
                    dulat=dulat,
                    pos=enclitic_pos,
                    gloss=gloss,
                    comment=row.comment,
                ),
            )

        return out_rows


def _append_group_row(
    out_rows: list[TabletRow],
    seen: set[tuple[str, str, str, str]],
    row: TabletRow,
) -> None:
    key = (
        row.analysis.strip(),
        row.dulat.strip(),
        row.pos.strip(),
        row.gloss.strip(),
    )
    if key in seen:
        return
    seen.add(key)
    out_rows.append(row)


def _to_enclitic_m_analysis(*, surface: str, analysis: str, dulat: str, pos: str) -> str:
    text = _normalize_variant_encoding(surface=surface, analysis=analysis, dulat=dulat, pos=pos)
    if "+m" in text:
        return text
    if not text or "~m" in text:
        return _normalize_known_weak_imperative_with_enclitic(
            surface=surface,
            dulat=dulat,
            pos=pos,
            analysis=text,
        )

    homonym_slash_match = re.search(r"m(\([IVX]+\)/)(?=$|[+~])", text)
    if homonym_slash_match:
        start = homonym_slash_match.start()
        suffix = homonym_slash_match.group(1)
        return _normalize_known_weak_imperative_with_enclitic(
            surface=surface,
            dulat=dulat,
            pos=pos,
            analysis=f"{text[:start]}{suffix}~m",
        )

    slash_match = re.search(r"m(?=/)", text)
    if slash_match:
        start = slash_match.start()
        return _normalize_known_weak_imperative_with_enclitic(
            surface=surface,
            dulat=dulat,
            pos=pos,
            analysis=f"{text[:start]}{text[start + 1 :]}~m",
        )

    for old, new in (("[m", "[~m"), ("/m", "/~m"), ("m[", "[~m")):
        if old in text:
            return _normalize_known_weak_imperative_with_enclitic(
                surface=surface,
                dulat=dulat,
                pos=pos,
                analysis=text.replace(old, new, 1),
            )

    if text.endswith("m"):
        return _normalize_known_weak_imperative_with_enclitic(
            surface=surface,
            dulat=dulat,
            pos=pos,
            analysis=f"{text[:-1]}~m",
        )

    return _normalize_known_weak_imperative_with_enclitic(
        surface=surface,
        dulat=dulat,
        pos=pos,
        analysis=f"{text}~m",
    )


def _normalize_known_weak_imperative_with_enclitic(
    *,
    surface: str,
    dulat: str,
    pos: str,
    analysis: str,
) -> str:
    """Normalize known weak imperative + enclitic shapes to canonical encoding."""
    text = analysis or ""
    if "~m" not in text:
        return analysis
    surface_norm = normalize_surface(surface).lower()
    pos_norm = (pos or "").lower()
    dulat_norm = (dulat or "").strip()
    if "vb" not in pos_norm or "impv." not in pos_norm:
        return analysis

    if surface_norm == "atm" and dulat_norm == "/ʔ-t-w/":
        return "!!(ʔ&at(w[~m"

    # Weak-final-y imperative + enclitic m: keep hidden y reconstructed as (y.
    # Example: ṯny[~m -> ṯn(y[~m for surface ṯnm.
    if surface_norm.endswith("m") and not surface_norm.endswith("ym"):
        for marker in ("y[~m", "y[/~m"):
            if marker not in text:
                continue
            head, tail = text.rsplit(marker, 1)
            candidate = f"{head}(y{marker[1:]}{tail}"
            if (
                normalize_surface(reconstruct_surface_from_analysis(candidate)).lower()
                == surface_norm
            ):
                return candidate

    return analysis


def _normalize_variant_encoding(*, surface: str, analysis: str, dulat: str, pos: str) -> str:
    text = (analysis or "").strip()
    host_surface = surface[:-1] if surface.endswith("m") else surface
    options = _split_slash_options(pos)
    if any(_requires_infinitive_encoding(option) for option in options):
        return _to_infinitive_encoding(host_surface, _strip_terminal_surface_m(text), dulat)
    if any(_requires_participle_encoding(option) for option in options):
        return _to_participle_encoding(host_surface, _strip_terminal_surface_m(text), dulat)
    if any(_requires_finite_encoding(option) for option in options):
        return _to_finite_encoding(text)
    return text


def _rewrite_pos_for_enclitic_variant(pos: str, note_morphologies: set[str]) -> str:
    value = (pos or "").strip()
    if not value or not _NOUNISH_HEAD_RE.search(value):
        return value

    numbers = _number_markers_from_morphologies(note_morphologies)
    if not numbers and any("suff" in morph for morph in note_morphologies):
        numbers = ["sg."]
    if not numbers:
        return value

    head, sep, rest = value.partition(",")
    base_option = head.split("/", 1)[0].strip()
    base_head = _NUMBER_TOKEN_RE.sub("", base_option)
    base_head = re.sub(r"\s{2,}", " ", base_head).strip()
    new_head = f"{base_head} {' / '.join(numbers)}".strip()
    if not sep:
        return new_head
    return f"{new_head}, {rest.strip()}"


def _number_markers_from_morphologies(morphologies: set[str]) -> list[str]:
    numbers: list[str] = []
    joined = " ".join(sorted(morphologies))
    if re.search(r"\bsg\.", joined, flags=re.IGNORECASE):
        numbers.append("sg.")
    if re.search(r"\bpl\.", joined, flags=re.IGNORECASE):
        numbers.append("pl.")
    if re.search(r"\bdu\.", joined, flags=re.IGNORECASE):
        numbers.append("du.")
    return numbers


def _should_add_synthetic_enclitic_variant(
    *,
    pos: str,
    plain_morphologies: set[str],
    note_morphologies: set[str],
) -> bool:
    """Return False for noisy nounish plural forms with only generic `suff.` note backing."""
    if not pos or not _NOUNISH_HEAD_RE.search(pos):
        return True
    if not any(_has_plural_or_dual_marker(value) for value in plain_morphologies):
        return True
    if not note_morphologies:
        return True
    if all(_is_generic_suffix_only_morphology(value) for value in note_morphologies):
        return False
    return True


def _has_plural_or_dual_marker(morphology: str) -> bool:
    text = (morphology or "").lower()
    return "pl." in text or "du." in text


def _is_generic_suffix_only_morphology(morphology: str) -> bool:
    text = (morphology or "").lower().strip().strip(",")
    return text == "suff."


def _strip_terminal_surface_m(text: str) -> str:
    value = (text or "").strip()
    for old, new in (("m[/", "[/"), ("m[", "["), ("m/", "/")):
        if old in value:
            return value.replace(old, new, 1)
    return value
