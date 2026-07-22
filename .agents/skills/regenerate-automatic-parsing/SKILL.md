---
name: regenerate-automatic-parsing
description: Regenerate Ugaritic automatic parsing TSVs with the current parser, either for the latest Text-Fabric release or for named historical TF versions, then refresh and evaluate lint and reviewed-agreement reports. Use when automatic parsing is stale after parser changes or when specific version directories must be rebuilt. Do not migrate reviewed TSVs unless separately requested.
---

# Regenerate Automatic Parsing

Keep parser version, TF source version, output directory, and report scope explicit. A current parser can legitimately regenerate several historical TF tokenizations.

## Choose the Route

1. Read `references/version-routing.md` completely.
2. Inspect the requested version directories, current TF releases, output status, and parser diff.
3. Decide between latest-version full regeneration and exact historical-version regeneration.
4. Start with a dry run and keep the per-step change-ratio safeguard enabled.

## Regenerate the Latest Version

From `agent/`:

```bash
./.venv/bin/python scripts/regenerate_tablets_and_reports.py \
  --dry-run --enforce-step-change-limit
```

Review the selected source, output, and file set, then run the same command without `--dry-run`. Limit with `--files` when the user names tablets.

## Regenerate an Exact Historical TF Version

Export each requested TF version explicitly:

```bash
./.venv/bin/python scripts/export_text_fabric_tablet_sources.py \
  --tf-version VERSION
```

Then parse that generated source into the matching output directory:

```bash
./.venv/bin/python scripts/run_tablet_parsing_pipeline.py \
  --source-dir generated_sources/cuc_tablets_tsv/VERSION \
  --out-dir ../auto_parsing/VERSION \
  --include-existing \
  --skip-source-refresh \
  --max-step-change-ratio 0.25
```

Repeat separately for every requested version. `--skip-source-refresh` is essential here: without it, automatic latest-version detection can replace the intended historical source.

## Validate and Review

1. Check pipeline summaries for source version, file count, token count, rows processed, rows changed, and steps near the change-ratio limit.
2. Do not use `--allow-large-step-changes` merely to make a failed run pass. Inspect the responsible step and obtain user direction if the broad change is intentional.
3. Run lint on the regenerated version and compare it with the matching pre-regeneration baseline using the lint-regression skill or `scripts/compare_lint_errors.py`.
4. For reviewed tablets, run `scripts/score_reviewed_morphology.py` or use the reports produced by full regeneration. Treat score changes as evidence, not as permission to overwrite reviewed data.
5. Inspect scoped diffs for only the requested `auto_parsing/VERSION` directories and intentionally refreshed reports. Confirm reviewed TSVs are unchanged.
6. Run relevant parser tests for changed steps, followed by the full unit suite when the parser change is broad.

If the user requests a commit, stage only requested generated versions, intentional reports, parser code, and tests. State the TF versions and current parser revision in the commit summary.

