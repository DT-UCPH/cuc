# Nominal Y/H Case Ending + Pronoun Closure Pipeline

## Goal

Normalize two recurring reconstructability errors while keeping changes DULAT-gated and conservative:

1. Pronouns should not use noun-style trailing `/` closure.
2. Noun/adjective forms ending in surface `y`/`h` should encode case ending as `/y` or `/h` when evidence exists.

## Step 1: Pronoun closure normalization

- Step: `PronounClosureFixer` (`pipeline/steps/pronoun_closure.py`)
- Input pattern: pronoun-like POS (`pn.` / `pron`) with analysis variants like `X/` or `X(II)/`.
- Rewrite:
  - `hw/` -> `hw`
  - `hm(II)/` -> `hm(II)`
- Safety:
  - skip unresolved variants (`?`)
  - skip variants with clitic/verb markers (`+`, `~`, `[`)
  - operate variant-by-variant with POS-slot alignment.

## Step 2: Morphology-aware nominal `y/h` case split

- Step: `NominalCaseEndingYHFixer` (`pipeline/steps/nominal_case_ending_yh.py`)
- Gate: DULAT exact token+surface morphology lookup via
  `DulatMorphGate.surface_morphologies(token, surface)`.
- Input pattern:
  - nominal/adjectival POS only (`n.`, `adj.`),
  - analyzable base form with trailing slash (`.../`),
  - surface ending in `y` or `h`.
- Rewrite:
  - `umy/` + DULAT `ủm` + surface `umy` -> `um/y`
  - `hkl/` + DULAT `hkl` + surface `hkly` -> `hkl/y`
- Safety:
  - skip unresolved or clitic/verb-marked variants,
  - skip forms whose matching DULAT morphology is suffix-only (`suff`),
  - require analysis/surface/declared-lemma alignment before rewriting.

## Pipeline order

Configured in `pipeline/tablet_parsing.py`:

1. `PronounClosureFixer`
2. ...
3. `IIIAlephCaseFixer`
4. `NominalCaseEndingYHFixer`
5. `SurfaceReconstructabilityFixer`

This order prevents pronoun false-positives early and applies nominal `y/h` encoding before final reconstructability cleanup.
