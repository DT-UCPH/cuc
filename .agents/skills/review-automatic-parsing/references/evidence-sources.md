# Evidence sources for a review pass, and what each one can settle

No source here is sufficient alone, and they are not interchangeable. Recording
*which* one settled a row is half the value of the review — see
`comment-conventions.md`.

The worked precedent is `docs/KTU_1.5_agent_review_notes.md` (and
`docs/KTU_1.3_1.4_agent_review_notes.md`), which show these sources being
weighed row by row on the most heavily reviewed tablet in the corpus. Read the
1.5 notes before a first review pass; they are shorter than this file.

## The sources

| source | what it settles | what it cannot settle |
|---|---|---|
| **DULAT** | lexeme, homonym, sense/gloss, attested forms | morphology at a given line; whether a listed sense applies here |
| **Tropper (2012)** | the grammatical rule behind a form, and a reasoned judgment on specific lines across the whole corpus | nothing verbatim — we hold an OCR whose roots and forms are silently corrupt; see `tropper-conventions.md` |
| **Published translations** — UNP, TCS, Wyatt, Gibson | which sense and homonym the line actually uses; phrase-level construal | anything about form; they disagree with each other constantly |
| **EUPT** (Göttingen) | a full per-token analysis — stem, conjugation, person, gender, number, case, state, lemma | anything against Tropper or DULAT: it is largely unpublished draft material and therefore preliminary. Coverage densest in KTU 1.14–1.16 |
| **Legacy expert review** (Ksenia, Elijah, Tania, Alex, Martijn; attribution is tablet-specific—KTU 1.3 is Tania's review) | a human reading of the consonantal text, authoritative on the analysis column where it contradicts the parser | POS/gloss (mostly unfilled); nothing on tablets it does not cover |
| **UDB** | concordance evidence and text-critical readings (`R1 assumes the Broken String: mhmrt`) | lexeme or morphology on its own |
| **KTU / KTU3** | what is actually on the tablet — sign readings, erasures, emendations | anything lexical |
| **Burns (2003)** | a rough lemmatiser (headword, and root in Workbook IX) and an onomastic classification — DN vs PN vs GN vs cultic term | nothing on its own, and it ranks below Tropper and DULAT; it covers cultic vocabulary and onomastica, not every token |

The mix shifts by tablet, for a principled reason rather than by taste. The Baal
Cycle tablets lean on the translations (KTU 1.5 cites UNP 83×, TCS 32×, Wyatt
12×, DULAT 107×); the Kirta tablets lean on EUPT, whose coverage is concentrated
there. Use what actually covers the text in front of you, and cite only what you
read.

### Verified reviewer provenance in the current repository history

This is tablet-specific; never infer it from an author's name alone.

| material | provenance consequence |
|---|---|
| KTU 1.2 reviewed TSV | Alex/agent review seeded from automatic 0.2.7; repository history explicitly says there is no human gold |
| KTU 1.3 | Tania's blank-slate review; omissions are silence, while positive readings are independent evidence |
| KTU 1.6 `origin/review/1.6-Kseniia` | Ksenia used automatic parsing, but the public branch head `248fa29` contains manual work only through V:9; column VI still matches its parser scaffold and is not an independent human review |
| KTU 1.14 legacy TXT | Martijn's independent review; no automatic-deletion inference |
| KTU 2.10–2.13 legacy TXT | Martijn's independent review; Tania's later blank-slate CSVs are separately available on `origin/Elijahs_Tagging` |
| KTU 2.14 legacy TXT | Elijah's auto-based review; Tania's later blank-slate CSV is a separate independent reading |
| KTU 2.15 legacy TXT | Elijah's auto-based review; its exact basis is `6b1017f:auto_parsing/0.2.6/KTU 2.15.tsv`. Tania's later blank-slate CSV at commit `6ac6442` is a separate independent reading |
| KTU 2.16 legacy TXT | Elijah's auto-based review; its exact basis is `6b1017f:auto_parsing/0.2.6/KTU 2.16.tsv`. Tania's later blank-slate CSV at commit `1cdc4c5` is a separate independent reading |
| KTU 2.38 legacy TXT / Elijah CSV | Auto-based review against exact basis `6b1017f:auto_parsing/0.2.6/KTU 2.38.tsv`; Elijah's later upload preserves the same core decisions. Tania's blank-slate revisions culminate at commit `35f0220` and supply independent positive readings, while omissions remain silence |

Recheck branch heads if repository history changes. The public branch heads were
verified on 2026-08-13; do not treat a later unexamined commit as having the same
coverage.

## Precedence when sources disagree

**DULAT and Tropper are the top tier.** Everything else yields to them on a
straight disagreement.

1. **DULAT is the arbiter of lexeme, homonym, and sense.** A gloss that is not
   DULAT's wording for the chosen sense is an invention. When DULAT genuinely
   offers nothing, `?` with a short reason beats a plausible guess — and `Not in
   DULAT` on an alternative row is an accepted, attested note.
2. **Tropper is the arbiter of the grammar.** Use him for why a form must be
   analysed a given way, and for his explicit judgments on named lines. His
   doubts are evidence too: a `(?)` where the parser is confident is a
   correction candidate no other source raises.
3. **EUPT is the richest per-token morphology, but it is preliminary.** It is
   largely unpublished drafts, so where it disagrees with Tropper or DULAT they
   win. Its value is that it is *independent of the parser* and states a full
   analysis for every token, which nothing else does — so it is the best source
   of a second reading, and a poor source of a final one.
4. **Translations break homonym and sense ties, not morphological ones.**
5. **Burns triangulates, especially for onomastics.** Below Tropper and DULAT.
   Useful as a rough lemmatiser and for deciding PN vs DN vs GN vs common noun,
   because his workbooks are organised by exactly that distinction.
6. **The legacy expert wins over the parser on the analysis column.** A `DIFFER`
   between the legacy review and a seeded row is a high-value finding — a human
   read the text and the parser contradicted them. Ksenia, Elijah, and Alex all
   reviewed automatic-parser output, so an automatic alternative demonstrably
   present in their exact historical basis but absent from their retained set is
   not ordinary source silence: it is an explicit rejection. The aligner labels
   this `REJECTED-AUTO`. Remove that option unless DULAT, Tropper, or another
   independent source supports it. Tania worked from a blank slate; her
   omissions, including in KTU 1.3, are ordinary silence rather than rejection.

## Principles that outrank the ranking

**Preserve the range of interpretation.** The ranking decides which reading goes
in the primary row; it does not licence deleting the others. Where two readings
are documented and defensible, both belong in the file as alternative rows —
that is what the corpus is for. This applies to UNP/TCS construal differences,
to an EUPT analysis Tropper does not share, and to the dissenting readings DULAT
itself records.

**DULAT `diff.` notes are place-specific.** Inside an article, DULAT cites an
attestation and then records who reads it differently *there*:

```
ỉ ỉṯt ảṯrt  verily, as DN is present, 1.14 IV 38
            (diff. Del Olmo MLRC 185: "¿dónde?", Hb. ʔy, Akk. ai)
qra ủ nqmd mlk … 1.161:12
            (diff. Tropper UG 202, 426: G-imp. with prothetic ủ-)
```

`sources_lookup.py` extracts these for the queried line only. **Never generalise
one to the lemma** — the note is an opinion about that one place, and carrying
it elsewhere silently invents an attestation.

**Silence is not evidence.** DULAT not citing a line, EUPT not tagging a token,
Burns not covering a word, the legacy file not covering a column — none of these
argues against a reading.

**Agreement between two independent sources against the row is decisive.**

## Getting at each source

### DULAT

Query recipes — senses, attestations by line citation, the `forms` table — are
in `.agents/skills/audit-onomastic-encoding/references/dulat-recipes.md` §1–3.
Do not re-derive them. The structured database is located as `dulat` by
`sources.py` (`CUC_DULAT_DB`); the separate full-text and reverse-reference
database is `dulat_search`, covered below.

The linter's own DULAT-backed checks are the cheapest first pass:

```bash
cd agent && ./.venv/bin/python linter/lint.py "../reviewed/KTU 1.5.tsv"
```

The DB paths default correctly via `project_paths`. Passing `--udb` by hand is
the usual way to break this: the working database is `udb_cache.sqlite`, and
pointing at `udb.sqlite` raises `no such table: concordance`.

Run it under `agent/.venv/bin/python`, which is 3.13. A system `python3` that is
older will fail to import the linter — and the wrappers that call it under
`|| true` will report the crash as zero errors.

### Translations, EUPT, and the DULAT citation index — one call

```bash
python3 <skill-dir>/scripts/sources_lookup.py --ktu 1.14:IV:35
python3 <skill-dir>/scripts/sources_lookup.py --ktu 1.5:I:14 --modules UNP,TCS --grep tear
python3 <skill-dir>/scripts/sources_lookup.py --list
```

This reads two databases that the repo-local caches do not cover:

- **`dulat_search.sqlite`** — `dulat_reverse_refs`, 48,684 rows: which DULAT
  entries are cited *at a given line*, with the reference-specific translation.
  This is the reverse-mention narrowing the labeling guide's §5 step 8 calls for.
- **`modules_cache.sqlite`** — 15 modules. **Line-level**: `EUPT_vocalisation`
  (2,830), `EUPT_translation` (3,236), `EUPT_commentary` (509), and the `CUC`
  text (7,616). **Tablet-level**: UNP, TCS, Smith, Coogan, ANET, DeMoor, Gordon,
  Incantations — whole documents, so `--grep` finds the passage inside one.

EUPT is **four layers, not one**: a vocalised transcription, a German
translation, a philological commentary, and — inside
`EUPT_vocalisation.data_json → words[]` — a **per-token morphology**
(`{form, morph, lemma, homonym}`). Reading only `content_text` throws the
morphology away. `sources_lookup.py` prints it:

```
form                 morph                    lemma      hom.
yinnagiḥāni          N-PKL 3.m.Du.            ngḥ
ka                   Präp.                    k          IV
ruˀumêma             Gen.m.Du.                rum
```

That single tag gives stem, conjugation, person, gender and number at once, and
is usually the fastest way to see what EUPT actually reads. `PKL`/`PKK` are the
long and short prefix conjugations, `SK` the suffix conjugation — so `N-PKL`
also settles whether a final `-n` belongs to the long-form ending or is an
enclitic. Mind the `GN` = *Gottesname* trap when reading the same column.

Granularity matters: a line-level module answers "what does EUPT read here";
a tablet-level one gives you the whole translation and you locate the line.
`--list` prints which is which.

EUPT's commentary is the densest single source for a contested token — for
`ṣdynm` at 1.14 IV:35 it lays out three analyses with preferences and argues
against the gentilic reading the parser assigned. It is in German; translate
what you quote (see `comment-conventions.md`).

The UDB concordance and the local DULAT+UDB server workflow are separate, and
documented in `agent/prompts/Morphological_Labeling_Agent_Guide.md` §4.2 (UDB)
and §4.6 (modules and Notarius) — including the `x`-wildcard trick for probing
the concordance with damaged surfaces.

### EUPT

EUPT's token-level morphology lives in `module_records.data_json → words[]` for
`EUPT_vocalisation`. Align it to the corpus with:

```bash
python3 .agents/skills/audit-onomastic-encoding/scripts/eupt_align.py 1.14 IV,V,VI
# set CUC_MODULES_DB only if the database is not found automatically
```

**Precondition:** the aligner needs a modules database that carries the EUPT
layer. Some older caches do not, and the script says so and exits; `sources.py`
prefers a copy that has it, so setting `CUC_MODULES_DB` is only needed when your
layout differs. If no such copy is available, review with the sources you do
have — and say so in the comments rather than citing EUPT you did not read.

**Read the tag mapping before interpreting output.** EUPT `GN` is *Gottesname*,
i.e. our `DN`, not our `GN`; mapping it straight through converts every deity
into a place name. The full table, plus the "bare case tag is not a denial of
proper-noun status" rule and the ±1 line-numbering offset, are in
`dulat-recipes.md` §"EUPT carries its own token-level morphology".

### Tropper (2012)

```bash
python3 <skill-dir>/scripts/tropper_index.py build          # once, and after each re-OCR
python3 <skill-dir>/scripts/tropper_index.py lookup --ktu 1.14:IV
python3 <skill-dir>/scripts/tropper_index.py lookup --term Energikus
```

The KTU register validates at 99.6% against our own corpus, so "which pages
discuss this line" is trustworthy. The text on those pages is not: roots and
forms are silently corrupt at ≥4.9%, and his transliteration differs from ours.
`references/tropper-conventions.md` has the measurements, the notation mapping,
and the citation format — read it before quoting him.

### Legacy expert review

```bash
python3 <skill-dir>/scripts/legacy_align.py 1.14 --columns IV,V,VI --seeded-only
```

Aligns by `# KTU <tablet> <col>:<line>` marker and surface sequence, **not by
token id** — the legacy ids are from an older Text-Fabric id space. An earlier
id-based certification attempt was reverted for exactly this reason; do not
resurrect it.

Verdicts: `AGREE`, `AGREE~` (equal once homonym tags are ignored — the legacy
file is simply less specific), `REJECTED-AUTO` (the legacy retained set is a
proper subset of the exact historical automatic basis), `CURRENT-EXTRA` (the
same set relation where the comparison cannot establish that provenance),
`DIFFER`, and `SPLIT/JOIN` (the two tokenizations disagree about word boundaries;
these are the candidates for `MERGE WITH` rows). A trailing `~` on either extra
verdict means the relation becomes visible after homonym tags are ignored.

The current seeder retains one automatic candidate per token, so the ordinary
comparison cannot reconstruct candidates deleted during the original human
review. Use `--automatic-basis-ref <git-ref>` and, for versioned output,
`--automatic-basis-path <path>` to compare the human review against the exact
automatic TSV Ksenia, Elijah, or Alex edited. `--current-as-review` is valid only
when that provenance is independently established. Tania's blank-slate review
cannot establish rejected automatic alternatives. Do not compare against a newer
parser version: an option added later was never available for the reviewer to
reject.

Two cautions the script prints for you:

- **Check the coverage line.** `reviewed/KTU 1.5.txt` covers 25% of its tablet;
  88% agreement over that slice says nothing about the other 75%.
- **`reviewed/orig/*.txt` cannot be used.** Those are bare id dumps with no line
  markers and an even older id space. The script detects this and says so.

### Burns (2003)

Duncan Coe Burns, *Contents, texts and contexts: a contextualist approach to the
Ugaritic texts and their cultic vocabulary*, PhD thesis, University of Sheffield,
2003 — <https://etheses.whiterose.ac.uk/id/eprint/15038/>. Nine workbooks,
converted to 45 CSVs (13,857 rows): Divine Names, Personal Names, Geographical
Names, Cultic Jargon, Commodities, Locations, Times and Events, Personnel, and
Actions.

`sources_lookup.py --ktu …` reports his rows for that line automatically. Two
things it gives that no other source does as directly:

- **A lemmatiser of sorts.** Workbook IX groups every attested form under its
  root, so `yadm` at 1.14 III:52 comes back as root `adm†` — useful when DULAT
  form lookup fails on an unresolved verb.
- **An onomastic classification.** The workbook a headword sits in *is* the
  DN/PN/GN judgment, which is exactly the distinction the parser most often gets
  wrong. `ṣrm` at 1.14 IV:35 is filed under Geographical Names.

Triangulation only, and **below Tropper and DULAT**. Never promote a reading on
Burns alone; his categories follow his own cultic-contextualist argument, not a
lexicographic one.

**Licence: CC BY-NC-ND 2.5.** The converted CSVs are local-only and not
redistributable. Cite him in a comment; do not copy his material into the repo.

Located via `$CUC_BURNS_WORKBOOKS` or a `context_labeling` checkout beside the
repository; the `output/` subdirectory is found automatically.

## Locating the sources

No script or document here names a machine-specific path. `scripts/sources.py`
resolves every source the same way: an explicit argument, then a `CUC_*`
environment variable, then `agent/project_paths.py` (so the repo's own layout
and variables keep working), then a sibling checkout found by walking up from
the repository root.

| variable | source |
|---|---|
| `CUC_DULAT_DB` | structured DULAT — entries, senses, forms, attestations |
| `CUC_DULAT_SEARCH_DB` | DULAT full-text and `dulat_reverse_refs` |
| `CUC_UDB_DB` | UDB concordance |
| `CUC_MODULES_DB` | translations, commentaries, EUPT layers |
| `CUC_TROPPER_OCR` | Tropper OCR directory or `.ocr.txt` |
| `CUC_BURNS_WORKBOOKS` | Burns cultic-vocabulary workbooks |

Set one only when your layout differs; co-located checkouts need no
configuration. Resolution is **content-aware for the modules database**: a copy
without the EUPT layer loses to one that has it, so an older repo-local cache
cannot silently shadow a complete sibling copy. If these databases become
standard for the pipeline rather than for this skill, promote them into
`agent/project_paths.py`, where the `CUC_*` convention lives.

## The circularity trap

The reviewed corpus was largely built *from* DULAT and then corrected. So:

- DULAT agreeing with an existing row is weak evidence — it may be the row's own
  ancestor.
- The parser agreeing with an existing row is *no* evidence — the row was seeded
  from the parser.
- A translation, EUPT, or the legacy expert agreeing is real evidence, because
  none of them was in the generation path.

This is why a review pass that only re-checks rows against DULAT will confirm
almost everything and find almost nothing.
