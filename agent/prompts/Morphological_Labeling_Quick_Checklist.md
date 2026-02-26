# Morphological Labeling Quick Checklist (Operator Mode)

Use this checklist during annotation of a new unlabeled file.
For full rules and examples, see `agent/Morphological_Labeling_Agent_Guide.md`.

## 1. Preflight

1. Keep `col1` and `col2` unchanged.
2. If source is `cuc_tablets_tsv`:
   - keep separator rows starting with `#----------------------------`,
   - token rows are `id<TAB>surface<TAB>surface` where `col3` is only a placeholder.
3. Use linter format mode explicitly when needed:
   - raw CUC TSV: `python linter/lint.py 'cuc_tablets_tsv/KTU 1.5.tsv' --input-format cuc_tablets_tsv --dulat sources/dulat_cache.sqlite --udb sources/udb_cache.sqlite`
   - labeled output: `python linter/lint.py 'out/KTU 1.5.tsv' --input-format labeled --dulat sources/dulat_cache.sqlite --udb sources/udb_cache.sqlite`
   - mixed/unknown: `python linter/lint.py 'out/KTU 1.5.tsv' --input-format auto --dulat sources/dulat_cache.sqlite --udb sources/udb_cache.sqlite`.
4. Check weak-final finite SC `-t` forms: for `/...-...-y/` or `/...-...-w/` verbs with surface ending `t`, use `[t` (for example `nš(y[t:n`), not `t[`.
5. For quick token-id -> line-reference lookup in current TSV files, use:
   - `python3 scripts/token_ref_index.py --id 139891 --glob 'out/KTU 1.*.tsv'`
6. If local DULAT+UDB server is available (`http://127.0.0.1:8000`), use:
   - `/concordance/?word=...` for UDB pattern probing (broken `x` cases),
   - `/api/entries/?q=...` for DULAT candidate extraction,
   - `/api/references/?ref=...` for line-level reverse mentions (`mentions[]`),
   - `/api/openapi.json` to verify current API parameters.
   - note: wildcard probing is done via `/concordance/`, not `/api/concordance/`.
7. Reverse-reference tables (direct DB fallback):
   - DULAT: `dulat_reverse_refs(norm_ref, entry_id, payload)`,
   - UDB: `ktu_to_dulat(ktu_ref, entry_id, payload)`,
   - UDB mapping: `reverse_index(norm_ref, target)`.
   Use these when one surface form maps to multiple DULAT entries.
8. Translation/commentary modules:
   - UI: `/modules/TCS/`, `/modules/Smith/`
   - DB: `sources/modules_cache.sqlite` (`module_records`, `module_refs`)
   Use this as contextual evidence for unresolved lexical/POS ties after DULAT + reverse mentions.
7. Verb-specific refinement aid:
   - `sources/notarius.compact.html`
   - extracted evidence JSON: `sources/notarius_evidence_claims.json`
   - helper: `scripts/notarius_refinement_pass.py`
   Use primarily for stem/voice/infinitive-participle decision points.
8. Output format per line:
   - `col1 id`
   - `col2 surface`
   - `col3 semicolon-separated analysis variants`
   - `col4 semicolon-separated DULAT entry sets (comma-separated inside multi-lexeme variants)`
   - `col5 semicolon-separated POS sets (comma-separated morpheme slots; `/` for POS options within one morpheme slot)`
   - `col6 semicolon-separated gloss sets (comma-separated inside multi-lexeme variants)`
   - optional `# comment` for residual notes only.
   - separator hierarchy: `;` variants, `,` morphemes, `/` POS-options-within-morpheme.
   - if a DULAT POS label itself contains `/`, rewrite it with `or` in `col5` (for example `det. or rel. functor`, `emph. or det. encl. morph.`).
9. Use project orthography in columns 2-3:
   - ayin as `ˤ`,
   - aleph vowels as `a i u`,
   - no `ʿ/ʕ/ả/ỉ/ủ` in columns 2-3.
10. Use DULAT orthography only inside comments or DB lookup normalization.

## 2. Per-Token Procedure

1. Propose candidate analysis from surface morphology.
2. Determine lexical class:
   - verb if `[` present,
   - noun/adj if `/` present without `[`,
   - deverbal if `[/`,
   - preposition/particle/pronoun often no closing marker.
