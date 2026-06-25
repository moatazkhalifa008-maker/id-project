# -*- coding: utf-8 -*-
from __future__ import annotations

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:
    arabic_reshaper = None
    get_display = None


def rtl_text(text: str) -> str:
    if not text:
        return ''
    text = str(text)
    if arabic_reshaper is None or get_display is None:
        return text
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text
