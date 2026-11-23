# CUC 0.4.0

CUC 0.4.0 adds 111 texts to 0.3.0: 21 KTU tablets whose reviews were finished
after 0.3.0, and the first 90 Ras Ibn Hani texts from RIH II. It also takes the
finished reviews of KTU 1.4 and 1.31 in place of their reference versions. The
other 340 tablets of 0.3.0 are unchanged. Earlier TF versions remain available.

| Node type | 0.3.0 | 0.4.0 | Interpretation |
| --- | ---: | ---: | --- |
| `sign` | 165,790 | 174,549 | 173,136 source-backed sign slots and 1,413 invisible synthetic slots in 0.4.0 |
| `word` | 30,842 | 32,602 | Source text units, including gaps and non-lexical content |
| `line` | 8,691 | 9,535 | Retained textual lines |
| `column` | 415 | 531 | Columns, implicit column I and fragment divisions |
| `tablet` | 342 | 453 | 363 KTU tablets and 90 RIH texts; 111 additions |
| `boundary` | 1,166 | 1,409 | 846 scribal rulings and 563 breaks |
| `alias` | 3 | 3 | Catalogue identifiers resolving to existing canonical spans |

There are 219,082 nodes in total. The build applies the same 42 configured
corrections as 0.3.0, recognizes one as already present and leaves none
unmatched; 41 lines carry `erratum`, all in tablets that were already in 0.3.0.

