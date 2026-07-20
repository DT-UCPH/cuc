from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reviewed_migration import ReviewedTabletMigrator


class ReviewedTabletMigratorTest(unittest.TestCase):
    def test_migrates_aligned_token_and_preserves_reviewed_pos_gloss(self) -> None:
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
                "136943\taliyn\taliyn/\tảlỉyn\tadj. m.\tThe Very / Most Powerful\treview note",
                output,
            )
            self.assertNotIn("\n1\taliyn\t", output)

    def test_uses_marked_auto_fallback_for_simple_concatenation(self) -> None:
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
                "137061\tbnx\t?\t?\t?\t?\tlegacy split | DULAT: NOT FOUND | "
                "Migrated from legacy reviewed tokenization.",
                output,
            )
            self.assertNotIn("\tbn(I)/\tbn (I)\t", output)

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

    def test_uses_marked_auto_fallback_for_simple_split(self) -> None:
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
                "137849\tw\t?\t?\t?\t?\tlegacy split source | DULAT: NOT FOUND | Migrated",
                output,
            )
            self.assertIn(
                "137850\ttˤn\t?\t?\t?\t?\tlegacy split source | DULAT: NOT FOUND | Migrated",
                output,
            )
            self.assertNotIn("\twtˤn/\twtˤn\t", output)
            self.assertEqual(output.count("legacy split source"), 2)

    def test_migrates_sign_span_schema_and_refreshes_split_token_spans(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            reviewed = root / "reviewed.tsv"
            raw = root / "raw.tsv"
            auto = root / "auto.tsv"
            reviewed.write_text(
                "id\tsurface form\tsign span\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.1 II:3\t\t\t\t\t\t\t\n"
                "125834\tḫršnr\t ḫršn       r\tḫršn&r/\tḫršn (I)\tn. m.\tmountain\treviewed\n",
                encoding="utf-8",
            )
            raw.write_text(
                "#---------------------------- KTU 1.1 II:3\n"
                "154257\tḫršn\tḫršn\tḫršn       \n"
                "154258\tr\tr\tr  \n",
                encoding="utf-8",
            )
            auto.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.1 II:3\t\t\t\t\t\t\n"
                "154257\tḫršn\tḫršn(I)/\tḫršn (I)\tn. m.\tmountain\t\n"
                "154258\tr\t?\t?\t?\t?\t\n",
                encoding="utf-8",
            )

            output = ReviewedTabletMigrator().migrate(reviewed, raw, auto)

            self.assertTrue(output.startswith("id\tsurface form\tsign span\t"))
            self.assertIn(
                "154257\tḫršn\tḫršn       \tḫršn(I)/\tḫršn (I)\tn. m.\tmountain\t"
                "reviewed | Migrated",
                output,
            )
            self.assertIn(
                "154258\tr\tr  \t&gr(I)/\tġr (I)\tn. m.\tmountain\t"
                "reviewed | Migrated",
                output,
            )

    def test_maps_positionally_reviewed_fields_across_split_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            reviewed = root / "reviewed.tsv"
            raw = root / "raw.tsv"
            auto = root / "auto.tsv"
            reviewed.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.2 III:3\t\t\t\t\t\t\n"
                "1\twḫss\tw ḫss/\tw; ḫss\tconj.; DN\tand; Khasis\treview note\n",
                encoding="utf-8",
            )
            raw.write_text(
                "#---------------------------- KTU 1.2 III:3\n"
                "10\tw\tw\n"
                "11\tḫss\tḫss\n",
                encoding="utf-8",
            )
            auto.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.2 III:3\t\t\t\t\t\t\n"
                "10\tw\tw\tw\tconj.\tand\t\n"
                "11\tḫss\tḫss/\tḫss\tDN\tKhasis\t\n",
                encoding="utf-8",
            )

            output = ReviewedTabletMigrator().migrate(reviewed, raw, auto)

            self.assertIn("10\tw\tw\tw\tconj.\tand\treview note | Migrated", output)
            self.assertIn(
                "11\tḫss\tḫss/\tḫss\tDN\tKhasis\treview note | Migrated",
                output,
            )

    def test_does_not_append_unreviewed_trailing_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            reviewed = root / "reviewed.tsv"
            raw = root / "raw.tsv"
            auto = root / "auto.tsv"
            reviewed.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.14 II:51\t\t\t\t\t\t\n"
                "1\tšd\tšd(I)/\tšd (I)\tn. m.\tfield\treviewed\n",
                encoding="utf-8",
            )
            raw.write_text(
                "#---------------------------- KTU 1.14 II:51\n10\tšd\tšd\n"
                "#---------------------------- KTU 1.14 III:1\n11\tkm\tkm\n",
                encoding="utf-8",
            )
            auto.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 1.14 II:51\t\t\t\t\t\t\n"
                "10\tšd\tšd(I)/\tšd (I)\tn. m.\tfield\t\n"
                "# KTU 1.14 III:1\t\t\t\t\t\t\n"
                "11\tkm\tkm\tkm\tadv.\tas\t\n",
                encoding="utf-8",
            )

            output = ReviewedTabletMigrator().migrate(reviewed, raw, auto)

            self.assertIn("10\tšd\t", output)
            self.assertNotIn("11\tkm\t", output)
            self.assertNotIn("KTU 1.14 III:1", output)

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

    def test_moves_inline_analysis_notes_to_comment_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            reviewed = root / "reviewed.tsv"
            raw = root / "raw.tsv"
            auto = root / "auto.tsv"
            reviewed.write_text(
                "1\tlak\t!!l(ʔ&ak[ # imperative reading\n",
                encoding="utf-8",
            )
            raw.write_text(
                "#---------------------------- KTU 2.10 10\n156573\tlak\tlak\n",
                encoding="utf-8",
            )
            auto.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 2.10 10\t\t\t\t\t\t\n"
                "156573\tlak\t!!l(ʔ&ak[\t/l-ʔ-k/\tvb\tto send\t\n",
                encoding="utf-8",
            )

            migrator = ReviewedTabletMigrator()
            output = migrator.migrate(reviewed, raw, auto)

            self.assertIn(
                "156573\tlak\t!!l(ʔ&ak[\t\t\t\timperative reading",
                output,
            )
            self.assertNotIn("!!l(ʔ&ak[ # imperative reading", output)

    def test_moves_inline_analysis_notes_without_space_after_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            reviewed = root / "reviewed.tsv"
            raw = root / "raw.tsv"
            auto = root / "auto.tsv"
            reviewed.write_text(
                "1\trgm\trgm/ #noun reading\n",
                encoding="utf-8",
            )
            raw.write_text(
                "#---------------------------- KTU 2.14 17\n156737\trgm\trgm\n",
                encoding="utf-8",
            )
            auto.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 2.14 17\t\t\t\t\t\t\n"
                "156737\trgm\trgm/\trgm\tn. m. sg.\tword\t\n",
                encoding="utf-8",
            )

            migrator = ReviewedTabletMigrator()
            output = migrator.migrate(reviewed, raw, auto)

            self.assertIn("156737\trgm\trgm/\t\t\t\tnoun reading", output)
            self.assertNotIn("rgm/ #noun reading", output)

    def test_normalizes_legacy_analysis_notation_during_migration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            reviewed = root / "reviewed.tsv"
            raw = root / "raw.tsv"
            auto = root / "auto.tsv"
            reviewed.write_text(
                "1\tl\tl\n2\tlk\tl+k\n3\taḫy\taḫ/(I)+y\n4\trgm\t!!rgm[\n",
                encoding="utf-8",
            )
            raw.write_text(
                "#---------------------------- KTU 2.38 1\n"
                "10\tl\tl\n"
                "11\tlk\tlk\n"
                "12\taḫy\taḫy\n"
                "13\trgm\trgm\n",
                encoding="utf-8",
            )
            auto.write_text(
                "id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments\n"
                "# KTU 2.38 1\t\t\t\t\t\t\n"
                "10\tl\tl(I)\tl (I)\tprep.\tto\t\n"
                "11\tlk\tl(I)+k\tl (I)\tprep.\tto\t\n"
                "12\taḫy\taḫ(I)/+y\tảḫ (I)\tn. m.\tbrother\t\n"
                "13\trgm\t!!rgm[/\t/r-g-m/\tvb G inf.\tto say\t\n",
                encoding="utf-8",
            )

            migrator = ReviewedTabletMigrator()
            output = migrator.migrate(reviewed, raw, auto)

            self.assertIn("10\tl\tl(I)\t", output)
            self.assertIn("11\tlk\tl(I)+k\t", output)
            self.assertIn("12\taḫy\taḫ(I)/+y\t", output)
            self.assertIn("13\trgm\t!!rgm[\t", output)


if __name__ == "__main__":
    unittest.main()
