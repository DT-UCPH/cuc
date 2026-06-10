"""Annotate line-final fragments rewritten in full on the next line.

Ugaritic scribes occasionally broke a word off at the end of a physical line
and then wrote the complete word at the beginning of the next line (KTU 1.6
V:17-18 ``b š | b šdm``; VI:10-11 ``s | spuy``). The orphan fragment is not a
lexeme: merging it with its neighbour or reporting ``DULAT: NOT FOUND`` are
both wrong. This step replaces the fragment's comment with a deterministic
explanation so downstream review and lint passes can recognize the pattern.
"""

from pathlib import Path
from typing import List, Optional, Tuple

from pipeline.steps.base import (
    RefinementStep,
    StepResult,
    TabletRow,
    is_unresolved,
    parse_tsv_line,
)

_MAX_FRAGMENT_LEN = 3
_NOT_FOUND_COMMENT = "DULAT: NOT FOUND"


def is_anticipation_fragment(
    fragment_surface: str,
    full_surface: str,
    max_fragment_len: int = _MAX_FRAGMENT_LEN,
) -> bool:
    """Return True when ``fragment_surface`` anticipates ``full_surface``.

    A fragment anticipates a full form when it is a short strict prefix of it:
    the scribe stopped mid-word and rewrote the word in full.
    """
    fragment = (fragment_surface or "").strip()
    full = (full_surface or "").strip()
    if not fragment or not full:
        return False
    if len(fragment) > max_fragment_len:
        return False
    return len(full) > len(fragment) and full.startswith(fragment)


def anticipation_comment(full_surface: str) -> str:
    """Comment text recorded on an anticipated fragment row."""
    return (
        f"Incomplete {full_surface} rewritten in full at the start of the next line "
        "(scribal anticipation)."
    )


class ScribalAnticipationAnnotator(RefinementStep):
    """Marks unresolved line-final fragments that the next line rewrites."""

    @property
    def name(self) -> str:
        return "scribal-anticipation-annotator"

    def refine_row(self, row: TabletRow) -> TabletRow:  # pragma: no cover
        return row

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()

        # (raw line index, physical-line group, row) for every data row; the
        # group counter advances on each separator so fragments can be matched
        # against the first rows of the following physical line only.
        parsed: List[Tuple[int, int, TabletRow]] = []
        group = 0
        for idx, raw in enumerate(lines):
            if raw.lstrip().startswith("#"):
                group += 1
                continue
            row = parse_tsv_line(raw)
            if row is None:
                continue
            parsed.append((idx, group, row))

        rows_changed = 0
        for pos, (line_index, row_group, row) in enumerate(parsed):
            if not is_unresolved(row):
                continue
            is_last_of_line = pos + 1 >= len(parsed) or parsed[pos + 1][1] != row_group
            if not is_last_of_line:
                continue
            full_surface = self._anticipated_full_surface(parsed, pos)
            if full_surface is None:
                continue
            comment = anticipation_comment(full_surface)
            updated = TabletRow(
                line_id=row.line_id,
                surface=row.surface,
                analysis=row.analysis,
                dulat=row.dulat,
                pos=row.pos,
                gloss=row.gloss,
                comment=self._merge_comment(row.comment, comment),
            )
            lines[line_index] = updated.to_tsv()
            rows_changed += 1

        if rows_changed:
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=len(parsed), rows_changed=rows_changed)

    @staticmethod
    def _merge_comment(existing: str, annotation: str) -> str:
        existing = (existing or "").replace(_NOT_FOUND_COMMENT, "").strip().strip(";").strip()
        if not existing:
            return annotation
        return f"{existing}; {annotation}"

    @staticmethod
    def _anticipated_full_surface(
        parsed: List[Tuple[int, int, TabletRow]],
        fragment_pos: int,
    ) -> Optional[str]:
        """Return the next line's full form anticipated by the fragment.

        Two attested layouts are recognized:
        - direct: the next line starts with the completed word (s | spuy);
        - context repeat: the next line repeats the token preceding the
          fragment, then the completed word (b š | b šdm).
        """
        _idx, fragment_group, fragment_row = parsed[fragment_pos]
        following = [
            row for _i, group, row in parsed[fragment_pos + 1 :] if group == fragment_group + 1
        ]
        if not following:
            return None
        first = following[0]
        if is_anticipation_fragment(fragment_row.surface, first.surface):
            return first.surface
        if fragment_pos > 0:
            _pidx, prev_group, prev_row = parsed[fragment_pos - 1]
            context_repeats = (
                prev_group == fragment_group and prev_row.surface.strip() == first.surface.strip()
            )
            if context_repeats and len(following) > 1:
                second = following[1]
                if is_anticipation_fragment(fragment_row.surface, second.surface):
                    return second.surface
        return None
