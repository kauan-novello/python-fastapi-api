from datetime import datetime
from zoneinfo import ZoneInfo

from jwt import decode
from sqlalchemy.ext.asyncio import AsyncSession

from backend.configs.security import settings
from backend.repositories.token_repository import RevokedTokenRepository
from backend.schemas.first_schema import Message


class LogoutService:
    def __init__(self, revoked_repo: RevokedTokenRepository) -> None:
        self.revoked_repo = revoked_repo

    async def execute(self, token: str, session: AsyncSession) -> Message:
        try:
            payload = decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            exp = payload.get('exp')
            expires_at = (
                datetime.fromtimestamp(exp, tz=ZoneInfo('UTC'))
                if exp is not None
                else None
            )
        except Exception:
            expires_at = None

        await self.revoked_repo.add(token=token, expires_at=expires_at)
        return Message(message='logged out')
