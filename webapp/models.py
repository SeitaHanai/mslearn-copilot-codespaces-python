from typing import Union
from uuid import UUID
from pydantic import BaseModel, Field


class Body(BaseModel):
    length: Union[int, None] = 20


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    total: int = Field(default=50, ge=1)


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedResponse(BaseModel):
    items: list[str]
    meta: PaginationMeta


class UserCreate(BaseModel):
    username: str
    email: str


class UserRead(BaseModel):
    id: UUID
    username: str
    email: str


class UserUpdate(BaseModel):
    username: Union[str, None] = None
    email: Union[str, None] = None
