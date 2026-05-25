import asyncio

import pytest

from backend.utils.rate_limit_backends import InMemoryRateLimiterBackend
from backend.utils.rate_limiter import (
    RateLimiter,
    forgot_password_limiter,
    register_limiter,
    resend_verification_limiter,
    reset_password_limiter,
    verify_email_limiter,
)


@pytest.mark.asyncio
async def test_first_request_is_allowed():
    limiter = RateLimiter(InMemoryRateLimiterBackend(5, 3600))
    assert await limiter.is_allowed('test_user') is True


@pytest.mark.asyncio
async def test_multiple_requests_within_limit():
    limiter = RateLimiter(InMemoryRateLimiterBackend(3, 3600))
    assert await limiter.is_allowed('test_user') is True
    assert await limiter.is_allowed('test_user') is True
    assert await limiter.is_allowed('test_user') is True


@pytest.mark.asyncio
async def test_request_exceeds_limit():
    limiter = RateLimiter(InMemoryRateLimiterBackend(2, 3600))
    assert await limiter.is_allowed('test_user') is True
    assert await limiter.is_allowed('test_user') is True
    assert await limiter.is_allowed('test_user') is False


@pytest.mark.asyncio
async def test_different_identifiers_independent():
    limiter = RateLimiter(InMemoryRateLimiterBackend(1, 3600))
    assert await limiter.is_allowed('user1') is True
    assert await limiter.is_allowed('user2') is True
    assert await limiter.is_allowed('user1') is False
    assert await limiter.is_allowed('user2') is False


@pytest.mark.asyncio
async def test_limiter_clears_old_attempts():
    limiter = RateLimiter(InMemoryRateLimiterBackend(2, 1))
    assert await limiter.is_allowed('test_user') is True
    assert await limiter.is_allowed('test_user') is True
    assert await limiter.is_allowed('test_user') is False

    await asyncio.sleep(1.1)

    assert await limiter.is_allowed('test_user') is True


@pytest.mark.asyncio
async def test_forgot_password_limiter_exists():
    assert forgot_password_limiter is not None
    assert await forgot_password_limiter.is_allowed('ip1') is True


@pytest.mark.asyncio
async def test_reset_password_limiter_exists():
    assert reset_password_limiter is not None
    assert await reset_password_limiter.is_allowed('ip1') is True


@pytest.mark.asyncio
async def test_verify_email_limiter_exists():
    assert verify_email_limiter is not None
    assert await verify_email_limiter.is_allowed('ip1') is True


@pytest.mark.asyncio
async def test_resend_verification_limiter_exists():
    assert resend_verification_limiter is not None
    assert await resend_verification_limiter.is_allowed('ip1') is True


@pytest.mark.asyncio
async def test_register_limiter_exists():
    assert register_limiter is not None
    assert await register_limiter.is_allowed('ip1') is True


@pytest.mark.asyncio
async def test_concurrent_requests_are_thread_safe():
    limiter = RateLimiter(InMemoryRateLimiterBackend(5, 3600))
    max_attempts = 5
    total_requests = 10

    async def make_request():
        return await limiter.is_allowed('concurrent_user')

    tasks = [make_request() for _ in range(total_requests)]
    results = await asyncio.gather(*tasks)

    assert sum(results) == max_attempts
    assert results.count(True) == max_attempts
    assert results.count(False) == max_attempts
