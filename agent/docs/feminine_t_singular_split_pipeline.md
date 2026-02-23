# Feminine `-t` Singular Split Pipeline

## Scope
This pipeline rule targets unsplit feminine singular noun-like analyses where column 3 still uses `...t/` instead of an explicit feminine split with `/t`.

## Inputs
- `col2` surface form
- `col3` analysis variants
- `col4` DULAT variants
- `col5` POS variants
- `data/onomastic_gloss_overrides.tsv` (`dulat`, `POS`, `gloss`)
- DULAT morphology gate (`pipeline/steps/dulat_gate.py`)

## Step Strategy
1. Candidate detection
- Match analysis variants of shape `...t/` (optionally with homonym marker before `/`).
- Skip variants already split as `/t` or `/t=`.

2. Feminine evidence gating
- Accept when POS explicitly marks feminine (`n. f.` or `adj. f.`).
- For onomastic POS (`DN/PN/TN/GN/MN`), accept only if the declared DULAT token is feminine in `data/onomastic_gloss_overrides.tsv`.

3. Safety gating
- Skip plural tokens according to DULAT form evidence for the current surface (`is_plural_token`).
- Skip variants containing verbal/clitic structure (`[`, `+`, `~`) in this conservative pass.

4. Deterministic rewrite
- If declared DULAT lemma is lexeme-final `-t`:
  - `Xt/ -> X(t/t`
  - `X/t -> X(t/t`
  - `Xt(I)/ -> X(t(I)/t`
  - `X(I)/t -> X(t(I)/t`
- If declared DULAT lemma is not lexeme-final `-t`:
  - keep feminine singular split as `.../t`.
- If analysis omits a homonym but declared DULAT token has one, inject it into transformed feminine split output (for example `b/t` + `bt (I)` -> `b(t(I)/t`).
- If surface has a terminal `m` and transformed analysis reconstructs to exactly `surface[:-1]`, append terminal `m` after `/t` (for example `thmtm`: `thm(t/t` -> `thm(t/tm`).

5. Post-check policy
- Keep aligned column structure unchanged (`col4`-`col6` untouched by this step).
- Rely on linter for reconstructability and DULAT consistency.

## Iteration Checklist
1. Add failing tests for representative noun and feminine DN cases.
2. Implement step and onomastic POS/gender loader support.
3. Run targeted unit tests.
4. Run Ruff format and Ruff lint.
5. Re-run only this rule across `out/*.tsv`.
6. Verify target rows and record in changelog.
