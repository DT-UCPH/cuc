#!/usr/bin/env python3
"""Generate committed lint reports under reports/ using local databases."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from project_paths import get_project_paths  # noqa: E402


def main() -> int:
    from lint_reports.generator import LintReportGenerator

    paths = get_project_paths(REPO_ROOT)
    generator = LintReportGenerator(
        out_dir=paths.default_output_dir(),
        reports_dir=paths.default_reports_dir(),
        dulat_db=paths.default_dulat_db(),
        udb_db=paths.default_udb_db(),
        linter_path=REPO_ROOT / "linter" / "lint.py",
    )
    return generator.run()


if __name__ == "__main__":
    sys.exit(main())
