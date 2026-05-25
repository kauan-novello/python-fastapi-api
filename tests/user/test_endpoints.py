from http import HTTPStatus

from backend.configs.security import create_access_token
from backend.schemas.user_schema import UserPublic

VALID_PASSWORD = 'Secret@123'
NEW_VALID_PASSWORD = 'NewPass@456'


def _auth_headers(user):
    token = create_access_token({'sub': user.email})
    return {'Authorization': f'Bearer {token}'}


def test_register_user(client, mail_outbox):
    response = client.post(
        '/auth/register',
        json={
            'username': 'alice',
            'email': 'alice@example.com',
            'password': VALID_PASSWORD,
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'username': 'alice',
        'email': 'alice@example.com',
        'email_verified': False,
        'role': 'user',
        'id': 1,
    }
    assert len(mail_outbox) == 1


def test_read_users_without_auth_returns_unauthorized(client):
    response = client.get('/users/')
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_read_users_forbidden_for_regular_user(client, user):
    response = client.get('/users/', headers=_auth_headers(user))
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_read_users_with_pagination(client, admin_user, other_user):
    expected_total = 2
    expected_offset = 0
    expected_limit = 10
    response = client.get(
        '/users/?offset=0&limit=10',
        headers=_auth_headers(admin_user),
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['total'] == expected_total
    assert data['offset'] == expected_offset
    assert data['limit'] == expected_limit
    assert len(data['users']) == expected_total


def test_read_users_search_filter(client, admin_user, other_user):
    response = client.get(
        f'/users/?search={other_user.username}',
        headers=_auth_headers(admin_user),
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['total'] == 1
    assert data['users'][0]['username'] == other_user.username


def test_read_users_limit_above_max_returns_validation_error(
    client, admin_user
):
    response = client.get(
        '/users/?limit=101',
        headers=_auth_headers(admin_user),
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_get_user_should_return_not_found(client, admin_user):
    response = client.get('/users/666', headers=_auth_headers(admin_user))

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'User not found'}


def test_get_user_forbidden_for_other_user(client, user, other_user):
    response = client.get(
        f'/users/{other_user.id}',
        headers=_auth_headers(user),
    )
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_get_user(client, user):
    response = client.get('/users/1', headers=_auth_headers(user))

    assert response.status_code == HTTPStatus.OK
    assert response.json() == UserPublic.model_validate(user).model_dump()


def test_admin_can_get_any_user(client, admin_user, other_user):
    response = client.get(
        f'/users/{other_user.id}',
        headers=_auth_headers(admin_user),
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['id'] == other_user.id


def test_update_user_partial_without_password(client, user):
    response = client.put(
        '/users/1',
        json={'username': 'bob'},
        headers=_auth_headers(user),
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['username'] == 'bob'
    assert response.json()['email'] == user.email


def test_update_user_requires_at_least_one_field(client, user):
    response = client.put(
        '/users/1',
        json={},
        headers=_auth_headers(user),
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_update_user(client, user):
    response = client.put(
        '/users/1',
        json={
            'username': 'bob',
            'email': 'bob@example.com',
            'password': NEW_VALID_PASSWORD,
        },
        headers=_auth_headers(user),
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'username': 'bob',
        'email': 'bob@example.com',
        'email_verified': True,
        'role': 'user',
        'id': 1,
    }


def test_admin_can_update_other_user(client, admin_user, other_user):
    response = client.put(
        f'/users/{other_user.id}',
        json={'username': 'updated_name'},
        headers=_auth_headers(admin_user),
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['username'] == 'updated_name'


def test_update_integrity_error(client, user):
    client.post(
        '/auth/register',
        json={
            'username': 'fausto',
            'email': 'fausto@example.com',
            'password': VALID_PASSWORD,
        },
    )

    response_update = client.put(
        f'/users/{user.id}',
        json={
            'username': 'fausto',
            'email': 'bob@example.com',
            'password': NEW_VALID_PASSWORD,
        },
        headers=_auth_headers(user),
    )
    assert response_update.status_code == HTTPStatus.CONFLICT
    assert response_update.json() == {
        'detail': 'Username or Email already exists'
    }


def test_update_user_should_return_forbidden_for_other_user(
    client, user, other_user
):
    response = client.put(
        f'/users/{other_user.id}',
        json={'username': 'bob'},
        headers=_auth_headers(user),
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {'detail': 'Not enough permissions'}


def test_delete_user_should_return_forbidden_for_other_user(
    client, user, other_user
):
    response = client.delete(
        f'/users/{other_user.id}',
        headers=_auth_headers(user),
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {'detail': 'Not enough permissions'}


def test_admin_can_delete_other_user(client, admin_user, other_user):
    response = client.delete(
        f'/users/{other_user.id}',
        headers=_auth_headers(admin_user),
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'User deleted'}


def test_delete_user(client, user):
    response = client.delete('/users/1', headers=_auth_headers(user))
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'User deleted'}
