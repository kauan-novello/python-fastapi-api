from typing import Annotated, TypeAlias

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from backend.configs.database import get_session
from backend.configs.security import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    oauth2_scheme,
)
from backend.models.user_model import User
from backend.repositories.token_repository import RevokedTokenRepository
from backend.repositories.user_repository import UserRepository
from backend.schemas.auth_schemas import (
    EmailRequest,
    ResetPasswordRequest,
    TokenOnlyRequest,
)
from backend.schemas.first_schema import Message
from backend.schemas.token_schema import Token
from backend.schemas.user_schema import UserCreate, UserPublic
from backend.services.create_user_service import CreateUserService
from backend.services.forgot_password_service import ForgotPasswordService
from backend.services.get_token_service import GetTokenService
from backend.services.logout_service import LogoutService
from backend.services.resend_verification_service import (
    ResendVerificationService,
)
from backend.services.reset_password_service import ResetPasswordService
from backend.services.verify_email_service import VerifyEmailService
from backend.utils.rate_limiter import (
    check_forgot_password_rate_limit,
    check_login_rate_limit,
    check_register_rate_limit,
    check_resend_verification_rate_limit,
    check_reset_password_rate_limit,
    check_verify_email_rate_limit,
)

router = APIRouter(prefix='/auth', tags=['auth'])

OAuth2Form: TypeAlias = Annotated[OAuth2PasswordRequestForm, Depends()]
SessionDB: TypeAlias = Annotated[AsyncSession, Depends(get_session)]

TokenAuth: TypeAlias = Annotated[str, Depends(oauth2_scheme)]

CurrentUser: TypeAlias = Annotated[User, Depends(get_current_user)]


@router.post('/token')
async def login_for_access_token(
    form_data: OAuth2Form,
    session: SessionDB,
    _check_rate_limit: Annotated[str, check_login_rate_limit],
) -> Token:
    service = GetTokenService(UserRepository(session), form_data=form_data)
    return await service.execute()


@router.post('/refresh_token')
async def refresh_access_token(
    session: SessionDB,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Token:
    user = await get_current_user(
        session=session,
        token=token,
        expected_token_type='refresh',
    )
    revoked_repo = RevokedTokenRepository(session)
    await revoked_repo.add(token=token)

    return Token(
        access_token=create_access_token(data={'sub': user.email}),
        refresh_token=create_refresh_token(data={'sub': user.email}),
        token_type='bearer',
    )


@router.get('/me', response_model=UserPublic)
async def read_me(current_user: CurrentUser) -> User:
    return current_user


@router.post('/register', response_model=UserPublic, status_code=201)
async def register(
    user: UserCreate,
    session: SessionDB,
    _check_rate_limit: Annotated[str, check_register_rate_limit],
) -> User:
    service = CreateUserService(UserRepository(session))
    return await service.execute(user)


@router.post('/logout')
async def logout(session: SessionDB, token: TokenAuth) -> Message:
    revoked_repo = RevokedTokenRepository(session)
    service = LogoutService(revoked_repo)
    return await service.execute(token=token, session=session)


@router.post('/forgot-password')
async def forgot_password(
    request: EmailRequest,
    session: SessionDB,
    _check_rate_limit: Annotated[str, check_forgot_password_rate_limit],
) -> Message:
    service = ForgotPasswordService(UserRepository(session))
    return await service.execute(request.email)


@router.post('/reset-password')
async def reset_password(
    body: ResetPasswordRequest,
    session: SessionDB,
    _check_rate_limit: Annotated[str, check_reset_password_rate_limit],
) -> Message:
    service = ResetPasswordService(UserRepository(session))
    return await service.execute(body)


@router.post('/verify-email')
async def verify_email(
    body: TokenOnlyRequest,
    session: SessionDB,
    _check_rate_limit: Annotated[str, check_verify_email_rate_limit],
) -> Message:
    service = VerifyEmailService(UserRepository(session))
    return await service.execute(body.token)


@router.post('/resend-verification')
async def resend_verification(
    request: EmailRequest,
    session: SessionDB,
    _check_rate_limit: Annotated[str, check_resend_verification_rate_limit],
) -> Message:
    service = ResendVerificationService(UserRepository(session))
    return await service.execute(request.email)
