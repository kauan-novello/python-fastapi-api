from fastapi import status

from backend.utils.rate_limiter import (
    forgot_password_limiter,
    login_limiter,
    register_limiter,
    resend_verification_limiter,
    reset_password_limiter,
    verify_email_limiter,
)


def test_register_rate_limit(client, session):
    """Test that registration has rate limiting."""
    register_limiter.clear()

    user_data = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPass123!',
    }

    # Make 10 successful requests (at limit)
    for i in range(10):
        user_data['email'] = f'test{i}@example.com'
        user_data['username'] = f'testuser{i}'
        response = client.post('/auth/register', json=user_data)
        assert response.status_code in {
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
        }

    # 11th request should be rate limited
    user_data['email'] = 'test11@example.com'
    user_data['username'] = 'testuser11'
    response = client.post('/auth/register', json=user_data)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


def test_login_rate_limit(client, user):
    """Test that login has rate limiting."""
    login_limiter.clear()

    for _ in range(10):
        response = client.post(
            '/auth/token',
            data={
                'username': user.email,
                'password': user.clean_password,
            },
        )
        assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS

    response = client.post(
        '/auth/token',
        data={
            'username': user.email,
            'password': user.clean_password,
        },
    )
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


def test_forgot_password_rate_limit(client):
    """Test that forgot password has rate limiting."""
    forgot_password_limiter.clear()

    email_data = {'email': 'test@example.com'}

    # Make 5 requests (at limit for forgot password)
    for _ in range(5):
        response = client.post('/auth/forgot-password', json=email_data)
        assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS

    # 6th request should be rate limited
    response = client.post('/auth/forgot-password', json=email_data)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


def test_reset_password_rate_limit(client):
    """Test that reset password has rate limiting."""
    reset_password_limiter.clear()

    reset_data = {
        'token': 'dummy-token',
        'new_password': 'NewPass123!',
    }

    # Make 5 requests (at limit for reset password)
    for _ in range(5):
        response = client.post('/auth/reset-password', json=reset_data)
        assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS

    # 6th request should be rate limited
    response = client.post('/auth/reset-password', json=reset_data)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


def test_verify_email_rate_limit(client):
    """Test that verify email has rate limiting."""
    verify_email_limiter.clear()

    token_data = {'token': 'dummy-token'}

    # Make 10 requests (at limit for verify email)
    for _ in range(10):
        response = client.post('/auth/verify-email', json=token_data)
        assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS

    # 11th request should be rate limited
    response = client.post('/auth/verify-email', json=token_data)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


def test_resend_verification_rate_limit(client):
    """Test that resend verification has rate limiting."""
    resend_verification_limiter.clear()

    email_data = {'email': 'test@example.com'}

    # Make 5 requests (at limit for resend verification)
    for _ in range(5):
        response = client.post('/auth/resend-verification', json=email_data)
        assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS

    # 6th request should be rate limited
    response = client.post('/auth/resend-verification', json=email_data)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
