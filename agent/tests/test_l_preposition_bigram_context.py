"""Tests for high-confidence `l + X` prepositional bigram normalization."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.l_preposition_bigram_context import LPrepositionBigramContextDisambiguator


class LPrepositionBigramContextDisambiguatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = LPrepositionBigramContextDisambiguator()

    def test_forces_l_i_before_generic_nominal_target(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\tarṣ\tarṣ/\tảrṣ\tn. f.\tearth\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 3)
            self.assertEqual(result.rows_changed, 1)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("1\tl\tl(I)\tl (I)\tprep.\tto\t", lines)
            self.assertNotIn("1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t", lines)

    def test_forces_l_i_and_baal_ii_outside_ktu4(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\tbˤl\tbˤl(II)/\tbʕl (II)\tn. m./DN\tBaʿlu/Baal\t\n"
            "2\tbˤl\tbˤl[\t/b-ʕ-l/\tvb\tto make\t\n"
            "3\tarṣ\tarṣ/\tảrṣ\tn. f.\tearth\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 5)
            self.assertEqual(result.rows_changed, 2)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("1\tl\tl(I)\tl (I)\tprep.\tto\t", lines)
            self.assertIn("2\tbˤl\tbˤl(II)/\tbʕl (II)\tn. m./DN\tBaʿlu/Baal\t", lines)
            self.assertNotIn("1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t", lines)
            self.assertNotIn("2\tbˤl\tbˤl[\t/b-ʕ-l/\tvb\tto make\t", lines)

    def test_keeps_l_baal_unchanged_for_ktu4_tablets(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\tbˤl\tbˤl(II)/\tbʕl (II)\tn. m./DN\tBaʿlu/Baal\t\n"
            "2\tbˤl\tbˤl[\t/b-ʕ-l/\tvb\tto make\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 4.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 4)
            self.assertEqual(result.rows_changed, 0)
            self.assertEqual(path.read_text(encoding="utf-8"), content)

    def test_collapses_l_pn_to_preposition_payload(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tl\tl(I)\tl (I)\tprep.\tto\t\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\tpn\tpn(m/\tpnm\tn. m. pl. tant.\tface\t\n"
            "2\tpn\tpn\tpn\tfunctor\tlest\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 4)
            self.assertEqual(result.rows_changed, 3)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("1\tl\tl(I)\tl (I)\tprep.\tto\t", lines)
            self.assertIn("2\tpn\tpn(m/\tpnm\tn. m. pl. tant.\tin front\t", lines)
            self.assertNotIn("1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t", lines)
            self.assertNotIn("2\tpn\tpn\tpn\tfunctor\tlest\t", lines)

    def test_normalizes_l_pnh_functor_style_to_preposition(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t\n"
            "2\tpnh\tpn/(m+h=\tpn\tfunctor\tlest\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_processed, 2)
            self.assertEqual(result.rows_changed, 2)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertIn("1\tl\tl(I)\tl (I)\tprep.\tto\t", lines)
            self.assertIn("2\tpnh\tpn(m/+h\tpnm\tn. m. pl. tant.\tin front\t", lines)
            self.assertNotIn("1\tl\tl(III)\tl (III)\tfunctor\tcertainly\t", lines)
            self.assertNotIn("2\tpnh\tpn/(m+h=\tpn\tfunctor\tlest\t", lines)


if __name__ == "__main__":
    unittest.main()
