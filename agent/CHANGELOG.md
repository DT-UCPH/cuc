# Changelog

## 2026-02-25

- Fixed verb stem/form enrichment gaps for suffixed/enclitic verb spellings:
  - `pipeline/steps/verb_pos_stem.py` and
    `pipeline/steps/verb_form_morph_pos.py` now fallback to host-form lookup by
    reconstructing analysis before suffix/enclitic payload markers (`+`, `~`).
  - this restores `vb <STEM> <FORM>` enrichment for rows like
    `yšqynh !y!šqy[+nh /š-q-y/` where DULAT form tables attest only host forms.
  - added regressions in:
    - `tests/test_refinement_steps.py` (`VerbPosStemFixerTest`)
    - `tests/test_verb_form_morph_pos.py`
  - re-ran full `--include-existing` pipeline to apply globally.

- Fixed include-existing pipeline behavior to keep DULAT-backed lexical refinement
  reproducible on preserved outputs:
  - `pipeline/tablet_parsing.py` now runs `refine_targets(...)` for all selected
    targets when `--include-existing` is used (not only freshly bootstrapped files).
  - this restores expected regeneration of stale glosses from DULAT metadata
    (for example `/ʕ-š-r/` verb rows no longer keep legacy attestational quotes).
  - added regression coverage in `tests/test_tablet_parsing_pipeline.py`.

- Added construct-state propagation for ambiguous nominal number POS:
  - `pipeline/steps/nominal_form_morph_pos.py` now carries DULAT
    construct labels into plural ambiguity rendering (for example
    `n. m. sg. / n. m. pl. cstr.` for `sg.` + `pl., cst./cstr.` forms).
  - construct morphology matching now accepts both `cst.` and `cstr.`
    spellings in:
    - `pipeline/steps/dulat_gate.py`
    - `linter/lint.py`
  - added/updated regressions:
    - `tests/test_nominal_form_morph_pos.py`
    - `tests/test_linter_plurale_tantum_m.py`
  - re-ran full `--include-existing` pipeline to apply globally.

- Fixed two regressions introduced by verb-form encoding split rollout:
  - `nominal-form-morph-pos` ambiguity rendering is now idempotent for
    slash-packed POS heads (dedupes repeated number alternatives and avoids
    dropping `du.` during ambiguity normalization).
  - added a post-verb unwrapping pass so late semicolon payloads from
    `verb-form-encoding-split` are emitted as separate rows:
    - `variant-row-unwrapper-post-verb`
    - `unwrapped-duplicate-pruner-post-verb`
  - added regression coverage in
    `tests/test_nominal_form_morph_pos.py` and
    `tests/test_tablet_parsing_pipeline.py`.
  - re-ran full `--include-existing` pipeline to apply globally.

- Added verb form encoding split refinement to enforce analysis/POS compatibility:
  - new step `pipeline/steps/verb_form_encoding_split.py`
    (`VerbFormEncodingSplitFixer`) splits mixed finite/non-finite verb POS
    options by encoding (`[` vs `[/`) and normalizes single-class mismatches.
  - wired in pipeline after `verb-form-morph-pos`.
  - added tests:
    - `tests/test_verb_form_encoding_split.py`
    - `tests/test_tablet_parsing_pipeline.py` (step ordering update).
  - documented strategy in `docs/verb_form_encoding_split_pipeline.md`.
  - re-ran full `--include-existing` pipeline to apply globally.

- Added full DULAT form-level POS enrichment for ambiguous exact-surface
  matches across the corpus:
  - new step `pipeline/steps/verb_form_morph_pos.py`
    (`VerbFormMorphPosFixer`) adds verbal form payloads from
    `forms.morphology` (for example `prefc.`, `suffc.`, `impv.`, `inf.`,
    `act. ptcpl.`, `pass. ptcpl.`), preserving ambiguity as explicit
    slash-separated options.
  - nominal exact-form number ambiguity is now explicit in POS where surface
    form does not disambiguate (for example `n. m. pl. / n. m. du.`) via
    `pipeline/steps/nominal_form_morph_pos.py`.
  - linter POS option splitting now accepts spaced slash options (`A / B`) in
    `linter/lint.py`.
  - added tests:
    - `tests/test_verb_form_morph_pos.py`
    - `tests/test_nominal_form_morph_pos.py` (ambiguous-number updates)
    - `tests/test_linter_pos_normalization.py` (slash splitting)
  - documented the strategy in
    `docs/verb_form_morph_pos_pipeline.md`.
  - re-ran full `--include-existing` pipeline to apply changes globally.

- Added DULAT reference-based ambiguity collapse for unwrapped token groups:
  - new index capability in `pipeline/dulat_attestation_index.py`:
    `has_reference_for_variant_token(...)` with normalized `KTU`/`CAT`
    citation matching.
  - new refinement step
    `pipeline/steps/attestation_reference_disambiguator.py`:
    for each `(line_id, surface)` group within a `# KTU ...` section, if
    exactly one option is attested at that section reference, keep it and
    remove the rest.
  - wired into pipeline after `unwrapped-duplicate-pruner`.
  - added tests:
    - `tests/test_dulat_attestation_index.py`
    - `tests/test_attestation_reference_disambiguator.py`
    - `tests/test_tablet_parsing_pipeline.py` (step ordering)
  - documented strategy in
    `docs/attestation_reference_disambiguator_pipeline.md`.
  - re-ran full `--include-existing` pipeline to apply globally.

- Extended feminine `-t` singular splitting for generic nominal POS rows:
  - `pipeline/steps/feminine_t_singular_split.py` now also applies
    DULAT-backed lexical-`t` splitting when POS is generic `n.`/`adj.` (no
    explicit gender), surface ends in `t`, and the declared lemma is `t`-final.
  - keeps explicit masculine rows unchanged.
  - added regressions in `tests/test_feminine_t_singular_split.py`:
    `test_splits_t_final_noun_for_generic_noun_pos`,
    `test_keeps_t_final_noun_with_explicit_masculine_pos`.

- Removed repeated header-like pseudo-data rows from preserved outputs:
  - `pipeline/steps/schema_formatter.py` now drops junk rows whose first two
    columns are `id` / `surface form` (for example
    `id\tsurface form\t?\t?\t?\t?\tDULAT: NOT FOUND`).
  - added regression in `tests/test_refinement_steps.py`:
    `test_drops_repeated_header_like_junk_rows`.
  - re-ran full `--include-existing` tablet pipeline to apply globally.

- Fixed global POS enrichment coverage and made it reproducible for
  `--include-existing` runs:
  - `pipeline/tablet_parsing.py` now runs `instruction_refine_targets(...)` for
    all selected targets (not only freshly bootstrapped files), preventing
    gender enrichment regressions on preserved outputs.
  - added regression in `tests/test_tablet_parsing_pipeline.py`:
    `test_run_include_existing_applies_instruction_refinement`.
- Extended `InstructionRefiner` with DULAT form-based number enrichment:
  - POS slots now receive `sg./pl./du.` when an exact surface form maps to a
    single unambiguous number in `forms.morphology`.
  - gender enrichment is still conservative and now shares token-key resolution
    with number enrichment for consistency.
  - added regressions in `tests/test_instruction_refiner.py`:
    `test_enriches_pos_number_from_surface_form_morphology`,
    `test_keeps_pos_number_when_form_number_is_ambiguous`.

- Fixed suffix-split nominal heads to preserve visible non-lexeme tail letters
  before clitic suffixes in parser rendering:
  - `scripts/refine_results_mentions.py` now rewrites split heads like
    `qdqd/ + +k` to `qdqd&h/+k` when base surface is `qdqdh`.
  - implemented via `inject_surface_only_tail_before_nominal_closure(...)`
    in split-variant rendering.
  - added regression in `tests/test_refine_results_mentions.py`:
    `test_render_split_variant_preserves_surface_only_tail_before_suffix`.
  - re-ran parser regeneration and full refinement-step pipeline across all
    tablets to apply this globally.

- Normalized aleph-prefix preformative encoding in verbal analyses:
  - canonicalized `!a!`, `!i!`, `!u!` to `!(ʔ&a!`, `!(ʔ&i!`, `!(ʔ&u!` in parser generation (`scripts/refine_results_mentions.py`) and legacy III-aleph fixer (`pipeline/steps/prefixed_iii_aleph_verb.py`).
  - updated prefix-marker detection in refinement/lint paths to accept canonical aleph-prefix markers:
    - `pipeline/steps/weak_verb.py`,
    - `pipeline/steps/weak_final_sc.py`,
    - `pipeline/steps/verb_n_stem_assimilation.py`,
    - `linter/lint.py`.
  - added regression coverage in:
    - `tests/test_refine_results_mentions.py`,
    - `tests/test_refinement_steps.py`,
    - `tests/test_linter_verb_pos_stem.py`.
  - re-ran parser regeneration (`scripts.refine_results_mentions`) and full refinement-step pipeline across all tablets, then regenerated reports.

- Fixed fallback-direct ambiguity suppression in `scripts/refine_results_mentions.py`:
  - suffix split variants are now generated when direct hits come only from
    lemma fallback (no exact DULAT form hit), instead of being suppressed.
  - split variants now deduplicate suffix homonym entries by suffix segment
    (for example `-y (I)/(II)`), preventing top-N crowding that hid lexical
    alternatives.
  - strong-score single-variant collapse is now disabled when split variants
    are present.
- Added regression in `tests/test_refine_results_mentions.py`:
  - `test_fallback_direct_hit_does_not_suppress_suffix_split_variants`.
- Re-ran refinement + full step pipeline across all tablets so affected
  fallback-direct cases (including `152206 yry`) are reproducibly restored.

- Fixed suffix segmentation for `...ny` surfaces where the final `n` belongs to
  the lexeme (e.g. `bn (I)` + suffix `y`):
  - `SuffixCliticFixer` now tries all matching suffix candidates and applies the
    first reconstructable one, instead of stopping at greedy longest match.
  - This corrects rows like `bny` from `bn(I)/` to `bn(I)/+y` (not `+ny`).
- Added regression in `tests/test_refinement_steps.py`:
  - `test_prefers_y_suffix_over_ny_when_lemma_ends_with_n`.

- Fixed weak-initial N-stem interaction between `weak-verb` and `verb-n-stem-assimilation`:
  - `WeakVerbFixer` now preserves leading `](n]` and inserts `(y` after it (instead of in front of it).
  - `VerbNStemAssimilationFixer` now normalizes semicolon variants independently and collapses legacy repeated `](n](y` insertions to a single canonical marker.
  - resolves runaway forms like `!y!](n](y](n](y...` to `!y!](n](y...`.

- Fixed global L-stem geminate placement in verbal analyses:
  - added `VerbLStemGeminationFixer` (`pipeline/steps/verb_l_stem_gemination.py`) to move stem-internal doubled radicals from tail position to stem position (for example `!t!qṭ[ṭ:l` -> `!t!qṭṭ[:l`).
  - wired step into pipeline between `verb-pos-stem` and `verb-stem-suffix-marker`.
- Improved parser generation parity for L stems in `scripts/refine_results_mentions.py`:
  - `analysis_for_entry` now expands terminal gemination for L-stem forms when the surface explicitly shows the doubled radical.
- Added regression coverage in:
  - `tests/test_refine_results_mentions.py`,
  - `tests/test_refinement_steps.py`,
  - `tests/test_tablet_parsing_pipeline.py`.

- Fixed legacy prefixed III-aleph verb rows that were encoded without preformative and aleph-contraction markers (e.g. `ḫṭʔ[u`):
  - added `PrefixedIIIAlephVerbFixer` (`pipeline/steps/prefixed_iii_aleph_verb.py`) to normalize to reconstructable form (`!t!ḫṭ(ʔ[&u`) from row-local evidence (`surface`, `POS`, `DULAT` root).
  - wired step into pipeline before verb stem enrichment/assimilation steps.
