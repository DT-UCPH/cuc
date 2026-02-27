"""Hardcoded high-frequency formula-bigram parsing rules.

Rules were selected from corpus bigram frequency analysis over `out/KTU 1.*.tsv`
and target high-confidence DN epithet contexts.
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
class FormulaBigramRule:
    """Canonical parsing rule for a frequent two-token surface formula."""

    first_surface: str
    second_surface: str
    first_target: TokenParse | None = None
    second_target: TokenParse | None = None
    min_count: int = 1
    note: str = ""


FORMULA_BIGRAM_RULES: tuple[FormulaBigramRule, ...] = (
    FormulaBigramRule(
        first_surface="aliyn",
        second_surface="bˤl",
        second_target=TokenParse(
            analysis="bˤl(II)/",
            dulat="bʕl (II)",
            pos="DN",
            gloss="Baʿlu",
        ),
        min_count=61,
        note="Epithets formula: ʿAliyn Baʿlu.",
    ),
    FormulaBigramRule(
        first_surface="zbl",
        second_surface="bˤl",
        second_target=TokenParse(
            analysis="bˤl(II)/",
            dulat="bʕl (II)",
            pos="DN",
            gloss="Baʿlu",
        ),
        min_count=12,
        note="Epithets formula: Prince Baʿlu.",
    ),
    FormulaBigramRule(
        first_surface="bˤl",
        second_surface="ṣpn",
        first_target=TokenParse(
            analysis="bˤl(II)/",
            dulat="bʕl (II)",
            pos="DN",
            gloss="Baʿlu",
        ),
        min_count=15,
        note="Epithets formula: Baʿlu of Ṣapānu.",
    ),
    FormulaBigramRule(
        first_surface="btlt",
        second_surface="ˤnt",
        second_target=TokenParse(
            analysis="ˤnt(I)/",
            dulat="ʕnt (I)",
            pos="DN",
            gloss="ʿAnatu",
        ),
        min_count=34,
        note="Epithets formula: Virgin ʿAnatu.",
    ),
    FormulaBigramRule(
        first_surface="bn",
        second_surface="il",
        first_target=TokenParse(
            analysis="bn(I)/",
            dulat="bn (I)",
            pos="n. m.",
            gloss="son",
        ),
        min_count=24,
        note="Formula sequence: bn il.",
    ),
    FormulaBigramRule(
        first_surface="bn",
        second_surface="ilm",
        first_target=TokenParse(
            analysis="bn(I)/",
            dulat="bn (I)",
            pos="n. m.",
            gloss="son",
        ),
        min_count=21,
        note="Formula sequence: bn ilm.",
    ),
    FormulaBigramRule(
        first_surface="bt",
        second_surface="bˤl",
        second_target=TokenParse(
            analysis="bˤl(II)/",
            dulat="bʕl (II)",
            pos="DN",
            gloss="Baʿlu",
        ),
        min_count=11,
        note="Formula sequence: bt bˤl.",
    ),
    FormulaBigramRule(
        first_surface="ṯr",
        second_surface="il",
        first_target=TokenParse(
            analysis="ṯr(I)/",
            dulat="ṯr (I)",
            pos="n. m.",
            gloss="bull",
        ),
        second_target=TokenParse(
            analysis="il(I)/",
            dulat="ỉl (I)",
            pos="DN",
            gloss="ˀIlu",
        ),
        min_count=8,
        note="Epithet formula: ṯr il (Bull Ilu).",
    ),
    FormulaBigramRule(
        first_surface="rbt",
        second_surface="aṯrt",
        second_target=TokenParse(
            analysis="aṯrt(II)/",
            dulat="ảṯrt (II)",
            pos="DN",
            gloss="Asherah",
        ),
        min_count=20,
        note="Epithets formula: Lady Asherah.",
    ),
)
