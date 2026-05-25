from dataclasses import asdict
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from backend.configs.database import get_session
from backend.models.user_model import User
from backend.repositories.user_repository import UserRepository
from backend.schemas.user_schema import UserSchema, UserUpdate

TEST_USERS_COUNT = 3
ALICE_EMAIL = 'alice@example.com'
BOB_EMAIL = 'bob@example.com'
CREATED_USERS = 5
SKIP_AMOUNT = 2
LIMIT_AMOUNT = 2


@pytest.mark.asyncio
async def test_get_session_yields_session():
    session_generator = get_session()

    session = await anext(session_generator)

    assert session is not None

    await session_generator.aclose()


@pytest.mark.asyncio
async def test_create_user_db(session, mock_db_time):
    """Test creating user in database with timestamps"""
    with mock_db_time(model=User) as time:
        new_user = User(
            username='alice', password='Secret@123', email='teste@test'
        )
        session.add(new_user)
        await session.commit()

    user = await session.scalar(select(User).where(User.username == 'alice'))

    assert asdict(user) == {
        'id': 1,
        'username': 'alice',
        'password': 'Secret@123',
        'email': 'teste@test',
        'email_verified': False,
        'role': 'user',
        'created_at': time,
        'updated_at': time,
    }


async def test_repository_get_by_email_found(session):
    """Test get_by_email returns user when found"""
    repository = UserRepository(session)

    user_data = UserSchema(
        username='alice',
        email='alice@example.com',
        password='Secret@123',
    )
    created_user = await repository.create(user_data)

    found_user = await repository.get_by_email('alice@example.com')
    assert found_user is not None
    assert found_user.email == 'alice@example.com'
    assert found_user.id == created_user.id


async def test_repository_get_by_email_not_found(session):
    """Test get_by_email returns None when user not found"""
    repository = UserRepository(session)

    found_user = await repository.get_by_email('nonexistent@example.com')
    assert found_user is None


async def test_repository_get_by_id_found(session):
    """Test get_by_id returns user when found"""
    repository = UserRepository(session)

    user_data = UserSchema(
        username='alice',
        email='alice@example.com',
        password='Secret@123',
    )
    created_user = await repository.create(user_data)

    found_user = await repository.get_by_id(created_user.id)
    assert found_user is not None
    assert found_user.id == created_user.id
    assert found_user.username == 'alice'


async def test_repository_get_by_id_not_found(session):
    """Test get_by_id returns None when user not found"""
    repository = UserRepository(session)

    found_user = await repository.get_by_id(999)
    assert found_user is None


async def test_repository_find_by_username_or_email_by_username(session):
    """Test find_by_username_or_email returns user by username"""
    repository = UserRepository(session)

    user_data = UserSchema(
        username='alice',
        email=ALICE_EMAIL,
        password='Secret@123',
    )
    await repository.create(user_data)

    found_user = await repository.find_by_username_or_email(
        username='alice', email='nonexistent@example.com'
    )
    assert found_user is not None
    assert found_user.username == 'alice'


async def test_repository_find_by_username_or_email_by_email(session):
    """Test find_by_username_or_email returns user by email"""
    repository = UserRepository(session)

    user_data = UserSchema(
        username='alice',
        email=ALICE_EMAIL,
        password='Secret@123',
    )
    await repository.create(user_data)

    found_user = await repository.find_by_username_or_email(
        username='nonexistent', email=ALICE_EMAIL
    )
    assert found_user is not None
    assert found_user.email == ALICE_EMAIL


async def test_repository_find_by_username_or_email_not_found(session):
    """Test find_by_username_or_email returns None when not found"""
    repository = UserRepository(session)

    found_user = await repository.find_by_username_or_email(
        username='nonexistent', email='nonexistent@example.com'
    )
    assert found_user is None


async def test_repository_get_all_empty(session):
    """Test get_all returns empty list when no users"""
    repository = UserRepository(session)

    users = await repository.get_all()
    assert users == []


async def test_repository_get_all_with_users(session):
    """Test get_all returns all users"""
    repository = UserRepository(session)

    for i in range(TEST_USERS_COUNT):
        user_data = UserSchema(
            username=f'user{i}',
            email=f'user{i}@example.com',
            password='Secret@123',
        )
        await repository.create(user_data)

    users = await repository.get_all()
    assert len(users) == TEST_USERS_COUNT


async def test_repository_get_all_with_pagination(session):
    """Test get_all respects skip and limit parameters"""
    repository = UserRepository(session)

    for i in range(CREATED_USERS):
        user_data = UserSchema(
            username=f'user{i}',
            email=f'user{i}@example.com',
            password='Secret@123',
        )
        await repository.create(user_data)

    users = await repository.get_all(skip=SKIP_AMOUNT, limit=100)
    assert len(users) == TEST_USERS_COUNT

    users = await repository.get_all(skip=0, limit=LIMIT_AMOUNT)
    assert len(users) == LIMIT_AMOUNT

    users = await repository.get_all(skip=1, limit=LIMIT_AMOUNT)
    assert len(users) == LIMIT_AMOUNT


async def test_repository_update_success(session):
    """Test update modifies user data"""
    repository = UserRepository(session)

    user_data = UserSchema(
        username='alice',
        email='alice@example.com',
        password='Secret@123',
    )
    created_user = await repository.create(user_data)

    updated_data = UserUpdate(
        username='bob',
        email='bob@example.com',
        password='NewPass@456',
    )
    updated_user = await repository.update(created_user.id, updated_data)

    assert updated_user is not None
    assert updated_user.username == 'bob'
    assert updated_user.email == 'bob@example.com'
    assert updated_user.id == created_user.id


async def test_repository_update_user_not_found(session):
    """Test update returns None when user not found"""
    repository = UserRepository(session)

    update_data = UserUpdate(
        username='bob',
        email='bob@example.com',
        password='NewPass@456',
    )
    result = await repository.update(999, update_data)

    assert result is None


async def test_repository_update_integrity_error(session):
    """Test update raises IntegrityError on duplicate email"""
    repository = UserRepository(session)

    user1_data = UserSchema(
        username='alice',
        email=ALICE_EMAIL,
        password='Secret@123',
    )
    user1 = await repository.create(user1_data)

    user2_data = UserSchema(
        username='bob',
        email=BOB_EMAIL,
        password='Secret@123',
    )
    await repository.create(user2_data)

    update_data = UserUpdate(
        username='alice_updated',
        email=BOB_EMAIL,
        password='NewPass@456',
    )

    with pytest.raises(IntegrityError):
        await repository.update(user1.id, update_data)


@pytest.mark.asyncio
async def test_create_rollback_on_integrity_error(session):
    repository = UserRepository(session)
    user_data = UserSchema(
        username='alice',
        email='alice@example.com',
        password='Secret@123',
    )

    rollback_spy = AsyncMock()
    commit_spy = AsyncMock(
        side_effect=IntegrityError(
            'statement', {'email': user_data.email}, Exception('boom')
        )
    )
    session.rollback = rollback_spy
    session.commit = commit_spy

    with pytest.raises(IntegrityError):
        await repository.create(user_data)

    rollback_spy.assert_called_once()
    commit_spy.assert_called_once()
