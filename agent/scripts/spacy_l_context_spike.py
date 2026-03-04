"""Debug runner for the spaCy-based `l`-context resolver spike."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from spacy_ugaritic.doc_builder import build_doc_from_path
    from spacy_ugaritic.language import create_ugaritic_nlp

    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    nlp = create_ugaritic_nlp()
    doc = build_doc_from_path(nlp, args.path)
    doc = nlp(doc)

    for token in doc:
        before = tuple((c.analysis, c.dulat, c.pos, c.gloss) for c in token._.candidates)
        after = tuple((c.analysis, c.dulat, c.pos, c.gloss) for c in token._.resolved_candidates)
        if before == after:
            continue
        print(f"{token._.line_id}\t{token.text}\t{token._.section_ref}")
        print(f"  before={before}")
        print(f"  after={after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
