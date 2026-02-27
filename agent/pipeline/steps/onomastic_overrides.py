"""Shared loader for onomastic override TSV data."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Mapping

_KEY_NORMALIZE_MAP = str.maketrans(
    {
        "ʿ": "ʕ",
        "ˤ": "ʕ",
        "ˁ": "ʕ",
        "ʾ": "ʔ",
        "ˀ": "ʔ",
        "ả": "a",
        "ỉ": "i",
        "ủ": "u",
    }
)
_FEM_POS_RE = re.compile(r"(?:^|[\s,/])f\.\??(?:$|[\s,/])", flags=re.IGNORECASE)


@dataclass(frozen=True)
class OnomasticOverrideEntry:
    """One onomastic override row."""

    gloss: str = ""
    pos: str = ""

    @property
    def is_feminine(self) -> bool:
        return bool(_FEM_POS_RE.search(self.pos or ""))


class OnomasticOverrideStore:
    """Canonical onomastic overrides indexed by declared DULAT token."""

    def __init__(self, entries: Mapping[str, OnomasticOverrideEntry] | None = None) -> None:
        self._entries: Dict[str, OnomasticOverrideEntry] = {
            self.normalize_key(key): value
            for key, value in (entries or {}).items()
            if self.normalize_key(key)
        }

    @classmethod
    def from_gloss_map(cls, overrides: Mapping[str, str]) -> "OnomasticOverrideStore":
        entries = {
            key: OnomasticOverrideEntry(gloss=(value or "").strip(), pos="")
            for key, value in overrides.items()
            if (key or "").strip()
        }
        return cls(entries=entries)

    @classmethod
    def from_tsv(cls, path: Path) -> "OnomasticOverrideStore":
        if not path.exists():
            return cls()

        rows = path.read_text(encoding="utf-8").splitlines()
        entries: Dict[str, OnomasticOverrideEntry] = {}
        header_index: Dict[str, int] | None = None

        for raw in rows:
            line = (raw or "").strip()
            if not line or line.startswith("#"):
                continue

            parts = [part.strip() for part in raw.split("\t")]
            if header_index is None and line.lower().startswith("dulat\t"):
                header_index = {
                    name.strip().lower(): idx for idx, name in enumerate(parts) if name.strip()
                }
                continue

            if header_index is not None:
                key = _value_at(parts, header_index.get("dulat", 0))
                pos = _value_at(parts, header_index.get("pos"))
                gloss_idx = header_index.get("gloss")
                gloss = _value_at(parts, gloss_idx)
                if not gloss and len(parts) > 1:
                    # Backward compatibility for two-column files.
                    gloss = parts[1].strip()
            else:
                key = parts[0].strip() if parts else ""
                pos = ""
                gloss = parts[1].strip() if len(parts) > 1 else ""
                if len(parts) > 2:
                    if _looks_pos(parts[1]):
                        pos = parts[1].strip()
                        gloss = parts[2].strip()
                    else:
                        pos = parts[2].strip()

            norm_key = cls.normalize_key(key)
            if not norm_key:
                continue
            entries[norm_key] = OnomasticOverrideEntry(gloss=gloss.strip(), pos=pos.strip())

        return cls(entries=entries)

    @staticmethod
    def normalize_key(value: str) -> str:
        return " ".join((value or "").translate(_KEY_NORMALIZE_MAP).split())

    def get_gloss(self, dulat_token: str) -> str | None:
        entry = self._entries.get(self.normalize_key(dulat_token))
        if entry is None:
            return None
        return entry.gloss or None

    def is_feminine(self, dulat_token: str) -> bool:
        entry = self._entries.get(self.normalize_key(dulat_token))
        if entry is None:
            return False
        return entry.is_feminine

    def feminine_tokens(self) -> set[str]:
        return {token for token, entry in self._entries.items() if entry.is_feminine}


def _value_at(parts: list[str], index: int | None) -> str:
    if index is None or index < 0 or index >= len(parts):
        return ""
    return parts[index].strip()


def _looks_pos(value: str) -> bool:
    token = (value or "").strip().upper()
    return any(tag in token for tag in ("DN", "PN", "TN", "GN", "MN", "N.", "ADJ", "VB"))
