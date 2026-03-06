"""Tests for slash-variant handling in refine_results_mentions helpers."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from pipeline.dulat_attestation_index import DulatAttestationIndex, normalize_reference_label
from scripts.refine_results_mentions import (
    Entry,
    Variant,
    analysis_for_entry,
    build_variants,
    compact_gloss,
    entry_label,
    is_usable_sense_definition,
    load_entries,
    parse_separator_ref,
    refine_file,
    render_variant,
)

_INSERT_ENTRY_SQL = (
    "INSERT INTO entries("
    "entry_id, lemma, homonym, pos, wiki_transcription, summary, text"
    ") VALUES (?, ?, ?, ?, ?, ?, ?)"
)


class RefineResultsMentionsTest(unittest.TestCase):
    def _init_dulat_schema(self, db_path: Path) -> None:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE entries ("
            "entry_id INTEGER PRIMARY KEY, "
            "lemma TEXT, homonym TEXT, pos TEXT, wiki_transcription TEXT, "
            "summary TEXT, text TEXT)"
        )
        cur.execute(
            "CREATE TABLE senses (id INTEGER PRIMARY KEY, entry_id INTEGER, definition TEXT)"
        )
        cur.execute("CREATE TABLE translations (entry_id INTEGER, text TEXT)")
        cur.execute("CREATE TABLE forms (text TEXT, entry_id INTEGER, morphology TEXT)")
        conn.commit()
        conn.close()

    def test_entry_label_preserves_short_prefix_slash_lemma(self) -> None:
        entry = Entry(
            entry_id=665,
            lemma="ỉ/ủšḫry",
            hom="",
            pos="DN",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(entry_label(entry), "ỉ/ủšḫry")

    def test_entry_label_preserves_non_root_slash_lemma(self) -> None:
        entry = Entry(
            entry_id=915,
            lemma="ʕllmy/n",
            hom="",
            pos="adj. /n.",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(entry_label(entry), "ʕllmy/n")

    def test_compact_gloss_keeps_parenthetical_comma(self) -> None:
        self.assertEqual(compact_gloss("(one, a) thousand"), "(one, a) thousand")

    def test_compact_gloss_still_splits_top_level_comma(self) -> None:
        self.assertEqual(compact_gloss("thousand, herd"), "thousand")

    def test_flags_attestation_style_sense_as_non_usable(self) -> None:
        self.assertFalse(
            is_usable_sense_definition(
                "ʕšr ʕšr b bt ỉlm a banquet is held in the temple of the gods, "
                "1.43:2. Cf. ʕšr(t) (I)."
            )
        )
        self.assertTrue(is_usable_sense_definition("banquet, feast"))

    def test_analysis_prefers_surface_for_short_prefix_slash_lemma(self) -> None:
        entry = Entry(
            entry_id=665,
            lemma="ỉ/ủšḫry",
            hom="",
            pos="DN",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(analysis_for_entry("ušḫry", entry), "ušḫry/")
        self.assertEqual(analysis_for_entry("išḫry", entry), "išḫry/")

    def test_analysis_prefers_surface_for_short_nominal_slash_lemma(self) -> None:
        entry = Entry(
            entry_id=525,
            lemma="ả/ỉr",
            hom="",
            pos="n.",
            gloss="light",
            wiki_tr="",
        )
        self.assertEqual(analysis_for_entry("ar", entry), "ar/")

    def test_analysis_prefers_surface_for_slash_variant_long_nominal(self) -> None:
        entry = Entry(
            entry_id=2801,
            lemma="m/bqr",
            hom="",
            pos="n.",
            gloss="spring",
            wiki_tr="",
        )
        self.assertEqual(analysis_for_entry("bqr", entry), "bqr/")

    def test_analysis_for_pronoun_does_not_add_nominal_slash(self) -> None:
        entry = Entry(
            entry_id=431,
            lemma="ản",
            hom="I",
            pos="pers. pn.",
            gloss="I",
            wiki_tr="",
        )
        self.assertEqual(analysis_for_entry("an", entry), "an(I)")

    def test_analysis_for_adverb_does_not_add_nominal_slash(self) -> None:
        entry = Entry(
            entry_id=432,
            lemma="ản",
            hom="II",
            pos="adv.",
            gloss="wherever",
            wiki_tr="",
        )
        self.assertEqual(analysis_for_entry("an", entry), "an(II)")

    def test_analysis_uses_surface_for_non_nominal_form_variant(self) -> None:
        entry = Entry(
            entry_id=1334,
            lemma="d",
            hom="",
            pos="det. / rel. functor",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(analysis_for_entry("dt", entry), "d&t")

    def test_analysis_encodes_nominal_y_to_surface_n_variant(self) -> None:
        entry = Entry(
            entry_id=915,
            lemma="ʕllmy/n",
            hom="",
            pos="adj. /n.",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(analysis_for_entry("ˤllmn", entry), "ˤllm(y/n")

    def test_analysis_for_mn_keeps_nominal_slash(self) -> None:
        entry = Entry(
            entry_id=434,
            lemma="ḫyr",
            hom="",
            pos="MN",
            gloss="aller de ci de là",
            wiki_tr="",
        )
        self.assertEqual(analysis_for_entry("ḫyr", entry), "ḫyr/")

    def test_analysis_for_rn_keeps_nominal_slash(self) -> None:
        entry = Entry(
            entry_id=435,
            lemma="nql",
            hom="",
            pos="RN",
            gloss="river-name",
            wiki_tr="",
        )
        self.assertEqual(analysis_for_entry("nql", entry), "nql/")

    def test_analysis_for_dn_keeps_nominal_slash(self) -> None:
        entry = Entry(
            entry_id=433,
            lemma="špš",
            hom="",
            pos="DN f.",
            gloss="Šapšu/Shapsh/Shapshu",
            wiki_tr="",
        )
        self.assertEqual(analysis_for_entry("špš", entry), "špš/")

    def test_analysis_keeps_trailing_prefixed_verb_tail(self) -> None:
        entry = Entry(
            entry_id=2520,
            lemma="/l-s-m/",
            hom="",
            pos="vb",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(analysis_for_entry("tlsmn", entry), "!t!lsm[n")

    def test_analysis_rewrites_prefixed_weak_final_tbnn(self) -> None:
        entry = Entry(
            entry_id=1245,
            lemma="/b-n-y/",
            hom="",
            pos="vb",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(
            analysis_for_entry("tbnn", entry, morph_values=["G, prefc."]),
            "!t!bn(y[n",
        )

    def test_analysis_rewrites_prefixed_weak_initial_h_ylkn(self) -> None:
        entry = Entry(
            entry_id=1747,
            lemma="/h-l-k/",
            hom="",
            pos="vb",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(
            analysis_for_entry("ylkn", entry, morph_values=["G, prefc."]),
            "!y!(hlk[n",
        )

    def test_analysis_rewrites_prefixed_i_aleph(self) -> None:
        entry = Entry(
            entry_id=642,
            lemma="/ʔ-s-p/",
            hom="",
            pos="vb",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(
            analysis_for_entry("tusp", entry, morph_values=["Gpass., prefc."]),
            "!t!(ʔ&usp[",
        )

    def test_analysis_rewrites_prefixed_ii_aleph(self) -> None:
        entry = Entry(
            entry_id=3012,
            lemma="/n-ʔ-ṣ/",
            hom="",
            pos="vb",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(
            analysis_for_entry("ynaṣn", entry, morph_values=["G, prefc., with suff."]),
            "!y!n(ʔ&aṣ[n",
        )

    def test_analysis_keeps_preformative_for_contracted_prefixed_verb(self) -> None:
        entry = Entry(
            entry_id=4000,
            lemma="/w-ḥ-y/",
            hom="",
            pos="vb",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(
            analysis_for_entry("twtḥ", entry, morph_values=["Gt, prefc."]),
            "!t!w]t]ḥ(y[",
        )

    def test_render_variant_keeps_non_nominal_suffix_host_without_slash(self) -> None:
        base = Entry(
            entry_id=431,
            lemma="ản",
            hom="I",
            pos="pers. pn.",
            gloss="I",
            wiki_tr="",
        )
        suffix = Entry(
            entry_id=9000,
            lemma="-h",
            hom="",
            pos="pers. pn.",
            gloss="his / her",
            wiki_tr="",
        )
        variant = Variant(entries=(base, suffix), base_surface="an")
        self.assertEqual(
            render_variant("anh", variant, forms_morph={}),
            ("an(I)+h", "ản (I),-h", "pers. pn.,pers. pn.", "I,his / her"),
        )

    def test_analysis_normalizes_aleph_prefix_preformative_marker(self) -> None:
        sh_entry = Entry(
            entry_id=4004,
            lemma="/h-l-k/",
            hom="",
            pos="vb",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(
            analysis_for_entry("ašhlk", sh_entry, morph_values=["Š, prefc."]),
            "!(ʔ&a!]š]hlk[",
        )

        iii_aleph_entry = Entry(
            entry_id=4005,
            lemma="/q-r-ʔ/",
            hom="",
            pos="vb",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(
            analysis_for_entry("iqra", iii_aleph_entry, morph_values=["G, prefc."]),
            "!(ʔ&i!qr(ʔ[&a",
        )
        self.assertEqual(
            analysis_for_entry(
                "uba",
                Entry(4006, "/b-ʔ/", "", "vb", "", ""),
                morph_values=["G, prefc."],
            ),
            "!(ʔ&u!b(ʔ[&a",
        )

    def test_analysis_keeps_preformative_for_st_marker_prefixed_verb(self) -> None:
        entry = Entry(
            entry_id=4001,
            lemma="/ḥ-w-y/",
            hom="II",
            pos="vb",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(
            analysis_for_entry("tštḥwy", entry, morph_values=["Št, prefc."]),
            "!t!]š]]t]ḥwy(II)[",
        )
        self.assertEqual(
            analysis_for_entry("yštḥwyn", entry, morph_values=["Št, prefc."]),
            "!y!]š]]t]ḥwy(II)[n",
        )

    def test_analysis_keeps_preformative_for_sh_marker_prefixed_verb(self) -> None:
        entry = Entry(
            entry_id=4002,
            lemma="/l-ḥ-m/",
            hom="I",
            pos="vb",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(
            analysis_for_entry("yšlḥm", entry, morph_values=["Š, prefc."]),
            "!y!]š]lḥm(I)[",
        )

    def test_analysis_keeps_non_prefixed_sh_stem_without_spurious_tail(self) -> None:
        entry = Entry(
            entry_id=4003,
            lemma="/q-r-b/",
            hom="",
            pos="vb",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(
            analysis_for_entry("šqrb", entry, morph_values=["Š, prefc."]),
            "]š]qrb[",
        )

    def test_analysis_encodes_contracted_n_weak_iii_aleph_prefixed_forms(self) -> None:
        entry = Entry(
            entry_id=5000,
            lemma="/n-š-ʔ/",
            hom="",
            pos="vb",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(
            analysis_for_entry("yšu", entry, morph_values=["G, prefc."]),
            "!y!(nš(ʔ[&u",
        )
        self.assertEqual(
            analysis_for_entry("tšan", entry, morph_values=["G, prefc."]),
            "!t!(nš(ʔ[&an",
        )
        self.assertEqual(
            analysis_for_entry("ytšu", entry, morph_values=["Gt, prefc."]),
            "!y!(n]t]š(ʔ[&u",
        )

    def test_analysis_encodes_prefixed_iii_aleph_forms(self) -> None:
        entry = Entry(
            entry_id=5001,
            lemma="/ḫ-ṭ-ʔ/",
            hom="",
            pos="vb",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(
            analysis_for_entry("tḫṭu", entry, morph_values=["G, prefc."]),
            "!t!ḫṭ(ʔ[&u",
        )

    def test_render_split_variant_preserves_surface_only_tail_before_suffix(self) -> None:
        base = Entry(
            entry_id=6001,
            lemma="qdqd",
            hom="",
            pos="n. m.",
            gloss="skull",
            wiki_tr="",
        )
        suffix = Entry(
            entry_id=6002,
            lemma="-k",
            hom="",
            pos="pers. pn.",
            gloss="your",
            wiki_tr="",
        )
        variant = render_variant(
            "qdqdhk",
            Variant((base, suffix), "qdqdh"),
            forms_morph={},
        )
        self.assertEqual(variant[0], "qdqd&h/+k")

    def test_analysis_keeps_l_stem_geminate_before_verbal_closure(self) -> None:
        entry = Entry(
            entry_id=5002,
            lemma="/q-ṭ(-ṭ)/",
            hom="",
            pos="vb",
            gloss="",
            wiki_tr="",
        )
        self.assertEqual(
            analysis_for_entry("tqṭṭ", entry, morph_values=["L, prefc."]),
            "!t!qṭṭ[",
        )
        self.assertEqual(
            analysis_for_entry("tqṭṭn", entry, morph_values=["L, prefc."]),
            "!t!qṭṭ[n",
        )

    def test_load_entries_falls_back_to_lemma_when_forms_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._init_dulat_schema(db_path)
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute(_INSERT_ENTRY_SQL, (170, "ủgrt", "", "TN", "", "", ""))
            cur.execute(
                "INSERT INTO senses(id, entry_id, definition) VALUES (?, ?, ?)",
                (1, 170, "Ugarit"),
            )
            conn.commit()
            conn.close()

            _entries_by_id, forms_map, lemma_map, suffix_map, forms_morph = load_entries(db_path)
            self.assertIn("ugrt", forms_map)
            self.assertEqual([entry.entry_id for entry in forms_map["ugrt"]], [170])

            variants = build_variants(
                surface="ugrt",
                current_ref="CAT 1.119 I:1",
                forms_map=forms_map,
                lemma_map=lemma_map,
                suffix_map=suffix_map,
                forms_morph=forms_morph,
                mention_ids=set(),
                entry_ref_count={},
                entry_tablets={},
                entry_family_count={},
                max_variants=3,
            )
            self.assertTrue(variants)
            self.assertEqual(variants[0].entries[0].entry_id, 170)

    def test_load_entries_prefers_translation_when_first_sense_is_attestation_example(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._init_dulat_schema(db_path)
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute(
                _INSERT_ENTRY_SQL,
                (1057, "/ʕ-š-r/", "", "vb", "", "", ""),
            )
            cur.execute(
                "INSERT INTO senses(id, entry_id, definition) VALUES (?, ?, ?)",
                (
                    61,
                    1057,
                    "ʕšr ʕšr b bt ỉlm a banquet is held in the temple of the gods, "
                    "1.43:2. Cf. ʕšr(t) (I).",
                ),
            )
            cur.executemany(
                "INSERT INTO translations(entry_id, text) VALUES (?, ?)",
                [
                    (1057, "to invite"),
                    (1057, "to give a banquet"),
                ],
            )
            cur.execute(
                "INSERT INTO forms(text, entry_id, morphology) VALUES (?, ?, ?)",
                ("yʕšr", 1057, "D, prefc."),
            )
            conn.commit()
            conn.close()

            entries_by_id, forms_map, _lemma_map, _suffix_map, _forms_morph = load_entries(db_path)
            self.assertIn("yʕšr", forms_map)
            self.assertEqual(entries_by_id[1057].gloss, "to invite")

    def test_fallback_direct_hit_does_not_suppress_suffix_split_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._init_dulat_schema(db_path)
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.executemany(
                _INSERT_ENTRY_SQL,
                [
                    (10, "yry", "", "PN", "", "", ""),
                    (11, "/y-r-y/", "", "vb", "", "", ""),
                    (12, "yr", "", "n. m.", "", "", ""),
                    (13, "-y", "I", "prep.", "", "", ""),
                ],
            )
            cur.executemany(
                "INSERT INTO forms(text, entry_id, morphology) VALUES (?, ?, ?)",
                [
                    ("yr", 11, "G, prefc."),
                    ("yr", 12, "sg."),
                ],
            )
            cur.executemany(
                "INSERT INTO translations(entry_id, text) VALUES (?, ?)",
                [
                    (10, "yry"),
                    (11, "to fire"),
                    (12, "early rain"),
                    (13, "my"),
                ],
            )
            conn.commit()
            conn.close()

            _entries, forms_map, lemma_map, suffix_map, forms_morph = load_entries(db_path)
            variants = build_variants(
                surface="yry",
                current_ref="CAT 1.101:4",
                forms_map=forms_map,
                lemma_map=lemma_map,
                suffix_map=suffix_map,
                forms_morph=forms_morph,
                mention_ids=set(),
                entry_ref_count={},
                entry_tablets={},
                entry_family_count={},
                max_variants=5,
            )

            rendered = [render_variant("yry", variant, forms_morph) for variant in variants]
            self.assertNotIn(("yry/", "yry", "PN", "yry"), rendered)
            self.assertTrue(any("+y(I)" in row[0] for row in rendered))
            self.assertTrue(any(row[0].startswith("yr/+y") for row in rendered))

    def test_exact_direct_lexical_candidate_blocks_suffix_split_variants(self) -> None:
        direct = Entry(
            entry_id=20,
            lemma="nny",
            hom="",
            pos="TN",
            gloss="nny",
            wiki_tr="",
        )
        base_one = Entry(
            entry_id=21,
            lemma="/g-r-š/",
            hom="",
            pos="vb",
            gloss="to eject",
            wiki_tr="",
        )
        base_two = Entry(
            entry_id=22,
            lemma="/g-r(-y)/",
            hom="",
            pos="vb",
            gloss="to attack",
            wiki_tr="",
        )
        suffix = Entry(
            entry_id=23,
            lemma="-y",
            hom="I",
            pos="prep.",
            gloss="my",
            wiki_tr="",
        )
        variants = build_variants(
            surface="nny",
            current_ref="CAT 1.16 I:1",
            forms_map={"nny": [direct], "nn": [base_one, base_two]},
            lemma_map={"nny": [direct]},
            suffix_map={"y": [suffix]},
            forms_morph={},
            mention_ids=set(),
            entry_ref_count={},
            entry_tablets={},
            entry_family_count={},
            max_variants=5,
        )

        rendered = [render_variant("nny", variant, forms_morph={}) for variant in variants]
        self.assertEqual(rendered[0], ("nny/", "nny", "TN", "nny"))
        self.assertFalse(any("+y(I)" in row[0] for row in rendered))

    def test_prunes_pn_variant_without_direct_dulat_attestation_when_non_pn_exists(self) -> None:
        dn_entry = Entry(
            entry_id=50,
            lemma="ltn",
            hom="I",
            pos="DN",
            gloss="Lotan",
            wiki_tr="",
        )
        pn_entry = Entry(
            entry_id=51,
            lemma="ltn",
            hom="II",
            pos="PN",
            gloss="ltn (II)",
            wiki_tr="",
        )

        variants = build_variants(
            surface="ltn",
            current_ref="CAT 1.5 I:1",
            forms_map={"ltn": [dn_entry, pn_entry]},
            lemma_map={"ltn": [dn_entry, pn_entry]},
            suffix_map={},
            forms_morph={("ltn", 50): {"abs."}, ("ltn", 51): {"cstr."}},
            mention_ids=set(),
            entry_ref_count={},
            entry_tablets={},
            entry_family_count={},
            direct_reference_index=DulatAttestationIndex.empty(),
            max_variants=5,
        )

        rendered = [render_variant("ltn", variant, forms_morph={}) for variant in variants]
        self.assertEqual(rendered, [("ltn(I)/", "ltn (I)", "DN", "Lotan")])

    def test_keeps_pn_variant_with_direct_dulat_attestation_when_non_pn_exists(self) -> None:
        dn_entry = Entry(
            entry_id=60,
            lemma="ltn",
            hom="I",
            pos="DN",
            gloss="Lotan",
            wiki_tr="",
        )
        pn_entry = Entry(
            entry_id=61,
            lemma="ltn",
            hom="II",
            pos="PN",
            gloss="ltn (II)",
            wiki_tr="",
        )
        attestation_index = DulatAttestationIndex(
            counts_by_key={},
            max_count_by_lemma={},
            refs_by_key={
                ("ltn", "II"): {normalize_reference_label("CAT 1.5 I:1")},
            },
        )

        variants = build_variants(
            surface="ltn",
            current_ref="CAT 1.5 I:1",
            forms_map={"ltn": [dn_entry, pn_entry]},
            lemma_map={"ltn": [dn_entry, pn_entry]},
            suffix_map={},
            forms_morph={("ltn", 60): {"abs."}, ("ltn", 61): {"cstr."}},
            mention_ids=set(),
            entry_ref_count={},
            entry_tablets={},
            entry_family_count={},
            direct_reference_index=attestation_index,
            max_variants=5,
        )

        rendered = [render_variant("ltn", variant, forms_morph={}) for variant in variants]
        self.assertIn(("ltn(I)/", "ltn (I)", "DN", "Lotan"), rendered)
        self.assertIn(("ltn(II)/", "ltn (II)", "PN", "ltn (II)"), rendered)

    def test_does_not_treat_personal_pronoun_as_prunable_pn_variant(self) -> None:
        pronoun_entry = Entry(
            entry_id=70,
            lemma="hm",
            hom="I",
            pos="pers. pn.",
            gloss="they",
            wiki_tr="",
        )
        conjunction_entry = Entry(
            entry_id=71,
            lemma="hm",
            hom="II",
            pos="conj./interr. functor",
            gloss="if",
            wiki_tr="",
        )

        variants = build_variants(
            surface="hm",
            current_ref="CAT 1.5 I:16",
            forms_map={"hm": [pronoun_entry, conjunction_entry]},
            lemma_map={"hm": [pronoun_entry, conjunction_entry]},
            suffix_map={},
            forms_morph={("hm", 70): {"sg."}, ("hm", 71): {"functor"}},
            mention_ids=set(),
            entry_ref_count={},
            entry_tablets={},
            entry_family_count={},
            direct_reference_index=DulatAttestationIndex.empty(),
            max_variants=5,
        )

        rendered = [render_variant("hm", variant, forms_morph={}) for variant in variants]
        self.assertIn(("hm(I)", "hm (I)", "pers. pn.", "they"), rendered)
        self.assertIn(("hm(II)", "hm (II)", "conj./interr. functor", "if"), rendered)

    def test_direct_exact_lexical_candidate_is_not_split_into_itself(self) -> None:
        direct = Entry(
            entry_id=30,
            lemma="hnny",
            hom="",
            pos="adv.",
            gloss="here",
            wiki_tr="",
        )
        suffix = Entry(
            entry_id=31,
            lemma="-ny",
            hom="",
            pos="deictic functor/adv.",
            gloss="behold!",
            wiki_tr="",
        )
        variants = build_variants(
            surface="hnny",
            current_ref="CAT 2.38:1",
            forms_map={"hnny": [direct], "hn": [direct]},
            lemma_map={"hnny": [direct]},
            suffix_map={"ny": [suffix]},
            forms_morph={("hn", 30): {"adv."}},
            mention_ids=set(),
            entry_ref_count={},
            entry_tablets={},
            entry_family_count={},
            max_variants=5,
        )

        rendered = [render_variant("hnny", variant, forms_morph={}) for variant in variants]
        self.assertEqual(rendered, [("hnny", "hnny", "adv.", "here")])

    def test_direct_exact_lexical_candidate_blocks_function_word_splits(self) -> None:
        direct = Entry(
            entry_id=40,
            lemma="hnny",
            hom="",
            pos="adv.",
            gloss="here",
            wiki_tr="",
        )
        base_hn = Entry(
            entry_id=41,
            lemma="hn",
            hom="",
            pos="deictic functor/adv.",
            gloss="behold!",
            wiki_tr="",
        )
        base_hnn = Entry(
            entry_id=42,
            lemma="hnn",
            hom="",
            pos="adv. functor",
            gloss="here",
            wiki_tr="",
        )
        suffix_ny = Entry(
            entry_id=43,
            lemma="-ny",
            hom="",
            pos="deictic functor/adv.",
            gloss="behold!",
            wiki_tr="",
        )
        suffix_y = Entry(
            entry_id=44,
            lemma="-y",
            hom="I",
            pos="postp.",
            gloss="my",
            wiki_tr="",
        )
        variants = build_variants(
            surface="hnny",
            current_ref="CAT 2.38:1",
            forms_map={"hnny": [direct], "hn": [base_hn], "hnn": [base_hnn]},
            lemma_map={"hnny": [direct]},
            suffix_map={"ny": [suffix_ny], "y": [suffix_y]},
            forms_morph={("hn", 41): {"deictic functor/adv."}, ("hnn", 42): {"adv. functor"}},
            mention_ids=set(),
            entry_ref_count={},
            entry_tablets={},
            entry_family_count={},
            max_variants=5,
        )

        rendered = [render_variant("hnny", variant, forms_morph={}) for variant in variants]
        self.assertEqual(rendered, [("hnny", "hnny", "adv.", "here")])

    def test_parse_separator_ref_supports_no_column_format(self) -> None:
        self.assertEqual(
            parse_separator_ref("#---------------------------- KTU 1.101 5"),
            "CAT 1.101:5",
        )
        self.assertEqual(
            parse_separator_ref("#---------------------------- KTU 1.3 I:23"),
            "CAT 1.3 I:23",
        )

    def test_refine_file_uses_reverse_mentions_with_no_column_separator(self) -> None:
        dn_entry = Entry(
            entry_id=1,
            lemma="ṭly",
            hom="",
            pos="DN",
            gloss="Tallay",
            wiki_tr="",
        )
        noun_entry = Entry(
            entry_id=2,
            lemma="ṭl",
            hom="",
            pos="n. m.",
            gloss="dew",
            wiki_tr="",
        )
        forms_map = {"ṭly": [noun_entry, dn_entry]}
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir) / "KTU 1.101.tsv"
            out_path.write_text(
                ("#---------------------------- KTU 1.101 5\n1\tṭly\t?\t?\t?\t?\t\n"),
                encoding="utf-8",
            )
            rows, changed = refine_file(
                path=out_path,
                out_path=out_path,
                forms_map=forms_map,
                lemma_map={},
                suffix_map={},
                forms_morph={},
                reverse_mentions={"CAT 1.101:5": {1}},
                entry_ref_count={},
                entry_tablets={},
                entry_family_count={},
            )
            self.assertEqual(rows, 1)
            self.assertEqual(changed, 1)
            lines = out_path.read_text(encoding="utf-8").splitlines()
            self.assertIn("\tṭly\tṭly/\tṭly\tDN\tTallay\t", lines[1])

    def test_load_entries_applies_form_text_alias_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._init_dulat_schema(db_path)
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute(_INSERT_ENTRY_SQL, (2520, "/l-s-m/", "", "vb", "", "", ""))
            cur.execute(
                "INSERT INTO forms(text, entry_id, morphology) VALUES (?, ?, ?)",
                ("tslmn", 2520, "G, prefc."),
            )
            conn.commit()
            conn.close()

            _entries, forms_map, _lemma_map, _suffix_map, forms_morph = load_entries(db_path)
            self.assertIn("tlsmn", forms_map)
            self.assertEqual([entry.entry_id for entry in forms_map["tlsmn"]], [2520])
            self.assertIn(("tlsmn", 2520), forms_morph)

    def test_refine_file_resolves_weak_final_prefixed_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._init_dulat_schema(db_path)
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute(_INSERT_ENTRY_SQL, (5001, "/ġ-l-y/", "", "vb", "", "", ""))
            cur.execute(
                "INSERT INTO translations(entry_id, text) VALUES (?, ?)",
                (5001, "to lose vitality"),
            )
            cur.execute(
                "INSERT INTO forms(text, entry_id, morphology) VALUES (?, ?, ?)",
                ("tġly", 5001, "D, prefc."),
            )
            conn.commit()
            conn.close()

            _entries, forms_map, lemma_map, suffix_map, forms_morph = load_entries(db_path)
            out_path = Path(tmp_dir) / "KTU 1.3.tsv"
            out_path.write_text(
                "#---------------------------- KTU 1.3 I:1\n"
                "136938\ttġl\t?\t?\t?\t?\tDULAT: NOT FOUND\n",
                encoding="utf-8",
            )

            rows, changed = refine_file(
                path=out_path,
                out_path=out_path,
                forms_map=forms_map,
                lemma_map=lemma_map,
                suffix_map=suffix_map,
                forms_morph=forms_morph,
                reverse_mentions={},
                entry_ref_count={},
                entry_tablets={},
                entry_family_count={},
            )
            self.assertEqual(rows, 1)
            self.assertEqual(changed, 1)
            line = out_path.read_text(encoding="utf-8").splitlines()[1]
            self.assertIn("\t!t!ġl(y[\t/ġ-l-y/\tvb\tto lose vitality\t", line)

    def test_load_entries_uses_forms_block_fallback_from_entry_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._init_dulat_schema(db_path)
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            entry_text = (
                "<b>¶ Forms:</b> G suffc. <i>ġly</i>; prefc. <i>yġly</i>; inf. <i>ġly</i>. "
                "D suffc. <i>ġltm</i>; prefc. <i>tġly</i>, <i>tġl</i> (?). <br><b>G</b>."
            )
            cur.execute(
                _INSERT_ENTRY_SQL,
                (5100, "/ġ-l-y/", "", "vb", "", "", entry_text),
            )
            cur.executemany(
                "INSERT INTO forms(text, entry_id, morphology) VALUES (?, ?, ?)",
                [
                    ("ġly", 5100, "G, suffc."),
                    ("yġly", 5100, "G, prefc."),
                    ("ġly", 5100, "G, inf."),
                ],
            )
            cur.execute(
                "INSERT INTO translations(entry_id, text) VALUES (?, ?)",
                (5100, "to lose vitality"),
            )
            conn.commit()
            conn.close()

            _entries, forms_map, _lemma_map, _suffix_map, _forms_morph = load_entries(db_path)
            self.assertIn("tġl", forms_map)
            self.assertEqual([entry.entry_id for entry in forms_map["tġl"]], [5100])

    def test_load_entries_applies_form_morph_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._init_dulat_schema(db_path)
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute(_INSERT_ENTRY_SQL, (4268, "tḥm", "", "n.", "", "", ""))
            cur.execute(
                "INSERT INTO forms(text, entry_id, morphology) VALUES (?, ?, ?)",
                ("tḥmk", 4268, "sg."),
            )
            conn.commit()
            conn.close()

            _entries, _forms_map, _lemma_map, _suffix_map, forms_morph = load_entries(db_path)
            self.assertEqual(forms_morph[("tḥmk", 4268)], {"suff."})

    def test_redirect_entry_adds_target_restoration_variant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._init_dulat_schema(db_path)
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute(
                _INSERT_ENTRY_SQL,
                (
                    10,
                    "rdmn",
                    "",
                    "→",
                    "",
                    "<b>rdmn</b> cf. <i>prdmn</i>.",
                    "rdmn <b>rdmn</b> cf. <i>prdmn</i>.",
                ),
            )
            cur.execute(_INSERT_ENTRY_SQL, (11, "prdmn", "", "DN", "", "", ""))
            cur.execute(
                "INSERT INTO translations(entry_id, text) VALUES (?, ?)",
                (11, "unknown deity"),
            )
            conn.commit()
            conn.close()

            _entries, forms_map, lemma_map, suffix_map, forms_morph = load_entries(db_path)
            variants = build_variants(
                surface="rdmn",
                current_ref="CAT 1.3 I:2",
                forms_map=forms_map,
                lemma_map=lemma_map,
                suffix_map=suffix_map,
                forms_morph=forms_morph,
                mention_ids=set(),
                entry_ref_count={},
                entry_tablets={},
                entry_family_count={},
                max_variants=3,
            )

            rendered = [render_variant("rdmn", variant, forms_morph) for variant in variants]
            self.assertIn(("rdmn", "rdmn", "→", "?"), rendered)
            self.assertIn(("(prdmn/", "prdmn", "DN", "unknown deity"), rendered)

    def test_redirect_entry_resolves_slash_root_target_with_weak_restoration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._init_dulat_schema(db_path)
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute(
                _INSERT_ENTRY_SQL,
                (
                    20,
                    "wld",
                    "",
                    "→",
                    "",
                    "<b>wld</b>, cf. /y-l-d/.",
                    "wld <b>wld</b>, cf. /y-l-d/.",
                ),
            )
            cur.execute(_INSERT_ENTRY_SQL, (21, "/y-l-d/", "", "vb", "", "", ""))
            cur.execute(
                "INSERT INTO translations(entry_id, text) VALUES (?, ?)",
                (21, "to give birth"),
            )
            conn.commit()
            conn.close()

            _entries, forms_map, lemma_map, suffix_map, forms_morph = load_entries(db_path)
            variants = build_variants(
                surface="wld",
                current_ref="CAT 1.14 III:48",
                forms_map=forms_map,
                lemma_map=lemma_map,
                suffix_map=suffix_map,
                forms_morph=forms_morph,
                mention_ids=set(),
                entry_ref_count={},
                entry_tablets={},
                entry_family_count={},
                max_variants=3,
            )

            rendered = [render_variant("wld", variant, forms_morph) for variant in variants]
            self.assertIn(("wld", "wld", "→", "?"), rendered)
            self.assertIn(("(y&wld[", "/y-l-d/", "vb", "to give birth"), rendered)

    def test_redirect_entry_restores_initial_sh_for_bare_verb_lemma(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._init_dulat_schema(db_path)
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute(
                _INSERT_ENTRY_SQL,
                (
                    30,
                    "šbʕr",
                    "",
                    "→",
                    "",
                    "<b>šbʕr</b>, cf. /b-ʕ-r/ (I).",
                    "šbʕr <b>šbʕr</b>, cf. /b-ʕ-r/ (I).",
                ),
            )
            cur.execute(_INSERT_ENTRY_SQL, (31, "/b-ʕ-r/", "I", "vb", "", "", ""))
            cur.execute(
                "INSERT INTO translations(entry_id, text) VALUES (?, ?)",
                (31, "to illuminate"),
            )
            conn.commit()
            conn.close()

            _entries, forms_map, lemma_map, suffix_map, forms_morph = load_entries(db_path)
            variants = build_variants(
                surface="šbˤr",
                current_ref="CAT 1.4 VI:10",
                forms_map=forms_map,
                lemma_map=lemma_map,
                suffix_map=suffix_map,
                forms_morph=forms_morph,
                mention_ids=set(),
                entry_ref_count={},
                entry_tablets={},
                entry_family_count={},
                max_variants=3,
            )

            rendered = [render_variant("šbˤr", variant, forms_morph) for variant in variants]
            self.assertIn(("šbˤr", "šbʕr", "→", "?"), rendered)
            self.assertIn(("]š]bˤr(I)[", "/b-ʕ-r/ (I)", "vb", "to illuminate"), rendered)


if __name__ == "__main__":
    unittest.main()
