from http import HTTPStatus

from freezegun import freeze_time

from backend.configs.security import create_refresh_token
from backend.controllers.auth_controller import refresh_access_token


def test_get_token(client, user):
    response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': user.clean_password},
    )
    token = response.json()

    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in token
    assert 'refresh_token' in token
    assert 'token_type' in token


def test_token_inexistent_user(client):
    response = client.post(
        '/auth/token',
        data={'username': 'no_user@no_domain.com', 'password': 'TestPass@123'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Incorrect email or password'}


def test_token_unverified_email(client):
    client.post(
        '/auth/register',
        json={
            'username': 'unverified',
            'email': 'unverified@example.com',
            'password': 'TestPass@123',
        },
    )

    response = client.post(
        '/auth/token',
        data={
            'username': 'unverified@example.com',
            'password': 'TestPass@123',
        },
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {'detail': 'Email not verified'}


def test_token_wrong_password(client, user):
    response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': 'wrong_password'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Incorrect email or password'}


def test_jwt_invalid_token(client):
    response = client.delete(
        '/users/1', headers={'Authorization': 'Bearer token-invalido'}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


def test_token_expired_after_time(client, user):
    with freeze_time('2023-07-14 12:00:00'):
        response = client.post(
            '/auth/token',
            data={'username': user.email, 'password': user.clean_password},
        )
        assert response.status_code == HTTPStatus.OK
        token = response.json()['access_token']

    with freeze_time('2023-07-14 12:31:00'):
        response = client.put(
            f'/users/{user.id}',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'username': 'wrongwrong',
                'email': 'wrong@wrong.com',
                'password': 'TestPass@123',
            },
        )

        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json() == {'detail': 'Could not validate credentials'}


def test_refresh_token(client, user):
    login_response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': user.clean_password},
    )
    refresh_token = login_response.json()['refresh_token']

    response = client.post(
        '/auth/refresh_token',
        headers={'Authorization': f'Bearer {refresh_token}'},
    )

    data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in data
    assert 'refresh_token' in data
    assert 'token_type' in data
    assert data['token_type'] == 'bearer'


def test_refresh_token_with_access_token_should_fail(client, user):
    login_response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': user.clean_password},
    )
    access_token = login_response.json()['access_token']

    response = client.post(
        '/auth/refresh_token',
        headers={'Authorization': f'Bearer {access_token}'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}


def test_token_expired_dont_refresh(client, user):
    with freeze_time('2023-07-14 12:00:00'):
        response = client.post(
            '/auth/token',
            data={'username': user.email, 'password': user.clean_password},
        )
        assert response.status_code == HTTPStatus.OK
        token = response.json()['access_token']

    with freeze_time('2023-07-14 12:31:00'):
        response = client.post(
            '/auth/refresh_token',
            headers={'Authorization': f'Bearer {token}'},
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json() == {'detail': 'Could not validate credentials'}


async def test_refresh_access_token_direct_call(session, user):
    refresh_token = create_refresh_token({'sub': user.email})

    data = await refresh_access_token(
        session=session,
        token=refresh_token,
    )

    assert data.token_type == 'bearer'
    assert data.access_token
    assert data.refresh_token
