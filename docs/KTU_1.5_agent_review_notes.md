# KTU 1.5 III:2–VI:31 — agent review notes (2026-06-10)

Review of the remainder of KTU 1.5 in `reviewed/KTU 1.5.tsv` (cols. I–II were reviewed
manually by Alexander; everything from III:2 on was reviewed by the agent). Sources used:
DULAT/UDB local databases (`projects/dulat/app/data`, `projects/dulat/app/udb`), the
`ktu_to_dulat` reverse-mention index, CUC line texts, and the UNP and TCS translations
(`projects/dulat/app/modules`). Helper script: `agent/scripts/dulat_lookup.py`.

## Main corrections against the auto-parser

| Ref | Token | Auto-parser | Corrected to | Evidence |
|---|---|---|---|---|
| III:2 | rḥbt | rḥbt 'amphora' | rḥb (I) adj. f. 'wide' | DULAT cites `[r]ḥbt ṯbt` 'wide residence (?)' here s.v. rḥb (I) |
| III:7 | dt | d (parse `d`) | form dt of d (f. sg. / pl.) | DULAT forms table |
| III:8 | dk | d+k / /d-l-l/+k | /d-k(-k)/ Gpass 'be pounded' | DULAT cites `dk k kbkb[m` here |
| III:11 | ašṯt | NOT FOUND | /š-t/ G prefc. 1 c. sg. (`!(ʔ&a!š&ṯt[`) | DULAT cites `ảl ảšt` here; the ṯ left as surface-only (&ṯ), scribal error? |
| III:12 | ahpkk | `…hpk[k` (suffix unmarked) | `!(ʔ&a!hpk[+k` | suffix must be `+k` |
| III:12 | ḥ | /l-q-ḥ/ (non-reconstructable) | ? (broken word ḥ[…]) | parse did not reconstruct to surface |
| III:13,14,20,27,28 | lk(x) | l (I)+k 'to you' | /h-l-k/ G impv. `(hlk[` 'go!' | DULAT: `ṯmm lk` 'be appalled (?) and go'; UNP 'And go, O Gods' |
| III:16 etc. | mud | parse `mi/` (non-reconstructable) | `mud/` (mỉ/ủd) | reconstructability |
| IV:3 | lṭlb | NOT FOUND | l + /ṭ-l-b/ (split) | DULAT s.v. /ṭ-l-b/ cites `w l ṭlb` here |
| IV:6 | gh | spurious /y-t-n/ row | g + h 'his voice' | formula |
| IV:9 | ynpˤ | malformed `!y!](n](ypˤ[ˤ` | `!y!]n](ypˤ[` N prefc. | DULAT: ynpʕ = N of /y-p-ʕ/ |
| IV:10 | ṯmnt | `ṯmn(I)/` (non-reconstructable) | `ṯmn(I)/t` | reconstructability |
| IV:14 | mrġṯm | `mrġṯ/+m(I)` (pron. suffix) | `mrġṯ/m` pl. (alt. `~m` encl.) | -m is not a pronominal suffix here |
| IV:16 | krpnm | `krpn/` (missing m) | `krpn/m` pl. | reconstructability |
| IV:20 | tṯtnyn | `ṯny[ny+n` (malformed) | `!t!ṯ]t]ny[~n` Gt prefc. | DULAT form `tṯtny[n]` Gt prefc. |
| IV:24 | mn | mn (IV) '?' | mn (I) 'what?, who?' | DULAT cites mn (I) here |
| IV:27 | niṣ | (kept) | G act. ptcpl. | DULAT form nỉṣ G act. ptc. |
| V:5 | n | parsing empty | `+n` (-n (IV)) | DULAT cites ảštn with -n (IV) here |
| V:6 | qḥ | `lqḥ[` (non-reconstructable) | `(lqḥ[` impv. | hidden l |
| V:7 | ˤrptk, rḥk | missing fem-t / missing +k | `ˤrp(t/t+k`, `rḥ(I)/+k` | reconstructability |
| V:8,10,11 | ˤmk | ʕm (II) 'lineage' | ʕm (I) prep. 'with you' | DULAT cites ʕm (I) here; UNP/TCS 'with you' |
| V:10 | ar | parse `a/` (non-reconstructable) | `ar/` ả/ỉr 'light' | DULAT form ảr sg. of ả/ỉr |
| V:11 | tṭly | NOT FOUND | `&tṭly/` = DN ṭly, initial t dittography | KTU {t}ṭly; UNP 'Tallay' |
| V:12 | ttn | `ytn[` (no preformative) | `!t=!(ytn[` 2 m. sg. | journey formula |
| V:13 | ša | `nšʔ[` (non-reconstructable) | `!!(nš(ʔ[&a` impv. | tagging conventions example |
| V:14 | rd | `yrd[` (non-reconstructable) | `(yrd[` impv. | hidden y |
| V:15–16 | b y\|rdm | y given functor readings | y+rdm = yrdm, G act. ptcpl. pl. (MERGE) | word split across lines; TCS 'those who go down' |
| V:16 | tdˤ | `ydˤ(I)[` (no preformative) | `!t!(ydˤ(I)[:w` 3 m. pl. / `!t=!…` 2 m. sg. | TCS vs UNP readings kept as two rows |
| V:17 | mtt | `mt[t` (1 c.?) | `mt[t=` 2 m. sg. | 'that you are dead' |
| V:18 | yuhb | `ʔhb[b:d` (malformed) | `!y!(ʔ&uhb[` G (alt. D) | DULAT: yủhb G or D prefc. |
| V:20 | ˤmnh | `ˤm(I)+h`/`+nh` | `ˤm(I)+nh=` 3 f. sg. | 'he lies with her' (the heifer) |
| V:21 | tšˤly | NOT FOUND | `!t!]š]ˤly[` Š (alt. Špass) | DULAT cites tš[ʕ]ly s.v. /ʕ-l-y/; Š/Špass attested |
| V:22 | tldn | `yld[+n` "N suffc." | `!t!(yld[~n` G prefc. 3 f. sg. | 'she bears a boy' |
| V:23 | šlbšn | `]š]lbš[n` | `]š]lbš[+n` Š suffc. + suff. | DULAT: -n (IV) 'him' |
| VI:1 | tgly | `!t!](n]gly[` | `!t!gly[` G (DULAT: G or N) prefc. 3 m. du. | formula; restored line |
| VI:2 | mlk | ptcpl. of /m-l-k/ or mlk (II) | mlk (I) n. 'king' | 'abode of the King' (so also Ksenia at 1.6 I:36) |
| VI:3–4 | sbn+y | `sbb[` (non-reconstructable) | `sb(b[ny` G suffc. 1 c. du. (MERGE) | TCS 'We have done the rounds'; sbn+[y] split across lines |
| VI:4 | ˤdk | `ˤd(I)` (non-reconstructable) | `ˤd(I)~k` prep + encl. -k | DULAT cites ʕd ksm mhyt here |
| VI:5, VI:8 | mġny | `mġy[y` (non-reconstructable) | `mġ(y[ny` G suffc. 1 c. du. | 'we (two) arrived' |
| VI:8–9 | a\|rṣ | unparsed | arṣ (MERGE, split across lines) | |
| VI:11 | ilxx | NOT FOUND | ỉl (I) DN + broken tail | UNP 'Beneficent El the Benign' |
| VI:14 | yṣq | "suffc." | prefc. 3 m. sg. | y-preformative |
| VI:14 | arṣm | `arṣ/+m(I)` | `arṣ/~m` encl. | -m is enclitic, not suffix |
| VI:15,16 | rišh, qdqdh | missing `+` | `riš(I)/+h`, `qdqd/+h` | suffix marking |
| VI:17,31 | mizrtm | `mizr(t/tm` "sg." | `mizr(t/t~m` + encl. (alt. du. `…/tm`) | DULAT cites -m (II) here |
| VI:24 | dgn | dgn (I) 'grain' | dgn (II) DN 'Dagan' | bn dgn 'Son of Dagan' |
| VI:24 | aṯr | adv. 'then' | prep. 'after' | 'After Baal I shall descend' |
| VI:25 | ard | `yrd[` (non-reconstructable) | `!(ʔ&a!(yrd[` 1 c. sg. | El's speech |
| VI:26 | ttlk | `h]t]lk[` (malformed) | `!t!]t](hlk[` Gt prefc. 3 f. sg. | DULAT cites /h-l-k/; Gt with elided h |
| VI:28 | lkbd | NOT FOUND | `l(I) kbd(I)/` (Split) | parallel VI:27 l kbd arṣ |

