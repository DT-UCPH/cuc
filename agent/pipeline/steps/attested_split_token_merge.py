"""Add attested lexical-upgrade merge variants for adjacent split token pairs.

This step is intentionally strict:
- look only at adjacent token pairs,
- require the second token to remain unresolved,
- require the concatenated surface to have a DULAT-attested variant at the
  current/next reference,
- require that concatenation to be a lexical upgrade over the current row
  (same gloss, different DULAT head).

This targets cases like `la` + `nk` -> `lảnk`, where the first token already
has a weaker lexical parse and the second token is left unresolved by the
normal pass.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Dict

from pipeline.steps.base import RefinementStep, StepResult, TabletRow, parse_tsv_line
from scripts.refine_results_mentions import (
    Variant,
    build_variants,
    load_entries,
    load_reverse_mentions,
    normalize_lookup,
    parse_separator_ref,
    render_variant,
)

_SUFFIX_SEGMENTS = ("hm", "hn", "km", "kn", "ny", "nm", "nn", "h", "k", "n", "y")
_PRONOMINAL_SUFFIX_RE = re.compile(
    r"\+(?:y|n=?|ny=?|k=?|nk|h=?|nh=?|nn|km=?|nkm|kn|hm=?|hn)(?=\s*$|[;,\s])",
    flags=re.IGNORECASE,
)
_NOMINAL_HEAD_RE = re.compile(
    r"^(?:n\.|adj\.|num\.|dn\b|pn\b|rn\b|tn\b|gn\b|mn\b)",
    flags=re.IGNORECASE,
)


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split(";") if part.strip()]


def _first_dulat_heads(value: str) -> set[str]:
    return {part.split(",", 1)[0].strip() for part in _split_semicolon(value)}


def _surface_tail(combined_surface: str, analysis: str) -> str:
    plain = "".join(ch for ch in analysis if ch.isalpha() or ch in "ˤʔḫṣṯẓġḏḥṭšʕʿ")
    if not combined_surface.startswith(plain):
        return ""
    return combined_surface[len(plain) :]


def _inject_nominal_suffix(analysis: str, suffix: str) -> str:
    value = (analysis or "").strip()
    if not suffix or not value.endswith("/"):
        return value
    return f"{value[:-1]}/+{suffix}"


def _pos_with_construct_for_pronominal_suffix(pos: str, analysis: str) -> str:
    value = (pos or "").strip()
    if not value:
        return value
    if not _PRONOMINAL_SUFFIX_RE.search((analysis or "").strip()):
        return value

    rewritten_variants: list[str] = []
    for variant in value.split(";"):
        text = variant.strip()
        if not text:
            continue
        head, sep, rest = text.partition(",")
        head_options = [part.strip() for part in head.split("/") if part.strip()] or [head.strip()]
        rewritten_heads: list[str] = []
        for option in head_options:
            if not _NOMINAL_HEAD_RE.match(option):
                rewritten_heads.append(option)
                continue
            option = re.sub(r"(?<!\w)(?:abs\.|cstr\.)(?!\w)", "", option)
            option = re.sub(r"\s{2,}", " ", option).strip()
            if "cstr." not in option:
                tokens = option.split()
                case_idx = next(
                    (
                        idx
                        for idx, token in enumerate(tokens)
                        if token in {"nom.", "gen.", "acc.", "acc.?"}
                    ),
                    -1,
                )
                if case_idx >= 0:
                    tokens.insert(case_idx, "cstr.")
                    option = " ".join(tokens)
                else:
                    option = f"{option} cstr."
            rewritten_heads.append(option.strip())
        new_head = " / ".join(rewritten_heads)
        if sep:
            rewritten_variants.append(f"{new_head}, {rest.strip()}")
        else:
            rewritten_variants.append(new_head)
    return "; ".join(rewritten_variants) if rewritten_variants else value


class AttestedSplitTokenMergeFixer(RefinementStep):
    def __init__(self, dulat_db: Path, udb_db: Path) -> None:
        self._dulat_db = dulat_db
        self._udb_db = udb_db
        self._loaded = False
        self._disabled = False
        self._entries_by_id = {}
        self._forms_map = {}
        self._lemma_map = {}
        self._suffix_map = {}
        self._forms_morph = {}
        self._reverse_mentions = {}
        self._entry_ref_count = {}
        self._entry_tablets = {}
        self._entry_family_count = {}

    @property
    def name(self) -> str:
        return "attested-split-token-merge"

    def refine_row(self, row: TabletRow) -> TabletRow:  # pragma: no cover
        return row

    def _ensure_loaded(self) -> bool:
        if self._loaded:
            return not self._disabled
        try:
            (
                self._entries_by_id,
                self._forms_map,
                self._lemma_map,
                self._suffix_map,
                self._forms_morph,
            ) = load_entries(self._dulat_db)
            (
                self._reverse_mentions,
                self._entry_ref_count,
                self._entry_tablets,
                self._entry_family_count,
            ) = load_reverse_mentions(self._dulat_db, self._udb_db)
        except (sqlite3.Error, OSError):
            self._disabled = True
        self._loaded = True
        return not self._disabled

    def refine_file(self, path: Path) -> StepResult:
        if not self._ensure_loaded():
            return StepResult(file=path.name, rows_processed=0, rows_changed=0)

        lines = path.read_text(encoding="utf-8").splitlines()
        rows_processed = 0
        rows_changed = 0
        current_ref = ""
        parsed: list[tuple[int, str, TabletRow]] = []

        for idx, raw in enumerate(lines):
            ref = parse_separator_ref(raw)
            if ref:
                current_ref = ref
                continue
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            row = parse_tsv_line(raw)
            if row is None:
                continue
            rows_processed += 1
            parsed.append((idx, current_ref, row))

        inserts_by_line: Dict[int, list[str]] = {}
        for pos in range(len(parsed) - 1):
            line_index, current_ref, row = parsed[pos]
            _next_line_index, next_ref, next_row = parsed[pos + 1]
            extra = self._merged_row_for_pair(current_ref, row, next_ref, next_row)
            if extra is None:
                continue
            payload = extra.to_tsv()
            inserts_by_line.setdefault(line_index, [])
            if payload in inserts_by_line[line_index]:
                continue
            inserts_by_line[line_index].append(payload)
            rows_changed += 1

        if not rows_changed:
            return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=0)

        out_lines: list[str] = []
        for idx, raw in enumerate(lines):
            out_lines.append(raw)
            out_lines.extend(inserts_by_line.get(idx, []))

        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)

    def _merged_row_for_pair(
        self,
        current_ref: str,
        row: TabletRow,
        next_ref: str,
        next_row: TabletRow,
    ) -> TabletRow | None:
        if not row.surface.strip() or not next_row.surface.strip():
            return None
        if row.analysis.strip() in {"", "?"}:
            return None
        if next_row.analysis.strip() != "?":
            return None
        if "DULAT: NOT FOUND" not in (next_row.comment or ""):
            return None

        combined_surface = row.surface.strip() + next_row.surface.strip()
        mention_ids: set[int] = set()
        if current_ref:
            mention_ids.update(self._reverse_mentions.get(current_ref, set()))
        if next_ref and next_ref != current_ref:
            mention_ids.update(self._reverse_mentions.get(next_ref, set()))

        variants = build_variants(
            combined_surface,
            current_ref or next_ref,
            self._forms_map,
            self._lemma_map,
            self._suffix_map,
            self._forms_morph,
            mention_ids,
            self._entry_ref_count,
            self._entry_tablets,
            self._entry_family_count,
            max_variants=5,
        )
        if not variants:
            return None

        current_heads = _first_dulat_heads(row.dulat)
        current_glosses = set(_split_semicolon(row.gloss))
        for variant in variants:
            analysis, dulat, pos, gloss = render_variant(
                combined_surface,
                variant,
                self._forms_morph,
            )
            if gloss not in current_glosses:
                continue
            if dulat in current_heads:
                continue
            merged_analysis = self._suffix_upgrade_for_direct_form(
                combined_surface=combined_surface,
                variant=variant,
                analysis=analysis,
            )
            merged_pos = _pos_with_construct_for_pronominal_suffix(row.pos, merged_analysis)
            return TabletRow(
                line_id=row.line_id,
                surface=row.surface,
                analysis=merged_analysis,
                dulat=dulat,
                pos=merged_pos,
                gloss=row.gloss,
                comment=f"If merged with following token {next_row.surface.strip()}.",
            )
        return None

    def _suffix_upgrade_for_direct_form(
        self,
        *,
        combined_surface: str,
        variant: Variant,
        analysis: str,
    ) -> str:
        if len(variant.entries) != 1:
            return analysis
        entry = variant.entries[0]
        morphs = self._forms_morph.get((normalize_lookup(combined_surface), entry.entry_id), set())
        if not any("suff" in (morph or "").lower() for morph in morphs):
            return analysis
        tail = _surface_tail(combined_surface, analysis.rstrip("/"))
        if tail not in _SUFFIX_SEGMENTS:
            return analysis
        return _inject_nominal_suffix(analysis, tail)
