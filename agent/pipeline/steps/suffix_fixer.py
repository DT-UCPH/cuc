"""Fix suffix/clitic forms missing the '+' separator in analysis column.

When DULAT morphology indicates a pronominal suffix and the surface form ends
with a known suffix segment (h, k, km, kn, n, ny, hm, hn, y), inject '+' before
the suffix in the analysis.
"""

import re
from typing import Optional

from pipeline.steps.analysis_utils import normalize_surface, reconstruct_surface_from_analysis
from pipeline.steps.base import RefinementStep, TabletRow
from pipeline.steps.dulat_gate import DulatMorphGate

# Ordered from longest to shortest so greedy match captures full suffix
_SUFFIX_SEGMENTS = ("hm", "hn", "km", "kn", "ny", "nm", "nn", "h", "k", "n", "y")

# POS patterns that commonly carry suffixes
_SUFFIXABLE_POS_PREFIXES = {"n.", "adj.", "prep.", "adv.", "vb"}
_LEMMA_STYLE_RE = re.compile(r"^[A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]+(?:\([IVX]+\))?$")
_TOKEN_RE = re.compile(r"^(.*?)(?:\s*\(([IVX]+)\))?$")
_LEMMA_LETTER_RE = re.compile(r"[^A-Za-zˤʔḫṣṯẓġḏḥṭšʕʿảỉủ]")
_EXPLICIT_SUFFIX_NY_RE = re.compile(r",\s*-[ny](?:\s|\(|$)", re.IGNORECASE)


