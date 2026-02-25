# `/b-ʕ-l/` Verbal Slash Normalization

## Problem
- The parser emitted verbal `/b-ʕ-l/` rows as `bˤl[` (and `!y!bˤl[`), which is not reconstructable under the project encoding conventions.
- Canonical verbal encoding must keep `[/` closure (for example `bˤl[/`).

## Pipeline Step
- Step: `BaalVerbalSlashFixer` (`pipeline/steps/baal_verbal_slash.py`)
- Scope: all `out/KTU *.tsv` files.
- Rule:
  - split aligned row variants (`col3` + `col4`) by `;`,
  - when `col4` variant is `/b-ʕ-l/` and `col3` variant ends with bare `[`,
  - normalize `col3` variant to `...[/`.

## Linter Parity
- Predicate: `row_has_baal_verbal_missing_slash` in `linter/lint.py`.
- Enforcement: error when any `/b-ʕ-l/` variant lacks `[/` in `col3`.

## Tests
- Parser step coverage: `tests/test_refinement_steps.py` (`BaalVerbalSlashFixerTest`).
- Linter predicate coverage: `tests/test_linter_warning_predicates.py`.
- Lint integration coverage: `tests/test_linter_baal_verbal_slash.py`.
