"""Unit tests for pipeline refinement steps (unittest-discover compatible)."""

import sqlite3
import tempfile
import textwrap
import unittest
from pathlib import Path

from pipeline.dulat_attestation_index import DulatAttestationIndex
from pipeline.steps.aleph_prefix import AlephPrefixFixer
from pipeline.steps.attestation_sort import AttestationSortFixer
from pipeline.steps.baal_labourer_ktu1 import BaalLabourerKtu1Fixer
from pipeline.steps.baal_plural import BaalPluralGodListFixer
from pipeline.steps.baal_verbal_slash import BaalVerbalSlashFixer
from pipeline.steps.base import (
    TabletRow,
    is_separator_line,
    is_unresolved,
    normalize_separator_row,
    parse_tsv_line,
)
from pipeline.steps.formula_bigram import FormulaBigramFixer
from pipeline.steps.formula_trigram import FormulaTrigramFixer
from pipeline.steps.generic_parsing_override import GenericOverride, GenericParsingOverrideFixer
from pipeline.steps.known_ambiguities import KnownAmbiguityExpander
from pipeline.steps.ktu1_family_homonym_pruner import Ktu1FamilyHomonymPruner
from pipeline.steps.noun_closure import NounPosClosureFixer
from pipeline.steps.offering_l_prep import OfferingListLPrepFixer
from pipeline.steps.onomastic_gloss import OnomasticGlossOverrideFixer
from pipeline.steps.plural_split import PluralSplitFixer
from pipeline.steps.prefixed_iii_aleph_verb import PrefixedIIIAlephVerbFixer
from pipeline.steps.schema_formatter import TsvSchemaFormatter
from pipeline.steps.suffix_fixer import SuffixCliticFixer
from pipeline.steps.surface_option_propagation import SurfaceOptionPropagationFixer
from pipeline.steps.verb_l_stem_gemination import VerbLStemGeminationFixer
from pipeline.steps.verb_n_stem_assimilation import VerbNStemAssimilationFixer
from pipeline.steps.verb_pos_stem import VerbPosStemFixer
from pipeline.steps.verb_stem_suffix_marker import VerbStemSuffixMarkerFixer
from pipeline.steps.weak_final_sc import WeakFinalSuffixConjugationFixer
from pipeline.steps.weak_verb import WeakVerbFixer


class FormulaBigramFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = FormulaBigramFixer()

    def test_disambiguates_aliyn_baal_to_dn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\taliyn\taliyn/\tảlỉyn\tadj. m.\tThe Very / Most Powerful\t\n"
                    "2\tbˤl\tbˤl(II)/;bˤl[\tbʕl (II);/b-ʕ-l/\tn. m./DN;vb\tBaʿlu;to make\t\n"
                ),
                encoding="utf-8",
            )
            result = self.fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 1)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("\tbˤl(II)/\tbʕl (II)\tDN\tBaʿlu\t", lines[2])

    def test_disambiguates_btlt_anat_to_dn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tbtlt\tbtlt/\tbtlt\tn. f.\tvirgin\t\n"
                    "2\tˤnt\tˤn(I)/t=;ˤnt(I)/;ˤnt(II)\tʕn (I);ʕnt (I);ʕnt (II)\t"
                    "n. f.;DN;adv.\teye;sister;now\t\n"
                ),
                encoding="utf-8",
            )
            result = self.fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 1)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("\tˤnt(I)/\tʕnt (I)\tDN\tʿAnatu\t", lines[2])

    def test_skips_when_dulat_target_not_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\taliyn\taliyn/\tảlỉyn\tadj. m.\tThe Very / Most Powerful\t\n"
                    "2\tbˤl\tbˤl(I)/\tbʕl (I)\tn. m.\tlabourer\t\n"
                ),
                encoding="utf-8",
            )
            result = self.fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 0)

    def test_disambiguates_bn_il_to_noun_son(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tbn\tbn(I)/;bn(II);bn[\tbn (I);bn (II);/b-n/\tn. m.;prep.;vb\t"
                    "son;between;to build\t\n"
                    "2\til\til(I)/\tỉl (I)\tn. m.\tgod\t\n"
                ),
                encoding="utf-8",
            )
            result = self.fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 1)
            line = path.read_text(encoding="utf-8").splitlines()[1]
            self.assertIn("\tbn(I)/\tbn (I)\tn. m.\tson\t", line)

    def test_disambiguates_bn_ilm_to_noun_son(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tbn\tbn(I)/;bn(II);bn[\tbn (I);bn (II);/b-n/\tn. m.;prep.;vb\t"
                    "son;between;to build\t\n"
                    "2\tilm\til(I)/m\tỉl (I)\tn. m.\tgods\t\n"
                ),
                encoding="utf-8",
            )
            result = self.fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 1)
            line = path.read_text(encoding="utf-8").splitlines()[1]
            self.assertIn("\tbn(I)/\tbn (I)\tn. m.\tson\t", line)

    def test_disambiguates_bt_baal_to_dn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tbt\tbt(II)/;bt(I)/;b(III)/t=\tbt (II);bt (I);bt (III)\tn. m.;"
                    "n. f.;n. m.\thouse;daughter;length\t\n"
                    "2\tbˤl\tbˤl(II)/;bˤl[\tbʕl (II);/b-ʕ-l/\tn. m./DN;vb\tBaʿlu;to make\t\n"
                ),
                encoding="utf-8",
            )
            result = self.fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 1)
            line = path.read_text(encoding="utf-8").splitlines()[2]
            self.assertIn("\tbˤl(II)/\tbʕl (II)\tDN\tBaʿlu\t", line)

    def test_disambiguates_thr_il_to_bull(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tṯr\tṯr(I)/;ṯr(IV)/\tṯr (I);ṯr (IV)\tn. m.;n. f.\tbull;"
                    "foul-smelling\t\n"
                    "2\til\til(I)/\tỉl (I)\tn. m.\tgod\t\n"
                ),
                encoding="utf-8",
            )
            result = self.fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 2)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("\tṯr(I)/\tṯr (I)\tn. m.\tbull\t", lines[1])
            self.assertIn("\til(I)/\tỉl (I)\tDN\tˀIlu\t", lines[2])


class FormulaTrigramFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = FormulaTrigramFixer()

    def test_disambiguates_rbt_athirat_ym_to_lady(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\trbt\trbt/;rbt(I)/;rbt(II)/\trb(b)t;rbt (I);rbt (II)\tnum.;n. f.;"
                    "n. f.\tten thousand;Lady;seine\t\n"
                    "2\taṯrt\taṯrt(II)/\tảṯrt (II)\tDN\tAsherah\t\n"
                    "3\tym\tym(II)/\tym (II)\tn. m.\tsea\t\n"
                ),
                encoding="utf-8",
            )
            result = self.fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 1)
            line = path.read_text(encoding="utf-8").splitlines()[1]
            self.assertIn("\trbt(I)/\trbt (I)\tn. f.\tLady\t", line)

    def test_disambiguates_journey_formula_l_to_functor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tidk\tidk\tỉdk\tnarrative adv. functor\tthen\t\n"
                    "2\tl\tl(I);l(II);l(III)\tl (I);l (II);l (III)\tprep.;adv.;functor\t"
                    "to;no;certainly\t\n"
                    "3\tttn\tytn[\t/y-t-n/\tvb\tto give\t\n"
                    "4\tpnm\tpn(m/m\tpnm\tn. m. pl. tant.\tface\t\n"
                ),
                encoding="utf-8",
            )
            result = self.fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 1)
            line = path.read_text(encoding="utf-8").splitlines()[2]
            self.assertIn("\tl(III)\tl (III)\tfunctor\tcertainly\t", line)

    def test_disambiguates_il_tader_baal_to_dn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\til\til(I)/\tỉl (I)\tn. m.\tgod\t\n"
                    "2\ttˤḏr\ttˤḏr/\ttʕḏr\tn. m.\thelp\t\n"
                    "3\tbˤl\tbˤl(II)/;bˤl[\tbʕl (II);/b-ʕ-l/\tn. m./DN;vb\tBaʿlu;to make\t\n"
                ),
                encoding="utf-8",
            )
            result = self.fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 1)
            line = path.read_text(encoding="utf-8").splitlines()[3]
            self.assertIn("\tbˤl(II)/\tbʕl (II)\tDN\tBaʿlu\t", line)

    def test_skips_when_target_dulat_not_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tidk\tidk\tỉdk\tnarrative adv. functor\tthen\t\n"
                    "2\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                    "3\tttn\tytn[\t/y-t-n/\tvb\tto give\t\n"
                ),
                encoding="utf-8",
            )
            result = self.fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 0)

    def test_does_not_rewrite_single_variant_style(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\trbt\trb(t(I)/t\trbt (I)\tn. f.\tLady\t\n"
                    "2\taṯrt\taṯrt(II)/\tảṯrt (II)\tDN\tAsherah\t\n"
                    "3\tym\tym(II)/\tym (II)\tn. m.\tsea\t\n"
                ),
                encoding="utf-8",
            )
            result = self.fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 0)


