#!/usr/bin/env python3
"""Build a regeneratable JSON index of DULAT attestation counts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    from pipeline.dulat_attestation_index import DulatAttestationIndex

    parser = argparse.ArgumentParser(
        description="Build JSON index mapping DULAT entries to attestation counts."
    )
    parser.add_argument(
        "--dulat-db",
        default="sources/dulat_cache.sqlite",
        help="Path to DULAT sqlite cache",
    )
    parser.add_argument(
        "--out",
        default="reports/dulat_attestation_index.json",
        help="Output JSON path",
    )
    args = parser.parse_args()

    index = DulatAttestationIndex.from_sqlite(Path(args.dulat_db))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "dulat_db": str(Path(args.dulat_db)),
        "entry_count": len(index.counts_by_key),
        "entries": [
            {
                "lemma": lemma,
                "homonym": homonym,
                "attestation_count": count,
            }
            for (lemma, homonym), count in sorted(
                index.counts_by_key.items(),
                key=lambda item: (-item[1], item[0][0], item[0][1]),
            )
        ],
    }
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {payload['entry_count']} indexed entries to {out_path}")


if __name__ == "__main__":
    main()
