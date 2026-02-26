# N-Stem Assimilated Nun Pipeline

## Problem
- Prefixed N-stem verb rows were emitted without explicit assimilated nun encoding.
- Example: `!t!ṯbr[` with `POS=vb N` should be `!t!](n]ṯbr[`.

## Pipeline Step
- Step: `VerbNStemAssimilationFixer` (`pipeline/steps/verb_n_stem_assimilation.py`)
- Placement: after verb POS/stem normalization steps, before final schema formatting.
- Rule:
  - when POS includes verbal stem `N`,
  - and analysis is a prefixed verb form (`!y!`, `!t!`, `!a!`, `!n!`, including `=` variants),
  - and no explicit/visible initial `n` follows the preformative,
  - insert `](n]` immediately after the preformative marker.

## Linter Parity
- `linter/lint.py` now raises:
  - `Prefixed N-stem forms should encode assimilated nun as '](n]'`
  - when a prefixed `vb N` analysis is missing this marker.

## Tests
- Step tests: `tests/test_refinement_steps.py` (`VerbNStemAssimilationFixerTest`)
- Linter helper tests: `tests/test_linter_warning_predicates.py`
- Linter integration tests: `tests/test_linter_verb_pos_stem.py`
- Pipeline ordering: `tests/test_tablet_parsing_pipeline.py`
