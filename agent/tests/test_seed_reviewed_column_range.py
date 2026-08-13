import subprocess
import sys
import unittest
from pathlib import Path


class SeedReviewedColumnRangeTests(unittest.TestCase):
    def test_columnless_tablet_can_be_seeded_in_dry_run(self):
        agent_dir = Path(__file__).resolve().parents[1]
        reviewed = agent_dir.parent / "reviewed" / "KTU 2.10.tsv"
        before = reviewed.read_text(encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable,
                "scripts/seed_reviewed_column_range.py",
                "2.10",
                "-",
                "--dry-run",
            ],
            cwd=agent_dir,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("KTU 2.10 from column -:", result.stdout)
        self.assertIn("(dry run — nothing written)", result.stdout)
        self.assertEqual(before, reviewed.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
