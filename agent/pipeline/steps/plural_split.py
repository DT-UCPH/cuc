"""Fix plural nouns missing explicit split endings (/m, /t=)."""

import re
from typing import Optional

from pipeline.steps.analysis_utils import normalize_surface, reconstruct_surface_from_analysis
from pipeline.steps.base import RefinementStep, TabletRow
from pipeline.steps.dulat_gate import DulatMorphGate

# Match a noun ending with the plural -m or -t directly before the '/' closure.
# e.g. nhrm/ → nhr/m or nhrt/ → nhr/t=
_PLURAL_M_RE = re.compile(r"^([A-Za-zˤʔḫṣṯẓġḏḥṭš()\[\]!&~:]+?)m(\([IVX]+\))?/$")
_PLURAL_T_RE = re.compile(r"^([A-Za-zˤʔḫṣṯẓġḏḥṭš()\[\]!&~:]+?)t(\([IVX]+\))?/$")
_TOKEN_RE = re.compile(r"^(.*?)(?:\s*\(([IVX]+)\))?$")
_LEMMA_LETTER_RE = re.compile(r"[^A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]")


class PluralSplitFixer(RefinementStep):
    """Rewrite plural noun analyses to use explicit split endings: X/m or X/t=."""

    def __init__(self, gate: Optional[DulatMorphGate] = None) -> None:
        self._gate = gate

    @property
    def name(self) -> str:
        return "plural-split"

    def refine_row(self, row: TabletRow) -> TabletRow:
        pos = row.pos.strip()
        if not pos:
            return row

        analysis = row.analysis
        if not analysis:
            return row

        variants = analysis.split(";")
        pos_variants = [v.strip() for v in pos.split(";")]
        dulat_variants = [v.strip() for v in row.dulat.split(";")]
        changed = False
        out_variants = []

        for idx, var in enumerate(variants):
            var = var.strip()
            pos_v = pos_variants[idx].strip() if idx < len(pos_variants) else ""
            dulat_tok = dulat_variants[idx].strip() if idx < len(dulat_variants) else ""
            new_var = self._fix_variant(var, pos_v, dulat_tok, row.surface)
            if new_var != var:
                changed = True
            out_variants.append(new_var)

        if not changed:
            return row

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=";".join(out_variants),
            dulat=row.dulat,
            pos=row.pos,
            gloss=row.gloss,
            comment=row.comment,
        )

    def _fix_variant(self, var: str, pos_v: str, dulat_tok: str, surface: str) -> str:
        """Fix a single analysis variant if it needs plural split."""
        # Only fix noun/adjective slots.
        first_slot = pos_v.split(",")[0].strip() if pos_v else ""
        if not (first_slot.startswith("n.") or first_slot.startswith("adj.")):
            return var

        # Require DULAT evidence that the token has plural morphology.
        if not self._is_plural_dulat_token(dulat_tok, surface):
            return var

        repaired = self._repair_truncated_lemma_before_split(
            var=var,
            dulat_tok=dulat_tok,
            surface=surface,
        )
        if repaired != var:
            return repaired

        # Already has explicit split (contains /m or /t=)?
        if var.endswith(("/m", "/t", "/m=", "/t=")):
            return var

        lemma_letters = _declared_lemma_letters(dulat_tok)

        # Try masculine plural: Xm/ → X/m
        m = _PLURAL_M_RE.match(var)
        if m and not lemma_letters.endswith("m"):
            base = m.group(1)
            hom = m.group(2) or ""
            return f"{base}{hom}/m"

        # Try feminine plural: Xt/ → X/t=
        m = _PLURAL_T_RE.match(var)
        if m and not lemma_letters.endswith("t"):
            base = m.group(1)
            hom = m.group(2) or ""
            return f"{base}{hom}/t="

        # Fallback for lemma-style analyses (e.g., il(I)/ for surface ilm):
        # if analysis reconstructs to the surface without final m/t, append split.
        if not var.endswith("/"):
            return var
        if "/" not in var:
            return var

        surface_norm = normalize_surface(surface)
        if not surface_norm:
            return var
        analysis_surface = normalize_surface(reconstruct_surface_from_analysis(var))
        if (
            surface_norm.endswith("m")
            and not lemma_letters.endswith("m")
            and analysis_surface == surface_norm[:-1]
        ):
            return f"{var}m"
        if (
            surface_norm.endswith("t")
            and not lemma_letters.endswith("t")
            and analysis_surface == surface_norm[:-1]
        ):
            return f"{var}t="

        return var

    def _is_plural_dulat_token(self, token: str, surface: str) -> bool:
        if not token or token == "?":
            return False
        if self._gate is None:
            return False
        return self._gate.is_plural_token(token, surface=surface)

    def _repair_truncated_lemma_before_split(
        self,
        var: str,
        dulat_tok: str,
        surface: str,
    ) -> str:
        """Repair malformed split variants like šl(II)/m -> šlm(II)/m.

        A previous split pass can accidentally drop a lemma-final consonant
        before the homonym marker. This method restores the consonant when:
        - variant has an explicit split ending (/m or /t=),
        - DULAT lemma ends with that same consonant, and
        - current reconstruction is exactly one letter short of the surface.
        """
        split_idx = var.rfind("/")
        if split_idx <= 0:
            return var

        split_suffix = var[split_idx + 1 :]
        if split_suffix not in {"m", "t", "t="}:
            return var
        split_letter = "m" if split_suffix == "m" else "t"

        prefix = var[:split_idx]
        hom_match = re.search(r"\([IVX]+\)$", prefix)
        if not hom_match:
            return var
        stem = prefix[: hom_match.start()]
        hom = hom_match.group(0)
        if not stem:
            return var

        lemma_letters = _declared_lemma_letters(dulat_tok)
        if not lemma_letters.endswith(split_letter):
            return var

        surface_norm = normalize_surface(surface)
        recon_norm = normalize_surface(reconstruct_surface_from_analysis(var))
        if not surface_norm or recon_norm != surface_norm[:-1]:
            return var

        if normalize_surface(stem).endswith(split_letter):
            return var

        return f"{stem}{split_letter}{hom}/{split_suffix}"


def _declared_lemma_letters(dulat_token: str) -> str:
    token = (dulat_token or "").strip()
    if not token:
        return ""
    if "," in token:
        token = token.split(",", 1)[0].strip()
    if token.startswith("/"):
        return ""
    m = _TOKEN_RE.match(token)
    lemma = (m.group(1) if m else token).strip()
    letters = _LEMMA_LETTER_RE.sub("", normalize_surface(lemma)).lower()
    return letters
