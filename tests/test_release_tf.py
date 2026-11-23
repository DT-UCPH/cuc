"""Read the published TF through its normal API and validate its new semantics."""

from pathlib import Path

import pytest
from tf.fabric import Fabric


_LOADED = {}


def load(version):
    if version not in _LOADED:
        root = Path(__file__).resolve().parents[1] / "tf" / version
        tf = Fabric(locations=str(root), silent="deep")
        result = tf.loadAll(silent="deep")
        assert result
        _LOADED[version] = result
    return _LOADED[version]


@pytest.fixture(scope="module", params=["0.3.0", "0.4.0"])
def api(request):
    """Checks every release since 0.3.0 must pass."""
    return load(request.param)


@pytest.fixture(scope="module")
def api030():
    return load("0.3.0")


@pytest.fixture(scope="module")
def api040():
    return load("0.4.0")


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


def test_431_short_alphabet_letters_are_distinct_single_slots(api030):
    """0.3.0's spellings; 0.4.0 reads them ṯ and ḫ (editorial decision 1)."""
    F, L = api030.F, api030.L
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


def test_language_follows_ktu3_tablet_and_line_range_statements(api):
    F, L = api.F, api.L

    def tablet(name):
        return next(n for n in F.otype.s("tablet") if F.tablet.v(n) == name)

    def languages(name, first=None, last=None):
        return {
            F.language.v(word)
            for line in L.d(tablet(name), "line")
            if first is None or first <= F.line.v(line) <= last
            for word in L.d(line, "word")
        }

    assert languages("KTU 1.1") == {"Ugaritic"}
    assert languages("KTU 1.26") == {"Hurrian"}
    assert languages("KTU 1.67") == {"Akkadian"}
    assert languages("KTU 1.148", 13, 17) == {"Hurrian"}
    assert languages("KTU 1.148", 1, 12) == languages("KTU 1.148", 18, 45) == {"Ugaritic"}
    assert languages("KTU 1.73", 1, 7) == {"Akkadian"}
    assert languages("KTU 1.73", 8, 18) == {"Ugaritic"}
    assert languages("KTU 1.111", 1, 13) == {None}
    assert languages("KTU 1.111", 14, 99) == {"Ugaritic"}
    assert languages("KTU 1.116") == languages("KTU 1.132") == {None}
    assert languages("KTU 5.24") == {None}


def test_030_language_counts(api030):
    F = api030.F
    assert set(F.language.freqList()) == {("Ugaritic", 29813), ("Hurrian", 640), ("Akkadian", 129)}


def test_tablet_language_states_ktu3_for_the_whole_tablet(api):
    F = api.F
    by_tablet = {F.tablet.v(t): F.tablet_language.v(t) for t in F.otype.s("tablet")}
    assert by_tablet["KTU 1.1"] == "Ugaritic"
    assert by_tablet["KTU 1.26"] == "Hurrian"
    assert by_tablet["KTU 1.67"] == "Akkadian"
    assert by_tablet["KTU 1.73"] == "Akkadian and Ugaritic"
    for name in ("KTU 1.111", "KTU 1.116", "KTU 1.132", "KTU 1.148"):
        assert by_tablet[name] == "Hurrian and Ugaritic"
    assert by_tablet["KTU 5.24"] is None


def test_030_tablet_language_counts(api030):
    assert dict(api030.F.tablet_language.freqList()) == {
        "Ugaritic": 322, "Hurrian": 10, "Akkadian": 2,
        "Hurrian and Ugaritic": 4, "Akkadian and Ugaritic": 1}


def test_validator_recovery_turns_ktu_11_ii_28_into_a_break(api):
    F, L, T = api.F, api.L, api.T
    column = T.nodeFromSection(("KTU 1.1", "II"))
    labels = [F.line_label.v(line) for line in L.d(column, "line")]
    assert "28" not in labels and "27" in labels
    line27 = T.nodeFromSection(("KTU 1.1", "II", "27"))
    after27 = [b for b in L.d(column, "boundary") if api.E.boundary_prev.f(b) == (line27,)]
    assert [F.boundary_kind.v(b) for b in after27] == ["break"]


# --- 0.4.0 ---------------------------------------------------------------

KTU_ADDED_040 = {"KTU 1.32", "KTU 1.33"} | {
    "KTU 4.%d" % n for n in range(42, 63) if n not in (52, 59)}
