"""Migrate reviewed tablet files to current TF-aligned token ids and conventions."""

from __future__ import annotations

import re
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
    sign_span: str = ""


@dataclass(frozen=True)
class TokenGroup:
    token_id: str
    surface: str
    ref: str
    rows: tuple[TokenRow, ...]
    sign_span: str = ""


class ReviewedTabletMigrator:
    """Rewrite reviewed tablets against the current TF raw token stream."""

    _EDITORIAL_CHANGE_COMMENT = "Token changed from previous version."
    _LEGACY_TOKENIZATION_COMMENT = "Migrated from legacy reviewed tokenization."

    def migrate(self, reviewed_path: Path, raw_path: Path, auto_path: Path) -> str:
        include_sign_span = self._has_sign_span_column(reviewed_path)
        reviewed_groups = self._parse_reviewed_groups(reviewed_path)
        raw_groups = self._parse_raw_groups(raw_path)
        raw_groups = self._limit_raw_groups_to_reviewed_refs(reviewed_groups, raw_groups)
        auto_groups = self._parse_reviewed_groups(auto_path)
        auto_by_id = {group.token_id: group for group in auto_groups}

        header_columns = ["id", "surface form"]
        if include_sign_span:
            header_columns.append("sign span")
        header_columns.extend(["morphological parsing", "DULAT", "POS", "gloss", "comments"])
        output_lines = ["\t".join(header_columns)]
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
                        emitted = self._migrate_aligned_group(reviewed_group, raw_group)
                    current_ref = self._append_group(
                        output_lines,
                        current_ref,
                        raw_group.ref,
                        emitted,
                        include_sign_span=include_sign_span,
                    )
                continue

            if self._is_simple_concatenation(reviewed_groups[i1:i2], raw_groups[j1:j2]):
                raw_group = raw_groups[j1]
                reviewed_comments = self._group_comments(reviewed_groups[i1:i2])
                emitted = self._fallback_group(
                    raw_group,
                    auto_by_id.get(raw_group.token_id),
                    extra_comments=reviewed_comments,
                )
                current_ref = self._append_group(
                    output_lines,
                    current_ref,
                    raw_group.ref,
                    emitted,
                    include_sign_span=include_sign_span,
                )
                continue

            if self._is_simple_split(reviewed_groups[i1:i2], raw_groups[j1:j2]):
                split_groups = self._migrate_split_group(
                    reviewed_groups[i1],
                    raw_groups[j1:j2],
                    auto_by_id,
                )
                for raw_group, emitted in zip(raw_groups[j1:j2], split_groups, strict=True):
                    current_ref = self._append_group(
                        output_lines,
                        current_ref,
                        raw_group.ref,
                        emitted,
                        include_sign_span=include_sign_span,
                    )
                continue

            for raw_group in raw_groups[j1:j2]:
                auto_group = auto_by_id.get(raw_group.token_id)
                emitted = self._fallback_group(raw_group, auto_group)
                current_ref = self._append_group(
                    output_lines,
                    current_ref,
                    raw_group.ref,
                    emitted,
                    include_sign_span=include_sign_span,
                )

        return "\n".join(output_lines) + "\n"

    def _migrate_split_group(
        self,
        reviewed_group: TokenGroup,
        raw_groups: list[TokenGroup],
        auto_by_id: dict[str, TokenGroup],
    ) -> list[TokenGroup]:
        override = self._split_override(reviewed_group, raw_groups)
        if override is not None:
            return override

        reviewed_comments = self._group_comments([reviewed_group])
        migrated_by_index: dict[int, list[TokenRow]] = {}
        meaningful_indices = [
            index for index, raw_group in enumerate(raw_groups) if raw_group.surface
        ]

        for reviewed_row in reviewed_group.rows:
            analysis_parts = self._split_analysis_field(
                reviewed_row.analysis, len(meaningful_indices)
            )
            if analysis_parts is None or not all(
                self._analysis_matches_surface(analysis, raw_groups[raw_index].surface)
                for analysis, raw_index in zip(
                    analysis_parts, meaningful_indices, strict=True
                )
            ):
                continue
            dulat_parts = self._split_semicolon_field(
                reviewed_row.dulat, len(meaningful_indices)
            )
            pos_parts = self._split_semicolon_field(
                reviewed_row.pos, len(meaningful_indices)
            )
            gloss_parts = self._split_semicolon_field(
                reviewed_row.gloss, len(meaningful_indices)
            )

            for part_index, raw_index in enumerate(meaningful_indices):
                raw_group = raw_groups[raw_index]
                auto_row = self._first_source_row(
                    raw_group, auto_by_id.get(raw_group.token_id)
                )
                migrated_by_index.setdefault(raw_index, []).append(
                    TokenRow(
                        token_id=raw_group.token_id,
                        surface=raw_group.surface,
                        ref=raw_group.ref,
                        analysis=analysis_parts[part_index],
                        dulat=dulat_parts[part_index]
                        if dulat_parts is not None
                        else auto_row.dulat,
                        pos=pos_parts[part_index]
                        if pos_parts is not None
                        else auto_row.pos,
                        gloss=gloss_parts[part_index]
                        if gloss_parts is not None
                        else auto_row.gloss,
                        comment=self._merge_comments(
                            reviewed_row.comment,
                            self._LEGACY_TOKENIZATION_COMMENT,
                        ),
                        sign_span=raw_group.sign_span,
                    )
                )

        migrated_groups: list[TokenGroup] = []
        for raw_index, raw_group in enumerate(raw_groups):
            migrated_rows = migrated_by_index.get(raw_index)
            if migrated_rows:
                migrated_groups.append(
                    TokenGroup(
                        token_id=raw_group.token_id,
                        surface=raw_group.surface,
                        ref=raw_group.ref,
                        rows=tuple(migrated_rows),
                        sign_span=raw_group.sign_span,
                    )
                )
                continue
            migrated_groups.append(
                self._fallback_group(
                    raw_group,
                    auto_by_id.get(raw_group.token_id),
                    extra_comments=reviewed_comments,
                )
            )
        return migrated_groups

    def _split_override(
        self, reviewed_group: TokenGroup, raw_groups: list[TokenGroup]
    ) -> list[TokenGroup] | None:
        """Apply reviewed reconstructions that cannot be inferred from token surfaces alone."""
        if reviewed_group.surface != "ḫršnr" or tuple(
            group.surface for group in raw_groups
        ) != ("ḫršn", "r"):
            return None

        source = reviewed_group.rows[0]
        fields = (
            ("ḫršn(I)/", source.dulat, source.pos, source.gloss),
            ("&gr(I)/", "ġr (I)", source.pos, "mountain"),
        )
        migrated_groups: list[TokenGroup] = []
        for raw_group, (analysis, dulat, pos, gloss) in zip(
            raw_groups, fields, strict=True
        ):
            row = TokenRow(
                token_id=raw_group.token_id,
                surface=raw_group.surface,
                ref=raw_group.ref,
                analysis=analysis,
                dulat=dulat,
                pos=pos,
                gloss=gloss,
                comment=self._merge_comments(
                    source.comment,
                    self._LEGACY_TOKENIZATION_COMMENT,
                ),
                sign_span=raw_group.sign_span,
            )
            migrated_groups.append(
                TokenGroup(
                    token_id=raw_group.token_id,
                    surface=raw_group.surface,
                    ref=raw_group.ref,
                    rows=(row,),
                    sign_span=raw_group.sign_span,
                )
            )
        return migrated_groups

    @staticmethod
    def _split_analysis_field(value: str, count: int) -> list[str] | None:
        if count <= 0:
            return []
        parts = [part.rstrip(";") for part in value.split()]
        return parts if len(parts) == count else None

    @staticmethod
    def _split_semicolon_field(value: str, count: int) -> list[str] | None:
        if count <= 0:
            return []
        parts = [part.strip() for part in value.split(";")]
        return parts if len(parts) == count else None

    @staticmethod
    def _analysis_matches_surface(analysis: str, surface: str) -> bool:
        normalized = re.sub(r"\([IV]+\)", "", analysis)
        analysis_letters = "".join(character for character in normalized if character.isalpha())
        surface_letters = "".join(character for character in surface if character.isalpha())
        if not analysis_letters or not surface_letters:
            return False
        return SequenceMatcher(
            a=analysis_letters,
            b=surface_letters,
            autojunk=False,
        ).ratio() >= 0.6

    @staticmethod
    def _first_source_row(raw_group: TokenGroup, auto_group: TokenGroup | None) -> TokenRow:
        return (auto_group.rows if auto_group is not None else raw_group.rows)[0]

    @staticmethod
    def _group_comments(groups: list[TokenGroup]) -> tuple[str, ...]:
        return tuple(
            row.comment
            for group in groups
            for row in group.rows
            if row.comment
        )

    def _migrate_aligned_group(
        self,
        reviewed_group: TokenGroup,
        raw_group: TokenGroup,
    ) -> TokenGroup:
        refreshed_rows: list[TokenRow] = []
        seen: set[tuple[str, str, str, str, str]] = set()

        for row in reviewed_group.rows:
            refreshed = TokenRow(
                token_id=raw_group.token_id,
                surface=raw_group.surface,
                ref=raw_group.ref,
                analysis=row.analysis,
                dulat=row.dulat,
                pos=row.pos,
                gloss=row.gloss,
                comment=row.comment,
                sign_span=raw_group.sign_span,
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
            sign_span=raw_group.sign_span,
        )

    @staticmethod
    def _limit_raw_groups_to_reviewed_refs(
        reviewed_groups: list[TokenGroup], raw_groups: list[TokenGroup]
    ) -> list[TokenGroup]:
        """Keep partial reviewed files bounded by their first and last reviewed refs."""
        if not reviewed_groups or not raw_groups:
            return raw_groups
        first_ref = reviewed_groups[0].ref
        last_ref = reviewed_groups[-1].ref
        first_indices = [index for index, group in enumerate(raw_groups) if group.ref == first_ref]
        last_indices = [index for index, group in enumerate(raw_groups) if group.ref == last_ref]
        if not first_indices or not last_indices:
            return raw_groups
        start = first_indices[0]
        stop = last_indices[-1] + 1
        return raw_groups[start:stop] if start < stop else raw_groups

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
                    sign_span=raw_group.sign_span,
                )
                for row in reviewed_group.rows
            ),
            sign_span=raw_group.sign_span,
        )

    def _fallback_group(
        self,
        raw_group: TokenGroup,
        auto_group: TokenGroup | None,
        *,
        extra_comments: tuple[str, ...] = (),
    ) -> TokenGroup:
        source_rows = list(auto_group.rows) if auto_group is not None else list(raw_group.rows)
        migrated_rows: list[TokenRow] = []
        for row in source_rows:
            comment = self._merge_comments(
                *extra_comments,
                row.comment,
                self._LEGACY_TOKENIZATION_COMMENT,
            )
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
                    sign_span=raw_group.sign_span,
                )
            )
        return TokenGroup(
            token_id=raw_group.token_id,
            surface=raw_group.surface,
            ref=raw_group.ref,
            rows=tuple(migrated_rows),
            sign_span=raw_group.sign_span,
        )

    @staticmethod
    def _append_group(
        output_lines: list[str],
        current_ref: str | None,
        ref: str,
        group: TokenGroup,
        *,
        include_sign_span: bool,
    ) -> str:
        if ref != current_ref:
            output_lines.append(f"# {ref}" + "\t" * (7 if include_sign_span else 6))
        for row in group.rows:
            fields = [row.token_id, row.surface]
            if include_sign_span:
                fields.append(row.sign_span)
            fields.extend([row.analysis, row.dulat, row.pos, row.gloss, row.comment])
            output_lines.append("\t".join(fields))
        return ref

    @staticmethod
    def _append_comment(existing: str, extra: str) -> str:
        if not existing:
            return extra
        if extra in existing:
            return existing
        return f"{existing} | {extra}"

    @classmethod
    def _merge_comments(cls, *comments: str) -> str:
        merged = ""
        for comment in comments:
            if comment:
                merged = cls._append_comment(merged, comment)
        return merged

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
        has_sign_span = ReviewedTabletMigrator._has_sign_span_column(path)
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
                            sign_span=rows_by_key[0].sign_span,
                        )
                    )
                    rows_by_key = []
                    current_key = None
                ref = line[2:].split("\t")[0]
                continue
            if not line.strip() or line.startswith("id\t"):
                continue
            parts = line.split("\t")
            expected_columns = 8 if has_sign_span else 7
            if len(parts) < expected_columns:
                parts += [""] * (expected_columns - len(parts))
            elif len(parts) > expected_columns:
                parts = parts[: expected_columns - 1] + [
                    "\t".join(parts[expected_columns - 1 :])
                ]
            token_id, surface = parts[0], parts[1]
            if has_sign_span:
                sign_span, analysis, dulat, pos, gloss, comment = parts[2:8]
            else:
                sign_span = ""
                analysis, dulat, pos, gloss, comment = parts[2:7]
            analysis, comment = ReviewedTabletMigrator._split_inline_analysis_comment(
                analysis, comment
            )
            key = (token_id, surface, ref)
            if current_key is not None and key != current_key:
                prev_id, prev_surface, prev_ref = current_key
                groups.append(
                    TokenGroup(
                        token_id=prev_id,
                        surface=prev_surface,
                        ref=prev_ref,
                        rows=tuple(rows_by_key),
                        sign_span=rows_by_key[0].sign_span,
                    )
                )
                rows_by_key = []
            current_key = key
            rows_by_key.append(
                TokenRow(
                    token_id=token_id,
                    surface=surface,
                    ref=ref,
                    analysis=normalize_reviewed_analysis(analysis),
                    dulat=dulat,
                    pos=pos,
                    gloss=gloss,
                    comment=comment,
                    sign_span=sign_span,
                )
            )

        if current_key is not None:
            token_id, surface, token_ref = current_key
            groups.append(
                TokenGroup(
                    token_id=token_id,
                    surface=surface,
                    ref=token_ref,
                    rows=tuple(rows_by_key),
                    sign_span=rows_by_key[0].sign_span,
                )
            )

        return groups

    @staticmethod
    def _split_inline_analysis_comment(analysis: str, comment: str) -> tuple[str, str]:
        match = _INLINE_ANALYSIS_COMMENT_RE.match(analysis)
        if match is None:
            return analysis, comment
        stripped_analysis = match.group("analysis").rstrip()
        inline_comment = match.group("comment").strip()
        if not inline_comment:
            return stripped_analysis, comment
        merged_comment = inline_comment if not comment else f"{inline_comment} | {comment}"
        return stripped_analysis, merged_comment

    @staticmethod
    def _has_sign_span_column(path: Path) -> bool:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split("\t")
            lowered = [part.strip().lower() for part in parts]
            if lowered[:3] == ["id", "surface form", "sign span"]:
                return True
            if parts[0].strip().isdigit():
                return len(parts) >= 8
        return False

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
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            token_id, surface = parts[:2]
            sign_span = parts[3] if len(parts) >= 4 else surface
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
                            sign_span=sign_span,
                        ),
                    ),
                    sign_span=sign_span,
                )
            )
        return groups


_INLINE_ANALYSIS_COMMENT_RE = re.compile(r"^(?P<analysis>.+?)\s+#\s*(?P<comment>.+)$")
