import math


def test_ping(client):
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- Pagination happy-path tests ---

def test_generate_default_pagination(client):
    """Default: page=1, page_size=10, total=50 → 10 items, 5 total_pages."""
    response = client.post("/generate", json={})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "meta" in data
    assert len(data["items"]) == 10
    meta = data["meta"]
    assert meta["page"] == 1
    assert meta["page_size"] == 10
    assert meta["total"] == 50
    assert meta["total_pages"] == 5


def test_generate_custom_page_size(client):
    """page_size=5, total=20 → 5 items, 4 total_pages."""
    response = client.post("/generate?page_size=5&total=20", json={})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["meta"]["total_pages"] == 4


def test_generate_custom_length(client):
    """Token length is respected."""
    response = client.post("/generate?page_size=3&total=3", json={"length": 10})
    assert response.status_code == 200
    items = response.json()["items"]
    assert all(len(t) == 10 for t in items)


def test_generate_last_page_partial(client):
    """Last page returns fewer items when total is not divisible by page_size."""
    response = client.post("/generate?page=2&page_size=3&total=5", json={})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2  # 5 - 3 = 2 items on page 2
    assert data["meta"]["total_pages"] == 2


def test_generate_page_size_one(client):
    """page_size=1 → exactly 1 token per page."""
    response = client.post("/generate?page=1&page_size=1&total=10", json={})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["meta"]["total_pages"] == 10


def test_generate_total_one(client):
    """total=1 → 1 item, 1 total_page."""
    response = client.post("/generate?page=1&page_size=10&total=1", json={})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["meta"]["total_pages"] == 1


def test_generate_max_length_token(client):
    """length=64 tokens are returned correctly."""
    response = client.post("/generate?page_size=2&total=2", json={"length": 64})
    assert response.status_code == 200
    items = response.json()["items"]
    assert all(len(t) == 64 for t in items)


# --- Validation / edge case tests ---

def test_generate_page_too_low(client):
    """page=0 fails Pydantic validation → 422."""
    response = client.post("/generate?page=0", json={})
    assert response.status_code == 422


def test_generate_page_size_too_high(client):
    """page_size=101 fails Pydantic validation → 422."""
    response = client.post("/generate?page_size=101", json={})
    assert response.status_code == 422


def test_generate_page_size_too_low(client):
    """page_size=0 fails Pydantic validation → 422."""
    response = client.post("/generate?page_size=0", json={})
    assert response.status_code == 422


def test_generate_page_out_of_range(client):
    """page > total_pages → HTTP 400."""
    response = client.post("/generate?page=99&page_size=10&total=10", json={})
    assert response.status_code == 400
    assert "total_pages" in response.json()["detail"]
