# Discussion points

## Scribal anticipation

Examples:

[KTU3 1.3 III 9](https://ugaritic-dict-1566828bafc2.herokuapp.com/texts/page/?ref=KTU+1.3&anchor=v-3-III-9)

```
KTU3 1.3 III 9
w . ʿrbn . lpʿn . ʿnt . hbr . w

KTU3 1.3 III 10
wql . tštḥwy . kbd . hyt
```

```
126322	a	?	?	?	?	Incomplete aliyn rewritten in full at the start of the next line (scribal anticipation).
# KTU 1.2 I:4						
126323	aliyn	aliyn/	ảlỉyn	adj. m. sg. abs. nom.	The Very / Most Powerful
```

```
131477	a	?	?	?	?	Incomplete an rewritten in full at the start of the next line (scribal anticipation).
# KTU 1.6 IV:23						
131478	an	an(I)	ản (I)	pers. pn.	I	
131478	an	an(II)	ản (II)	adv.	wherever	
```

```
131644	s	?	?	?	?	Incomplete spuy rewritten in full at the start of the next line (scribal anticipation).
# KTU 1.6 VI:11						
131645	spuy	!!spuy[/	/s-p-ʔ/	vb G inf.	to devour, eat, consume > to be consumed > fodder > give to eat > to feed, to serve > to eat
```

```
136840	pẓ	?	?	?	?	Incomplete pẓġm rewritten in full at the start of the next line (scribal anticipation).
# KTU 1.19 IV:11						
136841	pẓġm	pẓġ/m	pẓġ	n. m. pl. cstr. nom.	one who lacerates	
```

## Words broken by the scribe

```
140214	ašt	!(ʔ&a!št[	/š-t/	vb	to place	OR with next token: aštn (UDB R1; Del Olmo V:5 ast.n)
140215	n	-n(IV)	-n (IV)	pers. pn.	(for) him	enclitic -n (3ms/3fs); some readings merge with previous as aštn
```

```
130186	np	np(š(I)/	npš (I)	n. f. sg. abs. nom.	throat	Merge with the following?
130187	š	&š				
130188	npš	npš(I)/	npš (I)	n. f. sg. cstr. nom.	throat	
```

## Words to split by creating new ids

One 0.2.7 token currently holds two lexemes; we tag them as multi-lexeme
(space in col3, `;` in col4). Should these become two ids instead?

```
129957	bnġlmt	b~n ġlmt(II)/	b; ġlmt (II)	prep. + encl. -n; n. f. sg. abs.	in; concealment	bn ġlmt 'in the gloom' (// bn ẓlmt)
126073	lpˤn	l(I) pˤn/	l (I); pʕn	prep.; n. f. du. cstr. gen.	to; foot	l pˤn 'to the feet of'  (KTU 1.1)
127932	bšmm	b šm(m(I)/m	b; šmm (I)	prep.; n. m. du. abs.	in; heavens	b šmm 'in the heavens'  (KTU 1.3)
128041	lbˤl	l(I) bˤl(II)/	l (I); bʕl (II)	prep.; DN m. sg. gen.	to; Baʿlu	l bˤl 'to Baal'  (KTU 1.3)
127681	wl	w-l(II)	w; l (II)	conj.; neg. adv.	and; not	Tania: "SPLIT IN TWO WORDS!!"  (KTU 1.3)
```

## Words (and IDs) to be merged

One word split across two 0.2.7 ids (line break or tokeniser error). Currently
handled with the MERGE convention (both rows carry the same analysis, which
reconstructs the joined surface). Should these be one id instead? Tania flags
them with `[` on the fragment and/or a note ("d on next line should be attached").

```
127281	ybr	!y!brd[	/b-r-d/	vb G prefc. 3 m. sg.	to divide	MERGE: ybr+d = ybrd 'he carves' (Tania: d should be attached)
127282	d	!y!brd[	/b-r-d/	vb G prefc. 3 m. sg.	to divide	MERGE WITH THE PREVIOUS
```
```
127385	tm	!t!m]t]ḫṣ[	/m-ḫ-ṣ/	vb Gt prefc. 3 f. sg.	to fight	MERGE: tm+tḫṣ = tmtḫṣ (Tania: "one word with previous")
127517	bt	btlt/	btlt	n. f. sg. cstr. nom.	virgin	MERGE: bt+lt = btlt 'Maiden' (btlt ˤnt)
128446	h	hyn/	hyn	DN m. sg. abs. gen.	Hayyānu	MERGE: h+yn = hyn (Kothar); Tania "see DOL p346"
127268	p	prdmn/	prdmn	DN m. sg. abs. nom.	unknown deity	MERGE: p+rdmn = prdmn (DULAT redirects rdmn→prdmn)
```
Others of the same kind: `k+lbt`=klbt (127772-3), `u+dnh`=udnh (127792-3),
`bht+k`=bhtk (128189-90), `rišk+m`=riškm (128377-8); and in KTU 1.4 VIII the
descent formula has six: `y+rdm`=yrdm, `md+d`=mdd, `a+lp`=alp, `k+mn`=kmn,
`k+bd`=kbd, `q+rdm`=qrdm; KTU 1.1 `y+kbdnh`=ykbdnh. (See also the npš example
above.)

## Special characters inside DULAT lemmas

  * These are reconstruction markers, not parsing operators.
  * Handling proposal: remove them in the morphology and preserve in the DULAT reference column.
  * Complete [list of outliers](https://ugaritic-dict-1566828bafc2.herokuapp.com/search/?q=[%5E%5Cw/-]&field=lemma&regex=1&page=1) can be found from UgaritLab.
  * Examples:
    * special characters:
      * `ỉwrḫ‹`
      * `ỉwl[`
      * `ảsr(n)`
      * `ảy(ả/ỉ)ḫ`
      * `/ʕ-d(-d)/`
      * `ʕq[l]`
      * `/ʕ-s-y:s/`
      * `ʕṣbṣy[m`
      * `brs/ś(m)`
      * `b?ṣmm`
      * `*/g-h(-h/y)/`
      * `ġlb(x)[`
      * `/m-ḥ(-w:y)/`
      * `ś:sp/bś:sg`
      * `*/ṣ/ḍ-b-ṭ/`
    * rare transliteration symbols:
      * `ʕ̱zl`
      * `ks̱`
      * `s̄lẖt`
      * `s̄ls̄`
      * `s̄ls̄t`
      * `s̄mn`
      * `s̄mnt`
      * `s̄ql`
      * `s̄s̄`
      * `өḫr`
      * `өl`
      * `өr`
      * `өṭ`
    * whitespaces and word separators:
      * `gt.mlky`
      * `ḫdn ḫdlr`
      * `ḫlb gngnt`

## Documnetation needs an update

ksu/lli use the documented III-ʾ pattern ks(u/&u / ll(u/&i (discussion_points.md); the /& vs &/ order is still unsettled there.

## Broken signs (`x`)

Decision applied in the manual review: **do not encode `x` (illegible sign) in
the morphology** — the analysis carries only the readable part, and
reconstruction is not expected to hold for these tokens.

```
130076	bnx	bn(I)/	bn (I)	...	son	(was bn(I)/&x)
127567	ymxxxxxx	ym(II)/	ym (II)	...	sea	(was ym(II)/&x&x…)
127492	ḏxxmr	ḏxxmr	?	?	?	(heavily broken: surface only)
129881	hdxt	hd/ t	hd(d)	...	Haddu	(broken middle sign)
```

* **Linter implication:** the reconstruction check (col3 → col2) must ignore `x`
  (strip it from the surface, or skip x-tokens), otherwise these legitimately
  flag as non-reconstructable.

## Homonym disambiguation (which DULAT number?)

The auto-parser frequently picks the wrong homonym; translations + the DULAT
reverse-mention (attestation) index resolve them. Examples found in 1.2–1.4:

| line | token | auto → correct | reading |
|---|---|---|---|
| 1.3 I:15 | aṯrt | ảṯrt(I) 'nape' → **(II)** goddess | "a goblet **Athirat** may not eye" |
| 1.3 II:26 | kbd | kbd(II) 'total' → **(I)** 'liver' | "the **liver** of ʿAnatu" |
| 1.3 III:5 | dd | dd(II) 'cauldronful' → **(I)** 'love' | "the **love** of Mighty Baʿlu" |
| 1.2 (×16) | ym | ym(I) 'day' → **(II)** Yamm | zbl ym, tḥm ym, ym l mt "Yamm is dead" |
| 1.3 III:36 | gpn | gpn(I) 'vine' → **(III)** DN | "Gapnu and Ugaru" (messengers) |
| 1.3 IV:41 | mria | mrủ(II) 'fattener' → **(I)** 'fattened' | "an ox …, a **fatling**" |
| 1.3 bt rb | rb | rb(II) 'chief' → **rb(b)** 'drizzle' | "Tallay daughter of **Drizzle**" |
| 1.4 VIII | alp | ảlp(I) 'cattle' → **(II)** 'thousand' | "alp šd" (a thousand acres) |
| 1.3 II:6 | bn | bn(I) 'son' → **(II)** 'between' | "she fights **between** the two cities" |

**Proposal:** the parser should consult the DULAT reverse-mention index (which
entry DULAT cites for that exact line) when choosing a homonym; the linter should
flag any col4 entry that is *not* among DULAT's cited entries for the line.

## Noun state and case (Huehnergard §IV.B)

Construct = before a genitive noun or a pronominal suffix; genitive = after a
preposition or as a genitive complement; pl./du. have only nom. vs. oblique.
Systematic auto-parser errors corrected across 1.1–1.4:

* **Preposition → genitive** (oblique for pl./du.): `bd nˤm`, `k imr`, `b ks`,
  `ˤmn kbkbm`, `l rqm` → gen.
* **Pron. suffix → construct**: `mlkn`, `bšrtk` were `abs.` → `cstr.`
* **Genitive complement (last in chain) is absolute, not construct**: `bˤl arṣ`
  "Lord of the Earth" → `arṣ` **abs.** gen. (only `bˤl` is construct). This was
  the most pervasive error — many final genitives were over-marked `cstr.`
* **Case-vowel must match the POS case** (`&u`=nom, `&i`=gen, `&a`=acc):
  `lli` (k lli) `&i` → gen.; `la` (object) `&a` → acc.
* **Vocative = nominative** — there is no separate vocative case; 41 `voc.`
  labels in 1.4–1.6 changed to `nom.` (the interjection `y` keeps `voc. functor`
  as a *particle type*, not a case).

**Open question:** for pl./du. the grammar collapses gen.+acc. into one oblique
form — do we still label them `gen.`/`acc.` by syntactic role, or introduce `obl.`?

## Gloss sourcing: exact DULAT wording vs. readability

Working rule = exact DULAT wording, no paraphrase. Tensions that need a policy:

* **Opaque / non-English DULAT glosses** — `Schar` (prdmn), `ein Stein` (anhbm),
  `klug, verständig` (ḫss). Manual review replaced `Schar` → "unknown deity".
  Do we allow a plain-English gloss when DULAT's is German/opaque?
* **Verbose multi-sense strings** — e.g. `b` = "in; through, on; by, at; within…",
  `bn (I)` = "4) special uses b) pl. cstr./suff. bn 'sons of' > family". Trim?
* **Participles / agent nouns** glossed with the verb infinitive — `mḫṣ`
  "smiter" → DULAT "to wound, beat, crush, kill"; `qnyt` "creatress" → "to acquire".
* **DN/entry with empty DULAT gloss** — `gpn (III)`, some `bˤl` epithets → `?`,
  or the conventional name?

## Words attested in the text but not lemmatised in DULAT

Left as `?` (we do not invent entries). Worth flagging upstream to DULAT:
`rbb` "showers/dew" (only `rbbt` 'myriad' exists), `tant`/`tunt`, `ḥšqk`,
`amṣḫ` (/m-ṣ-ḫ/), `lḥmd` (lemma exists but has no gloss).

## Sign-reading / transliteration differences (whose is authoritative?)

Tania's parsing vs. the 0.2.7 surface differ on some readings:
`ḥkm`/`hkm`, `ḥš`/`hšk` (ḥ vs h); `klʔt`/`klat` (aleph as ʔ vs a). Since
reconstruction must match the recorded surface, we currently follow the 0.2.7
surface and encode the reviewer's reading (`128248 ḥkm`, `127372 kl(ʔ&a/t=`).
Which transliteration is canonical?

## Versioning / id alignment

Tania's 1.3 review uses an older id numbering (136937…); 0.2.7 numbers 1.3 as
127265–128456. We aligned by surface (≈98.7% direct) and kept the 0.2.7 ids
("always update reviewed → latest CUC"). A maintained id-version mapping would
make this repeatable.

## No human gold for KTU 1.1 and 1.2

1.1 (491 tokens) and 1.2 (950) were seeded from the auto-parse and *not* part of
the manual review (which covered 1.3–1.6). They are lower-confidence and
`?`-heavy; they should go to Tania/an expert. Example still to confirm: KTU 1.1
`125999 abn` is parsed as `ab`+`n` ('father') but the context `w lḫšt abn`
("the whisper of **stones**") wants `ảbn` 'stone'.

## Specific readings for the experts

* **1.3 I:2 `ˤbd`** — verb "serves" (Tania `ˤbd[`) or noun "servant"? And
  `p rdmn` (conj + name) vs `prdmn` (one DN; DULAT redirects rdmn→prdmn).
* **1.3 II:2 `bnt`** (`kpr šbˤ bnt`) — "seven **girls**" (bt I pl; UNP/TCS) or
  "tamarisk" (bnt III)?
* **1.3 II:37 `tṯar`** — context "arranges (the footstools)" but DULAT
  `/ṯ-ʔ-r/` = "to stand surety for"; no DULAT 'arrange' sense for this aleph root.
* **1.3 III:28 / IV:18 `atm`** (`atm w ank`) — Tania reads `/ʔ-t-w/` 'come' +
  encl. -m; vs. the independent pronoun "you (pl.)".
* **`ab šnm`** — Šunama (DN) vs "years" (šnt) (also raised for 1.5/1.6).

## Parser / linter improvements (the self-improving loop)

* N-stem assimilated *n*: parser emits `(]n]` which decodes wrong (`tnqrb`); the
  reconstructing order is `](n]` (`tqrb`).
* Homonym selection via the reverse-mention index (see above).
* Assign state/case from syntax (prep→gen, suffix→cstr, vocative→nom) rather than
  defaults; flag final genitives wrongly marked construct.
* Tokeniser: detect and merge line-split words; treat `x` as broken in the
  reconstruction check.
