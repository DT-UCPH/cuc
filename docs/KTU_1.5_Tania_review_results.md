# KTU 1.5: disposition of Tania Notarius’s feedback

Implementation and local-source research, 2026-09-07. This supersedes the initial
[plan](KTU_1.5_Tania_review_plan.md). Scope: the 25 token IDs touched by commits
`cb467e9`, `0dd3120`, and `453fdbc`, plus necessary validation and parser fixes.
Remote freshness was not checked. No new parsing notation has been adopted.

Integrated on 2026-09-28 against `c3d73d15`, including Tania's later commits
`08d82f96` and `c3d73d15`. The earlier dispositions below incorporate the
clarifications that affected the merge; new incomplete proposals remain pending.

## Preservation and structure

[Original feedback](KTU_1.5_Tania_feedback_original.json) records the exact Git
hunks from all five commits, including malformed records and deleted wording.
The source commits remain the ultimate audit trail; the preceding file is
`7af37cc:reviewed/KTU 1.5.tsv`. Original expert wording is preserved there even
where the working comments now distinguish accepted analyses from questions.

Repaired the extra tabs in `nšt` and `ṭˤn`, the missing comment field in `qrdm`,
and the broken `aliynqrdm` record. The latter retains its original sign span
`aliy[[n]] . qrdm`; Tania’s proposed segmentation is recorded as a proposal.
All 680 token IDs remain. The structural repair alone produced 789 data rows;
the initial adjudication left 782. Integration of the later accusative `thw`
and retained nominative `špt` alternatives leaves 784, each with eight fields. Removed agent
hypotheses remain recoverable in the original revisions; they are not presented
as published authorities. Separate physical tokens were not merged.

Tania’s explicit alternatives are first. Where she asks a question or rejects
one option without choosing another, the remaining order is not attributed to
her. Competing source readings remain as rows when expressible in the current
notation, or explicitly attributed in comments when encoding requires a decision.

## Per-comment evidence and disposition

References below are KTU references unless stated otherwise. DULAT entries and
forms were checked in the local structured cache; EUPT through the local module
lookup. Tropper references refer to *Ugaritische Grammatik* (2012), printed page
numbers. Exact scanned pages 559, 602, 622 and 634 were inspected, as was Wyatt
p. 119; additional Tropper prose was checked in the searchable text. The EUPT
line-number offset for `ṯbth` is recorded rather than silently harmonized.

