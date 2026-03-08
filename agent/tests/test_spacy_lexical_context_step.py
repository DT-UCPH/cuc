"""File-level tests for the integrated spaCy-based lexical context steps."""

import tempfile
import unittest
from pathlib import Path

from pipeline.dulat_attestation_index import DulatAttestationIndex, normalize_reference_label
from pipeline.steps.spacy_lexical_context import (
    SpacyBaalContextDisambiguator,
    SpacyYdkContextDisambiguator,
)


class SpacyBaalContextDisambiguatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = SpacyBaalContextDisambiguator()

    def test_prunes_baal_labourer_outside_ktu4(self) -> None:
        content = "\n".join(
            [
                (
                    "1\tbˤl\tbˤl(II)/;bˤl(I)/;bˤl[\tbʕl (II);bʕl (I);/b-ʕ-l/"
                    "\tn. m./DN;n. m.;vb\tBaʿlu;labourer;to make\t"
                ),
                "",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 1)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                lines[0],
                "1\tbˤl\tbˤl(II)/;bˤl[/\tbʕl (II);/b-ʕ-l/\tn. m./DN;vb\tBaʿlu;to make\t",
            )

    def test_collapses_aliyn_baal_sequence_to_dn_only(self) -> None:
        content = "\n".join(
            [
                "1\taliyn\taliyn/\tảlỉyn\tadj. m. sg. abs. nom.\tThe Very / Most Powerful\t",
                "2\tbˤl\tbˤl(II)/\tbʕl (II)\tDN pl. cstr.\tBaʿlu/Baal\t",
                "2\tbˤl\tbˤl(II)/\tbʕl (II)\tDN sg.\tBaʿlu/Baal\t",
                "2\tbˤl\tbˤl(II)/\tbʕl (II)\tn. m. pl. cstr.\tBaʿlu/Baal\t",
                "2\tbˤl\tbˤl(II)/\tbʕl (II)\tn. m. sg.\tBaʿlu/Baal\t",
                "2\tbˤl\tbˤl[/\t/b-ʕ-l/\tvb G act. ptcpl. m. sg. abs. nom.\tto make\t",
                "",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 5)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                lines[1], "2\tbˤl\tbˤl(II)/\tbʕl (II)\tDN m. sg. abs. nom.\tBaʿlu/Baal\t"
            )
            self.assertEqual(len([line for line in lines if line.startswith("2\tbˤl\t")]), 1)

    def test_prunes_unattested_baal_verbal_variant(self) -> None:
        content = "\n".join(
            [
                "# KTU 1.5 I:10",
                "1\tbˤl\tbˤl(II)/\tbʕl (II)\tn. m. sg. cstr. gen.\tBaʿlu/Baal\t",
                "1\tbˤl\tbˤl[/\t/b-ʕ-l/\tvb G act. ptcpl. m. sg. cstr. gen.\tto make\t",
                "",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 1)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                lines[1],
                "1\tbˤl\tbˤl(II)/\tbʕl (II)\tn. m. sg. cstr. gen.\tBaʿlu/Baal\t",
            )
            self.assertEqual(len([line for line in lines if line.startswith("1\tbˤl\t")]), 1)

    def test_keeps_attested_baal_verbal_variant(self) -> None:
        attestation_index = DulatAttestationIndex(
            counts_by_key={},
            max_count_by_lemma={},
            refs_by_key={("/b-ʕ-l/", ""): {normalize_reference_label("CAT 1.17 VI:24")}},
        )
        step = SpacyBaalContextDisambiguator(attestation_index=attestation_index)
        content = "\n".join(
            [
                "# KTU 1.17 VI:24",
                "1\tbˤl\tbˤl(II)/\tbʕl (II)\tn. m. sg. abs. nom.\tBaʿlu/Baal\t",
                "1\tbˤl\tbˤl[/\t/b-ʕ-l/\tvb G act. ptcpl. m. sg. abs. nom.\tto make\t",
                "",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = step.refine_file(path)

            self.assertEqual(result.rows_changed, 0)

    def test_prunes_unattested_bt_house_variant(self) -> None:
        content = "\n".join(
            [
                "# KTU 1.3 I:24",
                "1\tbt\tbt(II)/\tbt (II)\tn. m. sg. cstr. gen.\thouse\t",
                "1\tbt\tb(t(I)/t\tbt (I)\tn. f. sg. cstr. gen.\tdaughter\t",
                "2\tar\tar/\tả/ỉr\tn. m. sg. abs. gen.\tlight\t",
                "",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 2)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                lines[1],
                "1\tbt\tb(t(I)/t\tbt (I)\tn. f. sg. cstr. gen.\tdaughter\t",
            )
            self.assertEqual(len([line for line in lines if line.startswith("1\tbt\t")]), 1)

    def test_keeps_bt_house_variant_in_baal_phrase(self) -> None:
        content = "\n".join(
            [
                "# KTU 1.3 VI:3",
                "1\tbt\tbt(II)/\tbt (II)\tn. m. sg. abs. nom.\thouse\t",
                "1\tbt\tb(t(I)/t\tbt (I)\tn. f. sg. abs. nom.\tdaughter\t",
                "2\tl\tl(I)\tl (I)\tprep.\tto\t",
                "3\tbˤl\tbˤl(II)/\tbʕl (II)\tn. m. pl. abs. gen.\tBaʿlu/Baal\t",
                "",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 1)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                lines[1],
                "1\tbt\tbt(II)/\tbt (II)\tn. m. sg. abs. nom.\thouse\t",
            )
            self.assertEqual(len([line for line in lines if line.startswith("1\tbt\t")]), 1)

    def test_keeps_directly_attested_bt_house_variant(self) -> None:
        attestation_index = DulatAttestationIndex(
            counts_by_key={},
            max_count_by_lemma={},
            refs_by_key={("bt", "II"): {normalize_reference_label("CAT 1.3 V:3")}},
        )
        step = SpacyBaalContextDisambiguator(attestation_index=attestation_index)
        content = "\n".join(
            [
                "# KTU 1.3 V:3",
                "1\tbt\tbt(II)/\tbt (II)\tn. m. sg. abs. nom.\thouse\t",
                "1\tbt\tb(t(I)/t\tbt (I)\tn. f. sg. abs. nom.\tdaughter\t",
                "",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = step.refine_file(path)

            self.assertEqual(result.rows_changed, 1)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                lines[1],
                "1\tbt\tbt(II)/\tbt (II)\tn. m. sg. abs. nom.\thouse\t",
            )
            self.assertEqual(len([line for line in lines if line.startswith("1\tbt\t")]), 1)

    def test_collapses_thr_il_sequence_to_bull_and_el(self) -> None:
        content = "\n".join(
            [
                "1\tṯr\tṯr(I)/\tṯr (I)\tn. m. pl. abs. nom.\tbull\t",
                "1\tṯr\tṯr(I)/\tṯr (I)\tn. m. sg. abs. nom.\tbull\t",
                "2\til\til(I)/\tỉl (I)\tDN sg. abs. nom.\tʾIlu/Ilu/El\t",
                "2\til\til(I)/\tỉl (I)\tDN sg. cstr. nom.\tʾIlu/Ilu/El\t",
                "2\til\til(I)/\tỉl (I)\tDN m. sg. abs. nom.\tʾIlu/Ilu/El\t",
                "2\til\til(I)/\tỉl (I)\tDN m. sg. cstr. nom.\tʾIlu/Ilu/El\t",
                "2\til\til(I)/\tỉl (I)\tn. m. sg. abs. nom.\tgod\t",
                "2\til\til(I)/\tỉl (I)\tn. m. sg. cstr. nom.\tgod\t",
                "",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 8)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[0], "1\tṯr\tṯr(I)/\tṯr (I)\tn. m. sg. abs. nom.\tbull\t")
            self.assertEqual(lines[1], "2\til\til(I)/\tỉl (I)\tDN m. sg. abs. nom.\tʾIlu/Ilu/El\t")
            self.assertEqual(len([line for line in lines if line.startswith("1\tṯr\t")]), 1)
            self.assertEqual(len([line for line in lines if line.startswith("2\til\t")]), 1)


class SpacyYdkContextDisambiguatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = SpacyYdkContextDisambiguator()

    def test_resolves_ydk_before_sgr(self) -> None:
        content = "\n".join(
            [
                "1\tydk\tyd(I)/+k\tyd (I)\tn. f.\thand\t",
                "1\tydk\tyd(II)/+k\tyd (II)\tn. m.\tlove\t",
                "2\tṣġr\tṣġr/\tṣġr\tadj.\tsmall\t",
                "",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.step.refine_file(path)

            self.assertEqual(result.rows_changed, 2)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[0], "1\tydk\tyd(II)/+k=\tyd (II)\tn. m. cstr. nom.\tlove\t")


if __name__ == "__main__":
    unittest.main()
