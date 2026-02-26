# `l + kbd(I)` Compound Preposition

## Purpose

Normalize `l kbd` sequences where `kbd(I)` functions as part of a compound
preposition.

Target payload:

- `l`: `l(I) | l (I) | prep. | to`
- `kbd`: `kbd(I)/ | kbd (I) | n. | within`

## Pipeline Step

Implemented as `LKbdCompoundPrepDisambiguator` in:

- `pipeline/steps/l_kbd_compound_prep.py`

Registered in `TabletParsingPipeline` after `l-functor-vocative-context`.

## Rule

For each token-group pair:

1. Detect `l` immediately followed by `kbd`.
2. If the `kbd` group contains `kbd(I)`:
   - collapse `l` group to a single `l(I)` row,
   - collapse `kbd` group to a single `kbd(I)` row and set
     `POS=n.`, `gloss=within`.
3. Preserve token id/surface/comments from retained rows.

This is intentionally conservative: no rewrite happens if `kbd(I)` is absent
from the `kbd` group.

## Linter Parity

`linter/lint.py` warns when a `l + kbd` pair with available `kbd(I)` is not
collapsed to the canonical compound-preposition payload:

- `Compound preposition \`l kbd\` should use single readings: l(I) and kbd(I) with POS \`n.\` and gloss \`within\``
