"""Tests for HTML lint report rendering."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from linter.lint import Issue, render_html


class LinterHtmlReportTest(unittest.TestCase):
    def test_top_problem_types_are_grouped_by_severity(self) -> None:
        issues = [
            Issue("error", "f.tsv", 1, "1", "s", "a", "Error only"),
            Issue("error", "f.tsv", 2, "2", "s", "a", "Error only"),
            Issue("warning", "f.tsv", 3, "3", "s", "a", "Warning only"),
            Issue("info", "f.tsv", 4, "4", "s", "a", "Info only"),
        ]

        with TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "report.html"
            render_html(issues, out_path)
            html_text = out_path.read_text(encoding="utf-8")

        self.assertIn("<h2>Top Problem Types</h2>", html_text)
        self.assertIn("<h3>ERROR</h3>", html_text)
        self.assertIn("<h3>WARNING</h3>", html_text)
        self.assertIn("<h3>INFO</h3>", html_text)

        self.assertIn("<tr><td>Error only</td><td>2</td></tr>", html_text)
        self.assertIn("<tr><td>Warning only</td><td>1</td></tr>", html_text)
        self.assertIn("<tr><td>Info only</td><td>1</td></tr>", html_text)

        error_start = html_text.index("<h3>ERROR</h3>")
        warning_start = html_text.index("<h3>WARNING</h3>")
        info_start = html_text.index("<h3>INFO</h3>")

        error_section = html_text[error_start:warning_start]
        warning_section = html_text[warning_start:info_start]
        details_start = html_text.index("<h2>Detailed Issues</h2>")
        info_section = html_text[info_start:details_start]

        self.assertIn("Error only", error_section)
        self.assertNotIn("Warning only", error_section)
        self.assertNotIn("Info only", error_section)

        self.assertIn("Warning only", warning_section)
        self.assertNotIn("Error only", warning_section)
        self.assertNotIn("Info only", warning_section)

        self.assertIn("Info only", info_section)
        self.assertNotIn("Error only", info_section)
        self.assertNotIn("Warning only", info_section)


if __name__ == "__main__":
    unittest.main()