- Improved generation parity in `scripts/refine_results_mentions.py`:
  - prefixed III-aleph roots (`/...-ʔ/`) now generate `!preformative!...[&<vowel>` directly, including non-weak roots (e.g. `/ḫ-ṭ-ʔ/`, `/q-r-ʔ/`, `/b-ʔ/`).
- Added regression coverage:
  - `tests/test_refinement_steps.py`,
  - `tests/test_refine_results_mentions.py`,
  - `tests/test_tablet_parsing_pipeline.py`.
- Documented rule in `docs/prefixed_iii_aleph_verb_pipeline.md`.
- Re-ran full tablet pipeline and reports; target rows like `148130 tḫṭu` now normalize to `!t!ḫṭ(ʔ[&u`.

- Fixed Š-stem non-prefixed verb tail reconstruction bug that produced spurious duplicated final letters (e.g. `]š]qrb[b`):
  - `scripts/refine_results_mentions.py::analysis_for_entry` now computes non-prefixed verbal tails against `stem-marker + stem` when present, not just bare stem length.
  - This prevents extra-tail output for surface-aligned forms like `šqrb` (`]š]qrb[`).
- Added a global cleanup rule in `SurfaceReconstructabilityFixer`:
  - removes pure-letter tails after `[` when the analysis head already reconstructs the full surface (non-prefixed forms),
  - fixes existing corpus rows without manual `/out` edits.
- Added regression coverage:
  - `tests/test_refine_results_mentions.py`,
  - `tests/test_surface_reconstructability_fixer.py`.
- Re-ran full pipeline across all tablets and regenerated reports to apply the fix globally.

- Added global N-stem assimilated nun enforcement for prefixed verb forms:
  - new step `VerbNStemAssimilationFixer` (`pipeline/steps/verb_n_stem_assimilation.py`) inserts `](n]` after verbal preformatives for `vb N` rows where assimilated `n` is not visible.
  - example normalization: `!t!ṯbr[` -> `!t!](n]ṯbr[`.
- Added matching linter error in `linter/lint.py`:
  - `Prefixed N-stem forms should encode assimilated nun as '](n]'`.
- Added regression coverage in:
  - `tests/test_refinement_steps.py`,
  - `tests/test_linter_warning_predicates.py`,
  - `tests/test_linter_verb_pos_stem.py`,
  - `tests/test_tablet_parsing_pipeline.py`.
- Documented the rule pipeline in `docs/n_stem_assimilated_n_pipeline.md`.

- Fixed DULAT gloss compaction for comma-bearing parenthetical translations:
  - `scripts/refine_results_mentions.py::compact_gloss` now splits only on top-level commas (outside `()` / `[]`),
  - prevents truncation like `"(one"` for `ảlp (II)` and preserves `"(one, a) thousand"`.
- Added regression coverage in `tests/test_refine_results_mentions.py`:
  - `test_compact_gloss_keeps_parenthetical_comma`,
  - `test_compact_gloss_still_splits_top_level_comma`.
- Re-ran full reproducible bootstrap+refine+instruction+steps pipeline across all tablets (`KTU *.tsv`, `278` targets), regenerating `out/*.tsv` and `reports/*`.

- Added parser enforcement for POS-implied verbal stem suffix markers:
  - new step `VerbStemSuffixMarkerFixer` (`pipeline/steps/verb_stem_suffix_marker.py`) inserts required `:d`, `:l`, `:r`, `:pass` from POS stem labels (`vb D/L/R/*pass`),
  - step is wired after `VerbPosStemFixer` in `pipeline/tablet_parsing.py`.
- Aligned linter enforcement and stem consistency:
  - new POS-driven error when required markers are missing (`Verb stem marker(s) required by POS but missing in analysis: ...`),
  - extended stem compatibility checks for `:r`, `tD/tL`, and `Lpass`.
- Added regression coverage:
  - `tests/test_refinement_steps.py`,
  - `tests/test_linter_warning_predicates.py`,
  - `tests/test_linter_verb_pos_stem.py`,
  - `tests/test_tablet_parsing_pipeline.py`.
- Documented the rule as a reproducible pipeline strategy in `docs/verb_stem_suffix_marker_pipeline.md`.
- Re-ran the full parsing pipeline over all tablets (`278` targets) with safeguard override for the known high-churn duplicate-pruning stage, then regenerated `out/*.tsv` and `reports/*`.

- Fixed fallback `¶ Forms:` token cleaning to preserve non-ASCII transliteration letters (notably `ś`) instead of stripping them into false short keys:
  - `pipeline/config/dulat_entry_forms_fallback.py` now normalizes fallback form tokens via Unicode-letter filtering (`isalpha`) and keeps `-` where present.
  - Prevents spurious fallback keys like `wm`/`wt` derived from valid forms such as `śśwm`/`śśwt`.
- Aligned DULAT exact-surface matching paths to the same Unicode-letter normalization policy:
  - `pipeline/steps/dulat_gate.py`,
  - `pipeline/steps/verb_pos_stem.py`.
- Added regression coverage:
  - `tests/test_dulat_entry_forms_fallback.py`,
  - `tests/test_bootstrap_tablet_labeling.py`,
  - `tests/test_dulat_gate_plurale_tantum.py`.
- Re-ran full reproducible bootstrap+refine+instruction+steps pipeline across all tablets (`KTU *.tsv`, `278` targets), regenerating `out/*.tsv` and `reports/*`.
- Verified removal of the incorrect horse mapping for `wm`:
  - `152680` (`KTU 1.104.tsv`), `149498` (`KTU 1.67.tsv`), `139306` (`KTU 1.4.tsv`) no longer resolve to `s:śs/św`.

- Added provenance comments for redirect-derived reconstructions:
  - new step `pipeline/steps/redirect_reconstruction_comment.py` marks non-`→` rows in redirect ambiguity groups with `Based on DULAT reconstruction.`,
  - wired into pipeline after variant unwrapping so comments are applied per row (not to the whole packed group),
  - preserved existing comments and prevented duplicate insertions.
- Added tests in `tests/test_redirect_reconstruction_comment.py`.

- Fixed redirect-derived Š-initial verb reconstruction when DULAT target is a bare root:
  - `scripts/refine_results_mentions.py::analysis_for_entry` now handles redirect-restored verbs where surface is `š + root` but target lemma is bare (for example `/b-ʕ-r/`),
  - emits `]š]...[` instead of fallback `...[last-radical]` tails (for example `šbˤr` no longer becomes `bˤr(I)[r`; now `]š]bˤr(I)[`).
- Added regression test in `tests/test_refine_results_mentions.py`:
  - `test_redirect_entry_restores_initial_sh_for_bare_verb_lemma`.
- Re-ran targeted regeneration for all tablets containing `→` entries (38 files) so this redirect-derived verb fix is applied corpus-wide.

- Extended redirect (`→`) restoration to support root targets in `cf.` clauses:
  - `scripts/refine_results_mentions.py::extract_redirect_targets` now recognizes plain `cf. /root/` references (not only `<i>...</i>` targets),
  - redirect expansion now prefers slash-root entries when the target itself is slash-root notation (for example `/y-l-d/`),
  - redirect-derived verb rendering now supports weak-initial `y` -> surface `w` reconstructability (`wld` -> `(y&wld[`).
- Added regression in `tests/test_refine_results_mentions.py`:
  - `test_redirect_entry_resolves_slash_root_target_with_weak_restoration`.
- Re-ran targeted pipeline regeneration for all tablets containing `→` entries (38 files), so redirect-based root restoration is applied corpus-wide.

- Added redirect-aware reconstruction for DULAT `→` entries in refinement:
  - `scripts/refine_results_mentions.py` now parses redirect targets from entry notes (`cf. <i>target</i>`),
  - keeps the original `→` variant (`gloss = ?`) and adds a lexical target variant when resolvable (for example `rdmn` -> `(prdmn/`),
  - enables conservative nominal prefix restoration for redirect-derived variants so reconstructed surface loss is explicit.
- Wired redirect-target resolution into pipeline refinement invocation:
  - `pipeline/tablet_parsing.py` now passes `lemma_map` to `refine_file` / `build_variants`.
- Added regression coverage in `tests/test_refine_results_mentions.py`:
  - `test_redirect_entry_adds_target_restoration_variant` validates dual-row behavior (`→` row + restored lexical row).
- Re-ran targeted regeneration for tablets containing `→` entries to apply the rule deterministically across outputs.

- Fixed prefix-conjugation detection for Š/Št-stem analyses with explicit stem markers:
  - `scripts/refine_results_mentions.py::analysis_for_entry` now matches preformative bodies against both plain stems and marker+stem realizations (`š+root`, `št+root`),
  - restores missing `!preformative!` for forms like `yštḥwyn`, `tštḥwy`, `yšlḥm`,
  - prevents invalid long residual tails (for example `[ḥwyn`) by producing valid short endings (`[n` or empty).
- Added regression tests in `tests/test_refine_results_mentions.py` for:
  - `yštḥwyn` -> `!y!]š]]t]ḥwy(II)[n`,
  - `tštḥwy` -> `!t!]š]]t]ḥwy(II)[`,
  - `yšlḥm` -> `!y!]š]lḥm(I)[`.
- Re-ran targeted regeneration for all tablets containing this error class (33 files, including `KTU 1.1.tsv`, `KTU 1.2.tsv`, `KTU 1.3.tsv`, `KTU 1.4.tsv`, `KTU 1.6.tsv`, `KTU 1.100.tsv`, and relevant `KTU 2.*`/`KTU 3.*` files).

- Fixed contracted prefixed weak-form reconstruction for hidden terminal radicals:
  - `scripts/refine_results_mentions.py::analysis_for_entry` now marks hidden stem-final letters in contracted prefix forms as reconstructed (`(`),
  - example correction: `twtḥ` `/w-ḥ-y/` Gt prefc. now emits `!t!w]t]ḥ(y[` (not `!t!w]t]ḥy[`).
- Added regression update in `tests/test_refine_results_mentions.py` for contracted `twtḥ`.
- Re-ran targeted regeneration for affected tablets:
  - `KTU 1.1.tsv`, `KTU 1.3.tsv`, `KTU 1.7.tsv`.

- Fixed contracted `/n-...-ʔ/` prefix-conjugation verb encoding in parser generation:
  - `scripts/refine_results_mentions.py::analysis_for_entry` now uses DULAT form morphology (`prefc.`) + root shape to encode contracted forms as reconstructable prefix analyses (for example `yšu` -> `!y!(nš(ʔ[&u`, `tšun` -> `!t!(nš(ʔ[&un`, `ytšu` -> `!y!(n]t]š(ʔ[&u`).
  - prevents fallback reductions like `nšʔ[` for these prefixed forms.
- Added regression coverage in `tests/test_refine_results_mentions.py` for `yšu`, `tšan`, and `ytšu`.
- Re-ran targeted tablet regeneration (source->bootstrap->refine->instruction->steps) for all files containing `/n-...-ʔ/` prefixed verb forms:
  - `KTU 1.1.tsv`, `KTU 1.103.tsv`, `KTU 1.119.tsv`, `KTU 1.122.tsv`, `KTU 1.14.tsv`, `KTU 1.15.tsv`, `KTU 1.16.tsv`, `KTU 1.167.tsv`, `KTU 1.17.tsv`, `KTU 1.18.tsv`, `KTU 1.19.tsv`, `KTU 1.2.tsv`, `KTU 1.23.tsv`, `KTU 1.3.tsv`, `KTU 1.4.tsv`, `KTU 1.40.tsv`, `KTU 1.41.tsv`, `KTU 1.5.tsv`, `KTU 1.6.tsv`, `KTU 1.92.tsv`, `KTU 2.31.tsv`, `KTU 2.82.tsv`, `KTU 3.19.tsv`.

