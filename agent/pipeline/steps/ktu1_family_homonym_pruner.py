"""Prune non-KTU1 homonym variants in KTU 1.* rows when KTU1 homonyms exist."""

import re
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Mapping, Set, Tuple

from pipeline.steps.base import (
    RefinementStep,
    StepResult,
    TabletRow,
    is_separator_line,
    is_unresolved,
    parse_tsv_line,
)

_HOMONYM_LABEL_RE = re.compile(r"^(?P<lemma>.+)\s+\((?P<hom>[IVX]+)\)$")


def _split_variants(value: str) -> List[str]:
    return [v.strip() for v in (value or "").split(";") if v.strip()]


def _citation_family(citation: str) -> str:
    m = re.search(r"\bCAT\s+(\d+)\.", citation or "")
    if m:
        return m.group(1)
    m = re.search(r"\bKTU\s+(\d+)\.", citation or "")
    if m:
        return m.group(1)
    return ""


def _aligned_variants(
    analysis: str,
    dulat: str,
    pos: str,
    gloss: str,
) -> List[Tuple[str, str, str, str]]:
    cols = [
        _split_variants(analysis),
        _split_variants(dulat),
        _split_variants(pos),
        _split_variants(gloss),
    ]
    counts = [len(col) for col in cols]
    if any(count == 0 for count in counts):
        return []
    if len(set(counts)) != 1:
        return []
    return list(zip(cols[0], cols[1], cols[2], cols[3]))


def _head_label(dulat_variant: str) -> str:
    return (dulat_variant or "").split(",", 1)[0].strip()


class Ktu1FamilyHomonymPruner(RefinementStep):
    """Drop homonym options only attested outside CAT/KTU 1 from KTU 1.* rows.

    Rule:
    - For aligned multi-variant rows in `KTU 1.*`,
    - within each homonym lemma group (for example `bt (I)/(II)/(III)`),
    - if at least one variant is attested in CAT/KTU family 1,
      remove variants attested only in other families.
    """

    def __init__(
        self,
        dulat_db: Path | None = None,
        label_families: Mapping[str, Set[str]] | None = None,
    ) -> None:
        if label_families is not None:
            self._families_by_label = {k: set(v) for k, v in label_families.items()}
        else:
            db = dulat_db or (Path("sources") / "dulat_cache.sqlite")
            self._families_by_label = self._load_label_families(db)

    @property
    def name(self) -> str:
        return "ktu1-homonym-prune"

    def refine_row(self, row: TabletRow) -> TabletRow:
        # Path-aware logic is implemented in refine_file.
        return row

    def refine_file(self, path: Path) -> StepResult:
        lines = path.read_text(encoding="utf-8").splitlines()
        out_lines: List[str] = []
        rows_processed = 0
        rows_changed = 0

        is_ktu1 = path.name.startswith("KTU 1.")

        for raw in lines:
            if is_separator_line(raw) or not raw.strip():
                out_lines.append(raw)
                continue

            row = parse_tsv_line(raw)
            if row is None:
                out_lines.append(raw)
                continue

            rows_processed += 1
            if is_unresolved(row) or not is_ktu1:
                out_lines.append(raw)
                continue

            refined = self._prune_row(row)
            new_line = refined.to_tsv()
            if new_line != raw:
                rows_changed += 1
            out_lines.append(new_line)

        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return StepResult(file=path.name, rows_processed=rows_processed, rows_changed=rows_changed)

    def _prune_row(self, row: TabletRow) -> TabletRow:
        variants = _aligned_variants(row.analysis, row.dulat, row.pos, row.gloss)
        if len(variants) <= 1:
            return row

        indices_by_lemma: Dict[str, List[int]] = defaultdict(list)
        labels_by_index: Dict[int, str] = {}
        for idx, (_analysis, dulat, _pos, _gloss) in enumerate(variants):
            label = _head_label(dulat)
            m = _HOMONYM_LABEL_RE.match(label)
            if not m:
                continue
            lemma = m.group("lemma").strip()
            labels_by_index[idx] = label
            indices_by_lemma[lemma].append(idx)

        if not indices_by_lemma:
            return row

        drop_indexes: Set[int] = set()
        for _lemma, indices in indices_by_lemma.items():
            if len(indices) <= 1:
                continue
            ktu1_indexes: List[int] = []
            non1_indexes: List[int] = []
            for idx in indices:
                label = labels_by_index[idx]
                families = self._families_by_label.get(label, set())
                if "1" in families:
                    ktu1_indexes.append(idx)
                elif families:
                    non1_indexes.append(idx)
            if ktu1_indexes and non1_indexes:
                drop_indexes.update(non1_indexes)

        if not drop_indexes:
            return row

        kept = [item for idx, item in enumerate(variants) if idx not in drop_indexes]
        if not kept:
            return row

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=";".join(item[0] for item in kept),
            dulat=";".join(item[1] for item in kept),
            pos=";".join(item[2] for item in kept),
            gloss=";".join(item[3] for item in kept),
            comment=row.comment,
        )

    def _load_label_families(self, db_path: Path) -> Dict[str, Set[str]]:
        if not db_path.exists():
            return {}

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        entry_label: Dict[int, str] = {}
        cur.execute("SELECT entry_id, lemma, homonym FROM entries")
        for entry_id, lemma, homonym in cur.fetchall():
            lemma = (lemma or "").strip()
            homonym = (homonym or "").strip()
            if not lemma:
                continue
            label = f"{lemma} ({homonym})" if homonym else lemma
            entry_label[entry_id] = label

        families_by_label: Dict[str, Set[str]] = defaultdict(set)
        cur.execute("SELECT entry_id, citation FROM attestations")
        for entry_id, citation in cur.fetchall():
            label = entry_label.get(entry_id)
            if not label:
                continue
            family = _citation_family(citation or "")
            if family:
                families_by_label[label].add(family)

        conn.close()
        return {label: set(families) for label, families in families_by_label.items()}