0.4.0 is built on top of the 0.3.0 that restores word `language`, adds
`tablet_language` and applies the KTU Validator recovery (DT-UCPH/cuc#45). Its
340 unchanged tablets are identical to that build.

## Coverage

### KTU tablets added

Only reviews whose work file says the review is finished enter the release.
The KTU tablets below had no version in 0.3.0. KTU 4.42–4.62 come from the
reviews on the converter's `main`; KTU 1.32 and 1.33 are new reviews from the
KTU Validator.

| Newly available tablet | Language (`tablet_language`) | Retained lines | Reviewer source |
| --- | --- | ---: | --- |
| KTU 1.32 | Hurrian | 5 | finished review, 2026-11-07 |
| KTU 1.33 | Hurrian | 3 | finished review, 2026-11-07 |
| KTU 4.42 | Ugaritic | 8 | finished review, 2026-11-09 |
| KTU 4.43 | Ugaritic | 7 | finished review, 2026-11-09 |
| KTU 4.44 | Ugaritic | 32 | finished review, 2026-11-09 |
| KTU 4.45 | Ugaritic | 10 | finished review, 2026-11-09 |
| KTU 4.46 | Ugaritic | 14 | finished review, 2026-11-09 |
| KTU 4.47 | Ugaritic | 10 | finished review, 2026-11-09 |
| KTU 4.48 | Ugaritic | 12 | finished review, 2026-11-09 |
| KTU 4.49 | Ugaritic | 7 | finished review, 2026-11-09 |
| KTU 4.50 | Ugaritic | 17 | finished review, 2026-11-09 |
| KTU 4.51 | Ugaritic | 16 | finished review, 2026-11-16 |
| KTU 4.53 | Ugaritic | 16 | finished review, 2026-11-16 |
| KTU 4.54 | Ugaritic | 13 | finished review, 2026-11-16 |
| KTU 4.55 | Ugaritic | 34 | finished review, 2026-11-16 |
| KTU 4.56 | Ugaritic | 14 | finished review, 2026-11-17 |
| KTU 4.57 | Ugaritic | 11 | finished review, 2026-11-17 |
| KTU 4.58 | Ugaritic | 5 | finished review, 2026-11-17 |
| KTU 4.60 | Ugaritic | 10 | finished review, 2026-11-17 |
| KTU 4.61 | Ugaritic | 7 | finished review, 2026-11-17 |
| KTU 4.62 | Ugaritic | 3 | finished review, 2026-11-17 |


KTU 1.32 and 1.33 are Hurrian: KTU³ says "SR: Hurrian; fragment of the same
tablet as KTU 1.33" (and 1.32). The KTU 4 texts state no language and are
`Ugaritic`.

### RIH texts added

RIH II texts enter only where they convert with no special handling: no
source-lint finding, no open entry in the converter's editorial questions,
and no failed identity, alias or duplicate check. 90 of the 106 RIH II
transcriptions qualify. A RIH text's `tablet` is its KTU number where it has
one (75 texts, KTU 8.31, 8.32 and KTU 9.x) and its RIH number otherwise
(15 texts). No RIH text shares a `tablet` value with a KTU tablet or with
another RIH text, and no RIH text is a catalogue alias.

All 90 come from the RIH II transcriptions, not from the KTU Validator: the
RIH reviews in the validator are not used in this release.

| RIH II no. | RIH text | KTU no. | Retained lines | Breaks / rulings |
| ---: | --- | --- | ---: | --- |
| 3 | RIH 84/20 | KTU 9.495 | 3 | 1 / 1 |
| 5 | RIH 84/12 | KTU 9.493 | 9 | 0 / 5 |
| 8 | RIH 83/50 + 83/54 | KTU 9.484 | 53 | 3 / 3 |
| 12 | RIH 80/02 | KTU 9.450 | 26 | 3 / 0 |
| 13 | RIH 79/06 | KTU 9.446 | 7 | 0 / 1 |
| 14 | RIH 83/08 | KTU 9.463 | 33 | 0 / 2 |
| 15 | RIH 83/09 | KTU 9.464 | 10 | 0 / 0 |
| 16 | RIH 83/10 | KTU 9.465 | 9 | 0 / 0 |
| 17 | RIH 83/20C | — | 3 | 1 / 0 |
| 18 | RIH 83/25 + 83/46 | KTU 9.475 | 14 | 0 / 14 |
| 20 | RIH 84/[31,02] | KTU 9.501 | 9 | 0 / 1 |
| 21 | RIH 84/[31,07] | KTU 9.506 | 4 | 1 / 0 |
| 22 | RIH 84/[31,24] | KTU 9.523 | 3 | 1 / 0 |
| 23 | RIH 84/[31,09] | KTU 9.508 | 3 | 1 / 0 |
| 24 | RIH 94/01 | — | 6 | 1 / 1 |
| 26 | RIH 83/42 + 83/43 | KTU 9.478 | 8 | 1 / 1 |
| 28 | RIH 79/01 | KTU 9.443 | 15 | 2 / 1 |
| 30 | RIH 83/48 | KTU 9.482 | 15 | 1 / 9 |
| 32 | RIH 84/11 | KTU 9.492 | 5 | 0 / 1 |
| 33 | RIH 87/01 | KTU 9.528 | 19 | 0 / 2 |
| 34 | RIH 84/07 | KTU 9.490 | 2 | 0 / 0 |
| 36 | RIH 83/01 | KTU 9.457 | 15 | 0 / 7 |
| 38 | RIH 83/26 + 83/27 + 83/40 | KTU 9.476 | 8 | 0 / 0 |
| 39 | RIH 83/49 | KTU 9.483 | 3 | 1 / 2 |
| 40 | RIH 83/52 | KTU 9.485 | 7 | 2 / 1 |
| 44 | RIH 83/20 + 83/29 | KTU 9.473 | 13 | 1 / 6 |
| 46 | RIH 83/53 | KTU 9.486 | 12 | 1 / 0 |
| 47 | RIH 84/[31,05] | KTU 9.504 | 4 | 1 / 0 |
| 50 | RIH 83/18 | KTU 9.472 | 24 | 0 / 2 |
| 52 | RIH 83/44 | KTU 9.479 | 13 | 1 / 2 |
| 56 | RIH 83/39 + 83/55 | KTU 9.477 | 10 | 0 / 5 |
| 59 | RIH 84/03 | KTU 9.488 | 12 | 0 / 6 |
| 64 | RIH 83/03 | KTU 9.459 | 6 | 0 / 1 |
| 65 | RIH 83/13 | KTU 9.467 | 4 | 1 / 2 |
| 66 | RIH 83/45 | KTU 9.480 | 3 | 0 / 0 |
| 67 | RIH 84/[31,10] | KTU 9.509 | 4 | 1 / 0 |
| 68 | RIH 2001/01 | — | 5 | 1 / 0 |
| 70 | RIH 79/10 | KTU 9.449 | 12 | 2 / 2 |
| 71 | RIH 84/01 | KTU 9.487 | 5 | 1 / 3 |
| 73 | RIH 83/04 | KTU 9.460 | 9 | 1 / 0 |
| 74 | RIH 88/01 | — | 6 | 2 / 2 |
| 75 | RIH 84/24 | KTU 9.496 | 4 | 1 / 1 |
| 76 | RIH 84/[30A] | KTU 9.499 | 2 | 1 / 0 |
| 77 | RIH 84/[31,27] | KTU 9.526 | 2 | 1 / 0 |
| 78 | RIH 83/06 | KTU 9.462 | 2 | 1 / 0 |
| 79 | RIH 84/[31,01] | KTU 9.500 | 9 | 1 / 3 |
| 80 | RIH 86/02 | — | 2 | 1 / 1 |
| 81 | RIH 82/01 | KTU 9.456 | 5 | 3 / 0 |
| 103 | RIH 80/05 | KTU 9.453 | 9 | 1 / 0 |
| 104 | RIH 80/04 | KTU 9.452 | 4 | 1 / 0 |
| 105 | RIH 77/14B | KTU 8.32 | 4 | 0 / 0 |
| 107 | RIH 79/08 | KTU 9.448 | 4 | 1 / 0 |
| 109 | RIH 77/08B | KTU 9.439 | 4 | 1 / 0 |
| 110 | RIH 77/10C | KTU 9.440 | 2 | 1 / 0 |
| 111 | RIH 77/10D | KTU 9.441 | 3 | 1 / 0 |
| 112 | RIH 77/12 | KTU 8.31 | 3 | 1 / 0 |
| 113 | RIH 78/13B | — | 5 | 1 / 1 |
| 116 | RIH 79/02 | KTU 9.444 | 2 | 1 / 1 |
| 117 | RIH 79/04[A] | KTU 9.445 | 5 | 0 / 2 |
| 118 | RIH 79/07 | KTU 9.447 | 15 | 1 / 1 |
| 119 | RIH 80/03 | KTU 9.451 | 3 | 0 / 2 |
| 120 | RIH 81/02 | KTU 9.454 | 8 | 2 / 0 |
| 121 | RIH 81/03 | KTU 9.455 | 5 | 3 / 1 |
| 123 | RIH 83/20A | — | 3 | 1 / 1 |
| 124 | RIH 83/20B | — | 4 | 1 / 0 |
| 125 | RIH 83/20D | — | 2 | 1 / 0 |
| 126 | RIH 83/20E | — | 2 | 1 / 0 |
| 128 | RIH 84/14[A] | — | 2 | 1 / 1 |
| 129 | RIH 84/25 | KTU 9.497 | 1 | 1 / 0 |
| 130 | RIH 84/[30B] | — | 1 | 0 / 0 |
| 131 | RIH 84/[31,03] | KTU 9.502 | 1 | 1 / 0 |
| 132 | RIH 84/[31,04] | KTU 9.503 | 2 | 1 / 0 |
| 135 | RIH 84/[31,11] | KTU 9.510 | 1 | 1 / 0 |
| 136 | RIH 84/[31,12] | KTU 9.511 | 3 | 1 / 0 |
| 137 | RIH 84/[31,13] | KTU 9.512 | 1 | 0 / 0 |
| 138 | RIH 84/[31,14] | KTU 9.513 | 2 | 1 / 0 |
| 140 | RIH 84/[31,16] | KTU 9.515 | 5 | 1 / 0 |
| 141 | RIH 84/[31,17] | KTU 9.516 | 1 | 0 / 0 |
| 142 | RIH 84/[31,18] | KTU 9.517 | 2 | 1 / 0 |
| 143 | RIH 84/[31,19] | KTU 9.518 | 2 | 1 / 0 |
| 144 | RIH 84/[31,20] | KTU 9.519 | 3 | 1 / 0 |
| 145 | RIH 84/[31,21] | KTU 9.520 | 3 | 1 / 1 |
| 146 | RIH 84/[31,22] | KTU 9.521 | 2 | 1 / 0 |
| 147 | RIH 84/[31,23] | KTU 9.522 | 2 | 1 / 0 |
| 148 | RIH 84/[31,25] | KTU 9.524 | 2 | 1 / 0 |
| 149 | RIH 84/[31,26] | KTU 9.525 | 3 | 1 / 0 |
| 150 | RIH 84/[31,29] | KTU 9.527 | 1 | 0 / 0 |
| 151 | RIH 86/[03] | — | 1 | 0 / 0 |
| 152 | RIH 95/01 | — | 4 | 2 / 0 |
| 153 | RIH 98/01 | — | 1 | 1 / 0 |


Together the 90 texts have 590 lines, 1,125 words, 5,008 sign slots, 79 breaks
and 99 rulings.

### Not in this release

| Text | Why |
| --- | --- |
| KTU 1.5, 1.6, 1.35, 4.100 | Reviews not finished. KTU 1.5 and 1.6 keep their 0.3.0 versions, so KTU 1.6 IV 29 and V 30 are still lines reading `…` rather than breaks; that change arrives with the finished 1.6 review. |
| KTU 1.34 | `1.34 [= now KTU³ 1.26 fragment b]`: a catalogue alias whose target is a fragment. Aliases can point at a tablet or a column line span, not at `fragm. b`. |
| KTU 4.52 | Finished review prints the surface heading `rev. (?)`, which the source grammar does not know. |
| KTU 4.59 | Finished review prints `1[+ x ]` in line 3; `+` inside a numeral has no reading and the build refuses it. |
| KTU 4.63 | Finished review switches off the Akkadian subtotal lines (`ŠU.NIGÍN …`: I 24, II 14, 24, 29, 34, 39), so the line count skips them. |

The RIH II texts below are not included. "Malformed RIH identity" means the
heading combines texts, adds a former KTU² number, a line range or a remark
that the identity check does not accept; these are the texts whose identity
or alias needs a decision.

| RIH II text | Why |
| --- | --- |
| 4. RIH 83/02 (KTU 4.814) | Malformed RIH identity: `4. RIH 83/02 (KTU 4.814 [=former KTU2 9.458])` |
| 6. RIH 2002/01 | Line 18 uses `_`, which has no reading |
| 7. RIH 97/01 + 97/02 | Line 14 uses `` ` `` and line 41 uses `e`, which have no reading; also open editorial question on the erasure in line 22 |
| 9. RIH 83/17 + 83/19 + 83/38 + 83/41 (KTU 4.813) | Text in a nested Word text box with no reading order; malformed RIH identity (`[= former KTU2 9.471]`) |
| 19. RIH 84/09 (KTU 9.491) | Unrecognised paragraph `Tranche inférieure : anépigraphe ?` |
| 31. RIH 83/05 (KTU 9.461) | Duplicate line address I 2 (unnumbered erased lines); open editorial question on erasures |
| 37. RIH 83/16 (KTU 9.470) | Line 5 uses `,`; unrecognised paragraphs `Texte partiellement effacé` and `13-15 [traces]`; open editorial question on erasures |
| 41. RIH 84/05 (KTU 9.489) | Unrecognised paragraph `Tranche inférieure/supérieure` |
| 43. RIH 83/47 + 83/51 + 83/56 (KTU 9.481) | Lines 5 and 16 use `!`, which has no reading |
| 45. RIH 83/23 + 83/30 + 83/32–36 (KTU 9.474) | Unrecognised paragraph `Verso [détruit]` |
| 48. RIH 89/01 | Duplicate line address I 10 |
| 49. RIH 83/11A + [83/11B (KTU 9.466)] + [83/28 + 83/31 + 84/15 + 84/26 (KTU 4.781)] | Malformed RIH identity: two KTU numbers in one heading |
| 96. RIH 98/02 (KTU 1.180) | Malformed RIH identity: `(KTU 1.180: lines 1-5)` |
| 108. RIH 83/21 (KTU 6.23) | Malformed RIH identity: `(KTU 6.23) - RIH has 3 extra lines` |
| 122. RIH 83/15 (KTU 9.468 + 9.469) | Malformed RIH identity: `[A+B] (KTU 9.468 + 9.469)` |
| 134. RIH 84/[31,08] (KTU 9.507) | Line 4 uses `_`, which has no reading |

The editorial question on RIH erasures also names 10. RIH 77/02A+, 57. RIH
83/12 and 98. RIH 77/08A+; there are no transcriptions of these among the
106. The same question lists texts with "nothing left to bracket" (among the
90: 14, 15, 16, 59, 64 and 103); its open decision does not concern them, so
they are included.

## Languages

`language` and `tablet_language` carry the language KTU³ states in the SR:
or Ge: field of a KTU text, as in 0.3.0. KTU³ does not contain the RIH texts,
not even the 75 with a KTU 9.x number, so by the editors' decision they take
RIH II's own statement. RIH II has no per-text language field, but it divides
the volume. Its table of contents sets texts 1–153 under "Première partie ...
Les textes ougaritiques" and 154–168 under "Deuxième partie ... Les textes
suméro-akkadiens", and its back cover describes the texts as "en langue
ougaritique et en suméro-akkadien". All 90 RIH texts here are among 1–153, the
alphabetic texts; the syllabic ones are not in the corpus. Every RIH text is
therefore `Ugaritic`, on its words and on its tablet.

No RIH transcription writes an Akkadian logogram. The 90 texts have no
`logogram` word or sign, and none of the 106 RIH II transcriptions has a
capitalised sign group in a line. RIH II names logograms only in its
commentary, when it cites syllabic parallels such as `{DINGIR.U}` in RS 16.241.
In KTU the only logograms are the five Sumerograms of KTU 4.38, which are
`Ugaritic` like the rest of that text: `language` is the language of the text,
not a judgement about each word.

| `language` | Words in 0.3.0 | Words in 0.4.0 | Texts |
| --- | ---: | ---: | --- |
| `Ugaritic` | 29,813 | 31,556 | all other KTU texts, and the 1,125 words of the 90 RIH texts |
| `Hurrian` | 640 | 657 | as in 0.3.0, plus KTU 1.32 and 1.33 |
| `Akkadian` | 129 | 129 | KTU 1.67, 1.69; KTU 1.73 lines 1–7 |
| absent | 260 | 260 | as in 0.3.0: mixed passages and texts without a stated language |

`tablet_language`: `Ugaritic` 431 (341 KTU, 90 RIH), `Hurrian` 12, `Hurrian and
Ugaritic` 4, `Akkadian` 2, `Akkadian and Ugaritic` 1; absent on KTU 5.24, 5.27
and 7.191.

## Features

The 0.3.0 features keep their meaning. Eight node features appear for the first
time in a published CUC dataset; they come with the RIH texts. With `otype`
this makes 41 node features (33 in 0.3.0) and the same three edge features.

| Feature | Node | Meaning | Values in 0.4.0 |
| --- | --- | --- | --- |
| `tablet@rih` | `tablet` | A second name for every tablet, so that a Ras Ibn Hani text can be addressed by its RIH number: a RIH text is named by its RIH II citation, every other tablet by its usual name. Use it with `lang="rih"`, see below. | 453 tablets |
| `rih` | `tablet` | The RIH II citation of the text, for example `RIH 83/08`. A citation, not a claim about the physical object; a joined text cites all its pieces (`RIH 83/50 + 83/54`). | 90 tablets |
| `ktu` | `tablet` | The KTU number RIH II gives for the text, for example `KTU 9.463`. Absent on the 15 RIH texts without one and on all KTU tablets, whose number is `tablet`. | 75 tablets |
| `source_edition` | `tablet` | The edition the text is transcribed from: `RIH II`. Absent on KTU tablets. | 90 tablets |
| `surface_source` | `line` | The surface heading exactly as RIH II prints it, where it differs from the normalized `surface`: `Recto` 356 lines, `Verso` 113, `Recto/verso` 65, `Tranche inférieure` 22, `Recto/Verso` 9, `Tranche supérieure` 7, `Recto/verso ?` 6, `Tranche gauche` 4, `Verso/recto`, `Tranche droite` and `Tranche` 1 each. It was supported but not emitted in 0.3.0. | 585 lines |
| `number` | `line` | An integer printed after a line of RIH 83/08 (KTU 9.463), kept as a line annotation rather than as text. Line 1 `yṯpṭ 16` has `number=16`. | 30 lines |
| `line_mark` | `line` | An epigraphic tick of unknown function at the line, in RIH 83/50 + 83/54 (KTU 9.484): `tick`. | 24 lines |
| `line_mark_cert` | `line` | Certainty of that tick: `True` 22, `False` 2. | 24 lines |

Two existing features gain values from RIH II:

- `surface` gains the object-neutral `face` (81 lines: `Recto/verso`,
  `Recto/Verso`, `Recto/verso ?`, `Verso/recto`) and `edge` (1 line: `Tranche`),
  where RIH II does not say which face or edge it is. These lines have
  `surface_cert=False`, which rises from 15 lines in 0.3.0 to 97.
- `type=editorial` becomes common: RIH II writes a lacuna of unknown length as
  `[…]`, and the `…` is an editorial sign (483 slots) forming an editorial word
  (99 words). Editorial signs rise from 70 to 556 and editorial words from 6
  to 105.
- `cert` on RIH signs comes from RIH II's half-brackets: a sign inside `⸢ ⸣`
  is `False`, a read sign outside them `True`. An unread sign (`-` in RIH II,
  `x` in the corpus) is always `False`, as every `x` is in KTU.

### Addressing a Ras Ibn Hani text by its RIH number

A RIH text with a KTU number is addressed by that number, as before:
`T.nodeFromSection(("KTU 9.463", "I", "1"))`. It can now also be addressed by
its RIH number, with `lang="rih"`:

```python
line = T.nodeFromSection(("RIH 83/08", "I", "1"), lang="rih")
T.sectionFromNode(line)              # ('KTU 9.463', 'I', '1')
T.sectionFromNode(line, lang="rih")  # ('RIH 83/08', 'I', '1')
```

With `lang="rih"` every other tablet keeps its usual name, so the same calls
work for KTU tablets: `T.nodeFromSection(("KTU 1.1", "I", "1"), lang="rih")`.
This is Text-Fabric's mechanism for a second set of names for the top section
level (BHSA uses it for book names in several languages); `rih` names the
numbering, not a language.

## Changes within previously published tablets

340 of the 342 tablets of 0.3.0 are unchanged: the same lines, signs, spacing
and features. Two change because their finished reviews replace the reference
version used in 0.3.0. No line is added or removed in either.

| Tablet | Lines changed | Signs + / − | Spacing slots | `cert` | `emen` | `cont` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| KTU 1.4 | 27 | 1 / 2 | 22 | 12 | 1 | 1 |
| KTU 1.31 | 3 | 0 / 0 | 15 | 1 | 0 | 0 |

KTU 1.4 (1,680 → 1,681 words, 7,774 → 7,765 slots):

- a word divider gets its space: I 5 `il. abh` → `il . abh`, and likewise
  I 34, V 41, VI 6, VII 18 and VIII 44; VIII 49 loses a double space before
  `ugrt`;
- II 11 `tġzy` → `tġẓy`;
- lacunae are shorter by one to four slots in I 2, II 45, III 50, 51, 55,
  VI 60–62 and VIII 48, and longer by one in VIII 44 (gap slots 1,120 → 1,108);
- the other ten changed lines read the same and differ in certainty,
  editorial state or continuation marking.

KTU 1.31 (29 → 44 slots): each of its three lines has a lacuna five slots
longer, as the review measures it on the scan.

These lacuna widths are the reviewers' measurements and differ from the
reference transcription by design. They were checked against the KTU
Validator defect described below.

## Checks on the new reviews

Before v1.0.18 (6 November 2026) the KTU Validator could merge a rebuilt OCR
bundle into saved work, adding rows, changing lacuna widths and re-inserting
footnote markers. Every review new in 0.4.0 was checked for the symptoms:

- no column has a repeated line address (in the work files and in the built
  TF, where all 9,535 section addresses are unique);
- no two text rows share a scan crop;
- KTU 1.4 and 1.31, the only new reviews with a reference version, are
  compared above. KTU 1.4 was last saved about an hour after v1.0.18 was
  released and is not among the tablets whose widths the incident recovery
  restored; KTU 1.32 and 1.33 were saved the next day on the same computer.
  KTU 4.42–4.62 were reviewed on another computer whose validator version is
  not recorded; they have no reference transcription to compare widths with,
  so their widths could only be checked for the row symptoms above.

Footnote markers do not reach the published text, so a re-inserted marker
cannot change the data.

## Validation and tests

The 0.4.0 sources were frozen from the 0.3.0 source set (342 KTU documents),
23 finished KTU reviews and 90 RIH II transcriptions, with a hash of every
input. The build is a full rebuild with the converter at
alexsosn/CUC-doc-TF-converter branch `codex/release-040` (commit b95da78); no TF file was edited
by hand.

- Converter test suite: 1,062 passed, 10 skipped.
- Source lint: only the three findings already present in 0.3.0 (KTU 1.66
  marker a⁾ without footnote; one-sided brackets in KTU 4.24:2 and 4.41:5).
- Serialized-corpus lint: no findings.
- `cuc-convert diff` against 0.3.0: 340 tablets unchanged, 2 changed, 111 new,
  none gone.
- The CUC release tests check 0.4.0 as they check 0.3.0, plus the additions,
  the RIH features, RIH II's `Ugaritic` on RIH texts and the KTU 1.4/1.31
  changes: 30 passed. The general test that no `x` is certain runs on 0.4.0.
