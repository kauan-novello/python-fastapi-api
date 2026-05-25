from http import HTTPStatus

import pytest
from fastapi import HTTPException

from backend.configs.security import create_access_token
from backend.repositories.token_repository import RevokedTokenRepository
from backend.repositories.user_repository import UserRepository
from backend.services.forgot_password_service import ForgotPasswordService
from backend.services.logout_service import LogoutService
from backend.services.resend_verification_service import (
    ResendVerificationService,
)
from backend.services.reset_password_service import ResetPasswordService
from backend.services.verify_email_service import VerifyEmailService


class FakeEmailService:
    def __init__(self):
        self.password_reset_calls = []
        self.verification_calls = []

    def send_password_reset(self, recipient, token):
        self.password_reset_calls.append((recipient, token))

    def send_verification(self, recipient, token):
        self.verification_calls.append((recipient, token))


async def test_forgot_password_service_user_exists(session, user):
    """Test forgot_password returns reset token when user exists"""
    email_service = FakeEmailService()
    service = ForgotPasswordService(UserRepository(session), email_service)
    result = await service.execute(user.email)
    assert result.model_dump() == {
        'message': 'If the email exists, a reset link was sent.'
    }
    assert len(email_service.password_reset_calls) == 1
    assert email_service.password_reset_calls[0][0] == user.email


async def test_forgot_password_service_user_not_found(session):
    """Test forgot_password returns safe message for non-existent user"""
    service = ForgotPasswordService(UserRepository(session))
    result = await service.execute('nonexistent@example.com')
    assert result.model_dump() == {
        'message': 'If the email exists, a reset link was sent.'
    }


async def test_logout_service_revokes_token(session, user):
    """Test logout_service adds token to revoked list"""
    token = create_access_token({'sub': user.email})
    revoked_repo = RevokedTokenRepository(session)
    service = LogoutService(revoked_repo)

    result = await service.execute(token, session)

    assert result.model_dump() == {'message': 'logged out'}
    assert await revoked_repo.is_revoked(token)


async def test_logout_service_invalid_token(session):
    """Test logout_service handles invalid token gracefully"""
    revoked_repo = RevokedTokenRepository(session)
    service = LogoutService(revoked_repo)

    result = await service.execute('invalid-token', session)

    assert result.model_dump() == {'message': 'logged out'}


async def test_reset_password_service_success(session, user):
    """Test reset_password_service successfully resets password"""
    reset_token = create_access_token(
        {'sub': user.email},
        token_type='reset',
    )
    body_mock = type(
        'obj',
        (object,),
        {
            'token': reset_token,
            'new_password': 'NewPass@123',
        },
    )()

    service = ResetPasswordService(UserRepository(session))
    result = await service.execute(body_mock)

    assert result.model_dump() == {'message': 'password reset successful'}


async def test_reset_password_service_invalid_token(session):
    """Test reset_password_service raises for invalid token"""
    body_mock = type(
        'obj',
        (object,),
        {
            'token': 'invalid-token',
            'new_password': 'NewPass@123',
        },
    )()

    service = ResetPasswordService(UserRepository(session))

    with pytest.raises(HTTPException) as exc:
        await service.execute(body_mock)

    assert exc.value.status_code == HTTPStatus.BAD_REQUEST


async def test_reset_password_service_wrong_token_type(session):
    """Test reset_password_service raises for wrong token type"""
    access_token = create_access_token({'sub': 'test@example.com'})
    body_mock = type(
        'obj',
        (object,),
        {
            'token': access_token,
            'new_password': 'newpassword123',
        },
    )()

    service = ResetPasswordService(UserRepository(session))

    with pytest.raises(HTTPException) as exc:
        await service.execute(body_mock)

    assert exc.value.status_code == HTTPStatus.BAD_REQUEST
    assert exc.value.detail == 'Invalid token type'