- Fixed global reverse-mention disambiguation drift for tablets using compact section separators:
  - updated `scripts/refine_results_mentions.py::parse_separator_ref` to support both `KTU x.y COL:line` and `KTU x.y line` separator formats,
  - restored DULAT reverse-mention scoring for no-column tablets (for example `# ... KTU 1.101 5` -> `CAT 1.101:5`),
  - added regression tests in `tests/test_refine_results_mentions.py` for separator parsing and mention-driven DN selection.
- Added global DULAT form-text alias overrides for known source-table form typos:
  - new `pipeline/config/dulat_form_text_overrides.py`,
  - wired into bootstrap/refine loaders, linter loader, and verb stem index so form aliases are applied consistently across parser and linter.
- Fixed verb analysis reconstructability for prefixed forms with residual consonantal tails:
  - `scripts/refine_results_mentions.py::analysis_for_entry` now preserves trailing form letters after the stem (for example `tlsmn` -> `!t!lsm[n`).
- Extended tests for the new behavior:
  - `tests/test_bootstrap_tablet_labeling.py`,
  - `tests/test_refine_results_mentions.py`,
  - `tests/test_linter_dulat_form_morph_overrides.py`,
  - `tests/test_refinement_steps.py` (`VerbPosStemFixerTest` alias coverage).
- Re-ran the full parser pipeline across all tablets (`278` files) with explicit all-target bootstrap+refine+instruction+step passes and regenerated lint reports, so `out/` reflects only reproducible rule-based transformations.
- Fixed global prefixed-verb preformative detection for contracted weak forms:
  - `scripts/refine_results_mentions.py::analysis_for_entry` now recognizes prefixed forms by stem/body structural matching instead of raw markerized length checks,
  - preserves `!preformative!` for contracted prefixed realizations (for example `twtḥ` -> `!t!w]t]ḥy[`).
- Added regression test coverage for the contracted prefixed case in `tests/test_refine_results_mentions.py`.
- Re-ran full all-tablet bootstrap+refine+instruction+step pipeline after the fix (`278` targets), regenerating `out/*.tsv` and lint reports from rules only.
- Corrected DULAT form-morph override for `tḥm` suffixed forms:
  - added `("tḥm", "", "tḥmk", "sg.") -> "suff."` in `pipeline/config/dulat_form_morph_overrides.py`,
  - propagated to parser/linter loaders (including `scripts/refine_results_mentions.py`) so `tḥmk` is parsed as `tḥm/+k` corpus-wide.
- Added reproducible unresolved-surface override for `ḫršnr` in `data/generic_parsing_overrides.tsv`:
  - now normalized to `ḫršn&r/ | ḫršn (I) | n. m. | (divine) mountain` with UDB note.
- Added regression coverage:
  - `tests/test_linter_dulat_form_morph_overrides.py`,
  - `tests/test_dulat_gate_plurale_tantum.py`,
  - `tests/test_refine_results_mentions.py`,
  - `tests/test_refinement_steps.py` (`GenericParsingOverrideFixerTest` default override assertion).
- Re-ran targeted pipeline regeneration for affected tablets:
  - `KTU 1.1.tsv`, `KTU 1.3.tsv`, `KTU 1.4.tsv`, `KTU 2.36.tsv`, `KTU 2.77.tsv`, `KTU 2.83.tsv`.
- Extended III-aleph normalization to plural `-m` forms using exact DULAT form morphology (`pl.`):
  - `pipeline/steps/iii_aleph_case_fixer.py` now rewrites III-aleph plural forms to convention-aligned encodings:
    - oblique plural: `... (u&i/m` (e.g. `iqnim`),
    - same-vowel plural: `... (u&/m` (e.g. `rpum`).
  - wired gate-backed morphology checks into pipeline instantiation (`pipeline/tablet_parsing.py`).
- Added regression coverage in `tests/test_iii_aleph_case_fixer.py` for both oblique and same-vowel plural `-m` III-aleph cases.
- Re-ran targeted pipeline regeneration for all detected III-aleph plural `-m` candidates:
  - `KTU 1.1.tsv`, `KTU 1.161.tsv`, `KTU 1.20.tsv`, `KTU 1.21.tsv`, `KTU 1.22.tsv`,
    `KTU 1.3.tsv`, `KTU 1.4.tsv`, `KTU 1.6.tsv`, `KTU 1.7.tsv`, `KTU 1.82.tsv`, `KTU 2.73.tsv`.

- Replaced deletion-style variant pruning with linguistics-based reconstructability fixes driven by DULAT form evidence and Tagging conventions:
  - `FeminineTSingularSplitFixer` now handles feminine surface forms of masculine lemmas (for example `pḥl/` + `pḥlt` -> `pḥl/t`),
  - added reconstructable aleph substitution in `AlephPrefixFixer` (`ʔbd[` -> `(ʔ&abd[`),
  - `DulatMorphGate` now treats dual form morphology as split-eligible for nominal `-m` endings.
- Added new targeted parser steps:
  - `ToponymDirectionalHFixer` (`pipeline/steps/toponym_directional_h.py`) for TN `-h` directional/enclitic encoding (`.../` -> `.../~h`),
  - `DeicticFunctorEncliticMFixer` (`pipeline/steps/deictic_functor_enclitic_m.py`) for deictic functor extended `-m` forms (`hl` -> `hl~m` when attested),
  - `NominalFormMorphPosFixer` (`pipeline/steps/nominal_form_morph_pos.py`) to enrich nominal POS with form-level feminine/dual markers.
- Extended linter parity (`linter/lint.py`):
  - no `Suffix form without '+'` warning for `~`-encoded enclitics,
  - allow feminine noun POS when exact DULAT surface morphology is feminine,
  - normalize nominal number markers (`sg./du./pl.`) during POS-vs-DULAT validation.
- Added regression coverage:
  - `tests/test_nominal_form_morph_pos.py`,
  - `tests/test_toponym_directional_h.py`,
  - `tests/test_deictic_functor_enclitic_m.py`,
  - `tests/test_linter_form_gender_match.py`,
  - `tests/test_linter_pos_normalization.py`,
  - plus updates to `tests/test_feminine_t_singular_split.py`, `tests/test_refinement_steps.py`, `tests/test_dulat_gate_plurale_tantum.py`, and `tests/test_linter_warning_predicates.py`.
- Re-ran full parser + refinement pipeline over all `out/KTU *.tsv` files (278 tablets) with `--allow-large-step-changes`, regenerating `reports/*`.
- Fixed false feminine detection from `suff.` morphology tokens:
  - parser steps now require token-level `f.` morphology markers (not substring matches),
  - linter feminine-form override now also uses token-level morphology parsing.
- Extended `DulatMorphGate` with `token_genders(...)` and updated `NominalFormMorphPosFixer` to correct false `n. f.` assignments back to `n. m.` when token gender is unambiguously masculine and exact form morphology is non-feminine (e.g. `ab/+n` for `ảb`).
- Refined dual POS enrichment in `NominalFormMorphPosFixer`: `du.` is now added only for unambiguous dual-only surfaces, and removed when the same surface is explicitly `sg.`/`pl.`-competing (e.g. `ỉl` no longer forced to `n. m. du.` from `du., cstr.` overlap).
- Added regression tests for the `suff.` vs `f.` collision and token-gender correction:
  - `tests/test_nominal_form_morph_pos.py`,
  - `tests/test_dulat_gate_plurale_tantum.py`,
  - `tests/test_linter_form_gender_match.py`.
- Added source-level DULAT form-morph overrides for known table-parsing errors in `ỉl (I)` construct forms:
  - new `pipeline/config/dulat_form_morph_overrides.py`,
  - remaps `du., cstr.` to `sg., cstr.` for `ỉl` and to `pl., cstr.` for `ỉly`/`-y`.
- Wired DULAT form-morph overrides into both parser and linter loaders:
  - `pipeline/steps/dulat_gate.py`,
  - `linter/lint.py`.
- Refined `NominalFormMorphPosFixer` to remove stale `du.` when exact-surface DULAT morphology is explicitly non-dual (for example `pl., cstr.`).
- Added regression coverage:
  - `tests/test_linter_dulat_form_morph_overrides.py`,
  - updates in `tests/test_dulat_gate_plurale_tantum.py`,
  - updates in `tests/test_nominal_form_morph_pos.py`.
- Re-ran only `nominal-form-morph-pos` over all `out/KTU *.tsv` files; 3 row updates (`KTU 2.16.tsv`, `KTU 3.10.tsv`, `KTU 3.20.tsv`).
- Global rollback/correction for post-`c005507` destructive output drift:
  - restored all `out/KTU *.tsv` files to pre-regression baseline (`1d1775a`),
  - re-applied only safe form-driven nominal POS refinement (`nominal-form-morph-pos`) corpus-wide with current DULAT overrides (`415` row updates in `112` files).
- Updated pipeline execution strategy for `--include-existing` reprocessing:
  - existing `out/*.tsv` files are now preserved through bootstrap/refine/instruction phases,
  - bootstrap/refine/instruction run only for targets without an existing output file,
  - refinement steps still run over all selected targets.
- Added pipeline regression coverage for target partitioning:
  - `tests/test_tablet_parsing_pipeline.py::test_partition_targets_for_bootstrap_preserves_existing_outputs`.

- Reverted noun-side POS coercion in `l + noun` compound-preposition passes so suffix-friendly noun payloads are retained:
  - `L_PN_PREP_CANONICAL_PAYLOADS` now keeps `pn*` payloads as `n. m. pl. tant.` (not `prep.`),
  - `L_BODY_COMPOUND_PREP_RULES` now keeps `pˤn` as `n. f.` and `ẓr` as `n. m.` (not `prep.`),
  - `LKbdCompoundPrepDisambiguator` now emits `kbd(I)` as `n.` with gloss `within`.
- Updated linter parity in `linter/lint.py` to enforce the same noun-side payload policy and refreshed warning messages accordingly.
- Added/updated regression coverage for parser+linter alignment:
  - `tests/test_l_preposition_bigram_context.py`,
  - `tests/test_l_body_compound_prep.py`,
  - `tests/test_l_kbd_compound_prep.py`,
  - `tests/test_linter_l_preposition_bigram_context.py`,
  - `tests/test_linter_l_body_compound_prep.py`,
  - `tests/test_linter_l_kbd_compound_prep.py`.
- Applied only targeted steps across all `out/KTU *.tsv` files:
  - `l-kbd-compound-prep` (`14` row updates),
  - `l-body-compound-prep` (`48` row updates),
  - `l-preposition-bigram-context` (`21` row updates).

- Added `BaalVerbalSlashFixer` (`pipeline/steps/baal_verbal_slash.py`) and wired it into `pipeline/tablet_parsing.py` after `BaalLabourerKtu1Fixer`.
- New rule: for verbal `/b-ʕ-l/` readings, normalize analysis payloads from bare `...[` to canonical `...[/` (for example `bˤl[` -> `bˤl[/`, `!y!bˤl[` -> `!y!bˤl[/`).
- Updated `BaalLabourerKtu1Fixer` to emit canonical retained verbal variant `bˤl[/` and accept both legacy and canonical target payloads.
- Added linter parity:
  - new predicate `row_has_baal_verbal_missing_slash` in `linter/lint.py`,
  - new error when `/b-ʕ-l/` variants are encoded without `[/`.
- Added regression coverage:
  - parser step tests in `tests/test_refinement_steps.py` (`BaalVerbalSlashFixerTest`),
  - linter predicate tests in `tests/test_linter_warning_predicates.py`,
  - lint integration tests in `tests/test_linter_baal_verbal_slash.py`.