class Ktu1FamilyHomonymPrunerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = Ktu1FamilyHomonymPruner(
            label_families={
                "bt (I)": {"1", "2"},
                "bt (II)": {"1", "2"},
                "bt (III)": {"3"},
                "ql (I)": {"1"},
                "ql (II)": {"4"},
                "npš (I)": {"1"},
                "npš (II)": {"4"},
                "abc (I)": {"4"},
                "abc (II)": {"5"},
            }
        )

    def test_prunes_non_ktu1_homonym_when_ktu1_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tbt\tbt(II)/;bt(I)/;b(III)/t=\tbt (II);bt (I);bt (III)\tn. m.;"
                    "n. f.;n. m.\thouse;daughter;length\t\n"
                ),
                encoding="utf-8",
            )
            result = self.fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 1)
            line = path.read_text(encoding="utf-8").splitlines()[1]
            self.assertEqual(
                line,
                "1\tbt\tbt(II)/;bt(I)/\tbt (II);bt (I)\tn. m.;n. f.\thouse;daughter\t",
            )

    def test_keeps_when_no_ktu1_homonym_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tabc\tabc(I)/;abc(II)/\tabc (I);abc (II)\tn. m.;PN\tfirst;second\t\n"
                ),
                encoding="utf-8",
            )
            result = self.fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 0)

    def test_keeps_non_homonym_variant_and_prunes_non_ktu1_homonym(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tql\tql[;ql(I)/;ql(II)/\t/q-l/;ql (I);ql (II)\tvb;n. m.;n. m.\t"
                    "to call;voice;voice-alt\t\n"
                ),
                encoding="utf-8",
            )
            result = self.fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 1)
            line = path.read_text(encoding="utf-8").splitlines()[1]
            self.assertEqual(
                line,
                "1\tql\tql[;ql(I)/\t/q-l/;ql (I)\tvb;n. m.\tto call;voice\t",
            )

    def test_non_ktu1_file_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 4.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tnpš\tnpš(I)/;npš(II)/\tnpš (I);npš (II)\tn. f.;n. f.\tself;person\t\n"
                ),
                encoding="utf-8",
            )
            result = self.fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 0)


class StaticGate:
    """Small test double for DULAT feature-gating behavior."""

    def __init__(self, plural_tokens=None, suffix_tokens=None) -> None:
        self._plural = set(plural_tokens or [])
        self._suffix = set(suffix_tokens or [])

    def is_plural_token(self, token: str, surface: str = "") -> bool:
        return token in self._plural

    def has_suffix_token(self, token: str, surface: str = "") -> bool:
        return token in self._suffix


class ParseTsvLineTest(unittest.TestCase):
    def test_data_row(self) -> None:
        row = parse_tsv_line("12345\tum\tum/\tủm\tn. f.\tmother")
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.line_id, "12345")
        self.assertEqual(row.surface, "um")
        self.assertEqual(row.analysis, "um/")
        self.assertEqual(row.dulat, "ủm")
        self.assertEqual(row.pos, "n. f.")
        self.assertEqual(row.gloss, "mother")
        self.assertEqual(row.comment, "")

    def test_data_row_with_comment(self) -> None:
        row = parse_tsv_line("12345\tum\t?\t?\t?\t?\tDULAT: NOT FOUND")
        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual(row.comment, "DULAT: NOT FOUND")

    def test_separator_returns_none(self) -> None:
        self.assertIsNone(parse_tsv_line("#---- KTU 1.100 1"))

    def test_empty_line_returns_none(self) -> None:
        self.assertIsNone(parse_tsv_line(""))


class BaseHelpersTest(unittest.TestCase):
    def test_is_separator_line(self) -> None:
        self.assertTrue(is_separator_line("#---- KTU 1.100 1"))
        self.assertFalse(is_separator_line("12345\tum\tum/"))

    def test_is_unresolved(self) -> None:
        unresolved = TabletRow("1", "x", "?", "?", "?", "?", "DULAT: NOT FOUND")
        resolved = TabletRow("1", "um", "um/", "ủm", "n. f.", "mother", "")
        self.assertTrue(is_unresolved(unresolved))
        self.assertFalse(is_unresolved(resolved))

    def test_tablet_row_to_tsv(self) -> None:
        row = TabletRow("1", "um", "um/", "ủm", "n. f.", "mother", "")
        self.assertEqual(row.to_tsv(), "1\tum\tum/\tủm\tn. f.\tmother\t")
        row_with_comment = TabletRow("1", "x", "?", "?", "?", "?", "DULAT: NOT FOUND")
        self.assertEqual(
            row_with_comment.to_tsv(),
            "1\tx\t?\t?\t?\t?\tDULAT: NOT FOUND",
        )

    def test_normalize_separator_row_preserves_tab_shape(self) -> None:
        self.assertEqual(
            normalize_separator_row("#---------------------------- KTU 1.5 I:4\t\t\t\t\t\t"),
            "# KTU 1.5 I:4\t\t\t\t\t\t",
        )
        self.assertEqual(
            normalize_separator_row("#---------------------------- KTU 1.5 I:4"),
            "# KTU 1.5 I:4",
        )


class AlephPrefixFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = AlephPrefixFixer()

    def test_bare_aleph_gets_reconstructable_substitution(self) -> None:
        row = TabletRow("1", "ảb", "ʔb/", "ʔb", "n. m.", "father", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "(ʔ&ab/")

    def test_already_prefixed_unchanged(self) -> None:
        row = TabletRow("1", "ảb", "(ʔ&ab/", "ʔb", "n. m.", "father", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "(ʔ&ab/")

    def test_root_notation_skipped(self) -> None:
        row = TabletRow("1", "abd", "/ʔ-b-d/", "/ʔ-b-d/", "vb", "be missing", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "/ʔ-b-d/")

    def test_verb_surface_aleph_substitution_is_reconstructable(self) -> None:
        row = TabletRow("2", "abd", "ʔbd[", "/ʔ-b-d/", "vb G", "be missing", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "(ʔ&abd[")


class NounPosClosureFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = NounPosClosureFixer()

    def test_noun_without_slash_gets_slash(self) -> None:
        row = TabletRow("1", "bn", "bn", "bn (I)", "n. m.", "son", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "bn/")

    def test_verb_unchanged(self) -> None:
        row = TabletRow("1", "yṯb", "yṯb[", "/y-ṯ-b/", "vb", "to sit", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "yṯb[")

    def test_multi_variant_partial_fix(self) -> None:
        row = TabletRow(
            "1",
            "mlk",
            "mlk;mlk(II)/",
            "/m-l-k/;mlk (II)",
            "vb;n. m.",
            "to reign;kingdom",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "mlk;mlk(II)/")


class PluralSplitFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = PluralSplitFixer(gate=StaticGate(plural_tokens={"nhr (I)"}))

    def test_masc_plural_m_split(self) -> None:
        row = TabletRow("1", "nhrm", "nhrm/", "nhr (I)", "n. m.", "river", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "nhr/m")

    def test_masc_plural_with_homonym(self) -> None:
        row = TabletRow("1", "nhrm", "nhrm(I)/", "nhr (I)", "n. m.", "river", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "nhr(I)/m")

    def test_non_noun_unchanged(self) -> None:
        row = TabletRow("1", "yṯbm", "yṯbm[", "/y-ṯ-b/", "vb", "to sit", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "yṯbm[")

    def test_singular_lexeme_ending_with_m_is_unchanged(self) -> None:
        row = TabletRow("1", "um", "um/", "ủm", "n. f.", "mother", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "um/")

    def test_lemma_style_plural_surface_m_gets_split(self) -> None:
        fixer = PluralSplitFixer(gate=StaticGate(plural_tokens={"ỉl (I)"}))
        row = TabletRow("1", "ilm", "il(I)/", "ỉl (I)", "n. m.", "god", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "il(I)/m")

    def test_lemma_style_plural_surface_t_gets_split(self) -> None:
        fixer = PluralSplitFixer(gate=StaticGate(plural_tokens={"kṯr (I)"}))
        row = TabletRow("1", "kṯrt", "kṯr(I)/", "kṯr (I)", "n. f.", "Kothar", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "kṯr(I)/t=")

    def test_lemma_style_dual_surface_m_gets_split(self) -> None:
        fixer = PluralSplitFixer(gate=StaticGate(plural_tokens={"š"}))
        row = TabletRow("1", "šm", "š/", "š", "n. m.", "ram", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "š/m")

    def test_singular_t_form_not_forced_to_plural(self) -> None:
        fixer = PluralSplitFixer(gate=StaticGate(plural_tokens={"dqt (I)"}))
        row = TabletRow("1", "dqt", "dqt(I)/", "dqt (I)", "n. f.", "small", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "dqt(I)/")

    def test_repairs_truncated_lemma_before_split_m(self) -> None:
        fixer = PluralSplitFixer(gate=StaticGate(plural_tokens={"šlm (II)"}))
        row = TabletRow(
            "1",
            "šlmm",
            "šl(II)/m",
            "šlm (II)",
            "n. m.",
            "communion victim / sacrifice",
            "",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "šlm(II)/m")


class SuffixCliticFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = SuffixCliticFixer(gate=StaticGate(suffix_tokens={"npš"}))

    def test_suffix_h_injected(self) -> None:
        row = TabletRow("1", "npšh", "npšh/", "npš", "n. f.", "throat", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "npš/+h")

    def test_already_has_plus_unchanged(self) -> None:
        row = TabletRow("1", "npšh", "npš/+h", "npš", "n. f.", "throat", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "npš/+h")

    def test_verb_not_changed(self) -> None:
        row = TabletRow("1", "yblh", "yblh[", "/y-b-l/", "vb", "to carry", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "yblh[")

    def test_false_suffix_candidate_without_dulat_support_unchanged(self) -> None:
        row = TabletRow("1", "abn", "abn/", "ảbn", "n. f.", "stone", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "abn/")

    def test_adds_suffix_to_lemma_style_prep(self) -> None:
        fixer = SuffixCliticFixer(gate=StaticGate(suffix_tokens={"l (I)"}))
        row = TabletRow("1", "lnh", "l(I)", "l (I)", "prep.", "to", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "l(I)+h")

    def test_adds_suffix_to_homonym_noun_with_slash(self) -> None:
        fixer = SuffixCliticFixer(gate=StaticGate(suffix_tokens={"šmm (I)"}))
        row = TabletRow("1", "šmmh", "šmm(I)/", "šmm (I)", "n. m.", "heavens", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "šmm(I)/+h")

    def test_adds_suffix_when_reconstruction_matches_surface_base(self) -> None:
        fixer = SuffixCliticFixer(gate=StaticGate(suffix_tokens={"l (I)"}))
        row = TabletRow("1", "ln", "l(I)", "l (I)", "prep.", "to", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "l(I)+n")

    def test_no_suffix_injection_when_reconstruction_does_not_match(self) -> None:
        fixer = SuffixCliticFixer(gate=StaticGate(suffix_tokens={"l (I)"}))
        row = TabletRow("1", "lhn", "hmlk/", "l (I)", "prep.", "to", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "hmlk/")

    def test_reverts_enclitic_plus_pattern(self) -> None:
        fixer = SuffixCliticFixer(gate=StaticGate(suffix_tokens={"bʕd"}))
        row = TabletRow("1", "bˤdn", "bˤd~+n", "bʕd", "adv., prep.", "behind", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "bˤd~n")

    def test_reverts_lexeme_final_n_split(self) -> None:
        fixer = SuffixCliticFixer(gate=StaticGate(suffix_tokens={"mṯn"}))
        row = TabletRow("1", "mṯn", "mṯ/+n", "mṯn", "n. m.", "repetition", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "mṯn/")

    def test_reverts_lexeme_final_n_split_for_lshan(self) -> None:
        fixer = SuffixCliticFixer(gate=StaticGate(suffix_tokens={"lšn"}))
        row = TabletRow("1", "lšn", "lš/+n", "lšn", "n. f.", "tongue", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "lšn/")

    def test_prefers_y_suffix_over_ny_when_lemma_ends_with_n(self) -> None:
        fixer = SuffixCliticFixer(gate=StaticGate(suffix_tokens={"bn (I)"}))
        row = TabletRow("1", "bny", "bn(I)/", "bn (I)", "n. m.", "son", "")
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "bn(I)/+y")


class WeakVerbFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = WeakVerbFixer()

    def test_prefix_y_wrapped_and_hidden_y_reconstructed(self) -> None:
        row = TabletRow("1", "yṯb", "yṯb[", "/y-ṯ-b/", "vb", "to sit down", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!y!(yṯb[")

    def test_existing_preformative_adds_hidden_initial_y(self) -> None:
        row = TabletRow("1", "yṯb", "!y!ṯb[", "/y-ṯ-b/", "vb", "to sit down", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!y!(yṯb[")

    def test_existing_surface_y_after_preformative_becomes_hidden_y(self) -> None:
        row = TabletRow("1", "ybl", "!y!ybl[", "/y-b-l/", "vb", "to carry", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!y!(ybl[")

    def test_t_preformative_variant_gets_hidden_initial_y(self) -> None:
        row = TabletRow("1", "ttn", "!t!tn[", "/y-t-n/", "vb", "to give", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!t!(ytn[")

    def test_aleph_preformative_variant_gets_hidden_initial_y(self) -> None:
        row = TabletRow("1", "atn", "!(ʔ&a!tn[", "/y-t-n/", "vb", "to give", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!(ʔ&a!(ytn[")

    def test_keeps_assimilated_n_before_hidden_y_in_n_stem(self) -> None:
        row = TabletRow("1", "yld", "!y!](n]yld[", "/y-l-d/", "vb N", "to give birth", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!y!](n](yld[")

    def test_non_weak_initial_verb_unchanged(self) -> None:
        row = TabletRow("1", "tqru", "tqrʔ[", "/q-r-ʔ/", "vb", "to call", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "tqrʔ[")

    def test_non_verb_unchanged(self) -> None:
        row = TabletRow("1", "yd", "yd/", "yd (I)", "n. f.", "hand", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "yd/")


class KnownAmbiguityExpanderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = KnownAmbiguityExpander()

    def test_expands_ydk_to_full_ambiguity_set(self) -> None:
        row = TabletRow("1", "ydk", "!y!dk[", "d-k(-k)/", "vb", "to be pounded", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(
            result.analysis,
            "yd(I)/+k;yd(I)/+k=;yd(II)/+k;yd(II)/+k=;!y!dk[;!y=!dk[",
        )
        self.assertEqual(
            result.dulat,
            "yd (I);yd (I);yd (II);yd (II);d-k(-k)/;d-k(-k)/",
        )
        self.assertEqual(result.pos, "n. f.;n. f.;n. m.;n. m.;vb;vb")
        self.assertEqual(result.gloss, "hand;hand;love;love;to be pounded;to be pounded")

    def test_expands_shlmm_to_enclitic_and_plural_variants(self) -> None:
        row = TabletRow(
            "1",
            "šlmm",
            "šlm(II)/m",
            "šlm (II)",
            "n. m.",
            "communion victim / sacrifice",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "šlm(II)/~m;šlm(II)/m")
        self.assertEqual(result.dulat, "šlm (II);šlm (II)")
        self.assertEqual(result.pos, "n. m.;n. m.")

    def test_non_matching_surface_is_unchanged(self) -> None:
        row = TabletRow("1", "ydh", "yd(I)/+h", "yd (I), -h (I)", "n. f.,pers. pn.", "hand", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "yd(I)/+h")


class SurfaceOptionPropagationFixerTest(unittest.TestCase):
    def test_propagates_richer_payload_for_same_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            rich = root / "KTU 1.1.tsv"
            poor = root / "KTU 1.2.tsv"

            rich.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tydk\t"
                    "yd(I)/+k;yd(I)/+k=;yd(II)/+k;yd(II)/+k=;!y!dk[;!y=!dk[\t"
                    "yd (I);yd (I);yd (II);yd (II);"
                    "d-k(-k)/;d-k(-k)/\t"
                    "n. f.;n. f.;n. m.;n. m.;vb;vb\t"
                    "hand;hand;love;love;"
                    "to be pounded;to be pounded\t\n"
                ),
                encoding="utf-8",
            )
            poor.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "2\tydk\t!y!dk[\td-k(-k)/\tvb\tto be pounded\t\n"
                ),
                encoding="utf-8",
            )

            fixer = SurfaceOptionPropagationFixer(corpus_dir=root)
            result = fixer.refine_file(poor)
            self.assertEqual(result.rows_changed, 1)
            line = poor.read_text(encoding="utf-8").splitlines()[1]
            self.assertIn("yd(I)/+k;yd(I)/+k=", line)
            self.assertIn(";!y=!dk[", line)

    def test_requires_dulat_overlap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            rich = root / "KTU 1.1.tsv"
            poor = root / "KTU 1.2.tsv"

            rich.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\taaa\taaa/;bbb/\taaa;bbb\tn. m.;n. m.\tone;two\t\n"
                ),
                encoding="utf-8",
            )
            poor.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "2\taaa\taaa/\tccc\tn. m.\tone\t\n"
                ),
                encoding="utf-8",
            )

            fixer = SurfaceOptionPropagationFixer(corpus_dir=root)
            result = fixer.refine_file(poor)
            self.assertEqual(result.rows_changed, 0)

    def test_requires_aligned_variant_subset_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            rich = root / "KTU 1.1.tsv"
            poor = root / "KTU 1.2.tsv"

            rich.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\taaa\taaa/;bbb/\td1;d2\tn. m.;vb\tone;two\t\n"
                ),
                encoding="utf-8",
            )
            poor.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "2\taaa\taaa/\td1\tvb\tone\t\n"
                ),
                encoding="utf-8",
            )

            fixer = SurfaceOptionPropagationFixer(corpus_dir=root)
            result = fixer.refine_file(poor)
            self.assertEqual(result.rows_changed, 0)

    def test_skips_surface_with_competing_rich_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            rich1 = root / "KTU 1.1.tsv"
            rich2 = root / "KTU 1.2.tsv"
            poor = root / "KTU 1.3.tsv"

            rich1.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tbbb\txxx/;yyy/\tdx;dy\tn. m.;vb\ta;b\t\n"
                ),
                encoding="utf-8",
            )
            rich2.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "2\tbbb\txxx/;zzz/\tdx;dz\tn. m.;vb\ta;c\t\n"
                ),
                encoding="utf-8",
            )
            poor.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "3\tbbb\txxx/\tdx\tn. m.\ta\t\n"
                ),
                encoding="utf-8",
            )

            fixer = SurfaceOptionPropagationFixer(corpus_dir=root)
            result = fixer.refine_file(poor)
            self.assertEqual(result.rows_changed, 0)

    def test_skips_payload_with_non_matching_reconstruction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            rich = root / "KTU 1.1.tsv"
            poor = root / "KTU 1.2.tsv"

            rich.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tbth\tbt(II)/+h;bt(I)/\tbt (II), -h (I);bt (I)\tn. f.;n. f.\thouse;house\t\n"
                ),
                encoding="utf-8",
            )
            poor.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "2\tbth\tbt(II)/+h\tbt (II), -h (I)\tn. f.\thouse\t\n"
                ),
                encoding="utf-8",
            )

            fixer = SurfaceOptionPropagationFixer(corpus_dir=root)
            result = fixer.refine_file(poor)
            self.assertEqual(result.rows_changed, 0)

    def test_skips_short_surface_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            rich = root / "KTU 1.1.tsv"
            poor = root / "KTU 1.2.tsv"

            rich.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tl\tl(I);l(II)\tl (I);l (II)\tprep.;adv.\tto;no\t\n"
                ),
                encoding="utf-8",
            )
            poor.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "2\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                ),
                encoding="utf-8",
            )

            fixer = SurfaceOptionPropagationFixer(corpus_dir=root, min_surface_len=3)
            result = fixer.refine_file(poor)
            self.assertEqual(result.rows_changed, 0)

    def test_respects_allowed_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            rich = root / "KTU 1.1.tsv"
            poor = root / "KTU 1.2.tsv"

            rich.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tydk\t"
                    "yd(I)/+k;yd(I)/+k=;yd(II)/+k;yd(II)/+k=;!y!dk[;!y=!dk[\t"
                    "yd (I);yd (I);yd (II);yd (II);"
                    "d-k(-k)/;d-k(-k)/\t"
                    "n. f.;n. f.;n. m.;n. m.;vb;vb\t"
                    "hand;hand;love;love;"
                    "to be pounded;to be pounded\t\n"
                ),
                encoding="utf-8",
            )
            poor.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "2\tydk\t!y!dk[\td-k(-k)/\tvb\tto be pounded\t\n"
                ),
                encoding="utf-8",
            )

            fixer = SurfaceOptionPropagationFixer(corpus_dir=root, allowed_surfaces={"npš"})
            result = fixer.refine_file(poor)
            self.assertEqual(result.rows_changed, 0)

    def test_collapses_duplicate_variants_and_merges_gloss_with_slash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            rich = root / "KTU 1.1.tsv"
            poor = root / "KTU 1.2.tsv"

            rich.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tytn\t!y!(ytn[;!y!(ytn[\t/y-t-n/;/y-t-n/\tvb;vb\tto give;to grant\t\n"
                ),
                encoding="utf-8",
            )
            poor.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "2\tytn\t!y!(ytn[\t/y-t-n/\tvb\tto give\t\n"
                ),
                encoding="utf-8",
            )

            fixer = SurfaceOptionPropagationFixer(corpus_dir=root, allowed_surfaces={"ytn"})
            result = fixer.refine_file(poor)
            self.assertEqual(result.rows_changed, 1)
            line = poor.read_text(encoding="utf-8").splitlines()[1]
            self.assertIn("\t!y!(ytn[\t/y-t-n/\tvb\tto give/to grant\t", line)

    def test_harmonizes_glosses_for_same_dulat_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            rich = root / "KTU 1.1.tsv"
            poor = root / "KTU 1.2.tsv"

            rich.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\thwt\thwt(I)/;hw(t(I)/t\thwt (I);hwt (I)\tn. f.;n. f.\tword;matter\t\n"
                ),
                encoding="utf-8",
            )
            poor.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "2\thwt\thwt(I)/\thwt (I)\tn. f.\tword\t\n"
                ),
                encoding="utf-8",
            )

            fixer = SurfaceOptionPropagationFixer(corpus_dir=root, allowed_surfaces={"hwt"})
            result = fixer.refine_file(poor)
            self.assertEqual(result.rows_changed, 1)
            line = poor.read_text(encoding="utf-8").splitlines()[1]
            self.assertIn(
                "\thwt(I)/;hw(t(I)/t\thwt (I);hwt (I)\tn. f.;n. f.\tword/matter;word/matter\t",
                line,
            )

    def test_normalizes_weak_final_w_variant_to_substitution_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            rich = root / "KTU 1.1.tsv"
            poor = root / "KTU 1.2.tsv"

            rich.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\ttˤny\t!t!ˤny(I)[;!t!ˤny[\t/ʕ-n-y/ (I);/ʕ-n-w/\tvb;vb\t"
                    "to answer;to be depressed\t\n"
                ),
                encoding="utf-8",
            )
            poor.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "2\ttˤny\t!t!ˤny(I)[\t/ʕ-n-y/ (I)\tvb\tto answer\t\n"
                ),
                encoding="utf-8",
            )

            fixer = SurfaceOptionPropagationFixer(corpus_dir=root, allowed_surfaces={"tˤny"})
            result = fixer.refine_file(poor)
            self.assertEqual(result.rows_changed, 1)
            line = poor.read_text(encoding="utf-8").splitlines()[1]
            self.assertIn("!t!ˤny(I)[;!t!ˤn(w&y[", line)


class WeakFinalSuffixConjugationFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = WeakFinalSuffixConjugationFixer()

    def test_weak_final_y_gets_sc_t_marker(self) -> None:
        row = TabletRow("1", "dit", "dʔy[", "/d-ʔ-y/", "vb", "to fly", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "dʔy[t")

    def test_weak_final_w_gets_sc_t_marker(self) -> None:
        row = TabletRow("1", "šnwt", "šnw[", "/š-n-w/", "vb", "to change", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "šnw[t")

    def test_prefixed_form_unchanged(self) -> None:
        row = TabletRow("1", "tkly", "!t!kly[", "/k-l-y/", "vb", "to finish", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!t!kly[")

    def test_aleph_prefixed_form_unchanged(self) -> None:
        row = TabletRow("1", "aklyt", "!(ʔ&a!kly[", "/k-l-y/", "vb", "to finish", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!(ʔ&a!kly[")

    def test_middle_radical_t_unchanged(self) -> None:
        row = TabletRow("1", "ytt", "ytn[", "/y-t-n/", "vb", "to give", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "ytn[")

    def test_already_marked_unchanged(self) -> None:
        row = TabletRow("1", "dit", "dʔy[t", "/d-ʔ-y/", "vb", "to fly", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "dʔy[t")

    def test_non_verb_variant_unchanged(self) -> None:
        row = TabletRow("1", "klt", "kl(I)/t=", "klt (I)", "n. f.", "bride", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "kl(I)/t=")


class BaalPluralGodListFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = BaalPluralGodListFixer()

    def test_collapses_mixed_baal_ambiguity(self) -> None:
        row = TabletRow(
            "149082",
            "bˤlm",
            "bˤl(II)/;bˤl(I)/m",
            "bʕl (II);bʕl (I)",
            "n. m./DN;n. m.",
            "Baʿlu;labourer",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "bˤl(II)/m")
        self.assertEqual(result.dulat, "bʕl (II)")
        self.assertEqual(result.pos, "n. m.")
        self.assertEqual(result.gloss, "lord")

    def test_unrelated_baal_entry_unchanged(self) -> None:
        row = TabletRow(
            "1",
            "bˤl",
            "bˤl(II)/",
            "bʕl (II)",
            "n. m./DN",
            "Baʿlu",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "bˤl(II)/")

    def test_collapses_plural_mixed_baal_ambiguity(self) -> None:
        row = TabletRow(
            "154108",
            "bˤlm",
            "bˤl(II)/m;bˤl(I)/m",
            "bʕl (II);bʕl (I)",
            "n. m.;n. m.",
            "lord;labourer, unskilled labourer",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "bˤl(II)/m")
        self.assertEqual(result.dulat, "bʕl (II)")
        self.assertEqual(result.pos, "n. m.")
        self.assertEqual(result.gloss, "lord")


class BaalLabourerKtu1FixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = BaalLabourerKtu1Fixer()

    def test_removes_labourer_variant_in_ktu1(self) -> None:
        content = (
            "#---- KTU 1.105 25\n"
            "152715\tbˤl\tbˤl(II)/;bˤl(I)/;bˤl[\t"
            "bʕl (II);bʕl (I);/b-ʕ-l/\tn. m./DN;n. m.;vb\t"
            "Baʿlu;labourer;to make\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            f = Path(tmp_dir) / "KTU 1.105.tsv"
            f.write_text(content, encoding="utf-8")
            result = self.fixer.refine_file(f)
            self.assertEqual(result.rows_changed, 1)
            line = f.read_text(encoding="utf-8").splitlines()[1]
            self.assertEqual(
                line,
                "152715\tbˤl\tbˤl(II)/;bˤl[/\tbʕl (II);/b-ʕ-l/\tn. m./DN;vb\tBaʿlu;to make\t",
            )

    def test_keeps_variant_outside_ktu1(self) -> None:
        content = (
            "#---- KTU 4.1 1\n"
            "900001\tbˤl\tbˤl(II)/;bˤl(I)/;bˤl[\t"
            "bʕl (II);bʕl (I);/b-ʕ-l/\tn. m./DN;n. m.;vb\t"
            "Baʿlu;labourer;to make\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            f = Path(tmp_dir) / "KTU 4.1.tsv"
            f.write_text(content, encoding="utf-8")
            result = self.fixer.refine_file(f)
            self.assertEqual(result.rows_changed, 1)
            line = f.read_text(encoding="utf-8").splitlines()[1]
            self.assertEqual(
                line,
                "900001\tbˤl\tbˤl(II)/;bˤl(I)/;bˤl[\t"
                "bʕl (II);bʕl (I);/b-ʕ-l/\tn. m./DN;n. m.;vb\t"
                "Baʿlu;labourer;to make\t",
            )


class BaalVerbalSlashFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = BaalVerbalSlashFixer()

    def test_normalizes_bare_baal_verbal_variant(self) -> None:
        row = TabletRow(
            "1",
            "bˤl",
            "bˤl[",
            "/b-ʕ-l/",
            "vb",
            "to make",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "bˤl[/")

    def test_normalizes_ambiguous_row_variant_in_place(self) -> None:
        row = TabletRow(
            "1",
            "bˤl",
            "bˤl(II)/;bˤl[",
            "bʕl (II);/b-ʕ-l/",
            "n. m./DN;vb",
            "Baʿlu;to make",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "bˤl(II)/;bˤl[/")

    def test_non_baal_verbal_row_unchanged(self) -> None:
        row = TabletRow(
            "1",
            "rkb",
            "rkb[",
            "/r-k-b/",
            "vb",
            "to mount",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "rkb[")


class VerbPosStemFixerTest(unittest.TestCase):
    def _build_test_db(self, path: Path) -> None:
        conn = sqlite3.connect(str(path))
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE entries ("
            "entry_id INTEGER PRIMARY KEY, "
            "lemma TEXT, homonym TEXT, pos TEXT)"
        )
        cur.execute("CREATE TABLE forms (entry_id INTEGER, text TEXT, morphology TEXT)")
        cur.executemany(
            "INSERT INTO entries(entry_id, lemma, homonym, pos) VALUES (?, ?, ?, ?)",
            [
                (1, "/y-t-n/", "", "vb"),
                (2, "/r-g-m/", "", "vb"),
                (3, "ytn", "I", "n."),
                (4, "/l-s-m/", "", "vb"),
                (5, "/š-q-y/", "", "vb"),
            ],
        )
        cur.executemany(
            "INSERT INTO forms(entry_id, text, morphology) VALUES (?, ?, ?)",
            [
                (1, "ytn", "G, prefc."),
                (1, "ytn", "Š, prefc."),
                (2, "rgm", "G, suffc."),
                (3, "ytn", "pl."),
                (4, "tslmn", "G, prefc."),
                (5, "yšqy", "G, prefc."),
                (5, "yšqyn", "G, prefc."),
            ],
        )
        conn.commit()
        conn.close()

    def test_appends_stem_to_verb_pos(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._build_test_db(db_path)
            fixer = VerbPosStemFixer(dulat_db=db_path)

            row = TabletRow("1", "rgm", "rgm[", "/r-g-m/", "vb", "to say", "")
            result = fixer.refine_row(row)

            self.assertEqual(result.pos, "vb G")

    def test_appends_multiple_stems_in_stable_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._build_test_db(db_path)
            fixer = VerbPosStemFixer(dulat_db=db_path)

            row = TabletRow("1", "ytn", "!y!ytn[", "/y-t-n/", "vb", "to give", "")
            result = fixer.refine_row(row)

            self.assertEqual(result.pos, "vb G/Š")

    def test_non_verb_pos_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._build_test_db(db_path)
            fixer = VerbPosStemFixer(dulat_db=db_path)

            row = TabletRow("1", "ytn", "ytn/", "ytn (I)", "n.", "gift", "")
            result = fixer.refine_row(row)

            self.assertEqual(result.pos, "n.")

    def test_pos_with_existing_stem_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._build_test_db(db_path)
            fixer = VerbPosStemFixer(dulat_db=db_path)

            row = TabletRow("1", "rgm", "rgm[", "/r-g-m/", "vb G", "to say", "")
            result = fixer.refine_row(row)

            self.assertEqual(result.pos, "vb G")

    def test_non_head_vb_phrase_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._build_test_db(db_path)
            fixer = VerbPosStemFixer(dulat_db=db_path)

            row = TabletRow(
                "1",
                "n",
                "+n",
                "-n (II)",
                "suffixed pn. morph. used with vb",
                "me",
                "",
            )
            result = fixer.refine_row(row)

            self.assertEqual(result.pos, "suffixed pn. morph. used with vb")

    def test_applies_form_text_alias_override_for_stem_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._build_test_db(db_path)
            fixer = VerbPosStemFixer(dulat_db=db_path)

            row = TabletRow("1", "tlsmn", "!t!lsm[n", "/l-s-m/", "vb", "to run", "")
            result = fixer.refine_row(row)

            self.assertEqual(result.pos, "vb G")

    def test_uses_analysis_host_when_surface_includes_suffix_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "dulat.sqlite"
            self._build_test_db(db_path)
            fixer = VerbPosStemFixer(dulat_db=db_path)

            row = TabletRow(
                "1",
                "yšqynh",
                "!y!šqy[+nh",
                "/š-q-y/",
                "vb",
                "to offer (something to) drink",
                "",
            )
            result = fixer.refine_row(row)

            self.assertEqual(result.pos, "vb G")


class VerbLStemGeminationFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = VerbLStemGeminationFixer()

    def test_promotes_geminated_l_stem_radical_before_closure(self) -> None:
        row = TabletRow(
            "1",
            "tqṭṭ",
            "!t!qṭ[ṭ:l",
            "/q-ṭ(-ṭ)/",
            "vb L",
            "to commit transgression",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!t!qṭṭ[:l")

    def test_keeps_non_geminate_inflection_tail_after_promotion(self) -> None:
        row = TabletRow(
            "1",
            "tqṭṭn",
            "!t!qṭ[ṭn:l",
            "/q-ṭ(-ṭ)/",
            "vb L",
            "to commit transgression",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!t!qṭṭ[n:l")

    def test_skips_non_l_stem_rows(self) -> None:
        row = TabletRow(
            "1",
            "tqṭṭ",
            "!t!qṭ[ṭ:d",
            "/q-ṭ(-ṭ)/",
            "vb D",
            "to commit transgression",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!t!qṭ[ṭ:d")

    def test_skips_when_stem_already_geminated(self) -> None:
        row = TabletRow(
            "1",
            "tqṭṭ",
            "!t!qṭṭ[:l",
            "/q-ṭ(-ṭ)/",
            "vb L",
            "to commit transgression",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!t!qṭṭ[:l")


class VerbStemSuffixMarkerFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = VerbStemSuffixMarkerFixer()

    def test_adds_d_marker_for_vb_d(self) -> None:
        row = TabletRow("1", "kbd", "kbd[", "/k-b-d/", "vb D", "to honour", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "kbd[:d")

    def test_adds_l_marker_before_suffix_payload(self) -> None:
        row = TabletRow("1", "yknh", "!y!knn[+h", "/k-n/", "vb L", "to be stable", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!y!knn[:l+h")

    def test_adds_passive_marker_for_passive_stem(self) -> None:
        row = TabletRow("1", "qtl", "qtl[", "/q-t-l/", "vb Dpass", "to be killed", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "qtl[:pass")

    def test_keeps_nonverbal_row_unchanged(self) -> None:
        row = TabletRow("1", "kbd", "kbd/", "kbd (I)", "n. f.", "liver", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "kbd/")

    def test_does_not_touch_deverbal_nominal_analysis(self) -> None:
        row = TabletRow("1", "qtl", "qtl[/", "/q-t-l/", "vb D", "killing", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "qtl[/")


class VerbNStemAssimilationFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = VerbNStemAssimilationFixer()

    def test_inserts_assimilated_n_for_prefixed_n_stem(self) -> None:
        row = TabletRow("1", "tṯbr", "!t!ṯbr[", "/ṯ-b-r/", "vb N", "to break", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!t!](n]ṯbr[")

    def test_inserts_assimilated_n_for_aleph_prefixed_n_stem(self) -> None:
        row = TabletRow("1", "aṯbr", "!(ʔ&a!ṯbr[", "/ṯ-b-r/", "vb N", "to break", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!(ʔ&a!](n]ṯbr[")

    def test_keeps_row_when_marker_already_present(self) -> None:
        row = TabletRow("1", "tṯbr", "!t!](n]ṯbr[", "/ṯ-b-r/", "vb N", "to break", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!t!](n]ṯbr[")

    def test_keeps_non_prefixed_n_stem_row_unchanged(self) -> None:
        row = TabletRow("1", "nṯbr", "nṯbr[", "/ṯ-b-r/", "vb N", "to break", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "nṯbr[")

    def test_collapses_repeated_assimilated_n_insertions(self) -> None:
        row = TabletRow(
            "1",
            "yld",
            "!y!](n](y](n](y](n](yld[",
            "/y-l-d/",
            "vb N",
            "to give birth",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!y!](n](yld[")

    def test_normalizes_semicolon_variants_independently(self) -> None:
        row = TabletRow(
            "1",
            "yld",
            "!y!yld[; yld[/",
            "/y-l-d/; /y-l-d/",
            "vb N; vb N",
            "to give birth; to give birth",
            "",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!y!](n]yld[; yld[/")


class PrefixedIIIAlephVerbFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = PrefixedIIIAlephVerbFixer()

    def test_rewrites_prefixed_iii_aleph_g_form(self) -> None:
        row = TabletRow("1", "tḫṭu", "ḫṭʔ[u", "/ḫ-ṭ-ʔ/", "vb G", "to make a mistake", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!t!ḫṭ(ʔ[&u")

    def test_rewrites_prefixed_iii_aleph_aleph_preformative(self) -> None:
        row = TabletRow("1", "iqra", "qrʔ[a", "/q-r-ʔ/", "vb G", "to call", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!(ʔ&i!qr(ʔ[&a")

    def test_rewrites_prefixed_iii_aleph_n_form(self) -> None:
        row = TabletRow("2", "nḫtu", "ḫtʔ[u", "/ḫ-t-ʔ/", "vb N", "to be ground up", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!n!ḫt(ʔ[&u")

    def test_keeps_already_prefixed_row_unchanged(self) -> None:
        row = TabletRow("3", "tḫṭu", "!t!ḫṭ(ʔ[&u", "/ḫ-ṭ-ʔ/", "vb G", "to make a mistake", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "!t!ḫṭ(ʔ[&u")

    def test_skips_non_iii_aleph_root(self) -> None:
        row = TabletRow("4", "tqtl", "qtl[u", "/q-t-l/", "vb G", "to kill", "")
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "qtl[u")


class OfferingListLPrepFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = OfferingListLPrepFixer()

    def test_collapses_ambiguous_l_in_offering_sequence(self) -> None:
        content = textwrap.dedent(
            """\
            #---- KTU 1.119 1
            154176\tgdlt\tgdl(I)/t=\tgdlt (I)\tn. f.\thead of cattle
            154177\tl\tl(I);l(II);l(III)\tl (I);l (II);l (III)\tprep.;adv.;functor\tto;no;certainly
            154178\tbˤlm\tbˤl(II)/m\tbʕl (II)\tn. m.\tlord
            """
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            f = Path(tmp_dir) / "test.tsv"
            f.write_text(content, encoding="utf-8")
            result = self.fixer.refine_file(f)
            self.assertEqual(result.rows_changed, 3)
            lines = f.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[2], "154177\tl\tl(I)\tl (I)\tprep.\tto\t")

    def test_non_offering_context_unchanged(self) -> None:
        content = textwrap.dedent(
            """\
            #---- KTU 1.1 1
            135588\tḥẓr\tḥẓr/\tḥẓr\tn. m.\tmansion
            135589\tl\tl(I);l(II);l(III)\tl (I);l (II);l (III)\tprep.;adv.;functor\tto;no;certainly
            135590\tpˤn\tpˤn/\tpʕn\tn. f.\tfoot
            """
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            f = Path(tmp_dir) / "test.tsv"
            f.write_text(content, encoding="utf-8")
            result = self.fixer.refine_file(f)
            self.assertEqual(result.rows_changed, 3)


class AttestationSortFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.index = DulatAttestationIndex(
            counts_by_key={
                ("bʕl", "II"): 200,
                ("ʕbd", ""): 20,
                ("il", "I"): 600,
                ("mlk", ""): 120,
            },
            max_count_by_lemma={
                "bʕl": 200,
                "ʕbd": 20,
                "il": 600,
                "mlk": 120,
            },
        )
        self.fixer = AttestationSortFixer(index=self.index)

    def test_reorders_aligned_variants_by_attestation_count(self) -> None:
        row = TabletRow(
            line_id="1",
            surface="x",
            analysis="a1;a2;a3",
            dulat="ʕbd;bʕl (II);ỉl (I)",
            pos="p1;p2;p3",
            gloss="g1;g2;g3",
            comment="free comment",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "a3;a2;a1")
        self.assertEqual(result.dulat, "ỉl (I);bʕl (II);ʕbd")
        self.assertEqual(result.pos, "p3;p2;p1")
        self.assertEqual(result.gloss, "g3;g2;g1")
        self.assertEqual(result.comment, "free comment")

    def test_uses_first_dulat_entry_before_comma_for_ranking(self) -> None:
        row = TabletRow(
            line_id="2",
            surface="x",
            analysis="a1;a2",
            dulat="mlk, -m (I);ʕbd, -k (I)",
            pos="p1;p2",
            gloss="g1;g2",
            comment="c1;c2",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "a1;a2")
        self.assertEqual(result.comment, "c1;c2")

    def test_reorders_comment_when_comment_variants_are_aligned(self) -> None:
        row = TabletRow(
            line_id="3",
            surface="x",
            analysis="a1;a2",
            dulat="ʕbd;bʕl (II)",
            pos="p1;p2",
            gloss="g1;g2",
            comment="c1;c2",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.analysis, "a2;a1")
        self.assertEqual(result.comment, "c2;c1")


class OnomasticGlossOverrideFixerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = OnomasticGlossOverrideFixer(
            overrides={
                "ỉlmlk": "ʾIlimalku",
                "kṯr (III)": "Kôṯaru",
                "ḫss": "Ḫasisu",
                "ỉl (I)": "ʾIlu",
            }
        )

    def test_override_by_dulat_entry(self) -> None:
        row = TabletRow(
            line_id="1",
            surface="ilmlk",
            analysis="ilmlk/",
            dulat="ỉlmlk",
            pos="PN",
            gloss="Ilimalku",
            comment="",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.gloss, "ʾIlimalku")

    def test_does_not_override_when_pos_is_not_onomastic(self) -> None:
        row = TabletRow(
            line_id="1b",
            surface="il",
            analysis="il(I)/",
            dulat="ỉl (I)",
            pos="n. m.",
            gloss="god",
            comment="",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.gloss, "god")

    def test_override_applies_to_split_name_sequence(self) -> None:
        row = TabletRow(
            line_id="2",
            surface="kṯr",
            analysis="kṯr(III)/",
            dulat="kṯr (III)",
            pos="DN",
            gloss="?",
            comment="",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.gloss, "Kôṯaru")

    def test_slot_level_override_preserves_non_name_clitic_slot(self) -> None:
        row = TabletRow(
            line_id="3",
            surface="kṯrh",
            analysis="kṯr(III)/+h(I)",
            dulat="kṯr (III), -h (I)",
            pos="DN, pers. pn.",
            gloss="kṯr (III), his /her",
            comment="",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.gloss, "Kôṯaru, his /her")

    def test_normalizes_aleph_ayin_for_onomastic_pos_without_override(self) -> None:
        row = TabletRow(
            line_id="4",
            surface="x",
            analysis="x/",
            dulat="x",
            pos="TN",
            gloss="ˀxʕyˁzʔ",
            comment="",
        )
        result = self.fixer.refine_row(row)
        self.assertEqual(result.gloss, "ʾxʿyʿzʾ")


class GenericParsingOverrideFixerTest(unittest.TestCase):
    def test_applies_full_override_by_surface(self) -> None:
        fixer = GenericParsingOverrideFixer(
            overrides={
                "n": GenericOverride(
                    analysis="l(I)",
                    dulat="l (I)",
                    pos="prep.",
                    gloss="to",
                    comment="manual generic override",
                )
            }
        )
        row = TabletRow(
            line_id="1",
            surface="n",
            analysis="l(I); ˤl(I); mġy[",
            dulat="l (I); ʕl (I); /m-ġ-y/",
            pos="prep.; prep.; vb",
            gloss="to; upon; to come",
            comment="",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "l(I)")
        self.assertEqual(result.dulat, "l (I)")
        self.assertEqual(result.pos, "prep.")
        self.assertEqual(result.gloss, "to")
        self.assertEqual(result.comment, "manual generic override")

    def test_blank_optional_columns_preserve_existing_values(self) -> None:
        fixer = GenericParsingOverrideFixer(overrides={"km": GenericOverride(analysis="k(III)")})
        row = TabletRow(
            line_id="2",
            surface="km",
            analysis="k(III); k(I); k(IV)",
            dulat="k (III); k (I); k (IV)",
            pos="Subordinating or completive functor; prep.; adv.",
            gloss="when; like; thus",
            comment="existing note",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "k(III)")
        self.assertEqual(result.dulat, row.dulat)
        self.assertEqual(result.pos, row.pos)
        self.assertEqual(result.gloss, row.gloss)
        self.assertEqual(result.comment, row.comment)

    def test_applies_override_to_unresolved_row_during_file_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(
                (
                    "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                    "1\tlp\t?\t?\t?\t?\tDULAT: NOT FOUND\n"
                ),
                encoding="utf-8",
            )
            fixer = GenericParsingOverrideFixer(
                overrides={
                    "lp": GenericOverride(
                        analysis="l+p(I)",
                        dulat="l (I), p (I)",
                        pos="prep., conj. functor",
                        gloss="to, and",
                        comment="manual resolution",
                    )
                }
            )
            result = fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 1)
            line = path.read_text(encoding="utf-8").splitlines()[1]
            self.assertEqual(
                line,
                "1\tlp\tl+p(I)\tl (I), p (I)\tprep., conj. functor\tto, and\tmanual resolution",
            )

    def test_project_default_overrides_restore_hrshnr_payload(self) -> None:
        fixer = GenericParsingOverrideFixer()
        row = TabletRow(
            line_id="135554",
            surface="ḫršnr",
            analysis="?",
            dulat="?",
            pos="?",
            gloss="?",
            comment="DULAT: NOT FOUND",
        )
        result = fixer.refine_row(row)
        self.assertEqual(result.analysis, "ḫršn&r/")
        self.assertEqual(result.dulat, "ḫršn (I)")
        self.assertEqual(result.pos, "n. m.")
        self.assertEqual(result.gloss, "(divine) mountain")


class TsvSchemaFormatterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixer = TsvSchemaFormatter()
        self.header = "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments"
        self.separator = "# KTU 1.5 I:4\t\t\t\t\t\t"

    def test_normalizes_separator_and_expands_to_7_columns(self) -> None:
        content = textwrap.dedent(
            """\
            #---------------------------- KTU 1.5 I:4
            100\tabc\tabc/\tabc\tn. m.\tthing
            """
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            f = Path(tmp_dir) / "test.tsv"
            f.write_text(content, encoding="utf-8")
            result = self.fixer.refine_file(f)
            self.assertEqual(result.rows_changed, 3)
            lines = f.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[0], self.header)
            self.assertEqual(lines[1], self.separator)
            self.assertEqual(lines[2], "100\tabc\tabc/\tabc\tn. m.\tthing\t")

    def test_merges_extra_columns_into_comment(self) -> None:
        content = textwrap.dedent(
            """\
            # KTU 1.5 I:4
            101\tabc\tabc/\tabc\tn. m.\tthing\tc1\tc2
            """
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            f = Path(tmp_dir) / "test.tsv"
            f.write_text(content, encoding="utf-8")
            result = self.fixer.refine_file(f)
            self.assertEqual(result.rows_changed, 3)
            lines = f.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[0], self.header)
            self.assertEqual(lines[1], self.separator)
            self.assertEqual(lines[2], "101\tabc\tabc/\tabc\tn. m.\tthing\tc1 c2")

    def test_escapes_quotes_in_data_columns(self) -> None:
        content = textwrap.dedent(
            """\
            # KTU 1.5 I:4
            102\tabc\tabc/\tabc\tn. m.\tthing\tUNP: "quoted"
            """
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            f = Path(tmp_dir) / "test.tsv"
            f.write_text(content, encoding="utf-8")
            result = self.fixer.refine_file(f)
            self.assertEqual(result.rows_changed, 3)
            lines = f.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[1], self.separator)
            self.assertEqual(lines[2], "102\tabc\tabc/\tabc\tn. m.\tthing\tUNP: 'quoted'")

    def test_preserves_existing_header_without_change(self) -> None:
        content = textwrap.dedent(
            """\
            id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments
            # KTU 1.5 I:4\t\t\t\t\t\t
            103\tabc\tabc/\tabc\tn. m.\tthing\t
            """
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            f = Path(tmp_dir) / "test.tsv"
            f.write_text(content, encoding="utf-8")
            result = self.fixer.refine_file(f)
            self.assertEqual(result.rows_changed, 0)
            lines = f.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[0], self.header)
            self.assertEqual(lines[1], self.separator)

    def test_drops_repeated_header_like_junk_rows(self) -> None:
        content = textwrap.dedent(
            """\
            id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments
            id\tsurface form\tsurface form\t\t\t\tDULAT: NOT FOUND
            id\tsurface form\t?\t?\t?\t?\tDULAT: NOT FOUND
            # KTU 1.5 I:4\t\t\t\t\t\t
            103\tabc\tabc/\tabc\tn. m.\tthing\t
            """
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            f = Path(tmp_dir) / "test.tsv"
            f.write_text(content, encoding="utf-8")
            result = self.fixer.refine_file(f)
            self.assertEqual(result.rows_changed, 2)
            lines = f.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[0], self.header)
            self.assertEqual(lines[1], self.separator)
            self.assertEqual(lines[2], "103\tabc\tabc/\tabc\tn. m.\tthing\t")

    def test_normalizes_variant_divider_spacing_in_structured_columns(self) -> None:
        content = textwrap.dedent(
            """\
            # KTU 1.5 I:4
            104\tabc\ta;b\tx,y;z,w\tp,q;r,s\tg1,g2;g3,g4\tc1;c2
            """
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            f = Path(tmp_dir) / "test.tsv"
            f.write_text(content, encoding="utf-8")
            result = self.fixer.refine_file(f)
            self.assertEqual(result.rows_changed, 3)
            lines = f.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                lines[2],
                "104\tabc\ta; b\tx, y; z, w\tp, q; r, s\tg1, g2; g3, g4\tc1;c2",
            )

    def test_keeps_space_after_semicolon_when_next_variant_starts_with_comma(self) -> None:
        content = textwrap.dedent(
            """\
            # KTU 1.5 I:4
            105\tabc\ta;b\tx,y\t, p1;, p2\t, g1;, g2\t
            """
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            f = Path(tmp_dir) / "test.tsv"
            f.write_text(content, encoding="utf-8")
            result = self.fixer.refine_file(f)
            self.assertEqual(result.rows_changed, 3)
            lines = f.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[2], "105\tabc\ta; b\tx, y\t, p1; , p2\t, g1; , g2\t")


class RefineFileIntegrationTest(unittest.TestCase):
    def test_refine_file_preserves_structure(self) -> None:
        content = textwrap.dedent(
            """\
            #---- KTU 1.100 1
            12345\tum\tum/\tủm\tn. f.\tmother
            12346\tx\t?\t?\t?\t?\tDULAT: NOT FOUND
            #---- KTU 1.100 2
            12347\tbn\tbn\tbn (I)\tn. m.\tson
        """
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            f = Path(tmp_dir) / "test.tsv"
            f.write_text(content, encoding="utf-8")

            fixer = NounPosClosureFixer()
            result = fixer.refine_file(f)

            self.assertEqual(result.rows_processed, 3)
            self.assertEqual(result.rows_changed, 2)

            lines = f.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[0], "# KTU 1.100 1")
            self.assertTrue(lines[2].startswith("12346\tx\t?"))
            self.assertIn("bn/", lines[4])

    def test_refine_file_idempotent(self) -> None:
        content = textwrap.dedent(
            """\
            #---- KTU 1.100 1
            12345\tum\tum/\tủm\tn. f.\tmother
        """
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            f = Path(tmp_dir) / "test.tsv"
            f.write_text(content, encoding="utf-8")

            fixer = NounPosClosureFixer()
            r1 = fixer.refine_file(f)
            r2 = fixer.refine_file(f)

            self.assertEqual(r1.rows_changed, 1)
            self.assertEqual(r2.rows_changed, 0)


if __name__ == "__main__":
    unittest.main()
