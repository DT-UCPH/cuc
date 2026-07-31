#!/usr/bin/env python3
"""Certify auto-seeded reviewed rows backed by an aligned legacy review.

The legacy input must already be migrated to the same token IDs as the target
reviewed TSV.  A token is certified only when the unordered set of normalized
morphological analyses agrees exactly in both files.  Unresolved analyses are
never certified.  Current DULAT, POS, gloss, and sign-span fields are retained,
while legacy comments are merged into the target row.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

AGENT_ROOT = Path(__file__).resolve().parents[1]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from reviewed_evaluation.loader import MorphologyTsvLoader  # noqa: E402
from reviewed_normalization import normalize_reviewed_analysis  # noqa: E402

SEED_MARK = "SEEDED from auto-parse; not yet hand-reviewed."


def certify_exact_agreements(
    reviewed_path: Path,
    legacy_path: Path,
    *,
    minimum_id: int = 0,
    include_commented: bool = False,
) -> tuple[str, int, int]:
    """Return updated TSV text, certified token count, and changed row count."""

    loader = MorphologyTsvLoader()
    reviewed = loader.load(reviewed_path)
    legacy = loader.load(legacy_path)
    legacy_comments = _comments_by_analysis(legacy_path)
    commented_ids = {token_id for token_id, _analysis in legacy_comments}
    exact_ids = {
        token_id
        for token_id, current in reviewed.tokens_by_id.items()
        if token_id.isdigit()
        and int(token_id) >= minimum_id
        and token_id in legacy.tokens_by_id
        and current.surface == legacy.tokens_by_id[token_id].surface
        and current.analyses == legacy.tokens_by_id[token_id].analyses
        and current.analyses
        and "?" not in current.analyses
        and (include_commented or token_id not in commented_ids)
    }

    certified_ids: set[str] = set()
    changed_rows = 0
    output: list[str] = []
    for raw_line in reviewed_path.read_text(encoding="utf-8").splitlines():
        fields = raw_line.split("\t")
        if not fields or fields[0] not in exact_ids or len(fields) < 8:
            output.append(raw_line)
            continue
        if SEED_MARK not in fields[7]:
            output.append(raw_line)
            continue

        analysis = normalize_reviewed_analysis(fields[3])
        comments = legacy_comments.get((fields[0], analysis), ())
        fields[7] = _merge_comments(_remove_seed_marker(fields[7]), comments)
        output.append("\t".join(fields))
        certified_ids.add(fields[0])
        changed_rows += 1

    return "\n".join(output) + "\n", len(certified_ids), changed_rows


def _comments_by_analysis(path: Path) -> dict[tuple[str, str], tuple[str, ...]]:
    comments: dict[tuple[str, str], list[str]] = defaultdict(list)
    has_sign_span = MorphologyTsvLoader._has_sign_span_column(
        path.read_text(encoding="utf-8").splitlines()
    )
    analysis_index = 3 if has_sign_span else 2
    comment_index = 7 if has_sign_span else 6
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        fields = raw_line.split("\t")
        if (
            len(fields) <= comment_index
            or not fields[0].isdigit()
            or not fields[comment_index].strip()
        ):
            continue
        key = (fields[0], normalize_reviewed_analysis(fields[analysis_index]))
        comment = fields[comment_index].strip()
        if comment not in comments[key]:
            comments[key].append(comment)
    return {key: tuple(values) for key, values in comments.items()}


def _remove_seed_marker(comment: str) -> str:
    parts = [part.strip() for part in comment.split(" | ")]
    return " | ".join(part for part in parts if part and part != SEED_MARK)


def _merge_comments(existing: str, additions: tuple[str, ...]) -> str:
    parts = [part.strip() for part in existing.split(" | ") if part.strip()]
    for comment in additions:
        if comment not in parts:
            parts.append(comment)
    return " | ".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reviewed", type=Path)
    parser.add_argument("legacy", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--minimum-id", type=int, default=0)
    parser.add_argument(
        "--include-commented",
        action="store_true",
        help="also certify exact tokens carrying legacy editorial comments",
    )
    args = parser.parse_args()

    output, certified, changed_rows = certify_exact_agreements(
        args.reviewed,
        args.legacy,
        minimum_id=args.minimum_id,
        include_commented=args.include_commented,
    )
    args.out.write_text(output, encoding="utf-8")
    print(
        f"Certified {certified} token(s) across {changed_rows} row(s); "
        f"wrote {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
