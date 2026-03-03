"""Tests for token_ref_index discovery helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.token_ref_index import discover_files


class TokenRefIndexTest(unittest.TestCase):
    def test_discover_files_supports_absolute_glob(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            first = root / "KTU 1.1.tsv"
            second = root / "KTU 1.2.tsv"
            first.write_text("", encoding="utf-8")
            second.write_text("", encoding="utf-8")

            files = discover_files([], str(root / "KTU 1.*.tsv"))

            self.assertEqual(files, [first, second])


if __name__ == "__main__":
    unittest.main()
