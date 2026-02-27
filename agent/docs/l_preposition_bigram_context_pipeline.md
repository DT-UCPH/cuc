# `l + X` Prepositional Bigram Context

## Purpose

Normalize high-confidence `l` prepositional bigrams by forcing `l(I)` where
context is lexicalized and stable.

## Pipeline Step

Implemented as `LPrepositionBigramContextDisambiguator` in:

- `pipeline/steps/l_preposition_bigram_context.py`

Registered after `l-body-compound-prep` and before `k-functor-bigram-context`.

## Rules

1. Force single `l(I)` before stable prepositional followers:
   - `arṣ`, `špš`, `mlkt`, `ṣpn`, `il`, `kḥṯ`, `ršp`, `inš`, `bˤlt`, `ˤṯtrt`, `ˤpr`.
2. Force `l(I) + bˤl(II)` outside `KTU 4.*`:
   - collapse `l` to single `l(I)`,
   - collapse `bˤl` to a single `bˤl(II)` row.
3. Normalize lexicalized `l pn*` prepositions:
   - force single `l(I)`,
   - canonicalize `pn/pnm/pnh/pnk/pny/pnwh` to noun POS (`n. m. pl. tant.`)
     with gloss `in front`.

## Linter Parity

`linter/lint.py` enforces matching constraints:

- `Bigram \`l <surface>\` should use a single l(I) reading`
- `Outside KTU 4.*, \`l bˤl\` should use single readings: l(I) and bˤl(II)`
- `Lexicalized preposition \`l <pn-surface>\` should use single readings: l(I) and <analysis> with POS \`n. m. pl. tant.\` and gloss \`in front\``