| Token / reference | Evidence and disposition |
|---|---|
| `šlyṭ`, 158592 I:3; 158718 I:29 | Tania rejects the Š participles. Those rows were removed in the first pass; their disposition is now reopened following verification of DULAT’s reported alternatives (p. 810). Tropper p. 602 treats a divine name with tentative verbal-adjective derivation from √lw/yṭ, or alternatively √šlṭ with vowel-letter y; EUPT gives a divine name. Preserve Tropper’s etymological discussion in comments. A verbal etymology does not establish a synchronic participle. Wyatt’s “Encircler” does not justify three precise verbal parses. |
| `yṯb`, 158622 I:9; 158790 II:13 | Removed the endingless singular participle rejected by Tania. Tropper p. 634 lists prefix conjugation 3 m. dual at both occurrences and 1.2 I:19; EUPT instead tags suffix conjugation 3 m. dual. Both finite options remain. Parser rejection is restricted to these three attestations and requires a finite sibling for the same token. |
| `gmpn`, 158634 I:12 | Tania proposes `g&mpn`; the sign span marks m as erased. Current morphology targets the edited `gpn`, so no notation change. Her proposal remains visible. Physical signs, editorial deletion, and lexical allography must remain distinct. |
| `npš`, 158648 I:14 (adjacent 158647) | Tania identifies different meanings of the same lexeme. EUPT has two occurrences of the same lemma. Retain both physical IDs and withdraw the legacy token-joining question. Semantic identity is not evidence for joining tokens. |
| `hm`, 158651 I:15 | Retain Tania’s double-question analysis. DULAT hm II discusses the interrogative compound. Wyatt pp. 116–117 n. 11 explicitly proposes the tentative maritime emendation `thw hm` → `thm`; preserve that attribution in comments without merging tokens or calling it an established reading. |
| `brky`, 158657 I:16 | Preserve Tania’s asyndetic-relative-clause interpretation. Tropper p. 283 §52.421 discusses a pond attracting wild bulls and feminine agreement; EUPT instead gives masculine nominative `birkayu`. Record the disagreement for discussion; do not infer a new encoding or universal case policy from it. |
| `imt`, 158664–158665 I:18 | Tania rejects D. Keep the nominal option first, but retain the D alternative: Wyatt pp. 118–119 n. 20 explicitly proposes m(w)t “kill”, tentatively for all three occurrences, including the repetition at 158670. Replace the vague joint “Wyatt / Huehnergard lemma” attribution with the actual Wyatt passage. |
| `blt`, 158667 I:18 | “Not necessarily D” is non-exclusive. Add G first as the option supported by Tania’s objection and DULAT entry 1203’s form-level G suffc. label; DULAT’s entry-level stem is D. Retain D with Tropper p. 559 §74.414.2 and EUPT D-SK 3 f. sg. Both use the existing 3 f. sg. suffix marker `[t===`. |
| `qran`, 158689 I:23 | Preserve the proposed inflectional a as pending. DULAT entry 3519 gives imperative plus suffix; Tropper p. 622 §75.234 discusses suffix conjugation with an imperative alternative; EUPT gives G-SK 3 m. sg. plus 1 c. sg. suffix. These alternatives are described explicitly; no new marker is invented. |
| `nšt`, 158704 I:26 | Add Tania’s G prefix 1 c. pl. `/š-t-y/` “drink” first as `!n!št(y[`. DULAT entry 3206 itself records Smith UNP p. 142’s dissent “let us drink”. Preserve N `/n-š-y/`; also retain EUPT’s G suffix 2 m. sg. “forget”, alongside DULAT’s report of Del Olmo MLC p. 215’s precative G interpretation. This is a source disagreement, not a global N-stem rule. |
| `ṭˤn`, 158706 I:26 | Apply Tania’s `!!ṭˤn[/`: the slash was already required for infinitives and already checked by the linter. EUPT supports the infinitive. This repairs missed validation rather than introducing notation. |
| `ttrp`, 158723 I:31 | Preserve Tania’s “DULAT 733” citation. Structured DULAT entry 3678 supports Dt prefix conjugation. The printed DULAT page number has not been independently verified; no rule is inferred from the added citation. |
| `špt`, 158728 II:2 | Retain accusative and nominative. Tania's 2026-09-28 clarification explicitly allows either if a verb was omitted or erased, superseding the earlier rejection. EUPT supports accusative. General case policy remains pending. |
| `lšn`, 158735 II:3 | Remove unsupported nominative; retain the feminine accusative object interpretation first. Add EUPT’s masculine singular, case-unspecified reading with explicit attribution; DULAT gives feminine. The linter explains this exact reviewed disagreement without weakening gender checks elsewhere. |
| `ybl`, 158749 II:5 | Retain genitive first with Tania's 2026-09-28 clarification, "genitive if it depends on the preposition k", and Tropper p. 783 §83.111c's comparison to roasted olive. Retain the EUPT nominative alternative. Case depends on the syntactic construal. |
| `yraun`, 158754 II:6 | Keep Tania’s vowel-letter and scribal-error possibilities pending. Tropper p. 622 §75.236 discusses infinitive plus energic or emended suffix conjugation; EUPT tags suffix conjugation with energic II. Existing prefix analysis is not thereby certified. Source alternatives and the unresolved encoding problem remain in comments. |
| `ṯtˤnn`, 158757 II:7 | Preserve the enclitic-plus-assimilated-pronoun proposal and existing alternatives. EUPT tags suffix conjugation with energic II; Tropper p. 506 discusses infinitive, energic II and object suffix. No blanket `+nn` / `~nn` conversion. |
| `tbˤ`, 158760 II:8 | Preserve dual/plural question. EUPT’s dual suffix-conjugation tag and imperative translation need reconciliation. No plural reading is attributed to Tania simply because she asks. |
| `qrdm`, 158776 II:11 | Tania’s explicit singular plus enclitic -m is first. Normalize `sing.` to existing `sg.` and include the enclitic in POS. Retain plural with EUPT’s parallel at II:18 attributed. |
| `bn`, 158779 II:11 | Preserve the question about nominative after preceding l. EUPT reads vocative particle plus nominative `binu`; a vocative particle is not automatically a genitive-governing preposition. No general change. |
| `ṯbth`, 158804 II:16 | Infinitive remains a question. DULAT entry 4473 gives the feminine noun “seat / sitting”; EUPT at its II:15 likewise tags feminine genitive `ṯib(a)ti`. Burns’s action classification/root yṯb does not independently establish an infinitive. |
| `aliynqrdm`, 158817 II:18 | Restore the broken record and retain Tania’s complete segmentation proposal. EUPT distinguishes aliy and plural qrdm. Current combined token remains unresolved; do not invent a split or assign a new ID. |

