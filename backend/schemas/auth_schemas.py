from pydantic import BaseModel, EmailStr


class EmailRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class TokenOnlyRequest(BaseModel):
    token: str
