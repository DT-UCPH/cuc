# Verb POS Stem Enrichment

## Problem
- Verb rows in `out/*.tsv` used plain `POS=vb`/`vb.` without stem labels.
- DULAT form morphology already encodes stems (`G`, `Gt`, `D`, `Š`, etc.) for exact surface forms.

## Pipeline Step
- Step: `VerbPosStemFixer` (`pipeline/steps/verb_pos_stem.py`)
- Placement: late pipeline pass, after contextual disambiguators and before final schema formatting.
- Rule:
  - target only POS values that are verb-head (`^vb`), excluding verbal nouns (`vb. n.`),
  - resolve DULAT entry from col4 token + surface form,
  - extract stem tags from exact `forms.morphology` matches for that surface,
  - append stems to col5 as `vb <stem>` (for example `vb G`, `vb Gt`, `vb G/Š`),
  - keep non-verb rows and rows already carrying stem labels unchanged.

## Linter Parity
- `linter/lint.py` now warns when:
  - row is verbal in DULAT for the exact surface form,
  - stem tags are available from DULAT form morphology,
  - POS column lacks a verb stem label.
- Warning message prefix: `Verb POS should include stem label(s): ...`

## Tests
- Parser step: `tests/test_refinement_steps.py` (`VerbPosStemFixerTest`)
- Linter: `tests/test_linter_verb_pos_stem.py`
- Pipeline ordering guard: `tests/test_tablet_parsing_pipeline.py`