3. Reconstruct lookup lexeme from analysis:
   - strip wrappers `! ... !` and `] ... ]`,
   - interpret `(` and `&`,
   - strip clitic tails for headword lookup.
4. For verbs:
   - if reconstructed lexeme starts with `a/i/u`, map initial to `ʔ` for root lookup.
5. Query DULAT `forms` by normalized surface first to get entry candidates.
6. Validate candidates by reconstructed lexeme/root (`/q-t-l/` for verbs).
7. Enforce standalone-vs-clitic priority:
   - standalone token -> prefer non-clitic lemmas over `-x`,
   - clitic lemma only when morphology explicitly encodes clitic behavior.
8. Apply homonym filter `(I), (II), ...` if present in analysis.
9. If candidates still >1, use reverse mentions for the exact line ref:
   - API: `/api/references/?ref=1.2 III 12`,
   - DB fallback: `dulat_reverse_refs` + `ktu_to_dulat` (`CAT ...` and `KTU ...` keys),
   - intersect lexical candidate `entry_id`s with mention `entry_id`s.
   - if intersection has one entry, choose it; if empty, do not force.
   - if still tied, apply soft priors in order:
     1) exact `forms.morphology` fit (`suff., pn.`, etc.),
     2) global mention frequency (common entry before rare),
     3) tablet-family fit (`PN/TN/DN` narrow to one family -> down-rank outside it).
10. If still tied after reverse mentions, check TCS/Smith module context for the same tablet/column and apply only DULAT-valid choices.
11. Apply formula-level `l` priors when sequence matches exactly:
   - `tbʕ w l yṯb ỉlm` -> `l(II)` (`adv.`, `not`),
   - `ỉdk l ytn ...` -> `l(III)` (`functor`, `truly/certainly`).
12. If `[/`:
   - check both verb root and nominal lemma,
   - if only noun survives but `[` exists, flag mismatch.
13. Validate clitics separately:
   - `+` suffix/enclitic parts,
   - `~` postclitics,
   - post-`[` segments excluding pure stem markers (`:d`, `:l`, `:pass`),
   - skip parts with no reconstructed letters.
14. Use reference translation (if provided) to resolve remaining homonym ambiguity.
15. If two adjacent tokens are both unresolved, combine surfaces and retry `forms` lookup.
16. Validate stem markers against DULAT stems.
17. Write `col3` with all parse variants (`variant1; variant2; ...`).
18. Write aligned `col4/col5/col6`:
   - same number of semicolon groups as `col3`,
   - per-group comma counts aligned across `col4/col5/col6`,
   - POS alternatives for one morpheme must use `/` inside that one `col5` comma-slot.
19. Keep DULAT gloss compact:
   - no full article bodies, bibliography, or HTML tags (`<b>`, `<i>`, `<br>`, etc.),
   - prefer a short lexical gloss (roughly 1-8 words),
   - for `DN/TN/PN/GN`, prefer the canonical name gloss (for example `Ugarit`, `Baalu`, `El`, `ʿAnatu`) over literal/common-noun glosses.
20. Keep comment field for residual notes only (translation rationale, uncertainty, text-critical notes), not duplicated DULAT/POS/gloss payload.
21. For noun POS in `col5`, include DULAT gender when available:
   - use `n. m.` or `n. f.` (for example `n. f.`, `n. m./DN`).
   - for adjective POS with DULAT gender available, use `adj. m.` or `adj. f.`.
   - for pluralia tantum, add `pl. tant.` in that noun POS slot (or `pl. tant.?` when tentative) instead of writing this in comments.
22. For broken `x` tokens:
   - if token is only `x...`, skip lexical lookup,
   - if token has a single `x` (not x-only), query UDB concordance with `x -> -`,
   - if token has `xx...`, query UDB concordance with each `xx...` run replaced by `—`,
   - normalize ayin in lookup (`ʿ/ʕ/ˤ`) before deciding no-hit.
23. Reconstructability check (mandatory):
   - each semicolon variant in `col3` must reconstruct exactly to `col2`,
   - if it does not, revise the parse (usually missing clitic/ending or misplaced marker).
   - for repeated long surface sequences (formulaic parallels), align `col3/col4/col5/col6` across occurrences unless a comment explicitly justifies divergence.

## 3. Symbol Rules (High-Risk)

