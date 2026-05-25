from backend.schemas.user_schema import UserSchema


def _build_user_data():
    return UserSchema(
        username='alice',
        email='alice@example.com',
        password='Secret@123',
    )
