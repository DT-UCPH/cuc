# cuc-morph

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.10695308.svg)](https://doi.org/10.5281/zenodo.10695308)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC_BY--NC_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

This is an experiment on semi-automatic morphological parsing/agent-assisted data labeling for Ugaritic cuneiform texts. It is still work in progress.

This work is based on [DT-UCPH/cuc](https://github.com/DT-UCPH/cuc), if you want to cite, please cite them.



## Local Lint Reports

This repository now generates morphology lint reports locally and commits them under `reports/`.

### One-time setup

1. Create Python 3.13 virtual environment: `UV_CACHE_DIR=.uv-cache uv venv --python 3.13 .venv`
2. Configure tracked Git hooks: `./scripts/install_git_hooks.sh`

### Pre-commit behavior

On every commit attempt, the pre-commit hook:

1. Runs `ruff format` and `ruff check --fix` on staged Python files
2. Runs `ruff check` on staged Python files and fails commit on any warning/error
3. Runs the full test suite (`python -m unittest discover -s tests -v`) and fails commit if tests fail
4. For lint-relevant staged changes (`out/*.tsv`, `linter/**`, report tooling), runs `scripts/generate_lint_reports.py` with local DB access (`sources/dulat_cache.sqlite`, `sources/udb_cache.sqlite`)
5. Regenerates `reports/*` and stages updated Python/report files automatically

Generated files include:

- `reports/lint_report.txt`
- `reports/lint_summary.md`
- `reports/lint_stats.json`
- `reports/lint_history.json`
- `reports/lint_severity_trend.svg`
- `reports/lint_issue_types_trend.svg`
- `reports/lint_trends.md`

## Tablet Parsing Pipeline

Use the reusable pipeline to process new tablets from `cuc_tablets_tsv` into `out` and regenerate reports:

- Dry-run target discovery: `UV_CACHE_DIR=.uv-cache uv run --python .venv/bin/python python scripts/run_tablet_parsing_pipeline.py --dry-run`
- Parse only missing tablets (default): `UV_CACHE_DIR=.uv-cache uv run --python .venv/bin/python python scripts/run_tablet_parsing_pipeline.py`
- Parse specific tablets: `UV_CACHE_DIR=.uv-cache uv run --python .venv/bin/python python scripts/run_tablet_parsing_pipeline.py --files 'KTU 1.181.tsv' 'KTU 1.182.tsv'`
- Reprocess existing outputs too: `UV_CACHE_DIR=.uv-cache uv run --python .venv/bin/python python scripts/run_tablet_parsing_pipeline.py --include-existing`
- Tighten/relax step safety threshold: `python scripts/run_tablet_parsing_pipeline.py --max-step-change-ratio 0.20` or `python scripts/run_tablet_parsing_pipeline.py --allow-large-step-changes`

Pipeline stages are:

1. Start from prepared source files in `cuc_tablets_tsv/*.tsv` (token IDs + `# ... KTU ...` line references). The CUC-to-TSV conversion happens upstream.
2. Build first-pass analyses from DULAT (`scripts/bootstrap_tablet_labeling.py`): for each surface form, fill columns 3-6 from DULAT form matches; keep unresolved rows explicit as `DULAT: NOT FOUND`.
3. Re-rank and refine candidates with context (`scripts/refine_results_mentions.py`): combine direct form matches with conservative suffix splitting, then score using local context, reverse references (`dulat_reverse_refs`, `ktu_to_dulat`), and attestation/tablet-family signals.
4. Keep the best aligned options per token: up to 3 analysis/DULAT/POS/gloss options per row (or 1 when evidence is clearly stronger), while preserving meaningful human comments.
5. Run conservative normalization (`pipeline/instruction_refiner.py`): clean character/POS formatting, convert unresolved rows to `?` in cols 3-6, and add noun/adjective gender where DULAT gives a unique value.
6. Apply ordered linguistic heuristics with safeguards (`pipeline/tablet_parsing.py`): formula disambiguation, plural/suffix/feminine and weak-verb normalization, KTU1-specific pruning, controlled ambiguity expansion, onomastic/generic overrides, and schema formatting (first and last).
7. Regenerate lint reports in `reports/`.

## GitHub Actions

GitHub Actions no longer runs the linter itself. It parses committed files under `reports/` and publishes the summary in the workflow UI.
