"""Emit the reviewed block for KTU 1.4 column VIII (descent-to-Mot + colophon).

Replaces the raw auto-seeded VIII block in reviewed/KTU 1.4.tsv with a reviewed
one. Glosses are derived from the same DULAT-faithful authority used by
reconcile_1_4.py (auto contextual gloss for that id+entry, else DULAT primary
translation). Validates id-completeness, col4 validity and reconstructability.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reconcile_1_4 as R  # noqa: E402

REV = R.REV

# Each entry: ("H", "VIII:N") header, or
# (id, surface, analysis, col4, pos, comment)  -- gloss derived from col4.
ROWS = [
    ("H", "VIII:1"),
    ("129976", "idk", "idk", "ỉdk", "narrative adv. functor", "idk al ttn pnm 'then they set their faces'."),
    ("129977", "al", "al(II)", "ảl (II)", "asseverative functor", "Asseverative al (not negative); the journey formula."),
    ("129978", "ttn", "!t!(ytn[:w", "/y-t-n/", "vb G prefc. 3 m. pl.", "ttn pnm 'they set the face'."),
    ("129979", "pnm", "pn(m/m", "pnm", "n. m. pl. abs. acc.", ""),
    ("H", "VIII:2"),
    ("129980", "ˤm", "ˤm(I)", "ʕm (I)", "prep.", "toward"),
    ("129981", "ġr", "ġr(I)/", "ġr (I)", "n. m. sg. cstr. gen.", ""),
    ("129982", "trġzz", "trġzz/", "trġzz", "TN sg. abs. gen.", "Mt. Targuzizu."),
    ("H", "VIII:3"),
    ("129983", "ˤm", "ˤm(I)", "ʕm (I)", "prep.", ""),
    ("129984", "ġr", "ġr(I)/", "ġr (I)", "n. m. sg. cstr. gen.", ""),
    ("129985", "ṯrmg", "ṯrmg/", "ṯrmg", "TN sg. abs. gen.", "Mt. Tharumagi."),
    ("H", "VIII:4"),
    ("129986", "ˤm", "ˤm(I)", "ʕm (I)", "prep.", ""),
    ("129987", "tlm", "tl(I)/m", "tl (I)", "n. m. du. cstr. gen.", "tlm 'the two hills'."),
    ("129988", "ġṣr", "ġṣr/", "ġṣr", "n. m. sg. cstr. gen.", "ġṣr arṣ 'the edge of the earth'."),
    ("129989", "arṣ", "arṣ/", "ảrṣ", "n. f. sg. cstr. gen.", ""),
    ("H", "VIII:5"),
    ("129990", "ša", "(nš(ʔ[&a", "/n-š-ʔ/", "vb G impv. m. sg.", "ša 'lift!'."),
    ("129991", "ġr", "ġr(I)/", "ġr (I)", "n. m. sg. abs. acc.", ""),
    ("129992", "ˤl", "ˤl(I)", "ʕl (I)", "prep.", "ʕl ydm 'upon (both) hands' (prep., not ʕl III)."),
    ("129993", "ydm", "yd(I)/m", "yd (I)", "n. f. du. cstr. gen.", ""),
    ("H", "VIII:6"),
    ("129994", "ḫlb", "ḫlb(I)/", "ḫlb (I)", "n. m. sg. abs. acc.", ""),
    ("129995", "l", "l(I)", "l (I)", "prep.", ""),
    ("129996", "ẓr", "ẓr(I)/", "ẓr (I)", "n. m. sg. cstr. gen.", "l ẓr rḥtm 'upon the back of the palms'."),
    ("129997", "rḥtm", "rḥt/m", "rḥt", "n. f. du. abs. gen.", ""),
    ("H", "VIII:7"),
    ("129998", "w", "w", "w", "conj.", ""),
    ("129999", "rd", "(yrd[", "/y-r-d/", "vb G impv. m. sg.", "rd 'go down!' (hidden y)."),
    ("130000", "bt", "bt(II)/", "bt (II)", "n. m. sg. cstr. acc.", "bt ḫpṯt arṣ 'the netherworld house'."),
    ("130001", "ḫpṯt", "ḫpṯ(t/t", "ḫpṯt", "n. f. sg. cstr. gen.", "ḫpṯt: the netherworld; DULAT gives no gloss."),
    ("H", "VIII:8"),
    ("130002", "arṣ", "arṣ/", "ảrṣ", "n. f. sg. cstr. gen.", ""),
    ("130003", "tspr", "!t!spr[", "/s-p-r/", "vb G prefc. 2 m. sg.", "tspr b yrdm arṣ 'be numbered among those who go down'."),
    ("130004", "b", "b", "b", "prep.", "among"),
    ("130005", "y", "yrd[m", "/y-r-d/", "vb G act. ptcpl. m. pl. cstr. gen.", "MERGE WITH THE NEXT: y+rdm = yrdm 'those who go down', split VIII:8/9."),
    ("H", "VIII:9"),
    ("130006", "rdm", "yrd[m", "/y-r-d/", "vb G act. ptcpl. m. pl. cstr. gen.", "MERGE WITH THE PREVIOUS."),
    ("130007", "arṣ", "arṣ/", "ảrṣ", "n. f. sg. abs. gen.", ""),
    ("H", "VIII:10"),
    ("130008", "idk", "idk", "ỉdk", "narrative adv. functor", ""),
    ("130009", "al", "al(II)", "ảl (II)", "asseverative functor", ""),
    ("130010", "ttn", "!t!(ytn[:w", "/y-t-n/", "vb G prefc. 3 m. pl.", ""),
    ("H", "VIII:11"),
    ("130011", "pnm", "pn(m/m", "pnm", "n. m. pl. abs. acc.", ""),
    ("130012", "tk", "tk/", "tk", "n. m. sg. cstr. acc.", "tk qrth 'into the midst of his city'."),
    ("130013", "qrth", "qr(t(I)/t+h", "qrt (I)", "n. f. sg. cstr. gen. + 3 m. sg. suff.", "his city"),
    ("H", "VIII:12"),
    ("130014", "hmry", "hmry/", "hmry", "TN sg. abs. gen.", "His city Hmry ('Muddy')."),
    ("130015", "mk", "mk(I)/", "mk (I)", "n. m. sg. abs. nom.", "mk ksu ṯbth 'a pit is the throne of his seat'."),
    ("130016", "ksu", "ks(ủ/&u", "ks/śủ", "n. m. sg. cstr. nom.", "ksu 'throne' (DULAT ks/śủ; was unresolved)."),
    ("H", "VIII:13"),
    ("130017", "ṯbth", "ṯb(t/t+h", "ṯbt", "n. f. sg. cstr. nom. + 3 m. sg. suff.", ""),
    ("130018", "ḫḫ", "ḫḫ/", "ḫḫ", "n. m. sg. abs. nom.", "ḫḫ arṣ nḥlth 'mire is the land of his possession'."),
    ("130019", "arṣ", "arṣ/", "ảrṣ", "n. f. sg. abs. nom.", ""),
    ("H", "VIII:14"),
    ("130020", "nḥlth", "nḥl(t/t+h", "nḥlt", "n. f. sg. cstr. nom. + 3 m. sg. suff.", "his possession"),
    ("130021", "w", "w", "w", "conj.", ""),
    ("130022", "nġr", "nġr[", "/n-ġ-r/", "vb G impv. m. sg.", "w nġr 'and beware!'."),
    ("H", "VIII:15"),
    ("130023", "ˤnn", "ˤnn/", "ʕnn", "n. m. du. cstr. gen.", "ʕnn ilm 'O servants of the gods' (the messengers)."),
    ("130024", "ilm", "il(I)/m", "ỉl (I)", "n. m. pl. abs. gen.", ""),
    ("130025", "al", "al(I)", "ảl (I)", "neg. functor", "al tqrb 'do not approach'."),
    ("H", "VIII:16"),
    ("130026", "tqrb", "!t!qrb[:w", "/q-r-b/", "vb G prefc. 2 m. du.", "'do not approach'."),
    ("130027", "l", "l(I)", "l (I)", "prep.", ""),
    ("130028", "bn", "bn(I)/", "bn (I)", "n. m. sg. cstr. gen.", "bn ilm mt 'the divine Mot'."),
    ("130029", "ilm", "il(I)/m", "ỉl (I)", "n. m. pl. cstr. gen.", ""),
    ("H", "VIII:17"),
    ("130030", "mt", "mt(II)/", "mt (II)", "DN m. sg. abs. gen.", ""),
    ("130031", "al", "al(I)", "ảl (I)", "neg. functor", "al yʕdbkm 'lest he put you'."),
    ("130032", "yˤdbkm", "!y!ˤdb[+km", "/ʕ-d-b/", "vb G prefc. 3 m. sg. + 2 m. du. suff.", "'lest he place you two'."),
    ("H", "VIII:18"),
    ("130033", "k", "k(I)", "k (I)", "prep.", "k imr 'like a lamb'."),
    ("130034", "imr", "imr(I)/", "ỉmr (I)", "n. m. sg. abs. acc.", ""),
    ("130035", "b", "b", "b", "prep.", ""),
    ("130036", "ph", "p(III)/+h", "p (III)", "n. m. sg. cstr. gen. + 3 m. sg. suff.", "his mouth"),
    ("H", "VIII:19"),
    ("130037", "k", "k(I)", "k (I)", "prep.", "k lli 'like a kid' (prep., not suffix)."),
    ("130038", "lli", "ll(u&i/", "llủ", "n. m. sg. abs. acc.", ""),
    ("130039", "b", "b", "b", "prep.", ""),
    ("130040", "ṯbrn", "ṯbrn(I)/", "ṯbrn (I)", "n. m. sg. cstr. gen.", "ṯbrn qnh 'the gullet of his throat'."),
    ("H", "VIII:20"),
    ("130041", "qnh", "qn/+h", "qn", "n. m. sg. cstr. gen. + 3 m. sg. suff.", "his windpipe"),
    ("130042", "tḫtan", "!t!](n]ḫt(ʔ[&a&n", "/ḫ-t-ʔ/", "vb N prefc. 2 m. du.", "tḫtan 'lest you two be crushed' (N-stem; energic -an)."),
    ("H", "VIII:21"),
    ("130043", "nrt", "nr(t(I)/t", "nrt (I)", "n. f. sg. cstr. nom.", "nrt ilm špš 'the lamp of the gods, Šapšu'."),
    ("130044", "ilm", "il(I)/m", "ỉl (I)", "n. m. pl. cstr. gen.", ""),
    ("130045", "špš", "špš/", "špš", "DN f. sg. abs. nom.", ""),
    ("H", "VIII:22"),
    ("130046", "ṣḥrrt", "ṣḥrr[t", "/ṣ-ḥ-r-r/", "vb G suffc. 2 f. sg.", "špš ṣḥrrt 'Šapšu, you scorch'."),
    ("130047", "la", "la/", "lả", "n. m. sg. cstr. acc.", "lả šmm 'the strength of the heavens'."),
    ("H", "VIII:23"),
    ("130048", "šmm", "šm(m(I)/m", "šmm (I)", "n. m. du. abs. gen.", ""),
    ("130049", "b", "b", "b", "prep.", ""),
    ("130050", "yd", "yd(I)/", "yd (I)", "n. f. sg. cstr. gen.", "b yd 'in the power of'."),
    ("130051", "md", "mdd/", "mdd (I)", "n. m. sg. cstr. gen.", "MERGE WITH THE NEXT: md+d = mdd 'beloved', split VIII:23/24."),
    ("H", "VIII:24"),
    ("130052", "d", "mdd/", "mdd (I)", "n. m. sg. cstr. gen.", "MERGE WITH THE PREVIOUS."),
    ("130053", "ilm", "il(I)/m", "ỉl (I)", "n. m. pl. cstr. gen.", "mdd ilm mt 'the Beloved of the gods, Mot'."),
    ("130054", "mt", "mt(II)/", "mt (II)", "DN m. sg. abs. gen.", ""),
    ("130055", "b", "b", "b", "prep.", ""),
    ("130056", "a", "alp/", "ảlp (II)", "num.", "MERGE WITH THE NEXT: a+lp = alp 'thousand', split VIII:24/25."),
    ("H", "VIII:25"),
    ("130057", "lp", "alp/", "ảlp (II)", "num.", "MERGE WITH THE PREVIOUS."),
    ("130058", "šd", "šd(I)/", "šd (I)", "n. m. sg. abs. gen.", "alp šd 'a thousand acres'."),
    ("130059", "rbt", "rb(bt/", "rbbt", "num.", "rbt 'myriad' (DULAT rbbt, defectively written)."),
    ("130060", "k", "kmn/", "kmn (I)", "n. m. sg. abs. gen.", "MERGE WITH THE NEXT: k+mn = kmn 'acre', split VIII:25/26."),
    ("H", "VIII:26"),
    ("130061", "mn", "kmn/", "kmn (I)", "n. m. sg. abs. gen.", "MERGE WITH THE PREVIOUS."),
    ("130062", "l", "l(I)", "l (I)", "prep.", "l pʕn mt 'to the feet of Mot'."),
    ("130063", "pˤn", "pˤn/", "pʕn", "n. f. du. cstr. gen.", ""),
    ("130064", "mt", "mt(II)/", "mt (II)", "DN m. sg. abs. gen.", ""),
    ("H", "VIII:27"),
    ("130065", "hbr", "hbr[", "/h-b-r/", "vb G impv. m. sg.", "hbr w ql 'bow down and fall'."),
    ("130066", "w", "w", "w", "conj.", ""),
    ("130067", "ql", "ql[", "/q-l/", "vb G impv. m. sg.", "ql 'fall down!' (impv)."),
    ("H", "VIII:28"),
    ("130068", "tštḥwy", "!t!]š]]t]ḥwy(II)[", "/ḥ-w-y/ (II)", "vb Št prefc. 2 m. du.", "'prostrate yourselves'."),
    ("130069", "w", "w", "w", "conj.", ""),
    ("130070", "k", "kbd[", "/k-b-d/", "vb G impv. m. du.", "MERGE WITH THE NEXT: k+bd = kbd 'and honour!', split VIII:28/29."),
    ("H", "VIII:29"),
    ("130071", "bd", "kbd[", "/k-b-d/", "vb G impv. m. du.", "MERGE WITH THE PREVIOUS."),
    ("130072", "hwt", "hw(t(I)/t", "hwt (I)", "n. f. sg. abs. acc.", "kbd hwt 'honour him'."),
    ("130073", "w", "w", "w", "conj.", ""),
    ("130074", "rgm", "rgm[", "/r-g-m/", "vb G impv. m. sg.", "rgm 'say!' (impv)."),
    ("H", "VIII:30"),
    ("130075", "l", "l(I)", "l (I)", "prep.", ""),
    ("130076", "bnx", "bn(I)/&x", "bn (I)", "n. m. sg. cstr. gen.", "bn ilm mt; final sign broken (x)."),
    ("130077", "ilm", "il(I)/m", "ỉl (I)", "n. m. pl. cstr. gen.", ""),
    ("130078", "mt", "mt(II)/", "mt (II)", "DN m. sg. abs. gen.", ""),
    ("H", "VIII:31"),
    ("130079", "ṯny", "ṯny[", "/ṯ-n-y/", "vb G impv. m. sg.", "ṯny 'repeat!' (impv)."),
    ("130080", "l", "l(I)", "l (I)", "prep.", ""),
    ("130081", "ydd", "ydd(I)/", "ydd (I)", "adj. m. sg. cstr. gen.", "ydd il ġzr 'the beloved of El, the hero'."),
    ("H", "VIII:32"),
    ("130082", "il", "il(I)/", "ỉl (I)", "DN m. sg. cstr. gen.", ""),
    ("130083", "ġzr", "ġzr/", "ġzr", "n. m. sg. abs. gen.", ""),
    ("130084", "tḥm", "tḥm/", "tḥm", "n. m. sg. cstr. acc.", "tḥm aliyn bˤl 'the message of Mightiest Baal'."),
    ("H", "VIII:33"),
    ("130085", "aliyn", "aliyn/", "ảlỉyn", "adj. m. sg. cstr. gen.", ""),
    ("130086", "bˤl", "bˤl(II)/", "bʕl (II)", "DN m. sg. cstr. gen.", ""),
    ("H", "VIII:34"),
    ("130087", "hwt", "hw(t(I)/t", "hwt (I)", "n. f. sg. cstr. acc.", "hwt aliy qrdm 'the word of the Mightiest of heroes'."),
    ("130088", "aliy", "aliy/", "ảlỉy", "adj. m. sg. cstr. gen.", ""),
    ("130089", "q", "qrd/m", "qrd (I)", "n. m. pl. cstr. gen.", "MERGE WITH THE NEXT: q+rdm = qrdm 'heroes', split VIII:34/35."),
    ("H", "VIII:35"),
    ("130090", "rdm", "qrd/m", "qrd (I)", "n. m. pl. cstr. gen.", "MERGE WITH THE PREVIOUS."),
    ("130091", "bhty", "b&ht(II)/+y", "bt (II)", "n. m. pl. cstr. nom. + 1 c. sg. suff.", "bhty 'my house(s)'."),
    ("130092", "bnt", "bn(t(I)/t", "bnt (I)", "n. f. sg. cstr. nom.", "bnt dt ksp 'built of silver' (bnt I, not II)."),
    ("H", "VIII:36"),
    ("130093", "dt", "d+t", "d", "det. or rel. functor", "dt ksp 'those of silver'."),
    ("130094", "ksp", "ksp/", "ksp", "n. m. sg. abs. gen.", ""),
    ("130095", "rmmt", "rmm[t", "/r-m/", "vb L ptcpl. f. pl.", "rmmt 'raised (of gold)' (// bnt; /r-m/, tentative)."),
    ("H", "VIII:37"),
    ("130096", "dt", "d+t", "d", "det. or rel. functor", ""),
    ("130097", "ḫrṣ", "ḫrṣ/", "ḫrṣ", "n. m. sg. abs. gen.", ""),
    ("130098", "hkly", "hkl/+y", "hkl", "n. m. sg. cstr. nom. + 1 c. sg. suff.", "my palace"),
    ("H", "VIII:38"),
    ("130099", "aḫy", "aḫ(I)/+y", "ảḫ (I)", "n. m. du. cstr. nom. + 1 c. sg. suff.", "my brothers"),
    ("H", "VIII:39"),
    ("130100", "aḫy", "aḫ(I)/+y", "ảḫ (I)", "n. m. du. cstr. nom. + 1 c. sg. suff.", ""),
    ("H", "VIII:40"),
    ("130101", "bhty", "b&ht(II)/+y", "bt (II)", "n. m. pl. cstr. acc. + 1 c. sg. suff.", "my house"),
    ("H", "VIII:41"),
    ("130102", "qrb", "qrb[", "/q-r-b/", "vb G suffc. 3 m. sg.", ""),
    ("H", "VIII:42"),
    ("130103", "", "?", "?", "?", "Broken."),
    ("130104", "ṣḥt", "ṣḥ[t", "/ṣ-ḥ/", "vb G suffc. 1 c. sg.", "ṣḥt 'I summoned'."),
    ("H", "VIII:43"),
    ("130105", "", "?", "?", "?", "Broken."),
    ("130106", "mt", "mt(II)/", "mt (II)", "DN m. sg. cstr. gen.", ""),
    ("H", "VIII:44"),
    ("130107", "bn", "bn(I)/", "bn (I)", "n. m. sg. cstr. gen.", "bn ilm 'son of the gods'."),
    ("130108", "ilm", "il(I)/m", "ỉl (I)", "n. m. pl. abs. gen.", ""),
    ("H", "VIII:45"),
    ("130109", "ymru", "!y!mr(ʔ[&u", "/m-r-ʔ/", "vb G prefc. 3 m. sg.", ""),
    ("130110", "yd", "yd(I)/", "yd (I)", "n. f. sg. cstr. nom.", ""),
    ("H", "VIII:46"),
    ("130111", "ġzr", "ġzr/", "ġzr", "n. m. sg. cstr. gen.", ""),
    ("H", "VIII:47"),
    ("130112", "gpn", "gpn(III)/", "gpn (III)", "DN m. sg. abs. nom.", "gpn w ugr (Baal's messengers Gapnu-and-Ugaru); auto read gpn (I) 'vine'."),
    ("130113", "w", "w", "w", "conj.", ""),
    ("130114", "ugr", "ugr(II)/", "ủgr (II)", "DN m. sg. abs. nom.", ""),
    ("H", "VIII:48"),
    ("130115", "t", "?", "?", "?", "Broken single sign."),
    ("H", "VIII:49"),
    ("130116", "spr", "spr/", "spr (I)", "n. m. sg. abs. nom.", "Colophon: spr ỉlmlk 'the scribe Ilimilku'."),
    ("130117", "ilmlk", "ilmlk/", "ỉlmlk", "PN sg. abs. nom.", "Ilimilku (the scribe)."),
    ("130118", "ṯˤy", "ṯˤy(I)/", "ṯʕy (I)", "n. m. sg. cstr. nom.", ""),
    ("130119", "nqmd", "nqmd/", "nqmd", "PN sg. cstr. gen.", "Niqmaddu (king of Ugarit)."),
    ("130120", "mlk", "mlk(I)/", "mlk (I)", "n. m. sg. cstr. gen.", ""),
    ("130121", "ugrt", "ugrt/", "ủgrt", "TN sg. abs. gen.", ""),
]


def main():
    order, auto_rows, _ = R.parse_auto()
    gloss_for, valid = R.build_gloss_authority(auto_rows)

    block = []
    for item in ROWS:
        if item[0] == "H":
            block.append(f"# KTU 1.4 {item[1]}\t\t\t\t\t\t")
            continue
        tid, surf, ana, col4, pos, comment = item
        new_col4, gloss = R.derive_gloss(tid, col4, gloss_for)
        block.append("\t".join([tid, surf, ana, new_col4, pos, gloss, comment]))

    text = open(REV, encoding="utf-8").read().split("\n")
    start = next(i for i, l in enumerate(text) if l.startswith("# KTU 1.4 VIII:1"))
    # VIII is the last column -> replace to EOF (dropping trailing blank)
    head = text[:start]
    new = head + block
    open(REV, "w", encoding="utf-8").write("\n".join(new) + "\n")

    # ---- validation ----
    import sys as _sys
    _sys.path.insert(0, os.path.join(R.REPO, "agent"))
    from linter.lint import reconstruct_surface_from_analysis, normalize_surface
    auto_ids = [t for k, t in order if k == "T"]
    rv_ids, bad_col4, recon = [], {}, []
    last = None
    for l in open(REV, encoding="utf-8"):
        f = l.rstrip("\n").split("\t")
        if not (f and f[0].isdigit()):
            continue
        if f[0] != last:
            rv_ids.append(f[0]); last = f[0]
        for p in [x.strip() for x in f[3].split(";")]:
            if p not in ("", "?") and p not in valid:
                bad_col4[p] = bad_col4.get(p, 0) + 1
        comment = f[6] if len(f) > 6 else ""
        if f[2].strip() in ("", "?") or "MERGE" in comment:
            continue
        try:
            rec = reconstruct_surface_from_analysis(f[2])
            if normalize_surface(rec) != normalize_surface(f[1]):
                recon.append((f[0], f[1], f[2], rec))
        except Exception as e:  # noqa: BLE001
            recon.append((f[0], f[1], f[2], str(e)))
    rvset = set(rv_ids)
    print("missing vs auto:", [i for i in auto_ids if i not in rvset])
    print("invalid col4:", bad_col4)
    print("non-MERGE reconstruct mismatches:", len(recon))
    for r in recon:
        print("   ", r)


if __name__ == "__main__":
    main()