Also fixed a pre-existing formatting slip in the manually-checked portion: the `štp` row
(I:25, id 139886) was missing one field (gloss column), breaking the 7-column layout.

## Points for discussion (discrepancies between reviewers / open conventions)

1. **POS granularity.** Alexander (1.5 I–II) writes full POS: `vb G prefc. 2 m. sg.`,
   `n. m. sg. abs. acc.`. Ksenia (1.6) mostly stops at `vb G prefc.` / `n. m. sg.` without
   person/number/case. Elijah (KTU 2.x CSVs) likewise, and he marks mood in parentheses
   (`vb G prefc. (Jussive)`), a notation not used in 1.5. The agent followed Alexander's
   fuller style. Needs one agreed standard.
2. **Imperative person marking.** Alexander has both `vb G impv. 2` (II:8 rgm) and
   `vb G impv. m. sg.` (I:22 ṣḥn). The agent used `vb G impv. m. sg./du./pl.`.
3. **Weak first radical in parsing.** Ksenia explicitly asks (1.6 I:2, td): "how do we mark
   the weak -y- in parsing?" Her `!t!d(II)[` for /y-d-y/ (II) omits the hidden radical; the
   agent guide (§3.4) requires `(y` (so `!t!(yd(y(II)[`-style). In 1.5 the agent wrote
   `!y!(ydy(II)[` (VI:18), `!t!(ydˤ(I)[` (V:16), `(hlk[` (III:13ff.), `(lqḥ[`, `(yrd[`.
