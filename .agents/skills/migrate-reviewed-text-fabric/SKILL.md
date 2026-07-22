---
name: migrate-reviewed-text-fabric
description: Migrate manually reviewed Ugaritic TSV files to a new Text-Fabric tokenization and ID space while preserving analyses, alternatives, sign spans, glosses, and editorial comments. Use when a TF release splits, joins, renumbers, or changes reviewed tokens. Do not use merely to regenerate automatic parser output or to normalize unchanged reviewed morphology.
---

# Migrate Reviewed Text-Fabric

Treat reviewed annotations as irreplaceable editorial data and the target raw and automatic TSVs as alignment evidence. Preview every migration outside the reviewed tree before replacing a file.

## Establish the Migration Triple

1. Read `references/migration-invariants.md` completely.
2. Identify one reviewed source file, its raw TSV exported from the exact target TF version, and automatic parsing generated from that same raw TSV with the current parser.
3. Confirm tablet names, first and last reviewed references, target TF version, schemas, and sign-span availability.
4. Inspect `git status`. Preserve unrelated changes and never use a destructive reset.

Do not mix a raw file from one TF version with automatic output from another. Do not extend a partially reviewed tablet beyond its original first and last references.

## Preview the Migration

Run from `agent/` and always use `--out` for the first pass:

```bash
./.venv/bin/python scripts/migrate_reviewed_tablet.py \
  ../reviewed/FILE.tsv \
  generated_sources/cuc_tablets_tsv/VERSION/FILE.tsv \
  ../auto_parsing/VERSION/FILE.tsv \
  --out /tmp/FILE.migrated.tsv
```

Use a uniquely created temporary directory in actual work. Never point the preview output at the reviewed source.

## Review Alignment Decisions

Inspect every non-equal alignment block and every row containing either migration marker:

```bash
rg -n "Migrated from legacy|Token changed from previous|DULAT: NOT FOUND" \
  /tmp/FILE.migrated.tsv
```

For each split or join, classify it as:

- one lexical word distributed across physical tokens, requiring paired `MERGE WITH` comments and the whole analysis on both rows;
- one old token resegmented into independent lexemes, requiring a justified analysis for each new token;
- a genuinely unresolved token, where automatic fallback plus the migration marker is acceptable pending review.

Never accept `?` merely because a newly split component lacks an independent surface lookup. Use the legacy analysis, original comment, DULAT context, and combined surface to adjudicate it.

## Validate Before Replacement

1. Compare source and preview comments, duplicate alternatives, reference bounds, and sign spans.
2. If the split-token audit skill is available, run its bundled script with `--before` against the preview.
3. Lint the preview with the same DULAT/UDB configuration used for reviewed files.
4. Run the focused migration and merge-pair tests:

```bash
cd agent
./.venv/bin/python -m unittest \
  tests.test_reviewed_tablet_migrator \
  tests.test_linter_merge_pairs
```

5. Inspect a scoped diff. Require all old nonempty comments to survive verbatim inside some migrated comment unless the user explicitly approved rewriting one.

Only after validation, copy the preview over the reviewed file. Re-run lint and the split-token audit on the final path. Do not commit unless requested.

