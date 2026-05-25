import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.configs.database import get_session
from backend.configs.logging_config import setup_logging
from backend.repositories.token_repository import RevokedTokenRepository
from backend.services.cleanup_revoked_tokens_service import (
    CleanupRevokedTokensService,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger.info('Starting FastAPI boilerplate API')

    try:
        async for session in get_session():
            revoked_repo = RevokedTokenRepository(session)
            deleted = await CleanupRevokedTokensService(revoked_repo).execute()
            if deleted:
                logger.info(
                    'Startup cleanup removed %s expired tokens',
                    deleted,
                )
            break
    except Exception:
        logger.warning(
            'Startup token cleanup skipped',
            exc_info=True,
        )

    yield

    logger.info('Application shutdown complete')
