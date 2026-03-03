from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reviewed_migration import ReviewedTabletMigrator


class ReviewedTabletMigratorTest(unittest.TestCase):
    def test_migrates_aligned_token_and_refreshes_pos_gloss_from_auto(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            reviewed = root / "reviewed.tsv"
            raw = root / "raw.tsv"
            auto = root / "auto.tsv"
            reviewed.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.3 I:1\t\t\t\t\t\t\n"
                "1\taliyn\taliyn/\tảlỉyn\tadj. m.\tThe Very / Most Powerful\treview note\n",
                encoding="utf-8",
            )
            raw.write_text(
                "#---------------------------- KTU 1.3 I:1\n136943\taliyn\taliyn\n",
                encoding="utf-8",
            )
            auto.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.3 I:1\t\t\t\t\t\t\n"
                "136943\taliyn\taliyn/\tảlỉyn\tadj. m. sg.\tThe Very / Most Powerful\t\n",
                encoding="utf-8",
            )

            migrator = ReviewedTabletMigrator()
            output = migrator.migrate(reviewed, raw, auto)

            self.assertIn(
                "136943\taliyn\taliyn/\tảlỉyn\tadj. m. sg.\tThe Very / Most Powerful\treview note",
                output,
            )
            self.assertNotIn("\n1\taliyn\t", output)

    def test_uses_auto_rows_for_tokenization_mismatch_segment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            reviewed = root / "reviewed.tsv"
            raw = root / "raw.tsv"
            auto = root / "auto.tsv"
            reviewed.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.3 II:6\t\t\t\t\t\t\n"
                "10\tbn\tbn/\tbn (I)\tn. m.\tson\tlegacy split\n"
                "# KTU 1.3 II:7\t\t\t\t\t\t\n"
                "11\tx\t?\t?\t?\t?\tlegacy split\n",
                encoding="utf-8",
            )
            raw.write_text(
                "#---------------------------- KTU 1.3 II:6\n137061\tbnx\tbnx\n",
                encoding="utf-8",
            )
            auto.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.3 II:6\t\t\t\t\t\t\n"
                "137061\tbnx\t?\t?\t?\t?\tDULAT: NOT FOUND\n",
                encoding="utf-8",
            )

            migrator = ReviewedTabletMigrator()
            output = migrator.migrate(reviewed, raw, auto)

            expected = (
                "137061\tbnx\t?\t?\t?\t?\t"
                "DULAT: NOT FOUND | Migrated from legacy reviewed tokenization."
            )
            self.assertIn(expected, output)
            self.assertNotIn("\n10\tbn\t", output)
            self.assertNotIn("\n11\tx\t", output)

    def test_uses_auto_rows_when_surface_changed_under_same_alignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            reviewed = root / "reviewed.tsv"
            raw = root / "raw.tsv"
            auto = root / "auto.tsv"
            reviewed.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.3 I:26\t\t\t\t\t\t\n"
                "1\txht\txht\t?\t?\t?\tlegacy\n",
                encoding="utf-8",
            )
            raw.write_text(
                "#---------------------------- KTU 1.3 I:26\n137028\txxht\txxht\n",
                encoding="utf-8",
            )
            auto.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.3 I:26\t\t\t\t\t\t\n"
                "137028\txxht\t?\t?\t?\t?\tDULAT: NOT FOUND\n",
                encoding="utf-8",
            )

            migrator = ReviewedTabletMigrator()
            output = migrator.migrate(reviewed, raw, auto)

            expected = (
                "137028\txxht\t?\t?\t?\t?\t"
                "DULAT: NOT FOUND | Migrated from legacy reviewed tokenization."
            )
            self.assertIn(expected, output)
            self.assertNotIn("\txht\txht\t?\t?\t?\tlegacy", output)


if __name__ == "__main__":
    unittest.main()
