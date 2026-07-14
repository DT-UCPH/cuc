"""Hardcoded high-frequency formula-trigram parsing rules.

Rules are selected from corpus trigram frequency analysis over `out/KTU 1.*.tsv`
and target high-confidence formula contexts.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TokenParse:
    """Canonical token parse payload for one row."""

    analysis: str
    dulat: str
    pos: str
    gloss: str


@dataclass(frozen=True)
class FormulaTrigramRule:
    """Canonical parsing rule for a frequent three-token surface formula."""

    first_surface: str
    second_surface: str
    third_surface: str
    first_target: TokenParse | None = None
    second_target: TokenParse | None = None
    third_target: TokenParse | None = None
    min_count: int = 1
    note: str = ""


FORMULA_TRIGRAM_RULES: tuple[FormulaTrigramRule, ...] = (
    FormulaTrigramRule(
        first_surface="rbt",
        second_surface="aṯrt",
        third_surface="ym",
        first_target=TokenParse(
            analysis="rbt(I)/",
            dulat="rbt (I)",
            pos="n. f.",
            gloss="Lady",
        ),
        min_count=20,
        note="Epithets formula: Lady Asherah of the Sea.",
    ),
    FormulaTrigramRule(
        first_surface="zbl",
        second_surface="bˤl",
        third_surface="arṣ",
        first_target=TokenParse(
            analysis="zbl(I)/",
            dulat="zbl (I)",
            pos="n. m.",
            gloss="prince",
        ),
        min_count=9,
        note="Epithets formula: Prince Baʿlu of the Earth.",
    ),
    FormulaTrigramRule(
        first_surface="idk",
        second_surface="l",
        third_surface="ttn",
        second_target=TokenParse(
            analysis="l(III)",
            dulat="l (III)",
            pos="functor",
            gloss="certainly",
        ),
        min_count=9,
        note="Journey formula: idk l ttn pnm.",
    ),
    FormulaTrigramRule(
        first_surface="l",
        second_surface="ttn",
        third_surface="pnm",
        first_target=TokenParse(
            analysis="l(III)",
            dulat="l (III)",
            pos="functor",
            gloss="certainly",
        ),
        min_count=9,
        note="Journey formula: idk l ttn pnm.",
    ),
    FormulaTrigramRule(
        first_surface="il",
        second_surface="tˤḏr",
        third_surface="bˤl",
        third_target=TokenParse(
            analysis="bˤl(II)/",
            dulat="bʕl (II)",
            pos="DN",
            gloss="Baʿlu",
        ),
        min_count=6,
        note="Formula sequence: il tˤḏr bˤl.",
    ),
)
