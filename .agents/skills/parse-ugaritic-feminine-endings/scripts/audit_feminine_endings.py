#!/usr/bin/env python3
"""Conservatively audit feminine-ending encodings in reviewed CUC TSVs."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


FEMININE_POS_RE = re.compile(r"(?:\bn\.\s*f\.|\bDN\s+f\.)", re.IGNORECASE)
PLURAL_POS_RE = re.compile(r"\bpl\.", re.IGNORECASE)
DUAL_POS_RE = re.compile(r"\bdu\.", re.IGNORECASE)
ABSOLUTE_POS_RE = re.compile(r"\babs\.", re.IGNORECASE)
LEXICAL_T_OVERLAP_RE = re.compile(r"\(t(?:\([IV]+\))?/")
BARE_T_ENDING_RE = re.compile(r"/t(?=(?:[+~]|$))")
PLURAL_T_ENDING_RE = re.compile(r"/t=")
DUAL_TM_ENDING_RE = re.compile(r"/tm(?=(?:[+~]|$))")
PARENTHETICAL_RE = re.compile(r"\([^)]*\)")


@dataclass(frozen=True)
class Issue:
    path: Path
    line_number: int
    token_id: str
    surface: str
    code: str
    detail: str


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit mechanically provable feminine-ending errors in reviewed "
            "eight-column TSV files."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["reviewed"],
        help="TSV files or directories to scan (default: reviewed)",
    )
    return parser.parse_args(argv)


def collect_tsvs(raw_paths: Iterable[str]) -> list[Path]:
    paths: set[Path] = set()
    for raw in raw_paths:
        path = Path(raw)
        if path.is_dir():
            paths.update(candidate for candidate in path.rglob("*.tsv") if candidate.is_file())
        elif path.is_file():
            paths.add(path)
        else:
            raise FileNotFoundError(raw)
    return sorted(paths)


def declared_lexeme_ends_in_t(value: str) -> bool:
    """Return true when any declared DULAT lemma segment ends in lexical t."""
    if not value or value.strip() == "?":
        return False
    without_notes = PARENTHETICAL_RE.sub("", value)
    for segment in without_notes.split("/"):
        letters = "".join(character for character in segment if character.isalpha())
        if letters.endswith("t"):
            return True
    return False


def surface_letters(value: str) -> str:
    return "".join(character for character in value.strip() if character.isalpha())


def nominal_number(pos: str) -> str | None:
    """Return an unambiguous head-noun number, excluding suffix morphology."""
    noun_pos = pos.split("+", maxsplit=1)[0]
    numbers = {
        number
        for number, pattern in (
            ("sg", re.compile(r"\bsg\.")),
            ("du", DUAL_POS_RE),
            ("pl", PLURAL_POS_RE),
        )
        if pattern.search(noun_pos)
    }
    return next(iter(numbers)) if len(numbers) == 1 else None


def inspect_row(path: Path, line_number: int, columns: list[str]) -> list[Issue]:
    token_id, surface = columns[0].strip(), columns[1].strip()
    analysis, lexeme, pos = columns[3].strip(), columns[4].strip(), columns[5].strip()
    issues: list[Issue] = []

    if not token_id.isdigit() or not FEMININE_POS_RE.search(pos):
        return issues

    if declared_lexeme_ends_in_t(lexeme) and not LEXICAL_T_OVERLAP_RE.search(analysis):
        issues.append(
            Issue(
                path,
                line_number,
                token_id,
                surface,
                "missing-lexical-t-overlap",
                f"DULAT lexeme {lexeme!r} ends in t but analysis lacks '(t.../'",
            )
        )

    number = nominal_number(pos)

    if number == "pl" and BARE_T_ENDING_RE.search(analysis):
        issues.append(
            Issue(
                path,
                line_number,
                token_id,
                surface,
                "plural-bare-t-ending",
                "feminine plural uses /t where /t= is required",
            )
        )

    is_absolute_dual = number == "du" and ABSOLUTE_POS_RE.search(pos)
    if (
        is_absolute_dual
        and surface_letters(surface).endswith("tm")
        and BARE_T_ENDING_RE.search(analysis)
        and not DUAL_TM_ENDING_RE.search(analysis)
        and not PLURAL_T_ENDING_RE.search(analysis)
    ):
        issues.append(
            Issue(
                path,
                line_number,
                token_id,
                surface,
                "absolute-dual-missing-tm",
                "written absolute-dual -tm is not encoded as /tm",
            )
        )

    return issues


def inspect_file(path: Path) -> list[Issue]:
    issues: list[Issue] = []
    with path.open(encoding="utf-8-sig") as source:
        for line_number, raw_line in enumerate(source, start=1):
            if not raw_line.strip() or raw_line.lstrip().startswith("#"):
                continue
            columns = raw_line.rstrip("\r\n").split("\t")
            if columns[0].strip().lower() == "id":
                continue
            if len(columns) != 8:
                token_id = columns[0].strip() if columns else ""
                surface = columns[1].strip() if len(columns) > 1 else ""
                issues.append(
                    Issue(
                        path,
                        line_number,
                        token_id,
                        surface,
                        "invalid-column-count",
                        f"expected 8 TSV columns, found {len(columns)}",
                    )
                )
                continue
            issues.extend(inspect_row(path, line_number, columns))
    return issues


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        paths = collect_tsvs(args.paths)
    except FileNotFoundError as error:
        print(f"error: path not found: {error}", file=sys.stderr)
        return 2

    if not paths:
        print("error: no TSV files found", file=sys.stderr)
        return 2

    issues = [issue for path in paths for issue in inspect_file(path)]
    if issues:
        print("path\tline\tid\tsurface\tcode\tdetail")
        for issue in issues:
            print(
                f"{issue.path}\t{issue.line_number}\t{issue.token_id}\t"
                f"{issue.surface}\t{issue.code}\t{issue.detail}"
            )

    print(
        f"Scanned {len(paths)} TSV file(s); found {len(issues)} issue(s).",
        file=sys.stderr,
    )
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