class SuffixCliticFixer(RefinementStep):
    """Inject '+' separator before pronominal suffix segments in analysis."""

    def __init__(self, gate: Optional[DulatMorphGate] = None) -> None:
        self._gate = gate

    @property
    def name(self) -> str:
        return "suffix-clitic"

    def refine_row(self, row: TabletRow) -> TabletRow:
        surface = row.surface.strip()
        analysis = row.analysis.strip()
        pos = row.pos.strip()
        if not surface or not analysis or not pos:
            return row

        # Check if surface ends with a known suffix segment
        matched_suffix = None
        for seg in _SUFFIX_SEGMENTS:
            if surface.endswith(seg) and len(surface) > len(seg):
                matched_suffix = seg
                break

        if not matched_suffix:
            return row

        variants = analysis.split(";")
        pos_variants = [v.strip() for v in pos.split(";")]
        dulat_variants = [v.strip() for v in row.dulat.split(";")]
        changed = False
        out = []

        for idx, var in enumerate(variants):
            variant = var.strip()
            pos_v = pos_variants[idx].strip() if idx < len(pos_variants) else ""
            dulat_tok = dulat_variants[idx].strip() if idx < len(dulat_variants) else ""

            new_variant = self._fix_variant(
                analysis_variant=variant,
                pos_variant=pos_v,
                dulat_token=dulat_tok,
                suffix=matched_suffix,
                surface=surface,
            )
            if new_variant != variant:
                changed = True
            out.append(new_variant)

        if not changed:
            return row

        return TabletRow(
            line_id=row.line_id,
            surface=row.surface,
            analysis=";".join(out),
            dulat=row.dulat,
            pos=row.pos,
            gloss=row.gloss,
            comment=row.comment,
        )

    def _fix_variant(
        self,
        analysis_variant: str,
        pos_variant: str,
        dulat_token: str,
        suffix: str,
        surface: str,
    ) -> str:
        normalized = self._normalize_existing_plus(
            analysis_variant=analysis_variant,
            dulat_token=dulat_token,
            suffix=suffix,
        )
        if normalized != analysis_variant:
            return normalized

        # Already has '+' — suffix already marked
        if "+" in normalized:
            return normalized

        # Must have noun-like/adjectival POS for suffix injection
        first_pos = pos_variant.split(",")[0].strip() if pos_variant else ""
        if not any(first_pos.startswith(p) for p in _SUFFIXABLE_POS_PREFIXES):
            return normalized

        # Require DULAT evidence that this token supports pronominal suffixes.
        if not self._is_suffix_dulat_token(dulat_token, surface):
            return normalized

        # Do not force + after enclitic marker.
        if "~" in normalized:
            return normalized

        # If lemma already ends with the same letter and DULAT does not
        # explicitly encode that suffixal reading for this variant, keep it as
        # lexeme-final letter (e.g., mṯn, lšn, klny).
        if self._should_keep_lexeme_terminal_letter(dulat_token=dulat_token, suffix=suffix):
            return normalized

        if not self._is_confident_suffix_variant(
            analysis_variant=normalized,
            surface=surface,
            suffix=suffix,
        ):
            return normalized

        return self._inject_suffix(normalized, suffix)

    def _is_confident_suffix_variant(
        self,
        analysis_variant: str,
        surface: str,
        suffix: str,
    ) -> bool:
        """Return True when suffix insertion is supported by variant/surface shape."""
        # Direct shape evidence in analysis string.
        core = analysis_variant.rstrip("/")
        if core.endswith(suffix):
            return True
        if re.match(r"^(.+?)" + re.escape(suffix) + r"(\([IVX]+\))?/$", analysis_variant):
            return True
        if (
            _LEMMA_STYLE_RE.match(analysis_variant)
            and "/" not in analysis_variant
            and "[" not in analysis_variant
        ):
            return True

        # Fallback: analysis reconstructs to the surface without suffix.
        surface_norm = normalize_surface(surface)
        if not surface_norm.endswith(suffix):
            return False
        base_surface = surface_norm[: -len(suffix)]
        analysis_surface = normalize_surface(reconstruct_surface_from_analysis(analysis_variant))
        return analysis_surface == base_surface

    def _inject_suffix(self, analysis_variant: str, suffix: str) -> str:
        """Try to inject '+' before the suffix in a single analysis variant."""
        # Analysis ends with suffix letters followed by optional closure
        # e.g., "npšh/" → "npš/+h"
        # e.g., "bth(II)/" → "bt(II)/+h"
        # Strip trailing closure markers
        core = analysis_variant.rstrip("/")

        if core.endswith(suffix):
            base = core[: -len(suffix)]
            # Re-add the '/' if the original had it
            if analysis_variant.endswith("/"):
                return base + "/+" + suffix
            else:
                return base + "+" + suffix

        # Check if it ends with suffix + homonym tag + /
        m = re.match(r"^(.+?)" + re.escape(suffix) + r"(\([IVX]+\))?/$", analysis_variant)
        if m:
            base = m.group(1)
            hom = m.group(2) or ""
            return base + hom + "/+" + suffix

        # Surface-form-specific fallback: if DULAT confirms this surface is a
        # suffixal form but the analysis is lemma-style (e.g., l(I), šmm(I)/),
        # append +suffix conservatively.
        return analysis_variant + "+" + suffix

    def _normalize_existing_plus(
        self,
        analysis_variant: str,
        dulat_token: str,
        suffix: str,
    ) -> str:
        """Revert known bad '+suffix' encodings."""
        v = analysis_variant

        # Enclitic marker uses "~x", not "~+x".
        if "~+" in v:
            v = v.replace("~+", "~")

        # For lexemes ending in n/y, avoid converting the final lexeme letter
        # into a synthetic suffix split unless DULAT explicitly marks it.
        if self._should_keep_lexeme_terminal_letter(dulat_token=dulat_token, suffix=suffix):
            if suffix in {"n", "y"}:
                v = v.replace(f"/+{suffix}", f"{suffix}/")

        # bʕd + enclitic n should be represented as ~n.
        if self._is_baad_enclitic_n(dulat_token=dulat_token) and "+n" in v:
            v = v.replace("+n", "~n")
            v = v.replace("~+n", "~n")

        return v

    def _should_keep_lexeme_terminal_letter(self, dulat_token: str, suffix: str) -> bool:
        if suffix not in {"n", "y"}:
            return False
        if _EXPLICIT_SUFFIX_NY_RE.search(dulat_token or ""):
            return False
        lemma_letters = self._declared_lemma_letters(dulat_token)
        if not lemma_letters:
            return False
        return lemma_letters.endswith(suffix)

    def _declared_lemma_letters(self, dulat_token: str) -> str:
        token = (dulat_token or "").strip()
        if not token or token.startswith("/"):
            return ""
        if "," in token:
            token = token.split(",", 1)[0].strip()
        m = _TOKEN_RE.match(token)
        lemma = (m.group(1) if m else token).strip()
        return _LEMMA_LETTER_RE.sub("", normalize_surface(lemma)).lower()

    def _is_baad_enclitic_n(self, dulat_token: str) -> bool:
        lemma_letters = self._declared_lemma_letters(dulat_token)
        return lemma_letters == normalize_surface("bʕd")

    def _is_suffix_dulat_token(self, token: str, surface: str) -> bool:
        if not token or token == "?":
            return False
        if self._gate is None:
            return False
        return self._gate.has_suffix_token(token, surface=surface)
