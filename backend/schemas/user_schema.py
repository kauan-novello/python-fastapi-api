import re

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    field_validator,
    model_validator,
)

# Password validation constants
PASSWORD_MIN_LENGTH = 8
PASSWORD_PATTERN_UPPERCASE = r'[A-Z]'
PASSWORD_PATTERN_DIGIT = r'\d'
PASSWORD_PATTERN_SPECIAL = r'[!@#$%^&*(),.?":{}|<>]'


def validate_password_strength(password: str) -> str:
    """
    Validate password strength.

    Requirements: 8+ chars, 1 uppercase, 1 digit, 1 special char.
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        msg = 'Password must be at least 8 characters long'
        raise ValueError(msg)
    if not re.search(PASSWORD_PATTERN_UPPERCASE, password):
        msg = 'Password must contain at least one uppercase letter'
        raise ValueError(msg)
    if not re.search(PASSWORD_PATTERN_DIGIT, password):
        msg = 'Password must contain at least one digit'
        raise ValueError(msg)
    if not re.search(PASSWORD_PATTERN_SPECIAL, password):
        msg = (
            'Password must contain at least one special character '
            '(!@#$%^&*...)'
        )
        raise ValueError(msg)
    return password


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str

    @field_validator('password', mode='before')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength for user creation."""
        return validate_password_strength(v)


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None

    @field_validator('password', mode='before')
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        """Validate password strength when a new password is provided."""
        if v is None:
            return None
        return validate_password_strength(v)

    @model_validator(mode='after')
    def require_at_least_one_field(self) -> 'UserUpdate':
        if (
            self.username is None
            and self.email is None
            and self.password is None
        ):
            msg = 'At least one field must be provided'
            raise ValueError(msg)
        return self


class UserSchema(UserCreate):
    pass


class UserPublic(BaseModel):
    id: int
    username: str
    email: EmailStr
    email_verified: bool = False
    role: str = 'user'
    model_config = ConfigDict(from_attributes=True)


class UserDB(UserCreate):
    id: int


class UserList(BaseModel):
    users: list[UserPublic]
    total: int
    offset: int
    limit: int
