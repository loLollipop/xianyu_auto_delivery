from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from .models import Card


class CardStore:
    """从 xianyu_card 的思路抽象出的卡密仓储（SQLite 版）。"""

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
                    product_name TEXT NOT NULL,
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
                CREATE TABLE IF NOT EXISTS delivery_logs (
                    order_id TEXT PRIMARY KEY,
                    delivered_at TEXT NOT NULL,
                    card_count INTEGER NOT NULL,
                    delivery_message TEXT NOT NULL
                )
                """
            )

    def import_cards_from_file(self, product_name: str, file_path: str) -> int:
        inserted = 0
        now = datetime.utcnow().isoformat()
        with open(file_path, "r", encoding="utf-8") as f, self._conn() as conn:
            for raw in f:
                code = raw.strip()
                if not code:
                    continue
                cur = conn.execute(
                    """
                    INSERT OR IGNORE INTO cards(product_name, card_code, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (product_name, code, now),
                )
                inserted += cur.rowcount
        return inserted

    def allocate_cards(self, product_name: str, order_id: str, quantity: int) -> list[Card]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT id, product_name, card_code, created_at
                FROM cards
                WHERE product_name = ? AND is_used = 0
                ORDER BY id ASC
                LIMIT ?
                """,
                (product_name, quantity),
            ).fetchall()
            if len(rows) < quantity:
                return []

            cards = [
                Card(
                    card_id=int(row["id"]),
                    product_name=str(row["product_name"]),
                    card_code=str(row["card_code"]),
                    created_at=datetime.fromisoformat(str(row["created_at"])),
                )
                for row in rows
            ]

            now = datetime.utcnow().isoformat()
            conn.executemany(
                """
                UPDATE cards
                SET is_used = 1, used_by_order_id = ?, used_at = ?
                WHERE id = ?
                """,
                [(order_id, now, c.card_id) for c in cards],
            )
            return cards

    def rollback_cards(self, order_id: str) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """
                UPDATE cards
                SET is_used = 0, used_by_order_id = NULL, used_at = NULL
                WHERE used_by_order_id = ?
                """,
                (order_id,),
            )
            return cur.rowcount

    def is_order_delivered(self, order_id: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM delivery_logs WHERE order_id = ?",
                (order_id,),
            ).fetchone()
            return row is not None

    def mark_delivered(self, order_id: str, card_count: int, message: str) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO delivery_logs(order_id, delivered_at, card_count, delivery_message)
                VALUES (?, ?, ?, ?)
                """,
                (order_id, datetime.utcnow().isoformat(), card_count, message),
            )
