import types
from tf.advanced.app import App


CERTAINTY = dict(
    uncertain="uncertain",    
    restored="supplied",
    excised="excised",
    redundant="redundant",
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

        after = (F.traileru.v(n) if kind == "u" else F.trailer.v(n)) or ""
        material = (F.signu.v(n) if kind == "u" else F.sign.v(n)) or ""
        certainty = F.certainty.v(n)
        cls = CERTAINTY.get(certainty, None)
        material = f"""<span class="{cls}">{material}</span>"""

        return f"{material}{after}"