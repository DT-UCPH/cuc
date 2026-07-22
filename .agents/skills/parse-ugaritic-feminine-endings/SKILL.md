---
name: parse-ugaritic-feminine-endings
description: Audit and correct Ugaritic feminine noun and feminine divine-name ending encodings in reviewed TSV files. Use for `n. f.` or `DN f.` analyses involving lexical final `-t`, singular `/t`, plural `/t=`, dual `/tm`, suffixes, enclitics, allographs, or tokens split during a tokenization migration. Do not use to infer an uncertain lexeme or number from surface spelling alone.
---

# Parse Ugaritic Feminine Endings

Apply the project convention that lexical final `t` is both lexeme material and a nominal ending. Make narrow, reviewable corrections without changing token identity or editorial evidence.

## Establish Scope and Authority

1. Determine whether the request is an audit, an edit, or both. Do not edit for an audit-only request.
2. Locate the reviewed TSV files in scope and inspect the surrounding rows, not isolated search hits.
3. Read `references/encoding-rules.md` completely before deciding any correction.
4. If the repository has `lexicon_and_grammar/tagging_conventions_cuc.md`, treat it as authoritative when it differs from this skill.
5. Use the declared DULAT lexeme, its homonym, DULAT forms, reviewed POS, comments, and parallel attestations together. Surface spelling alone is insufficient.

## Audit Deterministic Errors

Resolve this skill's directory from the active `SKILL.md`, then run:

```bash
python3 <skill-dir>/scripts/audit_feminine_endings.py reviewed
```

Pass individual TSV paths instead of `reviewed` when the user limits the scope. The script reports only mechanically defensible candidates and exits nonzero when it finds any. Do not treat a clean audit as proof that every ambiguous analysis is correct.

Also search feminine rows directly when investigating a named form or rule:

```bash
rg -n "n\. f\.|DN f\." reviewed -g "*.tsv"
```

## Classify Each Candidate

For every candidate, identify:

- whether the DULAT lexeme itself ends in `t`;
- singular, plural, absolute dual, construct dual, suffix, or enclitic morphology;
- whether written `t` belongs to the ending, an allograph, or exceptional material;
- whether a tokenization split requires a whole-word analysis on more than one row;
- whether the POS number must change because an authoritative lexical form rules out the existing tag.

If the evidence does not select one analysis, preserve the reviewed row and report the ambiguity. Never normalize irregular or masculine plurals merely because the noun is feminine.

## Edit Conservatively

When asked to correct files:

1. Change the morphological analysis and, only when required by authoritative evidence, the POS.
2. Preserve all eight reviewed TSV columns, token IDs, surface forms, sign spans, lexemes, glosses, and comments.
3. Preserve homonym placement, `&` allographs, reconstructed letters, suffixes, enclitics, and alternative rows.
4. For migrated split tokens, preserve the original comment on the relevant row. A whole merged lexeme may intentionally be repeated on both component rows.
5. Keep unrelated worktree changes untouched.

## Validate the Result

1. Re-run `audit_feminine_endings.py` on the edited scope; require zero reported issues.
2. Run the repository linter on the same files. Separate pre-existing baseline findings from findings on changed rows.
3. Where the repository exposes a surface reconstruction helper, verify each changed analysis against the surface. Treat rows marked `MERGE WITH` as split-token exceptions and reconstruct the merged token instead.
4. Inspect the scoped diff and confirm that only intended analysis or POS fields changed and no comments disappeared.
5. Summarize corrected rows by rule and list any unresolved ambiguous rows. Do not commit unless the user requests a commit.
