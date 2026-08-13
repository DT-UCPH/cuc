#!/usr/bin/env python3
"""Audit what '(' and '&' are actually encoding in the analysis column.

The two marks carry at least five unrelated phenomena at once:

  morphological  a lexeme letter with no counterpart in the written form
                 (assimilated nun, elided radical, unwritten vowel)
  orthographic   the aleph sign standing for a vowel -- systematic, predictable,
                 and by far the commonest use
  text-critical  a letter an editor erased, supplied or corrected -- which the
                 sign-span column already brackets and Text-Fabric already
                 stores in `emen`, `alt` and `cert`
  lexicographic  the lexicon spelling a root differently from the texts
                 (DULAT /m-ṣ-ḥ/ against attested mṣḫ)
  layout         a word split across a physical line, which TF stores in `cont`

Morphological, orthographic, and lexicographic alignment belong in the analysis;
sign-level editorial deletions do not. This reports which is which, by
aligning every surface letter the analysis produces against the same letter in
the sign span, so an editorial claim can be checked against the editorial
markup instead of guessed at.

    audit_marker_layers.py                 # every reviewed/*.tsv
    audit_marker_layers.py 1.6 1.14        # named tablets
    audit_marker_layers.py --class dup     # list one class in full

Classes: ortho, dup, unsupported, lexical, other. See ../SKILL.md.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sources  # noqa: E402

ROOT = sources.ROOT

# Kept in step with linter.lint.ANALYSIS_SURFACE_LETTER_RE, copied rather than
# imported so this runs under the system interpreter; the linter needs 3.13.
ANALYSIS_SURFACE_LETTER_RE = re.compile(r"[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]")

HEADER_RE = re.compile(r"^# KTU (\S+)(?: ([IVX]+):| )(\d+)")
HOM_RE = re.compile(r"\(([IV]+)\)")
# The aleph signs: the script writes the consonant and its vowel together, so a
# lexical ʔ realised as a/i/u is orthography, not an editorial or lexical event.
ALEPH = set("ʔaiuảỉủ")

# Sign-span brackets, longest first so '[[' is not read as two '['.
SPAN_OPEN = [("[[", "erased"), ("[", "restored"), ("{", "excised"), ("<", "supplied")]
SPAN_CLOSE = {"erased": "]]", "restored": "]", "excised": "}", "supplied": ">"}


def span_letters(span: str):
    """[(letter, frozenset(bracket types enclosing it))] for the physical signs."""
    out, stack, i = [], [], 0
    while i < len(span):
        for token, kind in SPAN_OPEN:
            if span.startswith(token, i):
                stack.append(kind)
                i += len(token)
                break
        else:
            closed = False
            for kind in list(stack)[::-1]:
                token = SPAN_CLOSE[kind]
                if span.startswith(token, i):
                    stack.remove(kind)
                    i += len(token)
                    closed = True
                    break
            if closed:
                continue
            ch = span[i]
            if not ch.isspace() and ch not in "]}>":
                out.append((ch, frozenset(stack)))
            i += 1
    return out


def analysis_letters(analysis: str):
    """[(letter, provenance)] for every surface letter the analysis produces.

    Mirrors reconstruct_surface_from_analysis exactly; provenance is 'plain',
    'amp' for a bare '&Y', or 'sub:X' for a '(X&Y' substitution.
    """
    a = (analysis or "").strip()
    out, i, n = [], 0, len(a)
    while i < n:
        if a.startswith("(]n]", i):
            i += 4
            continue
        hom = HOM_RE.match(a[i:])
        if hom:
            i += len(hom.group(0))
            continue
        ch = a[i]
        if a.startswith(":pass", i):
            i += len(":pass")
            continue
        if any(a.startswith(":" + s, i) for s in "dlrwn"):
            i += 2
            continue
        if ch == ":":
            i += 1
            continue
        if ch == "(":
            if i + 1 < n and ANALYSIS_SURFACE_LETTER_RE.match(a[i + 1]):
                if i + 3 < n and a[i + 2] == "&" and ANALYSIS_SURFACE_LETTER_RE.match(a[i + 3]):
                    out.append((a[i + 3], "sub:" + a[i + 1]))
                    i += 4
                    continue
                i += 2
                continue
            i += 1
            continue
        if ch == "&":
            if i + 1 < n and ANALYSIS_SURFACE_LETTER_RE.match(a[i + 1]):
                out.append((a[i + 1], "amp"))
                i += 2
                continue
            i += 1
            continue
        if ch in {"!", "]", "[", "/", "=", "+", "~", ",", ")"}:
            i += 1
            continue
        if ANALYSIS_SURFACE_LETTER_RE.match(ch):
            out.append((ch, "plain"))
        i += 1
    return out


def classify(letter, provenance, brackets):
    """Which layer does this mark belong to?

    The bracket types do not mean the same thing for a '&' claim, which asserts
    that a letter is written but not lexical:

      [[ ]] erased, { } excised  the editor has removed this letter from the
                                 reading -- '&' wrongly restores it
      < >   supplied             the scribe never wrote it, so calling it a
                                 written letter contradicts the sign data
      [ ]   restored             damaged but part of the intended text, so
                                 treating it as written is legitimate
    """
    lexical = provenance.split(":", 1)[1] if provenance.startswith("sub:") else None
    if lexical in ALEPH or (provenance == "amp" and letter in ALEPH):
        return "ortho"
    if "supplied" in brackets:
        return "conflict"
    if brackets & {"erased", "excised"}:
        return "dup"
    if lexical:
        return "lexical"      # a written radical the lexeme does not have
    return "unsupported"      # surface-only letter, no editorial marking behind it


def audit(path: Path):
    rows, counts = [], Counter()
    with path.open(encoding="utf-8") as fh:
        reader = csv.reader(fh, delimiter="\t")
        header = next(reader, None)
        if not (header and "sign span" in header):
            return rows, counts
        ref = ""
        for row in reader:
            if not row:
                continue
            marker = HEADER_RE.match(row[0])
            if marker:
                ref = "%s:%s" % (marker.group(2) or "-", marker.group(3))
                continue
            if not row[0].strip().isdigit() or len(row) < 4:
                continue
            analysis, span = row[3].strip(), row[2]
            if "&" not in analysis:
                continue
            comment_all = row[7] if len(row) > 7 else ""
            # A MERGE row carries the whole word's analysis on each half, so its
            # sign span covers only part of it and cannot align by position.
            merged = "MERGE WITH" in comment_all.upper()
            marks = analysis_letters(analysis)
            signs = span_letters(span)
            aligned = (not merged) and len(marks) == len(signs)
            for idx, (letter, provenance) in enumerate(marks):
                if provenance == "plain":
                    continue
                brackets = signs[idx][1] if aligned and signs[idx][0] == letter else frozenset()
                kind = "merge" if merged else classify(letter, provenance, brackets)
                counts[kind] += 1
                rows.append(dict(
                    file=path.name, ref=ref, tid=row[0], surface=row[1],
                    analysis=analysis, span=span.strip(), letter=letter,
                    provenance=provenance, brackets=",".join(sorted(brackets)) or "-",
                    kind=kind, aligned=aligned,
                    comment=comment_all.split("##")[0].strip(),
                ))
    return rows, counts


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tablets", nargs="*")
    ap.add_argument("--class", dest="klass",
                    choices=["ortho", "dup", "unsupported", "lexical",
                             "conflict", "merge"],
                    help="list every occurrence of one class")
    ap.add_argument("--limit", type=int, default=25)
    args = ap.parse_args()

    reviewed = ROOT / "reviewed"
    paths = ([reviewed / ("KTU %s.tsv" % t) for t in args.tablets]
             if args.tablets else sorted(reviewed.glob("*.tsv")))

    all_rows, totals, per_file = [], Counter(), defaultdict(Counter)
    for p in paths:
        if not p.exists():
            raise SystemExit("no such reviewed file: %s" % p)
        rows, counts = audit(p)
        all_rows += rows
        totals += counts
        per_file[p.name] = counts

    print("'&' marks by layer\n")
    print("  %-14s %7s %7s %7s %7s %8s %6s"
          % ("", "ortho", "dup", "unsupp", "lexical", "conflict", "merge"))
    for name, c in per_file.items():
        if sum(c.values()):
            print("  %-14s %7d %7d %7d %7d %8d %6d"
                  % (name.replace(".tsv", ""), c["ortho"], c["dup"],
                     c["unsupported"], c["lexical"], c["conflict"], c["merge"]))
    print("  %-14s %7d %7d %7d %7d %8d %6d"
          % ("TOTAL", totals["ortho"], totals["dup"], totals["unsupported"],
             totals["lexical"], totals["conflict"], totals["merge"]))
    unaligned = sum(1 for r in all_rows if not r["aligned"])
    if unaligned:
        print("\n  %d mark(s) on rows whose analysis and sign span do not align "
              "letter-for-letter; those are reported as if unbracketed." % unaligned)

    print("""
  ortho     the aleph sign carrying a vowel -- orthography, belongs here
  dup       the sign span removes this letter from the edited reading;
            the analysis wrongly restores it with `&`
  unsupp    a surface-only letter with no editorial marking behind it
  lexical   a written radical the lexeme does not have (DULAT vs the texts)
  conflict  the analysis calls a letter written that the sign span says the
            scribe never wrote (supplied by an editor, < >)
  merge     a MERGE WITH row, whose span covers only part of the word by
            design and so cannot be checked positionally""")

    if args.klass:
        picked = [r for r in all_rows if r["kind"] == args.klass]
        print("\n%s: %d occurrence(s)\n" % (args.klass, len(picked)))
        for r in picked[: args.limit]:
            print("  %-9s %-8s %-10s %-22s span=%-22s %s"
                  % (r["file"].replace("KTU ", "").replace(".tsv", ""), r["ref"],
                     r["surface"], r["analysis"], r["span"],
                     ("[" + r["brackets"] + "] " if r["brackets"] != "-" else "")
                     + r["comment"][:44]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
