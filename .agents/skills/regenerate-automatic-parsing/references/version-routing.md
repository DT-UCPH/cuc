# Regeneration Version Routing

## Separate the Versions

- **Parser version**: the checked-out code and configuration used to analyze tokens.
- **TF version**: the tokenization and token-ID source under `tf/VERSION`.
- **Automatic output version**: must match the TF source directory name under `auto_parsing/VERSION`.
- **Reviewed version**: manually curated material; regeneration never rewrites it by itself.
- **Clean rebuild**: bootstrap every requested source into an empty staging directory.
- **Incremental refresh**: refine existing generated output in place; use only when explicitly intended.

“Regenerate 0.2.6 and 0.2.7 with the latest parser” means current code applied separately to TF 0.2.6 and TF 0.2.7, not conversion of their inputs to the latest TF tokenization.

## Route Selection

### Latest available TF

Use `regenerate_tablets_and_reports.py` with explicit empty staging paths for output and
reports. Its internal pipeline uses `include_existing=True`: pointing it at the tracked
output directory refines existing TSVs rather than bootstrapping them again.

Enable `--enforce-step-change-limit`; the full-regeneration CLI otherwise permits large step changes by default.

### Named historical TF version

Export with `export_text_fabric_tablet_sources.py --tf-version VERSION`, then run
`run_tablet_parsing_pipeline.py` with explicit `--source-dir`, an empty staged
`--out-dir`, and `--skip-source-refresh`. Omit `--include-existing` for a clean rebuild.

### Named tablets only

Add `--files 'KTU X.tsv' ...` to the appropriate route. Verify that every requested name exists in the selected source directory.

An incremental named-tablet refresh may use `--include-existing` only when preserving and
re-refining existing alternatives is the stated goal. Do not confuse this with regeneration
from raw TF tokens.

## Transaction Boundary

1. Save the current automatic version and its lint output before running any parser command.
2. Generate into an empty temporary output directory.
3. Validate source version, tablet count, token count, lint fingerprints, reviewed agreement,
   representative rows, and scoped diffs.
4. Move the exact existing version directory to a recoverable backup.
5. Publish the staged directory at the matching `auto_parsing/VERSION` path.
6. Recheck the published tree before removing the backup.

The current full-regeneration wrapper calls the pipeline's report generator before its delta
writer snapshots `before_latest`. Therefore a reported zero lint delta can compare the new
report with itself. Use the externally saved pre-run lint as the real baseline.

## Safety Signals

Stop and inspect when:

- the source summary reports a different TF version;
- output paths do not end in the selected version;
- a refinement step exceeds its change-ratio threshold;
- a step reports more changed rows than processed rows;
- file or token counts unexpectedly shrink;
- generated diffs touch reviewed files;
- lint gains new stable-signature errors;
- reviewed agreement drops materially in the rule family that changed.

Do not continue from partially refined output after a failure. Start over in a new empty
staging directory. Do not clean an output version with broad deletion commands; publish by
moving only the exact validated version directory while retaining a recoverable backup.

## Commit Scope

Regeneration can produce very large diffs. Before committing, verify:

- every changed output belongs to a requested TF version;
- reports correspond to the output version being evaluated;
- no cache database or local source artifact is staged;
- no reviewed file was incidentally rewritten;
- parser code and tests are included only when they were part of the requested change.
