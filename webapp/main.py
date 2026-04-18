import os
import base64
from typing import Union
from os.path import dirname, abspath, join
from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from .models import Body, UserCreate, UserRead, UserUpdate, PaginationParams, PaginatedResponse, ErrorResponse
from .services import TokenService, UserService, get_token_service, get_user_service

current_dir = dirname(abspath(__file__))
static_path = join(current_dir, "static")

# ---------------------------------------------------------------------------
# Rate limiter — keyed by client IP; global default: 60 req/minute
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(
    title="Token & User API",
    description="Generates paginated pseudo-random tokens and manages users.",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.mount("/ui", StaticFiles(directory=static_path), name="ui")


# ---------------------------------------------------------------------------
# Exception handlers — all errors return a consistent ErrorResponse body
# ---------------------------------------------------------------------------

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content=ErrorResponse(status_code=429, detail="Rate limit exceeded. Please slow down.").model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(status_code=exc.status_code, detail=str(exc.detail)).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = "; ".join(
        f"{' -> '.join(str(l) for l in e['loc'])}: {e['msg']}"
        for e in exc.errors()
    )
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(status_code=422, detail=errors).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(status_code=500, detail="An unexpected error occurred.").model_dump(),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get('/ping')
@limiter.limit("120/minute")
def ping(request: Request):
    return {'status': 'ok'}


@app.get('/')
def root():
    html_path = join(static_path, "index.html")
    return FileResponse(html_path)


@app.post('/generate', response_model=PaginatedResponse)
@limiter.limit("30/minute")
def generate(
    request: Request,
    body: Body,
    params: PaginationParams = Depends(),
    service: TokenService = Depends(get_token_service),
):
    """Generate a paginated list of pseudo-random token IDs.

    Tokens are base64-encoded random byte sequences. The full conceptual
    result set has ``total`` tokens; this endpoint returns the slice
    corresponding to the requested ``page``.

    Args:
        request: The incoming HTTP request (required by the rate limiter).
        body: Request body containing the desired character ``length`` of
            each token (default 20).
        params: Query parameters controlling pagination — ``page`` (>=1),
            ``page_size`` (1-100, default 10), and ``total`` (>=1,
            default 50).
        service: Injected ``TokenService`` instance used to generate tokens.

    Returns:
        A ``PaginatedResponse`` containing the tokens for the requested page
        and metadata (``total``, ``page``, ``page_size``, ``total_pages``).

    Raises:
        HTTPException: 400 if ``page`` exceeds the computed ``total_pages``.
        HTTPException: 422 if any query parameter fails Pydantic validation
            (e.g. ``page < 1``, ``page_size > 100``).
        HTTPException: 429 if the per-route rate limit (30/minute) is exceeded.
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
