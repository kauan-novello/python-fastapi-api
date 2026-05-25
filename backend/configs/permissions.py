from backend.models.user_model import User

ADMIN_ROLE = 'admin'
USER_ROLE = 'user'


def is_admin(user: User) -> bool:
    return getattr(user, 'role', USER_ROLE) == ADMIN_ROLE


def can_manage_user(current_user: User, target_user_id: int) -> bool:
    return is_admin(current_user) or current_user.id == target_user_id
