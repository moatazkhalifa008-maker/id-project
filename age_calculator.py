# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import date, datetime

def calculate_age(birth_date_str: str):
    try:
        b = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
    except Exception:
        return None
    today = date.today()
    return today.year - b.year - ((today.month, today.day) < (b.month, b.day))
