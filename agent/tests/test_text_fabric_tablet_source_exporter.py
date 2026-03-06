from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from text_fabric.tablet_source_exporter import TextFabricTabletSourceExporter


class _FakeOtypeFeature:
    def __init__(self, words: list[int]) -> None:
        self._words = words

    def s(self, node_type: str) -> list[int]:
        if node_type != "word":
            raise AssertionError(f"Unexpected node type: {node_type}")
        return list(self._words)


class _FakeValueFeature:
    def __init__(self, values: dict[int, str]) -> None:
        self._values = values

    def v(self, node: int) -> str:
        return self._values[node]


class _FakeF:
    def __init__(self, words: list[int], g_cons: dict[int, str]) -> None:
        self.otype = _FakeOtypeFeature(words)
        self.g_cons = _FakeValueFeature(g_cons)


class _FakeT:
    def __init__(self, sections: dict[int, tuple[str, str, int]]) -> None:
        self._sections = sections

    def sectionFromNode(self, node: int) -> tuple[str, str, int]:
        return self._sections[node]


class _FakeApi:
    def __init__(
        self, words: list[int], g_cons: dict[int, str], sections: dict[int, tuple[str, str, int]]
    ) -> None:
        self.F = _FakeF(words, g_cons)
        self.T = _FakeT(sections)


class TextFabricTabletSourceExporterTest(unittest.TestCase):
    def test_latest_version_uses_highest_semver_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            tf_root = root / "tf"
            (tf_root / "0.2.5").mkdir(parents=True)
            (tf_root / "0.10.0").mkdir(parents=True)
            (tf_root / "0.2.6").mkdir(parents=True)

            exporter = TextFabricTabletSourceExporter(repo_root=root, tf_root=tf_root)

            self.assertEqual(exporter.latest_version(), "0.10.0")

    def test_export_latest_writes_canonical_cuc_tablet_tsv_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            tf_root = root / "tf"
            (tf_root / "0.2.6").mkdir(parents=True)
            generated_root = root / "agent" / "generated_sources"
            api = _FakeApi(
                words=[136937, 136938, 136940, 136941, 200001],
                g_cons={
                    136937: "al",
                    136938: "tġl",
                    136940: "p",
                    136941: "bn",
                    200001: "ilm",
                },
                sections={
                    136937: ("KTU 1.3", "I", 1),
                    136938: ("KTU 1.3", "I", 1),
                    136940: ("KTU 1.3", "I", 2),
                    136941: ("KTU 1.3", "II", 1),
                    200001: ("KTU 1.4", "II", 3),
                },
            )

            exporter = TextFabricTabletSourceExporter(
                repo_root=root,
                tf_root=tf_root,
                generated_root=generated_root,
                loader=lambda _repo_root, _version: api,
            )

            summary = exporter.export_latest()

            self.assertEqual(summary.tf_version, "0.2.6")
            self.assertEqual(summary.file_count, 2)
            self.assertEqual(summary.token_count, 5)
            self.assertEqual(
                summary.output_dir,
                (generated_root / "cuc_tablets_tsv" / "0.2.6").resolve(),
            )
            self.assertEqual(
                (summary.output_dir / "KTU 1.3.tsv").read_text(encoding="utf-8"),
                "#---------------------------- KTU 1.3 I:1\n"
                "136937\tal\tal\n"
                "136938\ttġl\ttġl\n"
                "#---------------------------- KTU 1.3 I:2\n"
                "136940\tp\tp\n"
                "#---------------------------- KTU 1.3 II:1\n"
                "136941\tbn\tbn\n",
            )
            self.assertEqual(
                (summary.output_dir / "KTU 1.4.tsv").read_text(encoding="utf-8"),
                "#---------------------------- KTU 1.4 II:3\n200001\tilm\tilm\n",
            )

    def test_export_omits_column_i_for_single_column_tablet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            tf_root = root / "tf"
            (tf_root / "0.2.6").mkdir(parents=True)
            generated_root = root / "agent" / "generated_sources"
            api = _FakeApi(
                words=[157900, 157901],
                g_cons={
                    157900: "rb",
                    157901: "rb",
                },
                sections={
                    157900: ("KTU 2.38", "I", 27),
                    157901: ("KTU 2.38", "I", 27),
                },
            )

            exporter = TextFabricTabletSourceExporter(
                repo_root=root,
                tf_root=tf_root,
                generated_root=generated_root,
                loader=lambda _repo_root, _version: api,
            )

            summary = exporter.export_latest()

            self.assertEqual(
                (summary.output_dir / "KTU 2.38.tsv").read_text(encoding="utf-8"),
                "#---------------------------- KTU 2.38 27\n157900\trb\trb\n157901\trb\trb\n",
            )


if __name__ == "__main__":
    unittest.main()
