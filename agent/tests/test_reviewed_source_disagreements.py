import tempfile
import unittest
from pathlib import Path

from linter.lint import DulatEntry, lint_file


class ReviewedSourceDisagreementTest(unittest.TestCase):
    def lint_case(self, ref="KTU 1.5 I:26", analysis="nš(y[t=", reviewed=True):
        entry = DulatEntry(1, "/n-š-y/", "", "vb", "to be forgotten", "N, suffc.", "nšt")
        header = ["id", "surface form", "morphological parsing", "DULAT", "POS", "gloss", "comments"]
        row = ["1", "nšt", analysis, "/n-š-y/", "vb G suffc. 2 m. sg.", "to forget", ""]
        if reviewed:
            header.insert(2, "sign span")
            row.insert(2, "nšt")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "expert.tsv"
            path.write_text("\t".join(header)+"\n# "+ref+"\n"+"\t".join(row)+"\n", encoding="utf-8")
            return lint_file(
                path=path, dulat_forms={"nšt": [entry]},
                entry_meta={1: ("/n-š-y/", "", "vb", "to be forgotten")},
                lemma_map={"/n-š-y/": [entry]}, entry_stems={1: {"N"}},
                entry_gender={}, udb_words=None, baseline=None, input_format="auto", db_checks=True,
            )

    def test_exact_reviewed_dissent_is_informational_and_explained(self):
        hits = [i for i in self.lint_case() if i.message.startswith("Non-G stem")]
        self.assertTrue(hits)
        self.assertTrue(all(i.level == "info" and "EUPT" in i.message for i in hits))

    def test_other_reference_and_automatic_candidates_remain_errors(self):
        for kwargs in ({"ref": "KTU 1.5 I:25"}, {"reviewed": False}):
            with self.subTest(kwargs=kwargs):
                hits = [i for i in self.lint_case(**kwargs) if i.message.startswith("Non-G stem")]
                self.assertTrue(hits)
                self.assertTrue(all(i.level == "error" for i in hits))

    def test_changed_encoding_does_not_inherit_exception(self):
        hits = [i for i in self.lint_case(analysis="nšy[t=") if i.message.startswith("Non-G stem")]
        self.assertTrue(hits)
        self.assertTrue(all(i.level == "error" for i in hits))


if __name__ == "__main__":
    unittest.main()
