"""Read the published TF through its normal API and validate its new semantics."""

from pathlib import Path

import pytest
from tf.fabric import Fabric


@pytest.fixture(scope="module")
def api():
    root = Path(__file__).resolve().parents[1] / "tf/0.3.0"
    tf = Fabric(locations=str(root), silent="deep")
    result = tf.loadAll(silent="deep")
    assert result
    return result


def test_every_non_slot_node_is_reachable_and_anchors_have_no_visible_text(api):
    F, E, L, T = api.F, api.E, api.L, api.T
    for node in range(F.otype.maxSlot + 1, F.otype.maxNode + 1):
        assert E.oslots.s(node)
    for slot in F.synthetic.s("True"):
        assert F.type.v(slot) == "empty"
        assert not F.sign.v(slot)
        assert not F.usign.v(slot)
        assert not T.text(slot, fmt="text-orig-full")
        assert not T.text(slot, fmt="text-orig-unicode")
        assert len(L.u(slot, "tablet")) == 1


def test_aliases_have_exact_existing_target_spans(api):
    F, E, L = api.F, api.E, api.L
    tablets = {F.tablet.v(n): n for n in F.otype.s("tablet")}
    aliases = {F.catalogue_alias.v(n): n for n in F.otype.s("alias")}
    assert set(aliases) == {"KTU 1.8", "KTU 1.99", "KTU 2.19"}
    for alias, target in (("KTU 1.99", "KTU 1.98"), ("KTU 2.19", "KTU 3.12")):
        assert E.oslots.s(aliases[alias]) == E.oslots.s(tablets[target])
        assert alias not in tablets
    lines = [line for line in L.d(tablets["KTU 1.3"], "line")
             if F.column.v(L.u(line, "column")[0]) == "VI"
             and 1 <= F.line.v(line) <= 17]
    expected = {s for line in lines for s in E.oslots.s(line)}
    assert set(E.oslots.s(aliases["KTU 1.8"])) == expected


def test_boundary_anchors_and_edges_stay_within_their_column(api):
    F, E, L = api.F, api.E, api.L
    for boundary in F.otype.s("boundary"):
        slot, = E.oslots.s(boundary)
        assert F.synthetic.v(slot) == "True"
        assert F.boundary_kind.v(boundary) in {"break", "ruling"}
        assert F.boundary_source.v(boundary)
        column, = L.u(slot, "column")
        for feature, before in ((E.boundary_prev, True), (E.boundary_next, False)):
            adjacent = feature.f(boundary)
            assert len(adjacent) <= 1
            for line in adjacent:
                assert F.otype.v(line) == "line"
                assert L.u(line, "column") == (column,)
                if before:
                    assert max(E.oslots.s(line)) < slot
                else:
                    assert min(E.oslots.s(line)) > slot


def test_section_addresses_are_unique_and_empty_1150_has_no_fabricated_line(api):
    F, E, L, T = api.F, api.E, api.L, api.T
    addresses = [T.sectionFromNode(line) for line in F.otype.s("line")]
    assert len(addresses) == len(set(addresses))
    assert all(F.line_label.v(line) for line in F.otype.s("line"))
    tablet = next(n for n in F.otype.s("tablet") if F.tablet.v(n) == "KTU 1.150")
    slot, = E.oslots.s(tablet)
    assert F.synthetic.v(slot) == "True"
    assert not L.d(tablet, "line")
    assert not L.d(tablet, "word")


def test_431_short_alphabet_letters_are_distinct_single_slots(api):
    F, L = api.F, api.L
    for letter, glyph, count in (("s̄", "𐎘", 14), ("ẖ", "𐎃", 7)):
        slots = F.sign.s(letter)
        assert len(slots) == count
        for slot in slots:
            assert F.type.v(slot) == "cons"
            assert F.usign.v(slot) == glyph
            assert F.cert.v(slot) in {"True", "False"}
            assert F.tablet.v(L.u(slot, "tablet")[0]) == "KTU 4.31"
            assert letter in F.g_cons.v(L.u(slot, "word")[0])
    assert not F.sign.s("\u0304")
    assert not F.sign.s("\u0331")
