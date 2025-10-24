# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
import gettext, os, pathlib
from functools import lru_cache
DEFAULT_LANG="en"; ENV_VAR="NEURO_LANG"; DOMAIN="neuromotorica"
@lru_cache(maxsize=None)
def _translation(lang: str):
    locales_dir = pathlib.Path(__file__).with_suffix("").parent / "locales"
    try: return gettext.translation(DOMAIN, localedir=str(locales_dir), languages=[lang])
    except Exception:
        if lang!="en":
            try: return gettext.translation(DOMAIN, localedir=str(locales_dir), languages=["en"])
            except Exception: pass
        return gettext.NullTranslations()
def get_lang(explicit=None)->str:
    return (explicit or os.getenv(ENV_VAR) or DEFAULT_LANG).split("-")[0].lower()
def activate(lang=None):
    trans = _translation(get_lang(lang)); trans.install(names=("ngettext",))
    return trans.gettext, trans.ngettext
_ = activate()[0]
