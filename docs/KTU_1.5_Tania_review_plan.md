# KTU 1.5: Tania Notarius feedback inventory and implementation plan

Initial repository audit, 2026-09-07. This is a plan, not a linguistic adjudication.
No reviewed data, generated data, parser rules, or notation conventions were changed.
This document preserves the initial audit. The implementation and the later
2026-09-28 feedback are covered in [the results](KTU_1.5_Tania_review_results.md).

## Scope and provenance

The local checkout is at `453fdbc`. Tania's three commits affecting
`reviewed/KTU 1.5.tsv` are `cb467e9`, `0dd3120` (2026-08-16), and `453fdbc`
(2026-09-06). The file's immediately preceding revision is `7af37cc`.
The combined diff changes or adds 29 physical lines, touching 25 numeric token
IDs, all in columns I–II. Both versions contain 680 distinct numeric token IDs.
These findings concern the commits available locally; remote freshness was not checked.

Older comments already attributed to Tania are not newly introduced feedback.
Keep their provenance distinct from these three commits. Rejection of an existing
analysis does not automatically specify which remaining analysis she prefers.

## Structural findings

The reviewed schema has eight fields: ID, surface, sign span, analysis, DULAT,
POS, gloss, comments. Before these commits all 788 data rows had eight fields.
The current file has 790 physical data lines, of which five have incorrect widths:

| Current file line | Token | Problem | Repair boundary |
|---|---|---|---|
| 190 | 158704 `nšt` | Nine fields; proposed alternative contains a tab | Preserve the complete proposal in comments first; adjudicate separately |
| 192 | 158706 `ṭˤn` | Nine fields; proposed encoding contains a tab | Preserve the complete comment in one field |
| 301 | 158776 `qrdm` | Seven fields; new alternative lacks comments | Add final field and attribute the alternative to Tania; normalize `sing.` separately |
| 356–357 | 158817 `aliynqrdm` | One record broken into three- and six-field lines; sign-span content overwritten | Recover identity and sign span from the prior revision, verify against matching TF, and preserve her entire replacement text as a proposal |

The last case is not just a newline repair: `aliy[[n]] . qrdm` was replaced by
analysis-like text. Do not invent a new token or treat the continuation's `qrdm`
as an ID. Keep her proposed segmentation while restoring the canonical record.
After repair, expect 789 data rows: the original 788 plus her new `qrdm` alternative.
Preserve all 680 IDs, their order and line references, and all comments and alternatives.

## Complete inventory of newly affected tokens

The descriptions below summarize Tania's comments; they do not endorse or expand them.

| Reference / ID | Feedback | Initial treatment |
|---|---|---|
| I:3, 158592; I:29, 158718 `šlyṭ` | Rejects several proposed Š participles | Trace each alternative's source and history; separate unsupported agent hypotheses from published dissent |
| I:9, 158622; II:13, 158790 `yṯb` | Rejects participle; II:13 explicitly cites missing plural/dual ending and negation | Investigate clause, agreement, negation and parallels; avoid a blanket surface-based ban |
| I:12, 158634 `gmpn` | Suggests `g&mpn` | Discuss against current editorial-layer convention; `m` is erased in `g[[m]]pn` |
| I:14, 158648 `npš` | Two meanings of the same word, not different words | Inspect adjacent physical tokens and existing migration/merge note; do not merge IDs from semantics alone |
| I:15, 158651 `hm` | Rejects Wyatt-associated merge; identifies double-question marking | Preserve independently verified Wyatt reading and Tania's objection with separate attribution |
| I:16, 158657 `brky` | Replaces “fronted object” with “asyndetic relative clause” | Local syntactic interpretation; retain prior interpretation only if sourced |
| I:18, 158664–158665 `imt` | Rejects D-stem analysis | Verify what Wyatt actually proposes and what the Huehnergard lemma supports; combined attribution may overstate evidence |
| I:18, 158667 `blt` | “not necessarily D” | Non-exclusive objection; research G/D alternatives, not a categorical stem replacement |
| I:23, 158689 `qran` | Proposes moving `a` into inflection for lengthened imperative | Research linguistic claim and notation separately; defer convention change |
| I:26, 158704 `nšt` | Proposes `/š-t-y/` “drink”, `!n!št(y[` | Research as an alternative to DULAT-associated N `/n-š-y/`; derive full POS from evidence |
| I:26, 158706 `ṭˤn` | Infinitive requires `!!ṭˤn[/` | Already required by current conventions; verify local infinitive reading and existing lint behavior |
| I:31, 158723 `ttrp` | Adds “DULAT 733” | Citation addition; verify page and preserve, not a new rule |
| II:2, 158728 `špt`; II:3, 158735 `lšn` | Challenges case assignments and the policy of supplying cases | Separate local syntactic errors from proposed removal/replacement of case annotation; `špt` wording is ambiguous |
| II:5, 158749 `ybl` | Questions genitive | Local syntax audit, including the construct chain |
| II:6, 158754 `yraun` | Second aleph may be a vowel letter or an error for `n`; suggests encoding | Preserve both possibilities as provisional; check editorial and morphological layers |
| II:7, 158757 `ṯtˤnn` | `+nn` still enclitic despite assimilated pronoun | Research analysis of enclitic plus suffix and existing marker policy; defer global conversion |
| II:8, 158760 `tbˤ` | Questions dual versus plural | Investigate addressees and parallels; question does not assert plural |
| II:11, 158776 `qrdm` | Adds singular plus enclitic `-m` | Preserve as Tania's explicit first alternative; verify POS includes enclitic consistently |
| II:11, 158779 `bn` | Questions nominative after preposition/vocative particle | Distinguish possible analyses of preceding `l` before deciding case |
| II:16, 158804 `ṯbth` | Asks whether infinitive | Research proposal; do not silently promote a question to accepted morphology |
| II:18, 158817 `aliynqrdm` | Replaces row with segmented analysis-like text, including `qrd/~m ?` | Recover structure first; investigate tokenization and tentative segmentation separately |

