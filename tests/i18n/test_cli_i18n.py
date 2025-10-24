from neuromotorica.i18n.core import activate, _
def test_fallback():
    _ = activate("uk")[0]
    s = _("Benchmark runner initialized")
    assert isinstance(s, str)
