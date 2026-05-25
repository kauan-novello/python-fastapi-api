from datetime import datetime
from typing import Any, cast
from zoneinfo import ZoneInfo

from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.revoked_token import RevokedToken
from backend.utils.token_hash import hash_token


class RevokedTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        token: str,
        expires_at: datetime | None = None,
    ) -> None:
        revoked = RevokedToken(
            token_hash=hash_token(token),
            expires_at=expires_at,  # type: ignore[arg-type]
        )
        self.session.add(revoked)
        await self.session.commit()

    async def is_revoked(self, token: str) -> bool:
        token_hash = hash_token(token)
        result = await self.session.scalar(
            select(RevokedToken).where(RevokedToken.token_hash == token_hash)
        )
        return result is not None

    async def delete_expired(self) -> int:
        now = datetime.now(tz=ZoneInfo('UTC'))
        stmt = delete(RevokedToken).where(
            RevokedToken.expires_at.is_not(None),  # type: ignore[union-attr]
            RevokedToken.expires_at < now,  # type: ignore[arg-type,operator]
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        cursor = cast(CursorResult[Any], result)
        return int(cursor.rowcount or 0)
