# Discussion points


## Words broken by a line break

[KTU3 1.3 II 5](https://ugaritic-dict-1566828bafc2.herokuapp.com/texts/page/?file=udb_1_3.html&anchor=v-3-II-5)

```
bšt . ġr . whln . ʿnt . tm
tḫṣ . bʿmq . tḫtṣb . bnx
```

[KTU 1.5 V 5](https://ugaritic-dict-1566828bafc2.herokuapp.com/texts/page/?file=udb_1_5.html&anchor=v-5-V-5)

```
140214	ašt	!(ʔ&a!št[	/š-t/	vb	to place	OR with next token: aštn (UDB R1; Del Olmo V:5 ast.n)
140215	n	-n(IV)	-n (IV)	pers. pn.	(for) him	enclitic -n (3ms/3fs); some readings merge with previous as aštn
```

[KTU3 1.5 I 14](https://ugaritic-dict-1566828bafc2.herokuapp.com/texts/page/?file=udb_1_5.html&anchor=v-5-I-14)

```
130186	np	np(š(I)/	npš (I)	n. f. sg. abs. nom.	throat	Merge with the following?
130187	š	&š	?	?	?	
130188	npš	npš(I)/	npš (I)	n. f. sg. cstr. nom.	throat	
```

In KTU 1.4 VIII the descent formula has six: `y+rdm`=yrdm, `md+d`=mdd, `a+lp`=alp, `k+mn`=kmn,`k+bd`=kbd, `q+rdm`=qrdm.

KTU 1.1 `y+kbdnh`=ykbdnh.

## Missing word dividers

Sometimes word dividers are genuinely missing, e.g. because of the scribal error.

One 0.2.7 token currently holds two lexemes. I currently tag them as multi-lexeme
(space in col3, `;` in col4). Should these become two ids instead?

[KTU3 1.4 VII 54](https://ugaritic-dict-1566828bafc2.herokuapp.com/texts/page/?ref=KTU+1.4&anchor=v-4-VII-54)

```
129957	bnġlmt	b~n ġlmt(II)/	b; ġlmt (II)	prep. + encl. -n; n. f. sg. abs.	in; concealment	bn ġlmt 'in the gloom' (// bn ẓlmt)
```

KTU 1.1 III:24

```
126073	lpˤn	l(I) pˤn/	l (I); pʕn	prep.; n. f. du. cstr. gen.	to; foot	l pˤn 'to the feet of'  (KTU 1.1)
```

More:

```
127932	bšmm	b šm(m(I)/m	b; šmm (I)	prep.; n. m. du. abs.	in; heavens	b šmm 'in the heavens'  (KTU 1.3)
128041	lbˤl	l(I) bˤl(II)/	l (I); bʕl (II)	prep.; DN m. sg. gen.	to; Baʿlu	l bˤl 'to Baal'  (KTU 1.3)
127681	wl	w-l(II)	w; l (II)	conj.; neg. adv.	and; not	Tania: "SPLIT IN TWO WORDS!!"  (KTU 1.3)
```

[lalpm in KTU 1.4 I 27](https://ugaritic-dict-1566828bafc2.herokuapp.com/texts/page/?file=udb_1_4.html&anchor=v-4-I-27)

## Words (and IDs) to be merged

One word split across two ids (no line break). Currently handled with the MERGE convention. See older versions of 1.3.

## Scribal anticipation (different from a simple line break)

Examples:

[KTU 1.3 III 9](https://ugaritic-dict-1566828bafc2.herokuapp.com/texts/page/?ref=KTU+1.3&anchor=v-3-III-9)

```
KTU3 1.3 III 9
w . ʿrbn . lpʿn . ʿnt . hbr . w

KTU3 1.3 III 10
wql . tštḥwy . kbd . hyt
```

[KTU 1.6 IV:23](https://ugaritic-dict-1566828bafc2.herokuapp.com/texts/page/?ref=KTU+1.6&anchor=v-6-IV-22)

```
131477	a	?	?	?	?	Incomplete an rewritten in full at the start of the next line (scribal anticipation).
# KTU 1.6 IV:23						
131478	an	an(I)	ản (I)	pers. pn.	I	
131478	an	an(II)	ản (II)	adv.	wherever	
```

[KTU 1.6 VI:11](https://ugaritic-dict-1566828bafc2.herokuapp.com/texts/page/?ref=KTU+1.6&anchor=v-6-VI-10)

```
131644	s	?	?	?	?	Incomplete spuy rewritten in full at the start of the next line (scribal anticipation).
# KTU 1.6 VI:11						
131645	spuy	!!spuy[/	/s-p-ʔ/	vb G inf.	to devour, eat, consume > to be consumed > fodder > give to eat > to feed, to serve > to eat
```

[KTU 1.19 IV:11](https://ugaritic-dict-1566828bafc2.herokuapp.com/texts/page/?ref=KTU+1.19&anchor=v-19-IV-10)

```
136840	pẓ	?	?	?	?	Incomplete pẓġm rewritten in full at the start of the next line (scribal anticipation).
# KTU 1.19 IV:11						
136841	pẓġm	pẓġ/m	pẓġ	n. m. pl. cstr. nom.	one who lacerates	
```


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

## /& vs &/

The /& vs &/ order is still unsettled in the 'Tagging conventions.md', see "Suffixes and enclitics" section, `ks(u/&u` vs. `rp(u&/m`.

Documentation also has 

```
TODO: maybe think about other marker than !! for the [prosthetic aleph] prefix, because this is used for verbal prefixes.
```

## Broken signs (`x`)

Decision applied in my manual review: do not encode `x` (illegible sign) in
the morphology — the analysis carries only the readable part, not the x's.

```
130076	bnx	bn(I)/	bn (I)	...	son	
127567	ymxxxxxx	ym(II)/	ym (II)	...	sea	
127492	ḏxxmr	ḏxxmr	?	?	?	(heavily broken: surface only)
129881	hdxt	hd/ t	hd(d)	...	Haddu	(broken middle sign)
```

## Noun case

Do we want to label cases in the additional 'POS' column?

For pl./du. grammars collapse gen.+acc. into one oblique form — do we still label them `gen.`/`acc.` by syntactic role, or introduce `obl.`?

## Versioning / id alignment

Tania's 1.3 review uses an older id numbering (136937…); 0.2.7 numbers 1.3 as
127265–128456. I aligned by surface (≈98.7% direct) and kept the 0.2.7 ids. 

Does id-version mapping exist anywhere?


