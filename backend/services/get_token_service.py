from http import HTTPStatus

from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from backend.configs.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from backend.repositories.user_repository import UserRepository
from backend.schemas.token_schema import Token


class GetTokenService:
    def __init__(
        self,
        user_repository: UserRepository,
        form_data: OAuth2PasswordRequestForm,
    ) -> None:
        self.user_repository = user_repository
        self.form_data = form_data

    async def execute(self) -> Token:
        user = await self.user_repository.get_by_email(self.form_data.username)
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail='Incorrect email or password',
            )

        if not verify_password(self.form_data.password, user.password):
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail='Incorrect email or password',
            )

        if not user.email_verified:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='Email not verified',
            )
        access_token = create_access_token(data={'sub': user.email})
        refresh_token = create_refresh_token(data={'sub': user.email})
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type='bearer',
        )
