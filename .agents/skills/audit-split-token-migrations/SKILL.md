---
name: audit-split-token-migrations
description: Audit reviewed Ugaritic TSVs after tokenization migration for adjacent split-token pairs, paired MERGE comments, identical whole-word analyses, reconstruction against concatenated surfaces, and preservation of legacy comments. Use after TF token splits or when migrated component rows became unresolved. Do not assume every token split represents one lexical word.
---

# Audit Split-Token Migrations

Distinguish physical splitting of one lexical word from genuine lexical resegmentation. The correct treatment differs, but both must preserve the original editorial comment.

## Read the Split Model

Read `references/split-token-model.md` completely before classifying candidates.

## Run the Structural Audit

Resolve this skill’s directory from its active `SKILL.md`, then run:

```bash
python3 <skill-dir>/scripts/audit_split_token_pairs.py reviewed
```

To verify comment preservation for one migration preview:

```bash
python3 <skill-dir>/scripts/audit_split_token_pairs.py \
  --before /path/to/legacy.tsv /path/to/migrated.tsv
```

The script validates structured merge pairs and, with `--before`, reports legacy comments absent from the migrated file. It exits nonzero on structural or preservation failures.

## Inspect Migration Candidates

Search all rows marked as migration fallbacks or unresolved new components:

```bash
rg -n "Migrated from legacy|DULAT: NOT FOUND|MERGE WITH THE" reviewed -g "*.tsv"
```

For each changed tokenization, inspect the old row, all new adjacent rows, target raw sign spans, automatic parses, and DULAT evidence. Classify it as whole-word physical split, lexical resegmentation, or unresolved.

Do not automatically convert every adjacent split into a MERGE pair. Do not leave a component as `?` merely because it lacks an independent DULAT surface form when the legacy comment or combined analysis resolves it.

## Repair Conservatively

- For a whole lexical word, repeat the full analysis, DULAT head, POS, and gloss on both rows. Use `MERGE WITH THE NEXT: explanation` and `MERGE WITH THE PREVIOUS.` comments.
- For lexical resegmentation, give each component its own justified analysis while preserving the old comment on the relevant new rows.
- For unresolved cases, retain the migration marker and explain what evidence is missing.

Preserve IDs, surfaces, sign spans, alternatives, citations, and unrelated comments.

## Validate

1. Re-run the bundled audit and require zero failures.
2. Run the repository linter, which jointly validates structured merge pairs and suppresses inappropriate per-half reconstruction errors.
3. Run `tests.test_linter_merge_pairs` and migration tests after changing migration or linter logic.
4. Inspect the diff for comments lost, copied to the wrong component, or replaced by generic migration text.
5. Report pair count, repaired pairs, lexical resegmentations, unresolved candidates, and preserved-comment failures.