- Documented the strategy in `docs/baal_verbal_slash_pipeline.md`.
- Added `VerbPosStemFixer` (`pipeline/steps/verb_pos_stem.py`) and wired it into `pipeline/tablet_parsing.py` after `YdkContextDisambiguator` and before final `TsvSchemaFormatter`.
- New rule: enrich verbal POS in column 5 from exact DULAT form morphology stems (for example `vb` -> `vb G`, `vb` -> `vb Gt`, `vb` -> `vb G/Š`), while leaving non-verb and `vb. n.` rows unchanged.
- Added linter parity warning in `linter/lint.py`: when exact-surface verb stems are attested in DULAT but POS lacks a stem label (`Verb POS should include stem label(s): ...`).
- Added regression coverage:
  - parser step tests in `tests/test_refinement_steps.py` (`VerbPosStemFixerTest`),
  - linter regression tests in `tests/test_linter_verb_pos_stem.py`,
  - pipeline ordering guard update in `tests/test_tablet_parsing_pipeline.py`.
- Documented strategy in `docs/verb_pos_stem_pipeline.md`.

## 2026-02-24

- Added `VariantRowUnwrapper` (`pipeline/steps/variant_row_unwrapper.py`) and wired it into `pipeline/tablet_parsing.py` as the final content step before schema formatting.
- New output policy for `out/*.tsv`: one parsing option per row (no semicolon-packed variant payloads in col3-col6), with repeated `id`+`surface` across option rows.
- `VariantRowUnwrapper` formalized behavior:
  - split col3-col6 semicolon variants into aligned one-option rows,
  - preserve `col1` (`id`), `col2` (`surface`), and `col7` (`comments`) per emitted row,
  - reuse singleton col4/col5/col6 payload across emitted rows when needed,
  - drop duplicate emitted options with identical `(id, surface, col3, col4, col5, col6)`.
- Added linter enforcement in `linter/lint.py`:
  - error on packed semicolon variants in `out/*.tsv`,
  - error on duplicate unwrapped payload rows (`id`+`surface`+`col3`-`col6`),
  - context-sequence lint checks now collapse variant-expanded rows to one token stream entry per `(id, surface)`.
- Added regression tests:
  - `tests/test_variant_row_unwrapper.py`,
  - `tests/test_linter_unwrapped_rows.py`.
- Documented strategy in `docs/variant_row_unwrapper_pipeline.md`.
- Applied only `VariantRowUnwrapper` over `out/KTU 1.*.tsv` (`4,778` source rows rewritten in `133` files); packed variant rows in col3-col6 are now `0`.
- Follow-up fix for `k`-option alignment after unwrapping:
  - `VariantRowUnwrapper` now preserves explicit empty semicolon slots and trims only trailing empty slots,
  - added non-empty-anchor projection for gloss slots when legacy packed rows encode alignment empties in POS but not gloss (for example `k` override rows with `;;POS...` + compact gloss list),
  - added regression test `test_preserves_empty_slot_alignment_for_k_variants` in `tests/test_variant_row_unwrapper.py`.
- Re-applied only `VariantRowUnwrapper` from pre-unwrapped baseline (`6e8a89e`) across `out/KTU 1.*.tsv`; user-flagged rows (for example `135829` / `143662`) now map `k(III)` -> `when`, `k(I)` -> `like`, `k(II)` -> `yes` without shifted POS/gloss.
- Added `UnwrappedDuplicatePruner` (`pipeline/steps/unwrapped_duplicate_pruner.py`) after variant unwrapping to remove duplicated option rows with identical `(id, surface, col3, col4, col5, col6)` payload.
- Added regression coverage for duplicate pruning in `tests/test_unwrapped_duplicate_pruner.py`.
- Expanded pipeline scope defaults from `KTU 1.*.tsv` to `KTU *.tsv` (`pipeline/tablet_parsing.py`) and added `--source-glob` to `scripts/run_tablet_parsing_pipeline.py` for explicit family-scoped runs.
- Added pipeline test coverage for default all-family target selection (`tests/test_tablet_parsing_pipeline.py`).
- Applied the post-`c7ebe6f` instruction + refinement chain across all tablet families (`KTU *.tsv`) and regenerated lint reports; packed semicolon rows in `col3`-`col6` are now `0` corpus-wide and duplicate unwrapped payload rows are `0` corpus-wide.
- Corrective rollback after `7afe8cf` output overreach:
  - restored `out/KTU *.tsv` and `reports/*` to pre-commit state to preserve researcher comments and approved edits,
  - retained the code-level `ydk` parser/linter fixes from `7afe8cf`,
  - re-applied only the targeted context result in `out/KTU 1.22.tsv` (`146856` collapsed to `yd(II)/+k= | yd (II) | n. m. | love`).
- Added `LNegationVerbContextPruner` (`pipeline/steps/l_negation_verb_context.py`) and wired it into `pipeline/tablet_parsing.py` after unwrapping.
  - Rule: keep `l(II)` (`adv.`, `no/not`) only when the following token-group is verbal; otherwise prune `l(II)` from ambiguous `l` groups.
  - Guard: if `l(II)` is the only analysis row for a token, leave it unchanged.
- Added linter context warning in `linter/lint.py` for non-verbal `l(II)` usage: `l(II) ('no/not') should be used only before verbal forms`.
- Added tests:
  - `tests/test_l_negation_verb_context.py`,
  - `tests/test_linter_l_negation_context.py`,
  - updated `tests/test_tablet_parsing_pipeline.py` ordering guard.
- Applied only this targeted step across `out/KTU *.tsv` (`835` rows pruned in `163` files), including `out/KTU 1.6.tsv` `140451` (removed `l(II)` before `bˤl`).
- Follow-up exception refinement for DULAT-attested non-verbal `l(II)` contexts:
  - added shared exception matcher `pipeline/config/l_negation_exception_refs.py` for `KTU/CAT 1.3 IV:5`, `KTU/CAT 4.348:1`, and `KTU/CAT 4.213:2-23`,
  - updated `LNegationVerbContextPruner` to force a single `l(II)` reading in these refs (including restoration when historical passes already pruned `l(II)`),
  - updated linter behavior to enforce this exception-specific single-`l(II)` rule while suppressing the generic non-verbal warning in those refs,
  - added regression tests `tests/test_l_negation_exception_refs.py` and expanded parser/linter `l(II)` context tests.
- Added `l(III)` / `l(IV)` contextual disambiguation layer from DULAT reference sets:
  - new shared reference matcher `pipeline/config/l_functor_vocative_refs.py` (supports both `KTU x.y Z:n` and `KTU x.y n` separator styles),
  - new parser step `LFunctorVocativeContextDisambiguator` (`pipeline/steps/l_functor_vocative_context.py`) wired after `l-negation-verb-context`,
  - context policy:
    - `l(III)` refs force single `l(III)`,
    - `l(IV)` refs force single `l(IV)` only before non-verbal next tokens,
    - overlap refs (e.g. `KTU 1.17 I:23`) resolve by next-token verbality (`vb` -> `III`, non-`vb` -> `IV`).
- Extended linter parity in `linter/lint.py` to enforce the same `l(III)`/`l(IV)` context constraints with dedicated warnings.
- Added regression tests:
  - `tests/test_l_functor_vocative_refs.py`,
  - `tests/test_l_functor_vocative_context.py`,
  - `tests/test_linter_l_functor_vocative_context.py`,
  - updated pipeline ordering guard in `tests/test_tablet_parsing_pipeline.py`.
- Documented the strategy in `docs/l_functor_vocative_context_pipeline.md`.
- Applied only `l-functor-vocative-context` over `out/KTU *.tsv`: 124 row updates across 15 files (first pass 112 + format-variant pass 12), including `KTU 1.24`, `KTU 2.61`, and `KTU 2.72` section-style variants.
- Follow-up fix for over-forcing `l(III)/l(IV)`:
  - made `l` context reference keys section-aware in `pipeline/config/l_functor_vocative_refs.py` so Roman-column refs are not conflated (for example `KTU 1.4 I:23` vs `KTU 1.4 VII:23`),
  - added parser/linter regression tests for this collision class,
  - reapplied the corrected `l-functor-vocative-context` pass after restoring the previously over-pruned output files, preserving `l(I)` where no section-exact forcing is attested.
- Added `l + kbd(I)` compound-preposition normalization:
  - new parser step `LKbdCompoundPrepDisambiguator` (`pipeline/steps/l_kbd_compound_prep.py`) wired after `l-functor-vocative-context`,
  - context rule collapses `l` + `kbd` pairs (when `kbd(I)` is available) to single rows: `l(I)` and `kbd(I)/` with `POS=prep.` and `gloss=within`,
  - added linter parity warning for non-canonical `l kbd` payloads and regression tests for parser/linter behavior,
  - documented strategy in `docs/l_kbd_compound_prep_pipeline.md`.
- Added two additional high-frequency `l`/`k` bigram context refinements:
  - `LBodyCompoundPrepDisambiguator` (`pipeline/steps/l_body_compound_prep.py`) for `l + pˤn` and `l + ẓr` compound prepositions, collapsing to canonical single-row payloads with prepositional POS/gloss;
  - `KFunctorBigramContextDisambiguator` (`pipeline/steps/k_functor_bigram_context.py`) forcing `k(III)` in selected verb-leading bigrams (`yraš`, `tld`, `yṣḥ`, `yiḫd`, `ygˤr`) when the second token is verbal.
- Added shared config files for these context sets:
  - `pipeline/config/l_body_compound_prep_rules.py`,
  - `pipeline/config/k_functor_bigram_surfaces.py`.
- Added linter parity warnings for both new context layers and corresponding regression tests.
- Documented both strategies:
  - `docs/l_body_compound_prep_pipeline.md`,
  - `docs/k_functor_bigram_context_pipeline.md`.
- Added `LPrepositionBigramContextDisambiguator`
  (`pipeline/steps/l_preposition_bigram_context.py`) for high-confidence `l + X`
  contexts:
  - force single `l(I)` before `arṣ`, `špš`, `mlkt`, `ṣpn`, `il`, `kḥṯ`,
    `ršp`, `inš`, `bˤlt`, `ˤṯtrt`, `ˤpr`,
  - force `l(I) + bˤl(II)` outside `KTU 4.*`,
  - normalize lexicalized `l pn*` prepositions (`pn`, `pnm`, `pnh`, `pnk`,
    `pny`, `pnwh`) to canonical prepositional payloads with gloss `in front`.
- Added shared config for this context layer:
  - `pipeline/config/l_preposition_bigram_rules.py`.
- Extended linter parity with warnings for:
  - non-single `l(I)` in the targeted `l + X` bigrams,
  - non-collapsed `l bˤl` outside `KTU 4.*`,
  - non-canonical lexicalized `l pn*` prepositional payloads.
- Added regression tests:
  - `tests/test_l_preposition_bigram_context.py`,
  - `tests/test_linter_l_preposition_bigram_context.py`,
  - updated step-order guard in `tests/test_tablet_parsing_pipeline.py`.
- Documented strategy in `docs/l_preposition_bigram_context_pipeline.md`.

- Added `SuffixPayloadCollapseFixer` (`pipeline/steps/suffix_payload_collapse.py`) and wired it into `pipeline/tablet_parsing.py` after suffix normalization to collapse clitic-linked DULAT payloads to host-lexeme metadata.
- Rule: when `col3` already encodes suffix/enclitic markers (`+`, `~`, or bracketed clitic tails), strip `col4` suffix payload segments (`, -x ...`) and trim aligned suffix-function/suffix-gloss tails in `col5`/`col6`.
- Added linter support in `linter/lint.py` for this pattern (`variant_has_suffix_payload_linked_dulat`), warning when clitic-bearing analyses still link suffix payload lexemes in `col4`.
- Added regression coverage:
  - `tests/test_suffix_payload_collapse.py`,
  - `tests/test_linter_suffix_payload.py`,
  - expanded `tests/test_linter_warning_predicates.py`.
