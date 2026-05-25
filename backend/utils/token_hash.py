import hashlib

from backend.configs.settings import Settings

settings = Settings()


def hash_token(token: str) -> str:
    payload = f'{settings.SECRET_KEY}:{token}'.encode()
    return hashlib.sha256(payload).hexdigest()
