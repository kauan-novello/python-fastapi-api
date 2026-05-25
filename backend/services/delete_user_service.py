from http import HTTPStatus

from fastapi import HTTPException

from backend.configs.permissions import can_manage_user
from backend.models.user_model import User
from backend.repositories.user_repository import UserRepository
from backend.schemas.first_schema import Message


class DeleteUserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def execute(self, user_id: int, current_user: User) -> Message:
        if not can_manage_user(current_user, user_id):
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='Not enough permissions',
            )

        user = await self.repository.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail='User not found'
            )

        await self.repository.delete(user)

        return Message(message='User deleted')
