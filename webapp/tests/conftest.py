import pytest
from fastapi.testclient import TestClient

from webapp.main import app


@pytest.fixture()
def client():
    """Return a fresh TestClient (and a fresh in-memory store) for each test."""
    # Re-import to reset singleton state between tests
    import importlib
    import webapp.services as svc_module

    svc_module._user_service.__init__()  # reset in-memory store
    with TestClient(app) as c:
        yield c