RIH_HELD_040 = {  # RIH II texts left out of 0.4.0 (docs/release-0.4.0.md)
    "RIH 83/02", "RIH 2002/01", "RIH 97/01 + 97/02", "RIH 84/09", "RIH 83/05",
    "RIH 83/16", "RIH 84/05", "RIH 83/47 + 83/51 + 83/56", "RIH 89/01",
    "RIH 84/[31,08]"}


def _tablets(api):
    return {api.F.tablet.v(t): t for t in api.F.otype.s("tablet")}


def test_040_keeps_every_030_tablet_and_adds_111_texts(api030, api040):
    old, new = _tablets(api030), _tablets(api040)
    assert set(old) <= set(new)
    added = set(new) - set(old)
    assert len(added) == 111
    F = api040.F
    rih = {name for name in added if F.rih.v(new[name])}
    assert len(rih) == 90
    assert added - rih == KTU_ADDED_040
    assert not {"KTU 1.34", "KTU 4.52", "KTU 4.59", "KTU 4.63", "KTU 4.100"} & set(new)
    assert not RIH_HELD_040 & {F.rih.v(new[name]) for name in rih}
    counts = {kind: len(F.otype.s(kind)) for kind in
              ("sign", "word", "line", "column", "tablet", "boundary", "alias")}
    assert counts == {"sign": 174546, "word": 32872, "line": 9533, "column": 531,
                      "tablet": 453, "boundary": 1409, "alias": 3}
    assert len(F.synthetic.s("True")) == 1413


def test_040_rih_texts_carry_their_citations_and_rih_iis_language(api040):
    F, L = api040.F, api040.L
    rih = [t for t in F.otype.s("tablet") if F.rih.v(t)]
    assert len(rih) == 90
    for t in rih:
        assert F.source_edition.v(t) == "RIH II"
        assert F.tablet.v(t) == (F.ktu.v(t) or F.rih.v(t))
        # RIH II: texts 1-153 are "Les textes ougaritiques" (BN-47)
        assert F.tablet_language.v(t) == "Ugaritic"
        assert {F.language.v(w) for w in L.d(t, "word")} == {"Ugaritic"}
        assert not any(F.type.v(n) == "logogram" for n in L.d(t, "word") + L.d(t, "sign"))
    assert sum(1 for t in rih if F.ktu.v(t)) == 75
    for t in F.otype.s("tablet"):
        if not F.rih.v(t):
            assert F.source_edition.v(t) is None and F.ktu.v(t) is None
    # RIH 83/08 (KTU 9.463) line 1 `yṯpṭ 16`: the integer is an annotation.
    line1 = api040.T.nodeFromSection(("KTU 9.463", "I", "1"))
    assert F.number.v(line1) == 16
    assert len([n for n in F.otype.s("line") if F.number.v(n)]) == 30
    ticks = [n for n in F.otype.s("line") if F.line_mark.v(n)]
    assert {F.tablet.v(L.u(n, "tablet")[0]) for n in ticks} == {"KTU 9.484"}
    assert sorted(F.line_mark_cert.v(n) for n in ticks).count("True") == 22


def test_040_language_counts_and_new_hurrian_texts(api040):
    F, L = api040.F, api040.L
    tablets = _tablets(api040)
    for name in ("KTU 1.32", "KTU 1.33"):
        assert F.tablet_language.v(tablets[name]) == "Hurrian"
        assert {F.language.v(w) for w in L.d(tablets[name], "word")} == {"Hurrian"}
    assert set(F.language.freqList()) == {("Ugaritic", 31819), ("Hurrian", 664), ("Akkadian", 129)}
    assert dict(F.tablet_language.freqList()) == {
        "Ugaritic": 431, "Hurrian": 12, "Akkadian": 2,
        "Hurrian and Ugaritic": 4, "Akkadian and Ugaritic": 1}


def _lines(api, name):
    F, L, T = api.F, api.L, api.T
    tablet = _tablets(api)[name]
    return {(F.column.v(c), F.line_label.v(l)): T.text(l)
            for c in L.d(tablet, "column") for l in L.d(c, "line")}


