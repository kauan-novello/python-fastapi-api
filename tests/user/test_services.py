from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from backend.configs.security import get_password_hash
from backend.schemas.user_schema import UserSchema
from backend.services.create_user_service import CreateUserService
from backend.services.delete_user_service import DeleteUserService
from backend.services.get_token_service import GetTokenService
from backend.services.get_users_service import GetUsersService
from backend.services.update_user_service import UpdateUserService

ALICE_EMAIL = 'alice@example.com'
BOB_EMAIL = 'bob@example.com'
CHARLIE_EMAIL = 'charlie@example.com'
TEST_PASSWORD = 'secret'
NEW_PASSWORD = 'newsecret'
TEST_USERNAME = 'alice'
BOB_USERNAME = 'bob'


def _build_user_data():
    return UserSchema(
        username='alice',
        email='alice@example.com',
        password='secret',
    )


@pytest.mark.asyncio
async def test_create_user_service_success():
    user_repository = Mock()
    user_repository.find_by_username_or_email = AsyncMock(return_value=None)
    expected_user = SimpleNamespace(
        id=1,
        username='alice',
        email='alice@example.com',
    )
    user_repository.create = AsyncMock(return_value=expected_user)

    service = CreateUserService(user_repository)

    user = await service.execute(_build_user_data())

    assert user is expected_user
    user_repository.find_by_username_or_email.assert_called_once_with(
        username='alice',
        email='alice@example.com',
    )
    user_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_service_username_conflict():
    user_repository = Mock()
    user_repository.find_by_username_or_email = AsyncMock(
        return_value=SimpleNamespace(
            username='alice',
            email='another@example.com',
        )
    )

    service = CreateUserService(user_repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.execute(_build_user_data())

    assert exc_info.value.status_code == HTTPStatus.CONFLICT
    assert exc_info.value.detail == 'Username already exists'
    user_repository.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_user_service_email_conflict():
    user_repository = Mock()
    user_repository.find_by_username_or_email = AsyncMock(
        return_value=SimpleNamespace(
            username='another',
            email='alice@example.com',
        )
    )

    service = CreateUserService(user_repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.execute(_build_user_data())

    assert exc_info.value.status_code == HTTPStatus.CONFLICT
    assert exc_info.value.detail == 'Email already exists'
    user_repository.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_user_service_integrity_error():
    user_repository = Mock()
    user_repository.find_by_username_or_email = AsyncMock(return_value=None)
    user_repository.create = AsyncMock(
        side_effect=IntegrityError(
            'statement', {'username': 'alice'}, Exception('original error')
        )
    )

    service = CreateUserService(user_repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.execute(_build_user_data())

    assert exc_info.value.status_code == HTTPStatus.CONFLICT
    assert exc_info.value.detail == 'Username or Email already exists'


@pytest.mark.asyncio
async def test_get_token_service_success():
    """Test GetTokenService succeeds with correct credentials"""
    user_repository = Mock()
    correct_password = TEST_PASSWORD
    user = SimpleNamespace(
        id=1,
        username=TEST_USERNAME,
        email=ALICE_EMAIL,
        password=get_password_hash(correct_password),
    )
    user_repository.get_by_email = AsyncMock(return_value=user)

    form_data = SimpleNamespace(
        username=ALICE_EMAIL,
        password=correct_password,
    )

    service = GetTokenService(user_repository, form_data)
    token = await service.execute()

    assert token['token_type'] == 'bearer'
    assert 'access_token' in token
    assert 'refresh_token' in token
    user_repository.get_by_email.assert_called_once_with(ALICE_EMAIL)


@pytest.mark.asyncio
async def test_get_token_service_user_not_found():
    """Test GetTokenService raises 401 when user not found"""
    user_repository = Mock()
    user_repository.get_by_email = AsyncMock(return_value=None)

    form_data = SimpleNamespace(
        username='nonexistent@example.com',
        password=TEST_PASSWORD,
    )

    service = GetTokenService(user_repository, form_data)

    with pytest.raises(HTTPException) as exc_info:
        await service.execute()

    assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED
    assert exc_info.value.detail == 'Incorrect email or password'


@pytest.mark.asyncio
async def test_get_token_service_wrong_password():
    """Test GetTokenService raises 401 when password is wrong"""
    user_repository = Mock()
    user = SimpleNamespace(
        id=1,
        username=TEST_USERNAME,
        email=ALICE_EMAIL,
        password=get_password_hash('correctpassword'),
    )
    user_repository.get_by_email = AsyncMock(return_value=user)

    form_data = SimpleNamespace(
        username=ALICE_EMAIL,
        password='wrongpassword',
    )

    service = GetTokenService(user_repository, form_data)

    with pytest.raises(HTTPException) as exc_info:
        await service.execute()

    assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED
    assert exc_info.value.detail == 'Incorrect email or password'


@pytest.mark.asyncio
async def test_delete_user_service_success(session):
    """Test DeleteUserService successfully deletes user"""
    repository = Mock()
    current_user = SimpleNamespace(
        id=1, username=TEST_USERNAME, email=ALICE_EMAIL
    )
    user_to_delete = SimpleNamespace(
        id=1, username=TEST_USERNAME, email=ALICE_EMAIL
    )

    repository.get_by_id = AsyncMock(return_value=user_to_delete)
    repository.delete = AsyncMock()

    service = DeleteUserService(repository)
    result = await service.execute(user_id=1, current_user=current_user)

    assert result == {'message': 'User deleted'}
    repository.get_by_id.assert_called_once_with(1)
    repository.delete.assert_called_once_with(user_to_delete)


@pytest.mark.asyncio
async def test_delete_user_service_not_enough_permissions():
    """Test DeleteUserService raises 403 on cross-user delete"""
    repository = Mock()
    current_user = SimpleNamespace(
        id=1, username=TEST_USERNAME, email=ALICE_EMAIL
    )

    service = DeleteUserService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.execute(user_id=2, current_user=current_user)

    assert exc_info.value.status_code == HTTPStatus.FORBIDDEN
    assert exc_info.value.detail == 'Not enough permissions'
    repository.get_by_id.assert_not_called()


@pytest.mark.asyncio
async def test_delete_user_service_user_not_found():
    """Test DeleteUserService raises 404 when user to delete not found"""
    repository = Mock()
    current_user = SimpleNamespace(
        id=1, username=TEST_USERNAME, email=ALICE_EMAIL
    )

    repository.get_by_id = AsyncMock(return_value=None)

    service = DeleteUserService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.execute(user_id=1, current_user=current_user)

    assert exc_info.value.status_code == HTTPStatus.NOT_FOUND
    assert exc_info.value.detail == 'User not found'
    repository.delete.assert_not_called()


@pytest.mark.asyncio
async def test_get_users_service_execute_no_params():
    """Test GetUsersService.execute with default parameters"""
    repository = Mock()
    users = [
        SimpleNamespace(id=1, username=TEST_USERNAME, email=ALICE_EMAIL),
        SimpleNamespace(id=2, username=BOB_USERNAME, email=BOB_EMAIL),
    ]
    repository.get_all = AsyncMock(return_value=users)

    service = GetUsersService(repository)
    result = await service.execute()

    assert result == {'users': users}
    repository.get_all.assert_called_once_with(skip=0, limit=100)


@pytest.mark.asyncio
async def test_get_users_service_execute_with_pagination():
    """Test GetUsersService.execute respects skip and limit"""
    repository = Mock()
    users = [
        SimpleNamespace(id=2, username=BOB_USERNAME, email=BOB_EMAIL),
        SimpleNamespace(id=3, username='charlie', email=CHARLIE_EMAIL),
    ]
    repository.get_all = AsyncMock(return_value=users)

    service = GetUsersService(repository)
    result = await service.execute(skip=1, limit=2)

    assert result == {'users': users}
    repository.get_all.assert_called_once_with(skip=1, limit=2)


@pytest.mark.asyncio
async def test_get_users_service_by_id_success():
    """Test GetUsersService.by_id returns user when found"""
    repository = Mock()
    user = SimpleNamespace(id=1, username=TEST_USERNAME, email=ALICE_EMAIL)
    repository.get_by_id = AsyncMock(return_value=user)

    service = GetUsersService(repository)
    result = await service.by_id(user_id=1)

    assert result == user
    repository.get_by_id.assert_called_once_with(user_id=1)


@pytest.mark.asyncio
async def test_get_users_service_by_id_not_found():
    """Test GetUsersService.by_id raises 404 when user not found"""
    repository = Mock()
    repository.get_by_id = AsyncMock(return_value=None)

    service = GetUsersService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.by_id(user_id=999)

    assert exc_info.value.status_code == HTTPStatus.NOT_FOUND
    assert exc_info.value.detail == 'User not found'


@pytest.mark.asyncio
async def test_update_user_service_success():
    """Test UpdateUserService successfully updates user"""
    repository = Mock()
    current_user = SimpleNamespace(
        id=1, username=TEST_USERNAME, email=ALICE_EMAIL
    )
    user_to_update = SimpleNamespace(
        id=1, username=TEST_USERNAME, email=ALICE_EMAIL
    )
    updated_user = SimpleNamespace(
        id=1, username=BOB_USERNAME, email=BOB_EMAIL
    )

    repository.get_by_id = AsyncMock(return_value=user_to_update)
    repository.find_by_username_or_email = AsyncMock(return_value=None)
    repository.update = AsyncMock(return_value=updated_user)

    update_data = UserSchema(
        username=BOB_USERNAME,
        email=BOB_EMAIL,
        password=NEW_PASSWORD,
    )

    service = UpdateUserService(repository)
    result = await service.execute(
        user_id=1,
        current_user=current_user,
        user_data=update_data,
    )

    assert result == updated_user


@pytest.mark.asyncio
async def test_update_user_service_not_enough_permissions():
    """Test UpdateUserService raises 403 on cross-user update"""
    repository = Mock()
    current_user = SimpleNamespace(
        id=1, username=TEST_USERNAME, email=ALICE_EMAIL
    )

    update_data = UserSchema(
        username=BOB_USERNAME,
        email=BOB_EMAIL,
        password=NEW_PASSWORD,
    )

    service = UpdateUserService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.execute(
            user_id=2,
            current_user=current_user,
            user_data=update_data,
        )

    assert exc_info.value.status_code == HTTPStatus.FORBIDDEN
    assert exc_info.value.detail == 'Not enough permissions'


@pytest.mark.asyncio
async def test_update_user_service_user_not_found():
    """Test UpdateUserService raises 404 when user not found"""
    repository = Mock()
    current_user = SimpleNamespace(
        id=1, username=TEST_USERNAME, email=ALICE_EMAIL
    )

    repository.get_by_id = AsyncMock(return_value=None)

    update_data = UserSchema(
        username=BOB_USERNAME,
        email=BOB_EMAIL,
        password=NEW_PASSWORD,
    )

    service = UpdateUserService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.execute(
            user_id=1,
            current_user=current_user,
            user_data=update_data,
        )

    assert exc_info.value.status_code == HTTPStatus.NOT_FOUND
    assert exc_info.value.detail == 'User not found'


@pytest.mark.asyncio
async def test_update_user_service_username_or_email_conflict():
    """Test UpdateUserService raises 409 on username/email conflict"""
    repository = Mock()
    current_user = SimpleNamespace(
        id=1, username=TEST_USERNAME, email=ALICE_EMAIL
    )

    user_to_update = SimpleNamespace(
        id=1, username=TEST_USERNAME, email=ALICE_EMAIL
    )

    existing = SimpleNamespace(
        id=2, username='someone', email='someone@example.com'
    )

    repository.get_by_id = AsyncMock(return_value=user_to_update)
    repository.find_by_username_or_email = AsyncMock(return_value=existing)

    update_data = UserSchema(
        username='someone',
        email='someone@example.com',
        password=NEW_PASSWORD,
    )

    service = UpdateUserService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.execute(
            user_id=1, current_user=current_user, user_data=update_data
        )

    assert exc_info.value.status_code == HTTPStatus.CONFLICT
    assert exc_info.value.detail == 'Username or Email already exists'


@pytest.mark.asyncio
async def test_update_user_service_integrity_error():
    """Test UpdateUserService converts IntegrityError into 409"""
    repository = Mock()
    current_user = SimpleNamespace(
        id=1, username=TEST_USERNAME, email=ALICE_EMAIL
    )
    user_to_update = SimpleNamespace(
        id=1, username=TEST_USERNAME, email=ALICE_EMAIL
    )

    repository.get_by_id = AsyncMock(return_value=user_to_update)
    repository.find_by_username_or_email = AsyncMock(return_value=None)
    repository.update = AsyncMock(
        side_effect=IntegrityError('stmt', {}, Exception('orig'))
    )

    update_data = UserSchema(
        username='newname', email='new@example.com', password=NEW_PASSWORD
    )

    service = UpdateUserService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.execute(
            user_id=1, current_user=current_user, user_data=update_data
        )

    assert exc_info.value.status_code == HTTPStatus.CONFLICT
    assert exc_info.value.detail == 'Username or Email already exists'


@pytest.mark.asyncio
async def test_update_user_service_update_returns_none():
    """Test UpdateUserService raises 404 when repository.update returns None"""
    repository = Mock()
    current_user = SimpleNamespace(
        id=1, username=TEST_USERNAME, email=ALICE_EMAIL
    )
    user_to_update = SimpleNamespace(
        id=1, username=TEST_USERNAME, email=ALICE_EMAIL
    )

    repository.get_by_id = AsyncMock(return_value=user_to_update)
    repository.find_by_username_or_email = AsyncMock(return_value=None)
    repository.update = AsyncMock(return_value=None)

    update_data = UserSchema(
        username='newname', email='new@example.com', password=NEW_PASSWORD
    )

    service = UpdateUserService(repository)

    with pytest.raises(HTTPException) as exc_info:
        await service.execute(
            user_id=1, current_user=current_user, user_data=update_data
        )

    assert exc_info.value.status_code == HTTPStatus.NOT_FOUND
    assert exc_info.value.detail == 'User not found'


@pytest.mark.asyncio
async def test_update_user_service_allows_same_user_from_find():
    """Test UpdateUserService allows same-user update from lookup"""
    repository = Mock()
    current_user = SimpleNamespace(
        id=1, username=TEST_USERNAME, email=ALICE_EMAIL
    )
    user_to_update = SimpleNamespace(
        id=1, username=TEST_USERNAME, email=ALICE_EMAIL
    )
    updated_user = SimpleNamespace(
        id=1, username='newname', email='new@example.com'
    )

    repository.get_by_id = AsyncMock(return_value=user_to_update)
    repository.find_by_username_or_email = AsyncMock(
        return_value=SimpleNamespace(
            id=1, username='newname', email='new@example.com'
        )
    )
    repository.update = AsyncMock(return_value=updated_user)

    update_data = UserSchema(
        username='newname', email='new@example.com', password=NEW_PASSWORD
    )

    service = UpdateUserService(repository)
    result = await service.execute(
        user_id=1, current_user=current_user, user_data=update_data
    )

    assert result == updated_user