4. **1 c. du. suffix conjugation ending.** The paradigm table in `Tagging conventions.md`
   gives 1 c. du. = `qtl[n=` or `qtl[y`, but the forms sbny (VI:3–4) and mġny (VI:5, 8)
   write both n and y. The agent encoded `[ny` (e.g. `sb(b[ny`, `mġ(y[ny`). The convention
   table should be extended or the analysis changed.
5. **ab šnm (VI:2).** DULAT: šnm = DN Šunama (so TCS "father of Šunama"); UNP "Father of
   Years"; Ksenia at the 1.6 I:36 parallel chose šnt (I) "year" (`šn/m`). Both readings kept
   as rows in 1.5; needs a project-wide decision.
6. **qn ḏrˤh (VI:20 // 1.6 I:4).** DULAT has only qn 'cane' ("his humerus" in this line).
   Ksenia used a non-existent homonym `qn(II)` with gloss "name of part of the body" and asks
   whether qn ḏrˤh should be treated as one unit ("collarbone?").
7. **DN vs n. for ỉl / bʕl.** Ksenia tags il in formulae (ḏd il, nrt ilm špš) as `n. m.`
   and bˤl as `n. m. / DN`; Alexander tags the god as `DN m. sg. abs. <case>`. The agent
   followed Alexander. Same question for dgn (Ksenia: parsing dgn(II)/ but DULAT column
   "dgn (I)" + gloss 'grain' — internally inconsistent row).
8. **Multiple glosses.** Ksenia keeps numbered alternative glosses as duplicate rows
   ("1. to repeat for the third time" / "2. to plough"; also asks "should we leave only one
   meaning?"). Alexander keeps one gloss and uses extra rows only for morphologically
   distinct variants, with source attributions (Wyatt, UNP, DULAT…). The agent followed
   Alexander.
9. **Line-numbering shift in col. IV.** DULAT citations for 1.5 IV are consistently one
   line lower than the CUC/KTU numbering used in this project (DULAT IV:n = CUC IV:n+1),
   e.g. DULAT "1.5 IV 2" (w l ṭlb) = CUC IV:3. Relevant when checking DULAT references.
10. **dbr in the šd šḥlmmt formula.** DULAT classifies dbr here as dbr (II) "plague"
    (rendering "Pestilence" as a quasi-toponym); UNP "outback", TCS "pasture land".
    Kept dbr (II) with the translations noted.
11. **ˤd lḥm šty ilm (IV:13).** Two defensible readings kept: ʕd (I) conj. "while"
    (UNP) and ʕd (III) "throne/table". Auto-parser's first choice had been ʕd (III).
12. **Ksenia's file format.** Her 1.6 file is space-padded TSV (columns padded with
    spaces); this branch uses plain TSV. Will normalize to plain TSV when reviewing 1.6.
13. **mhyt (VI:5).** DULAT tags the form in this line as plural; encoded `mhy(t/t=`.
14. **hmlt (VI:24).** Tagged `n. f. pl. tant.` per the labeling guide (§7.13); Ksenia
    has `n. f. pl.` at 1.6 I:7.

## Unresolved tokens (left as `?`)

- III: x (140042), empty ids 140051/140083/140094/140098/140120, ḥ[… (140074),
  xxxṯ, xxxkṯ; k at broken right edge (III:6, III:7) tagged k (I) with caveat.
- IV: xxy, xxxxx, ˤ (IV:2), empty 140132, a[… (IV:10), x (IV:11), li[… (IV:22),
  x (IV:23), tlšx, px.
- V: head-of-column lacunae (140200, 140203, 140206, 140209, 140212), xxxx (V:24),
  xxxxxt (V:25), š… (V:26), t[h]rn (V:22 — reading known from KTU restoration but
  the surface is too broken to parse).
- VI: xxṣt, xxḥ (VI:4).

---

# KTU 1.6 (full tablet) — agent review notes (2026-06-10)

Reviewed `reviewed/KTU 1.6.tsv` on this branch (auto-parser version, token ids 130806–131832),
using the same sources as for 1.5, plus Kseniia's review on `origin/review/1.6-Kseniia`.

## Structural finding: two different token-id series

- This branch's `KTU 1.6.tsv` uses ids **130806–131832** (1027 tokens).
- Kseniia's file uses ids **140451–141470** (1016 tokens), continuing the 1.5 series
  (1.5 ends at 140450). The two id series do not overlap and cannot be joined by id.
- Kseniia's file also **changes tokenization** in places: she merged kgmn (I:21),
  aṯrtym (I:45), amlkn (I:46), tdrynn (II:32–33), dpid (III:10), kˤṣr (VI:3), wˤn (VI:9),
  t[ṣ]h (II:11), xxxxbl (VI:41); changed the surface abn→ab (I:2) and lxˤglh→l (II:7);
  and **deleted two tokens**: ylḥn (I:48) and pi (I:49). Token identity should be decided
  project-wide before merging the two lines of work.
- Her file is space-padded TSV; this branch keeps plain TSV.

## Main corrections against the auto-parser (selection)

- I:46 am+lkn = amlkn '(I) will make (him) king' — scribal divider am{.}lkn (KTU); -n (IV).
- I:48 ydˤ ylḥn — DULAT PN pair 'the Savant Shrewd' (kept verb reading as alternative).
- I:49–50 pi+d = pid (split across lines; Ksenia deleted the pi token instead).
- I:40–41 ṣb+rt = ṣbrt 'clan' (split across lines).
- II:11–12 tṣ+ḥ = tṣḥ; II:32–33 tdry+nn; IV:18–19 t+bl = tbl (/y-b-l/, per DULAT);
  V:15–16 rḥ+m = rḥm 'two millstones'; VI:15–16 kl+yy = klyy; VI:24–25 tmtḫ+ṣ = tmtḫṣ
  (Gt of /m-ḫ-ṣ/); VI:30–31 y+dd = ydd; VI:58 yrgb+bˤl = PN yrgbbˤl — all MERGE pairs.
- I:10 udmˤt = prosthetic aleph !(ʔ&u!dmˤ(t/t= (the conventions' own example; auto and
  Ksenia both had non-reconstructing dmˤt/).
- I:16 ṣpˤn: scribal ˤ marked &ˤ (Ksenia used (ˤ — wrong direction of the marker).
- II:9/II:30 tiḫd = !t!(ʔ&iḫd[ (auto/Ksenia parses did not reconstruct).
- II:14 taršn = 2 f. sg. (Mot addressing Anat).
- II:15 itlk = Gt of /h-l-k/ with elided h (!(ʔ&i!]t](hlk[).
- II:19 mġt = mġ(y[t (weak-final SC -t rule, guide §3.5).
- III:7 nbtm: -m is enclitic (-m (I) per DULAT), not plural.
- IV:1 etc. ˤnt in pl ˤnt šdm = ʕn (II) 'furrow' (DULAT direct citation), not Anat/eye/now.
- IV:6 ttbˤ = /t-b-ʕ/ prefc. (auto and Ksenia: NOT FOUND).
- V:3 dkym: DULAT segments d k ym 'those who are like Yam'.
- V:4 ymṣḫ = /m-ṣ-ḥ/ 'to pull' (auto: NOT FOUND).
- V:12 qlt = qlt (I) n. 'vileness' (DULAT), not /q-l/ 'fall'.
- V:12ff. pht = ph(y[t '(because of you) I experienced' (Mot's complaint series),
  with the following words as infinitives (dry, šrp, ṭḥn, ġly, drˤ).
- V:17–18 b š | b šdm and VI:10–11 s | spuy: scribe broke a word at line end and rewrote
  it in full on the next line; the orphan fragment is tagged ? with a note.
- VI:12 yṯb = /ṯ-b/ 'return' (DULAT), not /y-ṯ-b/ 'sit'.
- VI:13 yšl = scribal for yšu (l for u, marked (ʔ&l).
- VI:17ff. ˤz = /ʕ-z(-z)/ suffc.; the duel verbs yngḥn/ynṯkn/ymṣḫn/ytˤn tagged 3 m. du.
  (reciprocal).
- VI:44 trmmt: DULAT lemma trmt, second m scribal (tr{m}mt).
- VI:46f. tḥtk: both readings kept (/ḥ-t-k/ 'you rule' and tḥt+k 'under you' — DULAT
  cites both).
- VI:54–58 colophon: PN/GN tagging (Ilimilku, Shubanite, Attanu the diviner, Niqmaddu,
  Yargub-Baʿlu, Ṯarrumannu).

## Discrepancies with Kseniia's review (for discussion)

1. **Weak radicals not marked**: her ttn (`!t!tn[`), tdˤ-type forms, tšˤlynh (`(n` for a
   surface n), itlk (`h]t]lk[`), mġt (`mġy[t`), šd impv. (`šdy[`), pht (`phy[t`), tiḫd
   (`!t!ʔḫd[d`), taršn (`!t!ʔrš[šn:d`) do not reconstruct to the surface; the agent
   versions follow guide §3.4–3.5.
2. **tṭbḫ tagged "suffc."** in the sacrifice series (I:18–28) though parsed `!t!ṭbḫ[`
   (prefc. preformative); agent: prefc. 3 f. sg.
3. **aṯrt (V:1)**: Ksenia ảṯrt (I) 'back part of the head'; agent: the goddess (bn aṯrt).
4. **qlt (V:12)**: Ksenia /q-l/ 'fall'; DULAT cites qlt (I) 'vileness'.
5. **rḥ (V:15)**: Ksenia rḥ (I) 'wind' (+ l (I) for the orphan m); DULAT rḥ (III)
   'millstone' du., m belongs to it (MERGE).
6. **š (V:17)**: Ksenia š 'ram'; agent: incomplete šdm rewritten in V:18.
7. **kd (II:3–4)**: she kept kd (I) 'jar' and kd (II) rows; DULAT cites kd (II) (agent
   kept kd (II) with a note).
8. **dgn / il / bˤl / špš class**: as in 1.5 (DN vs n.), plus her šnm = šnt 'years' at
   1.6 I:36 vs DULAT DN Šunama (both kept as rows at the parallel and at I:36 here).
9. **ˤd (I:9)**: agreement — both chose ʕd (I) conj. against the auto-parser's
   ʕd (III) 'throne'.
10. **Her open questions** preserved in her comments (weak -y- marking; dot-above-k in
    idk I:32; qn ḏrˤh 'collarbone'; one meaning vs synonyms) — answered implicitly by
    the agent's choices above; to be confirmed at the team discussion.

## Unresolved tokens in 1.6 (left as `?`)

I:30 pšt (crux pštbm/t!tbm); I:48 broken ix at IV:6; IV:1 head lacunae (II:1–2 lxxxxxxxxxx,
ḥxxxxxxxxx); IV:22 a; IV:25–28 (x, dr-context, r, x, empty IV:29); V:23 aḥẓxxxxl;
V:24 xdxx; V:27–30 (štxx, dl, š, empty); VI:1–8 lacunae (xxxxxxx ×2, xxxxx, u, dnh, xxxxxxxxx,
xxxxxx ×2, xxu); VI:35–42 lacunae (xxxx ×3, xxxxxxxx, xxxxxxx, bl, xxšu); VI:44 s (orphan).