- Documented the strategy in `docs/suffix_payload_collapse_pipeline.md`.
- Re-ran only `SuffixPayloadCollapseFixer` across `out/KTU 1.*.tsv` outputs (`831` rows updated in `139` files), including `out/KTU 1.6.tsv` row `140617` (`g/+h | g | n. m. | (loud) voice`).

- Added `SuffixParadigmNormalizer` (`pipeline/steps/suffix_paradigm_normalizer.py`) and wired it into `pipeline/tablet_parsing.py` directly after `SuffixCliticFixer` to enforce canonical suffix/enclitic marker encoding in col3.
- Normalization rule: remove homonym numerals from pronominal suffix/enclitic segments while preserving marker and `=` (for example `+n(I)` -> `+n`, `+h(II)` -> `+h`, `+ny(III)=` -> `+ny=`, `~n(IV)` -> `~n`, `[n(II)=` -> `[n=`).
- Extended linter suffix marker validation in `linter/lint.py`: homonym numerals on marker slots are now flagged across the full pronominal suffix set (not only `n`), with updated warning text.
- Added regression coverage:
  - `tests/test_suffix_paradigm_normalizer.py`,
  - expanded `tests/test_linter_warning_predicates.py` for generalized marker checks.
- Documented the strategy in `docs/suffix_paradigm_pipeline.md`.
- Re-ran only `SuffixParadigmNormalizer` over current `out/KTU 1.*.tsv` outputs (`395` rows updated in `139` files), including user-facing `KTU 1.16` fixes (`143222`, `143578`, `143835`, `144119`, `144123`).

- Added `PronounClosureFixer` (`pipeline/steps/pronoun_closure.py`) and wired it into `pipeline/tablet_parsing.py` to remove noun-style trailing `/` from pronoun variants (for example `hw/` -> `hw`).
- Added morphology-aware `NominalCaseEndingYHFixer` (`pipeline/steps/nominal_case_ending_yh.py`) and wired it into `pipeline/tablet_parsing.py` to normalize noun/adjective terminal case endings `...y/` / `...h/` to explicit `/y` / `/h` when DULAT surface-form evidence supports it (for example `umy/` -> `um/y`).
- Extended `DulatMorphGate` with `surface_morphologies(token, surface)` for exact token+surface morphology lookup and used it as the gate for the new nominal case-ending step.
- Added linter warning support in `linter/lint.py` for pronoun rows that still use noun-style `/` closure.
- Added regression tests:
  - `tests/test_nominal_case_ending_yh.py`,
  - `tests/test_pronoun_closure.py`,
  - `tests/test_linter_pronoun_closure.py`,
  - extended `tests/test_dulat_gate_plurale_tantum.py` with `surface_morphologies` coverage.
- Re-ran only the new targeted refinement steps over current `out/KTU 1.*.tsv` outputs (`pronoun-closure`: `94` rows; `nominal-case-ending-yh`: `159` rows), including requested fixes in `out/KTU 1.6.tsv` (`140849`: `hw`, `141287`/`141303`: `um/y`).

- Added `IIIAlephCaseFixer` (`pipeline/steps/iii_aleph_case_fixer.py`) and wired it into `pipeline/tablet_parsing.py` to normalize III-aleph noun/adjective case-vowel encoding using `(u|i|a` + `/&u|&i|&a`.
- Added linter warning support for missing III-aleph case encoding in `linter/lint.py`:
  - detects stem-matching final-vowel noun/adjective variants that omit `/&` encoding and do not reconstruct surface.
- Added regression tests:
  - `tests/test_iii_aleph_case_fixer.py`,
  - `tests/test_linter_iii_aleph_case.py`.
- Documented strategy in `docs/iii_aleph_case_pipeline.md`.
- Re-ran only `IIIAlephCaseFixer` across `out/KTU *.tsv` (278 files scanned, 52 row updates), including `rpủ -> rpi`, `ỉqnủ -> iqni`, `nnủ (I) -> nni`, `ṣbủ (II) -> ṣba`, and `llủ -> lla/lli`.
- Corpus linter snapshot after this pass: reconstructability issues reduced from `4219` to `4164` (delta `-55`); III-aleph style warnings: `0`.

- Follow-up reconstructability pass for feminine `-t` and `ỉlt (I)` allographs:
  - added `ỉlt (I)` surface-`h` rewrites in `SurfaceReconstructabilityFixer` (`ilh -> il(t(I)/&h`, `ilht -> il(t(I)/&ht`) so `col3` reconstructs `col2`,
  - normalized sg/pl-ambiguous `ảṯt` and `ṯảt` surface forms from forced `/t=` to `/t` in targeted rows (`aṯ(t/t`, `ṯa(t/t`).
- Extended regression coverage in `tests/test_surface_reconstructability_fixer.py` for `ilh`, `ilht`, `aṯt`, and `ṯat`.
- Re-ran only `SurfaceReconstructabilityFixer` across `out/KTU *.tsv` (278 files scanned, 39 row updates), including user-flagged `153291`, `143704`, `153565`, and `153971`.

- Added `SurfaceReconstructabilityFixer` (`pipeline/steps/surface_reconstructability_fixer.py`) and wired it into `pipeline/tablet_parsing.py` before generic overrides to repair known surface/analysis mismatch classes in a dedicated pass.
- Implemented targeted reconstructability rewrites for user-flagged classes:
  - `thmt` singular ambiguity expansion (`thm(t/t; thm/t` with aligned DULAT/POS/gloss),
  - `thmtm` dual reconstruction (`thm(t/tm`),
  - `mtm` aligned variant repairs (`mt(II)/~m`, `mt[~m`, `mt(I)/m`, `mt(III)/m`),
  - `bnwt`/`bnwth` allographs (`bn&w(t(II)/t=`, `bn&w(t(II)/t=+h`),
  - `ymm`/`ymt`/`ymy` nominal allographs (`ym(I)/m`, `ym(I)/t=`, `ym(I)&y/`).
- Updated linter feminine `/t=` enforcement in `linter/lint.py` to skip plural-ending warnings when the same DULAT surface is explicitly singular+plural ambiguous (for example `thmt` with both `sg.` and `pl.` evidence).
- Added regression tests:
  - `tests/test_surface_reconstructability_fixer.py`,
  - `tests/test_linter_feminine_plural_t_ambiguous.py`.
- Documented the strategy in `docs/surface_reconstructability_pipeline.md`.
- Re-ran only `SurfaceReconstructabilityFixer` across `out/KTU *.tsv` (278 files scanned, 10 incremental row updates), including user-flagged `135723`, `138684`, `154087`, `152088`, `152470`.

- Added curated DULAT exclusions for automatic lexeme-final `-m` plurale-tantum classification (`pipeline/config/plurale_tantum_m_overrides.py`): `ḥlm (II)`, `ʕgm`, `ỉštnm`.
- Applied the same exclusion logic in both parser gate (`pipeline/steps/dulat_gate.py`) and linter (`linter/lint.py`) so `pl. tant.` expectations stay consistent.
- Extended non-plurale `-m` repair in `PluraleTantumMFixer` to restore truncated split forms (`ḥl(II)/m` -> `ḥlm(II)/m`) and strip stale `pl. tant.` POS markers even when analysis is already reconstructable.
- Extended feminine `-t` normalization (`pipeline/steps/feminine_t_singular_split.py`) to:
  - repair lexical `-t` in `/t=` variants (`hml/t=` -> `hml(t/t=`),
  - promote lexical `/t` to `/t=` in feminine plural contexts,
  - force `/t=` for curated tokens (`hmlt`, `ṯnt (II)`).
- Added regression coverage for these changes in:
  - `tests/test_dulat_gate_plurale_tantum.py`,
  - `tests/test_linter_plurale_tantum_m.py`,
  - `tests/test_plurale_tantum_m.py`,
  - `tests/test_feminine_t_singular_split.py`.
- Updated strategy docs:
  - `docs/plurale_tantum_m_pipeline.md`,
  - `docs/feminine_t_singular_split_pipeline.md`.
- Re-ran only targeted rules across `out/KTU *.tsv` (`PluralSplitFixer`, `PluraleTantumMFixer`, `FeminineTSingularSplitFixer`): 292 row updates in 69 files, including user-flagged `150689` (`ḥlm (II)` no longer `pl. tant.`) and `155988` (`ṯn(t(II)/t=`).
- Added `PluraleTantumMFixer` (`pipeline/steps/plurale_tantum_m.py`) as a dedicated targeted pass for lexeme-final `-m` plurale-tantum nouns, and wired it into `pipeline/tablet_parsing.py` after `PluralSplitFixer`.
- Extended `DulatMorphGate` (`pipeline/steps/dulat_gate.py`) with `is_plurale_tantum_noun_token(...)` using DULAT form morphology (`pl./du.` non-suffix inventory) to conservatively gate this rule.
- Normalized `col3` and `col5` for targeted rows:
  - enforced lexical + ending split style `...(m/m` (for example `šm(I)/m` -> `šm(m(I)/m`, `nš/m` -> `nš(m/m`, `šˤr/m` -> `šˤr(m/m`),
  - repaired unsplit forms (for example `šmm(I)/` -> `šm(m(I)/m`),
  - added `&y` allograph insertion when required (`šmym` -> `šm&y(m(I)/m`),
  - normalized spurious `+nm` tails in this class (for example `pn/m+nm` -> `pn(m/m`),
  - added `pl. tant.` in POS for targeted noun variants.
- Added dedicated parser tests (`tests/test_plurale_tantum_m.py`) for `šmm`, `šmym`, `šmmh`, `pnm`, `nšm`, `šʕrm`, multi-variant POS alignment, and non-target lemma safety.
- Added linter predicate `analysis_has_missing_lexeme_m_before_plural_split(...)` plus predicate tests (`tests/test_linter_warning_predicates.py`).
- Added linter rule for DULAT-backed lexeme-final `-m` nouns requiring `(m` before `/m` when reconstruction evidence indicates missing lexical `m`.
- Added linter rule for DULAT-backed plurale-tantum `-m` nouns requiring `pl. tant.` in POS, and regression coverage (`tests/test_linter_plurale_tantum_m.py`).
- Fixed a linter variable-clobber bug in `linter/lint.py` (`parts = analysis.split('+')`) that could corrupt downstream POS-column checks inside DB validation.
- Documented the rule workflow in `docs/plurale_tantum_m_pipeline.md`.
- Applied only the new `plurale-tantum-m` step across `out/KTU 1.*.tsv`: 475 rows updated in 78 files, including user-flagged IDs (`9544`, `139911`, `141623`, `146476`) and related `šmmh`/`pnm`/`nšm`/`šʕrm` classes.
- Follow-up fix: narrowed the `plurale-tantum-m` scope to DULAT lemmas that are explicitly lexeme-final `-m` (gate + step), preventing false `pl. tant.` POS promotion on non-`-m` lemmas (for example `pʕn`, `šp`).
- Reapplied only the corrected `plurale-tantum-m` step after restoring `out/KTU 1.*.tsv` to pre-pass state: 123 rows in 53 files updated, preserving intended `-m` targets and reverting over-broad POS changes.
- Extended `PluraleTantumMFixer` for host-drop terminal `-m` cases:
  - normalize `.../m` and `...m/` to `...(m/` when the host surface drops `m` (for example `pn/m; pn` -> `pn(m/; pn`, `pnm/+h` -> `pn(m/+h`),
  - infer missing suffix tails (`+h`, `+k`, `+y`, etc.) only when reconstruction becomes exact (for example `pnm/` -> `pn(m/+h`, `ḥym/` -> `ḥy(m/+k`),
  - normalize overlong `+n...` tails when dropping `n` is required by reconstruction (for example `+ny` -> `+y`).
