# Surface Reconstructability Pipeline

## Scope
This targeted rule repairs recurrent `col2` surface vs. `col3` analysis mismatches where the existing analysis cannot reconstruct the attested form, despite clear DULAT evidence.

## Inputs
- `col2` surface form
- `col3` analysis variants
- `col4` DULAT variants
- `col5` POS variants

## Step Strategy
1. Variant-safe rewrite
- Process semicolon-aligned variants independently.
- Rewrite only the variant whose `(surface, DULAT head)` pair matches a known mismatch class.
- Keep `col4`/`col6` unchanged except for explicit curated expansions.

2. `thmt` singular expansion
- For `surface=thmt`, `DULAT=thmt`, feminine noun rows:
  - `col3`: `thm(t/t; thm/t`
  - `col4`: `thmt; thm`
  - `col5`: `n. f.; n. m.`
  - `col6`: preserve primary gloss and append `ocean/deep`.

3. `thmtm` dual reconstructability
- For `surface=thmtm`, `DULAT=thmt`: rewrite to `thm(t/tm`.
- If POS contains `du.`, normalize aligned POS to `n. f.`.

4. `mtm` aligned repairs
- `mt (II)` -> `mt(II)/~m`
- `/m-t/` -> `mt[~m`
- `mt (I)` -> `mt(I)/m`
- `mt (III)` -> `mt(III)/m`

5. `bnt (II)` allograph repairs
- `bnwt` -> `bn&w(t(II)/t=`
- `bnwth` -> `bn&w(t(II)/t=+h`

6. `ym (I)` allograph repairs
- `ymm` -> `ym(I)/m`
- `ymt` -> `ym(I)/t=`
- `ymy` -> `ym(I)&y/`

7. `ỉlt (I)` `h`-allograph repairs
- `ilh` -> `il(t(I)/&h`
- `ilht` -> `il(t(I)/&ht`

8. Ambiguous sg/pl `-t` feminine forms
- For curated sg/pl-ambiguous surfaces where `/t=` was over-forced in prior passes, demote to `/t`:
  - `aṯt` (`ảṯt`) -> `aṯ(t/t`
  - `ṯat` (`ṯảt`) -> `ṯa(t/t`
- Rationale: `/t=` is reserved for explicitly plural encoding; these surface forms are ambiguous in DULAT (`sg.` + `pl.` on the same form).

## Linter Coupling
- Feminine `/t=` warnings must require plural-only surface morphology.
- If the same surface has explicit singular morphology in DULAT, do not force `/t=` (for example ambiguous `thmt` with both `sg.` and `pl.`).

## Iteration Checklist
1. Add failing tests for each mismatch class.
2. Implement targeted rewrite step as a separate pipeline stage.
3. Add/adjust linter regression tests for warning predicates.
4. Run Ruff format/check on changed code.
5. Run unit tests.
6. Re-run only this step over `out/KTU *.tsv`.
7. Verify user-flagged IDs and update changelog.
