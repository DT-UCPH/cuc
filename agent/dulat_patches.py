"""Entry-metadata patches for defective DULAT cache rows.

The DULAT sqlite cache occasionally carries malformed entry rows (for
example entry 2727: lemma ``mlk (I)`` with empty homonym and empty POS),
which makes high-frequency words invisible to lemma lookups and POS-based
ranking. Patches are maintained as a reviewable TSV
(``data_sources/dulat_entry_patches.tsv``) and applied by loaders at read
time, keeping the cache itself untouched.
"""

from pathlib import Path
from typing import Dict

_PATCH_FIELDS = ("lemma", "homonym", "pos")


def load_dulat_entry_patches(path: Path) -> Dict[int, Dict[str, str]]:
    """Load entry patches keyed by entry_id.

    Args:
        path: TSV with columns ``entry_id, lemma, homonym, pos``. Blank cells
            leave the corresponding field unpatched.

    Returns:
        Mapping of entry_id to the non-blank fields to override.
    """
    patches: Dict[int, Dict[str, str]] = {}
    if not path.exists():
        return patches
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.lower().startswith("entry_id\t"):
            continue
        parts = raw.split("\t")
        if not parts or not parts[0].strip().isdigit():
            continue
        entry_id = int(parts[0].strip())
        fields: Dict[str, str] = {}
        for offset, name in enumerate(_PATCH_FIELDS, start=1):
            value = parts[offset].strip() if len(parts) > offset else ""
            if value:
                fields[name] = value
        if fields:
            patches[entry_id] = fields
    return patches
