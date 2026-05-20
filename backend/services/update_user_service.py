from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from backend.models.user_model import User
from backend.schemas.user_schema import UserUpdate


class UpdateUserService:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    async def execute(
        self,
        user_id: int,
        current_user: User,
        user_data: UserUpdate,
    ):
        if current_user.id != user_id:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='Not enough permissions',
            )

        user_to_update = await self.user_repository.get_by_id(user_id)
        if not user_to_update:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='User not found',
            )

        user_exists = await self.user_repository.find_by_username_or_email(
            username=user_data.username,
            email=user_data.email,
        )

        if user_exists and user_exists.id != user_id:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Username or Email already exists',
            )

        try:
            user_updated = await self.user_repository.update(
                user_id, user_data
            )
        except IntegrityError:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Username or Email already exists',
            )

        if not user_updated:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail='User not found'
            )
        return user_updated
