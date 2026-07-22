# Regeneration Version Routing

## Separate the Versions

- **Parser version**: the checked-out code and configuration used to analyze tokens.
- **TF version**: the tokenization and token-ID source under `tf/VERSION`.
- **Automatic output version**: must match the TF source directory name under `auto_parsing/VERSION`.
- **Reviewed version**: manually curated material; regeneration never rewrites it by itself.

“Regenerate 0.2.6 and 0.2.7 with the latest parser” means current code applied separately to TF 0.2.6 and TF 0.2.7, not conversion of their inputs to the latest TF tokenization.

## Route Selection

### Latest available TF

Use `regenerate_tablets_and_reports.py`. It can refresh the generated source, rebuild outputs, generate lint reports, and calculate reviewed-agreement deltas.

Enable `--enforce-step-change-limit`; the full-regeneration CLI otherwise permits large step changes by default.

### Named historical TF version

Export with `export_text_fabric_tablet_sources.py --tf-version VERSION`, then run `run_tablet_parsing_pipeline.py` with explicit `--source-dir`, `--out-dir`, `--include-existing`, and `--skip-source-refresh`.

### Named tablets only

Add `--files 'KTU X.tsv' ...` to the appropriate route. Verify that every requested name exists in the selected source directory.

## Safety Signals

Stop and inspect when:

- the source summary reports a different TF version;
- output paths do not end in the selected version;
- a refinement step exceeds its change-ratio threshold;
- file or token counts unexpectedly shrink;
- generated diffs touch reviewed files;
- lint gains new stable-signature errors;
- reviewed agreement drops materially in the rule family that changed.

Do not clean an output version with broad deletion commands. Let the exporter’s scoped cleaning and pipeline’s explicit paths control generated files.

## Commit Scope

Regeneration can produce very large diffs. Before committing, verify:

- every changed output belongs to a requested TF version;
- reports correspond to the output version being evaluated;
- no cache database or local source artifact is staged;
- no reviewed file was incidentally rewritten;
- parser code and tests are included only when they were part of the requested change.

