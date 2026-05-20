import factory

from backend.configs.security import get_password_hash
from backend.models.user_model import User


class UserFactory(factory.Factory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'test{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@test.com')
    password = factory.LazyFunction(lambda: get_password_hash('defaultpass'))
