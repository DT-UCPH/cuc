# Prefixed III-Aleph Verb Pipeline

## Problem
- Legacy rows contained non-prefixed analyses like `ḫṭʔ[u` for prefixed III-aleph verb forms.
- Expected encoding is reconstructable prefix form with aleph contraction, e.g. `!t!ḫṭ(ʔ[&u`.

## Rule
- New step: `PrefixedIIIAlephVerbFixer` (`pipeline/steps/prefixed_iii_aleph_verb.py`)
- Applies when:
  - POS is verbal (`vb...`),
  - DULAT head token is a slash-root ending in `-ʔ` (III-aleph),
  - analysis is legacy pattern `...ʔ[a|i|u` without preformative.
- Rewrites to:
  - `!<preformative>!<stem-with-(ʔ>[&<inflection>`
  - with preformative derived from surface initial letter.

## Interaction With N-Stem Rule
- Runs before `VerbNStemAssimilationFixer`.
- For N-stem III-aleph forms:
  - first normalizes to prefixed III-aleph shape,
  - then `VerbNStemAssimilationFixer` adds `](n]` (e.g. `!n!](n]ḫt(ʔ[&u`).

## Tests
- `tests/test_refinement_steps.py` (`PrefixedIIIAlephVerbFixerTest`)
- `tests/test_refine_results_mentions.py` (`test_analysis_encodes_prefixed_iii_aleph_forms`)
- `tests/test_tablet_parsing_pipeline.py` (ordering guard)