- Hardened `PluraleTantumMFixer` rewrite safety: apply canonical rewrite only when it reconstructs to `col2`, or preserve already-reconstructable original.
- Extended linter predicate `analysis_has_missing_lexeme_m_before_plural_split(...)` to catch host-drop `-m` mismatches (for example `pnm/+h`, `pn/m`) and updated warning text accordingly.
- Expanded tests for `plurale_tantum_m` and linter predicates with `pnh`, `pn`, `pny`, `ḥyk`, and `+ny` normalization scenarios.
- Updated `docs/plurale_tantum_m_pipeline.md` with the formalized host-drop `-m` strategy, suffix inference, and tail-normalization rules.
- Re-ran only `PluraleTantumMFixer` across the full corpus (`out/KTU *.tsv`) from clean baseline: 36 rows updated in 25 files, including user-flagged `152464`/`152465` and related `143246`, `143400`, `143536`, `144092`, `150081`, `157515`, `160118`.
- Fixed plurale-tantum misclassification for `šlm (II)` by tightening DULAT gate logic: explicit singular morphology (`sg./sing`, including `sg., suff.`) now blocks `pl. tant.` classification in both parser gate (`pipeline/steps/dulat_gate.py`) and linter entry classification (`linter/lint.py`).
- Added regression coverage for this distinction:
  - new gate-level sqlite fixture test `tests/test_dulat_gate_plurale_tantum.py`,
  - parser repair test for `šl(m(II)/m~m; šlm(II)/m -> šlm(II)/~m; šlm(II)/m` in `tests/test_plurale_tantum_m.py`,
  - linter regression test ensuring no forced `pl. tant.` warning for `šlm (II)` with `sg., suff.` evidence in `tests/test_linter_plurale_tantum_m.py`.
- Extended `PluraleTantumMFixer` with a non-target repair path to clean historical false positives for non-plurale `-m` lemmas: restores lexical `m` heads and strips `pl. tant.` from aligned POS slots when reconstruction confirms the repair.
- Re-ran only `PluraleTantumMFixer` across `out/KTU *.tsv`: 40 rows in 19 files repaired for `šlm (II)` (including user-flagged `152787`).
- Tightened plurale-tantum classification to exclude cstr-only plural evidence (`pl., cstr.` without any absolute plural/dual form), fixing `qm` false positives.
- Added regression coverage for this case in parser/linter tests and re-ran only `PluraleTantumMFixer` across `out/KTU *.tsv` (2 rows updated), including user-flagged `136160` (`qm[; qm/`, POS `vb; n. m.`).

## 2026-02-23

- Clarified and simplified `README.md` pipeline-stage documentation for linguist-facing readability while matching the actual executed flow (upstream CUC-to-TSV input, bootstrap + context-aware candidate scoring, instruction refiner pass, ordered heuristic step chain, final report regeneration).
- Added shared onomastic override loader `pipeline/steps/onomastic_overrides.py` with support for the updated three-column TSV format (`dulat`, `POS`, `gloss`) while keeping backward compatibility for two-column files.
- Updated `pipeline/steps/onomastic_gloss.py` to consume the shared loader so gloss overrides now read the actual `gloss` column (not `POS`) from `data/onomastic_gloss_overrides.tsv`.
- Added `FeminineTSingularSplitFixer` (`pipeline/steps/feminine_t_singular_split.py`) and wired it into `pipeline/tablet_parsing.py` to normalize feminine singular unsplit analyses:
  - `Xt/ -> X/t`
  - `Xt(I)/ -> X(t(I)/t`
  - with conservative gates for feminine evidence, onomastic gender, and plural-form exclusion.
- Refined feminine singular split behavior for lexeme-final `-t` nouns so DULAT reconstruction remains faithful:
  - `Xt/ -> X(t/t`
  - `X/t -> X(t/t`
  - `Xt(I)/ -> X(t(I)/t`
  - `X(I)/t -> X(t(I)/t`
  - while preserving `.../t` for non-`t`-final lemmas.
- Added dedicated tests for the new feminine singular split step and for three-column onomastic override parsing (`tests/test_feminine_t_singular_split.py`, `tests/test_onomastic_gloss_overrides_format.py`).
- Extended linter predicates with `analysis_has_missing_feminine_singular_split` and added a noun-level warning for missing feminine singular `/t` splits in `linter/lint.py` plus predicate tests.
- Extended linter predicates with `analysis_has_lexeme_t_split_without_reconstructed_t` and added a warning for lexeme-final `-t` nouns that use `/t` without reconstructed `(t`.
- Added conservative linter fallback for feminine `/t` analyses so declared DULAT feminine headwords ending in `-t` can be validated via surface candidates when lexeme-only lookup omits them.
- Documented the rule-specific refinement workflow in `docs/feminine_t_singular_split_pipeline.md`.
- Re-ran only the new feminine singular split rule across `out/KTU *.tsv`: 1,350 rows updated in 184 files (including `9837`, `138163`, `160344`).
- Follow-up pass refined existing `/t` feminine splits for lexeme-final `-t` nouns to `...(t/t` and injected missing homonyms from declared DULAT tokens where needed (for example `9584`, `9588`): 624 rows updated in 143 files.
- Added terminal-`m` reconstructability completion for lexeme-final `-t` feminine splits where surface ends with `tm` (for example `thmtm` -> `thm(t/tm`), applied in a rule-only pass (72 rows).

## 2026-02-22

- Added generic surface-level parsing override support:
  - new step `GenericParsingOverrideFixer` in `pipeline/steps/generic_parsing_override.py`,
  - new curated source file `data/generic_parsing_overrides.tsv`,
  - pipeline wiring in `pipeline/tablet_parsing.py` (runs near the end of refinement, before final schema formatting),
  - unit coverage for full override application, optional-column preservation, and unresolved-row overrides.
- Enforced clitic-`n` annotation style in linter (`linter/lint.py`): column 3 now flags homonym-marked enclitic notation (for example `+n(I)`, `~n(II)`, `[n(III)`, `-n(IV)`) and requires host-style forms (`+n`, `+n=`, `~n`, `[n`, `[n=`).
- Updated `data/generic_parsing_overrides.tsv` high-frequency `n`/`tn` entries to host-style clitic notation in column 3 (no homonym numerals).
- Re-applied the latest curated `data/onomastic_gloss_overrides.tsv` updates across all generated tablet outputs (`out/KTU *.tsv`), refreshing onomastic glosses in 58 files (218 rows).
- Synced DN/PN/TN/MN/GN gloss payloads in regenerated outputs to the updated override table without changing pipeline code.
- Added canonical variant-divider spacing normalization in `pipeline/steps/schema_formatter.py` for structured columns (`col3`-`col6`): semicolons and commas now render with one following space (e.g. `a;b` -> `a; b`, `x,y` -> `x, y`).
- Added regression coverage in `tests/test_refinement_steps.py` for standard variant spacing and the edge case where the next variant begins with a clitic-leading comma.
- Re-ran schema formatting over `out/KTU 1.*.tsv` so variant separators are consistently spaced in all parsed tablet outputs.
- Added centralized onomastic gloss overrides file `data/onomastic_gloss_overrides.tsv` keyed by DULAT labels (with homonym markers where applicable).
- Added `OnomasticGlossOverrideFixer` (`pipeline/steps/onomastic_gloss.py`) and wired it into `pipeline/tablet_parsing.py` so onomastic glosses are overridden from the source file and DN/PN/TN/MN/GN glosses are normalized to `ʾ/ʿ` (not `ʔ/ʕ/ˀ/ˁ`).
- Added unit coverage for onomastic override behavior (direct override, slot-level override, non-onomastic guard, and transliteration normalization).
- Applied the onomastic pass across `out/KTU 1.*.tsv`, including global fixes for `ỉlmlk -> ʾIlimalku` and `kṯr (III)`/`ḫss` -> `Kôṯaru`/`Ḫasisu`.

## 2026-02-21

- Added lemma fallback indexing to `scripts/refine_results_mentions.py` so DULAT entries are considered even when `forms` has no matching rows for a token (for example `ủgrt` -> `ugrt`).
- Added `--only-not-found` mode to `scripts/refine_results_mentions.py` for targeted repopulation of rows marked `DULAT: NOT FOUND`, preserving unresolved rows (and their existing human comments) when no new candidates are found.
- Added regression coverage in `tests/test_refine_results_mentions.py` to ensure lemma-only DULAT entries still produce candidates.
- Re-ran targeted repopulation on `out/KTU 1.*.tsv`; 583 previously `DULAT: NOT FOUND` rows were filled from DULAT entry metadata.

## 2026-02-19

- Reversed the temporary `tnn`-only fallback scope and restored global KTU1-family homonym preference in bootstrap fallback (`scripts/bootstrap_tablet_labeling.py`): for lemma fallback rows, prefer homonyms attested in `CAT/KTU 1.*` when available.
- Added `Ktu1FamilyHomonymPruner` (`pipeline/steps/ktu1_family_homonym_pruner.py`) and wired it into `TabletParsingPipeline` to remove non-KTU1 homonym variants from aligned multi-option rows in `out/KTU 1.*.tsv` when at least one KTU1-attested homonym exists.
- Added unit coverage for the new pruner and updated bootstrap fallback tests (`tests/test_refinement_steps.py`, `tests/test_bootstrap_tablet_labeling.py`).
- Applied the new KTU1-family pruning rule across `out/KTU 1.*.tsv` (325 rows updated across 70 tablets) and regenerated lint reports under `reports/`.
- Added hardcoded bigram normalization for `ṯr il` in `pipeline/config/formula_bigram_rules.py` to force `ṯr (I)` (`n. m.`, `bull`) in the epithet formula “Bull Ilu”.
- Added regression coverage in `tests/test_refinement_steps.py` and applied the bigram pass across `out/KTU 1.*.tsv`, removing remaining `ṯr (IV)` “foul-smelling” ambiguity in `ṯr il` contexts.
- Tightened the same `ṯr il` rule to force the second token `il` to `DN` with gloss `ˀIlu` (instead of nominal readings such as `n. m. god`/`El`) for all occurrences of the epithet formula.
- Fixed slash-variant DN handling in `scripts/refine_results_mentions.py` for lemmas like `ỉ/ủšḫry`: prevent truncation to one-letter headwords in col3/col4, prefer the observed long surface shape in analysis when slash variants collapse to a short fragment, and added regression tests in `tests/test_refine_results_mentions.py`.
- Corrected affected rows for `ušḫry/išḫry` in `out/KTU 1.102.tsv`, `out/KTU 1.118.tsv`, `out/KTU 1.119.tsv`, `out/KTU 1.39.tsv`, and `out/KTU 1.47.tsv`.

## 2026-02-18

- Added conservative lemma-key fallback to `scripts/bootstrap_tablet_labeling.py` for DULAT entries that exist in `entries` but are missing from `forms`, while preserving explicit-form priority when form rows exist.
- Refined lemma fallback to prefer KTU 1-attested homonyms when available (using `attestations.citation` family parsing) so KTU 4-only homonyms are not imported into `KTU 1.*` fallback parses.
- Narrowed family-based fallback pruning to an explicit lemma allowlist (`tnn` only) so other cross-family homonym variants remain available for contextual interpretation.
- Added unit tests for bootstrap fallback behavior and precedence (`tests/test_bootstrap_tablet_labeling.py`).
- Corrected `out/KTU 1.6.tsv` row `141444` (`tnn`) from `DULAT: NOT FOUND` to DULAT-backed ambiguity (`tnn (I)`/`tnn (II)`) with explicit fallback comment.
- Normalized remaining mis-propagated `tnn` rows in `out/KTU 1.16.tsv` (`143862`) and `out/KTU 1.82.tsv` (`150000`) to the same DULAT-backed ambiguity payload.
- Tightened all current `tnn` rows in `KTU 1.*` back to KTU 1-attested `tnn (I)` only (`DN`, `dragon`) after validating `tnn (II)` is attested in `CAT 4.*`, not `CAT 1.*`.
- Added trigram formula discovery utility: `scripts/discover_formula_trigrams.py` (profiles top adjacent three-token formulas and dominant parsing payloads in `out/KTU 1.*.tsv`).
- Added hardcoded trigram formula normalization layer:
  - config: `pipeline/config/formula_trigram_rules.py`
  - step: `pipeline/steps/formula_trigram.py`
  - pipeline wiring: `pipeline/tablet_parsing.py` (runs before bigram disambiguation).
