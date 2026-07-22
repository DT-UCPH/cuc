#!/usr/bin/env python3
"""Audit G(-stem) passive-participle encodings in labeled Ugaritic TSV files.

Two deterministic findings, both grounded in Notarius, *The Ugaritic passive
participle*, §2.2 (`agent/local_sources/notarius.compact.html`):

* ``no-orthographic-diagnostic`` — a firm ``pass. ptcpl.`` on a *strong*
  triradical root. Alphabetic writing does not mark the qatūl/qatīl pattern on
  strong roots (§2.2.1), so such a parse rests entirely on syntax/semantics and
  must not be asserted from the bare skeleton alone. This is the class the
  automatic parser over-generates (e.g. ``rgm`` "word").
* ``iii-aleph-case-mismatch`` — a III-ʔ realized case-ending aleph whose vowel
  (u=nom, i=gen, a=acc) contradicts the labelled case (§2.2.2 criterion 4).

Neither finding decides a reading on its own; both mark rows a reviewer must
confirm against the clause, parallels, and DULAT.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

# Firm passive participle: `pass. ptcpl.` in any stem, and not an active
# participle. The `(?!\?)` guard is defensive; there is no `pass. ptcpl.?`
# convention (form-level uncertainty is not marked).
FIRM_PASS_PTCPL_RE = re.compile(r"\bpass\.\s*ptcpl\.(?!\?)", re.IGNORECASE)

# Realized case-ending aleph right after the nominal/participial boundary.
CASE_ALEPH_RE = re.compile(r"\[?/&([uia])(?=$|[+~=(;#\s])")
CASE_OF_ALEPH = {"u": "nom.", "i": "gen.", "a": "acc."}

# Root radicals from a DULAT root field such as `/n-š-ʔ/` or `/b-l-y/ (I)`.
ROOT_RE = re.compile(r"/([^/]+?)/")

WEAK = {"ʔ", "w", "y"}


def iter_tsv_paths(values: list[str]) -> list[Path]:
    paths: list[Path] = []
    for value in values:
        path = Path(value)
        if path.is_dir():
            paths.extend(sorted(path.glob("*.tsv")))
        elif path.suffix == ".tsv":
            paths.append(path)
    return paths


def split_variants(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(";")]


def variant(values: list[str], index: int) -> str:
    if index < len(values):
        return values[index]
    if len(values) == 1:
        return values[0]
    return ""


def root_radicals(dulat: str) -> list[str] | None:
    match = ROOT_RE.search(dulat or "")
    if not match:
        return None
    radicals = [r for r in match.group(1).split("-") if r]
    return radicals or None


def is_strong_triradical(radicals: list[str]) -> bool:
    if len(radicals) != 3:
        return False
    if any(r in WEAK for r in radicals):
        return False
    if radicals[1] == radicals[2]:  # geminate
        return False
    return True


def stated_cases(pos: str) -> set[str]:
    return {c + "." for c in re.findall(r"\b(nom|gen|acc)\.", pos or "")}


def audit_file(path: Path, *, selected_ids: set[str]) -> list[str]:
    issues: list[str] = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"id", "surface form", "morphological parsing", "DULAT", "POS"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            return [f"{path}: unsupported TSV header"]
        for line_no, row in enumerate(reader, 2):
            line_id = (row.get("id") or "").strip()
            if not line_id or line_id.startswith("#"):
                continue
            if selected_ids and line_id not in selected_ids:
                continue
            surface = (row.get("surface form") or "").strip()
            analyses = split_variants(row.get("morphological parsing") or "")
            pos_values = split_variants(row.get("POS") or "")
            dulat_values = split_variants(row.get("DULAT") or "")
            for index, analysis in enumerate(analyses):
                pos = variant(pos_values, index)
                if not FIRM_PASS_PTCPL_RE.search(pos):
                    continue
                dulat = variant(dulat_values, index)
                prefix = f"{path}:{line_no} {line_id} {surface}"

                # III-ʔ realized case-aleph vs labelled case.
                m = CASE_ALEPH_RE.search(analysis)
                if m:
                    expected = CASE_OF_ALEPH[m.group(1)]
                    cases = stated_cases(pos)
                    if cases and expected not in cases:
                        issues.append(
                            f"{prefix}\tiii-aleph-case-mismatch\t"
                            f"aleph={expected} label={','.join(sorted(cases))}\t{analysis}"
                        )

                # Strong-root passive participle with no orthographic diagnostic.
                radicals = root_radicals(dulat)
                if radicals and is_strong_triradical(radicals):
                    issues.append(
                        f"{prefix}\tno-orthographic-diagnostic\t{analysis}"
                    )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="TSV files or directories containing TSVs")
    parser.add_argument("--id", action="append", default=[], help="limit the audit to one token ID")
    args = parser.parse_args()

    paths = iter_tsv_paths(args.paths)
    if not paths:
        parser.error("no TSV files found")
    selected_ids = set(args.id)
    issues = [
        issue for path in paths for issue in audit_file(path, selected_ids=selected_ids)
    ]
    for issue in issues:
        print(issue)
    print(f"Audited {len(paths)} file(s); found {len(issues)} issue(s).")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
