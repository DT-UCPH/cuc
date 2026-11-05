import types
from html import escape
from tf.advanced.app import App

EMENDATION = dict(
    restored="supplied",
    excised="excised",
    redundant="redundant",
    missing="missing",
)

def fmt_layoutTrans(app, n, **kwargs):
    return app._wrapHtml(n, "t")


def fmt_layoutUnicode(app, n, **kwargs):
    return app._wrapHtml(n, "u")


class TfApp(App):
    def __init__(app, *args, **kwargs):
        app.fmt_layoutTrans = types.MethodType(fmt_layoutTrans, app)
        app.fmt_layoutUnicode = types.MethodType(fmt_layoutUnicode, app)
        app.fmt_layout = types.MethodType(fmt_layoutTrans, app)
        super().__init__(*args, **kwargs)


    def _wrapHtml(app, n, kind):
        api = app.api
        F = api.F
        L = api.L

        synthetic = getattr(F, "synthetic", None)
        if synthetic is not None and synthetic.v(n) == "True":
            return ""

        material = escape((F.usign.v(n) if kind == "u" else F.sign.v(n)) or "")
        emendation = F.emen.v(n)
        cls = EMENDATION.get(emendation, None)

        if cls is not None:
             material = f"""<span class="{cls}">{material}</span>"""

        if F.cert.v(n) == "True":
            material = f"""<em>{material}</em>"""

        after_feature = getattr(F, "uafter" if kind == "u" else "after", None)
        words = L.u(n, "word")
        trailer = ""
        trailer_emendation = None
        if words:
            word = words[0]
            trailer = (F.utrailer.v(word) if kind == "u" else F.trailer.v(word)) or ""
            trailer_emendation = F.trailer_emen.v(word)
        if after_feature is not None:
            after = after_feature.v(n) or ""
        else:
            # Older datasets put dividers only on their word node.
            after = trailer if words and n == L.d(words[0], "sign")[-1] else ""
        after_cls = EMENDATION.get(trailer_emendation) if after == trailer else None
        after = escape(after)
        if after and after_cls is not None:
            after = f"""<span class="{after_cls}">{after}</span>"""
        return f"{material}{after}"
