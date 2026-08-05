---
name: review-automatic-parsing
description: Turn automatic parsing output into hand-reviewed data for a Ugaritic tablet column, adjudicating each token against DULAT and Tropper's grammar first, then the published translations, EUPT, Burns's cultic-vocabulary workbooks and the legacy expert review, and recording contested readings as alternative rows. Use to review or finish a reviewed tablet, to seed and work through a new column, or to check what is still unreviewed. Do not use to regenerate automatic parsing, to migrate reviewed files to a new tokenization, or to audit a single phenomenon corpus-wide.
---

# Review Automatic Parsing

The review pass is what converts parser output into gold data. It is the only
step that touches `reviewed/**` token by token, and it is bounded by a column,
not a tablet — a column is roughly 150–270 tokens, which is one working unit.

This skill covers the *workflow*. It does not restate the notation: column
semantics, reconstruction markers, stem marking, clitics and the DULAT lookup
order live in `agent/prompts/Morphological_Labeling_Agent_Guide.md`, with the
condensed form in `Morphological_Labeling_Quick_Checklist.md`. Read the guide's
§3 (symbols) and §5 (procedure) before the first token, and keep the checklist
open. `agent/prompts/Tagging conventions.md` is authoritative on notation where
either disagrees with this skill.

**KTU 1.5 is the precedent tablet** — the most heavily reviewed in the corpus,
with a granular human pass and then a full six-column re-review. Where a newer
tablet does something else, follow 1.5. `docs/KTU_1.5_agent_review_notes.md` is
the worked example of a review pass and is worth reading first.

## Establish Scope

1. Decide whether the request is a review, an audit, or both. Do not edit for an
   audit-only request.
2. `reviewed/**` is hand-curated — edit it directly. `auto_parsing/**` is
   generated: never hand-edit it. If the parser is wrong, fix the pipeline step
   and regenerate (`CLAUDE.md`, and the regenerate-automatic-parsing skill).
3. Establish what is outstanding before touching anything, with
   `review_status.py` below.
4. Name the column you are reviewing and stay in it. Reviewing two columns in
   one commit makes the diff unreadable and the lint delta unattributable.

```bash
python3 <skill-dir>/scripts/review_status.py 1.14
```

Columns flagged `<-` have rows still marked `SEEDED from auto-parse`, or `?` on
a legible surface with no explanation. Both are unfinished work.

## Seed the Column, If Needed

Only when the reviewed file does not yet cover the column:

```bash
cd agent && ./.venv/bin/python scripts/seed_reviewed_column_range.py 1.14 IV --dry-run
```

It appends auto-parse rows in the current 8-column reviewed layout, marks every
one `SEEDED from auto-parse; not yet hand-reviewed.`, and never rewrites rows
already present. Drop `--dry-run` to write. Seeding is not reviewing: a seeded
column is a worklist, and the marker is what says so.

## Build the Worklist

Four passes over the column, cheapest first. Each produces rows to adjudicate;
none of them decides anything. **Run all of them.** Skipping the grammar or the
translations because the first two passes already agree is how a reading ends up
resting on one source without anyone noticing.

```bash
# 1. The parser against the human who read the tablet.
python3 <skill-dir>/scripts/legacy_align.py 1.14 --columns IV --seeded-only

# 2. The parser against an independent morphology.
python3 .agents/skills/audit-onomastic-encoding/scripts/eupt_align.py 1.14 IV

# 3. What the reference grammar says about these very lines.
python3 <skill-dir>/scripts/tropper_index.py lookup --ktu 1.14:IV

# 4. The linter's own DULAT-backed checks.
cd agent && ./.venv/bin/python linter/lint.py "../reviewed/KTU 1.14.tsv"
```

Then, per contested token, everything the sources say about its line:

```bash
python3 <skill-dir>/scripts/sources_lookup.py --ktu 1.14:IV:35
```

In one call: DULAT's citations at that line and any dissenting readings it
records there under `diff.`; all four EUPT layers — vocalisation, German
translation, philological commentary, and the **per-token morphology** from
`data_json → words[]`; the published translations of the tablet; and Burns's
headword, root and onomastic category.

The morphology line is usually the quickest read in the whole output: a tag like
`N-PKL 3.m.Du.` states stem, conjugation, person, gender and number together.
Use `eupt_align.py` to scan a whole column for disagreements; use this when you
have one token in front of you.

`legacy_align.py` aligns on line reference and surface, **not token id** — the
legacy ids are from an older Text-Fabric id space. Its `DIFFER` rows on seeded
tokens are the highest-value findings in the column: a human read the text and
the parser contradicted them. Its `SPLIT/JOIN` rows are candidates for `MERGE
WITH` pairs.

`tropper_index.py` returns the printed pages where the reference grammar treats
each line of the column, with the PDF page beside it. Run `build` once (and
again after any new OCR run) before the first `lookup`. Read
`references/tropper-conventions.md` before using a single word of it: the OCR
corrupts roots and forms silently, and Tropper's transliteration is not ours.

