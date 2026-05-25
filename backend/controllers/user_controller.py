from typing import Annotated, TypeAlias

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.configs.database import get_session
from backend.configs.security import get_current_user
from backend.models.user_model import User
from backend.repositories.user_repository import UserRepository
from backend.schemas.filters_schemas import FilterPage
from backend.schemas.first_schema import Message
from backend.schemas.user_schema import (
    UserList,
    UserPublic,
    UserUpdate,
)
from backend.services.delete_user_service import DeleteUserService
from backend.services.get_users_service import GetUsersService
from backend.services.update_user_service import UpdateUserService

router = APIRouter(prefix='/users', tags=['users'])
SessionDB: TypeAlias = Annotated[AsyncSession, Depends(get_session)]
CurrentUser: TypeAlias = Annotated[User, Depends(get_current_user)]
FilterUsers: TypeAlias = Annotated[FilterPage, Query()]


@router.get('/')
async def get_users(
    session: SessionDB,
    filters: FilterUsers,
    current_user: CurrentUser,
) -> UserList:
    service = GetUsersService(UserRepository(session))
    return await service.execute(
        current_user=current_user,
        skip=filters.offset,
        limit=filters.limit,
        search=filters.search,
    )


@router.put('/{user_id}', response_model=UserPublic)
async def update_user(
    user_id: int,
    user: UserUpdate,
    session: SessionDB,
    current_user: CurrentUser,
) -> User:
    service = UpdateUserService(UserRepository(session))
    return await service.execute(
        user_id=user_id,
        user_data=user,
        current_user=current_user,
    )


@router.delete('/{user_id}')
async def delete_user(
    user_id: int,
    session: SessionDB,
    current_user: CurrentUser,
) -> Message:
    service = DeleteUserService(UserRepository(session))
    return await service.execute(user_id=user_id, current_user=current_user)


@router.get('/{user_id}', response_model=UserPublic)
async def get_user_by_id(
    user_id: int,
    session: SessionDB,
    current_user: CurrentUser,
) -> User:
    service = GetUsersService(UserRepository(session))
    return await service.by_id(
        user_id=user_id,
        current_user=current_user,
    )
