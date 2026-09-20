from fastapi.testclient import TestClient


def test_register_login_and_read_profile(client: TestClient) -> None:
    registration = client.post(
        "/auth/register",
        json={"email": "User@Example.com", "password": "a-very-secure-password"},
    )
    assert registration.status_code == 201
    assert registration.json()["user"]["email"] == "user@example.com"
    token = registration.json()["access_token"]

    profile = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.json()["email"] == "user@example.com"

    login = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "a-very-secure-password"},
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"


def test_authentication_failures_are_safe(client: TestClient) -> None:
    payload = {"email": "user@example.com", "password": "a-very-secure-password"}
    assert client.post("/auth/register", json=payload).status_code == 201
    assert client.post("/auth/register", json=payload).status_code == 409
    assert client.post("/auth/login", json={**payload, "password": "wrong"}).status_code == 401
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer nonsense"}).status_code == 401
