#!/usr/bin/env python3
"""
Run a conservative morphology refinement pass using extracted Notarius evidence.

This script does not rewrite parsing columns by default. It links token rows in
results/*.txt and results/*.tsv to KTU line refs via cuc_tablets_tsv and reports
where Notarius claim entries suggest additional morphology attention.
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


SEPARATOR_RE = re.compile(
    r"^#-+\s*KTU\s+(\d+\.\d+)\s+([IVX]+):(\d+)\s*$",
    flags=re.IGNORECASE,
)


def normalize_ref(ref: str) -> str:
    ref = ref.strip()
    ref = ref.replace("–", "-")
    ref = re.sub(r"\s+", " ", ref)
    return ref


def normalize_token(token: str) -> str:
    token = token.strip().lower()
    token = token.replace("ʿ", "ˤ")
    token = token.replace("ʕ", "ˤ")
    token = token.replace("’", "'")
    token = token.replace("'", "")
    token = token.replace("-", "")
    token = token.replace("x", "")
    return token


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("–", "-")).strip()


def iter_result_files(patterns: Sequence[str]) -> Iterable[Path]:
    seen = set()
    for pat in patterns:
        for fp in glob.glob(pat):
            p = Path(fp)
            if p in seen or not p.is_file():
                continue
            seen.add(p)
            yield p


def map_ids_to_refs(cuc_dir: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for tsv in sorted(cuc_dir.glob("KTU *.tsv")):
        current_ref = ""
        for raw in tsv.read_text(encoding="utf-8").splitlines():
            line = raw.rstrip("\n")
            m = SEPARATOR_RE.match(line)
            if m:
                current_ref = f"{m.group(1)} {m.group(2).upper()} {m.group(3)}"
                continue
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split("\t")
            if not parts:
                continue
            line_id = parts[0].strip()
            if line_id and current_ref:
                out[line_id] = current_ref
    return out


@dataclass
class Evidence:
    eid: int
    refs: List[str]
    forms_norm: List[str]
    tags: List[str]
    claim_strength: str
    snippet: str
    text: str


def load_evidence(
    evidence_path: Path, min_claim_strength: str
) -> Dict[str, List[Evidence]]:
    rank = {"none": 0, "weak": 1, "moderate": 2, "strong": 3}
    threshold = rank.get(min_claim_strength, 2)
    data = json.loads(evidence_path.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    by_ref: Dict[str, List[Evidence]] = {}
    for entry in entries:
        cs = entry.get("claim_strength", "none")
        if rank.get(cs, 0) < threshold:
            continue
        refs = [normalize_ref(r) for r in entry.get("refs", []) if r]
        if not refs:
            continue
        forms = entry.get("forms", []) or []
        forms_norm = [normalize_token(f) for f in forms if normalize_token(f)]
        snippet_list = entry.get("parse_claim_snippets") or entry.get("snippets") or []
        snippet = clean_text(snippet_list[0]) if snippet_list else ""
        ev = Evidence(
            eid=int(entry.get("id", 0)),
            refs=refs,
            forms_norm=forms_norm,
            tags=entry.get("tags", []) or [],
            claim_strength=cs,
            snippet=snippet,
            text=clean_text(entry.get("text", "")),
        )
        for ref in refs:
            by_ref.setdefault(ref, []).append(ev)
    return by_ref


def row_matches_evidence(surface: str, ev: Evidence) -> bool:
    s_norm = normalize_token(surface)
    if not s_norm:
        return False
    if ev.forms_norm:
        return s_norm in ev.forms_norm
    # Fallback when no explicit forms were extracted.
    return re.search(rf"\b{re.escape(s_norm)}\b", normalize_token(ev.text)) is not None


def infer_claim_hints(ev: Evidence) -> set:
    hints = set(ev.tags)
    s = (ev.snippet or ev.text).lower()
    if "→ n" in s or "-> n" in s or " n-stem" in s:
        hints.add("n_stem")
    if "→ gt" in s or "-> gt" in s:
        hints.add("gt_stem")
    if "→ št" in s or "-> št" in s or "→ st" in s or "-> st" in s:
        hints.add("st_stem")
    if "→ š " in s or "-> š " in s:
        hints.add("s_stem")
    if "gpass" in s or "g passive" in s:
        hints.add("g_passive")
    if "passive participle" in s:
        hints.add("passive_participle")
    if "infinitive" in s:
        hints.add("infinitive")
    return hints


def detect_suggestions(analysis: str, ev: Evidence) -> List[str]:
    suggestions: List[str] = []
    tags = infer_claim_hints(ev)
    has_verb = "[" in analysis
    has_inf = "[/" in analysis
    has_pass = ":pass" in analysis
    has_nstem = (
        bool(re.search(r"![^!]+!n", analysis))
        or "!n!" in analysis
        or analysis.startswith("n")
    )
    has_t_infix = "]t]" in analysis
    has_s_infix = "]š]" in analysis

    if "infinitive" in tags and has_verb and not has_inf:
        suggestions.append("consider infinitive marker ([/)")
    if "g_passive" in tags and not has_pass:
        suggestions.append("consider passive marker (:pass) or OR variant")
    if "n_stem" in tags and not has_nstem:
        suggestions.append("consider N-stem OR variant (!n!)")
    if "gt_stem" in tags and not has_t_infix:
        suggestions.append("consider Gt marker ]t] or OR variant")
    if "st_stem" in tags and not (has_s_infix and has_t_infix):
        suggestions.append("consider St/Št markers ]š]]t] or OR variant")
    if "s_stem" in tags and not has_s_infix:
        suggestions.append("consider Š marker ]š] or OR variant")
    if "debated" in tags:
        suggestions.append(
            "text-critical/debated in Notarius; keep OR in comment if needed"
        )
    return suggestions


@dataclass
class Hit:
    file: str
    line_no: int
    line_id: str
    ref: str
    surface: str
    analysis: str
    evidence_id: int
    claim_strength: str
    tags: str
    suggestions: str
    snippet: str


def collect_hits(
    result_files: Sequence[Path],
    id_to_ref: Dict[str, str],
    evidence_by_ref: Dict[str, List[Evidence]],
) -> List[Hit]:
    hits: List[Hit] = []
    for path in result_files:
        for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            main, *_comment = line.split("#", 1)
            parts = main.split("\t")
            if len(parts) < 3:
                continue
            line_id = parts[0].strip()
            surface = parts[1].strip()
            analysis = parts[2].strip()
            if not line_id or not surface:
                continue
            ref = id_to_ref.get(line_id, "")
            if not ref:
                continue
            evs = evidence_by_ref.get(ref, [])
            if not evs:
                continue
            for ev in evs:
                if not row_matches_evidence(surface, ev):
                    continue
                suggestions = detect_suggestions(analysis, ev)
                hits.append(
                    Hit(
                        file=str(path),
                        line_no=i,
                        line_id=line_id,
                        ref=ref,
                        surface=surface,
                        analysis=analysis,
                        evidence_id=ev.eid,
                        claim_strength=ev.claim_strength,
                        tags=",".join(ev.tags),
                        suggestions=" | ".join(suggestions),
                        snippet=ev.snippet,
                    )
                )
    return hits


def write_report(hits: Sequence[Hit], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(
            [
                "file",
                "line_no",
                "id",
                "ref",
                "surface",
                "analysis",
                "evidence_id",
                "claim_strength",
                "tags",
                "suggestions",
                "snippet",
            ]
        )
        for h in hits:
            w.writerow(
                [
                    h.file,
                    h.line_no,
                    h.line_id,
                    h.ref,
                    h.surface,
                    h.analysis,
                    h.evidence_id,
                    h.claim_strength,
                    h.tags,
                    h.suggestions,
                    h.snippet,
                ]
            )


def print_summary(hits: Sequence[Hit]) -> None:
    by_file: Dict[str, int] = {}
    actionable = 0
    by_suggestion: Dict[str, int] = {}
    by_strength: Dict[str, int] = {}
    for h in hits:
        by_file[h.file] = by_file.get(h.file, 0) + 1
        by_strength[h.claim_strength] = by_strength.get(h.claim_strength, 0) + 1
        if h.suggestions:
            actionable += 1
            for part in [p.strip() for p in h.suggestions.split("|")]:
                if not part:
                    continue
                by_suggestion[part] = by_suggestion.get(part, 0) + 1

    unique_rows = {(h.file, h.line_id) for h in hits}
    print(f"Matched evidence hits: {len(hits)}")
    print(f"Unique token rows matched: {len(unique_rows)}")
    print(f"Actionable suggestion hits: {actionable}")
    print(
        "By claim strength:",
        ", ".join(f"{k}={v}" for k, v in sorted(by_strength.items())),
    )
    print("By file:")
    for f, n in sorted(by_file.items()):
        print(f"  - {f}: {n}")
    if by_suggestion:
        print("Suggestion breakdown:")
        for s, n in sorted(by_suggestion.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  - {s}: {n}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Notarius-based refinement pass on results files."
    )
    parser.add_argument(
        "--evidence",
        default="data/notarius_evidence_claims.json",
        help="Evidence JSON file (claims split is recommended).",
    )
    parser.add_argument(
        "--results",
        nargs="+",
        default=["results/*.tsv", "results/*.txt"],
        help="Glob patterns for result files.",
    )
    parser.add_argument(
        "--cuc-dir",
        default="cuc_tablets_tsv",
        help="Directory with raw CUC tablet TSV files used for id->ref mapping.",
    )
    parser.add_argument(
        "--min-claim-strength",
        choices=["weak", "moderate", "strong"],
        default="moderate",
        help="Minimum Notarius claim strength to include.",
    )
    parser.add_argument(
        "--report",
        default="results/notarius_refinement_report.tsv",
        help="Output report TSV path.",
    )
    args = parser.parse_args()

    result_files = sorted(iter_result_files(args.results), key=lambda p: str(p))
    if not result_files:
        raise SystemExit("No result files matched.")

    id_to_ref = map_ids_to_refs(Path(args.cuc_dir))
    evidence_by_ref = load_evidence(
        Path(args.evidence), min_claim_strength=args.min_claim_strength
    )
    hits = collect_hits(
        result_files, id_to_ref=id_to_ref, evidence_by_ref=evidence_by_ref
    )
    write_report(hits, Path(args.report))
    print_summary(hits)
    print(f"Report written: {args.report}")


if __name__ == "__main__":
    main()
