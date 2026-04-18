import uuid


# --- Create ---

def test_create_user(client):
    response = client.post("/users", json={"username": "alice", "email": "alice@example.com"})
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data
    uuid.UUID(data["id"])  # validates it's a well-formed UUID


# --- List ---

def test_list_users_empty(client):
    response = client.get("/users")
    assert response.status_code == 200
    assert response.json() == []


def test_list_users_returns_created(client):
    client.post("/users", json={"username": "bob", "email": "bob@example.com"})
    client.post("/users", json={"username": "carol", "email": "carol@example.com"})
    response = client.get("/users")
    assert response.status_code == 200
    assert len(response.json()) == 2


# --- Get single ---

def test_get_user(client):
    created = client.post("/users", json={"username": "dave", "email": "dave@example.com"}).json()
    response = client.get(f"/users/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_get_user_not_found(client):
    response = client.get(f"/users/{uuid.uuid4()}")
    assert response.status_code == 404


# --- Update ---

def test_update_user(client):
    created = client.post("/users", json={"username": "eve", "email": "eve@example.com"}).json()
    response = client.put(f"/users/{created['id']}", json={"email": "eve2@example.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "eve"        # unchanged
    assert data["email"] == "eve2@example.com"  # updated


def test_update_user_not_found(client):
    response = client.put(f"/users/{uuid.uuid4()}", json={"username": "ghost"})
    assert response.status_code == 404


# --- Delete ---

def test_delete_user(client):
    created = client.post("/users", json={"username": "frank", "email": "frank@example.com"}).json()
    response = client.delete(f"/users/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/users/{created['id']}").status_code == 404


def test_delete_user_not_found(client):
    response = client.delete(f"/users/{uuid.uuid4()}")
    assert response.status_code == 404
