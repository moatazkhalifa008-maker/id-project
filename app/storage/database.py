# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import List, Dict

DB_NAME = 'id_check.db'
APP_DIR = Path(__file__).resolve().parents[2] / 'user_data'
APP_DIR.mkdir(exist_ok=True)
DB_PATH = APP_DIR / DB_NAME

class Database:
    def __init__(self, db_path: str | os.PathLike | None = None):
        self.db_path = str(db_path or DB_PATH)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                address TEXT,
                national_id TEXT NOT NULL UNIQUE,
                birth_date TEXT,
                age INTEGER,
                image_path TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            '''
        )
        cur.execute('CREATE INDEX IF NOT EXISTS idx_records_normalized_name ON records(normalized_name)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_records_created_at ON records(created_at DESC)')
        self.conn.commit()

    def insert_record(self, **kwargs):
        cur = self.conn.cursor()
        cur.execute(
            '''
            INSERT INTO records(full_name, normalized_name, address, national_id, birth_date, age, image_path)
            VALUES(:full_name, :normalized_name, :address, :national_id, :birth_date, :age, :image_path)
            ''',
            kwargs,
        )
        self.conn.commit()

    def national_id_exists(self, national_id: str) -> bool:
        cur = self.conn.cursor()
        cur.execute('SELECT 1 FROM records WHERE national_id = ? LIMIT 1', (national_id,))
        return cur.fetchone() is not None

    def search_by_name(self, query: str) -> List[Dict]:
        from app.utils.arabic_normalizer import normalize_arabic
        nq = f"%{normalize_arabic(query)}%"
        cur = self.conn.cursor()
        cur.execute(
            '''
            SELECT full_name, address, national_id, birth_date, age, image_path, created_at
            FROM records
            WHERE normalized_name LIKE ?
            ORDER BY created_at DESC
            ''',
            (nq,),
        )
        return [dict(r) for r in cur.fetchall()]

    def list_recent(self, limit: int = 50) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute(
            '''
            SELECT full_name, address, national_id, birth_date, age, image_path, created_at
            FROM records
            ORDER BY created_at DESC
            LIMIT ?
            ''',
            (limit,),
        )
        return [dict(r) for r in cur.fetchall()]

    def export_rows(self) -> List[Dict]:
        cur = self.conn.cursor()
        cur.execute(
            '''
            SELECT full_name AS name, age, address, national_id
            FROM records
            ORDER BY created_at DESC
            '''
        )
        return [dict(r) for r in cur.fetchall()]
