import os
import base64
from typing import Union
from os.path import dirname, abspath, join
from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .models import Body, UserCreate, UserRead, UserUpdate, PaginationParams, PaginatedResponse
from .services import TokenService, UserService, get_token_service, get_user_service

current_dir = dirname(abspath(__file__))
static_path = join(current_dir, "static")

app = FastAPI()
app.mount("/ui", StaticFiles(directory=static_path), name="ui")


@app.get('/ping')
def ping():
    return {'status': 'ok'}


@app.get('/')
def root():
    html_path = join(static_path, "index.html")
    return FileResponse(html_path)


@app.post('/generate', response_model=PaginatedResponse)
def generate(
    body: Body,
    params: PaginationParams = Depends(),
    service: TokenService = Depends(get_token_service),
):
    """Generate a paginated list of pseudo-random token IDs.

    Tokens are base64-encoded random byte sequences. The full conceptual
    result set has ``total`` tokens; this endpoint returns the slice
    corresponding to the requested ``page``.

    Args:
        body: Request body containing the desired character ``length`` of
            each token (default 20).
        params: Query parameters controlling pagination — ``page`` (≥1),
            ``page_size`` (1–100, default 10), and ``total`` (≥1,
            default 50).
        service: Injected ``TokenService`` instance used to generate tokens.

    Returns:
        A ``PaginatedResponse`` containing the tokens for the requested page
        and metadata (``total``, ``page``, ``page_size``, ``total_pages``).

    Raises:
        HTTPException: 400 if ``page`` exceeds the computed ``total_pages``.
        HTTPException: 422 if any query parameter fails Pydantic validation
            (e.g. ``page < 1``, ``page_size > 100``).
    """
    total_pages = -(-params.total // params.page_size)  # ceiling division
    if params.page > total_pages:
        raise HTTPException(
            status_code=400,
            detail=f"page {params.page} exceeds total_pages {total_pages}",
        )
    return service.generate_page(
        length=body.length,
        page=params.page,
        page_size=params.page_size,
        total=params.total,
    )


# --- User CRUD ---

@app.post('/users', response_model=UserRead, status_code=201)
def create_user(data: UserCreate, service: UserService = Depends(get_user_service)):
    return service.create(data)


@app.get('/users', response_model=list[UserRead])
def list_users(service: UserService = Depends(get_user_service)):
    return service.list()


@app.get('/users/{user_id}', response_model=UserRead)
def get_user(user_id: UUID, service: UserService = Depends(get_user_service)):
    user = service.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put('/users/{user_id}', response_model=UserRead)
def update_user(user_id: UUID, data: UserUpdate, service: UserService = Depends(get_user_service)):
    user = service.update(user_id, data)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.delete('/users/{user_id}', status_code=204)
def delete_user(user_id: UUID, service: UserService = Depends(get_user_service)):
    if not service.delete(user_id):
        raise HTTPException(status_code=404, detail="User not found")