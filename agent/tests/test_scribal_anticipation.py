"""Scribal-anticipation annotation for line-final word fragments.

Regression source: KTU 1.6 V:17-18 (b š | b šdm) and VI:10-11 (s | spuy) -
the scribe broke a word off at the line end and rewrote it in full at the
start of the next line. The orphan fragment is not a lexeme and must not be
merged with its neighbour; it should carry an explanatory comment instead of
'DULAT: NOT FOUND'.
"""

import tempfile
import unittest
from pathlib import Path

from pipeline.steps.scribal_anticipation import (
    ScribalAnticipationAnnotator,
    is_anticipation_fragment,
)


class IsAnticipationFragmentTest(unittest.TestCase):
    def test_fragment_prefix_of_full_form(self) -> None:
        self.assertTrue(is_anticipation_fragment("s", "spuy"))
        self.assertTrue(is_anticipation_fragment("š", "šdm"))

    def test_equal_or_longer_fragment_is_rejected(self) -> None:
        self.assertFalse(is_anticipation_fragment("spuy", "spuy"))
        self.assertFalse(is_anticipation_fragment("spuy", "s"))

    def test_non_prefix_is_rejected(self) -> None:
        # tṣ | ḥ is a genuine split word (tṣḥ), not an anticipation.
        self.assertFalse(is_anticipation_fragment("tṣ", "ḥ"))

    def test_long_fragment_is_rejected(self) -> None:
        self.assertFalse(is_anticipation_fragment("spuy", "spuym", max_fragment_len=3))


class ScribalAnticipationAnnotatorTest(unittest.TestCase):
    HEADER = "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"

    def _run(self, body: str) -> str:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "KTU 1.test.tsv"
            path.write_text(self.HEADER + body, encoding="utf-8")
            step = ScribalAnticipationAnnotator()
            step.refine_file(path)
            return path.read_text(encoding="utf-8")

    def test_direct_fragment_is_annotated(self) -> None:
        body = (
            "# KTU 1.6 VI:10\t\t\t\t\t\t\n"
            "1\tbˤl\tbˤl(II)/\tbʕl (II)\tDN\tBaal\t\n"
            "2\ts\t?\t?\t?\t?\tDULAT: NOT FOUND\n"
            "# KTU 1.6 VI:11\t\t\t\t\t\t\n"
            "3\tspuy\t!!sp(ʔ&u[/+y\t/s-p-ʔ/\tvb G inf.\tfood\t\n"
        )
        result = self._run(body)
        self.assertIn("scribal anticipation", result)
        self.assertIn("Incomplete spuy", result)
        self.assertNotIn("DULAT: NOT FOUND", result)

    def test_context_repeat_fragment_is_annotated(self) -> None:
        body = (
            "# KTU 1.6 V:17\t\t\t\t\t\t\n"
            "1\tb\tb\tb\tprep.\tin\t\n"
            "2\tš\t?\t?\t?\t?\tDULAT: NOT FOUND\n"
            "# KTU 1.6 V:18\t\t\t\t\t\t\n"
            "3\tb\tb\tb\tprep.\tin\t\n"
            "4\tšdm\tšd(I)/m\tšd (I)\tn. m. pl.\topen field\t\n"
        )
        result = self._run(body)
        self.assertIn("scribal anticipation", result)
        self.assertIn("Incomplete šdm", result)

    def test_genuine_split_word_is_untouched(self) -> None:
        body = (
            "# KTU 1.6 II:11\t\t\t\t\t\t\n"
            "1\ttṣ\t?\t?\t?\t?\tDULAT: NOT FOUND\n"
            "# KTU 1.6 II:12\t\t\t\t\t\t\n"
            "2\tḥ\t?\t?\t?\t?\tDULAT: NOT FOUND\n"
        )
        result = self._run(body)
        self.assertNotIn("scribal anticipation", result)

    def test_resolved_fragment_is_untouched(self) -> None:
        body = (
            "# KTU 1.6 VI:10\t\t\t\t\t\t\n"
            "1\ts\ts/\ts\tn.\tsomething\t\n"
            "# KTU 1.6 VI:11\t\t\t\t\t\t\n"
            "2\tspuy\t!!sp(ʔ&u[/+y\t/s-p-ʔ/\tvb G inf.\tfood\t\n"
        )
        result = self._run(body)
        self.assertNotIn("scribal anticipation", result)

    def test_same_line_fragment_is_untouched(self) -> None:
        body = (
            "# KTU 1.6 VI:10\t\t\t\t\t\t\n"
            "1\ts\t?\t?\t?\t?\tDULAT: NOT FOUND\n"
            "2\tspuy\t!!sp(ʔ&u[/+y\t/s-p-ʔ/\tvb G inf.\tfood\t\n"
        )
        result = self._run(body)
        self.assertNotIn("scribal anticipation", result)


if __name__ == "__main__":
    unittest.main()
