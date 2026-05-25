from types import SimpleNamespace

from backend.configs.permissions import (
    ADMIN_ROLE,
    USER_ROLE,
    can_manage_user,
    is_admin,
)


def test_is_admin():
    admin = SimpleNamespace(role=ADMIN_ROLE)
    user = SimpleNamespace(role=USER_ROLE)
    assert is_admin(admin) is True
    assert is_admin(user) is False


def test_can_manage_user():
    admin = SimpleNamespace(id=1, role=ADMIN_ROLE)
    owner = SimpleNamespace(id=2, role=USER_ROLE)

    assert can_manage_user(admin, 99) is True
    assert can_manage_user(owner, 2) is True
    assert can_manage_user(owner, 3) is False
