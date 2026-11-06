"""Render the released sign/trailer model, including invisible TF anchors."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def render():
    spec = importlib.util.spec_from_file_location(
        "cuc_release_app", Path(__file__).resolve().parents[1] / "app/app.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def run(values, *, kind="t", words=(100,), signs=(1, 2), modern=True):
        names = {"sign", "usign", "cert", "emen", "trailer", "utrailer", "trailer_emen"}
        if modern:
            names |= {"after", "uafter", "synthetic"}
        features = SimpleNamespace(**{
            name: SimpleNamespace(v=lambda n, key=name: values.get(key, {}).get(n))
            for name in names
        })
        app = SimpleNamespace(api=SimpleNamespace(
            F=features, L=SimpleNamespace(u=lambda *_: words, d=lambda *_: signs)
        ))
        return module.TfApp._wrapHtml(app, 1, kind)

    return run


def test_certain_sign_is_italic_and_uncertain_sign_is_roman(render):
    assert render({"sign": {1: "a"}, "cert": {1: "True"}}) == "<em>a</em>"
    assert render({"sign": {1: "a"}, "cert": {1: "False"}}) == "a"


def test_synthetic_boundary_slot_has_no_word_and_no_visible_content(render):
    assert render({"synthetic": {1: "True"}}, words=()) == ""


def test_after_is_rendered_at_its_slot_even_inside_a_word(render):
    assert render({"sign": {1: "ṯ"}, "after": {1: "₂"}}) == "ṯ₂"
    assert render({"usign": {1: "𐎘"}, "uafter": {1: "₂"}}, kind="u") == "𐎘₂"


def test_real_trailer_preserves_its_own_emendation(render):
    values = {"sign": {1: "a"}, "after": {1: "."},
              "trailer": {100: "."}, "trailer_emen": {100: "restored"}}
    assert render(values, signs=(1,)) == 'a<span class="supplied">.</span>'


def test_source_material_is_escaped_as_text(render):
    assert render({"sign": {1: "<"}, "after": {1: "&"}}) == "&lt;&amp;"


def test_028_fallback_emits_word_trailer_once(render):
    values = {"sign": {1: "a"}, "trailer": {100: "."}}
    assert render(values, signs=(1,), modern=False) == "a."
    assert render(values, signs=(1, 2), modern=False) == "a"