1. `(` = in lexeme, absent in surface.
2. `&` = in surface, absent in lexeme.
3. Substitution order is `(X&Y` for the same segment.
4. If multiple letters are reconstructed, each letter must be prefixed with `(`.
5. Invalid: `š(lyṭ/`; valid: `š(l(y(ṭ/`.
6. Do not treat non-adjacent `&` and `(` as a substitution error.
7. Prefix conjugation preformative in `!!`: `!t!qtl[`.
8. Weak-initial `/y-.../` prefix forms must keep both markers:
   - preformative in `!...!` and hidden first radical as `(y`:
   - `!y!(ytn[`, `!t!(ytn[`, `!a!(ytn[`, `!y!(yṯb[`.
9. Stem augment/infix in `]]`: `]š]qtl[`.
10. Pronominal suffixes with `+`: `mlk/+h`.
11. Postclitic with `~`: `!y!rgm[~n`.
12. Homonym disambiguation in lemma: `il(I)/`, `-h(I)` vs `-h(II)`.
13. Feminine noun/adjective endings:
    - lexeme-final `-t` nouns: f.sg `.../t`, f.pl `.../t=` (for example `am(t/t`, `am(t/t=`).
    - nouns with no `-t` in singular but `-t` in plural: use `.../t=` (for example `gg/t=`).
    - adjectives/participles: f.sg `.../t`, f.pl `.../t=` (for example `kbd/t`, `kbd/t=`).

## 4. Stem Marker Checks

Treat these as stem indicators in analysis:

- `]š]`,
- `]t]`,
- `:d`,
- `:l`,
- `:pass`.

Compatibility with DULAT:

1. `]š]` -> DULAT should allow `Š` or `Št` or `Špass`.
2. `]t]` -> DULAT should allow `Gt` or `Št` or `Dt` or `Lt` or `Nt`.
3. `:d` -> DULAT should allow `D` or `Dt`.
4. `:l` -> DULAT should allow `L` or `Lt`.
5. `:pass` -> DULAT should allow `Špass`.
6. If DULAT has no `G` for the verb, at least one explicit stem marker must appear.

## 5. POS Closure Checks

1. Verb analysis should contain `[`.
2. Noun/adjective/proper-name analysis should contain `/`.
3. Deverbal nominal should contain `[/`.
4. Pronouns/particles/prepositions can be unclosed.

## 6. Known Edge-Case Patterns

1. Substitution + reconstruction in deverbal forms: query verbal root, not raw surface.
2. III-aleph/case-vowel alternation: keep reconstructed and surface layers distinct (`(` vs `&`).
3. Non-adjacent `&` and `(`: do not flag as substitution-order error.
4. Combined stem indicators: allow if DULAT stem evidence supports the combination.
5. `[/` forms: always check both verbal and nominal pathways.
6. Post-`[` clitics: split and validate separately from head verb.
7. Homonym-sensitive verbs: enforce explicit homonym marker before translation-based disambiguation.
8. Mixed POS proper-name entries (`n., DN`, `TN, DN`): resolve with line-level translation context (`DN/TN/PN` vs `n.`).
9. High-frequency ambiguous lemmas (`bʕl`, `ỉl`, `ṣpn` etc.): batch-check all occurrences for consistent DN/PN/n policy.
10. `/y-t-n/` short/imperative `tn` forms can be represented without preformative as `!!(ytn[` when context supports imperative.
11. Ambiguous `yX...` prefix forms may require two variants when DULAT supports both roots:
    - for example `!y!(yṯb[;!y!ṯb[` with `/y-ṯ-b/;/ṯ-b/`.
12. Nouns with DULAT sg/pl same-form behavior can stay unsplit and should be marked in POS:
    - add `pl. tant.` in POS `col5` (or `pl. tant.?` when tentative), not in comments.
    - keep plural ending explicit in `col3`: `.../m` for `-m` plural (for example `nš(m/m`) and `.../t=` for feminine `-t` plural (for example `hml(t/t=`).
13. Formula disambiguation for `l`:
   - `tbʕ w l yṯb ỉlm` -> `l(II)` (`not`),
   - `ỉdk l ytn ...` -> `l(III)` (`truly/certainly`).

## 7. Minimal Output Policy

