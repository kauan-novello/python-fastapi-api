import logging

from backend.repositories.token_repository import RevokedTokenRepository

logger = logging.getLogger(__name__)


class CleanupRevokedTokensService:
    def __init__(self, revoked_repo: RevokedTokenRepository) -> None:
        self.revoked_repo = revoked_repo

    async def execute(self) -> int:
        deleted = await self.revoked_repo.delete_expired()
        if deleted:
            logger.info('Removed %s expired revoked tokens', deleted)
        return deleted
