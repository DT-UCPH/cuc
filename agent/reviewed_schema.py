"""Strict record validation for the eight-column, sign-span reviewed format.

Legacy seven-column imports retain their own compatibility normalization.
Validate before splitting inline comments or padding fields: either can hide
an accidental tab or physical newline in an expert's feedback.
"""


def reviewed_record_error(parts: list[str]) -> str | None:
    if len(parts) != 8:
        return f"Expected exactly 8 columns in reviewed row, got {len(parts)}"
    if not parts[0].strip().isdigit():
        return "Expected a numeric token ID in reviewed row"
    return None
