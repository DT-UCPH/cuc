# CUC 0.3.0

CUC 0.3.0 expands the corpus with completed KTU transcriptions and repairs the
conversion of document structure, word boundaries, sign variants, and editorial
markup. It also makes breaks and scribal rulings queryable in Text-Fabric.
The previous TF versions remain available.

| Node type | 0.2.8 | 0.3.0 | Interpretation |
| --- | ---: | ---: | --- |
| `sign` | 146,017 | 165,665 | 164,496 source-backed sign slots and 1,169 invisible synthetic slots in 0.3.0 |
| `word` | 27,770 | 30,843 | Source text units, including gaps and non-lexical content |
| `line` | 7,616 | 8,692 | Retained textual lines |
| `column` | 334 | 415 | Columns, implicit column I and fragment divisions |
| `tablet` | 279 | 342 | Independent KTU texts; 63 additions |
| `boundary` | — | 1,165 | 705 scribal rulings and 460 breaks |
| `alias` | — | 3 | Catalogue identifiers resolving to existing canonical spans |

There are 207,125 nodes in total. The build applies 42 configured corrections,
recognizes one as already present, and leaves no unmatched correction. Forty-one
lines carry `erratum`; multiple corrections can affect one line, and a restored
ruling is represented by its own boundary node.

## Coverage and languages

Only completed reviews enter this release. KTU 1.3 and 1.62 use their completed
reviews. The reviews of KTU 1.4 and 1.5 are in progress, so those tablets retain
their reference versions. KTU 1.125 and the corrected KTU 5.24 are included.
RIH II conversion is supported by the converter but **no RIH tablets are
published in this release**. No Akkadian-language tablet is newly added.

The language labels below describe the texts; they are not new word-level
language annotations. The converter cannot infer each word's language from
transliteration. In particular, Sumerograms in an Ugaritic text do not make the
whole tablet Sumerian or Akkadian.

| Newly available tablet | Language or text type | Retained lines |
| --- | --- | ---: |
| KTU 1.9 | Ugaritic | 20 |
| KTU 1.10 | Ugaritic | 104 |
| KTU 1.11 | Ugaritic | 21 |
| KTU 1.12 | Ugaritic | 102 |
| KTU 1.13 | Ugaritic | 38 |
| KTU 1.26 | Hurrian | 18 |
| KTU 1.30 | Hurrian | 5 |
| KTU 1.42 | Hurrian | 62 |
| KTU 1.51 | Hurrian | 20 |
| KTU 1.66 | Hurrian | 37 |
| KTU 1.68 | Hurrian | 34 |
| KTU 1.77 | Ugaritic | 5 |
| KTU 1.125 | Hurrian | 18 |
| KTU 1.135 | Hurrian | 15 |
| KTU 1.148 | Ugaritic and Hurrian; Hurrian passage in lines 13–17 | 45 |
| KTU 1.150 | No readable textual lines; language unassigned | 0 |
| KTU 1.151 | Ugaritic | 15 |
| KTU 1.152 | Ugaritic | 11 |
| KTU 2.2 | Ugaritic | 12 |
| KTU 2.106 | Ugaritic | 14 |
| KTU 4.1 | Ugaritic | 4 |
| KTU 4.2 | Ugaritic | 5 |
| KTU 4.3 | Ugaritic | 5 |
| KTU 4.4 | Ugaritic | 10 |
| KTU 4.5 | Ugaritic | 3 |
| KTU 4.6 | Ugaritic | 5 |
| KTU 4.7 | Ugaritic | 21 |
| KTU 4.8 | Ugaritic | 7 |
| KTU 4.9 | Ugaritic | 6 |
| KTU 4.10 | Ugaritic | 10 |
| KTU 4.11 | Ugaritic | 15 |
| KTU 4.12 | Ugaritic | 16 |
| KTU 4.13 | Ugaritic | 36 |
| KTU 4.15 | Ugaritic | 13 |
| KTU 4.16 | Ugaritic | 13 |
| KTU 4.17 | Ugaritic | 22 |
| KTU 4.19 | Ugaritic | 3 |
| KTU 4.20 | Ugaritic | 5 |
| KTU 4.21 | Ugaritic | 3 |
| KTU 4.22 | Ugaritic | 6 |
| KTU 4.23 | Ugaritic | 14 |
| KTU 4.24 | Ugaritic | 7 |
| KTU 4.25 | Ugaritic | 6 |
| KTU 4.27 | Ugaritic | 22 |
| KTU 4.28 | Ugaritic | 9 |
| KTU 4.29 | Ugaritic | 4 |
| KTU 4.30 | Ugaritic | 14 |
| KTU 4.31 | Ugaritic; short Semitic alphabet | 11 |
| KTU 4.32 | Ugaritic | 5 |
| KTU 4.33 | Ugaritic | 41 |
| KTU 4.34 | Ugaritic | 9 |
| KTU 4.35 | Ugaritic | 50 |
| KTU 4.36 | Ugaritic | 4 |
| KTU 4.37 | Ugaritic | 7 |
| KTU 4.38 | Ugaritic with Sumerograms in quantity expressions | 6 |
| KTU 4.39 | Ugaritic | 7 |
| KTU 4.40 | Ugaritic | 18 |
| KTU 4.41 | Ugaritic | 12 |
| KTU 4.140 | Ugaritic | 2 |
| KTU 4.185 | Ugaritic | 10 |
| KTU 5.24 | Alphabet exercise; no continuous language assignment | 1 |
| KTU 5.27 | Alphabet exercise; no continuous language assignment | 5 |
| KTU 7.191 | Undetermined; unclassified fragment | 7 |

