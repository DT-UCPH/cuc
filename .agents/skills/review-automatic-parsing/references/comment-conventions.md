# Recording a reading: alternative rows first, comments second

## Who reads the comment column

**A user of the published corpus.** They know the literature, the linguistics
and the text. They know nothing about the parser, its versions, our editing
stages, our token ids, the linter, or which pass produced a row — and none of
that belongs in front of them.

Write in their vocabulary: lexica, editions, translations, grammatical
description, parallels, text-critical observations. Nothing about how the file
was made.

Two hard rules:

- **Never begin a comment with `#`.**
- **Put anything addressed to us after a `##`, at the end of the comment**, so it
  can be stripped from the published corpus automatically.

Everything before the `##` is published. Everything after it is ours.

### What earns a `##`

Genuine red flags a developer or researcher must look at:

- a systematic problem in a source — a lexicon's structured fields disagreeing
  with its own article text, an edition's coverage gap, entries from different
  works merged indistinguishably;
- a parsing or pipeline defect the row exposes;
- a linguistic phenomenon the notation cannot currently express;
- a bug, or an inconsistency in the corpus's own conventions.

```
… EUPT reads yinnagiḥāni, N-PKL 3.m.Du. ## The dual ending -āni is written [n
here, while tmṭrn and tmġyn encode the same ending as ~n; the corpus needs one
convention.
```

Not for `##`: ordinary uncertainty, a reading you merely find unpersuasive, or a
note that you checked something. If it is only interesting to whoever edited the
row, it belongs nowhere.

## How much to write

The conventions below are read off **KTU 1.5**, the most heavily reviewed tablet
in the corpus — 56 commits, a granular human pass column by column, then a full
six-column line-by-line re-review. Where a newer tablet does something else,
1.5 is the precedent.

The single most important thing 1.5 shows: **most reviewed rows carry no comment
at all** (~37% are commented). Ambiguity is recorded structurally, in alternative
rows, not in prose. Reach for a comment when there is something a later reader
could not reconstruct from the columns themselves.

## Alternative rows are the primary device

94 token ids in 1.5 carry more than one row — the highest density in the corpus.
This is the normal way to record a contested reading, not a last resort.

Repeat the id, surface, and sign span verbatim; vary columns 4–8. The first row
is the primary reading. Each further row says, briefly, where it comes from:

```
158592  šlyṭ  šlyṭ/          n. m. sg. abs. acc.            tyrant       šlyṭ d šbˤt rašm 'the tyrant of seven heads' (// 1.3 III:42).
158592  šlyṭ  ]š]l(w&yṭ[/    vb Š act. ptcpl. m. sg. …      to enwrap    Not in DULAT
158592  šlyṭ  ]š]lyṭ[/       vb Š act. ptcpl. m. sg. …      to enwrap    Not in DULAT
158592  šlyṭ  ]š]lyṭ[/       vb Š pass. ptcpl. m. sg. …     to be cursed Not in DULAT
158592  šlyṭ  šlyṭ/          DN m. abs. acc.                Šaliyaṭu     Not in DULAT
```

A short conditional note carries the condition and nothing else. Older rows
wrote it with a leading `#`; that is retired, since the column must never begin
with `#`:

```
158596  tṯkḥ  !t!ṯkḥ[:w   vb G prefc. 3 m. pl.   to burn
158596  tṯkḥ  !t!ṯkḥ[     vb G prefc. 3 m. du.   to burn   if šmm is dual
```

Do not use alternative rows to dodge adjudication — one source's silence is not
a second reading — but do not collapse a genuine, sourced disagreement into a
single row either. **Preserving the range of interpretation is a goal of the
corpus, not a concession.** A UNP/TCS construal difference, an EUPT analysis
Tropper does not share, and a reading DULAT records under `diff.` all belong in
the file, with the better-attested one first and each attributed.

A `diff.` reading is scoped to its attestation. Cite it on the row it belongs to
and nowhere else:

