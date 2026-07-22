import unittest

from lint_reports.regression import find_new_issues, parse_lint_issues


class LintRegressionTest(unittest.TestCase):
    def test_ignores_token_and_row_renumbering(self):
        baseline = parse_lint_issues(
            "ERROR /tmp/head/auto_parsing/0.2.8/KTU 1.1.tsv:17 125834 r "
            "Unknown DULAT token in column 4: /ġr/"
        )
        candidate = parse_lint_issues(
            "ERROR /tmp/stage/auto_parsing/0.2.8/KTU 1.1.tsv:29 154258 r "
            "Unknown DULAT token in column 4: /ġr/"
        )

        self.assertEqual(find_new_issues(baseline, candidate), [])

    def test_ignores_mutable_references_inside_messages(self):
        baseline = parse_lint_issues(
            "ERROR /tmp/head/KTU.tsv:803 172717 tn Duplicate feature bundle; first seen on line 802"
        )
        candidate = parse_lint_issues(
            "ERROR /tmp/stage/KTU.tsv:811 192999 tn Duplicate feature bundle; "
            "first seen on line 810"
        )

        self.assertEqual(find_new_issues(baseline, candidate), [])

    def test_reports_changed_diagnostic(self):
        baseline = parse_lint_issues(
            "ERROR /tmp/head/KTU.tsv:17 125834 r Unknown DULAT token in column 4: /ġr/"
        )
        candidate = parse_lint_issues(
            "ERROR /tmp/stage/KTU.tsv:29 154258 r Unknown DULAT token in column 4: /r(II)/"
        )

        new_issues = find_new_issues(baseline, candidate)
        self.assertEqual(len(new_issues), 1)
        self.assertIn("/r(II)/", new_issues[0].rendered)

    def test_reports_an_extra_duplicate_occurrence(self):
        line = "ERROR parse.tsv:17 125834 r Unknown DULAT token in column 4: /ġr/"
        baseline = parse_lint_issues(line)
        candidate = parse_lint_issues("\n".join([line, line]))

        self.assertEqual(len(find_new_issues(baseline, candidate)), 1)

    def test_does_not_cancel_same_error_between_different_files(self):
        baseline = parse_lint_issues("ERROR auto_parsing/0.2.6/KTU 1.1.tsv:17 125834 r Broken")
        candidate = parse_lint_issues("ERROR auto_parsing/0.2.7/KTU 1.1.tsv:17 125834 r Broken")

        self.assertEqual(len(find_new_issues(baseline, candidate)), 1)

    def test_parses_file_names_with_spaces_and_global_issues(self):
        issues = parse_lint_issues("ERROR /tmp/KTU 1.1.tsv:0   A file-level diagnostic")

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].line_id, "")
        self.assertEqual(issues[0].surface, "")
        self.assertEqual(issues[0].message, "A file-level diagnostic")


if __name__ == "__main__":
    unittest.main()
