from http import HTTPStatus

import pytest
from fastapi import HTTPException
from jwt import decode, encode, get_unverified_header

from backend.configs.security import (
    create_access_token,
    get_current_user,
    get_password_hash,
    settings,
    verify_password,
)
from backend.models.user_model import User


def test_jwt():
    data = {'test': 'test'}
    token = create_access_token(data)

    decoded = decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )

    assert decoded['test'] == data['test']
    assert 'exp' in decoded


def test_jwt_includes_expiration():
    """Test JWT token includes expiration time"""
    data = {'sub': 'test@example.com'}
    token = create_access_token(data)

    decoded = decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )

    assert 'exp' in decoded
    assert decoded['sub'] == 'test@example.com'


def test_get_token(client, user):
    response = client.post(
        'auth/token',
        data={'username': user.email, 'password': user.clean_password},
    )
    token = response.json()

    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in token
    assert 'refresh_token' in token
    assert 'token_type' in token


def test_jwt_invalid_token(client):
    response = client.delete(
        '/users/1', headers={'Authorization': 'Bearer token-invalido'}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


def test_password_hash_and_verify():
    """Test password hashing and verification"""
    password = 'mypassword123'
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed)


def test_verify_password_wrong_password():
    """Test verify_password returns False for wrong password"""
    password = 'correctpassword'
    hashed = get_password_hash(password)

    assert not verify_password('wrongpassword', hashed)


async def test_get_current_user_success(session):
    """Test get_current_user returns user when token is valid"""
    user = User(
        username='testuser',
        email='test@example.com',
        password=get_password_hash('password123'),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    token = create_access_token({'sub': 'test@example.com'})

    current_user = await get_current_user(session=session, token=token)

    assert current_user.email == 'test@example.com'
    assert current_user.username == 'testuser'


async def test_get_current_user_invalid_token(session):
    """Test get_current_user raises 401 for invalid token"""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(session=session, token='invalid-token')

    assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED
    assert exc_info.value.detail == 'Could not validate credentials'


async def test_get_current_user_missing_sub(session):
    """Test get_current_user raises 401 when 'sub' is missing from token"""
    token = encode(
        {'data': 'no_subject'},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(session=session, token=token)

    assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED
    assert exc_info.value.detail == 'Could not validate credentials'


async def test_get_current_user_user_not_found(session):
    """Test get_current_user raises 401 when user not found in database"""
    token = create_access_token({'sub': 'nonexistent@example.com'})

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(session=session, token=token)

    assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED
    assert exc_info.value.detail == 'Could not validate credentials'


def test_create_access_token_has_correct_algorithm():
    """Test create_access_token uses the correct algorithm"""
    data = {'sub': 'test@example.com'}
    token = create_access_token(data)

    header = get_unverified_header(token)

    assert header['alg'] == settings.ALGORITHM


def test_get_password_hash_different_hashes():
    """Test that same password produces different hashes"""
    password = 'mypassword'
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    assert hash1 != hash2
    assert verify_password(password, hash1)
    assert verify_password(password, hash2)