1. If one DULAT candidate remains: emit one variant in `col3` and aligned `col4/col5/col6`.
2. If several remain: keep explicit candidate list in comment.
3. If no valid candidate remains: mark unresolved and explain why in comment.
   - for fully unresolved variant, use `?` in `col3/col4/col5/col6` (not only in lexical columns).
4. Never silently guess across homonyms.
5. Before final unresolved status, test merge fallback for consecutive unresolved token pairs.
6. Final file must be structurally aligned:
   - semicolon-group counts equal in `col3/col4/col5/col6`,
   - comma-item counts equal per group in `col4/col5/col6`,
   - POS alternatives inside one morpheme slot are `/`-separated (not comma-separated).

## 8. Translation-Driven Improvement Pass

Use this pass after initial morphology is complete.

1. Align by token `id` + line context (`<tablet>.json`/UDB/other concordance if available).
2. Cross-check the same segment against UDB line text; if CUC/UDB numeration is shifted, align by neighboring token sequence, not line number alone.
3. Compare in-file word-by-word comment with:
   - primary translation,
   - alternative translation(s),
   - commentary/notes editions,
   - any user-supplied philological references.
4. Flag only morphology-relevant discrepancies:
   - lexical headword,
   - POS,
   - stem,
   - proper-name class (`DN/PN/TN` vs common noun),
   - segmentation.
5. Ignore purely stylistic/literary differences (comment-only; no parse change).
6. Validate every alternative with DULAT before editing parse.
7. If two adjacent unresolved tokens persist, test merged lookup using translation cue.

## 9. Promote to Structured Variants vs Keep Comment-Only

Promote to explicit semicolon variants in `col3/col4/col5/col6` when all are true:

1. Alternative is morphologically expressible in project notation.
2. DULAT supports a lexical path (entry/root/stem).
3. Translation note is line-specific.
4. Difference changes morphology or segmentation.
5. If two published readings are both DULAT-attested, keep both; order primary by stronger lexical/stem evidence and keep the other as secondary variant.

Keep comment-only when:

1. No DULAT support.
2. Difference is interpretive only.
3. Evidence is too broken/uncertain for a defensible parse.

## 10. Comment Reference Format

Use short references directly in comments:

1. `Translation A line 12`
2. `Translation B note 7`
3. `Commentary C p45 n3`
4. Mark uncertainty explicitly: `supported`, `plausible`, `conjectural`.
5. For DN/PN/n decisions, add a short context note:
   - `TCS/UNP: proper-name usage`
   - `TCS/UNP: title/common-noun usage`

Quick examples:

1. Keep baseline parse; add a second semicolon variant when alternative changes POS/stem/segmentation and is DULAT-valid.
2. For verb-vs-function-word ambiguity, include both parses in structured columns and reference line-level note in comment.
3. For restoration-driven alternatives, include explicit uncertainty marker (`conjectural`) in comment.
4. For unattested exact forms, add variant only if lexical pathway is defensible and clearly flagged.

Final comment hygiene:

1. Do not write `OR:` in comments.
2. Do not duplicate `DULAT: lemma [POS] — gloss` in comments when encoded in cols 4-6.
3. When citing concordance evidence, write `UDB concordance ...` (not `server ...`).
4. `DULAT: NOT FOUND` is allowed only when cols 4-6 are empty for that token.

## 11. Appendix A (Optional): Concrete Examples from Existing Files

Use only as a pattern reference; not required for new tablets.

1. `9510 sid s(ʔ&id[/` -> reconstructed radical with substitution; lookup `/s-ʔ-d/`.
2. `9527 mri mr(u[/&i` -> root/case alternation across reconstructed and surface layers.
3. `9548 tpphnh !t!p&ph(y[n+h` -> non-adjacent `&` and `(` (no false substitution-order error).
4. `9842 tštḥwy !t!]š]]t]ḥwy(II)[` -> multiple stem indicators in one verb.
5. `10049 rkb rkb(I)[/` -> deverbal check against both `/r-k-b/` and `rkb(I)`.
6. `10132 atm !!at(w[~m(II)` -> root before `[`, clitic after `[` is separate.
7. `139819 yˤn !y!ˤn(y(I)[` -> homonym `(I)` enforced before contextual disambiguation.
8. `139777 š &š` -> CUC marks this as uncertain/excised; keep token in sequence and mark unresolved `col3/col4/col5/col6` as `?`, with a short note.
