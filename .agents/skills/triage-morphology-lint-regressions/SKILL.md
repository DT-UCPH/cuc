---
name: triage-morphology-lint-regressions
description: Compare morphology linter results against an appropriate baseline while ignoring Text-Fabric token renumbering and row-number churn, then identify and explain only newly introduced error occurrences. Use for failing pre-commit lint, regenerated automatic TSVs, parser-rule changes, or “fix linter” requests. Diagnose only unless the user also asks to implement fixes.
---

# Triage Morphology Lint Regressions

Compare like with like: same logical file and version, same linter code, same database configuration, and different content snapshots. A large historical lint baseline is not itself a regression.

## Establish the Comparison

1. Read `references/regression-fingerprints.md` completely.
2. Determine whether the candidate is staged, unstaged, regenerated, or a temporary migration preview.
3. Select the matching baseline: normally `HEAD` for the same logical path and TF version.
4. Record the exact linter, DULAT database, UDB database, input format, and override tables.

If setup or database loading fails, report an environmental failure rather than treating missing output as a clean lint run.

## Use the Existing Stable Comparator

For staged automatic-parsing files, the tracked hook already performs the correct comparison:

```bash
.githooks/pre-commit
```

For manual runs, lint baseline and candidate separately, then compare:

```bash
cd agent
./.venv/bin/python scripts/compare_lint_errors.py \
  /tmp/baseline.lint /tmp/candidate.lint
```

The comparator exits nonzero only when candidate ERROR occurrences remain after multiset subtraction of stable baseline signatures.

## Investigate Each New Occurrence

For every reported regression:

1. Open the candidate row, surrounding reference, duplicate alternatives, and comments.
2. Locate the corresponding baseline token by logical file, surface, context, and diagnostic—not by mutable TF ID alone.
3. Decide whether the new occurrence comes from data, parser behavior, linter behavior, tokenization, or changed external evidence.
4. Check whether one source defect produces several downstream diagnostics; identify the earliest actionable cause.
5. Keep warnings and informational findings separate from commit-blocking errors unless the user asks for broader cleanup.

## Report or Fix

For diagnosis-only requests, report new errors, causes, affected files, and the smallest plausible fix without editing.

When fixes are requested, change the authoritative source: reviewed row, parser rule, override, or linter predicate. Add a regression test, re-lint baseline and candidate with identical settings, and require zero new ERROR occurrences. Do not suppress a valid diagnostic merely to make the comparator pass.

