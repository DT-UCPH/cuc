# Š-Stem Tail Reconstructability Pipeline

## Problem
- Some non-prefixed Š-stem verb analyses were emitted with a spurious extra tail after `[`.
- Example: `šqrb` became `]š]qrb[b` instead of `]š]qrb[`.

## Root Cause
- In `analysis_for_entry`, non-prefixed verbal tail length was computed against bare stem length only.
- For marked stems (`]š]`, `]t]`), this over-counted and duplicated the final surface letter as tail.

## Parser Fix
- Updated `scripts/refine_results_mentions.py::analysis_for_entry`:
  - for non-prefixed verbs, tail is now derived from:
    1. `stem-marker + stem` match,
    2. fallback `stem` match,
    3. only then legacy length fallback.

## Corpus Cleanup Step
- Added a generic cleanup in `SurfaceReconstructabilityFixer`:
  - if analysis head (before `[`) already reconstructs full surface, and tail is pure letters, trim the tail.
  - restricted to non-prefixed forms to avoid touching `!preformative!` analyses.

## Tests
- `tests/test_refine_results_mentions.py`:
  - `test_analysis_keeps_non_prefixed_sh_stem_without_spurious_tail`
- `tests/test_surface_reconstructability_fixer.py`:
  - `test_removes_spurious_non_prefixed_stem_tail`
  - `test_keeps_prefixed_forms_unchanged_for_tail_rule`
