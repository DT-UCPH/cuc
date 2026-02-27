"""Instruction-driven high-confidence refinement for parsed tablet TSV files."""

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from pipeline.config.dulat_form_text_overrides import expand_dulat_form_texts

DISALLOWED_NORMALIZE = str.maketrans(
    {
        "ʿ": "ˤ",
        "ʕ": "ˤ",
        "ả": "a",
        "ỉ": "i",
        "ủ": "u",
    }
)
_PLURAL_RE = re.compile(r"\bpl\.", flags=re.IGNORECASE)
_PLURAL_WORD_RE = re.compile(r"\bplural\b", flags=re.IGNORECASE)
_DUAL_RE = re.compile(r"\bdu\.", flags=re.IGNORECASE)
_DUAL_WORD_RE = re.compile(r"\bdual\b", flags=re.IGNORECASE)
_SINGULAR_RE = re.compile(r"\bsg\.", flags=re.IGNORECASE)
_SINGULAR_WORD_RE = re.compile(r"\bsing", flags=re.IGNORECASE)
_NUMBER_MARKER_RE = re.compile(r"\b(?:sg|pl|du)\.", flags=re.IGNORECASE)

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


@dataclass(frozen=True)
class RefinementResult:
    """Refinement summary for one file batch."""

    files: int
    rows: int
    changed: int