## Diagnosed failure mechanisms and durable changes

1. **Incomplete source retrieval and unresolved morphological precision.**
   The šlyṭ verbal rows entered history at `045abca`; current automatic output
   does not contain them. That establishes where the rows entered this file,
   not that their lexical hypotheses were invented. On reinspection following
   the user's correction, DULAT p. 810, entry 4055, explicitly reports Margalit
   MLD p. 90 (lw/yṭ), De Moor UF 11 (1979), p. 641 n. 12 (ly/uṭ, Š), and other
   interpretations. The lookup helper previously omitted these full notes.
   It now includes them. The blanket characterization of these roots as
   unsupported is withdrawn. Which historical row matches which author's
   proposed root, stem, voice and gloss still needs direct-source adjudication;
   Tania's rejection remains attributed. See the
   [lexeme-registry discussion](KTU_1.5_shlyt_lexeme_registry_discussion.md).
2. **Candidates not adjudicated in context.** The exact messenger yṯb participles
   survived automatic ambiguity. Added an attestation-scoped pruner and warning,
   retaining conflicting finite analyses. An inventory found 48 yṯb participle
   rows in committed automatic 0.2.8, only three in this rule’s scope; 45 are
   outside adjudication. Historical 0.2.7 has 46/3 and 0.2.6 has 48/3. Historical
   generated directories were not rebuilt.
3. **Overconfident construct/case inference.** The spaCy context step interpreted
   any adjacent nominal slash as a construct head, imposed nominative on heads,
   and could turn prepositional dependents into absolute state. It now requires
   explicit, unambiguous construct support, preserves head case when not governed,
   and preserves state under a standalone preposition. The previous step changed
   812/2511 rows (32.34%) and tripped its safeguard in the representative run;
   the corrected context step changed 282/2511 (11.23%). The separate default
   nominal-case fallback remains unchanged pending policy discussion.
4. **Edited-reading validation drift.** Clean regeneration exposed im and lnh
   analyses reconstructing physical signs despite edited targets m and ln.
   Reconstruction pruning/fallback now uses the edited target, editorial
   normalization precedes final fallback, and fallback retains comments and
   candidate hints. No lexical solution is invented for these unresolved tokens.
5. **Malformed records silently accepted.** A shared validator now rejects
   non-eight-field reviewed records and nonnumeric IDs before comment splitting
   or padding. The linter reports the exact bad line; evaluation fails explicitly.
   Legacy seven-field input remains supported. An unrelated malformed reviewed
   `KTU 2.10.tsv` record (line 20) was exposed by strict whole-corpus scoring and
   is outside this review; named-tablet scoring now scopes its inputs explicitly.
6. **Reports could overwrite their own baseline.** The full-regeneration wrapper
   now owns report generation and disables the nested pipeline refresh. Its
   explicit reports directory is respected. External before/after lint captures
   remain the independent check.
7. **Published dissent mistaken for invalid data.** Two exact reviewed analyses
   (nšt G versus DULAT N, lšn masculine versus DULAT feminine) now produce source
   disagreement information for the named diagnostic. Attestation, analysis,
   lexeme and POS must all match. Automatic rows and unrelated diagnostics retain
   their checks; reconstruction is never exempted by scholarly attribution.

## Discussion agenda

These are open decisions, not silently implemented rules:

- Which cases should be supplied when contextual evidence is incomplete, and how
  should syntactic roles and uncertainty be represented? Separate this from
  construct state and from the lexical gender disagreement in brky/lšn.
- How should lengthened imperative a be encoded, and which qran reading applies?
- How should energic material, enclitics and assimilated object suffixes compose
  in yraun and ṯtˤnn? Resolve the linguistic analysis before marker conversion.
- Should sign-level deletions ever enter morphology, or remain solely in the
  sign span? Current reconstruction deliberately uses the edited reading.
- Does aliynqrdm require an upstream tokenization correction? What is the desired
  reviewed representation until that correction is independently established?
- Reconcile the remaining local readings: tbˤ number/conjugation, ṯbth noun versus
  infinitive, brky syntax/gender/case, and the tentative Wyatt maritime emendation.

## Validation scope

The automatic regeneration scope is TF 0.2.8, KTU 1.5 plus its direct messenger
parallel KTU 1.2. Other automatic tablets and historical TF versions are not
claimed to have been brought up to date. This bounded run tests the implicated
parallel and the broader context change without overwriting unrelated reviewed
material. All generated files are published only from completed staged pipeline
runs with change-ratio safeguards enabled; no generated TSV was hand-edited.

See the final validation figures appended below. Agreement scoring compares
unordered analysis sets; it neither measures first-option preference nor proves
philological correctness.

