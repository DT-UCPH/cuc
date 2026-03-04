"""Rule-based spaCy component for offering-list `l` preposition normalization."""

from dataclasses import dataclass

from spacy.language import Language
from spacy.tokens import Doc

from pipeline.steps.base import TabletRow, is_unresolved
from pipeline.steps.dulat_gate import LOOKUP_NORMALIZE

_OFFERING_SURFACES = {
    "gdlt",
    "alp",
    "alpm",
    "šnpt",
    "ʕr",
    "npš",
    "ššrt",
    "š",
    "ynt",
}


@dataclass(frozen=True)
class ResolutionEvent:
    token_index: int
    rule: str
    before: TabletRow
    after: TabletRow


def _normalize(text: str) -> str:
    return (text or "").translate(LOOKUP_NORMALIZE).strip()


def _is_nominal_pos(pos_text: str) -> bool:
    pos = (pos_text or "").strip()
    if not pos:
        return False
    return any(tag in pos for tag in ("n.", "adj.", "num.", "DN", "PN", "TN"))


def _is_ambiguous_l_row(row: TabletRow) -> bool:
    return (
        row.surface.strip() == "l"
        and row.analysis.strip() == "l(I);l(II);l(III)"
        and row.dulat.strip() == "l (I);l (II);l (III)"
        and row.pos.strip() == "prep.;adv.;functor"
        and row.gloss.strip() == "to;no;certainly"
    )


def _is_offering_row(row: TabletRow) -> bool:
    return _normalize(row.surface) in _OFFERING_SURFACES and _is_nominal_pos(row.pos)


def _is_recipient_row(row: TabletRow) -> bool:
    pos_text = (row.pos or "").strip()
    if "vb" in pos_text:
        return False
    return _is_nominal_pos(pos_text)


def _canonical_l_prep(row: TabletRow) -> TabletRow:
    return TabletRow(
        line_id=row.line_id,
        surface=row.surface,
        analysis="l(I)",
        dulat="l (I)",
        pos="prep.",
        gloss="to",
        comment=row.comment,
    )


class OfferingContextResolver:
    def __call__(self, doc: Doc) -> Doc:
        doc.user_data.setdefault("offering_context_events", [])
        for token in doc:
            token._.resolved_row = token._.row

        snapshot = [token._.resolved_row for token in doc]
        for index, token in enumerate(doc):
            row = snapshot[index]
            if row is None or is_unresolved(row):
                continue
            if not _is_ambiguous_l_row(row):
                continue
            if index == 0 or index + 1 >= len(doc):
                continue
            prev_row = snapshot[index - 1]
            next_row = snapshot[index + 1]
            if prev_row is None or next_row is None:
                continue
            if not _is_offering_row(prev_row):
                continue
            if not _is_recipient_row(next_row):
                continue
            updated = _canonical_l_prep(row)
            token._.resolved_row = updated
            doc.user_data["offering_context_events"].append(
                ResolutionEvent(index, "offering-l-prep", row, updated)
            )
        return doc


@Language.factory("ugaritic_offering_context_resolver")
def make_offering_context_resolver(nlp, name):
    return OfferingContextResolver()