These counts are retained textual line nodes, not the highest printed line
number, page count, ruling count, or a count of editorial footnotes. KTU 1.150
has a tablet node and one invisible anchor, but no fabricated line or reading.

Three catalogue identifiers become queryable redirects:

| Alias | Canonical span |
| --- | --- |
| KTU 1.8 | KTU 1.3 VI 1–17 |
| KTU 1.99 | KTU 1.98 |
| KTU 2.19 | KTU 3.12 |

## Node types and slot membership

`sign` remains the slot type. A slot can represent a letter, a literal numeral,
an unread sign, editorial punctuation, or source spacing. It is therefore not
correct to count every sign node as a preserved letter. Source-backed slots and
synthetic empty slots are reported separately.

`word` remains a source text unit, rather than a claim about linguistic
segmentation in every damaged passage. Its explicit `type` distinguishes
lexical words from wholly unreadable units, lacuna units, numbers, logograms,
and editorial objects. Bounded KTU non-breaking-space patterns now separate
words and lacuna units. For example, in KTU 1.62 I 6 the long lacuna preceding
`m]lakm` becomes a gap word; the restored `m` remains part of the lexical word
`mlakm`. The lacuna may have contained wholly lost words, but the converter does
not infer their number. `[.]` remains a bracketed divider, not an invented word
boundary.

`line` keeps a source-positioned textual line. Its string address is now
`line_label`; the integer `line` remains the printed count where applicable.
`column` represents a column, an implicit column I, or a separately numbered
fragment division. A five-line tablet such as KTU 3.34 does not require an
editor to insert a column heading merely to satisfy the software.
`tablet` represents an independent catalogue text, including the empty KTU
1.150. Catalogue redirects do not create additional tablets.

Two node types are new:

- `boundary` represents an independently positioned break or scribal ruling.
  Each owns one synthetic empty sign slot at the corresponding point in the
  source sequence. It does not borrow a letter from an adjacent line.
- `alias` represents a catalogue cross-reference. It spans exactly the already
  existing slots of its canonical tablet or specified column/line range. It
  adds no text and allocates no additional slot.

