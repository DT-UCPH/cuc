"""Compare legacy and spaCy-based `l`-context strategies on the tablet corpus."""

from __future__ import annotations

import argparse
import difflib
import shutil
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if TYPE_CHECKING:
    from pipeline.steps.base import RefinementStep


def _parse_args() -> argparse.Namespace:
    from project_paths import get_project_paths

    paths = get_project_paths(Path(__file__).resolve())
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=paths.default_source_dir())
    parser.add_argument("--dulat-db", type=Path, default=paths.default_dulat_db())
    parser.add_argument("--udb-db", type=Path, default=paths.default_udb_db())
    parser.add_argument("--source-glob", default="KTU *.tsv")
    parser.add_argument("--files", nargs="*", default=None)
    parser.add_argument("--max-diffs", type=int, default=10)
    return parser.parse_args()


def _apply_steps(paths: list[Path], steps: list[RefinementStep]) -> None:
    for path in paths:
        for step in steps:
            step.refine_file(path)


def _first_diff_excerpt(legacy_path: Path, spacy_path: Path, max_lines: int = 60) -> str:
    diff = difflib.unified_diff(
        legacy_path.read_text(encoding="utf-8").splitlines(),
        spacy_path.read_text(encoding="utf-8").splitlines(),
        fromfile=str(legacy_path.name),
        tofile=str(spacy_path.name),
        lineterm="",
    )
    return "\n".join(line for _, line in zip(range(max_lines), diff, strict=False))


def main() -> int:
    from pipeline.l_context_step_factory import build_legacy_l_context_steps
    from pipeline.tablet_parsing import PipelineConfig, TabletParsingPipeline

    args = _parse_args()
    with tempfile.TemporaryDirectory(prefix="compare-l-context-") as tmp_dir:
        temp_root = Path(tmp_dir)
        pre_dir = temp_root / "pre"
        legacy_dir = temp_root / "legacy"
        spacy_dir = temp_root / "spacy"
        pre_dir.mkdir()

        pre_pipeline = TabletParsingPipeline(
            PipelineConfig(
                source_dir=args.source_dir,
                out_dir=pre_dir,
                dulat_db=args.dulat_db,
                udb_db=args.udb_db,
                include_existing=False,
                source_glob=args.source_glob,
            )
        )
        targets = pre_pipeline.select_targets(explicit_names=args.files)
        target_names = [path.name for path in targets]
        pre_pipeline.bootstrap_targets(targets)
        pre_pipeline.refine_targets(targets)
        pre_pipeline.instruction_refine_targets(targets)
        _apply_steps(
            [pre_dir / name for name in target_names],
            list(pre_pipeline.pre_l_context_steps),
        )

        shutil.copytree(pre_dir, legacy_dir)
        shutil.copytree(pre_dir, spacy_dir)

        legacy_pipeline = TabletParsingPipeline(
            PipelineConfig(
                source_dir=args.source_dir,
                out_dir=legacy_dir,
                dulat_db=args.dulat_db,
                udb_db=args.udb_db,
                include_existing=True,
                source_glob=args.source_glob,
            )
        )
        spacy_pipeline = TabletParsingPipeline(
            PipelineConfig(
                source_dir=args.source_dir,
                out_dir=spacy_dir,
                dulat_db=args.dulat_db,
                udb_db=args.udb_db,
                include_existing=True,
                source_glob=args.source_glob,
            )
        )

        legacy_targets = [legacy_dir / name for name in target_names]
        spacy_targets = [spacy_dir / name for name in target_names]
        _apply_steps(legacy_targets, build_legacy_l_context_steps())
        _apply_steps(legacy_targets, list(legacy_pipeline.post_l_context_steps))
        _apply_steps(spacy_targets, list(spacy_pipeline.l_context_steps))
        _apply_steps(spacy_targets, list(spacy_pipeline.post_l_context_steps))

        differing_files: list[tuple[str, str]] = []
        for name in target_names:
            legacy_path = legacy_dir / name
            spacy_path = spacy_dir / name
            if legacy_path.read_text(encoding="utf-8") == spacy_path.read_text(encoding="utf-8"):
                continue
            differing_files.append((name, _first_diff_excerpt(legacy_path, spacy_path)))

        print(f"Compared {len(target_names)} tablets.")
        print(f"Differing outputs: {len(differing_files)}")
        for name, excerpt in differing_files[: args.max_diffs]:
            print(f"\n=== {name} ===")
            print(excerpt)
        return 1 if differing_files else 0


if __name__ == "__main__":
    raise SystemExit(main())
