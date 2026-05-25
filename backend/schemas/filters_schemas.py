from pydantic import BaseModel, Field


class FilterPage(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=100)
    search: str | None = Field(
        default=None,
        max_length=100,
        description='Filter by username or email (partial match)',
    )
