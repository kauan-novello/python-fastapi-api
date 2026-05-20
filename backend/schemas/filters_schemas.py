from pydantic import BaseModel, Field


class FilterPage(BaseModel):
    offset: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=100)
