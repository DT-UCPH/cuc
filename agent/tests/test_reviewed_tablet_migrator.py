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

    def test_preserves_reviewed_rows_for_simple_concatenation(self) -> None:
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

            self.assertIn(
                "137061\tbnx\tbn/\tbn (I)\tn. m.\tson\tlegacy split",
                output,
            )
            self.assertIn("137061\tbnx\t?\t?\t?\t?\tlegacy split", output)
            self.assertNotIn("Migrated from legacy reviewed tokenization.", output)

    def test_preserves_reviewed_rows_for_editorial_surface_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            reviewed = root / "reviewed.tsv"
            raw = root / "raw.tsv"
            auto = root / "auto.tsv"
            reviewed.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.3 I:25\t\t\t\t\t\t\n"
                "1\tpdr<y>\tpdry/\tpdry\tDN\tPidray\tlegacy\n",
                encoding="utf-8",
            )
            raw.write_text(
                "#---------------------------- KTU 1.3 I:25\n137025\tpdry\tpdry\n",
                encoding="utf-8",
            )
            auto.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.3 I:25\t\t\t\t\t\t\n"
                "137025\tpdry\tpdr(I)/+y\tpdr (I)\tn. m.\ttown\t\n",
                encoding="utf-8",
            )

            migrator = ReviewedTabletMigrator()
            output = migrator.migrate(reviewed, raw, auto)

            self.assertIn(
                "137025\tpdry\tpdry/\tpdry\tDN\tPidray\t"
                "legacy | Token changed from previous version.",
                output,
            )
            self.assertNotIn("\tpdr(I)/+y\tpdr (I)\tn. m.\ttown\t", output)

    def test_preserves_reviewed_rows_for_simple_split(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            reviewed = root / "reviewed.tsv"
            raw = root / "raw.tsv"
            auto = root / "auto.tsv"
            reviewed.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.3 V:19\t\t\t\t\t\t\n"
                "1\tw  tˤn\twtˤn/\twtˤn\tn. m.\tmock\tlegacy split source\n",
                encoding="utf-8",
            )
            raw.write_text(
                "#---------------------------- KTU 1.3 V:19\n137849\tw\tw\n137850\ttˤn\ttˤn\n",
                encoding="utf-8",
            )
            auto.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.3 V:19\t\t\t\t\t\t\n"
                "137849\tw\t?\t?\t?\t?\tDULAT: NOT FOUND\n"
                "137850\ttˤn\t?\t?\t?\t?\tDULAT: NOT FOUND\n",
                encoding="utf-8",
            )

            migrator = ReviewedTabletMigrator()
            output = migrator.migrate(reviewed, raw, auto)

            self.assertIn(
                "137849\tw\twtˤn/\twtˤn\tn. m.\tmock\tlegacy split source",
                output,
            )
            self.assertIn(
                "137850\ttˤn\twtˤn/\twtˤn\tn. m.\tmock\tlegacy split source",
                output,
            )
            self.assertNotIn("Migrated from legacy reviewed tokenization.", output)

    def test_uses_auto_rows_for_non_editorial_surface_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            reviewed = root / "reviewed.tsv"
            raw = root / "raw.tsv"
            auto = root / "auto.tsv"
            reviewed.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.3 V:31\t\t\t\t\t\t\n"
                "1\thkm\thkm/\thkm\tn. m.\twise one\tlegacy\n",
                encoding="utf-8",
            )
            raw.write_text(
                "#---------------------------- KTU 1.3 V:30\n137913\tḥkm\tḥkm\n",
                encoding="utf-8",
            )
            auto.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.3 V:30\t\t\t\t\t\t\n"
                "137913\tḥkm\tḥkm/\tḥkm\tn. m.\twise person\t\n",
                encoding="utf-8",
            )

            migrator = ReviewedTabletMigrator()
            output = migrator.migrate(reviewed, raw, auto)

            self.assertIn(
                "137913\tḥkm\tḥkm/\tḥkm\tn. m.\twise person\t"
                "Migrated from legacy reviewed tokenization.",
                output,
            )
            self.assertNotIn("\thkm/\thkm\tn. m.\twise one\tlegacy", output)


if __name__ == "__main__":
    unittest.main()
