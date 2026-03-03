"""Export canonical raw tablet TSV files from Text-Fabric data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class ExportSummary:
    """Summary for a raw tablet source export run."""

    tf_version: str
    output_dir: Path
    file_count: int
    token_count: int


class TextFabricTabletSourceExporter:
    """Generate raw `cuc_tablets_tsv` files from a Text-Fabric corpus."""

    def __init__(
        self,
        repo_root: Path,
        tf_root: Path | None = None,
        generated_root: Path | None = None,
        loader: Callable[[Path, str], object] | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.tf_root = (tf_root or (self.repo_root / "tf")).resolve()
        self.generated_root = (
            generated_root or (self.repo_root / "agent" / "generated_sources")
        ).resolve()
        self._loader = loader or self._default_loader

    def available_versions(self) -> list[str]:
        if not self.tf_root.exists():
            return []
        return [
            path.name
            for path in sorted(self.tf_root.iterdir(), key=_version_sort_key)
            if path.is_dir()
        ]

    def latest_version(self) -> str:
        versions = self.available_versions()
        if not versions:
            raise FileNotFoundError(f"No Text-Fabric versions found under {self.tf_root}")
        return versions[-1]

    def output_dir_for_version(self, version: str) -> Path:
        return self.generated_root / "cuc_tablets_tsv" / version

    def export_latest(self, clean: bool = True) -> ExportSummary:
        return self.export(version=self.latest_version(), clean=clean)

    def export(
        self,
        version: str | None = None,
        out_dir: Path | None = None,
        clean: bool = True,
    ) -> ExportSummary:
        tf_version = version or self.latest_version()
        output_dir = (out_dir or self.output_dir_for_version(tf_version)).resolve()
        api = self._loader(self.repo_root, tf_version)
        tablet_rows = self._collect_tablet_rows(api)

        output_dir.mkdir(parents=True, exist_ok=True)
        if clean:
            for existing in output_dir.glob("*.tsv"):
                existing.unlink()

        file_count = 0
        token_count = 0
        for tablet_name, rows in tablet_rows.items():
            (output_dir / f"{tablet_name}.tsv").write_text("".join(rows), encoding="utf-8")
            file_count += 1
            token_count += sum(1 for row in rows if not row.startswith("#"))

        return ExportSummary(
            tf_version=tf_version,
            output_dir=output_dir,
            file_count=file_count,
            token_count=token_count,
        )

    def _default_loader(self, repo_root: Path, version: str) -> object:
        from tf.fabric import Fabric

        tf = Fabric(locations=str(repo_root), modules=f"tf/{version}")
        return tf.load("g_cons tablet column line")

    def _collect_tablet_rows(self, api: object) -> dict[str, list[str]]:
        F = api.F
        T = api.T
        rows_by_tablet: dict[str, list[str]] = {}
        last_ref_by_tablet: dict[str, str] = {}

        for word in F.otype.s("word"):
            section = T.sectionFromNode(word)
            if not section or len(section) < 3:
                continue
            tablet_name, column, line = section[:3]
            surface = str(F.g_cons.v(word) or "")
            reference = self._format_reference(tablet_name, column, line)

            tablet_rows = rows_by_tablet.setdefault(tablet_name, [])
            if last_ref_by_tablet.get(tablet_name) != reference:
                tablet_rows.append(f"#---------------------------- {reference}\n")
                last_ref_by_tablet[tablet_name] = reference
            tablet_rows.append(f"{word}\t{surface}\t{surface}\n")

        return rows_by_tablet

    @staticmethod
    def _format_reference(tablet_name: str, column: object, line: object) -> str:
        column_text = str(column).strip() if column is not None else ""
        line_text = str(line).strip() if line is not None else ""
        if column_text and line_text:
            return f"{tablet_name} {column_text}:{line_text}"
        if line_text:
            return f"{tablet_name} {line_text}"
        return str(tablet_name)


def ensure_generated_cuc_tablet_sources(paths: object, source_dir: Path) -> ExportSummary | None:
    """Refresh generated raw tablet TSVs when the requested source dir is TF-backed."""

    requested_dir = source_dir.expanduser().resolve()
    if not paths.is_generated_source_dir(requested_dir):
        return None

    exporter = TextFabricTabletSourceExporter(
        repo_root=paths.repo_root,
        tf_root=paths.tf_root_dir,
        generated_root=paths.generated_sources_dir,
    )
    version = paths.generated_source_version(requested_dir) or exporter.latest_version()
    return exporter.export(version=version, out_dir=requested_dir)


def _version_sort_key(path: Path) -> tuple[int, ...]:
    parts: list[int] = []
    for token in path.name.split("."):
        try:
            parts.append(int(token))
        except ValueError:
            parts.append(-1)
    return tuple(parts)
