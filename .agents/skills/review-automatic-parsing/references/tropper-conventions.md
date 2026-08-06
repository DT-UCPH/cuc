# Tropper (2012) — what the OCR can be trusted for, and how to cite it

Josef Tropper, *Ugaritische Grammatik*, 2nd ed. (AOAT 273), 2012 — the standard
reference grammar. We hold an OCR of it, not the text itself, so what follows is
about a scan with measurable error, not about the grammar.

He is a **fourth independent witness**, alongside DULAT, the translations, EUPT
and the legacy expert review. Unlike EUPT he covers the whole corpus.

## Pointing the tools at it

```bash
python3 <skill-dir>/scripts/tropper_index.py build
python3 <skill-dir>/scripts/tropper_index.py lookup --ktu 1.14:IV:35
python3 <skill-dir>/scripts/tropper_index.py lookup --term Energikus
python3 <skill-dir>/scripts/tropper_index.py lookup --page 497
```

Source resolution goes through `scripts/sources.py`: `--ocr`, else
`$CUC_TROPPER_OCR`, else a `ugaritic_ocr/` checkout found beside the repository
or any of its parents (so a git worktree works too). No path is hardcoded. The
index is written next to the OCR, not into this repo — it is a derived artefact
of a file we do not own.

**After a new OCR run, rerun `build`.** Nothing is hand-corrected, so a rebuild
is always safe, and the quality report is the measurement of whether the model
improved. `lookup` warns when the OCR file no longer matches the built index.

## Reliability is not uniform — it tracks how numeric the content is

Measured against our own corpus and DULAT, on the 2026-08 OCR:

| part of the book | quality | basis |
|---|---|---|
| KTU passage register | **99.6 % verified** | 4,329 of 4,345 refs exist in `auto_parsing` |
| subject register (Sachregister) | clean | German + page numbers only |
| German prose | readable, content intact | rules come through usable |
| forms in running discussion | mostly sound | 9 of 11 spot-checked forms verified |
| root register | **weak** | `√` marker correct on only 163 of 702 rows |
| `√`-roots in running text | **≥ 4.9 % corrupt** | floor; 47 % of spellings occur once |
| morphological templates | corrupt | `{yiqtatYl}` for `{yiqtatVl}` |
| syllabic cuneiform citations | wrecked | `vr"DINGIR-iš-tam-i` |

The pattern is principled: digits survive, diacritics do not. The KTU register is
almost pure numerals; the root register is nothing else.

**The dangerous failures are silent.** The model was fine-tuned on Ugaritic and
hallucinates diacritics onto anything: `Ḫerausgeber` for *Herausgeber*, `Ṣ 2012`
for *© 2012*, Syriac `netqʿṭel` for `netqṭel`. In roots it produces
`ʾbd` → `ʿbd` ("perish" → "serve"), `ʾḫd` → `ʾḥd` ("seize" → "one"),
`ytn` → `yṯn`. **Both outputs are real words**, so nothing downstream flags them.

Hence the standing rule:

> Prose may be paraphrased from the OCR. Every **form, root, and template** must
> be checked against the scan before it enters a skill, a comment, or a parse.

`lookup --page N` prints the `pdftotext` command for the right PDF page. The
page anchor is probed at build time, not assumed (currently `printed = pdf − 22`).

## His transliteration is not ours

This would cause silent errors even with a perfect scan. Same class of trap as
EUPT `GN` = *Gottesname*.

| | Tropper | CUC / DULAT |
|---|---|---|
| aleph | `ʾa ʾi ʾu` | `a i u` |
| ayin | `ʿ` | `ˤ` (CUC), `ʕ` (DULAT roots) |
| root citation | `√wṯb`, `√wtn`, `√wld` (original I-w) | `/y-ṯ-b/`, `/y-t-n/`, `/y-l-d/` |
| what is cited | reconstructions (`raʾš`) beside attested forms (`riš`) | attested surface only |

So `√wtn` and `/y-t-n/` are the same root, and Tropper's `ʾalp` is our `alp`.
Never map his spelling into a parse without applying this table.

## Citing him in a parse

Reviewed comments are in English and the grammar is in German, so **every German
quotation gets an English translation in parentheses.** Cite the § where he
gives one, otherwise the printed page.

```
Tropper §74.232 "Der Gt-Stamm zeichnet sich durch die Infigierung eines
Morphems -t- nach dem ersten Wurzelradikal aus" ("the Gt stem is characterised
by the infixing of a morpheme -t- after the first root radical").
```

```
Tropper p. 364 "gemeint ist ein Marschieren in Zweier- bzw. Dreierformation"
("what is meant is marching in formations of two or three").
```

```
Tropper p. 364: "Die Deutung von rbt als Singular ist weniger wahrscheinlich"
("the interpretation of rbt as a singular is less likely") — supports the
numeral reading over rb (I) + suffix.
```

Do not paste untranslated German into a comment, and do not quote a form from
the OCR inside such a citation without having seen it on the page.

## What he is good for, concretely

Looking up KTU 1.14 IV — a column still seeded — returns 70 indexed references.
Among them:

- **IV:35/38 `ṣdynm`** — the parser labels it `TN pl. abs. gen.` outright;
  Tropper gives `/ṣīd(i)yānîma/?` "Bewohner von Sidon"(?) ("inhabitants of
  Sidon"), with two question marks, and prefers an ONN reading at IV:36/39.
  Neither DULAT nor EUPT surfaces that doubt.
- **IV:18 `rbt`** — he argues against the singular reading, corroborating the
  reviewer's numeral analysis.
- **IV:51 `ḥṭb`** — he reads `ḥṭb <ṭ>`, an emendation, cross-referenced to DUL 377.

## Reading the index's own flags

- `[unverified against corpus]` — the reference does not match a line we hold.
  Either Tropper cites a reading we do not have, or the OCR mangled it. Check
  the page before using it.
- `[page list suspect]` — the page numbers do not ascend, which they always do
  in the printed register. At least one is an OCR digit error.
- The **root register is unflagged but unreliable as a whole**; `lookup --root`
  says so on every call. Treat a hit as "look at these pages", never as evidence
  that the root is spelled that way.
