# `k(III)` Bigram Context

## Purpose

Disambiguate frequent `k` bigrams where context strongly supports the
subordinating/completive functor reading (`k(III)`, gloss `when`).

Current target second-token surfaces:

- `yraš`
- `tld`
- `yṣḥ`
- `yiḫd`
- `ygˤr`

## Pipeline Step

Implemented as `KFunctorBigramContextDisambiguator` in:

- `pipeline/steps/k_functor_bigram_context.py`

Registered after `l-body-compound-prep`.

## Rule

For each `k` token-group:

1. Detect that the next token surface is in the configured target set.
2. Require verbal evidence on the next token-group (`pos` contains `vb`).
3. Collapse `k` to a single `k(III)` row:
   - `k(III) | k (III) | Subordinating or completive functor | when`

## Linter Parity

`linter/lint.py` warns when targeted bigrams are not single-`k(III)`:

- `Formula bigram \`k <surface>\` should use a single k(III) reading`
