#!/usr/bin/env python3
"""Discover frequent two-token formulas from parsed tablet TSV files."""

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TokenPayload:
    analysis: str
    dulat: str
    pos: str
    gloss: str


@dataclass(frozen=True)
class BigramRecord:
    first_surface: str
    second_surface: str
    first_payload: TokenPayload
    second_payload: TokenPayload


def _iter_rows(path: Path) -> list[tuple[str, TokenPayload]]:
    out: list[tuple[str, TokenPayload]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if not parts or not parts[0].isdigit():
            continue
        surface = (parts[1] if len(parts) > 1 else "").strip()
        analysis = (parts[2] if len(parts) > 2 else "").strip()
        dulat = (parts[3] if len(parts) > 3 else "").strip()
        pos = (parts[4] if len(parts) > 4 else "").strip()
        gloss = (parts[5] if len(parts) > 5 else "").strip()
        if not surface or analysis == "?":
            continue
        out.append((surface, TokenPayload(analysis, dulat, pos, gloss)))
    return out


def discover_bigrams(
    out_dir: Path,
    file_glob: str = "KTU 1.*.tsv",
) -> tuple[Counter[tuple[str, str]], dict[tuple[str, str], Counter[BigramRecord]]]:
    count_by_surface_bigram: Counter[tuple[str, str]] = Counter()
    payload_by_surface_bigram: dict[tuple[str, str], Counter[BigramRecord]] = defaultdict(Counter)

    for path in sorted(out_dir.glob(file_glob)):
        rows = _iter_rows(path)
        for idx in range(len(rows) - 1):
            first, second = rows[idx], rows[idx + 1]
            key = (first[0], second[0])
            count_by_surface_bigram[key] += 1
            payload_by_surface_bigram[key][
                BigramRecord(
                    first_surface=first[0],
                    second_surface=second[0],
                    first_payload=first[1],
                    second_payload=second[1],
                )
            ] += 1
    return count_by_surface_bigram, payload_by_surface_bigram


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover frequent two-token formulas.")
    parser.add_argument("--out-dir", default="out", help="Parsed tablet directory")
    parser.add_argument("--file-glob", default="KTU 1.*.tsv", help="Tablet filename glob")
    parser.add_argument("--top", type=int, default=40, help="Top N bigrams to print")
    parser.add_argument(
        "--min-count",
        type=int,
        default=10,
        help="Only print bigrams with count >= min-count",
    )
    args = parser.parse_args()

    counts, payloads = discover_bigrams(
        out_dir=Path(args.out_dir),
        file_glob=args.file_glob,
    )

    printed = 0
    for (first_surface, second_surface), count in counts.most_common():
        if count < args.min_count:
            continue
        variants = payloads[(first_surface, second_surface)]
        top_record, top_count = variants.most_common(1)[0]
        top_share = float(top_count) / float(count)
        print(
            f"{first_surface} {second_surface}\tcount={count}\t"
            f"payload_variants={len(variants)}\ttop_share={top_share:.3f}"
        )
        print(
            "  first:",
            top_record.first_payload.analysis,
            "|",
            top_record.first_payload.dulat,
            "|",
            top_record.first_payload.pos,
            "|",
            top_record.first_payload.gloss,
        )
        print(
            "  second:",
            top_record.second_payload.analysis,
            "|",
            top_record.second_payload.dulat,
            "|",
            top_record.second_payload.pos,
            "|",
            top_record.second_payload.gloss,
        )
        printed += 1
        if printed >= args.top:
            break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
