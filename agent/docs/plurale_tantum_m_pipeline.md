# Plurale Tantum `-m` Pipeline

## Scope
This targeted rule normalizes noun analyses where DULAT evidence shows a lexeme-final `-m` and plurale-tantum behavior (plural/dual-only non-suffix forms), but output rows are inconsistent in `col3`/`col5`.

## Inputs
- `col2` surface form
- `col3` analysis variants
- `col4` DULAT variants
- `col5` POS variants
- DULAT morphology gate (`pipeline/steps/dulat_gate.py`)

## Step Strategy
1. Candidate detection
- Work variant-by-variant on noun slots (`n.`; excluding `n. num.`).
- Keep only variants whose declared DULAT token is a gate-backed plurale-tantum noun with lexeme-final `-m`.
- Do not classify tokens as plurale tantum when DULAT morphology has explicit singular evidence (for example `sg., suff.`), even if plural forms exist.
- Do not classify tokens as plurale tantum when DULAT non-suffix evidence is only plural construct-state (`pl., cstr.`) without any absolute plural/dual form.
- Apply curated exclusions for known non-plurale lemmas with plural `-m` forms (`ḥlm (II)`, `ʕgm`, `ỉštnm`) even when only plural morphology is attested.

2. Canonical `col3` rewrite for terminal `-m`
- Normalize to explicit lexeme + nominal ending encoding:
  - `šm(I)/m` -> `šm(m(I)/m`
  - `šmm(I)/` -> `šm(m(I)/m`
  - `nš/m` -> `nš(m/m`
  - `šˤr/m` -> `šˤr(m/m`
- Preserve already-correct `...(m/m` variants.
- If an unsplit lexical `(m/` host is detected, enforce `/m` (`...(m/` -> `...(m/m`).
- If the host surface (after removing suffix/enclitic tail) drops terminal `m`, normalize head to `...(m/` (without `/m`):
  - `pn/m` -> `pn(m/`
  - `pnm/+h` -> `pn(m/+h`

3. Surface allograph completion
- When surface has an inserted `y` before final `m` and reconstruction is otherwise exact, inject `&y` before `(m`:
  - `šm(I)/m` + `šmym` -> `šm&y(m(I)/m`.

4. Suffix-tail safety
- If a `+...` tail is spurious because the host head already reconstructs to the full surface, drop the tail before normalization (for example `pn/m+nm` -> `pn/m` -> `pn(m/m`).
- If the normalized head reconstructs to a suffixless base, infer a missing pronominal suffix tail only when reconstruction is exact (`+h`, `+k`, `+y`, etc.; for example `pnm/` -> `pn(m/+h`, `ḥym/` -> `ḥy(m/+k`).
- If tail starts with `+n...` and dropping that leading `n` is the only reconstruction-preserving completion, normalize tail (`+ny` -> `+y`).

5. POS normalization
- Ensure targeted noun POS carries `pl. tant.` in `col5` for that variant.

6. False-positive repair for non-plurale lemmas
- If a non-target `-m` lemma (gate says not plurale tantum) still contains an old injected split pattern `...(m/m` plus enclitic/suffix tail, restore lexical `m` in the head:
  - `šl(m(II)/m~m` -> `šlm(II)/~m`
- If a non-target `-m` lemma has truncated split form `.../m` before homonym, restore missing lexical `m`:
  - `ḥl(II)/m` -> `ḥlm(II)/m`
- Strip `pl. tant.` from aligned POS variants for the repaired DULAT slot.
- Also strip stale `pl. tant.` markers for non-target `-m` slots even when analysis is already reconstructable.

## Post-check policy
- Keep `col4`/`col6` untouched.
- Preserve variant alignment by rewriting per variant only.
- Rely on linter reconstructability and DULAT checks for final validation.

## Iteration Checklist
1. Add failing unit tests for `šmm`, `šmym`, `šmmh`, `pnm`, `nšm`, `šʕrm`.
2. Implement targeted step as a separate refinement stage.
3. Add linter predicate/rules for missing lexical `(m` and POS `pl. tant.`.
4. Run Ruff format/check.
5. Run unit tests.
6. Run only this rule across `out/KTU 1.*.tsv`.
7. Verify user-flagged IDs and update changelog.
