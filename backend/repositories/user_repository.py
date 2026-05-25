from typing import Any, cast

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select

from backend.configs.security import get_password_hash
from backend.models.user_model import User
from backend.schemas.user_schema import UserCreate, UserUpdate


def _apply_user_search(
    query: Select[Any],
    search: str | None,
) -> Select[Any]:
    if not search:
        return query
    pattern = f'%{search.strip()}%'
    return query.where(
        or_(
            User.username.ilike(pattern),
            User.email.ilike(pattern),
        )
    )


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        return cast(
            User | None,
            await self.session.scalar(select(User).where(User.email == email)),
        )

    async def find_by_username_or_email(
        self,
        username: str,
        email: str,
    ) -> User | None:
        return cast(
            User | None,
            await self.session.scalar(
                select(User).where(
                    (User.username == username) | (User.email == email)
                )
            ),
        )

    async def create(self, user_data: UserCreate) -> User:
        user = User(
            username=user_data.username,
            email=user_data.email,
            password=get_password_hash(user_data.password),
        )

        self.session.add(user)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
        await self.session.refresh(user)

        return user

    async def count_all(self, search: str | None = None) -> int:
        query = select(func.count()).select_from(User)
        query = _apply_user_search(query, search)
        result = await self.session.scalar(query)
        return int(result or 0)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
    ) -> list[User]:
        query = select(User).offset(skip).limit(limit)
        query = _apply_user_search(query, search)
        result = await self.session.scalars(query)
        return list(result.all())

    async def get_by_id(self, user_id: int) -> User | None:
        return cast(
            User | None,
            await self.session.scalar(select(User).where(User.id == user_id)),
        )

    async def update(self, user_id: int, user_data: UserUpdate) -> User | None:
        user = await self.get_by_id(user_id)

        if not user:
            return None

        if user_data.username is not None:
            user.username = user_data.username
        if user_data.email is not None:
            user.email = str(user_data.email)
        if user_data.password is not None:
            user.password = get_password_hash(user_data.password)

        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
        await self.session.refresh(user)

        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.commit()

    async def mark_email_verified(self, user: User) -> User:
        user.email_verified = True
        await self.session.commit()
        await self.session.refresh(user)

        return user
