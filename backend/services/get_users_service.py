from http import HTTPStatus

from fastapi import HTTPException


class GetUsersService:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    async def execute(self, skip: int = 0, limit: int = 100):
        users = await self.user_repository.get_all(skip=skip, limit=limit)
        return {'users': users}

    async def by_id(self, user_id: int):
        user = await self.user_repository.get_by_id(user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail='User not found'
            )
        return user
