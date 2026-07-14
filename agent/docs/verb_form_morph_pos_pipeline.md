# Verb Form Morphology POS Pipeline

This step documents the DULAT-driven POS refinement for verbal rows.

## Goal

Use exact `surface + DULAT token` matches from `forms.morphology` to enrich
POS with verbal form information (for example: `prefc.`, `suffc.`, `impv.`,
`inf.`, `act. ptcpl.`, `pass. ptcpl.`), and preserve ambiguity as explicit POS
options when the surface is genuinely ambiguous.

## Step

`pipeline/steps/verb_form_morph_pos.py` (`VerbFormMorphPosFixer`)

## Strategy

1. Build `VerbFormMorphIndex` from DULAT sqlite:
   - Keep only verbal entries (`vb`, excluding `vb. n.`).
   - Normalize form text and index morphology by `(surface, entry_id)` and by
     `surface` fallback.
2. For each TSV row variant with verbal POS:
   - Resolve exact morphologies via `surface + declared DULAT token`.
   - Parse morphology markers into canonical payload:
     - stem (`G`, `N`, `D`, `Š`, `Gt`, etc.),
     - form (`prefc.`, `suffc.`, `impv.`, `inf.`, participles),
     - optional gender/number (`m./f.`, `sg./pl./du.`).
3. Keep stem-safe behavior:
   - If current POS already constrains stem, ignore morphology options that
     conflict with that stem.
4. Emit deterministic POS options:
   - Single reading: `vb <stem> <form> ...`
   - Ambiguous reading: `option1 / option2 / ...` (stable ordered, deduped).

## Linter Alignment

`linter/lint.py::split_pos_options(...)` accepts spaced slash options (`A / B`)
so enriched ambiguity payloads validate without ad-hoc formatting hacks.

## Tests

- `tests/test_verb_form_morph_pos.py`
- `tests/test_linter_pos_normalization.py` (slash-option splitting)

