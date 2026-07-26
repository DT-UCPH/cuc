---
name: audit-onomastic-encoding
description: Audit and correct Ugaritic divine/personal/place-name (DN, PN, GN, TN) encodings in reviewed or automatic TSV files, and reconcile them against DULAT senses and external semantic catalogues such as the Burns cultic-vocabulary workbooks. Use when a deity reading is recorded only in the gloss and not the POS, when a gloss contradicts its own lexeme homonym or row comment, when an onomastic POS trips the linter's allowlist, or when an outside source claims a name reading the corpus does not. Do not promote a token to DN/PN/GN from a translation, an epithet, or a semantic catalogue alone.
---

# Audit Onomastic Encoding

Onomastic status in this corpus lives in **two independent columns** — the POS
(`DN m. sg. abs. nom.`) and the gloss (`2) DN`, `Yammu`) — plus the DULAT lexeme
homonym in column 4. They drift apart silently: nothing forces `ym (II)` glossed
`2) DN` to also carry a `DN` POS. This skill finds and closes those gaps.

## Establish Scope and Authority

1. Decide whether the request is an audit, an edit, or both. Do not edit for an
   audit-only request.
2. `lexicon_and_grammar/tagging_conventions_cuc.md` is authoritative when it
   differs from this skill.
3. `reviewed/**` is hand-curated — edit it directly. `auto_parsing/**` is
   generated: never hand-edit it; fix the pipeline step and regenerate
   (see `CLAUDE.md`).
4. DULAT is the arbiter of lexeme, homonym, and sense. A translation, an
   epithet, or a semantic catalogue is evidence, never a decision on its own.

## Run the Audit

```bash
python3 <skill-dir>/scripts/audit_onomastic.py reviewed
```

It reports four classes, each with token ids and locations:

- **gloss-pos-mismatch** — gloss names a deity/person/place but POS is a common
  noun, or the reverse. This is the main defect class.
- **gloss-drift** — the same `lexeme (homonym)` carries different glosses across
  rows with the same POS class. The minority spelling is usually the error.
- **allowlist-gap** — a row declares an onomastic POS for a DULAT lexeme whose
  DULAT `pos` is not onomastic, and the lexeme is absent from
  `agent/data_sources/onomastic_gloss_overrides.tsv`. These *will* fail the
  linter. Fix the override table, not the row.
- **comment-conflict** — the row's own comment argues for a different reading
  than its gloss.

Findings are candidates, not verdicts. Confirm every one against DULAT before
editing.

## Cross-check Against EUPT

DULAT is not the only authority, and reviewed data was largely built *from*
DULAT — so DULAT silence proves nothing and DULAT agreement is partly circular.
EUPT supplies an **independent token-level morphology**: stem, conjugation,
person, gender, number, case, state and lemma, in
`module_records.data_json → words[]` for `EUPT_vocalisation`.

```bash
CUC_MODULES_DB=<path>/modules_cache.sqlite \
  python3 <skill-dir>/scripts/eupt_align.py <tablet> [COL,COL]
```

It aligns EUPT words to corpus rows on the consonantal skeleton and reports
class disagreements. **Read the tag mapping in `references/dulat-recipes.md`
before interpreting output — EUPT `GN` means *Gottesname*, i.e. our `DN`, not our
`GN`.** Agreement between EUPT and DULAT against the corpus is the strongest
signal available; EUPT alone is enough to open a second option.

## Confirm Against DULAT

Read `references/dulat-recipes.md` for the query patterns. The three that matter:

1. **Sense numbers are the gloss vocabulary.** A gloss like `2) DN` means DULAT
   sense 2 of that entry. Check the `senses` table before inventing wording;
   reuse DULAT's own definition text.
2. **Attestations are cited by line.** Query `attestations` filtered on the
   citation (`CAT 1.4 VI:12`) to see whether DULAT reads a name at exactly that
   line. Absence of a citation is not evidence against a reading, but presence
   settles it.
3. **The `forms` table settles paradigm questions.** If DULAT lists the surface
   as an explicit form of an entry (e.g. `ỉlm` as pl. of `ảl (III)` "ram"), that
   entry is licensed even when the surface looks like another lexeme.

## Decide

Promote a token to `DN`/`PN`/`GN`/`TN` only when DULAT assigns the name sense to
that lexeme *and* the context supports it. Specifically:

- **Do not** promote because the gloss transliterates a name. `bʕl (II)` glossed
  `Baʿlu/Baal` inside `zbl bʕl arṣ` is the common noun "lord" — DULAT indexes
  that line under `zbl (I)`. Fix the *gloss*, not the POS.
- **Do not** promote an epithet. `lṭpn`, `aliyn`, `rbm` stay adjectives.
- **Do not** promote from an appellative in a divine context. `ilm` "gods",
  `ġrm` "mountains", `arṣ` "earth" are common nouns even in myth.
- **Do** promote when DULAT's sense for that citation is the name sense, and
  align case with the surrounding construct chain or apposition.

When two readings are both defensible **and documented**, add a second option
row rather than choosing. Repeat id, surface, and sign span verbatim; vary
columns 4–8; cite the source in the comment.

## Verify

Always lint-diff against a baseline. **The linter only drops the reviewed
`sign span` column when the file's parent directory is literally named
`reviewed`** (`file_has_reviewed_sign_span_column` in `agent/linter/lint.py`).
Copying TSVs into a scratch directory with any other name silently shifts every
column by one and invalidates the whole run.

```bash
python3 <skill-dir>/scripts/lint_diff.sh
```

or manually — note the `reviewed/` subdirectory in both trees:

```bash
mkdir -p "$TMP/base/reviewed" "$TMP/cur/reviewed"
```

Then compare `ERROR` counts, not raw totals, and normalise away file paths and
row numbers before diffing. A changed "choose one of: …" hint is not a new
error.

## Report

State for each finding: token id, location, what changed, and the DULAT evidence
by citation. Report rejected candidates too, with the reason — a documented
rejection is as useful as a fix and stops the next pass re-opening it.
