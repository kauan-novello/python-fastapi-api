from http import HTTPStatus

from jwt import decode

from backend.configs.security import settings


def test_me_endpoint(client, user):
    response = client.post(
        '/auth/token',
        data={
            'username': user.email,
            'password': user.clean_password,
        },
    )
    assert response.status_code == HTTPStatus.OK
    access_token = response.json()['access_token']

    response = client.get(
        '/auth/me', headers={'Authorization': f'Bearer {access_token}'}
    )
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data['email'] == user.email
    assert 'id' in data


def test_register_endpoint(client, mail_outbox):
    payload = {
        'username': 'newuser',
        'email': 'new@user.com',
        'password': 'TestPass@123',
    }
    response = client.post('/auth/register', json=payload)
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data['username'] == 'newuser'
    assert data['email'] == 'new@user.com'
    assert data['email_verified'] is False
    assert len(mail_outbox) == 1


def test_logout_revokes_token(client, user):
    response = client.post(
        '/auth/token',
        data={
            'username': user.email,
            'password': user.clean_password,
        },
    )
    access_token = response.json()['access_token']

    response = client.post(
        '/auth/logout', headers={'Authorization': f'Bearer {access_token}'}
    )
    assert response.status_code == HTTPStatus.OK

    response = client.get(
        '/auth/me', headers={'Authorization': f'Bearer {access_token}'}
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_forgot_and_reset_password_flow(client, user, mail_outbox):
    response = client.post('/auth/forgot-password', json={'email': user.email})
    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert body == {'message': 'If the email exists, a reset link was sent.'}
    assert len(mail_outbox) == 1
    reset_token = mail_outbox[-1].get_content().split('token=')[1].strip()

    payload = decode(
        reset_token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    assert payload['token_type'] == 'reset'

    new_password = 'BrandNewPass@123'
    response = client.post(
        '/auth/reset-password',
        json={'token': reset_token, 'new_password': new_password},
    )
    assert response.status_code == HTTPStatus.OK

    response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': new_password},
    )
    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in response.json()


def test_resend_and_verify_email(client, unverified_user, mail_outbox):
    response = client.post(
        '/auth/resend-verification', json={'email': unverified_user.email}
    )
    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert body == {
        'message': 'If the account exists, verification was resent.'
    }
    assert len(mail_outbox) == 1
    verify_token = mail_outbox[-1].get_content().split('token=')[1].strip()

    response = client.post('/auth/verify-email', json={'token': verify_token})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'email verified'}

    response = client.post(
        '/auth/resend-verification',
        json={'email': unverified_user.email},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'message': 'If the account exists, verification was resent.'
    }
    assert len(mail_outbox) == 1
