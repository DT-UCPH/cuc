"""Score morphology-column agreement against reviewed/ tablet files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

AGENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare automatic morphology analyses against reviewed gold TSVs. "
            "Scoring is per reviewed token id, using unordered sets of morphology options."
        )
    )
    parser.add_argument(
        "--reviewed",
        default=str(REPO_ROOT / "reviewed"),
        help="Reviewed TSV file or directory (default: reviewed/).",
    )
    parser.add_argument(
        "--auto",
        default=None,
        help="Auto TSV file or directory (defaults to latest auto_parsing/<version>/).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit full JSON output instead of the human-readable summary.",
    )
    parser.add_argument(
        "--show-mismatches",
        action="store_true",
        help="Print mismatching reviewed ids with missing/extra analyses.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of mismatches to print per run (default: 20).",
    )
    return parser


def main() -> int:
    from reviewed_evaluation import (
        EvaluationTargetResolver,
        MorphologyAgreementScorer,
        MorphologyTsvLoader,
    )

    args = build_parser().parse_args()
    reviewed_root = _resolve_repo_relative_path(args.reviewed)
    auto_root = _resolve_repo_relative_path(args.auto) if args.auto else _default_auto_root()

    loader = MorphologyTsvLoader()
    resolver = EvaluationTargetResolver()
    scorer = MorphologyAgreementScorer()

    pairs = resolver.resolve(reviewed_root, auto_root)
    file_results = []
    for pair in pairs:
        reviewed = loader.load(pair.reviewed_path)
        auto = loader.load(pair.auto_path) if pair.auto_path else loader.empty(pair.label)
        file_results.append(scorer.score_file_pair(label=pair.label, reviewed=reviewed, auto=auto))

    aggregate = scorer.score_many(
        reviewed_root=reviewed_root,
        auto_root=auto_root,
        file_results=file_results,
    )

    if args.json:
        print(json.dumps(aggregate.to_dict(), ensure_ascii=False, indent=2))
        return 0

    _print_summary(aggregate)
    if args.show_mismatches:
        _print_mismatches(file_results, limit=max(args.limit, 0))
    return 0


def _default_auto_root() -> Path:
    auto_root = REPO_ROOT / "auto_parsing"
    if not auto_root.exists():
        return auto_root
    candidates = [path for path in auto_root.iterdir() if path.is_dir()]
    if not candidates:
        return auto_root
    return max(candidates, key=_version_key)


def _resolve_repo_relative_path(path_text: str | None) -> Path | None:
    if path_text is None:
        return None
    path = Path(path_text)
    if path.is_absolute() or path.exists():
        return path
    repo_relative = REPO_ROOT / path
    return repo_relative if repo_relative.exists() else path


def _version_key(path: Path) -> tuple[int, ...]:
    parts = []
    for token in path.name.split("."):
        parts.append(int(token) if token.isdigit() else 0)
    return tuple(parts)


def _print_summary(aggregate) -> None:
    summary = aggregate.summary
    print(f"Reviewed root: {aggregate.reviewed_root}")
    print(f"Auto root: {aggregate.auto_root}")
    print(f"Files scored: {len(aggregate.file_results)}")
    print(f"Reviewed ids: {summary.compared_ids}")
    print("")
    print("Overall")
    _print_metric_block(summary)
    if aggregate.unambiguous_summary is not None:
        print("")
        print("Unambiguous Gold")
        _print_metric_block(aggregate.unambiguous_summary)
    if aggregate.ambiguous_summary is not None:
        print("")
        print("Ambiguous Gold")
        _print_metric_block(aggregate.ambiguous_summary)
    print("")
    print("Per File")
    for result in aggregate.file_results:
        print(
            f"{result.label}: ids={result.summary.compared_ids} "
            f"exact={result.summary.exact_set_accuracy:.4f} "
            f"macro_f1={result.summary.macro_f1:.4f} "
            f"micro_f1={result.summary.micro_f1:.4f} "
            f"coverage={result.summary.gold_coverage:.4f}"
        )


def _print_metric_block(summary) -> None:
    print(f"exact_set_accuracy: {summary.exact_set_accuracy:.4f}")
    print(f"macro_precision: {summary.macro_precision:.4f}")
    print(f"macro_recall: {summary.macro_recall:.4f}")
    print(f"macro_f1: {summary.macro_f1:.4f}")
    print(f"macro_jaccard: {summary.macro_jaccard:.4f}")
    print(f"micro_precision: {summary.micro_precision:.4f}")
    print(f"micro_recall: {summary.micro_recall:.4f}")
    print(f"micro_f1: {summary.micro_f1:.4f}")
    print(f"gold_coverage: {summary.gold_coverage:.4f}")
    print(f"mean_extra_options: {summary.mean_extra_options:.4f}")
    print(f"mean_missing_options: {summary.mean_missing_options:.4f}")
    print(f"mean_option_count_error: {summary.mean_option_count_error:.4f}")
    print(f"reviewed_option_count: {summary.reviewed_option_count}")
    print(f"auto_option_count: {summary.auto_option_count}")
    print(f"true_positive_option_count: {summary.true_positive_option_count}")


def _print_mismatches(file_results, *, limit: int) -> None:
    shown = 0
    print("")
    print("Mismatches")
    for result in file_results:
        for item in result.per_id:
            if item.exact_set_match:
                continue
            print(f"{result.label} {item.ref} {item.token_id} {item.surface}")
            print(f"  reviewed: {', '.join(item.reviewed_analyses) or '∅'}")
            print(f"  auto: {', '.join(item.auto_analyses) or '∅'}")
            print(f"  missing: {', '.join(item.missing_analyses) or '∅'}")
            print(f"  extra: {', '.join(item.extra_analyses) or '∅'}")
            shown += 1
            if shown >= limit:
                return


if __name__ == "__main__":
    raise SystemExit(main())
