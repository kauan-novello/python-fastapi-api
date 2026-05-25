from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from backend.configs.permissions import can_manage_user
from backend.models.user_model import User
from backend.repositories.user_repository import UserRepository
from backend.schemas.user_schema import UserUpdate


class UpdateUserService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def execute(
        self,
        user_id: int,
        current_user: User,
        user_data: UserUpdate,
    ) -> User:
        if not can_manage_user(current_user, user_id):
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

        username = (
            user_data.username
            if user_data.username is not None
            else user_to_update.username
        )
        email = (
            str(user_data.email)
            if user_data.email is not None
            else user_to_update.email
        )

        if user_data.username is not None or user_data.email is not None:
            user_exists = await self.user_repository.find_by_username_or_email(
                username=username,
                email=email,
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
            ) from None

        if not user_updated:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail='User not found'
            )
        return user_updated
