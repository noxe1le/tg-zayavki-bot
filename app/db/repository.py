from datetime import datetime

from app.db.base import Database
from app.models import Request


class RequestRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def add(
        self,
        *,
        user_id: int,
        username: str | None,
        name: str,
        phone: str,
        comment: str,
    ) -> Request:
        created_at = datetime.now().replace(microsecond=0)
        cursor = await self._db.conn.execute(
            "INSERT INTO requests (user_id, username, name, phone, comment, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, name, phone, comment, created_at.isoformat()),
        )
        await self._db.conn.commit()
        return Request(
            id=cursor.lastrowid or 0,
            user_id=user_id,
            username=username,
            name=name,
            phone=phone,
            comment=comment,
            created_at=created_at,
        )

    async def by_user(self, user_id: int, *, limit: int = 5, offset: int = 0) -> list[Request]:
        cursor = await self._db.conn.execute(
            "SELECT id, user_id, username, name, phone, comment, created_at"
            " FROM requests WHERE user_id = ? ORDER BY id DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset),
        )
        rows = await cursor.fetchall()
        return [
            Request(
                id=row["id"],
                user_id=row["user_id"],
                username=row["username"],
                name=row["name"],
                phone=row["phone"],
                comment=row["comment"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    async def count(self, user_id: int | None = None) -> int:
        if user_id is None:
            cursor = await self._db.conn.execute("SELECT COUNT(*) FROM requests")
        else:
            cursor = await self._db.conn.execute(
                "SELECT COUNT(*) FROM requests WHERE user_id = ?", (user_id,)
            )
        row = await cursor.fetchone()
        return int(row[0]) if row else 0
