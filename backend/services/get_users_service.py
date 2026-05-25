from http import HTTPStatus

from fastapi import HTTPException

from backend.configs.permissions import is_admin
from backend.models.user_model import User
from backend.repositories.user_repository import UserRepository
from backend.schemas.user_schema import UserList, UserPublic


class GetUsersService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def execute(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
    ) -> UserList:
        if not is_admin(current_user):
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='Not enough permissions',
            )

        users = await self.user_repository.get_all(
            skip=skip,
            limit=limit,
            search=search,
        )
        total = await self.user_repository.count_all(search=search)
        return UserList(
            users=[UserPublic.model_validate(user) for user in users],
            total=total,
            offset=skip,
            limit=limit,
        )

    async def by_id(self, user_id: int, current_user: User) -> User:
        if not is_admin(current_user) and current_user.id != user_id:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='Not enough permissions',
            )

        user = await self.user_repository.get_by_id(user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail='User not found'
            )
        return user
