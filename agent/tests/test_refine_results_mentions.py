"""Tests for slash-variant handling in refine_results_mentions helpers."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

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
            self.assertIn(("yry/", "yry", "PN", "yry"), rendered)
            self.assertTrue(any("+y(I)" in row[0] for row in rendered))
            self.assertTrue(any(row[0].startswith("yr/+y") for row in rendered))

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
            self.assertIn("\tṭly/\tṭly\tDN\tTallay\t", lines[1])

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
