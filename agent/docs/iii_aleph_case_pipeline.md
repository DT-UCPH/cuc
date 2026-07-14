# III-Aleph Case Pipeline

## Scope
This targeted rule normalizes reconstructability for III-aleph noun/adjective forms where surface case vowels (`u/i/a`) are not encoded explicitly in `col3`.

## Inputs
- `col2` surface form
- `col3` analysis variants
- `col4` DULAT variants
- `col5` POS variants

## Step Strategy
1. Candidate detection
- Process semicolon-aligned variants independently.
- Restrict to noun/adjective slots (`n.`, `adj.`).
- Require declared DULAT lemma and surface to share the same stem with a final case vowel in `{u, i, a}`.

2. Safety gates
- Skip unresolved or non-lexical variants (`?`, `[`, `+`, `~`).
- Skip variants already using explicit case-vowel encoding (`/&`).
- Skip variants that already reconstruct exactly to `col2`.

3. Canonical rewrite
- For base variants like `rpu/`, `ṣbu(II)/`, `nnu(I)/`:
  - remove the final analysis vowel from the visible stem,
  - reconstruct lexeme-final vowel as `(u|i|a`,
  - encode surface case vowel as `/&u|&i|&a`.
- Examples:
  - `rpu/` + `rpi` -> `rp(u/&i`
  - `ṣbu(II)/` + `ṣba` -> `ṣb(u(II)/&a`
  - `nnu(I)/` + `nni` -> `nn(u(I)/&i`

## Linter Coupling
- Add warning for III-aleph noun/adjective variants that match the stem+vowel profile but omit `(V` + `/&V` encoding.

## Iteration Checklist
1. Add failing unit tests for representative III-aleph forms (`rpủ`, `ṣbủ (II)`, `nnủ (I)`).
2. Implement dedicated refinement step.
3. Add linter regression tests for warning/no-warning cases.
4. Run Ruff format/check on changed Python files.
5. Run focused unit tests.
6. Re-run only this step across `out/KTU *.tsv`.
7. Verify top mismatch classes and update changelog.
