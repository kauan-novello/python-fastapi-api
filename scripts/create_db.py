import asyncio

from backend.configs.database import engine
from backend.models.revoked_token import RevokedToken  # noqa: F401
from backend.models.user_model import table_registry


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.create_all)
    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