- Full unit suite: **1,057 tests passed**.
- Reviewed reconstruction on 2026-09-07: **724 variants checked, zero mismatches**; nine
  merge exceptions and two damaged targets were explicitly skipped.
- Independent ERROR multiset comparison: **zero new occurrences** in reviewed
  KTU 1.5 or in the two regenerated automatic files. Existing reviewed errors
  decrease from 57 to 43; automatic errors decrease from 27 to 19. These files
  are not claimed to be lint-clean.
- Regeneration retains all 958 automatic token IDs in 1.2 and 680 in 1.5;
  automatic data rows change from 1398 to 1437 and from 957 to 967 respectively.
  The context fix preserves more competing candidates instead of collapsing
  them through unsupported construct chains. Default nominative labels remain
  a known limitation, not newly adjudicated syntactic conclusions.
- Exact analysis-set agreement against the revised reviewed data improves from
  **68.79% to 69.10%** for KTU 1.2 and **68.24% to 68.97%** for KTU 1.5.
- Project skill validators pass. Generated empty comment fields deliberately
  retain trailing tab delimiters required by the seven-field schema.

Reproduction from the repository root (use a fresh empty staging directory):

```bash
(cd agent && .venv/bin/python -m unittest discover -s tests)
agent/.venv/bin/python agent/scripts/regenerate_tablets_and_reports.py \
  --source-dir agent/generated_sources/cuc_tablets_tsv/0.2.8 \
  --out-dir /tmp/ktu15-reproduction/auto_parsing/0.2.8 \
  --reports-dir /tmp/ktu15-reproduction/reports \
  --files 'KTU 1.2.tsv' 'KTU 1.5.tsv' \
  --skip-source-refresh --enforce-step-change-limit
agent/.venv/bin/python .agents/skills/audit-ugaritic-analysis-reconstruction/scripts/check_reconstruction.py \
  'reviewed/KTU 1.5.tsv'
```

Refreshed latest lint reports are
local artifacts under `agent/reports`; named-tablet agreement reports are under
`agent/reports/ktu_1_5_tania`. These report directories are ignored by Git.

## Integration of the September 28 feedback

The working file contained five unresolved stash-conflict blocks after commits
`08d82f96` and `c3d73d15`. Resolution preserves the later comments rather than
reapplying the September 7 dispositions unchanged:

- Retained Tania's accusative `thw` alternative with its complete identity and
  sign span; retained both cases for `špt` and the conditional genitive for `ybl`.
- Restored missing comment delimiters in `kḏd` and `ˤbdk`. The intentionally
  emptied POS and gloss of the unsplit `kḏd` row remain empty.
- Attached the four incomplete alternative records for `aṣḥ` (158834), `ḥšn`
  (158857, 158860) and `tˤtd` (158861) to their tokens as attributed proposals.
  Their exact original lines, including spacing and tabs, remain in the audit.
- Moved `/ Haddu` from the `unhd` sign span into its comment. Other later
  linguistic comments remain available for adjudication, including the genitive
  requests at II:12 and II:20 and the column III proposals.

The audit now contains 51 changed hunks from all five expert commits. It is
reproducible with the checked-in exporter; the first three commits reproduce
the original audit byte for byte:

```bash
agent/.venv/bin/python agent/scripts/export_review_feedback.py \
  --tablet 'reviewed/KTU 1.5.tsv' \
  --output docs/KTU_1.5_Tania_feedback_original.json \
  cb467e9 0dd3120 453fdbc 08d82f96 c3d73d15
```

Validation on 2026-09-28:

- 784 reviewed rows, exactly eight fields each; the original 680 token IDs are
  unchanged. Reconstruction checks 726 variants with zero mismatches, with
  the same nine merge exceptions and two damaged targets skipped.
- All 1,057 unit tests passed. Five report tests passed again after adding
  assertions that nested pipeline report generation is disabled.
- Clean, safeguarded regeneration of TF 0.2.8 KTU 1.2 and 1.5 matches the
  prepared automatic files byte for byte. Exact analysis-set agreement is
  69.10% and 68.97%, respectively.
- Independent lint against `c3d73d15`, using the same current linter and local
  DULAT/UDB databases for both sides, reports zero new ERROR occurrences.
  Reviewed KTU 1.5 decreases from 69 errors to 43; automatic KTU 1.2 from
  14 to 12 and KTU 1.5 from 13 to 7. Existing errors remain outside this cleanup.

The remote fetch failed because SSH authentication was unavailable. These
results use the local `c3d73d15` baseline, not a verified fresh remote head.
