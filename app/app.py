import types
from tf.advanced.app import App


CERTAINTY = dict(
    uncertain="uncertain",
)

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

        material = (F.usign.v(n) if kind == "u" else F.sign.v(n)) or ""
        emendation = F.emen.v(n)
        certainty = F.cert.v(n)
        material = f"""<span class="{CERTAINTY.get(certainty, None)} {EMENDATION.get(emendation, None)}">{material}</span>"""

        after = (F.utrailer.v(L.u(n, 'word')[0]) if kind == "u" else F.trailer.v(L.u(n, 'word')[0])) or ""
       	trailer_emendation = F.trailer_emen.v(L.u(n, 'word')[0])
        after = f"""<span class="{CERTAINTY.get(trailer_emendation, None)}">{after}</span>"""

        if n == L.d(L.u(n, 'word')[0], 'sign')[-1]:
            return f"{material}{after}"
        else:
            return material