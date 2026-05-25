from datetime import timedelta
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from backend.configs.security import create_access_token
from backend.models.user_model import User
from backend.repositories.user_repository import UserRepository
from backend.schemas.user_schema import UserCreate
from backend.services.email_service import SMTPEmailService


class CreateUserService:
    def __init__(
        self,
        user_repository: UserRepository,
        email_service: SMTPEmailService | None = None,
    ) -> None:
        self.user_repository = user_repository
        self.email_service = email_service or SMTPEmailService()

    async def execute(self, user_data: UserCreate) -> User:
        user_exists = await self.user_repository.find_by_username_or_email(
            username=user_data.username,
            email=user_data.email,
        )

        if user_exists:
            if user_exists.username == user_data.username:
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail='Username already exists',
                )

            if user_exists.email == user_data.email:
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail='Email already exists',
                )

        try:
            user = await self.user_repository.create(user_data)
        except IntegrityError:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Username or Email already exists',
            ) from None

        self._send_verification_email(user.email)
        return user

    def _send_verification_email(self, email: str) -> None:
        verify_token = create_access_token(
            data={'sub': email},
            expires_delta=timedelta(hours=24),
            token_type='verify',
        )
        self.email_service.send_verification(email, verify_token)