`oslots`, the standard TF containment edge, consequently includes the new
boundary anchors, empty textual anchors, and alias spans. Ancestor containers
reuse their descendants' slots. A synthetic slot has no visible `sign` or
`usign` value; it is not a reconstructed letter or an estimate of lacuna width.
Absolute node numbers change and must not be used as cross-version identifiers.

## Every emitted node feature

The standard TF feature `otype` records a node's kind: `sign`, `word`, `line`,
`column`, `tablet`, `boundary`, or `alias`. Its vocabulary gains the two new node
kinds described above. Together with the 30 features below, it makes 31 emitted
node features in this dataset.

### Signs

| Feature | Meaning and derivation in 0.3.0 |
| --- | --- |
| `sign` | The source sign in Latin/editorial transcription. KTU 4.31's short-alphabet `s̄` and `ẖ` each occupy one slot; the combining macron is part of `s̄`, not an extra sign. Canonically decomposed `h` plus U+0331 is represented as `ẖ`. Word non-breaking spaces are serialized as plain spaces; the bounded word-division decision is made before that normalization. Synthetic anchors have no value. |
| `usign` | Unicode rendering of the same slot. Ugaritic letters use the mapping; literal numbers and approved Sumerograms retain their printed values. By explicit editorial decision, short-alphabet `ẖ` maps to `𐎃` and `s̄` maps to `𐎘`; their distinct Latin readings remain in `sign` and `g_cons`. The Hurrian `Ṯ` uses the thanna sign with an enclosing circle instead of `?`. |
| `type` | Explicit slot role determined from the character and current editorial context. `cons` is a readable letter; `unreadable` is `x`; `gap` is spacing in a lacuna/editorial span; `sep` is ordinary source spacing; `divider` is a dot that remains a slot; `editorial` is notation such as `?` or `-`; `number` is literal numerical text; `logogram` is a character in an approved Sumerogram; `logogram_sep` is its internal dot; `empty` is an invisible synthetic anchor. |
| `synthetic` | `True` only on an invisible anchor created to retain an otherwise slotless textual entity. Absence means the slot comes from the source character sequence. |
| `sign_index` | Integer variant index attached to the letter's own slot. KTU 1.77's `ṯ₂`, `ḫ₂`, and `ẓ₂` each have one letter slot with index 2. The subscript is not a separate sign. |
| `after` | Literal Latin/editorial material following this slot that is retained for reconstruction but does not itself occupy a slot, notably a definite word divider or letter index. Its position is preserved even when it precedes the last slot of a word. |
| `uafter` | Unicode counterpart of `after`: a word-divider sign for a definite dot, or the literal variant subscript. |
| `cert` | The edition's certainty judgement derived character by character from Word formatting: `True` for a certain/italic letter and `False` for an uncertain/roman letter. Brackets and certainty are independent: rare italic letters inside restorations are preserved. Roman Sumerograms do not acquire false uncertainty merely because their script is typeset roman. |
| `emen` | Editorial state from the bracket stack: `restored` for `[ ]`, `excised` for `[[ ]]`, `redundant` for `{ }`, `missing` for `< >`, and `remark` for `( )`. A closer returns to its enclosing state; the state resets at the next line. |
| `alt` | Alternative reading or slash-separated alternatives attached to the preceding sign, in edition order. `l/d/u` gives primary `l` and `alt=d/u`; alternative letters do not become extra slots. State cannot leak to a preceding word. |
| `cont` | `continued` on the slot immediately before an editorial backslash continuation boundary. It no longer marks every later sign in the line. The backslash is control notation, not a visible sign. |

### Words

