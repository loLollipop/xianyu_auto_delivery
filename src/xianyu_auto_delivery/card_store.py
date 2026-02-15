from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from .models import CardCode


class CardStore:
    """参考 xianyu_card 的本地卡密库存能力。"""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_key TEXT NOT NULL,
                    card_code TEXT NOT NULL UNIQUE,
                    is_used INTEGER NOT NULL DEFAULT 0,
                    used_by_order_id TEXT,
                    created_at TEXT NOT NULL,
                    used_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS delivered_orders (
                    order_id TEXT PRIMARY KEY,
                    delivered_at TEXT NOT NULL
                )
                """
            )

    def import_cards_from_file(self, product_key: str, file_path: str) -> int:
        now = datetime.utcnow().isoformat()
        inserted = 0
        with open(file_path, "r", encoding="utf-8") as file, self._conn() as conn:
            for raw in file:
                code = raw.strip()
                if not code:
                    continue
                cur = conn.execute(
                    "INSERT OR IGNORE INTO cards(product_key, card_code, created_at) VALUES (?, ?, ?)",
                    (product_key, code, now),
                )
                inserted += cur.rowcount
        return inserted

    def allocate_cards(self, product_key: str, order_id: str, quantity: int) -> list[CardCode]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT id, card_code FROM cards
                WHERE product_key = ? AND is_used = 0
                ORDER BY id ASC LIMIT ?
                """,
                (product_key, quantity),
            ).fetchall()
            if len(rows) < quantity:
                return []

            ids = [int(row["id"]) for row in rows]
            now = datetime.utcnow().isoformat()
            conn.executemany(
                "UPDATE cards SET is_used = 1, used_by_order_id = ?, used_at = ? WHERE id = ?",
                [(order_id, now, card_id) for card_id in ids],
            )
            return [CardCode(code=str(row["card_code"])) for row in rows]

    def rollback_cards(self, order_id: str) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE cards
                SET is_used = 0, used_by_order_id = NULL, used_at = NULL
                WHERE used_by_order_id = ?
                """,
                (order_id,),
            )

    def is_delivered(self, order_id: str) -> bool:
        with self._conn() as conn:
            row = conn.execute("SELECT 1 FROM delivered_orders WHERE order_id = ?", (order_id,)).fetchone()
            return row is not None

    def mark_delivered(self, order_id: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO delivered_orders(order_id, delivered_at) VALUES (?, ?)",
                (order_id, datetime.utcnow().isoformat()),
            )
