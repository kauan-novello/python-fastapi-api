import smtplib

from backend.configs.security import settings
from backend.services.email_service import SMTPEmailService


def test_smtp_email_service_sends_messages_with_login(monkeypatch):
    sent_messages = []
    logins = []

    class DummySMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        @staticmethod
        def starttls():
            return None

        @staticmethod
        def login(username, password):
            logins.append((username, password))

        @staticmethod
        def send_message(message):
            sent_messages.append(message)

    monkeypatch.setattr(
        'backend.services.email_service.smtplib.SMTP', DummySMTP
    )
    monkeypatch.setattr(settings, 'SMTP_USERNAME', 'smtp-user')
    monkeypatch.setattr(settings, 'SMTP_PASSWORD', 'smtp-pass')
    monkeypatch.setattr(settings, 'SMTP_USE_TLS', True)
    monkeypatch.setattr(settings, 'FRONTEND_URL', 'https://frontend.test')

    service = SMTPEmailService()
    service.send_password_reset('user@example.com', 'reset-token')
    service.send_verification('user@example.com', 'verify-token')

    expected_message_count = 2

    assert len(sent_messages) == expected_message_count
    assert logins == [
        ('smtp-user', 'smtp-pass'),
        ('smtp-user', 'smtp-pass'),
    ]
    assert sent_messages[0]['Subject'] == 'Reset your password'
    assert sent_messages[1]['Subject'] == 'Verify your email'
    assert 'reset-token' in sent_messages[0].get_content()
    assert 'verify-token' in sent_messages[1].get_content()


def test_smtp_email_service_handles_smtp_exception(monkeypatch, caplog):
    class FailingSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        @staticmethod
        def starttls():  # noqa: PLR6301
            raise smtplib.SMTPException('Connection failed')

    monkeypatch.setattr(
        'backend.services.email_service.smtplib.SMTP', FailingSMTP
    )
    monkeypatch.setattr(settings, 'SMTP_USERNAME', 'smtp-user')
    monkeypatch.setattr(settings, 'SMTP_PASSWORD', 'smtp-pass')
    monkeypatch.setattr(settings, 'SMTP_USE_TLS', True)

    service = SMTPEmailService()
    result = service.send('user@example.com', 'Test Subject', 'Test body')

    assert result is False
    assert 'SMTP error' in caplog.text


def test_smtp_email_service_handles_generic_exception(monkeypatch, caplog):
    class FailingSMTP:
        def __init__(self, *args, **kwargs):
            raise RuntimeError('Unexpected error')

    monkeypatch.setattr(
        'backend.services.email_service.smtplib.SMTP', FailingSMTP
    )

    service = SMTPEmailService()
    result = service.send('user@example.com', 'Test Subject', 'Test body')

    assert result is False
    assert 'Unexpected error' in caplog.text


def test_smtp_email_service_returns_true_on_success(monkeypatch):
    class SuccessSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            pass

        def login(self, username, password):
            pass

        def send_message(self, message):
            pass

    monkeypatch.setattr(
        'backend.services.email_service.smtplib.SMTP', SuccessSMTP
    )
    monkeypatch.setattr(settings, 'SMTP_USERNAME', 'smtp-user')
    monkeypatch.setattr(settings, 'SMTP_PASSWORD', 'smtp-pass')
    monkeypatch.setattr(settings, 'SMTP_USE_TLS', True)

    service = SMTPEmailService()
    result = service.send('user@example.com', 'Test Subject', 'Test body')

    assert result is True
