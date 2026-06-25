# -*- coding: utf-8 -*-
from __future__ import annotations
import re

ARABIC_DIACRITICS = re.compile(r'[ؐ-ًؚ-ٰٟۖ-ۭ]')
SPACES = re.compile(r'\s+')

def normalize_arabic(text: str) -> str:
    if not text:
        return ''
    text = ARABIC_DIACRITICS.sub('', text)
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ى', 'ي')
    text = text.replace('ؤ', 'و').replace('ئ', 'ي')
    text = text.replace('ة', 'ه')
    text = SPACES.sub(' ', text).strip()
    return text.lower()
