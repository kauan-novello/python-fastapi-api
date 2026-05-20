from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.configs.security import get_password_hash
from backend.models.user_model import User
from backend.schemas.user_schema import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str):
        return await self.session.scalar(
            select(User).where(User.email == email)
        )

    async def find_by_username_or_email(
        self,
        username: str,
        email: str,
    ):
        return await self.session.scalar(
            select(User).where(
                (User.username == username) | (User.email == email)
            )
        )

    async def create(self, user_data: UserCreate):
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

    async def get_all(self, skip: int = 0, limit: int = 100):
        result = await self.session.scalars(
            select(User).offset(skip).limit(limit)
        )
        return result.all()

    async def get_by_id(self, user_id: int):
        return await self.session.scalar(
            select(User).where(User.id == user_id)
        )

    async def update(self, user_id: int, user_data: UserUpdate):
        user = await self.get_by_id(user_id)

        if not user:
            return None

        user.username = user_data.username
        user.email = user_data.email
        user.password = get_password_hash(user_data.password)

        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise
        await self.session.refresh(user)

        return user

    async def delete(self, user: User):
        await self.session.delete(user)
        await self.session.commit()