- Hardcoded high-confidence formula trigrams from corpus frequency/context:
  - `rbt aṯrt ym` -> enforce `rbt (I)` (`n. f.`, `Lady`)
  - `zbl bˤl arṣ` -> enforce `zbl (I)` (`n. m.`, `prince`)
  - `idk l ttn` and `l ttn pnm` -> enforce `l (III)` (`functor`, `certainly`)
  - `il tˤḏr bˤl` -> enforce `bʕl (II)` as `DN` (`Baʿlu`)
- Added unit tests for trigram rule application and DULAT-safety guards.
- Applied trigram normalization across `out/KTU 1.*.tsv` (34 row updates in 10 tablets) and refreshed reports.
- Expanded hardcoded formula-bigram normalization with three additional high-confidence rules:
  - `bn il` -> enforce `bn (I)` (`n. m.`, `son`)
  - `bn ilm` -> enforce `bn (I)` (`n. m.`, `son`)
  - `bt bˤl` -> enforce `bʕl (II)` as `DN` (`Baʿlu`)
- Added regression tests for all three new formula bigram rules in `tests/test_refinement_steps.py`.
- Applied the updated formula-bigram pass across `out/KTU 1.*.tsv` (34 row updates in 11 tablets) and regenerated lint reports.
- Added frequency-based formula-bigram discovery utility: `scripts/discover_formula_bigrams.py` (profiles top adjacent-token combinations and dominant parsing payloads in `out/KTU 1.*.tsv`).
- Added hardcoded DN-epithet bigram normalization layer:
  - config: `pipeline/config/formula_bigram_rules.py`
  - step: `pipeline/steps/formula_bigram.py`
  - pipeline wiring: `pipeline/tablet_parsing.py` (runs before offering-`l` disambiguation).
- Hardcoded high-confidence formula bigrams from corpus frequency detection:
  - `aliyn bˤl` -> enforce `bˤl (II)` as `DN` (`Baʿlu`)
  - `zbl bˤl` -> enforce `bˤl (II)` as `DN` (`Baʿlu`)
  - `bˤl ṣpn` -> enforce `bˤl (II)` as `DN` (`Baʿlu`)
  - `btlt ˤnt` -> enforce `ʕnt (I)` as `DN` (`ʿAnatu`)
  - `rbt aṯrt` -> enforce `ảṯrt (II)` as `DN` (`Asherah`)
- Added unit tests for formula-bigram rule application and safety guards.
- Applied formula-bigram normalization + follow-up offering-`l` cleanup across `out/KTU 1.*.tsv` (53 direct formula-row updates + 5 context updates).
- Refined `SurfaceOptionPropagationFixer` canonicalization to prevent malformed propagated ambiguity bundles:
  - collapse duplicated `(analysis, DULAT, POS)` variants and merge same-entry glosses with `/`,
  - harmonize glosses across variants that share the same `(DULAT, POS)` entry pair,
  - normalize weak-final `/...-...-w/` prefix variants from `...y[` to `...(w&y[` when needed,
  - compare subset compatibility by `(analysis, DULAT, POS)` instead of gloss text so canonical gloss rewrites can apply safely.
- Updated propagation allowlist to exclude `abn` and `bˤlm` from automatic cross-tablet propagation.
- Expanded `BaalPluralGodListFixer` to collapse mixed `bˤlm` plural rows already encoded as `bˤl(II)/m;bˤl(I)/m` to `bˤl(II)/m` (`lord`) in `KTU 1.*`.
- Repaired affected tablet rows:
  - fixed duplicated `ytn` alternatives (`!y!(ytn[;!y!(ytn[` -> single parse + slash-gloss),
  - fixed `hwt` gloss alignment to `word/matter;word/matter` when both options map to `hwt (I)`,
  - fixed `tˤny` weak-final `w` option to `!t!ˤn(w&y[`,
  - restored `out/KTU 1.3.tsv` to pre-whitelist state except requested row `9910` (`abn/;!a!bn[`).
- Added explicit `SURFACE_OPTION_PROPAGATION_ALLOWLIST` (`pipeline/config/surface_option_allowlist.py`) and wired `TabletParsingPipeline` to run `SurfaceOptionPropagationFixer` only on lint-vetted surfaces.
- Applied whitelist-only propagation across `out/KTU 1.*.tsv`: 384 rows in 54 files updated, with zero newly introduced lint issues and one resolved lint issue versus baseline.
- Excluded currently unsafe surfaces from propagation (`anš`, `imt`, `tbn`, `ˤnn`) based on lint-delta vetting.
- Tightened `SurfaceOptionPropagationFixer` safeguards to prevent low-confidence ambiguity spreading:
  - require aligned tuple-subset matching across `analysis`/`DULAT`/`POS`/`gloss` before expansion,
  - skip surfaces with competing equally-rich canonical payloads,
  - require all propagated analysis variants to reconstruct to the exact surface form.
- Added regression tests for the new safeguards (aligned-subset requirement, competing payload skip, and reconstruction gate).
- Generalized DULAT matching in the linter: when analysis-derived lexeme lookup fails but the surface form exists in DULAT, the linter now falls back to surface matching and reports a dedicated warning (`Lexeme parse did not match DULAT; matched by surface form`) instead of a hard `No DULAT entry found` error.
- Added reusable `SurfaceOptionPropagationFixer` pipeline step to propagate richer aligned option sets (`col3`-`col6`) across parallel rows sharing the same surface token when DULAT overlap confirms compatibility.
- Wired `SurfaceOptionPropagationFixer` into `TabletParsingPipeline` before attestation sorting so propagated options are normalized/sorted consistently downstream.
- Added tests for lookup fallback selection and surface-option propagation (positive case + overlap guard + short-surface guard).
- Added `KnownAmbiguityExpander` pipeline refinement step and wired it into `TabletParsingPipeline` so known high-value ambiguities are preserved on every run (currently `ydk` and `šlmm` full option sets).
- Added unit tests for pipeline ambiguity expansion behavior (`ydk`, `šlmm`, and non-matching rows).
- Follow-up test cleanup: restored `WeakVerbFixer` non-weak/non-verb assertions to `WeakVerbFixerTest` class scope after adding ambiguity-step tests.
- Expanded ambiguous lexeme rows to preserve all user-provided parsing alternatives for later contextual disambiguation:
  - `ydk`: added six aligned options (`yd(I)/+k`, `yd(I)/+k=`, `yd(II)/+k`, `yd(II)/+k=`, `!y!dk[`, `!y=!dk[`) with aligned DULAT/POS/gloss variants.
  - `šlmm`: added both nominal alternatives (`šlm(II)/~m` and `šlm(II)/m`) with aligned DULAT/POS/gloss variants.
