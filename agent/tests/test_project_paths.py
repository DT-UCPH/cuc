"""Tests for migrated project path resolution."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from project_paths import ProjectPaths


class ProjectPathsTest(unittest.TestCase):
    def _make_agent_root(self, base: Path) -> Path:
        agent_root = base / "agent"
        (agent_root / "pipeline").mkdir(parents=True, exist_ok=True)
        (agent_root / "pyproject.toml").write_text("[project]\nname='test'\n", encoding="utf-8")
        return agent_root

    def test_prefers_local_sqlite_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            agent_root = self._make_agent_root(Path(tmp_dir))
            local_dir = agent_root / "local_sources"
            data_dir = agent_root / "data_sources"
            local_dir.mkdir()
            data_dir.mkdir()
            (data_dir / "dulat_cache.sqlite").write_text("data", encoding="utf-8")
            (local_dir / "dulat_cache.sqlite").write_text("local", encoding="utf-8")

            paths = ProjectPaths(anchor=agent_root)

            self.assertEqual(paths.default_dulat_db(), local_dir / "dulat_cache.sqlite")

    def test_uses_latest_auto_parsing_version_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            agent_root = self._make_agent_root(Path(tmp_dir))
            auto_root = agent_root.parent / "auto_parsing"
            (auto_root / "0.2.5").mkdir(parents=True)
            (auto_root / "0.2.6").mkdir(parents=True)
            (auto_root / "0.10.0").mkdir(parents=True)

            paths = ProjectPaths(anchor=agent_root)

            self.assertEqual(paths.default_output_dir(), auto_root / "0.10.0")

    def test_default_source_dir_uses_latest_text_fabric_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            agent_root = self._make_agent_root(Path(tmp_dir))
            tf_root = agent_root.parent / "tf"
            (tf_root / "0.2.5").mkdir(parents=True)
            (tf_root / "0.2.6").mkdir(parents=True)

            paths = ProjectPaths(anchor=agent_root)

            self.assertEqual(
                paths.default_source_dir(),
                agent_root / "generated_sources" / "cuc_tablets_tsv" / "0.2.6",
            )

    def test_env_override_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            agent_root = self._make_agent_root(Path(tmp_dir))
            override = Path(tmp_dir) / "override.sqlite"
            override.write_text("db", encoding="utf-8")
            previous = os.environ.get("CUC_DULAT_DB")
            os.environ["CUC_DULAT_DB"] = str(override)
            try:
                paths = ProjectPaths(anchor=agent_root)
                self.assertEqual(paths.default_dulat_db(), override.resolve())
            finally:
                if previous is None:
                    os.environ.pop("CUC_DULAT_DB", None)
                else:
                    os.environ["CUC_DULAT_DB"] = previous


if __name__ == "__main__":
    unittest.main()