```
DULAT records a dissent here: diff. Del Olmo MLRC 185 "¿dónde?" ("where?"),
comparing Hb. ʔy, Akk. ai — 1.14 IV:38 only.
```

## When a comment earns its place

**Competing published readings.** 1.5 records the debate rather than hiding the
losing side:

```
UNP: 'but let me tear you to pieces', Gibson: 'with a breaking in pieces', TCS:
'like the folds (?)', noun or verbal noun? Tania: cf. Hebrew רסיסים, Amos 6:11
(not in HALOT).
UNP: y{.}ṣḥn 'invite me'; DULAT reads ylḥn 'how could he provide moisture?' (/l-ḥ(-ḥ)/).
bt ḫpṯt 'house of ḫpṯt' = the underworld; UNP 'House of Freedom'; DULAT '?'.
```

**The phrase the token sits in**, when the analysis alone does not show it:

```
DULAT cites ḏd (III) here: 'the spring (which), in truth, the herd (of hinds seeks)'.
ap lb 'front of the chest' (UNP: 'he plows his chest like a garden'); DULAT ảp (II) sense 4.
```

**Grammatical authority**, when the row turns on a rule rather than a lexeme.
Reviewed comments are in English and Tropper is in German, so **every German
quotation carries an English translation in parentheses**:

```
Tropper p. 364 "Die Deutung von rbt als Singular ist weniger wahrscheinlich"
("the interpretation of rbt as a singular is less likely") — supports the
numeral reading over rb (I) + 2 m. pl. suffix.
Tropper §74.232 "Infigierung eines Morphems -t- nach dem ersten Wurzelradikal"
("infixing of a morpheme -t- after the first root radical").
```

Cite the § where he gives one, otherwise the printed page. Never paste
untranslated German, and never quote a form or root out of the OCR without
having read it on the scan — see `tropper-conventions.md`.

**Text-critical observations** — scribal errors, emendations, editions
disagreeing about the signs:

```
Scribal anticipation of k(ḥrr) rewritten in full at the start of the next line (cf. I:2 š).
DULAT reads ảl ảšt (s.v. /š-t/); ṯ unexplained (scribal error?). KTU: ašṯt.
DULAT dbr (II) (par. šḥlmmt), emended b <arṣ> dbr; UNP 'outback', TCS 'pasture land'.
KTU3: written above a sign probably representing a Hurrian phoneme (ṯ?) of ln. 27.
```

**Parallels**, which carry real weight in formulaic text:

```
It is aliy in II:11
Or beginning of a broken word (cf. k kbkb[m] III:8); divider before k rules out suffix -k.
```

## Unresolved rows

`?` on a broken or empty surface needs nothing. `?` on a **legible** surface is a
claim that a readable word cannot be analysed, and 1.5 gives the reason — often
in three or four words:

```
erased sign
DULAT, UDB: not found. UNP: štm, UDB: štm̊.
DULAT-only fallback; legacy reviewed alternatives retained below.
UNP restores: [lḥm.ˤm.aḫy.(?)a]p.mlḥmy/[wštm.ˤm.aryy.yny (?)]
```

`review_status.py` reports the ones missing a reason as `?undocumented`. Add the
note — do not manufacture an analysis to clear the count.

## Separating lexemes: `|`, never `,` or `;`

When one token carries two lexemes, the structured columns separate them with
` | `:

```
160692  bn amt   bn(I)/ am(t(I)/t   bn (I) | ảmt (I)
                 n. m. sg. cstr. gen. | n. f. sg. abs. gen.
                 son | female slave
```

**Neither punctuation mark is available to us**, because DULAT uses both inside
a single gloss: a **comma between synonyms** and a **semicolon between
non-synonyms**. `ḏd (III)` is glossed `flock, herd` and `hn` is glossed
`behold!; look!; thus` — one gloss each. Delimiting with either would make a
two-lexeme row unreadable, and reading either as a delimiter silently splits a
DULAT gloss into senses it does not have.