| Feature | Meaning and derivation in 0.3.0 |
| --- | --- |
| `g_cons` | Consonantal reading derived from this word's own source span. It retains unread `x` but excludes alternative readings, punctuation and numerical-only content; use the sign stream for the complete transcription. Split words now receive their own independently derived reading. |
| `type` | `lexical` for a readable letter-bearing unit; `unreadable` if its reading contains `x`; `gap` for a wholly lost unit; `numeric` for numerical-only content; `logogram` for an approved Sumerogram; `editorial` or `divider` for the corresponding non-lexical objects. These are source-unit categories, not morphology or word-language labels. |
| `trailer` | Definite word-divider material assigned to this word. Classification depends on the dot's semantic position, not its character offset or the number of following spaces. |
| `utrailer` | Unicode counterpart of the word trailer. This word-level summary remains available although display reconstruction now uses slot-level `after/uafter`. |
| `trailer_emen` | Editorial state at an actual trailer. A word with no trailer no longer inherits an unrelated bracket state. Restored trailers on newly split words are derived at their own divider position. |

The former word feature `language`, which always said `Ugaritic`, is removed.
Keeping that constant would mislabel Hurrian passages and mixed-language texts.
No inferred replacement language feature is introduced.

### Lines, columns and tablets

| Feature | Node | Meaning and derivation in 0.3.0 |
| --- | --- | --- |
| `line_label` | `line` | String address as printed, including a prime or letter where present. It is the line section feature, so uncounted lines can have addresses without fabricated integer numbers. |
| `line` | `line` | Integer edition line count on counted lines. It is retained for numeric queries; it is not a global absolute line number. |
| `numbering` | `line` | `relative` when a printed prime or an earlier break of unknown extent makes the numbering relative in that column. It does not renumber the text. |
| `surface` | `line` | Canonical surface name, replacing `side`. Leading/trailing whitespace is removed; the value resets per tablet and defaults to `obv.` until a heading changes it. |
| `surface_cert` | `line` | `True` when the surface attribution is asserted and `False` when the edition questions it. Thus `rev.?` becomes `surface=rev.` and `surface_cert=False`, instead of an extra surface category. |
| `erratum` | `line` | Citation identifying an improved reading applied at conversion. It is set only when the quoted original reading matches the selected line; the source transcription itself is preserved. Damaged letters in the replacement are assigned the corresponding certainty. |
| `column` | `column` | Column label or fragment division such as `fragm. a`. A single unheaded column is `I`; a fragment's own numbering restarts as printed. |
| `fragment` | `column` | Sparse fragment siglum, for example `a` from `fragm. a:`. It belongs to the division, rather than being copied onto every line. |
| `tablet` | `tablet` | Independent KTU text identifier taken from the tablet heading. Redirect identifiers are carried by alias nodes instead. |
| `tablet_info` | `tablet` | Existing scholarly notes about the damaged state or nonjoining line spans of KTU 1.7 and 1.84. This feature is retained. |

### Breaks, rulings and aliases

| Feature | Node | Meaning and derivation in 0.3.0 |
| --- | --- | --- |
| `boundary_kind` | `boundary` | `break` for a transcription break or `ruling` for a scribal ruling, derived from the corresponding standalone marker paragraph. |
| `boundary_source` | `boundary` | Exact printed marker, such as `…`, `-----`, or `=====`. This preserves the notation and single/double ruling distinction. |
| `catalogue_alias` | `alias` | Superseded catalogue identifier, for example `KTU 1.99`. |
| `catalogue_target` | `alias` | Canonical identifier and optional column/line range, for example `KTU 1.3 VI 1-17`. The declared target is resolved and validated against retained corpus nodes. |
| `catalogue_alias_source` | `alias` | Literal catalogue cross-reference statement printed by the edition, including its edition number. It is textual catalogue evidence, not a document location or workflow record. |

The two new valueless edge features point **from a boundary node** to its
immediately preceding retained line (`boundary_prev`) and immediately following
retained line (`boundary_next`) within the same column. An edge is absent at a
column end or where no adjacent retained line exists. Neither edge crosses
into another column or tablet.