Read `references/evidence-sources.md` before interpreting any of this — the
EUPT `GN` = *Gottesname* trap, why DULAT agreement with an existing row is
partly circular evidence, and the `CUC_*` variables that locate each source.
Nothing here hardcodes a path: co-located checkouts are found automatically,
and the modules database is chosen by content, so a cache without the EUPT
layer cannot shadow a complete one.

## Review Each Token

Work down the column in order, not by defect class — a column reads as
connected text, and the parallels within it are the best evidence available.

For each token:

1. Read the line as a clause first. Most corrections in practice are case,
   state, and person errors that only a clause-level reading exposes.
2. Take the analysis from the guide's §5 procedure; take lexeme, homonym and
   sense from DULAT; consult Tropper on the grammatical question the row raises,
   quoting his prose only after reading the page. **DULAT and Tropper are the
   top tier**: EUPT is a full per-token analysis but preliminary draft material,
   and Burns triangulates — both yield where either of the top two disagrees.
   Burns is the quickest check on PN vs DN vs GN, and on the root of a verb
   DULAT form lookup cannot resolve.
3. Reconcile the worklist findings for that row. Where sources conflict, follow
   the precedence in `references/evidence-sources.md` — and record the conflict.
   **Re-derive the analysis from the lexeme; never patch the existing string.**
   Changing a stem marker or an ending while inheriting the rest of a row's
   spelling is how an unmarked radical survives a review: the row keeps a
   consonant its own column 4 does not have. After any edit, read the analysis
   against column 4 letter by letter — every letter of the lexeme must be present
   or reconstructed with `(`, and every written letter absent from the lexeme
   marked with `&`.
4. Check the parallels. Formulaic repetition is dense in these texts; a reading
   settled at one attestation should be applied to the others in the column, and
   a reading that cannot be applied to them is probably wrong.
5. Where two sourced readings are both defensible, record both as alternative
   rows rather than picking. On KTU 1.5 this is the primary device — 94 ids
   carry more than one row. Preserving the interpretative range is a goal, not a
   concession: it covers UNP/TCS construal differences, an EUPT reading Tropper
   does not share, and DULAT's own `diff.` dissents — which attach to their one
   attestation and must never be generalised to the lemma.
6. Clear the seed marker, and comment only where there is something to record.
   The comment column is read by **users of the published corpus**, who know the
   literature and the text and nothing about our parser, passes or token ids.
   Never begin a comment with `#`; put anything addressed to us — source defects,
   pipeline bugs, notation gaps — after a `##` at the end, where it can be
   stripped automatically. See `references/comment-conventions.md`. Most reviewed
   rows on 1.5 carry no comment at all, so do not invent one to fill the space;
   every `?` on a legible surface does need its reason.

Escalate rather than improvise:

- A phenomenon that recurs across the column (Gt stems, N stems, feminine
  endings, passive participles, onomastics, reconstruction) has its own audit
  skill. Use it for that class instead of deciding case by case.
- A finding that is a general rule rather than a local reading belongs to the
  review-linguistic-rule-change skill, which measures every affected row before
  anything changes.
- A parser defect is a pipeline fix plus a test plus a regeneration, never a
  hand-edit of `auto_parsing/**`.

## Verify

```bash
python3 <skill-dir>/scripts/review_status.py 1.14          # column must be clean

PYTHON="$PWD/agent/.venv/bin/python" \
  bash .agents/skills/audit-onomastic-encoding/scripts/lint_diff.sh HEAD "KTU 1.14.tsv"
```

The column is done when `review_status.py` reports 0 seeded and 0
`?undocumented` for it.

**Pass `PYTHON=` explicitly.** `lint_diff.sh` defaults to whatever `python3` is
on `PATH`, the linter needs 3.13, and the script runs it under `|| true` — so a
too-old interpreter produces `baseline: 0 errors / current: 0 errors` and an
empty regression list. A lint diff that reports zero on *both* sides is the
signature of a linter that never ran; check it against a direct
`./.venv/bin/python linter/lint.py` count before believing it.

For the lint delta, compare **ERROR counts against a baseline**, not raw totals:
`INFO` churn and changed "choose one of: …" hints are expected. **The linter only
drops the reviewed `sign span` column when the file's parent directory is
literally named `reviewed`** — copying a TSV into a scratch directory with any
other name silently shifts every column by one and invalidates the run.
`lint_diff.sh` nests the directory correctly; hand-rolled comparisons usually do
not.

A residual ERROR is not automatically a data defect. Where a reviewed encoding is
defended in its comment and the linter still objects, the linter rule is the
thing to fix — with a test — not the row. Do not silence a rule you have not
understood, and do not leave the disagreement undocumented in either direction.

## Report

Per column: tokens reviewed, rows changed, rows left `?` and why, alternative
rows added, and the lint delta as `before → after` ERROR counts. List the
adjudicated `DIFFER` rows with the evidence that settled each, and the rejected
candidates with the reason — a documented rejection stops the next pass
re-opening the same question.

Commit one column per commit, `review: verify KTU <tablet> column <N>`, touching
only that reviewed file. Pipeline, linter, and lexicon changes are separate
commits: they alter generated output and must be able to move independently of
the review.
