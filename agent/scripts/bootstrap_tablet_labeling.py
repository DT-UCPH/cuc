#!/usr/bin/env python3
"""
Bootstrap structured morphology TSV from raw cuc_tablets_tsv rows.

This is a deterministic first pass:
- preserves separator rows and col1/col2,
- fills col3-col6 from DULAT form matches where possible,
- keeps unresolved tokens explicit.
"""

import argparse
import html
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from pipeline.config.dulat_entry_forms_fallback import extract_forms_from_entry_text
from pipeline.config.dulat_form_text_overrides import expand_dulat_form_texts

LOOKUP_NORMALIZE = str.maketrans(
    {
        "ʿ": "ʕ",
        "ˤ": "ʕ",
        "ả": "a",
        "ỉ": "i",
        "ủ": "u",
    }
)

ANALYSIS_ORTHO = str.maketrans(
    {
        "ʿ": "ˤ",
        "ʕ": "ˤ",
    }
)

POS_LABEL_NORMALIZATION = {
    "det. / rel. functor": "det. or rel. functor",
    "subordinating / completive functor": "Subordinating or completive functor",
    "emph./det. encl. morph.": "emph. or det. encl. morph.",
    "adv./emph. functor": "adv. or emph. functor",
    "adv./prep.": "adv. or prep.",
    "adj./n.": "adj. or n.",
    "adj. /n.": "adj. or n.",
    "n./adj. (?)": "n. or adj. (?)",
    "pn/dn": "PN or DN",
    "pn/gn": "PN or GN",
    "pn/tn (?)": "PN or TN (?)",
    "dn/tn": "DN or TN",
    "gn/tn": "GN or TN",
    "tn/toponymic element": "TN or toponymic element",
}


def normalize_lookup(s: str) -> str:
    return (s or "").translate(LOOKUP_NORMALIZE).strip()


def normalize_pos_label(pos: str) -> str:
    tok = re.sub(r"\s+", " ", (pos or "").strip())
    if not tok:
        return ""
    return POS_LABEL_NORMALIZATION.get(tok.lower(), tok)


def strip_html(text: str) -> str:
    t = html.unescape(text or "")
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


@dataclass
class Entry:
    entry_id: int
    lemma: str
    hom: str
    pos: str
    gloss: str
    families: frozenset[str]


def _citation_family(citation: str) -> str:
    m = re.search(r"\bCAT\s+(\d+)\.", citation or "")
    if m:
        return m.group(1)
    m = re.search(r"\bKTU\s+(\d+)\.", citation or "")
    if m:
        return m.group(1)
    return ""


def load_dulat_forms(db_path: Path) -> Dict[str, List[Entry]]:
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    cur.execute("SELECT entry_id, text FROM translations ORDER BY entry_id, rowid")
    gloss_map: Dict[int, str] = {}
    for entry_id, text_val in cur.fetchall():
        if entry_id not in gloss_map and text_val:
            gloss_map[entry_id] = strip_html(text_val)

    cur.execute("PRAGMA table_info(entries)")
    entry_columns = {row[1] for row in cur.fetchall()}
    has_text = "text" in entry_columns

    if has_text:
        cur.execute("SELECT entry_id, lemma, homonym, pos, text FROM entries")
    else:
        cur.execute("SELECT entry_id, lemma, homonym, pos FROM entries")
    meta: Dict[int, Tuple[str, str, str]] = {}
    entry_text_by_id: Dict[int, str] = {}
    for row in cur.fetchall():
        entry_id, lemma, hom, pos = row[:4]
        if has_text and len(row) >= 5 and row[4]:
            entry_text_by_id[int(entry_id)] = row[4]
        lemma = (lemma or "").strip()
        hom = (hom or "").strip()
        if lemma and not hom:
            m = re.match(r"^(.*)\s+\(([IV]+)\)$", lemma)
            if m:
                lemma = m.group(1).strip()
                hom = m.group(2)
        meta[entry_id] = (lemma, hom, pos or "")

    entry_families: Dict[int, set[str]] = {}
    cur.execute("SELECT entry_id, citation FROM attestations")
    for entry_id, citation in cur.fetchall():
        fam = _citation_family(citation or "")
        if fam:
            entry_families.setdefault(entry_id, set()).add(fam)

    entries_by_id: Dict[int, Entry] = {}
    for entry_id, (lemma, hom, pos) in meta.items():
        entries_by_id[entry_id] = Entry(
            entry_id=entry_id,
            lemma=lemma,
            hom=hom,
            pos=pos,
            gloss=gloss_map.get(entry_id, ""),
            families=frozenset(entry_families.get(entry_id, set())),
        )

    forms_map: Dict[str, List[Entry]] = {}
    seen_form_entry: set[Tuple[str, int]] = set()
    cur.execute("SELECT text, entry_id FROM forms")
    for form_text, entry_id in cur.fetchall():
        entry = entries_by_id.get(entry_id)
        if not form_text or entry is None:
            continue
        for form_variant in expand_dulat_form_texts(
            lemma=entry.lemma,
            homonym=entry.hom,
            form_text=form_text,
        ):
            key = normalize_lookup(form_variant)
            marker = (key, entry.entry_id)
            if marker in seen_form_entry:
                continue
            seen_form_entry.add(marker)
            forms_map.setdefault(key, []).append(entry)

    for entry_id, entry_text in entry_text_by_id.items():
        entry = entries_by_id.get(entry_id)
        if entry is None:
            continue
        for fallback_form in extract_forms_from_entry_text(entry_text):
            for form_variant in expand_dulat_form_texts(
                lemma=entry.lemma,
                homonym=entry.hom,
                form_text=fallback_form,
            ):
                key = normalize_lookup(form_variant)
                marker = (key, entry.entry_id)
                if marker in seen_form_entry:
                    continue
                seen_form_entry.add(marker)
                forms_map.setdefault(key, []).append(entry)

    explicit_form_keys = set(forms_map.keys())

    # Conservative fallback: if DULAT has an entry lemma but no `forms` row for
    # that same token, index the lemma itself so bootstrap can still propose
    # candidates (for example tnn). When KTU 1 attestations are present among
    # homonyms, prefer that family to avoid importing KTU 4-only readings.
    fallback_by_key: Dict[str, List[Entry]] = {}
    for entry in entries_by_id.values():
        lemma_key = normalize_lookup(entry.lemma)
        if not lemma_key or " " in lemma_key:
            continue
        if lemma_key in explicit_form_keys:
            continue
        fallback_by_key.setdefault(lemma_key, []).append(entry)

    for lemma_key, candidates in fallback_by_key.items():
        ktu1_candidates = [entry for entry in candidates if "1" in entry.families]
        selected = ktu1_candidates if ktu1_candidates else candidates
        forms_map.setdefault(lemma_key, []).extend(selected)

    conn.close()
    return forms_map


