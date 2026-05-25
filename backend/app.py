from http import HTTPStatus

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.configs.health import check_database
from backend.configs.lifespan import lifespan
from backend.configs.settings import Settings
from backend.controllers.auth_controller import router as auth_router
from backend.controllers.user_controller import router as user_router
from backend.schemas.first_schema import Message

settings = Settings()

app = FastAPI(
    title='FastAPI Boilerplate API',
    version='1.0.0',
    description=(
        'Boilerplate de API com FastAPI, JWT, SQLAlchemy async e Alembic.'
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allow_headers=['*'],
)

app.include_router(user_router)
app.include_router(auth_router)


@app.get('/', status_code=HTTPStatus.OK)
async def read_root() -> Message:
    return Message(message='FastAPI boilerplate running.')


@app.get('/health', status_code=HTTPStatus.OK)
async def health_check() -> dict[str, str]:
    database_ok = await check_database()
    status_value = 'ok' if database_ok else 'degraded'
    return {
        'status': status_value,
        'database': 'ok' if database_ok else 'error',
    }
