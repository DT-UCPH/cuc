import unittest

from lint_reports.parser import LintOutputParser


class LintOutputParserTest(unittest.TestCase):
    def test_parse_counts_and_normalization(self):
        text = "\n".join(
            [
                "ERROR out/KTU 1.5.tsv:13 139778 šlyṭ Unknown DULAT token in column 4: /l-y-ṭ/",
                "WARNING out/KTU 1.5.tsv:21 139785 krs TODO/uncertain marker in comment: merge",
                "INFO out/KTU 1.5.tsv:101 139999 x Surface x parsed inconsistently: a; b",
                "Total issues: 3",
            ]
        )
        parser = LintOutputParser()
        stats = parser.parse(lint_output=text, files_checked=1)

        self.assertEqual(stats.total_issues, 3)
        self.assertEqual(stats.by_severity["ERROR"], 1)
        self.assertEqual(stats.by_severity["WARNING"], 1)
        self.assertEqual(stats.by_severity["INFO"], 1)

        buckets = {
            (row.severity, row.problem_type): row.count for row in stats.by_problem_type
        }
        self.assertEqual(buckets[("ERROR", "Unknown DULAT token in column 4")], 1)
        self.assertEqual(buckets[("WARNING", "TODO/uncertain marker in comment")], 1)
        self.assertEqual(
            buckets[("INFO", "Surface parsed inconsistently across IDs")], 1
        )

    def test_fallback_counter_increases_for_unmatched_message(self):
        text = "ERROR out/KTU 1.5.tsv:1 1 x Some custom nonstandard message\nTotal issues: 1\n"
        stats = LintOutputParser().parse(lint_output=text, files_checked=1)
        self.assertEqual(stats.fallback_parsed, 1)


if __name__ == "__main__":
    unittest.main()