def dedupe_entries(entries: List[Entry]) -> List[Entry]:
    seen = set()
    out = []
    for e in entries:
        if e.entry_id in seen:
            continue
        seen.add(e.entry_id)
        out.append(e)
    return out


def is_verb_pos(pos: str) -> bool:
    return "vb" in (pos or "").lower()


def is_nominal_pos(pos: str) -> bool:
    p = (pos or "").lower()
    return any(k in p for k in ("n.", "adj", "dn", "pn", "tn", "gn", "mn", "num"))


def analysis_for(surface: str, entry: Entry) -> str:
    base = (surface or "").translate(ANALYSIS_ORTHO)
    hom = f"({entry.hom})" if entry.hom else ""
    if is_verb_pos(entry.pos):
        return f"{base}{hom}["
    if is_nominal_pos(entry.pos):
        return f"{base}{hom}/"
    return f"{base}{hom}".strip()


def lemma_for(entry: Entry) -> str:
    if entry.hom:
        return f"{entry.lemma} ({entry.hom})"
    return entry.lemma


def score_candidate(surface: str, entry: Entry) -> int:
    s = normalize_lookup(surface)
    lemma_plain = re.sub(r"[^A-Za-zʕḫṣṯẓġḏḥṭš]", "", normalize_lookup(entry.lemma))
    score = 0
    if lemma_plain == s:
        score += 5
    if is_verb_pos(entry.pos) and s and s[0] in {"y", "t", "a", "n", "i", "u"}:
        score += 2
    if entry.gloss:
        score += 1
    if "→" in (entry.pos or ""):
        score -= 2
    return score


def build_row(line_id: str, surface: str, entries: List[Entry], max_variants: int = 3) -> str:
    if not surface.strip():
        return "\t".join([line_id, surface, "", "", "", "", ""])

    if re.fullmatch(r"[xX]+", surface):
        return "\t".join([line_id, surface, surface, "", "", "", ""])

    if not entries:
        return "\t".join(
            [line_id, surface, surface.translate(ANALYSIS_ORTHO), "", "", "", "DULAT: NOT FOUND"]
        )

    entries = dedupe_entries(entries)
    entries.sort(key=lambda e: (-score_candidate(surface, e), e.lemma, e.hom, e.pos))
    shown = entries[:max_variants]

    analyses = [analysis_for(surface, e) for e in shown]
    lemmas = [lemma_for(e) for e in shown]
    poses = [normalize_pos_label(e.pos) for e in shown]
    glosses = [strip_html(e.gloss) for e in shown]

    comment = ""
    if len(entries) > max_variants:
        comment = f"ambiguous DULAT candidates: {len(entries)} (showing top {max_variants})"

    return "\t".join(
        [
            line_id,
            surface,
            ";".join(analyses),
            ";".join(lemmas),
            ";".join(poses),
            ";".join(glosses),
            comment,
        ]
    )


def process_file(in_path: Path, out_path: Path, forms_map: Dict[str, List[Entry]]) -> None:
    out_lines: List[str] = []
    for raw in in_path.read_text(encoding="utf-8").splitlines():
        if raw.startswith("#"):
            out_lines.append(raw)
            continue
        if not raw.strip():
            out_lines.append(raw)
            continue

        parts = raw.split("\t")
        if len(parts) < 2:
            out_lines.append(raw)
            continue
        line_id = (parts[0] or "").strip()
        surface = parts[1] or ""
        key = normalize_lookup(surface)
        entries = forms_map.get(key, [])
        out_lines.append(build_row(line_id, surface, entries))

    out_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bootstrap KTU tablet to structured morphology TSV."
    )
    parser.add_argument("input", nargs="+", help="Input raw cuc_tablets_tsv files")
    parser.add_argument(
        "--dulat-db",
        default="sources/dulat_cache.sqlite",
        help="Path to dulat cache sqlite",
    )
    parser.add_argument("--out-dir", default="results", help="Output directory")
    args = parser.parse_args()

    forms_map = load_dulat_forms(Path(args.dulat_db))
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for f in args.input:
        inp = Path(f)
        out = out_dir / inp.name
        process_file(inp, out, forms_map)
        print(f"Wrote {out}")


if __name__ == "__main__":
    main()
