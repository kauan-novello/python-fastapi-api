from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_as_dataclass, mapped_column

from backend.models.user_model import table_registry


@mapped_as_dataclass(table_registry)
class RevokedToken:
    __tablename__ = 'revoked_tokens'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    revoked_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] | None = mapped_column(
        DateTime,
        nullable=True,
    )