`surface_source` is supported by the converter but is **not emitted in this
KTU release**: it would retain the literal heading when an edition's surface
term needs canonical normalization. `fragment_source` does not exist.
The converter's RIH-specific `rih`, `ktu`, `source_edition`, `line_mark`,
`line_mark_cert`, and `number` features are also absent from this dataset.
`prime` is supported for both KTU and RIH: it records one or two printed prime
marks after a counted line number. No selected KTU line emits it in this build,
so it is likewise absent. These absent features must not be counted as new
features of the published KTU corpus.

## Changes within the 279 previously published tablets

| Change in existing tablets | Measured result |
| --- | ---: |
| Newly retained textual lines | 1 |
| Removed textual lines | 0 |
| Paired lines with changes in signs, spacing, editorial features or surface | 5,902 |
| Visible transcription characters added / removed | 159 / 134 |
| Readable letters within those additions / removals | 89 / 78 |
| Unreadable `x` signs within those additions / removals | 25 / 12 |
| Editorial/divider characters within those additions / removals | 45 / 44 |
| Whitespace-slot edits | 13,764 |
| Aligned signs with changed `cert` | 202 |
| Aligned signs or whitespace with changed `emen` | 130 |
| Aligned slots with changed `alt` | 11 |
| Aligned slots with changed `cont` | 119 |
| Aligned slots with changed `usign` | 1 |
| Lines with changed surface attribution | 5,410 |
| Lines with changed surface uncertainty | 9 |
| Retained word units | 27,770 → 27,790 |
| Wholly lost word units | 519 inferred from old whitespace-only spans → 523 explicitly typed gaps |
| Explicitly typed lacuna-spacing slots in the new version of existing tablets | 38,457 |
| Newly represented scribal rulings / breaks in existing tablets | 531 / 376 |
| Non-empty alternative-reading annotations | 79 → 90 |
| Slots carrying a continuation boundary | 102 → 18 |
| Words with non-empty trailer emendation | 2,889 → 1,593 |

One old tablet is unchanged under this textual comparison; 278 change, mainly
because surface attribution and spacing are corrected. All 279 remain present.
The old release had no boundary nodes, so the 531 rulings and 376 breaks are
newly represented source entities rather than edits to existing boundary IDs.
The 63 added tablets contribute a further 174 rulings and 84 breaks.

For existing tablets, `cert=True` changes from 53,664 to 53,743 and `cert=False`
from 23,551 to 23,496. These totals also include additions/removals and therefore
are different from the 202 aligned certainty changes. Existing `emen` totals are
51,597 → 51,260 restored, 396 → 393 excised, 72 → 73 redundant, 123 → 125 missing,
and 43 → 56 remark slots. Trailer-emendation counts shrink because bracket state
is no longer written on words without a trailer.

The comparison pairs lines by tablet, column and printed line address, then
aligns their visible sign sequences. A replacement is one removal plus one
addition. These are visible transcription characters, including editorial
characters, rather than a count restricted to alphabetic letters. Spacing
changes count added/removed whitespace slots, including normalization of NBSP
and changes to lacuna padding; they are not a count of newly discovered gaps.
New-tablet data are excluded from these existing-tablet statistics.

## Converter fixes relative to the original notebook

- Surfaces no longer leak from one tablet into the next. Surface and column
  names are trimmed, unmarked obverses are explicit, and uncertainty about the
  surface is separate from its name.
- Editorial state resets at line boundaries. Nested brackets restore their
  enclosing state, and double square brackets represent erasure correctly.
- Breaks and scribal rulings survive as positioned nodes. Otherwise empty
  textual units remain reachable through invisible anchors; container nodes
  reuse descendant anchors.
- Definite dividers are identified by source order rather than a fragile
  character index. `trailer_emen` is set only on real trailers. Both configured
  text formats reconstruct dividers and indexed variants through `after/uafter`.
