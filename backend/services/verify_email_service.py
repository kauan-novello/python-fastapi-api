from http import HTTPStatus

from fastapi import HTTPException
from jwt import decode

from backend.configs.security import settings
from backend.repositories.user_repository import UserRepository
from backend.schemas.first_schema import Message


class VerifyEmailService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def execute(self, token: str) -> Message:
        try:
            payload = decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
        except Exception:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail='Invalid token'
            ) from None

        if payload.get('token_type') != 'verify':
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail='Invalid token type'
            )

        email = payload.get('sub')
        if not isinstance(email, str):
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail='Invalid token'
            )

        user = await self.user_repository.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail='Invalid token'
            )

        if not user.email_verified:
            await self.user_repository.mark_email_verified(user)

        return Message(message='email verified')
