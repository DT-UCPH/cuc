"""Migrate reviewed tablet files to current TF-aligned token ids and conventions."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from reviewed_normalization import normalize_reviewed_analysis


@dataclass(frozen=True)
class TokenRow:
    token_id: str
    surface: str
    ref: str
    analysis: str
    dulat: str
    pos: str
    gloss: str
    comment: str


@dataclass(frozen=True)
class TokenGroup:
    token_id: str
    surface: str
    ref: str
    rows: tuple[TokenRow, ...]


class ReviewedTabletMigrator:
    """Rewrite reviewed tablets against the current TF raw token stream."""

    _EDITORIAL_CHANGE_COMMENT = "Token changed from previous version."
    _LEGACY_TOKENIZATION_COMMENT = "Migrated from legacy reviewed tokenization."

    def migrate(self, reviewed_path: Path, raw_path: Path, auto_path: Path) -> str:
        reviewed_groups = self._parse_reviewed_groups(reviewed_path)
        raw_groups = self._parse_raw_groups(raw_path)
        auto_groups = self._parse_reviewed_groups(auto_path)
        auto_by_id = {group.token_id: group for group in auto_groups}

        output_lines = ["id\tsurface form\tmorphological parsing\tDULAT\tPOS\tgloss\tcomments"]
        current_ref: str | None = None

        reviewed_seq = [self._normalize_surface(group.surface) for group in reviewed_groups]
        raw_seq = [self._normalize_surface(group.surface) for group in raw_groups]
        matcher = SequenceMatcher(a=reviewed_seq, b=raw_seq, autojunk=False)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for offset in range(i2 - i1):
                    reviewed_group = reviewed_groups[i1 + offset]
                    raw_group = raw_groups[j1 + offset]
                    auto_group = auto_by_id.get(raw_group.token_id)
                    if reviewed_group.surface != raw_group.surface:
                        if self._is_editorial_surface_change_only(
                            reviewed_group.surface, raw_group.surface
                        ):
                            emitted = self._preserve_reviewed_group(
                                reviewed_group,
                                raw_group,
                                extra_comment=self._EDITORIAL_CHANGE_COMMENT,
                            )
                        else:
                            emitted = self._fallback_group(raw_group, auto_group)
                    else:
                        emitted = self._migrate_aligned_group(reviewed_group, raw_group, auto_group)
                    current_ref = self._append_group(
                        output_lines, current_ref, raw_group.ref, emitted
                    )
                continue

            if self._is_simple_concatenation(reviewed_groups[i1:i2], raw_groups[j1:j2]):
                raw_group = raw_groups[j1]
                emitted = self._preserve_reviewed_groups(reviewed_groups[i1:i2], raw_group)
                current_ref = self._append_group(output_lines, current_ref, raw_group.ref, emitted)
                continue

            if self._is_simple_split(reviewed_groups[i1:i2], raw_groups[j1:j2]):
                reviewed_group = reviewed_groups[i1]
                for raw_group in raw_groups[j1:j2]:
                    emitted = self._preserve_reviewed_group(reviewed_group, raw_group)
                    current_ref = self._append_group(
                        output_lines, current_ref, raw_group.ref, emitted
                    )
                continue

            for raw_group in raw_groups[j1:j2]:
                auto_group = auto_by_id.get(raw_group.token_id)
                emitted = self._fallback_group(raw_group, auto_group)
                current_ref = self._append_group(output_lines, current_ref, raw_group.ref, emitted)

        return "\n".join(output_lines) + "\n"

    def _migrate_aligned_group(
        self,
        reviewed_group: TokenGroup,
        raw_group: TokenGroup,
        auto_group: TokenGroup | None,
    ) -> TokenGroup:
        auto_rows = list(auto_group.rows) if auto_group is not None else []
        refreshed_rows: list[TokenRow] = []
        seen: set[tuple[str, str, str, str, str]] = set()

        for row in reviewed_group.rows:
            pos, gloss = self._refresh_pos_gloss(row, auto_rows)
            refreshed = TokenRow(
                token_id=raw_group.token_id,
                surface=raw_group.surface,
                ref=raw_group.ref,
                analysis=row.analysis,
                dulat=row.dulat,
                pos=pos,
                gloss=gloss,
                comment=row.comment,
            )
            marker = (
                refreshed.analysis,
                refreshed.dulat,
                refreshed.pos,
                refreshed.gloss,
                refreshed.comment,
            )
            if marker in seen:
                continue
            seen.add(marker)
            refreshed_rows.append(refreshed)

        return TokenGroup(
            token_id=raw_group.token_id,
            surface=raw_group.surface,
            ref=raw_group.ref,
            rows=tuple(refreshed_rows),
        )

    def _preserve_reviewed_group(
        self,
        reviewed_group: TokenGroup,
        raw_group: TokenGroup,
        extra_comment: str | None = None,
    ) -> TokenGroup:
        return TokenGroup(
            token_id=raw_group.token_id,
            surface=raw_group.surface,
            ref=raw_group.ref,
            rows=tuple(
                TokenRow(
                    token_id=raw_group.token_id,
                    surface=raw_group.surface,
                    ref=raw_group.ref,
                    analysis=row.analysis,
                    dulat=row.dulat,
                    pos=row.pos,
                    gloss=row.gloss,
                    comment=self._append_comment(row.comment, extra_comment)
                    if extra_comment
                    else row.comment,
                )
                for row in reviewed_group.rows
            ),
        )

    def _preserve_reviewed_groups(
        self,
        reviewed_groups: list[TokenGroup],
        raw_group: TokenGroup,
        extra_comment: str | None = None,
    ) -> TokenGroup:
        preserved_rows: list[TokenRow] = []
        for reviewed_group in reviewed_groups:
            for row in reviewed_group.rows:
                preserved_rows.append(
                    TokenRow(
                        token_id=raw_group.token_id,
                        surface=raw_group.surface,
                        ref=raw_group.ref,
                        analysis=row.analysis,
                        dulat=row.dulat,
                        pos=row.pos,
                        gloss=row.gloss,
                        comment=self._append_comment(row.comment, extra_comment)
                        if extra_comment
                        else row.comment,
                    )
                )
        return TokenGroup(
            token_id=raw_group.token_id,
            surface=raw_group.surface,
            ref=raw_group.ref,
            rows=tuple(preserved_rows),
        )

    def _fallback_group(self, raw_group: TokenGroup, auto_group: TokenGroup | None) -> TokenGroup:
        source_rows = list(auto_group.rows) if auto_group is not None else list(raw_group.rows)
        migrated_rows: list[TokenRow] = []
        for row in source_rows:
            comment = self._append_comment(row.comment, self._LEGACY_TOKENIZATION_COMMENT)
            migrated_rows.append(
                TokenRow(
                    token_id=raw_group.token_id,
                    surface=raw_group.surface,
                    ref=raw_group.ref,
                    analysis=row.analysis,
                    dulat=row.dulat,
                    pos=row.pos,
                    gloss=row.gloss,
                    comment=comment,
                )
            )
        return TokenGroup(
            token_id=raw_group.token_id,
            surface=raw_group.surface,
            ref=raw_group.ref,
            rows=tuple(migrated_rows),
        )

    def _refresh_pos_gloss(
        self, reviewed_row: TokenRow, auto_rows: list[TokenRow]
    ) -> tuple[str, str]:
        exact = [
            row
            for row in auto_rows
            if row.analysis == reviewed_row.analysis and row.dulat == reviewed_row.dulat
        ]
        if len(exact) == 1:
            return exact[0].pos, exact[0].gloss

        same_dulat = [row for row in auto_rows if row.dulat == reviewed_row.dulat and row.dulat]
        if len(same_dulat) == 1:
            return same_dulat[0].pos, same_dulat[0].gloss

        return reviewed_row.pos, reviewed_row.gloss

    @staticmethod
    def _append_group(
        output_lines: list[str],
        current_ref: str | None,
        ref: str,
        group: TokenGroup,
    ) -> str:
        if ref != current_ref:
            output_lines.append(f"# {ref}\t\t\t\t\t\t")
        for row in group.rows:
            output_lines.append(
                "\t".join(
                    [
                        row.token_id,
                        row.surface,
                        row.analysis,
                        row.dulat,
                        row.pos,
                        row.gloss,
                        row.comment,
                    ]
                )
            )
        return ref

    @staticmethod
    def _append_comment(existing: str, extra: str) -> str:
        if not existing:
            return extra
        if extra in existing:
            return existing
        return f"{existing} | {extra}"

    def _is_simple_concatenation(
        self, reviewed_groups: list[TokenGroup], raw_groups: list[TokenGroup]
    ) -> bool:
        if len(reviewed_groups) < 2 or len(raw_groups) != 1:
            return False
        concatenated_reviewed = "".join(
            self._normalize_surface(group.surface) for group in reviewed_groups
        )
        raw_surface = self._normalize_surface(raw_groups[0].surface)
        return concatenated_reviewed == raw_surface

    def _is_simple_split(
        self, reviewed_groups: list[TokenGroup], raw_groups: list[TokenGroup]
    ) -> bool:
        if len(reviewed_groups) != 1 or len(raw_groups) < 2:
            return False
        reviewed_surface = self._normalize_surface(reviewed_groups[0].surface)
        concatenated_raw = "".join(self._normalize_surface(group.surface) for group in raw_groups)
        return reviewed_surface == concatenated_raw

    def _is_editorial_surface_change_only(self, reviewed_surface: str, raw_surface: str) -> bool:
        if reviewed_surface == raw_surface:
            return False
        return self._strip_editorial_marks(reviewed_surface) == self._strip_editorial_marks(
            raw_surface
        )

    @staticmethod
    def _strip_editorial_marks(surface: str) -> str:
        normalized = surface.replace("ˤ", "ʿ").replace("bˤl", "bʿl")
        return normalized.replace("<", "").replace(">", "").replace("x", "").replace(" ", "")

    @staticmethod
    def _normalize_surface(surface: str) -> str:
        normalized = surface.replace("ˤ", "ʿ").replace("bˤl", "bʿl")
        replacements = {
            "pdr<y>": "pdry",
            "xxht": "xht",
            "w  tʿn": "wtʿn",
            "kṯ<r>": "kṯr",
            "hkm": "ḥkm",
            "ṯlḥ<t>": "ṯlḥnt",
        }
        return replacements.get(normalized, normalized)

    @staticmethod
    def _parse_reviewed_groups(path: Path) -> list[TokenGroup]:
        groups: list[TokenGroup] = []
        ref = ""
        rows_by_key: list[TokenRow] = []
        current_key: tuple[str, str, str] | None = None

        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# KTU "):
                if current_key is not None:
                    token_id, surface, token_ref = current_key
                    groups.append(
                        TokenGroup(
                            token_id=token_id,
                            surface=surface,
                            ref=token_ref,
                            rows=tuple(rows_by_key),
                        )
                    )
                    rows_by_key = []
                    current_key = None
                ref = line[2:].split("\t")[0]
                continue
            if not line.strip() or line.startswith("id\t"):
                continue
            parts = line.split("\t")
            if len(parts) < 7:
                parts += [""] * (7 - len(parts))
            elif len(parts) > 7:
                parts = parts[:6] + ["\t".join(parts[6:])]
            parts = ReviewedTabletMigrator._split_inline_analysis_comment(parts)
            token_id, surface = parts[0], parts[1]
            key = (token_id, surface, ref)
            if current_key is not None and key != current_key:
                prev_id, prev_surface, prev_ref = current_key
                groups.append(
                    TokenGroup(
                        token_id=prev_id,
                        surface=prev_surface,
                        ref=prev_ref,
                        rows=tuple(rows_by_key),
                    )
                )
                rows_by_key = []
            current_key = key
            rows_by_key.append(
                TokenRow(
                    token_id=token_id,
                    surface=surface,
                    ref=ref,
                    analysis=normalize_reviewed_analysis(parts[2]),
                    dulat=parts[3],
                    pos=parts[4],
                    gloss=parts[5],
                    comment=parts[6],
                )
            )

        if current_key is not None:
            token_id, surface, token_ref = current_key
            groups.append(
                TokenGroup(
                    token_id=token_id, surface=surface, ref=token_ref, rows=tuple(rows_by_key)
                )
            )

        return groups

    @staticmethod
    def _split_inline_analysis_comment(parts: list[str]) -> list[str]:
        analysis = parts[2]
        if " # " not in analysis:
            return parts
        stripped_analysis, inline_comment = analysis.split(" # ", 1)
        stripped_analysis = stripped_analysis.rstrip()
        inline_comment = inline_comment.strip()
        if not inline_comment:
            parts[2] = stripped_analysis
            return parts
        parts[2] = stripped_analysis
        parts[6] = inline_comment if not parts[6] else f"{inline_comment} | {parts[6]}"
        return parts

    @staticmethod
    def _parse_raw_groups(path: Path) -> list[TokenGroup]:
        groups: list[TokenGroup] = []
        ref = ""
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("#---------------------------- "):
                ref = line.split("#---------------------------- ", 1)[1]
                continue
            if not line.strip():
                continue
            token_id, surface, _placeholder = line.split("\t")
            groups.append(
                TokenGroup(
                    token_id=token_id,
                    surface=surface.replace("ʿ", "ˤ").replace("bʿl", "bˤl"),
                    ref=ref,
                    rows=(
                        TokenRow(
                            token_id=token_id,
                            surface=surface.replace("ʿ", "ˤ").replace("bʿl", "bˤl"),
                            ref=ref,
                            analysis="?",
                            dulat="?",
                            pos="?",
                            gloss="?",
                            comment="DULAT: NOT FOUND",
                        ),
                    ),
                )
            )
        return groups
