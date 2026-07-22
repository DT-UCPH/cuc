---
name: parse-ugaritic-gt-stems
description: Audit and correct Ugaritic Gt-stem verb encodings in reviewed or automatic TSV files. Use for `vb Gt` analyses involving the infixed `-t-`, `]t]`, elided root-initial `/n/` or `/h/`, aleph-vowel spellings, metathesis, possible Gt/Št ambiguity, or proposals to infer reflexive, reciprocal, autobenefactive, or anticausative meaning. Do not infer Gt from a surface `t` or reflexive translation alone.
---

# Parse Ugaritic Gt-Stems

Keep the written Gt formative separate from lexical radicals. Treat formal identification and semantic classification as two different decisions.

## Establish the Analysis

1. Read `references/gt-stem-encoding.md` completely.
2. Inspect the full TSV row, surrounding clause, comments, parallels, and DULAT form morphology.
3. Confirm Gt from an attested form or decisive root-and-context evidence. Do not promote Chapter 6's debated forms automatically.
4. Determine conjugation and agreement independently from stem.
5. Encode the lexical root in its historical order even when its first radical is not written.

## Audit the Scope

Resolve this skill's directory from its `SKILL.md`, then run:

```bash
python3 <skill-dir>/scripts/audit_gt_stems.py reviewed
python3 <skill-dir>/scripts/audit_gt_stems.py auto_parsing/0.2.8
python3 <skill-dir>/scripts/audit_gt_stems.py --id 160585 reviewed/KTU\ 1.14.tsv
```

The audit detects firm `vb Gt` rows without `]t]` and noncanonical ordering of an elided initial `/n/` or `/h/`. It intentionally exempts `Gt?` and cannot establish a disputed stem from spelling alone.

## Correct Conservatively

- Mark a written Gt formative as `]t]` after the first lexical radical.
- Reconstruct an elided first radical before the formative: `(n]t]pl[` and `(h]t]lk[`.
- For I-aleph forms written with `i`, keep the lexical radical and written vowel distinct: `(ʔ&i]t]...`.
- Preserve explicit metathesis as written and explain it in the comment.
- Keep assimilated I-dental forms uncertain unless independent evidence establishes Gt; do not label a non-`t` sign as written `]t]`.
- Do not encode `reflexive`, `reciprocal`, or `autobenefactive` in the morphological string. Record a semantic decision in the gloss/comment only when the clause supports it.
- Preserve IDs, readings, alternatives, glosses, comments, and migration provenance.
- Fix productive parser or linter defects at their source and add focused tests. Do not regenerate automatic TSVs or commit unless requested.

## Validate

1. Re-run `audit_gt_stems.py` on the changed scope.
2. Verify each changed analysis reconstructs the surface.
3. Run focused paradigm-matcher and verb-stem linter tests.
4. Run the repository linter; separate new findings from its existing baseline.
5. Inspect the scoped diff for semantic overreach and unrelated normalization.
6. Report deterministic changes separately from interpretive candidates.
