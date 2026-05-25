from contextlib import contextmanager
from datetime import datetime
from email.message import EmailMessage

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from backend.app import app
from backend.configs.database import get_session
from backend.configs.security import create_access_token, get_password_hash
from backend.models.user_model import table_registry
from backend.utils.rate_limiter import (
    forgot_password_limiter,
    login_limiter,
    register_limiter,
    resend_verification_limiter,
    reset_password_limiter,
    verify_email_limiter,
)

from .user.user_factory import UserFactory

MAIL_OUTBOX: list[EmailMessage] = []


@pytest.fixture(autouse=True)
def clear_rate_limiters():
    register_limiter.clear()
    login_limiter.clear()
    forgot_password_limiter.clear()
    reset_password_limiter.clear()
    verify_email_limiter.clear()
    resend_verification_limiter.clear()


@pytest.fixture(autouse=True)
def mock_smtp(monkeypatch):
    MAIL_OUTBOX.clear()

    class DummySMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        @staticmethod
        def starttls():
            return None

        @staticmethod
        def login(username, password):
            return None

        @staticmethod
        def send_message(message):
            MAIL_OUTBOX.append(message)

    monkeypatch.setattr('smtplib.SMTP', DummySMTP)
    yield
    MAIL_OUTBOX.clear()


@pytest.fixture
def mail_outbox():
    return MAIL_OUTBOX


@pytest.fixture
def client(session):
    def get_session_override():
        return session

    with TestClient(app) as client:
        app.dependency_overrides[get_session] = get_session_override
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        'sqlite+aiosqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(table_registry.metadata.drop_all)


@pytest_asyncio.fixture
async def user(session):
    password = 'TestPass@123'
    user = UserFactory(password=get_password_hash(password))
    user.email_verified = True
    session.add(user)
    await session.commit()
    await session.refresh(user)

    user.clean_password = password

    return user


@pytest.fixture
def token(user):
    return create_access_token({'sub': user.email})


@pytest_asyncio.fixture
async def unverified_user(session):
    password = 'TestPass@123'
    user = UserFactory(password=get_password_hash(password))
    session.add(user)
    await session.commit()
    await session.refresh(user)

    user.clean_password = password

    return user


@pytest_asyncio.fixture
async def admin_user(session):
    password = 'TestPass@123'
    user = UserFactory(password=get_password_hash(password))
    user.email_verified = True
    user.role = 'admin'
    session.add(user)
    await session.commit()
    await session.refresh(user)

    user.clean_password = password

    return user


@pytest_asyncio.fixture
async def other_user(session):
    password = 'TestPass@123'
    user = UserFactory(password=get_password_hash(password))
    user.email_verified = True

    session.add(user)
    await session.commit()
    await session.refresh(user)

    user.clean_password = password

    return user


@contextmanager
def _mock_db_time(*, model, time=datetime(2024, 1, 1)):

    def fake_time_hook(mapper, connection, target):
        if hasattr(target, 'created_at'):
            target.created_at = time
        if hasattr(target, 'updated_at'):
            target.updated_at = time

    event.listen(model, 'before_insert', fake_time_hook)

    yield time

    event.remove(model, 'before_insert', fake_time_hook)


@pytest.fixture
def mock_db_time():
    return _mock_db_time
