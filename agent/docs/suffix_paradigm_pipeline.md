# Suffix/Enclitic Paradigm Normalization Pipeline

## Goal

Keep column-3 suffix/enclitic encoding aligned with the tagging conventions:

- pronominal suffixes use `+` (for example `mlk/+h`, `bn(I)/+ny`);
- postclitic consonants use `~` (for example `!y!rgm[~n`);
- no homonym numerals on suffix/enclitic markers in col3.

## Canonical marker inventory

The normalization targets the pronominal segments used in the paradigm:

- `y`, `n`, `k`, `h`
- `ny`, `nk`, `nh`, `nn`
- `km`, `kn`, `hm`, `hn`
- `nkm`

Optional `=` is preserved where present (for example `+h=` or `+ny=`).

## Step behavior

- Step: `SuffixParadigmNormalizer` (`pipeline/steps/suffix_paradigm_normalizer.py`)
- Rule: strip homonym numerals attached to marker segments:
  - `+n(I)` -> `+n`
  - `+h(II)` -> `+h`
  - `+ny(III)=` -> `+ny=`
  - `~n(IV)` -> `~n`
  - `[n(II)=` -> `[n=`
- Deliberate non-target:
  - do not rewrite non-pronominal `+m(I)` / `+m(II)` patterns in this step.

## Pipeline ordering

Wired in `pipeline/tablet_parsing.py` immediately after `SuffixCliticFixer`:

1. `SuffixCliticFixer` injects/normalizes missing `+` and enclitic forms.
2. `SuffixParadigmNormalizer` removes residual homonym numerals from clitic slots.

This ordering keeps suffix insertion and suffix canonicalization separate and deterministic.
