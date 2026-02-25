# `l + Body-Part` Compound Prepositions

## Purpose

Normalize frequent lexicalized `l + X` body-part sequences where `X` functions
as part of a compound preposition.

Current targets:

- `l + pˤn` -> `pˤn` as `n. f.`, gloss `at the feet of`
- `l + ẓr` -> `ẓr` as `n. m.`, gloss `upon`

## Pipeline Step

Implemented as `LBodyCompoundPrepDisambiguator` in:

- `pipeline/steps/l_body_compound_prep.py`

Registered after `l-kbd-compound-prep` and before `k-functor-bigram-context`.

## Rule

For each token-group pair:

1. Detect `l` followed by a configured target surface.
2. Verify the second token-group contains the expected DULAT-aligned analysis.
3. Collapse `l` to a single `l(I)` row.
4. Collapse the second token-group to one canonical row with noun
   POS and contextual gloss payload.

## Linter Parity

`linter/lint.py` warns when these sequences are not in canonical payload form:

- `Compound preposition \`l pˤn\` should use single readings: l(I) and pˤn/ with POS \`n. f.\` and gloss \`at the feet of\``
- `Compound preposition \`l ẓr\` should use single readings: l(I) and ẓr(I)/ with POS \`n. m.\` and gloss \`upon\``