def test_040_text_changes_in_030_tablets_are_the_reviews_and_the_short_alphabet(api030, api040):
    changed = {name for name in _tablets(api030)
               if _lines(api030, name) != _lines(api040, name)}
    assert changed == {"KTU 1.4", "KTU 1.5", "KTU 1.6", "KTU 1.31", "KTU 4.31"}
    old14, new14 = _lines(api030, "KTU 1.4"), _lines(api040, "KTU 1.4")
    assert set(old14) == set(new14)
    assert (old14[("II", "11")], new14[("II", "11")]) == ("tġzy . bny . bnwt", "tġẓy . bny . bnwt")
    assert new14[("I", "5")] == "il . abh . il mlk"
    old131, new131 = _lines(api030, "KTU 1.31"), _lines(api040, "KTU 1.31")
    assert all(len(new131[k]) == len(old131[k]) + 5 for k in old131)
    new16 = _lines(api040, "KTU 1.6")
    assert new16[("VI", "45")].startswith("yn . tġẓyt")


def test_040_ktu_16_iv_29_and_v_30_are_breaks(api030, api040):
    F, L, E = api040.F, api040.L, api040.E
    old16 = _lines(api030, "KTU 1.6")
    assert old16[("IV", "29")].strip() == old16[("V", "30")].strip() == "…"
    tablet = _tablets(api040)["KTU 1.6"]
    for column, last in (("IV", "28"), ("V", "29")):
        node = next(c for c in L.d(tablet, "column") if F.column.v(c) == column)
        labels = [F.line_label.v(l) for l in L.d(node, "line")]
        assert labels[-1] == last
        after = [b for b in L.d(node, "boundary")
                 if [F.line_label.v(l) for l in E.boundary_prev.f(b)] == [last]]
        assert [F.boundary_kind.v(b) for b in after] == ["break"]


def test_040_ktu_431_short_alphabet_reads_t_and_h_and_keeps_its_spelling(api040):
    F, L = api040.F, api040.L
    tablet = _tablets(api040)["KTU 4.31"]
    sources = [(F.sign.v(s), F.usign.v(s), F.sign_source.v(s))
               for s in L.d(tablet, "sign") if F.sign_source.v(s)]
    assert sorted(set(sources)) == [("ḫ", "𐎃", "ẖ"), ("ṯ", "𐎘", "s̄")]
    assert len(sources) == 21
    assert not F.sign.s("s̄") and not F.sign.s("ẖ")
    assert _lines(api040, "KTU 4.31")[("I", "2")].startswith("b ṯṯ ʿṯr ṯmn . rqḫ")


def test_040_ktu_11_ii_10_ayin_of_db_is_uncertain(api030, api040):
    def ayin_cert(api):
        F, L, T = api.F, api.L, api.T
        line = T.nodeFromSection(("KTU 1.1", "II", "10"))
        word = next(w for w in L.d(line, "word") if F.g_cons.v(w) == "ʿdb")
        return F.cert.v(L.d(word, "sign")[0])
    assert (ayin_cert(api030), ayin_cert(api040)) == ("True", "False")


def test_040_a_lost_stretch_after_a_word_is_a_gap_word(api030, api040):
    """KTU 4.24 I 5 `[          ]xšt . b[n           ]`, whose source did not
    change between the releases."""
    def words(api):
        F, L, T = api.F, api.L, api.T
        line = T.nodeFromSection(("KTU 4.24", "I", "5"))
        return [(F.g_cons.v(w), F.type.v(w)) for w in L.d(line, "word")][-2:]
    assert words(api030)[-1] == ("bn", "lexical")
    assert words(api040) == [("bn", "lexical"), ("", "gap")]
    F = api040.F
    assert sum(1 for w in F.otype.s("word") if F.type.v(w) == "gap") == 938


def test_040_a_rih_text_is_addressed_by_its_rih_number(api040):
    F, T = api040.F, api040.T
    by_rih = getattr(F, "tablet@rih")
    tablets = F.otype.s("tablet")
    assert all(by_rih.v(t) == (F.rih.v(t) or F.tablet.v(t)) for t in tablets)
    for t in tablets:
        assert T.nodeFromSection((by_rih.v(t),), lang="rih") == t
    line = T.nodeFromSection(("RIH 83/08", "I", "1"), lang="rih")
    assert line == T.nodeFromSection(("KTU 9.463", "I", "1"))
    assert T.sectionFromNode(line, lang="rih") == ("RIH 83/08", "I", "1")
    assert T.nodeFromSection(("KTU 1.1", "I", "1"), lang="rih") == T.nodeFromSection(("KTU 1.1", "I", "1"))

