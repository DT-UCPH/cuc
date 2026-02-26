# Verb Stem Suffix Marker Pipeline

## Problem
- Verb rows with explicit stem labels in POS (for example `vb D`, `vb L`, `vb R`, `vb Gpass`) were not guaranteed to encode the matching analysis suffix marker.
- This produced non-canonical parses such as `kbd[` with `POS=vb D` where the expected form is `kbd[:d`.

## Pipeline Step
- Step: `VerbStemSuffixMarkerFixer` (`pipeline/steps/verb_stem_suffix_marker.py`)
- Placement: immediately after `VerbPosStemFixer`, before final schema formatting.
- Rule:
  - POS stems `D/Dt/tD` require `:d`.
  - POS stems `L/Lt/tL` require `:l`.
  - POS stem `R` requires `:r`.
  - POS stems `Gpass/Dpass/Lpass/Špass` require `:pass`.
  - Marker is inserted after `[` and before suffix/enclitic payload (`+`, `~`) when present.
  - Non-verbal rows and deverbal nominal analyses (`[/`) are not changed.

## Linter Parity
- `linter/lint.py` now emits an error when POS implies a required marker that is missing in analysis:
  - `Verb stem marker(s) required by POS but missing in analysis: ...`
- Stem-consistency checks were aligned to cover:
  - `:r` vs DULAT `R`,
  - `:d` vs `D/Dt/tD`,
  - `:l` vs `L/Lt/tL`,
  - `:pass` vs `Gpass/Dpass/Lpass/Špass/N`.

## Tests
- Parser step tests: `tests/test_refinement_steps.py` (`VerbStemSuffixMarkerFixerTest`).
- Linter helper tests: `tests/test_linter_warning_predicates.py`.
- Linter integration tests: `tests/test_linter_verb_pos_stem.py`.
- Pipeline ordering guard: `tests/test_tablet_parsing_pipeline.py`.
