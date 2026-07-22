#!/usr/bin/env python3
"""Audit structured split-token pairs and legacy-comment preservation."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


MERGE_NEXT_RE = re.compile(r"\bMERGE WITH THE NEXT\b", re.IGNORECASE)
MERGE_PREVIOUS_RE = re.compile(r"\bMERGE WITH THE PREVIOUS\b", re.IGNORECASE)


@dataclass(frozen=True)
class Row:
    line_number: int
    token_id: str
    surface: str
    analysis: str
    comment: str


@dataclass(frozen=True)
class Token:
    token_id: str
    surface: str
    rows: tuple[Row, ...]


@dataclass(frozen=True)
class Issue:
    path: Path
    line_number: int
    token_id: str
    code: str
    detail: str


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        default=["reviewed"],
        help="Reviewed TSV files or directories to scan (default: reviewed)",
    )
    parser.add_argument(
        "--before",
        type=Path,
        help="Legacy TSV whose nonempty comments must survive in one migrated TSV",
    )
    return parser.parse_args(argv)


def collect_tsvs(raw_paths: Iterable[str]) -> list[Path]:
    paths: set[Path] = set()
    for raw in raw_paths:
        path = Path(raw)
        if path.is_dir():
            paths.update(
                candidate for candidate in path.rglob("*.tsv") if candidate.is_file()
            )
        elif path.is_file():
            paths.add(path)
        else:
            raise FileNotFoundError(raw)
    return sorted(paths)


def parse_data_rows(path: Path) -> list[Row]:
    rows: list[Row] = []
    with path.open(encoding="utf-8-sig") as source:
        for line_number, raw_line in enumerate(source, start=1):
            if not raw_line.strip() or raw_line.lstrip().startswith("#"):
                continue
            columns = raw_line.rstrip("\r\n").split("\t")
            if columns[0].strip().lower() == "id" or not columns[0].strip().isdigit():
                continue
            if len(columns) >= 8:
                surface, analysis, comment = columns[1], columns[3], columns[7]
            elif len(columns) >= 7:
                surface, analysis, comment = columns[1], columns[2], columns[6]
            else:
                continue
            rows.append(
                Row(
                    line_number=line_number,
                    token_id=columns[0].strip(),
                    surface=surface.strip(),
                    analysis=analysis.strip(),
                    comment=comment.strip(),
                )
            )
    return rows


def group_tokens(rows: list[Row]) -> list[Token]:
    tokens: list[Token] = []
    for row in rows:
        if tokens and tokens[-1].token_id == row.token_id:
            previous = tokens[-1]
            tokens[-1] = Token(previous.token_id, previous.surface, previous.rows + (row,))
        else:
            tokens.append(Token(row.token_id, row.surface, (row,)))
    return tokens


def directions(token: Token) -> set[str]:
    found: set[str] = set()
    for row in token.rows:
        if MERGE_NEXT_RE.search(row.comment):
            found.add("next")
        if MERGE_PREVIOUS_RE.search(row.comment):
            found.add("previous")
    return found


def annotated_analyses(token: Token) -> set[str]:
    return {
        row.analysis
        for row in token.rows
        if MERGE_NEXT_RE.search(row.comment) or MERGE_PREVIOUS_RE.search(row.comment)
    }


def normalized_letters(value: str) -> str:
    mapping = str.maketrans({"ả": "a", "ỉ": "i", "ủ": "u", "ʿ": "ʕ", "ˤ": "ʕ"})
    return "".join(character for character in value if character.isalpha()).translate(mapping)


def load_reconstructor():
    skill_path = Path(__file__).resolve()
    for parent in skill_path.parents:
        agent_root = parent / "agent"
        if (agent_root / "pipeline" / "steps" / "analysis_utils.py").is_file():
            sys.path.insert(0, str(agent_root))
            from pipeline.steps.analysis_utils import reconstruct_surface_from_analysis

            return reconstruct_surface_from_analysis
    return None


def audit_pairs(path: Path) -> tuple[list[Issue], int]:
    tokens = group_tokens(parse_data_rows(path))
    issues: list[Issue] = []
    pair_count = 0
    reconstruct = load_reconstructor()

    for index, token in enumerate(tokens):
        token_directions = directions(token)
        if token_directions == {"next", "previous"}:
            issues.append(
                Issue(
                    path,
                    token.rows[0].line_number,
                    token.token_id,
                    "mixed-merge-directions",
                    "one token is annotated toward both next and previous tokens",
                )
            )
            continue

        if "next" in token_directions:
            partner = tokens[index + 1] if index + 1 < len(tokens) else None
            if partner is None or "previous" not in directions(partner):
                issues.append(
                    Issue(
                        path,
                        token.rows[0].line_number,
                        token.token_id,
                        "missing-next-partner",
                        "MERGE WITH THE NEXT lacks an adjacent PREVIOUS partner",
                    )
                )
                continue

            pair_count += 1
            own_analyses = annotated_analyses(token)
            partner_analyses = annotated_analyses(partner)
            if own_analyses != partner_analyses:
                issues.append(
                    Issue(
                        path,
                        token.rows[0].line_number,
                        token.token_id,
                        "analysis-mismatch",
                        f"pair analyses differ: {sorted(own_analyses)} vs "
                        f"{sorted(partner_analyses)}",
                    )
                )
                continue

            combined = token.surface + partner.surface
            if reconstruct is None or "x" in combined.lower():
                continue
            expected = normalized_letters(combined)
            for analysis in sorted(own_analyses):
                actual = normalized_letters(reconstruct(analysis))
                if actual != expected:
                    issues.append(
                        Issue(
                            path,
                            token.rows[0].line_number,
                            token.token_id,
                            "merged-reconstruction-mismatch",
                            f"{analysis!r} reconstructs as {actual!r}; expected {expected!r}",
                        )
                    )

        elif "previous" in token_directions:
            partner = tokens[index - 1] if index > 0 else None
            if partner is None or "next" not in directions(partner):
                issues.append(
                    Issue(
                        path,
                        token.rows[0].line_number,
                        token.token_id,
                        "missing-previous-partner",
                        "MERGE WITH THE PREVIOUS lacks an adjacent NEXT partner",
                    )
                )

    return issues, pair_count


def comments_in_file(path: Path) -> Counter[str]:
    comments: Counter[str] = Counter()
    with path.open(encoding="utf-8-sig") as source:
        for raw_line in source:
            if not raw_line.strip() or raw_line.lstrip().startswith("#"):
                continue
            columns = raw_line.rstrip("\r\n").split("\t")
            if not columns or not columns[0].strip().isdigit():
                continue
            comment = ""
            if len(columns) >= 8:
                comment = columns[7].strip()
            elif len(columns) >= 7:
                comment = columns[6].strip()
            elif len(columns) >= 3:
                inline = re.search(r"\s+#\s*(?P<comment>.+)$", columns[2])
                if inline:
                    comment = inline.group("comment").strip()
            if comment:
                comments[comment] += 1
    return comments


def audit_comment_preservation(before: Path, after: Path) -> list[Issue]:
    before_comments = comments_in_file(before)
    after_comments = [row.comment for row in parse_data_rows(after) if row.comment]
    issues: list[Issue] = []
    for comment, required_count in before_comments.items():
        actual_count = sum(comment in candidate for candidate in after_comments)
        if actual_count < required_count:
            issues.append(
                Issue(
                    after,
                    0,
                    "",
                    "lost-legacy-comment",
                    f"preserved {actual_count}/{required_count} occurrence(s) of {comment!r}",
                )
            )
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
    if args.before and len(paths) != 1:
        print("error: --before requires exactly one migrated TSV path", file=sys.stderr)
        return 2

    issues: list[Issue] = []
    pair_count = 0
    for path in paths:
        file_issues, file_pairs = audit_pairs(path)
        issues.extend(file_issues)
        pair_count += file_pairs
    if args.before:
        if not args.before.is_file():
            print(f"error: path not found: {args.before}", file=sys.stderr)
            return 2
        issues.extend(audit_comment_preservation(args.before, paths[0]))

    if issues:
        print("path\tline\tid\tcode\tdetail")
        for issue in issues:
            print(
                f"{issue.path}\t{issue.line_number}\t{issue.token_id}\t"
                f"{issue.code}\t{issue.detail}"
            )

    print(
        f"Scanned {len(paths)} TSV file(s); found {pair_count} merge pair(s) and "
        f"{len(issues)} issue(s).",
        file=sys.stderr,
    )
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
