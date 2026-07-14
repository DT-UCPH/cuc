"""Load reviewed-tablet morphology TSVs and resolve reviewed/auto file pairs."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from reviewed_normalization import normalize_reviewed_analysis

from .models import EvaluationPair, MorphologyDataset, MorphologyToken


class MorphologyTsvLoader:
    """Load morphology analyses from reviewed-style TSV files."""

    def load(self, path: Path) -> MorphologyDataset:
        current_ref = ""
        analyses_by_id: dict[str, set[str]] = defaultdict(set)
        surface_by_id: dict[str, str] = {}
        ref_by_id: dict[str, str] = {}

        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.rstrip("\n")
            if line.startswith("# KTU "):
                current_ref = line[2:].split("\t")[0]
                continue
            if not line.strip() or line.startswith("id\t"):
                continue

            parts = self._normalize_parts(line)

            token_id = parts[0].strip()
            surface = parts[1].strip()
            analysis = normalize_reviewed_analysis(parts[2])
            if not token_id:
                continue
            self._validate_group_identity(
                token_id=token_id,
                surface=surface,
                ref=current_ref,
                surface_by_id=surface_by_id,
                ref_by_id=ref_by_id,
                source=path,
            )
            if analysis:
                analyses_by_id[token_id].add(analysis)

        tokens_by_id = {
            token_id: MorphologyToken(
                token_id=token_id,
                surface=surface_by_id[token_id],
                ref=ref_by_id[token_id],
                analyses=frozenset(analyses_by_id.get(token_id, set())),
            )
            for token_id in sorted(surface_by_id, key=_token_sort_key)
        }
        return MorphologyDataset(
            label=path.name,
            source_path=path,
            tokens_by_id=tokens_by_id,
        )

    @staticmethod
    def empty(label: str) -> MorphologyDataset:
        return MorphologyDataset(label=label, source_path=None, tokens_by_id={})

    @staticmethod
    def _normalize_parts(line: str) -> list[str]:
        parts = line.split("\t")
        if len(parts) < 7:
            parts += [""] * (7 - len(parts))
        elif len(parts) > 7:
            parts = parts[:6] + ["\t".join(parts[6:])]

        if _looks_like_collapsed_surface_analysis(parts):
            surface, analysis = parts[1].rsplit(" ", 1)
            parts = [
                parts[0],
                surface,
                analysis,
                parts[2],
                parts[3],
                parts[4],
                parts[5] if len(parts) > 5 else "",
            ]
        parts = _split_inline_analysis_comment(parts)
        return parts

    @staticmethod
    def _validate_group_identity(
        *,
        token_id: str,
        surface: str,
        ref: str,
        surface_by_id: dict[str, str],
        ref_by_id: dict[str, str],
        source: Path,
    ) -> None:
        existing_surface = surface_by_id.get(token_id)
        if existing_surface is not None and existing_surface != surface:
            raise ValueError(
                f"Token id {token_id} in {source} has conflicting surfaces: "
                f"{existing_surface!r} vs {surface!r}"
            )
        existing_ref = ref_by_id.get(token_id)
        if existing_ref is not None and ref and existing_ref != ref:
            raise ValueError(
                f"Token id {token_id} in {source} has conflicting refs: {existing_ref!r} vs {ref!r}"
            )
        surface_by_id.setdefault(token_id, surface)
        ref_by_id.setdefault(token_id, ref)


class EvaluationTargetResolver:
    """Resolve reviewed/auto file pairs, using `reviewed/` as the gold root."""

    def resolve(
        self,
        reviewed_path: Path,
        auto_path: Path | None,
    ) -> list[EvaluationPair]:
        if reviewed_path.is_file():
            return [self._resolve_single_file(reviewed_path, auto_path)]

        if not reviewed_path.is_dir():
            raise FileNotFoundError(f"Reviewed path not found: {reviewed_path}")

        if auto_path is not None and auto_path.is_file():
            raise ValueError("Auto path must be a directory when reviewed path is a directory.")

        pairs: list[EvaluationPair] = []
        for path in self._reviewed_files(reviewed_path):
            pairs.append(
                EvaluationPair(
                    label=path.name,
                    reviewed_path=path,
                    auto_path=self._resolve_auto_match(
                        reviewed_path=path,
                        auto_path=auto_path,
                    ),
                )
            )
        return pairs

    def _resolve_single_file(
        self,
        reviewed_path: Path,
        auto_path: Path | None,
    ) -> EvaluationPair:
        if auto_path is None:
            return EvaluationPair(
                label=reviewed_path.name,
                reviewed_path=reviewed_path,
                auto_path=None,
            )
        if auto_path.is_dir():
            return EvaluationPair(
                label=reviewed_path.name,
                reviewed_path=reviewed_path,
                auto_path=self._resolve_auto_match(
                    reviewed_path=reviewed_path,
                    auto_path=auto_path,
                ),
            )
        return EvaluationPair(
            label=reviewed_path.name,
            reviewed_path=reviewed_path,
            auto_path=auto_path,
        )

    @staticmethod
    def _reviewed_files(reviewed_dir: Path) -> list[Path]:
        supported_files: list[Path] = []
        for extension in (".tsv", ".txt"):
            supported_files.extend(reviewed_dir.glob(f"*{extension}"))
        return sorted(supported_files, key=lambda item: item.name)

    @staticmethod
    def _resolve_auto_match(reviewed_path: Path, auto_path: Path | None) -> Path | None:
        if auto_path is None:
            return None
        for candidate in _candidate_auto_paths(reviewed_path, auto_path):
            if candidate.exists():
                return candidate
        return None


def _candidate_auto_paths(reviewed_path: Path, auto_dir: Path) -> tuple[Path, ...]:
    exact_name = auto_dir / reviewed_path.name
    if reviewed_path.suffix == ".tsv":
        return (exact_name,)
    return (
        exact_name,
        auto_dir / f"{reviewed_path.stem}.tsv",
    )


def _looks_like_collapsed_surface_analysis(parts: list[str]) -> bool:
    if len(parts) < 5 or " " not in parts[1]:
        return False
    if not parts[2].startswith("/") or not parts[2].endswith("/"):
        return False
    _, trailing = parts[1].rsplit(" ", 1)
    return bool(trailing) and "/" not in trailing


def _token_sort_key(token_id: str) -> tuple[int, object]:
    return (0, int(token_id)) if token_id.isdigit() else (1, token_id)


_INLINE_ANALYSIS_COMMENT_RE = re.compile(r"^(?P<analysis>.+?)\s+#\s*(?P<comment>.+)$")


def _split_inline_analysis_comment(parts: list[str]) -> list[str]:
    analysis = parts[2]
    match = _INLINE_ANALYSIS_COMMENT_RE.match(analysis)
    if match is None:
        return parts
    stripped_analysis = match.group("analysis").rstrip()
    inline_comment = match.group("comment").strip()
    if not inline_comment:
        parts[2] = stripped_analysis
        return parts
    parts[2] = stripped_analysis
    parts[6] = inline_comment if not parts[6] else f"{inline_comment} | {parts[6]}"
    return parts
