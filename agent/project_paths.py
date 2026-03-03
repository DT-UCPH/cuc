"""Shared path resolution for the migrated morphology tooling."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


class ProjectPaths:
    """Resolve agent-local and repo-level paths in the migrated layout."""

    def __init__(self, anchor: Path | None = None) -> None:
        self.agent_root = self._resolve_agent_root(anchor or Path(__file__).resolve())
        self.repo_root = self.agent_root.parent
        self.data_sources_dir = self.agent_root / "data_sources"
        self.local_sources_dir = self.agent_root / "local_sources"
        self.generated_sources_dir = self.agent_root / "generated_sources"
        self.reports_dir = self.agent_root / "reports"
        self.tf_root_dir = self.repo_root / "tf"

    def default_dulat_db(self) -> Path:
        return self._env_or_candidates(
            "CUC_DULAT_DB",
            [
                self.local_sources_dir / "dulat_cache.sqlite",
                self.data_sources_dir / "dulat_cache.sqlite",
                self.repo_root / "sources" / "dulat_cache.sqlite",
            ],
        )

    def default_udb_db(self) -> Path:
        return self._env_or_candidates(
            "CUC_UDB_DB",
            [
                self.local_sources_dir / "udb_cache.sqlite",
                self.data_sources_dir / "udb_cache.sqlite",
                self.repo_root / "sources" / "udb_cache.sqlite",
            ],
        )

    def default_modules_db(self) -> Path:
        return self._env_or_candidates(
            "CUC_MODULES_DB",
            [
                self.local_sources_dir / "modules_cache.sqlite",
                self.data_sources_dir / "modules_cache.sqlite",
                self.repo_root / "sources" / "modules_cache.sqlite",
            ],
        )

    def default_notarius_html(self) -> Path:
        return self._env_or_candidates(
            "CUC_NOTARIUS_HTML",
            [
                self.local_sources_dir / "notarius.compact.html",
                self.data_sources_dir / "notarius.compact.html",
                self.repo_root / "sources" / "notarius.compact.html",
            ],
        )

    def default_notarius_evidence_claims(self) -> Path:
        return self._env_or_candidates(
            "CUC_NOTARIUS_EVIDENCE_CLAIMS",
            [
                self.local_sources_dir / "notarius_evidence_claims.json",
                self.data_sources_dir / "notarius_evidence_claims.json",
                self.repo_root / "sources" / "notarius_evidence_claims.json",
            ],
        )

    def default_notarius_evidence_context(self) -> Path:
        return self._env_or_candidates(
            "CUC_NOTARIUS_EVIDENCE_CONTEXT",
            [
                self.local_sources_dir / "notarius_evidence_context.json",
                self.data_sources_dir / "notarius_evidence_context.json",
                self.repo_root / "sources" / "notarius_evidence_context.json",
            ],
        )

    def latest_tf_version(self) -> str:
        versions = (
            sorted(
                [path for path in self.tf_root_dir.iterdir() if path.is_dir()],
                key=_version_sort_key,
            )
            if self.tf_root_dir.exists()
            else []
        )
        if not versions:
            raise FileNotFoundError(f"No Text-Fabric versions found under {self.tf_root_dir}")
        return versions[-1].name

    def default_source_dir(self) -> Path:
        env_value = os.environ.get("CUC_SOURCE_DIR", "").strip()
        if env_value:
            return Path(env_value).expanduser().resolve()
        return self.generated_sources_dir / "cuc_tablets_tsv" / self.latest_tf_version()

    def is_generated_source_dir(self, path: Path) -> bool:
        resolved = path.expanduser().resolve()
        generated_root = (self.generated_sources_dir / "cuc_tablets_tsv").resolve()
        return _is_relative_to(resolved, generated_root)

    def generated_source_version(self, path: Path) -> str | None:
        resolved = path.expanduser().resolve()
        generated_root = (self.generated_sources_dir / "cuc_tablets_tsv").resolve()
        if not _is_relative_to(resolved, generated_root):
            return None
        relative = resolved.relative_to(generated_root)
        if not relative.parts:
            return None
        version = relative.parts[0]
        candidate = self.tf_root_dir / version
        return version if candidate.exists() else None

    def default_output_dir(self) -> Path:
        env_value = os.environ.get("CUC_OUTPUT_DIR", "").strip()
        if env_value:
            return Path(env_value).expanduser().resolve()

        auto_root = self.repo_root / "auto_parsing"
        versioned_dirs = (
            sorted(
                [path for path in auto_root.iterdir() if path.is_dir()],
                key=_version_sort_key,
            )
            if auto_root.exists()
            else []
        )
        if versioned_dirs:
            return versioned_dirs[-1]

        legacy_out = self.repo_root / "out"
        if legacy_out.exists():
            return legacy_out

        return auto_root / "current"

    def default_reports_dir(self) -> Path:
        env_value = os.environ.get("CUC_REPORTS_DIR", "").strip()
        if env_value:
            return Path(env_value).expanduser().resolve()
        legacy_reports = self.repo_root / "reports"
        if legacy_reports.exists() and not self.reports_dir.exists():
            return legacy_reports
        return self.reports_dir

    def default_token_ref_glob(self) -> str:
        return str(self.default_output_dir() / "KTU 1.*.tsv")

    @staticmethod
    def _resolve_agent_root(anchor: Path) -> Path:
        current = anchor if anchor.is_dir() else anchor.parent
        for candidate in [current, *current.parents]:
            if (candidate / "pyproject.toml").exists() and (candidate / "pipeline").exists():
                return candidate
        raise RuntimeError(f"Could not locate agent root from {anchor}")

    @staticmethod
    def _first_existing(paths: Iterable[Path]) -> Path | None:
        for path in paths:
            if path.exists():
                return path
        return None

    def _env_or_candidates(self, env_key: str, candidates: list[Path]) -> Path:
        env_value = os.environ.get(env_key, "").strip()
        if env_value:
            return Path(env_value).expanduser().resolve()
        existing = self._first_existing(candidates)
        if existing is not None:
            return existing
        return candidates[0]


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _version_sort_key(path: Path) -> tuple[int, ...]:
    parts: list[int] = []
    for token in path.name.split("."):
        try:
            parts.append(int(token))
        except ValueError:
            parts.append(-1)
    return tuple(parts)


def get_project_paths(anchor: Path | None = None) -> ProjectPaths:
    """Return a shared resolver rooted at the agent directory."""
    return ProjectPaths(anchor=anchor)