async def test_reset_password_service_user_not_found(session):
    """Test reset_password_service raises when user not found"""
    reset_token = create_access_token(
        {'sub': 'nonexistent@example.com'},
        token_type='reset',
    )
    body_mock = type(
        'obj',
        (object,),
        {
            'token': reset_token,
            'new_password': 'newpassword123',
        },
    )()

    service = ResetPasswordService(UserRepository(session))

    with pytest.raises(HTTPException) as exc:
        await service.execute(body_mock)

    assert exc.value.status_code == HTTPStatus.BAD_REQUEST


async def test_verify_email_service_success(session, user):
    """Test verify_email_service accepts valid verify token"""
    service = VerifyEmailService(UserRepository(session))
    verify_token = create_access_token(
        {'sub': user.email},
        token_type='verify',
    )

    result = await service.execute(verify_token)

    assert result.model_dump() == {'message': 'email verified'}


async def test_verify_email_service_marks_user_verified(session, user):
    """Test verify_email_service persists the verified flag"""
    verify_token = create_access_token(
        {'sub': user.email},
        token_type='verify',
    )

    service = VerifyEmailService(UserRepository(session))
    result = await service.execute(verify_token)

    refreshed = await UserRepository(session).get_by_email(user.email)
    assert result.model_dump() == {'message': 'email verified'}
    assert refreshed.email_verified is True


async def test_verify_email_service_invalid_token(session):
    """Test verify_email_service raises for invalid token"""
    service = VerifyEmailService(UserRepository(session))

    with pytest.raises(HTTPException) as exc:
        await service.execute('invalid-token')

    assert exc.value.status_code == HTTPStatus.BAD_REQUEST


async def test_verify_email_service_wrong_token_type(session):
    """Test verify_email_service raises for wrong token type"""
    access_token = create_access_token({'sub': 'test@example.com'})
    service = VerifyEmailService(UserRepository(session))

    with pytest.raises(HTTPException) as exc:
        await service.execute(access_token)

    assert exc.value.status_code == HTTPStatus.BAD_REQUEST
    assert exc.value.detail == 'Invalid token type'


async def test_verify_email_service_missing_subject(session):
    """Test verify_email_service raises when token lacks subject"""
    token_without_sub = create_access_token({}, token_type='verify')
    service = VerifyEmailService(UserRepository(session))

    with pytest.raises(HTTPException) as exc:
        await service.execute(token_without_sub)

    assert exc.value.status_code == HTTPStatus.BAD_REQUEST
    assert exc.value.detail == 'Invalid token'


async def test_verify_email_service_user_not_found(session):
    """Test verify_email_service raises when user does not exist"""
    verify_token = create_access_token(
        {'sub': 'missing@example.com'},
        token_type='verify',
    )
    service = VerifyEmailService(UserRepository(session))

    with pytest.raises(HTTPException) as exc:
        await service.execute(verify_token)

    assert exc.value.status_code == HTTPStatus.BAD_REQUEST
    assert exc.value.detail == 'Invalid token'


async def test_resend_verification_service_user_exists(
    session, unverified_user
):
    """Test resend_verification returns verify token when user exists"""
    email_service = FakeEmailService()
    service = ResendVerificationService(UserRepository(session), email_service)
    result = await service.execute(unverified_user.email)

    assert result.model_dump() == {
        'message': 'If the account exists, verification was resent.'
    }
    assert len(email_service.verification_calls) == 1
    assert email_service.verification_calls[0][0] == unverified_user.email


async def test_resend_verification_service_user_not_found(session):
    """Test resend_verification returns safe message for non-existent user"""
    service = ResendVerificationService(UserRepository(session))
    result = await service.execute('nonexistent@example.com')

    assert result.model_dump() == {
        'message': 'If the account exists, verification was resent.'
    }


async def test_resend_verification_service_user_already_verified(
    session, user
):
    """Test resend_verification does not resend already verified users"""
    user.email_verified = True
    await session.commit()

    email_service = FakeEmailService()
    service = ResendVerificationService(UserRepository(session), email_service)
    result = await service.execute(user.email)

    assert result.model_dump() == {
        'message': 'If the account exists, verification was resent.'
    }
    assert email_service.verification_calls == []
