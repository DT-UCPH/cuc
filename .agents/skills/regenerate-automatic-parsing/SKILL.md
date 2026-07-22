---
name: regenerate-automatic-parsing
description: Regenerate Ugaritic automatic parsing TSVs with the current parser, either for the latest Text-Fabric release or for named historical TF versions, then refresh and evaluate lint and reviewed-agreement reports. Use when automatic parsing is stale after parser changes or when specific version directories must be rebuilt. Do not migrate reviewed TSVs unless separately requested.
---

# Regenerate Automatic Parsing

Keep parser version, TF source version, output directory, and report scope explicit. A current parser can legitimately regenerate several historical TF tokenizations.

## Choose the Route

1. Read `references/version-routing.md` completely.
2. Inspect the requested version directories, current TF releases, output status, and parser diff.
3. Decide between a clean rebuild and an explicitly requested incremental refresh.
4. Decide between latest-version and exact historical-version regeneration.
5. Snapshot the matching output and lint baseline before any pipeline command can rewrite them.
6. Start with a dry run and keep the per-step change-ratio safeguard enabled.

For a clean rebuild, always generate into an empty staging output directory. The current
pipeline treats `--include-existing` as “refine existing output in place”; it is not a clean
regeneration mode and is unsafe after a failed or interrupted run.

## Regenerate the Latest Version

From `agent/`:

```bash
./.venv/bin/python scripts/regenerate_tablets_and_reports.py \
  --dry-run --enforce-step-change-limit
```

Review the selected source and file set. Then create an empty temporary staging root and
run the wrapper with explicit staged output and report paths:

```bash
REGEN_STAGE="$(mktemp -d)"
./.venv/bin/python scripts/regenerate_tablets_and_reports.py \
  --out-dir "$REGEN_STAGE/auto/0.2.8" \
  --reports-dir "$REGEN_STAGE/reports" \
  --enforce-step-change-limit
```

Replace `0.2.8` with the latest version confirmed by the dry run. Limit with `--files`
when the user names tablets. Publish the staged directory only after validation; preserve
the exact previous version directory in a recoverable backup until the comparison is done.

## Regenerate an Exact Historical TF Version

Export each requested TF version explicitly:

```bash
./.venv/bin/python scripts/export_text_fabric_tablet_sources.py \
  --tf-version VERSION
```

Then parse that generated source into an empty staging output directory:

```bash
REGEN_STAGE="$(mktemp -d)"
./.venv/bin/python scripts/run_tablet_parsing_pipeline.py \
  --source-dir generated_sources/cuc_tablets_tsv/VERSION \
  --out-dir "$REGEN_STAGE/auto/VERSION" \
  --skip-source-refresh \
  --max-step-change-ratio 0.25
```

Repeat separately for every requested version. `--skip-source-refresh` is essential here:
without it, automatic latest-version detection can replace the intended historical source.
Do not add `--include-existing` during a clean historical rebuild.

## Validate and Review

1. Check pipeline summaries for source version, file count, token count, rows processed, rows changed, and steps near the change-ratio limit.
2. Require `0 <= changed_rows <= processed_rows` before interpreting a change ratio. A ratio above 100% is a counter defect, not evidence of a broad parser change.
3. Do not resume from output touched by a failed safeguard. Start again in a new empty staging directory.
4. Do not use `--allow-large-step-changes` merely to make a failed run pass. Inspect the responsible step. If the counter itself is invalid, disable it only inside isolated staging and rely on scoped diffs, lint, and agreement checks.
5. Run lint on the staged version and compare it with the external pre-regeneration baseline using the lint-regression skill or `scripts/compare_lint_errors.py`.
6. For reviewed tablets, run `scripts/score_reviewed_morphology.py` or use the reports produced by full regeneration. Treat score changes as evidence, not as permission to overwrite reviewed data.
7. Do not treat the wrapper's zero lint delta as sufficient evidence: the pipeline currently refreshes lint reports before its delta writer snapshots `before_latest`.
8. Inspect scoped diffs for only the requested `auto_parsing/VERSION` directories and intentionally refreshed reports. Confirm reviewed TSVs are unchanged.
9. Run relevant parser tests for changed steps, followed by the full unit suite when the parser change is broad.
10. Publish only the validated staged output. Keep the backup until the published tree has been rechecked.

If the user requests a commit, stage only requested generated versions, intentional reports, parser code, and tests. State the TF versions and current parser revision in the commit summary.
