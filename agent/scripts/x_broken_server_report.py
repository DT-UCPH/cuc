#!/usr/bin/env python3
import argparse
import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple


MATCH_RE = re.compile(r'<li>\s*<a href="/concordance/\?word=[^"]+">([^<]+)</a>', re.S)


def fetch_text(url: str, timeout: int = 15) -> str:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")


def fetch_json(url: str, timeout: int = 15) -> Dict:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", "ignore"))


def pattern_from_surface(surface: str) -> str:
    if re.search(r"x{2,}", surface, flags=re.I):
        return re.sub(r"x{2,}", "—", surface, flags=re.I)
    return re.sub(r"x", "-", surface, flags=re.I)


def extract_matches(concordance_html: str) -> List[str]:
    words = MATCH_RE.findall(concordance_html)
    seen = set()
    out = []
    for w in words:
        if w in seen:
            continue
        seen.add(w)
        out.append(html.unescape(w))
    return out


def format_entry(entry: Dict) -> str:
    lemma = (entry.get("lemma") or "").strip()
    hom = (entry.get("homonym") or "").strip()
    pos = (entry.get("pos") or "").strip()
    gloss = (entry.get("summary") or "").strip()
    hom_tag = f" ({hom})" if hom else ""
    bits = [f"{lemma}{hom_tag}"]
    if pos:
        bits.append(f"[{pos}]")
    if gloss:
        bits.append(f"— {gloss}")
    return " ".join(bits)


def lookup_entries(host: str, word: str) -> List[Dict]:
    aliases = [word]
    # Normalize ayin variants used across sources (ʿ/ʕ/ˤ) for resilient API lookup.
    for src, dst in (("ʿ", "ʕ"), ("ˤ", "ʕ"), ("ʕ", "ʿ")):
        alt = word.replace(src, dst)
        if alt not in aliases:
            aliases.append(alt)

    seen = set()
    out: List[Dict] = []
    for q in aliases:
        url = f"{host}/api/entries/?{urllib.parse.urlencode({'q': q})}"
        data = fetch_json(url)
        for row in data.get("results") or []:
            rid = row.get("id")
            key = rid if rid is not None else (row.get("lemma"), row.get("homonym"), row.get("pos"))
            if key in seen:
                continue
            seen.add(key)
            out.append(row)
    return out


def collect_x_rows(tsv_path: Path) -> List[Tuple[str, str]]:
    rows = []
    for raw in tsv_path.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split("\t")
        if len(parts) < 2:
            continue
        line_id = parts[0].strip()
        surface = parts[1].strip()
        if not surface:
            continue
        if "x" not in surface.lower():
            continue
        if re.fullmatch(r"x+", surface.lower()):
            continue
        rows.append((line_id, surface))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Build server-backed report for x-containing broken tokens.")
    parser.add_argument("tsv", help="TSV file to inspect")
    parser.add_argument("--host", default="http://127.0.0.1:8000", help="Server base URL")
    parser.add_argument("--out", default="results/x_broken_server_report.tsv", help="Output TSV path")
    parser.add_argument("--max-matches", type=int, default=10, help="How many matched words to keep in preview")
    parser.add_argument("--max-entries", type=int, default=5, help="How many DULAT entries to keep per matched word")
    args = parser.parse_args()

    tsv_path = Path(args.tsv)
    out_path = Path(args.out)
    rows = collect_x_rows(tsv_path)

    out_lines = [
        "\t".join(
            [
                "id",
                "surface",
                "pattern",
                "match_count",
                "matches_preview",
                "entries_preview",
                "note",
            ]
        )
    ]

    for line_id, surface in rows:
        pattern = pattern_from_surface(surface)
        c_url = f"{args.host}/concordance/?{urllib.parse.urlencode({'word': pattern})}"
        try:
            conc_html = fetch_text(c_url)
            matches = extract_matches(conc_html)
        except Exception as exc:
            out_lines.append("\t".join([line_id, surface, pattern, "ERR", "", "", f"concordance lookup failed: {exc}"]))
            continue

        match_preview = ", ".join(matches[: args.max_matches])
        entries_preview_parts = []
        for match_word in matches[: min(len(matches), args.max_matches)]:
            try:
                entries = lookup_entries(args.host, match_word)
            except Exception as exc:
                entries_preview_parts.append(f"{match_word}: <lookup error: {exc}>")
                continue
            # Keep only entries that look like direct candidates for this surface word.
            shortlist = []
            for ent in entries:
                lemma = (ent.get("lemma") or "").strip()
                if not lemma:
                    continue
                if lemma == match_word or lemma.startswith("/") or match_word in lemma:
                    shortlist.append(ent)
            if not shortlist:
                shortlist = entries[: args.max_entries]
            entry_preview = "; ".join(format_entry(e) for e in shortlist[: args.max_entries])
            entries_preview_parts.append(f"{match_word}: {entry_preview}")

        note = ""
        if len(matches) == 1:
            note = "single concordance match"
        elif len(matches) == 0:
            note = "no concordance matches"
        else:
            note = "multiple concordance matches"

        out_lines.append(
            "\t".join(
                [
                    line_id,
                    surface,
                    pattern,
                    str(len(matches)),
                    match_preview,
                    " | ".join(entries_preview_parts),
                    note,
                ]
            )
        )

    out_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_path} ({len(rows)} token rows)")


if __name__ == "__main__":
    main()