- Bounded NBSP cases split the appropriate lexical and lacuna units. The first
  restored letter after a long lacuna remains attached to its word, and `[.]`
  is not misread as a boundary. Ordinary NBSP typography is normalized to a
  plain space in the resulting TF.
- Italic certainty is read per character and is invariant under Word run
  partitioning. The edition's rare italic restorations pass through.
- Alternative readings attach to a sign in the current word and retain every
  printed alternative. Continuation marks describe the immediately preceding
  boundary instead of contaminating later signs.
- Structural recognition matches complete headings. Fragment divisions,
  relative numbering and uncounted line addresses are explicit. Missing column
  headings on single-column tablets are handled automatically.
- Literal numbers, fractions, indexed letters, the bare abecedary aleph, and
  the attested Sumerograms are accepted without requiring source-format hacks.
  The Hurrian `Ṯ` receives its proper Unicode rendering. Short-alphabet `s̄`
  and `ẖ` are legal letters, each with one slot and one certainty position even
  when a combining mark is in a separate Word run; word readings retain them.
  The editors' cuneiform mappings are `ẖ` → `𐎃` (7 signs) and
  `s̄` → `𐎘` (14 signs), all in the newly added KTU 4.31.
- Catalogue redirects survive as aliases without duplicating text. Finished
  reviews replace reference texts, while unfinished reviews remain excluded.
- Footnote markers and bounded apparatus are recognized and omitted from the
  current TF text. Missing footnote counterparts do not justify source edits
  or fabricated TF notes.
- The conversion is a testable package with independent source-structure
  validation, value and structural divergence ledgers, aggregate source/corpus
  lint, real-walker comparisons, and staged output publication. Word lock files
  are ignored; malformed input, invalid mappings, stale declarations and unsafe
  overwrites fail explicitly.

The CUC viewer uses the new reconstruction features, renders synthetic anchors
as empty, and displays certainty according to the serialized Boolean strings.
Its line labels follow `line_label`. Older datasets retain a trailer fallback.
Automatic GitHub CI triggers are disabled; the workflow remains manually
dispatchable.

## Validation and tests

The complete converter suite passes with **1,044 tests passed and 2 skipped**
against the frozen TF 0.2.8 comparison data. A real Text-Fabric build succeeds
over all 342 selected tablets; serialized-corpus lint reports no findings.
Configured corrections report **42 applied, 1 already present, 0 unmatched**.
The CUC release and display tests pass **13/13**.

Source lint reports no unsupported characters. Six unpaired-footnote diagnostics
concern apparatus excluded from the published text. Two bracket diagnostics,
KTU 4.24:2 and 4.41:5, concern source-attested one-sided breaks. They are recorded
as limitations of those lint checks, rather than used to rewrite the edition.

New or corrected converter tests cover tablet-to-tablet state resets, complete
heading grammar, nested editorial markup, per-character italics, divider roles,
trailer emendation, source-ordered empty anchors and ancestor reuse, boundary
edges, aliases and exact target spans, relative/uncounted numbering, fragment
resets, implicit column I, indexed letters, numbers and Sumerograms, complete
alternative readings, Unicode rendering, finished-source selection, and errata
matching. The NBSP suite preserves the 12 researched readings independently of
later editorial changes and audits the current full selection against a source
model. Mutation tests verify that wrong word readings, types, trailers and
trailer emendations fail validation.

Golden comparison uses stable source coordinates for structural migrations and
unchanged word membership for value comparison. Replaced word spans are checked
directly against raw-source membership and features. Both undeclared changes
and stale exceptions fail. A real Text-Fabric walker is compared with the
recording model.

The CUC tests additionally exercise certain/uncertain display, invisible
synthetic anchors without word parents, indexed letters within words, trailer
emendation, text escaping, and older-version trailer fallback. Release-data
checks validate containment, alias spans, boundary edges, section addresses,
and the absence of visible content on synthetic anchors.
