from http import HTTPStatus

from fastapi import HTTPException
from jwt import decode

from backend.configs.security import settings
from backend.repositories.user_repository import UserRepository
from backend.schemas.auth_schemas import ResetPasswordRequest
from backend.schemas.first_schema import Message
from backend.schemas.user_schema import UserUpdate


class ResetPasswordService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def execute(self, body: ResetPasswordRequest) -> Message:
        try:
            payload = decode(
                body.token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
        except Exception:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Invalid token',
            ) from None

        if payload.get('token_type') != 'reset':
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Invalid token type',
            )

        email = payload.get('sub')
        if not isinstance(email, str):
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Invalid token',
            )

        user = await self.user_repository.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Invalid token',
            )

        user_update = UserUpdate(password=body.new_password)
        await self.user_repository.update(user.id, user_update)
        return Message(message='password reset successful')