So on a two-lexeme row the gloss reads `yes | flock, herd`: one pipe, and the
comma stays DULAT's.

The analysis column separates its lexemes with a space (`k(I) r(ks/`), which is
unambiguous there because no analysis contains one.

`split_csv_field` in the linter splits on `|`, falling back to `,` for rows
written before the convention, and the packed-variant check no longer reads a
semicolon in the gloss column as a delimiter.

## Segment separator

Appended segments are joined with ` | `, which is also how machine-added
provenance arrives:

```
bn ilm mt: il + encl. -m (sg. 'El/god'); EUPT reads sg. il + EP -m. | Migrated
from legacy reviewed tokenization.
It is aliy in II:11 | DULAT: NOT FOUND | Migrated from legacy reviewed tokenization.
```

Preserve those trailing segments when you edit a row — re-deriving them later is
not possible — but they record our editing history rather than the text, so they
belong **after the `##`**, not in front of the corpus user:

```
It is aliy in II:11 ## DULAT: NOT FOUND; Migrated from legacy reviewed tokenization.
```

Note that the ` | ` in those legacy segments is the old provenance separator,
not the lexeme separator: they occupy different columns and never meet.

## MERGE rows

When the Text-Fabric token boundary cuts across a lexical word, both rows carry
the **same whole-word analysis** and the comments pair up. In 1.5 both sides may
carry rationale, and the source is cited:

```
MERGE WITH THE NEXT: mh+mrt = mhmrt (UDB: 'R1 assumes the Broken String:
mhmrt.'); DULAT mhmrt (cf. hmrt 'drain, sink').
MERGE WITH THE PREVIOUS: b y|rdm arṣ 'among those who go down into the earth' (TCS).
MERGE WITH THE NEXT: sbn+[y] = sbny, split across lines VI:3/4; TCS: 'We have
done the rounds of…'.
```

The linter validates the pairing — `MERGE WITH THE NEXT` without a matching
`MERGE WITH THE PREVIOUS` is an error — and exempts these rows from the `merge`
TODO-marker warning. `legacy_align.py`'s `SPLIT/JOIN` findings are where to look
for candidates. Log the case in `docs/tf-0.2.8-tokenizer-problems.tsv` too; that
file is the upstream report.

## The seed marker

`seed_reviewed_column_range.py` writes exactly:

```
SEEDED from auto-parse; not yet hand-reviewed.
```

**Clear it on every row you examine** — that is what "reviewed" means. But clear
it to *empty* when the row has nothing to record; do not invent a confirmation
string to fill the space. 1.5 has no such convention, and a column of identical
"reviewed and retained" comments is noise that makes the real notes harder to
find.

This does mean the marker's removal is the only per-row record that someone
looked. That is why it must never be cleared in bulk, and why the commit — one
column per commit — is the audit trail. `review_status.py` counts what is left.

The linter will not catch a stale marker: `todo_markers_in_comment` matches only
`merge`, `???`, `todo`, `fix`, `repair`.

## What not to write

- **Anything the corpus already encodes.** Restoration and damage state live in
  the Text-Fabric features and the sign span. Comments duplicating them were
  deliberately stripped once and should not come back.
- **Provenance for its own sake.** "DULAT direct ref" on an unambiguous row adds
  nothing.
- **Anything naming our machinery** — parser versions, seeding, token ids of our
  own rows, linter messages, lint counts, database column names, or which pass
  looked at the row. Explain a residual linter complaint in terms of the
  *evidence* ("DULAT lists only a G for this root and does not cite this line"),
  never by quoting the tool.
- **Markers the linter treats as unfinished work** — `todo`, `fix`, `repair`,
  `???`, or a bare `merge` outside a `MERGE WITH` annotation. Resolve them
  before committing rather than shipping the marker.
