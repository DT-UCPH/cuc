# KTU 1.4 and 1.3 — agent review notes (2026-06-14)

Review of `reviewed/KTU 1.4.tsv` (all 8 columns) and `reviewed/KTU 1.3.tsv`
(all 6 columns), against CUC **0.2.7** auto-parsing. Sources: DULAT/UDB local
caches, the `dulat_cache__attestations` reverse index, CUC line texts, and the
UNP/TCS translations. KTU 1.3 was anchored to **Tania's gold-standard analyses**
in `reviewed/KTU_1.3_original.txt`. Helper scripts: `agent/scripts/reconcile_1_4.py`,
`agent/scripts/emit_1_4_col8.py`, `agent/scripts/build_1_3_from_tania.py`,
`agent/scripts/dulat_lookup.py`.

Both tablets now validate: every CUC 0.2.7 id present, every col4 a real DULAT
lemma (or `?`), every non-MERGE row reconstructs col2 from col3, 7-column layout.

---

## 0. Data-integrity repairs (flagged by Alexander)

Two serious defects in the agent's earlier column-by-column work on 1.4, both
fixed and guarded against going forward:

1. **20 dropped tokens.** A `grep`-style dedup while emitting columns silently
   removed tokens whose only displayed variant matched the filter (e.g. 129486
   `tṯb`, recurring `ṣḥ`/`lḥm`, `ks`, `ḫrṣ`, `dr`, `ḫrn`, `rmm`, `ttn`, `tšty`,
   `rḥq`, `ˤrb`, `qdm`, `ˤn`, `bnġlmt`). All restored. 1.5/1.6 had **no** drops.
2. **Invented DULAT entries / glosses.** col4 values that are not DULAT lemmas
   (e.g. `nblảt` → real lemma **`nblủ`** 'flame') and paraphrased glosses were
   replaced: col4 now always names a real DULAT lemma (or `?`), and col6 is
   DULAT's exact wording (auto-parser contextual gloss for that id+entry, else
   the DULAT primary translation). 815 glosses in 1.4 were corrected this way.
   1.5/1.6 col4 inventions also fixed (`šlyṭ` n. 'tyrant'; `krs` unglossed
   lemma; sense-number suffixes like `ʕm (I) 2` stripped).

---

## 1. Parser/linter defects observed

* **N-stem assimilated *n* order.** The auto-parser emits `(]n]` (e.g.
  `!t!(]n]qrb[`), which decodes to `tnqrb` — wrong. The reconstructing order is
  `](n]` (→ `tqrb`). Recurs throughout; applied correctly in the reviews
  (1.4 VIII:20 `tḫtan` = `!t!](n]ḫt(ʔ[…`, 1.3 `tšu` = `!t!](n]š(ʔ[&u`).
* **Preposition `ʕl` mis-tagged as `ʕl (III)` 'offspring'.** In `ša ġr ʕl ydm`
  (1.4 VIII:5) `ʕl` is the preposition `ʕl (I)` 'upon'.
* **`k` 'like' tagged as suffix `-k (I)`.** In `k lli` (1.4 VIII:19) `k` is the
  preposition `k (I)`.
* **Imperatives tagged as suffix-conjugation.** `rd`, `ql`, `rgm`, `ṯny`, `hbr`
  (1.4 VIII) and many 1.3 forms are G imperatives, not suffc.
* **Line-split words not merged.** Numerous words split across CUC lines are left
  as two unrelated tokens. 1.4 VIII alone: `yrdm`, `mdd`, `alp`, `kmn`, `kbd`,
  `qrdm`. Handled with the MERGE convention (both rows reconstruct the joined
  surface).
* **Unresolved tokens that DULAT does resolve:** `ksu` → `ks/śủ` 'throne';
  `rbt` → `rbbt` 'myriad' (defective spelling); `hšk` (1.3) → `/ḥ-š/ (I)`.
* **Broken signs (`x`).** Tokens containing `x` (illegible sign) need the `x`
  encoded as surface-only `&x` to reconstruct (e.g. `bnx` = `bn(I)/&x`).

---

## 2. KTU 1.4 — selected corrections against the auto-parser

