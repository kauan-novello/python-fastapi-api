import logging
import smtplib
from email.message import EmailMessage

from backend.configs.security import settings

logger = logging.getLogger(__name__)


class SMTPEmailService:
    def __init__(self) -> None:
        self.settings = settings

    def send(self, recipient: str, subject: str, body: str) -> bool:
        """
        Send email via SMTP.

        Returns True if successful, False otherwise.
        """
        try:
            message = EmailMessage()
            message['From'] = self.settings.EMAIL_FROM
            message['To'] = recipient
            message['Subject'] = subject
            message.set_content(body)

            with smtplib.SMTP(
                self.settings.SMTP_HOST,
                self.settings.SMTP_PORT,
            ) as smtp:
                if self.settings.SMTP_USE_TLS:
                    smtp.starttls()

                if self.settings.SMTP_USERNAME and self.settings.SMTP_PASSWORD:
                    smtp.login(
                        self.settings.SMTP_USERNAME,
                        self.settings.SMTP_PASSWORD,
                    )

                smtp.send_message(message)
            return True
        except smtplib.SMTPException as e:
            logger.error(f'SMTP error sending email to {recipient}: {str(e)}')
            return False
        except Exception as e:
            logger.error(
                f'Unexpected error sending email to {recipient}: {str(e)}'
            )
            return False

    def send_password_reset(self, recipient: str, token: str) -> None:
        reset_link = (
            f'{self.settings.FRONTEND_URL}/reset-password?token={token}'
        )
        body = (
            'You requested a password reset. Use the link below to '
            f'reset your password:\n\n{reset_link}\n'
        )
        self.send(recipient, 'Reset your password', body)

    def send_verification(self, recipient: str, token: str) -> None:
        verify_link = (
            f'{self.settings.FRONTEND_URL}/verify-email?token={token}'
        )
        body = (
            'Please verify your email using the link below:\n\n'
            f'{verify_link}\n'
        )
        self.send(recipient, 'Verify your email', body)
