---
name: audit-ugaritic-analysis-reconstruction
description: Verify that Ugaritic morphological analyses reconstruct the edited linguistic reading in reviewed or automatic TSV files. Use when designing or reviewing marker encodings, diagnosing linter reconstruction failures, checking migrated token analyses, interpreting KTU erasure, redundant-sign, missing-sign, or restoration markup, or distinguishing a structurally valid parse from one that merely resembles the edited word. Handles intentional `MERGE WITH` split-token rows as explicit exceptions; does not decide lexical or morphological correctness by reconstruction alone.
---

# Audit Ugaritic Analysis Reconstruction

Treat reconstruction as a hard encoding invariant, then evaluate linguistic correctness separately.

## Understand the Decoder

1. Read `references/reconstruction-semantics.md` completely.
2. When a raw or reviewed sign span contains KTU editorial notation, also read `references/editorial-sign-semantics.md` completely.
3. Use the repository's own reconstruction helper rather than an ad hoc character-stripper.
4. Remember that a reconstructing analysis can still assign a letter to the wrong morpheme or use the wrong stem marker.

## Check One or More Analyses

Resolve this skill's directory from its `SKILL.md`, then run:

```bash
python3 <skill-dir>/scripts/check_reconstruction.py --pair nšt ']n](nš(y[t'
python3 <skill-dir>/scripts/check_reconstruction.py reviewed/KTU\ 1.5.tsv
```

The script auto-detects labeled TSV columns, uses `agent/pipeline/steps/analysis_utils.py`, skips unresolved `?` analyses, and reports intentional `MERGE WITH` rows separately. A nonzero exit means at least one ordinary analysis failed reconstruction.

## Diagnose a Mismatch

1. Derive the expected edited reading from the sign span, then compare it with the decoder's reconstructed output.
2. Locate the first differing letter.
3. Classify it as lexical, formative, inflectional, suffixal, enclitic, allographic, editorial, or part of a migrated merged token.
4. Check whether `(` was expected to hide more than one letter; it binds only one atom.
5. Check marker ordering and whether a written letter was incorrectly represented as reconstructed or vice versa.
6. For editorial notation, distinguish the physical token, edited reading, selected lexeme, and final analysis. Morphology targets the edited reading; do not repeat sign-level deletions with `&` or `(`.
7. Consult DULAT, POS, comments, context, and the relevant specialized skill before editing.

For N-stem verbs, use `$parse-ugaritic-n-stems`. For migration-related merged rows, use `$audit-split-token-migrations`.

## Apply and Validate a Fix

- Preserve comments, alternatives, sign spans, and IDs.
- Do not alter a lexeme or POS merely to make the character decoder pass.
- Add a positive reconstruction test and a near-miss negative test when changing parser or decoder behavior.
- If the encoding expresses a productive rule, use `$review-linguistic-rule-change` to propagate it through reviewed data, parser logic, linter logic, documentation, and tests.
- Re-run this audit and the repository linter on the changed scope. Report merged-token exceptions and unresolved rows explicitly.
