from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User
from app.repositories.user import UserRepository


def test_register_creates_user_with_hashed_password(
    client: TestClient,
    db_session: Session,
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "nickname": "organizer",
            "email": "Organizer@Example.com",
            "password": "StrongPass123",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "organizer@example.com"
    assert body["nickname"] == "organizer"
    assert "password" not in body
    assert "password_hash" not in body

    user = UserRepository(db_session).get_by_email("organizer@example.com")
    assert user is not None
    assert user.password_hash != "StrongPass123"
    assert verify_password("StrongPass123", user.password_hash)


def test_register_duplicate_email_returns_conflict(client: TestClient) -> None:
    payload = {
        "nickname": "organizer",
        "email": "organizer@example.com",
        "password": "StrongPass123",
    }

    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    response = client.post(
        "/api/v1/auth/register",
        json={**payload, "nickname": "another"},
    )

    assert response.status_code == 409


def test_register_rejects_bcrypt_unsafe_password_length(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "nickname": "organizer",
            "email": "organizer@example.com",
            "password": "a" * 73,
        },
    )

    assert response.status_code == 422


def test_login_returns_bearer_token(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "nickname": "organizer",
            "email": "organizer@example.com",
            "password": "StrongPass123",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "organizer@example.com", "password": "StrongPass123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_with_wrong_password_returns_unauthorized(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "nickname": "organizer",
            "email": "organizer@example.com",
            "password": "StrongPass123",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "organizer@example.com", "password": "WrongPass123"},
    )

    assert response.status_code == 401


def test_me_returns_current_user(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "nickname": "organizer",
            "email": "organizer@example.com",
            "password": "StrongPass123",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "organizer@example.com", "password": "StrongPass123"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "organizer@example.com"


def test_me_without_token_returns_unauthorized(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_with_deleted_user_returns_unauthorized(
    client: TestClient,
    db_session: Session,
) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "nickname": "organizer",
            "email": "organizer@example.com",
            "password": "StrongPass123",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "organizer@example.com", "password": "StrongPass123"},
    )
    token = login_response.json()["access_token"]

    user = db_session.query(User).filter_by(email="organizer@example.com").one()
    db_session.delete(user)
    db_session.commit()

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
