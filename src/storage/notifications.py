"""SQLite を用いた通知リポジトリ実装。"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.models import NotificationCreate, NotificationRecord


class NotificationRepository:
    """通知を SQLite に永続化するリポジトリ。"""

    def __init__(
        self,
        db_path: str | Path,
        max_stored: int = 50,
        timezone_name: str = "Asia/Tokyo",
    ) -> None:
        self._db_path = Path(db_path)
        self._max_stored = max_stored
        self._tz = ZoneInfo(timezone_name)
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        """SQLite 接続を生成して返す。"""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        """テーブルが存在しない場合に作成する。"""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_name TEXT NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    received_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def add(self, payload: NotificationCreate) -> NotificationRecord:
        """通知を保存し、上限を超えた古いレコードを削除する。"""
        now = datetime.now(self._tz)
        received_iso = now.isoformat()

        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO notifications (app_name, title, body, received_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    payload.app_name.strip(),
                    payload.title.strip(),
                    payload.body.strip(),
                    received_iso,
                ),
            )
            record_id = int(cursor.lastrowid or 0)

            # 上限件数を超える古い通知を削除して肥大化を防止する
            conn.execute(
                """
                DELETE FROM notifications
                WHERE id NOT IN (
                    SELECT id FROM notifications
                    ORDER BY id DESC
                    LIMIT ?
                )
                """,
                (self._max_stored,),
            )
            conn.commit()

        return NotificationRecord(
            id=record_id,
            app_name=payload.app_name.strip(),
            title=payload.title.strip(),
            body=payload.body.strip(),
            received_at=now,
        )

    def list_recent(self, limit: int = 10) -> list[NotificationRecord]:
        """最新の通知を新しい順で取得する。"""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, app_name, title, body, received_at
                FROM notifications
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            NotificationRecord(
                id=int(row["id"]),
                app_name=str(row["app_name"]),
                title=str(row["title"]),
                body=str(row["body"]),
                received_at=datetime.fromisoformat(str(row["received_at"])),
            )
            for row in rows
        ]

    def clear_all(self) -> int:
        """すべての通知を削除し、削除件数を返す。"""
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM notifications")
            deleted = cursor.rowcount if cursor.rowcount >= 0 else 0
            conn.commit()
        return deleted