| Ref | Token | Auto | Corrected | Evidence |
|---|---|---|---|---|
| VIII:1,10 | al | ảl (I) 'no' | **ảl (II)** asseverative | `idk al ttn pnm`, journey formula (DULAT) |
| VIII:5 | ˤl | ʕl (III) 'offspring' | **ʕl (I)** prep. 'upon' | `ʕl ydm` 'upon the hands' (DULAT) |
| VIII:12 | ksu | ? | **ks/śủ** 'throne' | `mk ksu ṯbth` (DULAT) |
| VIII:15 | ˤnn | 'herald' | ʕnn 'manservant, servant' | DULAT gloss |
| VIII:19 | k | -k (I) suffix | **k (I)** prep. 'like' | `k lli` 'like a kid' |
| VIII:24–26 | a‖lp, rbt, k‖mn | split / 'Lady' | **alp** 'thousand', **rbbt** 'myriad', **kmn** 'acre' | area formula (DULAT) |
| VIII:23–24 | md‖d | md (II) + rel. d | **mdd (I)** 'beloved' (MERGE) | `mdd ilm mt` (DULAT) |
| VIII:34–35 | q‖rdm | ? + 'to go down' | **qrd (I)** 'hero' pl. (MERGE) | `aliy qrdm` |
| VIII:47 | gpn / ugr | gpn (I) 'vine' | **gpn (III)** DN / **ủgr (II)** DN | messenger pair Gapnu-wa-Ugaru (cf. VII) |
| VIII:49 | spr | vb /s-p-r/ | spr (I) n. 'scribe' | colophon `spr ỉlmlk` |

Earlier-column highlights (already committed): `ḫrn/` faithful parse; N-stem
fixes (`tṯbr`, `tnḫtan`-type); MERGE pairs (`aṯrt`, `ilt`, `yšlḥ`, `mria`,
`aliyn`, `ḥln`, `ġlmh`); `mlk (I)` 'king' (not ptcpl); `dgn (II)` DN.

**Open convention point.** `ksu`/`lli` use the documented III-ʾ pattern
`ks(u/&u` / `ll(u/&i` (`discussion_points.md`); the `/&` vs `&/` order is still
unsettled there.

---

## 3. KTU 1.3 — Tania's gold standard vs CUC 0.2.7

Tania's review (`reviewed/KTU_1.3_original.txt`) is authoritative for the
morphological parsing (col3). It uses an **older id numbering** (136937–138120);
0.2.7 numbers 1.3 as **127265–128456**. Per project policy ("always update to the
latest version") the reviewed file uses 0.2.7 ids, with Tania's analyses aligned
by surface (difflib, 98.7% direct 1:1). DULAT col4/POS come from the auto-parse
and glosses from DULAT; Tania's inline `# …` notes are kept as comments.

### 3.1 Tokenization / notation differences (Tania ↔ 0.2.7)

| 0.2.7 id | 0.2.7 surface | Tania | Resolution |
|---|---|---|---|
| 127353 | pdry | pdr<y> (restored) | `pdry/` DN Pidray |
| 127390 | bnx | bn + x | `bn(I)/&x` (bn + broken sign) |
| 127538 | ṯlḥnt | ṯlḥ<t> | `ṯlḥn/t` 'table' |
| 127567 | ymxxxxxx | ym + xxxxxx | `ym(II)/&x…` |
| 127872 | tdˤ | td + ˤ | `!t!(ydˤ(I)[` 'she knows' |
| 127932 | bšmm | b + šmm | `b šm(m(I)/m` split |
| 128041 | lbˤl | l + bˤl | `l(I) bˤl(II)/` split |
| 128184–5 | w / tˤn | w  tˤn (one) | split: w + `!t!ˤn(y[` |
| 128211 | amḫṣxxx | amḫṣ + xxx | `!(ʔ&a!mḫṣ[&x&x&x` |
| 128456 | qrdm | (absent) | `qrd/m` 'heroes' (added) |

### 3.2 Sign-reading and aleph-notation differences

* **h / ḥ:** 0.2.7 `hkm` / `hšk` vs Tania `ḥkm` / `ḥš`. Kept the 0.2.7 surface,
  encoded the reading difference (`128248 ḥkm`; `127847 (ḥ&hš[+k`).
* **aleph a / ʔ:** Tania occasionally writes the consonantal aleph `ʔ` where
  0.2.7 writes `a` (e.g. `klat` vs `klʔt`); analyses adjusted to reconstruct the
  0.2.7 surface (`127372 kl(ʔ&a/t=`).
* **weak radicals:** a few analyses needed the unwritten radical encoded to
  reconstruct (`127688 ibġyh`, `127814 yˤnyn`).

### 3.2a Auto col4/POS corrected against Tania's gold col3

Merging Tania's col3 with the auto-parser's col4/POS is *not* safe on its own —
the auto-parse contradicted her in 41 places, and where they conflict Tania (the
expert) is authoritative. Every conflict was checked against DULAT + context:

* **Auto mis-tagged nouns as verbs/particles** (12): `brkm` 'knees' (not
  /b-r-k/), `ḏmr` 'warriors' (not vb), `rgm` 'word' ×3 (not /r-g-m/), `šlm`
  'peace' ×2, `rḥq` 'distant', `qrb` 'midst', `klt` 'bride' ×2, `ʕtk` 'the Savage
  One'.
* **Auto mis-tagged verbs as nouns/particles** (16): `ˤbd` 'serves', `tḫtṣb` 'does
  battle' ×3 (/ḫ-ṣ-b/, auto made it a noun "tḫtṣb"), `šbˤt` 'is sated' (/š-b-ʕ/ II,
  not the number 'seven'), `sk`/`št` 'pour/place!' (imperatives, not nouns),
  `ˤn` 'look!' (/ʕ-n/, not 'eye'), `lk` 'go!' ×2 (/h-l-k/, not prep. l), `anš`,
  `atm`, `šnt`.
