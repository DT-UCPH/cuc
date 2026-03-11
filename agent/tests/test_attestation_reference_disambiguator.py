"""Tests for reference-based ambiguity collapse using DULAT attestations."""

import tempfile
import unittest
from pathlib import Path

from pipeline.dulat_attestation_index import DulatAttestationIndex
from pipeline.steps.attestation_reference_disambiguator import (
    AttestationReferenceDisambiguator,
)


class AttestationReferenceDisambiguatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.index = DulatAttestationIndex(
            counts_by_key={},
            max_count_by_lemma={},
            refs_by_key={
                ("al", "I"): {"1.3 I:1", "1.3 V:20"},
                ("al", "II"): {"1.3 V:22"},
            },
        )
        self.fixer = AttestationReferenceDisambiguator(index=self.index)

    def test_collapses_group_when_single_variant_matches_section_ref(self) -> None:
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.3 I:1\t\t\t\t\t\t\n"
            "136937\tal\tal(I)\tảl (I)\tneg. functor\tno\t\n"
            "136937\tal\tal(II)\tảl (II)\tpos. functor\tsurely\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.3.tsv"
            path.write_text(content, encoding="utf-8")

            result = self.fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 1)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 3)
            self.assertEqual(lines[2], "136937\tal\tal(I)\tảl (I)\tneg. functor\tno\t")

    def test_keeps_group_when_multiple_variants_match_ref(self) -> None:
        index = DulatAttestationIndex(
            counts_by_key={},
            max_count_by_lemma={},
            refs_by_key={
                ("al", "I"): {"1.3 I:1"},
                ("al", "II"): {"1.3 I:1"},
            },
        )
        fixer = AttestationReferenceDisambiguator(index=index)
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.3 I:1\t\t\t\t\t\t\n"
            "136937\tal\tal(I)\tảl (I)\tneg. functor\tno\t\n"
            "136937\tal\tal(II)\tảl (II)\tpos. functor\tsurely\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.3.tsv"
            path.write_text(content, encoding="utf-8")

            result = fixer.refine_file(path)
            self.assertEqual(result.rows_changed, 0)

    def test_keeps_multiple_rows_for_single_matching_dulat_head(self) -> None:
        index = DulatAttestationIndex(
            counts_by_key={},
            max_count_by_lemma={},
            refs_by_key={
                ("ym", "I"): {"1.14 III:2"},
            },
        )
        fixer = AttestationReferenceDisambiguator(index=index)
        content = (
            "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
            "# KTU 1.14 III:2\t\t\t\t\t\t\n"
            "142023\tym\tym(I)/\tym (I)\tn. m. sg. cstr. nom.\tday\t\n"
            "142023\tym\tym(I)/\tym (I)\tn. m. sg. abs. nom.\tday\t\n"
            "142023\tym\tym(II)/\tym (II)\tn. m. sg. abs. nom.\tsea\t\n"
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.14.tsv"
            path.write_text(content, encoding="utf-8")

            result = fixer.refine_file(path)

            self.assertEqual(result.rows_changed, 1)
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 4)
            self.assertIn(
                "142023\tym\tym(I)/\tym (I)\tn. m. sg. cstr. nom.\tday\t",
                lines,
            )
            self.assertIn(
                "142023\tym\tym(I)/\tym (I)\tn. m. sg. abs. nom.\tday\t",
                lines,
            )
            self.assertNotIn(
                "142023\tym\tym(II)/\tym (II)\tn. m. sg. abs. nom.\tsea\t",
                lines,
            )


if __name__ == "__main__":
    unittest.main()
