import sqlite3
from pathlib import Path
from typing import Dict, Optional

from fastapi import HTTPException, status

from backend.app.board_seed import SEED_CARDS, SEED_COLUMNS


class BoardStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT NOT NULL UNIQUE,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS boards (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL UNIQUE,
                  name TEXT NOT NULL DEFAULT 'Kanban Board',
                  version INTEGER NOT NULL DEFAULT 1,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS columns (
                  id TEXT PRIMARY KEY,
                  board_id INTEGER NOT NULL,
                  slot_key TEXT NOT NULL,
                  title TEXT NOT NULL,
                  position INTEGER NOT NULL,
                  version INTEGER NOT NULL DEFAULT 1,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
                  UNIQUE (board_id, slot_key),
                  UNIQUE (board_id, position)
                );

                CREATE TABLE IF NOT EXISTS cards (
                  id TEXT PRIMARY KEY,
                  board_id INTEGER NOT NULL,
                  column_id TEXT NOT NULL,
                  title TEXT NOT NULL,
                  details TEXT NOT NULL,
                  sort_order REAL NOT NULL,
                  version INTEGER NOT NULL DEFAULT 1,
                  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
                  FOREIGN KEY (column_id) REFERENCES columns(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_cards_board_id ON cards(board_id);
                CREATE INDEX IF NOT EXISTS idx_cards_column_sort ON cards(column_id, sort_order);
                CREATE INDEX IF NOT EXISTS idx_cards_board_updated ON cards(board_id, updated_at);
                """
            )

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def get_board_snapshot(self, username: str) -> Dict[str, object]:
        with self.connect() as connection:
            board_id = self._get_or_seed_board(connection, username)
            return self._read_board_snapshot(connection, board_id)

    def get_card(self, username: str, card_id: str) -> Dict[str, object]:
        with self.connect() as connection:
            board_id = self._get_or_seed_board(connection, username)
            row = connection.execute(
                """
                SELECT id, column_id, title, details, sort_order, version
                FROM cards
                WHERE board_id = ? AND id = ?
                """,
                (board_id, card_id),
            ).fetchone()

            if row is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Card not found",
                )

            return self._card_snapshot_from_row(row)

    def rename_column(
        self,
        username: str,
        column_id: str,
        title: str,
        expected_version: int,
    ) -> Dict[str, object]:
        with self.connect() as connection:
            board_id = self._get_or_seed_board(connection, username)
            column = self._get_column(connection, board_id, column_id)
            self._ensure_version(column["version"], expected_version, "Column")

            connection.execute(
                """
                UPDATE columns
                SET title = ?, version = version + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND board_id = ?
                """,
                (title, column_id, board_id),
            )
            self._touch_board(connection, board_id)
            connection.commit()
            return self._read_board_snapshot(connection, board_id)

    def create_card(
        self,
        username: str,
        card_id: str,
        column_id: str,
        title: str,
        details: str,
        before_card_id: Optional[str],
        after_card_id: Optional[str],
    ) -> Dict[str, object]:
        with self.connect() as connection:
            board_id = self._get_or_seed_board(connection, username)
            self._get_column(connection, board_id, column_id)
            sort_order = self._resolve_sort_order(
                connection,
                board_id=board_id,
                target_column_id=column_id,
                before_card_id=before_card_id,
                after_card_id=after_card_id,
                moving_card_id=None,
            )

            connection.execute(
                """
                INSERT INTO cards (id, board_id, column_id, title, details, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (card_id, board_id, column_id, title, details, sort_order),
            )
            self._touch_board(connection, board_id)
            connection.commit()
            return self._read_board_snapshot(connection, board_id)

    def update_card(
        self,
        username: str,
        card_id: str,
        title: str,
        details: str,
        expected_version: int,
    ) -> Dict[str, object]:
        with self.connect() as connection:
            board_id = self._get_or_seed_board(connection, username)
            card = self._get_card_row(connection, board_id, card_id)
            self._ensure_version(card["version"], expected_version, "Card")

            connection.execute(
                """
                UPDATE cards
                SET title = ?, details = ?, version = version + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND board_id = ?
                """,
                (title, details, card_id, board_id),
            )
            self._touch_board(connection, board_id)
            connection.commit()
            return self._read_board_snapshot(connection, board_id)

    def move_card(
        self,
        username: str,
        card_id: str,
        target_column_id: str,
        expected_version: int,
        before_card_id: Optional[str],
        after_card_id: Optional[str],
    ) -> Dict[str, object]:
        with self.connect() as connection:
            board_id = self._get_or_seed_board(connection, username)
            card = self._get_card_row(connection, board_id, card_id)
            self._ensure_version(card["version"], expected_version, "Card")
            self._get_column(connection, board_id, target_column_id)
            sort_order = self._resolve_sort_order(
                connection,
                board_id=board_id,
                target_column_id=target_column_id,
                before_card_id=before_card_id,
                after_card_id=after_card_id,
                moving_card_id=card_id,
            )

            connection.execute(
                """
                UPDATE cards
                SET column_id = ?, sort_order = ?, version = version + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND board_id = ?
                """,
                (target_column_id, sort_order, card_id, board_id),
            )
            self._touch_board(connection, board_id)
            connection.commit()
            return self._read_board_snapshot(connection, board_id)

    def delete_card(
        self,
        username: str,
        card_id: str,
        expected_version: int,
    ) -> Dict[str, object]:
        with self.connect() as connection:
            board_id = self._get_or_seed_board(connection, username)
            card = self._get_card_row(connection, board_id, card_id)
            self._ensure_version(card["version"], expected_version, "Card")

            connection.execute(
                "DELETE FROM cards WHERE id = ? AND board_id = ?",
                (card_id, board_id),
            )
            self._touch_board(connection, board_id)
            connection.commit()
            return self._read_board_snapshot(connection, board_id)

    def _get_or_seed_board(self, connection: sqlite3.Connection, username: str) -> int:
        user_id = self._get_or_create_user(connection, username)
        board = connection.execute(
            "SELECT id FROM boards WHERE user_id = ?",
            (user_id,),
        ).fetchone()

        if board is not None:
            return int(board["id"])

        cursor = connection.execute(
            "INSERT INTO boards (user_id) VALUES (?)",
            (user_id,),
        )
        board_id = int(cursor.lastrowid)
        connection.executemany(
            """
            INSERT INTO columns (id, board_id, slot_key, title, position)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    column["id"],
                    board_id,
                    column["slot_key"],
                    column["title"],
                    column["position"],
                )
                for column in SEED_COLUMNS
            ],
        )
        connection.executemany(
            """
            INSERT INTO cards (id, board_id, column_id, title, details, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    card["id"],
                    board_id,
                    card["column_id"],
                    card["title"],
                    card["details"],
                    card["sort_order"],
                )
                for card in SEED_CARDS
            ],
        )
        connection.commit()
        return board_id

    def _get_or_create_user(self, connection: sqlite3.Connection, username: str) -> int:
        row = connection.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()

        if row is not None:
            return int(row["id"])

        cursor = connection.execute(
            "INSERT INTO users (username) VALUES (?)",
            (username,),
        )
        return int(cursor.lastrowid)

    def _read_board_snapshot(
        self,
        connection: sqlite3.Connection,
        board_id: int,
    ) -> Dict[str, object]:
        board_row = connection.execute(
            "SELECT version FROM boards WHERE id = ?",
            (board_id,),
        ).fetchone()

        if board_row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Board not found",
            )

        column_rows = connection.execute(
            """
            SELECT id, slot_key, title, position, version
            FROM columns
            WHERE board_id = ?
            ORDER BY position
            """,
            (board_id,),
        ).fetchall()
        card_rows = connection.execute(
            """
            SELECT id, column_id, title, details, sort_order, version
            FROM cards
            WHERE board_id = ?
            ORDER BY column_id, sort_order, id
            """,
            (board_id,),
        ).fetchall()

        card_ids_by_column = {}
        cards = {}
        for row in card_rows:
            card = self._card_snapshot_from_row(row)
            cards[card["id"]] = card
            card_ids_by_column.setdefault(card["columnId"], []).append(card["id"])

        columns = []
        for row in column_rows:
            columns.append(
                {
                    "id": row["id"],
                    "slotKey": row["slot_key"],
                    "title": row["title"],
                    "position": row["position"],
                    "version": row["version"],
                    "cardIds": card_ids_by_column.get(row["id"], []),
                }
            )

        return {
            "version": board_row["version"],
            "columns": columns,
            "cards": cards,
        }

    def _card_snapshot_from_row(self, row: sqlite3.Row) -> Dict[str, object]:
        return {
            "id": row["id"],
            "columnId": row["column_id"],
            "title": row["title"],
            "details": row["details"],
            "sortOrder": row["sort_order"],
            "version": row["version"],
        }

    def _touch_board(self, connection: sqlite3.Connection, board_id: int) -> None:
        connection.execute(
            """
            UPDATE boards
            SET version = version + 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (board_id,),
        )

    def _get_column(
        self,
        connection: sqlite3.Connection,
        board_id: int,
        column_id: str,
    ) -> sqlite3.Row:
        row = connection.execute(
            """
            SELECT id, title, version
            FROM columns
            WHERE board_id = ? AND id = ?
            """,
            (board_id, column_id),
        ).fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Column not found",
            )
        return row

    def _get_card_row(
        self,
        connection: sqlite3.Connection,
        board_id: int,
        card_id: str,
    ) -> sqlite3.Row:
        row = connection.execute(
            """
            SELECT id, column_id, title, details, sort_order, version
            FROM cards
            WHERE board_id = ? AND id = ?
            """,
            (board_id, card_id),
        ).fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found",
            )
        return row

    def _resolve_sort_order(
        self,
        connection: sqlite3.Connection,
        board_id: int,
        target_column_id: str,
        before_card_id: Optional[str],
        after_card_id: Optional[str],
        moving_card_id: Optional[str],
    ) -> float:
        before_row = None
        after_row = None

        if before_card_id:
            before_row = self._get_card_row(connection, board_id, before_card_id)
            if before_row["column_id"] != target_column_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="beforeCardId must be in the target column",
                )
            if before_card_id == moving_card_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot position a card relative to itself",
                )

        if after_card_id:
            after_row = self._get_card_row(connection, board_id, after_card_id)
            if after_row["column_id"] != target_column_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="afterCardId must be in the target column",
                )
            if after_card_id == moving_card_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot position a card relative to itself",
                )

        if before_row and after_row and before_row["sort_order"] <= after_row["sort_order"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="beforeCardId must come after afterCardId",
            )

        if before_row and after_row:
            return (before_row["sort_order"] + after_row["sort_order"]) / 2

        if before_row:
            previous_row = connection.execute(
                """
                SELECT sort_order
                FROM cards
                WHERE board_id = ? AND column_id = ? AND id != ? AND sort_order < ?
                ORDER BY sort_order DESC
                LIMIT 1
                """,
                (
                    board_id,
                    target_column_id,
                    moving_card_id or "",
                    before_row["sort_order"],
                ),
            ).fetchone()
            previous_order = previous_row["sort_order"] if previous_row else before_row["sort_order"] - 1000
            return (previous_order + before_row["sort_order"]) / 2

        if after_row:
            next_row = connection.execute(
                """
                SELECT sort_order
                FROM cards
                WHERE board_id = ? AND column_id = ? AND id != ? AND sort_order > ?
                ORDER BY sort_order ASC
                LIMIT 1
                """,
                (
                    board_id,
                    target_column_id,
                    moving_card_id or "",
                    after_row["sort_order"],
                ),
            ).fetchone()
            next_order = next_row["sort_order"] if next_row else after_row["sort_order"] + 1000
            return (after_row["sort_order"] + next_order) / 2

        last_row = connection.execute(
            """
            SELECT sort_order
            FROM cards
            WHERE board_id = ? AND column_id = ? AND id != ?
            ORDER BY sort_order DESC
            LIMIT 1
            """,
            (board_id, target_column_id, moving_card_id or ""),
        ).fetchone()
        if last_row is None:
            return 1000.0
        return float(last_row["sort_order"]) + 1000.0

    def _ensure_version(
        self,
        current_version: int,
        expected_version: int,
        label: str,
    ) -> None:
        if current_version != expected_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{label} version conflict",
            )
