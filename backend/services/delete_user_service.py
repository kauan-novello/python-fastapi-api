from http import HTTPStatus

from fastapi import HTTPException

from backend.models.user_model import User
from backend.repositories.user_repository import UserRepository


class DeleteUserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def execute(self, user_id: int, current_user: User):
        if current_user.id != user_id:
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

        return {'message': 'User deleted'}
