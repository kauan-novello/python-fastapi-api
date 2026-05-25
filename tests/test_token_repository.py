from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from backend.configs.security import create_access_token
from backend.repositories.token_repository import RevokedTokenRepository
from backend.utils.token_hash import hash_token


@pytest.mark.asyncio
async def test_revoked_token_is_stored_as_hash(session):
    repo = RevokedTokenRepository(session)
    token = create_access_token({'sub': 'user@example.com'})

    await repo.add(token=token)

    assert await repo.is_revoked(token) is True
    assert await repo.is_revoked('different-token') is False


@pytest.mark.asyncio
async def test_delete_expired_removes_only_expired_tokens(session):
    repo = RevokedTokenRepository(session)
    expired_token = create_access_token(
        {'sub': 'expired@example.com'},
        expires_delta=timedelta(minutes=-5),
    )
    valid_token = create_access_token({'sub': 'valid@example.com'})

    await repo.add(
        token=expired_token,
        expires_at=datetime.now(tz=ZoneInfo('UTC')) - timedelta(minutes=1),
    )
    await repo.add(token=valid_token, expires_at=None)

    deleted = await repo.delete_expired()

    assert deleted == 1
    assert await repo.is_revoked(expired_token) is False
    assert await repo.is_revoked(valid_token) is True


def test_hash_token_is_deterministic():
    token = 'sample-token'
    assert hash_token(token) == hash_token(token)
    assert hash_token(token) != hash_token('other-token')