class InstructionRefiner:
    """Applies conservative, instruction-backed formatting refinements."""

    def __init__(self, dulat_db: Optional[Path] = None) -> None:
        self._gender_index: Dict[Tuple[str, str], List[str]] = {}
        self._form_morph_index: Dict[Tuple[str, str], Dict[str, set[str]]] = {}
        if dulat_db is not None and Path(dulat_db).exists():
            db_path = Path(dulat_db)
            self._gender_index = self._load_gender_index(db_path)
            self._form_morph_index = self._load_form_morph_index(db_path)

    def refine_files(self, paths: Sequence[Path]) -> RefinementResult:
        file_count = 0
        row_count = 0
        changed_count = 0
        for path in paths:
            rows, changed = self.refine_file(path)
            file_count += 1
            row_count += rows
            changed_count += changed
        return RefinementResult(files=file_count, rows=row_count, changed=changed_count)

    def refine_file(self, path: Path) -> Tuple[int, int]:
        rows = 0
        changed = 0
        out_lines: List[str] = []
        for raw in path.read_text(encoding="utf-8").splitlines():
            if not raw.strip() or raw.startswith("#"):
                out_lines.append(raw)
                continue

            parts = raw.split("\t")
            if len(parts) < 2:
                out_lines.append(raw)
                continue

            rows += 1
            line_id = parts[0].strip()
            surface = self._normalize_col23(parts[1] if len(parts) > 1 else "")
            analysis = self._normalize_col23(parts[2] if len(parts) > 2 else "")
            dulat = (parts[3] if len(parts) > 3 else "").strip()
            pos = self._normalize_pos_field(parts[4] if len(parts) > 4 else "")
            gloss = (parts[5] if len(parts) > 5 else "").strip()
            note = "\t".join(parts[6:]).strip() if len(parts) > 6 else ""

            if self._is_unresolved_row(
                analysis=analysis,
                dulat=dulat,
                pos=pos,
                gloss=gloss,
                note=note,
            ):
                analysis = "?"
                dulat = "?"
                pos = "?"
                gloss = "?"
            else:
                pos = self._enrich_pos_gender(dulat_field=dulat, pos_field=pos)
                pos = self._enrich_pos_number(
                    surface_field=surface,
                    dulat_field=dulat,
                    pos_field=pos,
                )

            new_parts = [line_id, surface, analysis, dulat, pos, gloss]
            if note:
                new_parts.append(note)
            new_line = "\t".join(new_parts)
            if new_line != raw:
                changed += 1
            out_lines.append(new_line)

        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
        return rows, changed

    def _normalize_col23(self, value: str) -> str:
        return (value or "").translate(DISALLOWED_NORMALIZE).strip()

    def _normalize_pos_field(self, field: str) -> str:
        variants = [item.strip() for item in (field or "").split(";")]
        normalized_variants: List[str] = []
        for variant in variants:
            if not variant:
                continue
            slots = [slot.strip() for slot in variant.split(",")]
            normalized_slots: List[str] = []
            for slot in slots:
                if not slot:
                    continue
                compact = " ".join(slot.split())
                normalized_slots.append(POS_LABEL_NORMALIZATION.get(compact.lower(), compact))
            normalized_variants.append(",".join(normalized_slots))
        return ";".join(normalized_variants)

    def _enrich_pos_gender(self, dulat_field: str, pos_field: str) -> str:
        if not self._gender_index:
            return pos_field

        d_variants = [item.strip() for item in (dulat_field or "").split(";")]
        p_variants = [item.strip() for item in (pos_field or "").split(";")]
        if not d_variants or not p_variants:
            return pos_field

        out_variants: List[str] = []
        for idx, p_variant in enumerate(p_variants):
            d_variant = d_variants[idx] if idx < len(d_variants) else ""
            d_slots = [slot.strip() for slot in d_variant.split(",") if slot.strip()]
            p_slots = [slot.strip() for slot in p_variant.split(",") if slot.strip()]
            if not d_slots or not p_slots:
                out_variants.append(p_variant)
                continue

            for slot_idx, p_slot in enumerate(p_slots):
                if slot_idx >= len(d_slots):
                    continue
                gender = self._gender_for_token(d_slots[slot_idx])
                if gender is None:
                    continue
                p_slots[slot_idx] = self._inject_gender(p_slot=p_slot, gender=gender)

            out_variants.append(",".join(p_slots))

        return ";".join(out_variants)

    def _gender_for_token(self, token: str) -> Optional[str]:
        lemma, hom = self._parse_declared_dulat_token(token)
        if not lemma or lemma == "?":
            return None

        genders: List[str] = []
        for key in self._keys_for_token(lemma=lemma, hom=hom):
            for value in self._gender_index.get(key, []):
                if value not in genders:
                    genders.append(value)

        if len(set(genders)) == 1:
            return genders[0]
        return None

    def _enrich_pos_number(self, surface_field: str, dulat_field: str, pos_field: str) -> str:
        if not self._form_morph_index:
            return pos_field

        d_variants = [item.strip() for item in (dulat_field or "").split(";")]
        p_variants = [item.strip() for item in (pos_field or "").split(";")]
        if not d_variants or not p_variants:
            return pos_field

        out_variants: List[str] = []
        for idx, p_variant in enumerate(p_variants):
            d_variant = d_variants[idx] if idx < len(d_variants) else ""
            d_slots = [slot.strip() for slot in d_variant.split(",") if slot.strip()]
            p_slots = [slot.strip() for slot in p_variant.split(",") if slot.strip()]
            if not d_slots or not p_slots:
                out_variants.append(p_variant)
                continue

            for slot_idx, p_slot in enumerate(p_slots):
                if slot_idx >= len(d_slots):
                    continue
                number = self._number_for_token_surface(
                    token=d_slots[slot_idx], surface=surface_field
                )
                if number is None:
                    continue
                p_slots[slot_idx] = self._inject_number(p_slot=p_slot, number=number)

            out_variants.append(",".join(p_slots))

        return ";".join(out_variants)

    def _number_for_token_surface(self, token: str, surface: str) -> Optional[str]:
        lemma, hom = self._parse_declared_dulat_token(token)
        if not lemma or lemma == "?":
            return None

        surface_key = self._normalize_lookup(surface)
        if not surface_key:
            return None

        numbers: set[str] = set()
        for key in self._keys_for_token(lemma=lemma, hom=hom):
            by_surface = self._form_morph_index.get(key, {})
            for morphology in by_surface.get(surface_key, set()):
                numbers.update(self._extract_number_markers(morphology))

        if len(numbers) == 1:
            return next(iter(numbers))
        return None

    def _extract_number_markers(self, morphology: str) -> set[str]:
        text = (morphology or "").lower()
        markers: set[str] = set()
        if _SINGULAR_RE.search(text) or _SINGULAR_WORD_RE.search(text):
            markers.add("sg.")
        if _PLURAL_RE.search(text) or _PLURAL_WORD_RE.search(text):
            markers.add("pl.")
        if _DUAL_RE.search(text) or _DUAL_WORD_RE.search(text):
            markers.add("du.")
        return markers

    def _inject_gender(self, p_slot: str, gender: str) -> str:
        slot = p_slot
        if re.search(r"\bn\.\s*[mf]\.", slot):
            return slot
        if re.search(r"\badj\.\s*[mf]\.", slot):
            return slot

        if "n." in slot:
            slot = re.sub(r"\bn\.(?!\s*[mf]\.)", "n. %s" % gender, slot, count=1)
        if "adj." in slot:
            slot = re.sub(r"\badj\.(?!\s*[mf]\.)", "adj. %s" % gender, slot, count=1)
        return slot

    def _inject_number(self, p_slot: str, number: str) -> str:
        slot = p_slot
        if _NUMBER_MARKER_RE.search(slot):
            return slot
        if "n." in slot:
            if re.search(r"\bn\.\s*[mf]\.", slot):
                return re.sub(
                    r"(\bn\.\s*[mf]\.)",
                    r"\1 %s" % number,
                    slot,
                    count=1,
                )
            return re.sub(r"\bn\.", "n. %s" % number, slot, count=1)
        if "adj." in slot:
            if re.search(r"\badj\.\s*[mf]\.", slot):
                return re.sub(
                    r"(\badj\.\s*[mf]\.)",
                    r"\1 %s" % number,
                    slot,
                    count=1,
                )
            return re.sub(r"\badj\.", "adj. %s" % number, slot, count=1)
        return slot

    def _load_gender_index(self, db_path: Path) -> Dict[Tuple[str, str], List[str]]:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        index: Dict[Tuple[str, str], List[str]] = {}

        for lemma, homonym, gender in cur.execute("SELECT lemma, homonym, gender FROM entries"):
            lemma_raw = (lemma or "").strip()
            hom = (homonym or "").strip()
            g = (gender or "").strip().lower()
            if g not in {"m.", "f."}:
                continue

            if lemma_raw and not hom:
                match = re.match(r"^(.*)\s+\(([IV]+)\)$", lemma_raw)
                if match:
                    lemma_raw = match.group(1).strip()
                    hom = match.group(2)

            key = (self._normalize_lookup(lemma_raw), hom)
            values = index.setdefault(key, [])
            if g not in values:
                values.append(g)

        conn.close()
        return index

    def _load_form_morph_index(self, db_path: Path) -> Dict[Tuple[str, str], Dict[str, set[str]]]:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        entry_index: Dict[int, Tuple[str, str]] = {}
        for entry_id, lemma, homonym in cur.execute("SELECT entry_id, lemma, homonym FROM entries"):
            lemma_raw = (lemma or "").strip()
            hom = (homonym or "").strip()
            if lemma_raw and not hom:
                match = re.match(r"^(.*)\s+\(([IV]+)\)$", lemma_raw)
                if match:
                    lemma_raw = match.group(1).strip()
                    hom = match.group(2)
            entry_index[int(entry_id)] = (self._normalize_lookup(lemma_raw), hom)

        form_morph_index: Dict[Tuple[str, str], Dict[str, set[str]]] = {}
        for entry_id, text, morphology in cur.execute(
            "SELECT entry_id, text, morphology FROM forms"
        ):
            key = entry_index.get(int(entry_id))
            if not key:
                continue
            lemma, hom = key
            morph = (morphology or "").strip().lower()
            if not morph:
                continue
            for form_variant in expand_dulat_form_texts(
                lemma=lemma,
                homonym=hom,
                form_text=text or "",
            ):
                surface_key = self._normalize_lookup(form_variant)
                if not surface_key:
                    continue
                by_surface = form_morph_index.setdefault(key, {})
                by_surface.setdefault(surface_key, set()).add(morph)

        conn.close()
        return form_morph_index

    def _normalize_lookup(self, text: str) -> str:
        return (text or "").translate(DISALLOWED_NORMALIZE).strip()

    def _keys_for_token(self, lemma: str, hom: str) -> List[Tuple[str, str]]:
        lemma_key = self._normalize_lookup(lemma)
        hom_key = (hom or "").strip()
        if not lemma_key:
            return []

        keys = [(lemma_key, hom_key)]
        if hom_key:
            return keys

        seen = set(keys)
        for source in (self._gender_index, self._form_morph_index):
            for key in source.keys():
                if key[0] != lemma_key or key in seen:
                    continue
                keys.append(key)
                seen.add(key)
        return keys

    def _parse_declared_dulat_token(self, token: str) -> Tuple[str, str]:
        tok = (token or "").strip()
        if not tok:
            return "", ""

        match = re.match(r"^(.*?)(?:\s*\(([IV]+)\))?$", tok)
        if not match:
            return tok, ""
        lemma = (match.group(1) or "").strip()
        hom = (match.group(2) or "").strip()
        return lemma, hom

    def _is_unresolved_row(
        self, analysis: str, dulat: str, pos: str, gloss: str, note: str
    ) -> bool:
        note_upper = (note or "").upper()
        if "DULAT: NOT FOUND" in note_upper:
            return True
        if (analysis or "").strip() == "?":
            return True
        if not dulat and not pos and not gloss:
            return True
        return False