- Normalized DULAT token spelling to `d-k(-k)/` in `out/*.tsv` so multi-option `ydk` rows remain linter-clean while keeping the expanded ambiguity.
- Fixed false-positive `No DULAT entry found for lexeme/surface` hits for `ydk` by expanding verb-root lookup keys in `linter/lint.py` to support both slash-wrapped (`/d-k/`) and non-leading-slash (`d-k/`) lemma conventions used in DULAT.
- Hardened `PluralSplitFixer` against malformed homonym plural splits (for example `šl(II)/m`) by repairing truncated lemma-final consonants when DULAT + surface reconstruction evidence is explicit.
- Normalized high-confidence TSV rows accordingly (including `šl(II)/m` -> `šlm(II)/m` and `d-k(-k)/` token normalization) across `out/*.tsv`, eliminating `ydk` and `šlmm` from `No DULAT entry found` top offenders.
- Reverted the recent `out/KTU 1.5.tsv` simplification pass for the user-flagged rows (`139778`, `139852`, `139857`, `140202`) and restored the prior multi-option analyses/POS values.
- Propagated the validated `KTU 1.1` formula fixes to true parallels in other tablets: `tḥmk -> tḥm/+k` with `tḥm, -k (I)` / `n. m.,pers. pn.` / `message, your(s)` in `out/KTU 1.3.tsv` (`10488`, `10496`) and `out/KTU 1.4.tsv` (`138769`, `138777`), and `twtḥ -> !t!w]t]ḥ(y[` in `out/KTU 1.7.tsv` (`141600`).
- Moved morphology lint report generation from GitHub Actions to a local pre-commit workflow.
- Added `scripts/generate_lint_reports.py` and `lint_reports/` modules to run linter with local DULAT/UDB databases and materialize committed reports under `reports/`.
- Added tracked hook `.githooks/pre-commit` and installer `scripts/install_git_hooks.sh` to enforce report refresh before commit.
- Added report parser `scripts/parse_lint_reports.py` and simplified `.github/workflows/morphology-lint.yml` to parse committed reports only.
- Added unit tests for lint output parsing and SVG trend chart rendering.
- Updated pre-commit hook to run Ruff on staged Python files (`ruff format` + `ruff check --fix` + `ruff check`) before report generation.
- Bootstrapped first-pass structured morphology outputs for all remaining `cuc_tablets_tsv/KTU 1.*.tsv` files into `out/` (coverage now matches all `KTU 1.*` sources).
- Added reusable tablet parsing pipeline (`pipeline/tablet_parsing.py` + `scripts/run_tablet_parsing_pipeline.py`) to automate missing/new tablet processing: bootstrap, mention-based refinement, and report regeneration.
- Added unit tests for pipeline target selection and dry-run behavior.
- Added instruction-driven refinement (`pipeline/instruction_refiner.py`) to normalize disallowed col2/col3 characters and force unresolved `?` rows when DULAT is explicitly missing.
- Applied instruction-driven cleanup to newly parsed `out/KTU 1.*.tsv` tablets (excluding curated `KTU 1.1-1.6`) and refreshed reports.
- Extended instruction-driven refinement to inject DULAT-backed POS gender markers for `n.`/`adj.` slots when gender is uniquely known (including pipeline wiring and unit tests).
- Re-ran refinement across non-curated `out/KTU 1.*.tsv` outputs and regenerated reports, removing 8,350 warning-level issues in this pass.
- Strengthened `.githooks/pre-commit` to use `uv` + `.venv` for repo-wide Ruff checks and full test-suite execution before commit; kept report regeneration for lint-relevant staged changes.
- Cleared pre-existing Ruff blockers in helper scripts (`scripts/generate_lint_reports.py`, `scripts/refine_results_mentions.py`, `scripts/notarius_refinement_pass.py`) and modules (`lint_reports/charts.py`, `linter/lint.py`) so the stricter gate passes.
- Migrated project runtime baseline to Python 3.13 (`pyproject.toml` + hook guard) and updated setup docs accordingly.
- Added pre-commit safeguard fallback: when `uv run` is unavailable, checks execute directly via `.venv` so commits remain enforceable.
- Converted refinement-step tests to `unittest.TestCase` style so they run under `unittest discover` in pre-commit.
- Added DULAT-backed token/form gate (`pipeline/steps/dulat_gate.py`) and wired `PluralSplitFixer`/`SuffixCliticFixer` to require matching DULAT evidence before rewriting analyses.
- Added refinement safety guard in `pipeline/tablet_parsing.py` to abort when any step changes too high a share of rows unless explicitly overridden.
- Extended pipeline CLI with safeguard controls (`--max-step-change-ratio`, `--allow-large-step-changes`) and reran full `out/KTU 1.*.tsv` + reports with the guarded step chain.
- Refined `SuffixCliticFixer` fallback for lemma-style analyses (e.g., `l(I)`, `šmm(I)/`) when exact DULAT surface forms are suffixal, and added regression tests for these patterns.
- Applied the improved suffix step across non-curated `out/KTU 1.*.tsv` files and regenerated reports (substantial reduction in suffix-related warnings/errors).
- Refined `WeakVerbFixer` for weak-initial `/y-/` prefix forms to enforce `!preformative!` + hidden `(y` normalization (including conversion of `!y!y...` to `!y!(y...`) and added focused unit tests.
- Applied a weak-verb-only refinement pass to `out/KTU 1.*.tsv` and regenerated reports, eliminating all weak-initial `(y` lint errors and reducing total issues from `8602` to `8223`.
- Added `WeakFinalSuffixConjugationFixer` to normalize weak-final finite forms with surface `-t` from `[` to `[t` when DULAT root is `/...-...-(y|w)/` (non-prefixed SC context), with dedicated tests.
- Applied the weak-final SC fixer across `out/KTU 1.*.tsv` and regenerated reports, eliminating all weak-final `"[t"` warnings.
- Refined `PluralSplitFixer` for lemma-style plural surfaces (for example `il(I)/` + surface `ilm` -> `il(I)/m`) using DULAT-gated morphology plus analysis-to-surface reconstruction checks; kept safeguards for lexemes whose lemma already ends in `m/t`.
- Refined `SuffixCliticFixer` confidence checks via analysis/surface reconstruction while preserving lemma-style suffix injection for DULAT-confirmed forms.
- Added shared reconstruction utilities (`pipeline/steps/analysis_utils.py`) and predicate tests for linter warning precision.
- Tightened linter warning predicates for `"Suffix form without '+'"` and `"Plural form missing split ending"` to trigger only on analysis/surface pairs with explicit missing-split evidence.
- Applied plural/suffix refinements across `out/KTU 1.*.tsv` and regenerated reports: total issues `8199 -> 6612`, warning count `1173 -> 126`, with `"Suffix form without '+'"` reduced to `32` and `"Plural form missing split ending"` reduced to `10`.
- Corrected enclitic/suffix encoding for lexeme-final `n/y` and enclitic `~` forms in `SuffixCliticFixer`: normalize `~+x` to `~x`, preserve lemma-final `n/y` (e.g., `mṯn`, `lšn`), and enforce `bʕd~n` instead of `bʕd+n`.
- Added linter guards for invalid enclitic `~+` usage and for false `/+n`/`/+y` splits when `n/y` is part of the declared lexeme (with unit tests).
- Reverted affected `out/*.tsv` cases (including the requested `9950`, `10199`, `10504`, `138180`, `139921`) and restored `klnyy` alternative parsing as `klny~y;kl(I)+ny~y`.
- Added `BaalPluralGodListFixer` and wired it into the parsing pipeline to normalize mixed `bˤlm` ambiguity rows to a single noun plural reading (`bˤl(II)/m`, `bʕl (II)`, `n. m.`, `lord`).
- Added a linter predicate/rule to flag the known bad `bˤlm` mix (`Baʿlu` DN + `labourer` plural) and unit tests for both the rule and the refinement step.
- Applied the fixer across `out/KTU 1.*.tsv` and corrected all currently matching rows (20 rows in 8 tablets), including `149082`.
- Added context-aware `OfferingListLPrepFixer` and wired it into the parsing pipeline to normalize sacrificial offering-list sequences (`offering noun + l + recipient`) from ambiguous `l(I);l(II);l(III)` to `l(I)` (`prep.`, `to`).
- Added a linter predicate for offering-list `l` ambiguity and unit tests for both the new refinement step and predicate.
- Applied the offering-list `l` normalization across `out/KTU 1.*.tsv` (34 rows in 17 tablets), including `KTU 1.119` row `154177`.
- Added `BaalLabourerKtu1Fixer` and pipeline wiring to remove `bʕl (I)` "labourer" from `KTU 1.*` `bˤl` ambiguity rows while preserving `bʕl (II)` and `/b-ʕ-l/`.
- Added linter predicate/guard for forbidden `bʕl (I)` "labourer" usage in `KTU 1.*` plus unit tests for both fixer and predicate.
- Applied the rule across `out/KTU 1.*.tsv` (171 rows in 50 tablets), including `152715` in `KTU 1.105`.
- Added `TsvSchemaFormatter` and pipeline wiring to normalize separator rows to compact `# KTU ...` format and enforce exactly 7 columns on labeled rows.
- Updated row serialization in pipeline steps to always emit 7 columns (`id`, `surface`, `analysis`, `DULAT`, `POS`, `gloss`, `comment`).
- Added strict linter check for `out/*.tsv` rows that are not exactly 7 columns and fixed parsing so `#` inside column-7 comments is preserved.
- Applied schema formatting across all `out/KTU 1.*.tsv` files; separator rows now use `# KTU ...` and data rows are normalized to 7 columns.
- Extended `TsvSchemaFormatter` to enforce a canonical TSV header row (`id`, `surface form`, `morphological parsing`, `DULAT`, `POS`, `gloss`, `comments`) and escape double quotes in data cells for safer GitHub TSV rendering.
- Added linter support for headered `out/*.tsv`: require a valid first header row and skip it from numeric-ID/content checks.
- Re-applied schema formatting across all `out/*.tsv` files to inject headers and quote-escape existing comments/glosses.
- Switched quote escaping from backslash style to RFC TSV quoting (for example `"..."` with doubled inner quotes `""`) to satisfy GitHub TSV parser requirements.
- Normalized separator rows to full 7-column TSV shape (for example `# KTU ...` in column 1 plus six empty columns) so files remain tabular under GitHub rendering.
- Added regeneratable DULAT attestation index support (`pipeline/dulat_attestation_index.py`) based on the `attestations` table, plus CLI builder script `scripts/build_dulat_attestation_index.py`.
- Added `AttestationSortFixer` and pipeline wiring to reorder aligned parsing options (`col3`–`col6`, and aligned `col7` comments) by DULAT attestation frequency descending, using the first DULAT entry per option when multiple entries/clitics are present.
- Applied attestation-based option sorting across all `out/*.tsv` files (1,036 rows updated in 112 tablets).
- Hardened base refinement separator handling to preserve separator row TSV column shape across all steps after schema normalization.
- Added a final `TsvSchemaFormatter` pass at the end of the refinement chain so later steps cannot reintroduce non-canonical quoting/shape issues.
- Switched schema formatter quote handling to GitHub-safe normalization: embedded double quotes in data fields are converted to single quotes.
- Re-applied schema formatting to `out/*.tsv` and removed remaining double-quote patterns that triggered GitHub TSV "Illegal quoting" rendering errors.
- Refined `KTU 1.1` lines with DULAT/UDB-backed parses in the `tlsmn`/`twtḥ` formula and nearby broken context (`ḫršnr`, `tḥmk`, `rdyk`), plus normalized `tptq` Gt stem marking (`]t]`) for correct DULAT mapping.
- Refined high-confidence `KTU 1.5` parses from DULAT-backed evidence: collapsed `šlyṭ` to the DULAT-supported nominal reading, normalized `/m-t/` verbal variants (`!i!mt[`) and POS token casing (`vb`), and normalized `bˤl` POS from `DN m.` to `DN`.
- Manual TCS-aligned pass on `out/KTU 1.5.tsv`: normalized the repeated `šlyṭ ... krs` formula payload across the parallel block (including `krs` as DULAT-backed `n. m. belt` baseline with explicit note-212 caveat), tightened the `nšt` note to keep both `/š-t-y/` and `/n-š-y/` readings, normalized the parallel `l(II)` gloss to `not`, and preserved unresolved broken tokens as explicit `?` payloads in cols 3-6.
- Added global fallback extraction of `¶ Forms:` tokens from `entries.text` (`pipeline/config/dulat_entry_forms_fallback.py`) so form lookup is no longer limited to the imperfect parsed `forms` table.
- Integrated the fallback into all DULAT loaders used by parsing and linting (`scripts/bootstrap_tablet_labeling.py`, `scripts/refine_results_mentions.py`, `linter/lint.py`) with deduplication safeguards.
- Extended form-text alias expansion for weak-final prefixed contractions (`/…-…-(y|w)/`: e.g., `tġly` -> `tġl`) in `pipeline/config/dulat_form_text_overrides.py`.
- Fixed fallback handling of word-break markers in forms (`<i>ytn</i>{.}<i>hm</i>`): fragments are now merged to full tokens (`ytnhm`) and no longer indexed as standalone fake forms (`hm`, `nn`).
- Tightened fallback `¶ Forms` truncation so extraction continues across genuine stem sections (`G ... . D ...`) but stops before lexical examples/prose, preventing spillover tokens like `ảlp`/`kbdm` from being indexed as forms of unrelated lemmas (`ảrḫ`, `mtnt`, `zbl`).
- Added fallback support for restoration-encoded split forms (`<i>mt</i>&lt;<i>n</i>&gt;<i>tm</i>` -> `mtntm`) and removed non-morphological `cf.` from abbreviation handling.
- Added regression coverage for both alias and forms-block fallback paths across parser/refiner/linter loaders, plus direct extractor tests.
- Re-ran the full tablet parsing pipeline (bootstrap + refine + refinement steps) for all tablets using explicit-file mode; regenerated `out/*.tsv` and lint reports with the new form recovery behavior.
- Refined gloss selection in `scripts/refine_results_mentions.py` to ignore attestation-style/cross-reference `senses.definition` rows (for example rows containing citations like `1.43:2` or `cf.`) and fall back to `translations` for compact gloss output.
- Added regression tests in `tests/test_refine_results_mentions.py` for attestation-sense filtering and translation fallback behavior.
- Refined `FeminineTSingularSplitFixer` to emit both singular and plural feminine `-t` parses for sg/pl-ambiguous DULAT surface forms (for example `ṣrrt/` -> `ṣrr(t/t;ṣrr(t/t=`), while keeping explicit `pl. tant.` rows plural-only.
- Extended `FeminineTSingularSplitFixer` to cover unlabeled numeral POS (`num.`) with lexical final `-t` (for example `rb(b)t` -> `rb(t/t`), and prevented numeral rows from auto-expanding to `;.../t=` in sg/pl-ambiguous form lists.
- Added regression coverage in `tests/test_feminine_t_singular_split.py` for sg/pl-ambiguous feminine `-t` reconstruction.
- Re-applied the feminine `-t` split step across `out/KTU *.tsv` (66 files touched, 275 rows updated) to propagate this fix corpus-wide.
- Refined `NominalFormMorphPosFixer` so feminine split analyses carry explicit POS number markers: `/t` -> `sg.`, `/t=` -> `pl.` (including `num.` rows such as `rb(b)t`), while preserving existing number labels.
- Added regression tests in `tests/test_nominal_form_morph_pos.py` for noun and numeral rows with feminine split endings.
- Re-applied `nominal-form-morph-pos` across `out/KTU *.tsv` to propagate sg./pl. POS normalization after feminine split unwrapping.
- Refined `VerbFormEncodingSplitFixer` to encode infinitives as `!!...[/` and participles as `...[/`, and to split mixed finite/infinitive/participle POS bundles into distinct aligned variants before unwrapping.
- Added linter guardrails for verbal non-finite encoding: `vb ... inf.` now warns unless analysis is `!!...[/`, and participles warn when they incorrectly use the infinitive `!!` marker.
- Added regression tests in `tests/test_verb_form_encoding_split.py` and `tests/test_linter_infinitive_encoding.py`, and applied a targeted global post-refinement pass (`verb-form-encoding-split` + post-verb unwrap/dedupe) across all `out/KTU *.tsv`.
