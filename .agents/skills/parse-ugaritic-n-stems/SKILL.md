---
name: parse-ugaritic-n-stems
description: Audit and correct Ugaritic N-stem verb encodings in reviewed or automatic TSV files. Use for `vb N` analyses involving visible `]n]` or reconstructed `(]n]` formatives, root-initial `/n/`, assimilated nun, weak radicals, prefix or suffix conjugation, or incorrect generic `:n` stem labels. Do not infer an N stem from surface `n` alone.
---

# Parse Ugaritic N-Stems

Represent the N-stem formative independently from lexical radicals and verbal endings. Require both linguistic evidence and correct surface reconstruction.

## Establish the Analysis

1. Read `references/n-stem-encoding.md` completely.
2. Inspect the full TSV row, context, comments, and parallel reviewed attestations.
3. Confirm the N stem from DULAT morphology, a cited lexical source, or decisive textual evidence. Do not classify a verb as N solely because its surface starts with `n`.
4. Identify the conjugation, person/number/gender ending, root radicals, and which formative or radical is actually written.
5. If the repository tagging conventions disagree with this skill, follow the repository and report the discrepancy.

## Audit the Scope

Resolve this skill's directory from its `SKILL.md`, then run:

```bash
python3 <skill-dir>/scripts/audit_n_stems.py reviewed
python3 <skill-dir>/scripts/audit_n_stems.py auto_parsing/0.2.8
python3 <skill-dir>/scripts/audit_n_stems.py --id 158704 reviewed/KTU\ 1.5.tsv
```

Pass individual TSV paths when the user limits the scope. The audit finds structural errors; it does not prove that every `vb N` decision is linguistically correct.

Classify every hit as confirmed, negative, ambiguous, or a migrated split-token exception. Search reviewed and automatic files independently and report their counts separately.

## Correct Conservatively

- Use `]n]` for a written N-stem formative and `(]n]` for a reconstructed/unwritten formative.
- Use a separate `(n` when a lexical root-initial `/n/` is not separately written.
- Mark each unwritten weak radical separately. Because `(` binds one atom, `]n](nšy[t` leaves `y` visible; use `]n](nš(y[t` for surface `nšt`.
- Do not use `:n` as a generic substitute for the N-stem formative.
- Preserve IDs, sign spans, alternatives, glosses, comments, and migration provenance.
- For a productive parser defect, fix the rule source and add tests. Do not regenerate automatic TSVs or commit unless requested.

Use `$audit-ugaritic-analysis-reconstruction` to prove the edited analysis reconstructs its surface. Use `$review-linguistic-rule-change` when expert feedback may establish a broader rule.

## Validate

1. Re-run `audit_n_stems.py` on the changed scope.
2. Verify changed analyses with the reconstruction audit.
3. Run focused candidate-generation, refinement-step, and linter tests.
4. Run the repository linter and separate changed-row findings from its existing baseline.
5. Inspect the scoped diff for lost comments or unrelated normalization.
6. Report the accepted rule, changed rows, automatic-parser status, and unresolved cases.
