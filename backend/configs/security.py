from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Any, cast
from zoneinfo import ZoneInfo

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import decode, encode
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.configs.database import get_session
from backend.configs.settings import Settings
from backend.models.user_model import User
from backend.repositories.token_repository import RevokedTokenRepository

settings = Settings()
pwd_context = PasswordHash.recommended()


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
    token_type: str = 'access',
) -> str:
    to_encode = data.copy()
    expire = datetime.now(tz=ZoneInfo('UTC')) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({'exp': expire, 'token_type': token_type})
    encoded_jwt = encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict[str, Any]) -> str:
    return create_access_token(
        data,
        expires_delta=timedelta(days=7),
        token_type='refresh',
    )


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='auth/token', refreshUrl='auth/refresh_token'
)


async def get_current_user(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
    expected_token_type: str | None = 'access',
) -> User:
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        subject_email = payload.get('sub')
        token_type = payload.get('token_type')

        if not subject_email:
            raise credentials_exception

        if (
            expected_token_type is not None
            and token_type != expected_token_type
        ):
            raise credentials_exception

    except InvalidTokenError:
        raise credentials_exception

    revoked_repo = RevokedTokenRepository(session)
    if await revoked_repo.is_revoked(token):
        raise credentials_exception

    user = cast(
        User | None,
        await session.scalar(select(User).where(User.email == subject_email)),
    )

    if not user:
        raise credentials_exception

    return user