## Where mistakes may originate

1. **Reviewed alternatives without adequate evidence.** The `šlyṭ` verbal
   strings enter file history at `045abca` (2026-07-22). Today's automatic
   output contains nominal/name options, not these verb options. Inspect that
   commit and its supporting sources before assigning responsibility. An older
   helper, `agent/scripts/fix_col4_1_5_1_6.py`, already describes invented
   `šlyṭ` roots: the issue has been recognized before, but the helper is not
   evidence for the correct linguistic reading and should not be rerun blindly.
2. **Automatic ambiguity surviving review.** Today's automatic file contains
   `yṯb` participles at both disputed occurrences. Compare the exact historical
   automatic input to the agent review; current overlap alone does not prove
   the original route. Review must test each candidate in its clause.
3. **Inferred features appearing certain.**
   `agent/morph_features/nominal_completion.py::_infer_case` defaults eligible
   nominals to `nom.` without clause evidence. Audit callers, later context
   refinements and history to identify its actual contribution to these rows.
   Construct state must not be equated with genitive case.
4. **Existing checks not closing the review loop.** Infinitive notation already
   requires `!!...[/`, and `test_linter_infinitive_encoding.py` exists. Establish
   whether this row was flagged, the severity, and how the warning was handled.
5. **Structural consumers are permissive.** The evaluation loader pads short
   rows, folds excess fields into comments, and accepts a nonnumeric nonempty
   token ID. It can therefore misinterpret the broken continuation instead of
   failing explicitly. The linter's exact-width check is scoped to `out/*.tsv`;
   reviewed schema validation needs dedicated examination and tests.
6. **Instructions can perpetuate reviewed errors.** The review skill says to
   follow KTU 1.5 as the precedent and describes Tania's reviews as blank-slate.
   That description needs review-specific provenance; it is false for these
   comments on agent analyses. The quick checklist also retains older column,
   alternative-format, and DULAT-only restrictions that need reconciliation with
   the current guide and this task's attribution policy. The June review notes
   use old IDs and older schemas and cannot serve as current authority.

## Ordered implementation plan

1. **Lossless structural repair only.** Use immutable Git revisions as the
   original evidence. Restore the eight-field records, preserving every word of
   Tania's feedback and the prior sign spans. Verify token identity against TF
   0.2.8, the version matching the current automatic directory. Review the small
   structural diff before linguistic edits.
2. **Create an evidence ledger.** One issue per token/claim, recording reference,
   original text, author/commit, original analysis, expert preference or question,
   source passages, disposition and implementation scope. Distinguish new comments
   from old Tania attributions. Keep discussion proposals explicitly pending.
3. **Adjudicate columns I and II separately.** Consult local DULAT entries,
   forms and attestation-specific citations; Tropper index and actual pages;
   EUPT morphology/commentary; Wyatt, UNP/TCS and other cited sources. Verify
   cited evidence rather than treating existing row comments as proof. Follow
   the source tools and OCR cautions in the review skill. External research is
   a subsequent phase; no new philological source claims were verified in this audit.
4. **Preserve attributed disagreements.** Put Tania's explicit proposed reading
   first, with her name and review provenance; retain independently supported
   conflicting readings below with precise source attribution. Where she only
   rejects or asks, do not invent her preferred analysis. Unsupported agent
   speculation remains in the audit history, not an equal scholarly authority.
   Do not silently add a status column or teach the scorer to count rejected
   hypotheses as accepted alternatives. Decide their representation explicitly.
5. **Discuss notation proposals before adopting them.** Agenda: case versus
   syntactic relations; lengthened imperative `a`; enclitic/suffix composition;
   aleph interpretation; physical signs versus edited reading. Correct the
   already-documented infinitive marker separately. For `gmpn`, explain the
   current editorial rule before considering whether the rule should change.
6. **Make narrowly justified durable fixes.** Structural validation belongs in
   the linter/loaders; isolated readings in reviewed data; finite lexical
   exceptions in configuration; productive rules in parser steps. Audit affected
   reviewed and automatic rows separately, including parallels outside 1.5.
   Update the guide, checklist, review skill and relevant phenomenon skills to
   share the accepted policy, without changing research proposals into rules.
7. **Validate and regenerate.** Add positive, negative and boundary cases for
   parser/linter changes and malformed-reviewed-row tests for structural changes.
   Run focused tests, reconstruction checks and lint comparisons against the
   pre-feedback and pre-fix baselines for their different purposes. Regenerate
   representative automatic tablets with safeguards, inspect intended/unintended
   changes, then regenerate the justified wider scope and reports. Never patch
   generated files. Run agreement scoring only against structurally valid,
   adjudicated alternatives; it currently treats analyses as a set, so first-row
   preference is not measured by that score.

Completion means every comment has a recorded disposition, no feedback is lost,
source-supported alternatives remain attributed, tentative proposals remain
visible as tentative, and each code change has evidence and bounded validation.
