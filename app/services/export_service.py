# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path


def export_csv(db, folder_path: str) -> str:
    folder = Path(folder_path).expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise ValueError('المسار غير موجود أو ليس مجلدًا صالحًا')
    rows = db.export_rows()
    file_name = f'id_check_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    out_path = folder / file_name
    with out_path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'age', 'address', 'national_id'])
        writer.writeheader()
        writer.writerows(rows)
    return str(out_path)
