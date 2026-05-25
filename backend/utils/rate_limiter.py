from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, Request, status

from backend.utils.rate_limit_backends import (
    InMemoryRateLimiterBackend,
    RateLimiterBackend,
    create_rate_limit_backend,
)

RateLimitDependency = Callable[[Request], Awaitable[str]]


class RateLimiter:
    def __init__(self, backend: RateLimiterBackend) -> None:
        self.backend = backend

    async def is_allowed(self, identifier: str) -> bool:
        return await self.backend.is_allowed(identifier)

    def clear(self) -> None:
        if isinstance(self.backend, InMemoryRateLimiterBackend):
            self.backend.attempts.clear()


def _build_limiter(
    prefix: str,
    max_attempts: int,
    window_seconds: int,
) -> RateLimiter:
    return RateLimiter(
        create_rate_limit_backend(prefix, max_attempts, window_seconds)
    )


forgot_password_limiter = _build_limiter('forgot_password', 5, 3600)
reset_password_limiter = _build_limiter('reset_password', 5, 3600)
verify_email_limiter = _build_limiter('verify_email', 10, 3600)
resend_verification_limiter = _build_limiter('resend_verification', 5, 3600)
register_limiter = _build_limiter('register', 10, 86400)
login_limiter = _build_limiter('login', 10, 3600)


def _get_client_identifier(request: Request) -> str:
    return request.client.host if request.client else 'unknown'


def _create_rate_limit_dependency(
    limiter: RateLimiter, error_detail: str
) -> RateLimitDependency:
    async def check_rate_limit(request: Request) -> str:
        identifier = _get_client_identifier(request)
        if not await limiter.is_allowed(identifier):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_detail,
            )
        return identifier

    return check_rate_limit


check_register_rate_limit = Depends(
    _create_rate_limit_dependency(
        register_limiter, 'Too many registration attempts. Try again later.'
    )
)

check_forgot_password_rate_limit = Depends(
    _create_rate_limit_dependency(
        forgot_password_limiter,
        'Too many password reset requests. Try again later.',
    )
)

check_reset_password_rate_limit = Depends(
    _create_rate_limit_dependency(
        reset_password_limiter,
        'Too many password reset attempts. Try again later.',
    )
)

check_verify_email_rate_limit = Depends(
    _create_rate_limit_dependency(
        verify_email_limiter,
        'Too many verification attempts. Try again later.',
    )
)

check_resend_verification_rate_limit = Depends(
    _create_rate_limit_dependency(
        resend_verification_limiter,
        'Too many resend verification requests. Try again later.',
    )
)

check_login_rate_limit = Depends(
    _create_rate_limit_dependency(
        login_limiter, 'Too many login attempts. Try again later.'
    )
)
