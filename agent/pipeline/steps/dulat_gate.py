"""DULAT-backed morphology feature gate for conservative refinement steps."""

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

LOOKUP_NORMALIZE = str.maketrans(
    {
        "ʿ": "ʕ",
        "ˤ": "ʕ",
        "ả": "a",
        "ỉ": "i",
        "ủ": "u",
    }
)

_PLURAL_RE = re.compile(r"\bpl\.", flags=re.IGNORECASE)
_PLURAL_WORD_RE = re.compile(r"\bplur", flags=re.IGNORECASE)
_SUFFIX_RE = re.compile(r"\bsuff", flags=re.IGNORECASE)
_TOKEN_RE = re.compile(r"^(.*?)(?:\s*\(([IVX]+)\))?$")
_NON_FORM_CHAR_RE = re.compile(r"[^A-Za-zʔʕˤʿḫḥṭṣṯẓġḏšảỉủ]")


@dataclass(frozen=True)
class TokenFeatures:
    """Feature flags extracted from DULAT forms for one token."""

    has_plural: bool
    has_pronominal_suffix: bool


class DulatMorphGate:
    """Provides feature checks for declared DULAT tokens in column 4."""

    def __init__(self, db_path: Path) -> None:
        self._features: Dict[Tuple[str, str], TokenFeatures] = {}
        self._forms_by_token: Dict[Tuple[str, str], List[Tuple[str, str]]] = {}
        if db_path.exists():
            self._features, self._forms_by_token = self._load_features(db_path)

    def is_plural_token(self, token: str, surface: str = "") -> bool:
        return self._feature_for_token(token, surface).has_plural

    def has_suffix_token(self, token: str, surface: str = "") -> bool:
        return self._feature_for_token(token, surface).has_pronominal_suffix

    def _feature_for_token(self, token: str, surface: str = "") -> TokenFeatures:
        lemma, hom = self._parse_declared_token(token)
        if not lemma or lemma == "?":
            return TokenFeatures(has_plural=False, has_pronominal_suffix=False)

        keys = self._keys_for_token(lemma=lemma, hom=hom)
        if not keys:
            return TokenFeatures(has_plural=False, has_pronominal_suffix=False)

        # Conservative surface-aware mode: only trust features for matched surface forms.
        if surface:
            match = self._surface_match_features(keys=keys, surface=surface)
            if match is not None:
                return match
            return TokenFeatures(has_plural=False, has_pronominal_suffix=False)

        plural = False
        suffix = False
        for key in keys:
            features = self._features.get(key)
            if features is None:
                continue
            plural = plural or features.has_plural
            suffix = suffix or features.has_pronominal_suffix

        return TokenFeatures(has_plural=plural, has_pronominal_suffix=suffix)

    def _load_features(
        self, db_path: Path
    ) -> Tuple[
        Dict[Tuple[str, str], TokenFeatures],
        Dict[Tuple[str, str], List[Tuple[str, str]]],
    ]:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        entry_index: Dict[int, Tuple[str, str]] = {}
        for entry_id, lemma, homonym in cur.execute("SELECT entry_id, lemma, homonym FROM entries"):
            lemma_raw = (lemma or "").strip()
            hom = (homonym or "").strip()
            if lemma_raw and not hom:
                match = re.match(r"^(.*)\s+\(([IVX]+)\)$", lemma_raw)
                if match:
                    lemma_raw = match.group(1).strip()
                    hom = match.group(2)
            entry_index[int(entry_id)] = (self._normalize(lemma_raw), hom)

        by_key: Dict[Tuple[str, str], List[str]] = {}
        forms_by_key: Dict[Tuple[str, str], List[Tuple[str, str]]] = {}
        for entry_id, text, morphology in cur.execute(
            "SELECT entry_id, text, morphology FROM forms"
        ):
            key = entry_index.get(int(entry_id))
            if not key:
                continue
            morph = (morphology or "").strip()
            by_key.setdefault(key, []).append(morph)
            forms_by_key.setdefault(key, []).append((self._normalize_form(text or ""), morph))

        conn.close()

        features: Dict[Tuple[str, str], TokenFeatures] = {}
        for key, morphologies in by_key.items():
            flags = self._flags_from_morphologies(morphologies)
            features[key] = flags
        return features, forms_by_key

    def _flags_from_morphologies(self, morphologies: Sequence[str]) -> TokenFeatures:
        has_plural = False
        has_suffix = False
        for morph in morphologies:
            text = (morph or "").lower()
            if not text:
                continue
            if _PLURAL_RE.search(text) or _PLURAL_WORD_RE.search(text):
                has_plural = True
            if _SUFFIX_RE.search(text):
                has_suffix = True
            if has_plural and has_suffix:
                break

        return TokenFeatures(has_plural=has_plural, has_pronominal_suffix=has_suffix)

    def _normalize(self, text: str) -> str:
        return (text or "").translate(LOOKUP_NORMALIZE).strip()

    def _normalize_form(self, text: str) -> str:
        normalized = self._normalize(text).lower()
        return _NON_FORM_CHAR_RE.sub("", normalized)

    def _parse_declared_token(self, token: str) -> Tuple[str, str]:
        tok = (token or "").strip()
        if not tok or tok.startswith("/") or tok == "?":
            return "", ""

        match = _TOKEN_RE.match(tok)
        if not match:
            return tok, ""
        lemma = (match.group(1) or "").strip()
        hom = (match.group(2) or "").strip()
        return lemma, hom

    def _keys_for_token(self, lemma: str, hom: str) -> List[Tuple[str, str]]:
        key = (self._normalize(lemma), hom or "")
        if hom:
            return [key]

        out: List[Tuple[str, str]] = []
        for (lemma_key, hom_key), _features in self._features.items():
            if lemma_key == key[0]:
                out.append((lemma_key, hom_key))
        return out

    def _surface_match_features(
        self, keys: Sequence[Tuple[str, str]], surface: str
    ) -> TokenFeatures | None:
        canon_surface = self._normalize_form(surface)
        if not canon_surface:
            return None

        matched_morphologies: List[str] = []
        for key in keys:
            for form_text, morphology in self._forms_by_token.get(key, []):
                if form_text == canon_surface:
                    matched_morphologies.append(morphology)

        if not matched_morphologies:
            return None
        return self._flags_from_morphologies(matched_morphologies)
