#!/usr/bin/env python3
"""Generate committed lint reports under reports/ using local databases."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    from lint_reports.generator import LintReportGenerator

    repo_root = REPO_ROOT
    generator = LintReportGenerator(
        out_dir=repo_root / "out",
        reports_dir=repo_root / "reports",
        dulat_db=repo_root / "sources" / "dulat_cache.sqlite",
        udb_db=repo_root / "sources" / "udb_cache.sqlite",
        linter_path=repo_root / "linter" / "lint.py",
    )
    return generator.run()


if __name__ == "__main__":
    sys.exit(main())
