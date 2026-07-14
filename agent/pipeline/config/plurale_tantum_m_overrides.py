"""Curated DULAT overrides for automatic -m plurale-tantum detection."""

from __future__ import annotations

from typing import Final

# Keys use parser/linter-normalized lemma text:
# - ʿ/ˤ -> ʕ
# - ả/ỉ/ủ -> a/i/u
PLURALE_TANTUM_M_EXCLUDED_KEYS: Final[set[tuple[str, str]]] = {
    ("ḥlm", "II"),
    ("ʕgm", ""),
    ("ištnm", ""),
}
