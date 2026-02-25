"""Overrides for known DULAT form-morph parsing inconsistencies."""

from __future__ import annotations

LOOKUP_NORMALIZE = str.maketrans(
    {
        "ʿ": "ʕ",
        "ˤ": "ʕ",
        "ả": "a",
        "ỉ": "i",
        "ủ": "u",
    }
)


def _norm_text(value: str) -> str:
    return (value or "").strip().translate(LOOKUP_NORMALIZE).lower()


def _norm_homonym(value: str) -> str:
    return (value or "").strip().upper()


_FORM_MORPH_OVERRIDES: dict[tuple[str, str, str, str], str] = {
    # ỉl (I): `du., cstr.` leaked onto plain construct forms during table parsing.
    # DULAT forms: sg. ỉl; pl. cstr. ỉly; du. ỉlmy.
    ("il", "I", "il", "du., cstr."): "sg., cstr.",
    ("il", "I", "ily", "du., cstr."): "pl., cstr.",
    ("il", "I", "-y", "du., cstr."): "pl., cstr.",
    # tḥm: suffixed form tḥmk is tagged as sg. in parsed table data.
    # DULAT forms: sg. tḥm; suff. tḥmk.
    ("tḥm", "", "tḥmk", "sg."): "suff.",
}


def override_dulat_form_morphology(
    *,
    lemma: str,
    homonym: str,
    form_text: str,
    morphology: str,
) -> str:
    """Return corrected morphology label for known table-parsing mislabels."""
    source = (morphology or "").strip()
    if not source:
        return source
    key = (
        _norm_text(lemma),
        _norm_homonym(homonym),
        _norm_text(form_text),
        source.lower(),
    )
    return _FORM_MORPH_OVERRIDES.get(key, source)
