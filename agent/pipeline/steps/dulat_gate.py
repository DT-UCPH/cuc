"""DULAT-backed morphology feature gate for conservative refinement steps."""

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from pipeline.config.dulat_form_morph_overrides import override_dulat_form_morphology
from pipeline.config.dulat_form_text_overrides import expand_dulat_form_texts
from pipeline.config.plurale_tantum_m_overrides import PLURALE_TANTUM_M_EXCLUDED_KEYS

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
_DUAL_RE = re.compile(r"\bdu\.", flags=re.IGNORECASE)
_DUAL_WORD_RE = re.compile(r"\bdual", flags=re.IGNORECASE)
_SINGULAR_RE = re.compile(r"\bsg\.", flags=re.IGNORECASE)
_SINGULAR_WORD_RE = re.compile(r"\bsing", flags=re.IGNORECASE)
_SUFFIX_RE = re.compile(r"\bsuff", flags=re.IGNORECASE)
_CONSTRUCT_RE = re.compile(r"\bcst(?:r)?\.?\b", flags=re.IGNORECASE)
_TOKEN_RE = re.compile(r"^(.*?)(?:\s*\(([IVX]+)\))?$")


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
        self._plurale_tantum_noun_keys: set[Tuple[str, str]] = set()
        self._genders_by_token: Dict[Tuple[str, str], set[str]] = {}
        if db_path.exists():
            (
                self._features,
                self._forms_by_token,
                self._plurale_tantum_noun_keys,
                self._genders_by_token,
            ) = self._load_features(db_path)

    def is_plural_token(self, token: str, surface: str = "") -> bool:
        return self._feature_for_token(token, surface).has_plural

    def has_suffix_token(self, token: str, surface: str = "") -> bool:
        return self._feature_for_token(token, surface).has_pronominal_suffix

    def is_plurale_tantum_noun_token(self, token: str) -> bool:
        lemma, hom = self._parse_declared_token(token)
        if not lemma or lemma == "?":
            return False
        keys = self._keys_for_token(lemma=lemma, hom=hom)
        if not keys:
            return False
        return any(key in self._plurale_tantum_noun_keys for key in keys)

    def token_genders(self, token: str) -> set[str]:
        """Return DULAT entry gender markers (e.g. m./f.) for declared token."""
        lemma, hom = self._parse_declared_token(token)
        if not lemma or lemma == "?":
            return set()
        keys = self._keys_for_token(lemma=lemma, hom=hom)
        out: set[str] = set()
        for key in keys:
            out.update(self._genders_by_token.get(key, set()))
        return out

    def surface_morphologies(self, token: str, surface: str) -> set[str]:
        """Return morphology labels for exact token+surface matches."""
        lemma, hom = self._parse_declared_token(token)
        if not lemma or lemma == "?":
            return set()
        keys = self._keys_for_token(lemma=lemma, hom=hom)
        if not keys:
            return set()

        canon_surface = self._normalize_form(surface)
        if not canon_surface:
            return set()

        out: set[str] = set()
        for key in keys:
            for form_text, morphology in self._forms_by_token.get(key, []):
                if form_text != canon_surface:
                    continue
                morph = (morphology or "").strip().lower()
                if morph:
                    out.add(morph)
        return out

    def has_surface_form(self, token: str, surface: str) -> bool:
        """Return True when token has an exact surface form in DULAT forms."""
        lemma, hom = self._parse_declared_token(token)
        if not lemma or lemma == "?":
            return False
        keys = self._keys_for_token(lemma=lemma, hom=hom)
        if not keys:
            return False

        canon_surface = self._normalize_form(surface)
        if not canon_surface:
            return False

        for key in keys:
            for form_text, _morphology in self._forms_by_token.get(key, []):
                if form_text == canon_surface:
                    return True
        return False

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
        set[Tuple[str, str]],
        Dict[Tuple[str, str], set[str]],
    ]:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        entry_index: Dict[int, Tuple[str, str]] = {}
        entry_pos_index: Dict[int, str] = {}
        entry_gender_index: Dict[int, str] = {}
        for entry_id, lemma, homonym in cur.execute("SELECT entry_id, lemma, homonym FROM entries"):
            lemma_raw = (lemma or "").strip()
            hom = (homonym or "").strip()
            if lemma_raw and not hom:
                match = re.match(r"^(.*)\s+\(([IVX]+)\)$", lemma_raw)
                if match:
                    lemma_raw = match.group(1).strip()
                    hom = match.group(2)
            entry_index[int(entry_id)] = (self._normalize(lemma_raw), hom)
        for entry_id, pos in cur.execute("SELECT entry_id, pos FROM entries"):
            entry_pos_index[int(entry_id)] = (pos or "").strip()
        try:
            for entry_id, gender in cur.execute("SELECT entry_id, gender FROM entries"):
                g = (gender or "").strip().lower()
                if g:
                    entry_gender_index[int(entry_id)] = g
        except sqlite3.Error:
            entry_gender_index = {}

        by_key: Dict[Tuple[str, str], List[str]] = {}
        forms_by_key: Dict[Tuple[str, str], List[Tuple[str, str]]] = {}
        for entry_id, text, morphology in cur.execute(
            "SELECT entry_id, text, morphology FROM forms"
        ):
            key = entry_index.get(int(entry_id))
            if not key:
                continue
            lemma, hom = key
            morph = override_dulat_form_morphology(
                lemma=lemma,
                homonym=hom,
                form_text=text or "",
                morphology=(morphology or "").strip(),
            )
            by_key.setdefault(key, []).append(morph)
            for form_variant in expand_dulat_form_texts(
                lemma=lemma,
                homonym=hom,
                form_text=text or "",
            ):
                forms_by_key.setdefault(key, []).append((self._normalize_form(form_variant), morph))

        conn.close()

        features: Dict[Tuple[str, str], TokenFeatures] = {}
        plurale_tantum_noun_keys: set[Tuple[str, str]] = set()
        genders_by_key: Dict[Tuple[str, str], set[str]] = {}
        for entry_id, key in entry_index.items():
            gender = entry_gender_index.get(entry_id, "")
            if not gender:
                continue
            genders_by_key.setdefault(key, set()).add(gender)

        for key, morphologies in by_key.items():
            flags = self._flags_from_morphologies(morphologies)
            features[key] = flags
            if self._is_plurale_tantum_noun_key(
                key=key,
                morphologies=morphologies,
                entry_index=entry_index,
                entry_pos_index=entry_pos_index,
            ):
                plurale_tantum_noun_keys.add(key)
        return features, forms_by_key, plurale_tantum_noun_keys, genders_by_key

    def _flags_from_morphologies(self, morphologies: Sequence[str]) -> TokenFeatures:
        has_plural = False
        has_suffix = False
        for morph in morphologies:
            text = (morph or "").lower()
            if not text:
                continue
            if (
                _PLURAL_RE.search(text)
                or _PLURAL_WORD_RE.search(text)
                or _DUAL_RE.search(text)
                or _DUAL_WORD_RE.search(text)
            ):
                has_plural = True
            if _SUFFIX_RE.search(text):
                has_suffix = True
            if has_plural and has_suffix:
                break

        return TokenFeatures(has_plural=has_plural, has_pronominal_suffix=has_suffix)

    def _is_plurale_tantum_noun_key(
        self,
        key: Tuple[str, str],
        morphologies: Sequence[str],
        entry_index: Dict[int, Tuple[str, str]],
        entry_pos_index: Dict[int, str],
    ) -> bool:
        if not (key[0] or "").endswith("m"):
            return False
        if key in PLURALE_TANTUM_M_EXCLUDED_KEYS:
            return False
        pos_values = {
            (entry_pos_index.get(entry_id) or "").lower()
            for entry_id, entry_key in entry_index.items()
            if entry_key == key
        }
        if not pos_values:
            return False
        if not all(pos.startswith("n.") and "num" not in pos for pos in pos_values):
            return False

        non_suffix = []
        for morph in morphologies:
            text = (morph or "").lower().strip()
            if not text:
                continue
            if _SUFFIX_RE.search(text):
                continue
            non_suffix.append(text)

        if not non_suffix:
            return False
        if any(self._morphology_is_explicit_singular(morph) for morph in morphologies):
            return False
        if not any(
            (
                _PLURAL_RE.search(morph)
                or _PLURAL_WORD_RE.search(morph)
                or _DUAL_RE.search(morph)
                or _DUAL_WORD_RE.search(morph)
            )
            and not _CONSTRUCT_RE.search(morph)
            for morph in non_suffix
        ):
            return False
        return all(
            (
                _PLURAL_RE.search(morph)
                or _PLURAL_WORD_RE.search(morph)
                or _DUAL_RE.search(morph)
                or _DUAL_WORD_RE.search(morph)
            )
            for morph in non_suffix
        )

    def _morphology_is_explicit_singular(self, morph: str) -> bool:
        text = (morph or "").lower().strip()
        if not text:
            return False
        return bool(_SINGULAR_RE.search(text) or _SINGULAR_WORD_RE.search(text))

    def _normalize(self, text: str) -> str:
        return (text or "").translate(LOOKUP_NORMALIZE).strip()

    def _normalize_form(self, text: str) -> str:
        normalized = self._normalize(text).lower()
        return "".join(ch for ch in normalized if ch.isalpha())

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
