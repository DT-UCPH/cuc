# `l(III)` / `l(IV)` Context Disambiguation

## Purpose

Disambiguate `l` tokens in DULAT-attested contexts where:

- `l (III)` = emphatic/functor (`certainly`)
- `l (IV)` = vocative interjection (`oh!`)

This avoids overloading `l(I)`/`l(II)` in known epic and ritual formulas.

## Pipeline Step

Implemented as `LFunctorVocativeContextDisambiguator` in:

- `pipeline/steps/l_functor_vocative_context.py`

Registered in `TabletParsingPipeline` after `l-negation-verb-context`.

## Reference Matcher

Shared rule source:

- `pipeline/config/l_functor_vocative_refs.py`

It normalizes section labels to canonical keys and supports:

- `KTU 1.4 V:59` style
- `KTU 1.24 15` style

Keys are section-aware (`<tablet> <column>:<line>` when a Roman column is
present), so `KTU 1.4 I:23` and `KTU 1.4 VII:23` are not conflated.

## Disambiguation Logic

For each `l` token group:

1. Read current section reference from nearest separator line.
2. Detect whether the following token group has a verbal reading (`pos` contains `vb`).
3. Resolve expected homonym from DULAT reference sets:
   - `l(III)` refs force `l(III)`.
   - `l(IV)` refs force `l(IV)` only before non-verbal next tokens.
   - Overlap refs (e.g. `1.17 I:23`) choose:
     - next verbal -> `l(III)`
     - next non-verbal -> `l(IV)`
4. Collapse the token to a single reading; if target variant is missing, synthesize canonical row:
   - `l(III) | l (III) | functor | certainly`
   - `l(IV) | l (IV) | interj. | oh!`

## Linter Parity

`linter/lint.py` uses the same matcher and emits warnings when context-constrained
tokens are not single-target:

- `DULAT context requires a single l(III) reading`
- `DULAT context requires a single l(IV) reading`
