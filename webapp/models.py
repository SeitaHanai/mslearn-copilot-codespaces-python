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
    """Paginated list of generated tokens with accompanying metadata.

    Attributes:
        items: The tokens generated for the requested page. The number of
            items equals ``page_size`` for all pages except the last, which
            may contain fewer items when ``total`` is not evenly divisible
            by ``page_size``.
        meta: Pagination metadata describing the current page position and
            the overall result set size.
    """

    items: list[str]
    meta: PaginationMeta


class ErrorResponse(BaseModel):
    """Uniform error envelope returned by all exception handlers.

    Attributes:
        status_code: The HTTP status code of the error.
        detail: Human-readable description of what went wrong.
    """

    status_code: int
    detail: str


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
