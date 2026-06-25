# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional

from app.utils.age_calculator import calculate_age

@dataclass
class OCRResult:
    full_name: str = ''
    address: str = ''
    national_id: str = ''
    birth_date: str = ''
    age: Optional[int] = None
    message: str = 'بانتظار المراجعة'

class OCRService:
    SAMPLE_PATTERN = re.compile(
        r"name_(?P<name>.+?)__nid_(?P<nid>\d{14})__birth_(?P<birth>\d{4}-\d{2}-\d{2})__addr_(?P<addr>.+?)(?:\.[A-Za-z]+)?$"
    )

    def process(self, image_path: str) -> OCRResult:
        base = os.path.basename(image_path)
        m = self.SAMPLE_PATTERN.search(base)
        if not m:
            return OCRResult(message='فشل التعرف على البيانات. أعد تصوير البطاقة مرة أخرى بصورة أوضح.')
        full_name = m.group('name').replace('_', ' ').strip()
        address = m.group('addr').replace('_', ' ').strip()
        national_id = m.group('nid').strip()
        birth = m.group('birth').strip()
        age = calculate_age(birth)
        return OCRResult(
            full_name=full_name,
            address=address,
            national_id=national_id,
            birth_date=birth,
            age=age,
            message='تم استخراج البيانات بنجاح. راجعها ثم احفظ.',
        )
