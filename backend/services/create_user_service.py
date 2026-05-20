from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from backend.schemas.user_schema import UserCreate


class CreateUserService:
    def __init__(self, user_repository):
        self.user_repository = user_repository

    async def execute(self, user_data: UserCreate):
        user_exists = await self.user_repository.find_by_username_or_email(
            username=user_data.username,
            email=user_data.email,
        )

        if user_exists:
            if user_exists.username == user_data.username:
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail='Username already exists',
                )

            if user_exists.email == user_data.email:
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail='Email already exists',
                )

        try:
            user = await self.user_repository.create(user_data)
        except IntegrityError:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Username or Email already exists',
            )

        return user
