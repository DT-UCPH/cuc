"""Tests for two encoding-consistency checks.

* A passive-stem POS (Gpass/Dpass/Lpass/Špass) must carry the `:pass` marker.
* The deverbal `[/` boundary is valid only on a verbal POS; nouns close with
  `/` on their own noun lemma.
"""

import tempfile
import unittest
from pathlib import Path

from linter.lint import (
    analysis_missing_pass_marker,
    deverbal_marker_on_nonverbal_pos,
    lint_file,
)


class PassMarkerHelperTest(unittest.TestCase):
    def test_gpass_without_pass_marker_flags(self) -> None:
        self.assertTrue(analysis_missing_pass_marker("ḫbṯ[/", "vb Gpass ptcpl. m. sg."))

    def test_gpass_with_pass_marker_ok(self) -> None:
        self.assertFalse(analysis_missing_pass_marker("prš[&a:pass", "vb Gpass suffc."))

    def test_dpass_without_marker_flags(self) -> None:
        self.assertTrue(analysis_missing_pass_marker("bšr[", "vb Dpass prefc. 2 m. sg."))

    def test_passive_participle_voice_is_not_a_passive_stem(self) -> None:
        # `G pass. ptcpl.` is a G-stem participle, not the Gpass stem; no :pass.
        self.assertFalse(analysis_missing_pass_marker("rtq[/", "vb G pass. ptcpl. m. sg."))

    def test_active_stem_is_ignored(self) -> None:
        self.assertFalse(analysis_missing_pass_marker("qtl[", "vb G suffc. 3 m. sg."))


class DeverbalMarkerHelperTest(unittest.TestCase):
    def test_deverbal_on_noun_flags(self) -> None:
        self.assertTrue(deverbal_marker_on_nonverbal_pos("s(ʔ&id[/", "n. m. sg. cstr. nom."))

    def test_deverbal_on_adjective_flags(self) -> None:
        self.assertTrue(deverbal_marker_on_nonverbal_pos("kny[/t=", "adj. f. pl. abs. nom."))

    def test_deverbal_on_participle_ok(self) -> None:
        self.assertFalse(deverbal_marker_on_nonverbal_pos("rtq[/", "vb G pass. ptcpl. m. sg."))

    def test_deverbal_on_infinitive_ok(self) -> None:
        self.assertFalse(deverbal_marker_on_nonverbal_pos("!!nš(ʔ[/&i", "vb G inf. cstr. gen."))

    def test_verbal_noun_pos_ok(self) -> None:
        # `vb. n.` (Infinitive / Verbal noun) counts as verbal.
        self.assertFalse(deverbal_marker_on_nonverbal_pos("!!qtl[/", "vb. n. G"))

    def test_plain_noun_close_ok(self) -> None:
        self.assertFalse(deverbal_marker_on_nonverbal_pos("mr(u(I)/&i", "n. m. sg. abs. gen."))


class LintFileIntegrationTest(unittest.TestCase):
    def _lint(self, row: str):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "auto_parsing" / "0.2.8"
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / "KTU 1.test.tsv"
            path.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                + row
                + "\n",
                encoding="utf-8",
            )
            return lint_file(
                path=path,
                dulat_forms={},
                entry_meta={},
                lemma_map={},
                entry_stems={},
                entry_gender={},
                udb_words=None,
                baseline=None,
                input_format="auto",
                db_checks=False,
            )

    def test_gpass_missing_marker_is_error(self) -> None:
        issues = self._lint("1\tḫbṯ\tḫbṯ[/\t/ḫ-b-ṯ/\tvb Gpass ptcpl. m. sg. abs. nom.\tflee\t")
        msgs = [i for i in issues if i.message.startswith("Passive-stem POS requires")]
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].level, "error")

    def test_deverbal_on_noun_is_error(self) -> None:
        issues = self._lint("1\tsid\ts(ʔ&id[/\tsỉd\tn. m. sg. cstr. nom.\tbutler\t")
        msgs = [i for i in issues if i.message.startswith("Deverbal `[/`")]
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].level, "error")


if __name__ == "__main__":
    unittest.main()
