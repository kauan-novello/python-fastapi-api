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
from backend.repositories.user_repository import UserRepository
from backend.schemas.token_schema import Token
from backend.services.get_token_service import GetTokenService

router = APIRouter(prefix='/auth', tags=['auth'])

OAuth2Form: TypeAlias = Annotated[OAuth2PasswordRequestForm, Depends()]
SessionDB: TypeAlias = Annotated[AsyncSession, Depends(get_session)]

CurrentUser: TypeAlias = Annotated[User, Depends(get_current_user)]


@router.post('/token', response_model=Token)
async def login_for_access_token(form_data: OAuth2Form, session: SessionDB):
    service = GetTokenService(UserRepository(session), form_data=form_data)
    return await service.execute()


@router.post('/refresh_token', response_model=Token)
async def refresh_access_token(
    session: SessionDB,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    user = await get_current_user(
        session=session,
        token=token,
        expected_token_type='refresh',
    )
    new_access_token = create_access_token(data={'sub': user.email})
    new_refresh_token = create_refresh_token(data={'sub': user.email})

    return {
        'access_token': new_access_token,
        'refresh_token': new_refresh_token,
        'token_type': 'bearer',
    }
