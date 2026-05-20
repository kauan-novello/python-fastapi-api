from http import HTTPStatus

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.controllers.auth_controller import router as auth_router
from backend.controllers.user_controller import router as user_router
from backend.schemas.first_schema import Message

app = FastAPI(
    title='FastAPI Boilerplate API',
    version='1.0.0',
    description=(
        'Boilerplate de API com FastAPI, JWT, SQLAlchemy async e Alembic.'
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(user_router)
app.include_router(auth_router)


@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
async def read_root():
    return {'message': 'FastAPI boilerplate running.'}


@app.get('/health', status_code=HTTPStatus.OK)
async def health_check():
    return {'status': 'ok'}