* **Stem corrected to Tania's** (8): e.g. `šnst` D, `tgrš` D, `ˤtkt` G, `klt`
  /k-l-l/ D, `ištmdh` Gt, `ybˤr` G, `ymḥ` G-passive.

Two flagged conflicts were left as-is deliberately: `127282 d[` (relative
functor; Tania's `[` is a notation quirk that still reconstructs `d`) and
`128418 ṯbth` (the lexicalised noun `ṯbt` 'seat' in the formula `ksu ṯbth`, where
Tania's col3 shows the deverbal `/y-ṯ-b/` origin).

### 3.2b Noun case vs the analysis case-vowel (project-wide)

The realised case vowel in the analysis must agree with the POS case label —
`…/&u` = nom., `…/&i` = gen., `…/&a` = acc. — and a noun governed by a
preposition is genitive. Fixed the visible-vowel mismatches: `lli` (1.4 VIII:19,
after `k` 'like') acc.→**gen.**; `la` (1.3 V:18, object) nom.→**acc.** (Tania:
"a noun in accusative"); `mri` (1.3 I:8, `qṣ mri`) auto's "adj. f. pl. cstr.
nom."→**n. m. sg. cstr. gen.** (Tania: "likely passive participle"). Note: the
plural oblique `-im`/`-i` legitimately covers both gen. and acc., so those are
not flagged. A broader pass setting *all* prep-governed nouns to gen. (incl. the
unwritten-case majority) is a separate decision — case is mostly notional where
no aleph makes it visible.

### 3.3 Word-split tokens resolved (Tania's "[" fragments / merge-notes)

Tania flags tokenizer splits two ways: a `[`-closed fragment that can't stand
alone (e.g. `d[`) and explicit "merge/attach" notes. These are real splits — the
0.2.7 tokenizer cut one word into two — and were joined with the MERGE convention
(both rows carry the same analysis reconstructing the joined surface):

| ids | joined | analysis | DULAT |
|---|---|---|---|
| 127281+282 | ybrd | `!y!brd[` | /b-r-d/ 'he carves (a portion)' |
| 127385+386 | tmtḫṣ | `!t!m]t]ḫṣ[` | /m-ḫ-ṣ/ Gt 'she fights' |
| 127517+518 | btlt | `btlt/` | btlt 'Maiden' (btlt ˤnt) |
| 127772+773 | klbt | `klb(t/t` | klb (I) 'bitch (of the gods)' |
| 127792+793 | udnh | `udn/+h` | ủdn (I) 'his ear' |
| 128189+190 | bhtk | `b&ht(II)/+k` | bt (II) 'your house' |
| 128377+378 | riškm | `riš(I)/+km` | rỉš (I) 'your (pl.) head' |
| 128446+447 | hyn | `hyn/` | hyn (DN Hayyānu/Kothar) |

Two were left as Tania set them, per her own notes: **127732 `m`** ("MERGE WITH
NEXT?? or the previous one" — she is unsure) and **128088 `nn`** ("No! let us
keep it as it is, separately!"). These remain a project/tokenizer decision.

---

## 4. Cross-reviewer note

No prior reviewer covered 1.4 or 1.3 in the 0.2.7 format: Elijah's CSVs are the
KTU 2.x range and Ksenia reviewed 1.6. So 1.4 discrepancies are agent-vs-parser,
and 1.3 is agent-aligned-onto-Tania. The POS-granularity / DN-vs-n. / multiple-
glosses questions raised for 1.5/1.6 (see `KTU_1.5_agent_review_notes.md`) apply
here too.
