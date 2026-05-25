from datetime import timedelta

from backend.configs.security import create_access_token
from backend.repositories.user_repository import UserRepository
from backend.schemas.first_schema import Message
from backend.services.email_service import SMTPEmailService


class ForgotPasswordService:
    def __init__(
        self,
        user_repository: UserRepository,
        email_service: SMTPEmailService | None = None,
    ) -> None:
        self.user_repository = user_repository
        self.email_service = email_service or SMTPEmailService()

    async def execute(self, email: str) -> Message:
        user = await self.user_repository.get_by_email(email)
        if not user:
            return Message(
                message='If the email exists, a reset link was sent.'
            )

        reset_token = create_access_token(
            data={'sub': user.email},
            expires_delta=timedelta(hours=1),
            token_type='reset',
        )
        self.email_service.send_password_reset(user.email, reset_token)

        return Message(message='If the email exists, a reset link was sent.')
