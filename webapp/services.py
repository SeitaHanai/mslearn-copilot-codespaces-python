import math
import os
import base64
from uuid import UUID, uuid4

from .models import UserCreate, UserRead, UserUpdate, PaginationMeta, PaginatedResponse


class TokenService:
    def generate(self, length: int) -> str:
        return base64.b64encode(os.urandom(64))[:length].decode("utf-8")

    def generate_page(self, length: int, page: int, page_size: int, total: int) -> PaginatedResponse:
        total_pages = math.ceil(total / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, total)
        count = max(0, end - start)
        items = [self.generate(length) for _ in range(count)]
        return PaginatedResponse(
            items=items,
            meta=PaginationMeta(
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            ),
        )


class UserService:
    def __init__(self) -> None:
        self._store: dict[UUID, UserRead] = {}

    def create(self, data: UserCreate) -> UserRead:
        user = UserRead(id=uuid4(), username=data.username, email=data.email)
        self._store[user.id] = user
        return user

    def get(self, user_id: UUID) -> UserRead | None:
        return self._store.get(user_id)

    def list(self) -> list[UserRead]:
        return list(self._store.values())

    def update(self, user_id: UUID, data: UserUpdate) -> UserRead | None:
        user = self._store.get(user_id)
        if user is None:
            return None
        updated = user.model_copy(
            update={k: v for k, v in data.model_dump().items() if v is not None}
        )
        self._store[user_id] = updated
        return updated

    def delete(self, user_id: UUID) -> bool:
        if user_id not in self._store:
            return False
        del self._store[user_id]
        return True


# Singletons — shared across the app lifetime
_token_service = TokenService()
_user_service = UserService()


def get_token_service() -> TokenService:
    return _token_service


def get_user_service() -> UserService:
    return _user_service
