import pytest
from app.models.user import User


def test_register_success(client):
    response = client.post(
        "/auth/register",
        json={
            "username": "trader_alice",
            "email": "alice@talktrading.com",
            "password": "SecurePassword123!",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "trader_alice"
    assert data["email"] == "alice@talktrading.com"
    assert "id" in data
    assert "user_uuid" in data
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_email(client):
    client.post(
        "/auth/register",
        json={
            "username": "user_one",
            "email": "duplicate@talktrading.com",
            "password": "Password123!",
        },
    )
    # Attempt register with same email
    res2 = client.post(
        "/auth/register",
        json={
            "username": "user_two",
            "email": "duplicate@talktrading.com",
            "password": "Password123!",
        },
    )
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_register_duplicate_username(client):
    client.post(
        "/auth/register",
        json={
            "username": "same_user",
            "email": "one@talktrading.com",
            "password": "Password123!",
        },
    )
    res2 = client.post(
        "/auth/register",
        json={
            "username": "same_user",
            "email": "two@talktrading.com",
            "password": "Password123!",
        },
    )
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_register_invalid_password(client):
    # Password too short (< 8 chars)
    res = client.post(
        "/auth/register",
        json={
            "username": "short_pass",
            "email": "short@talktrading.com",
            "password": "short",
        },
    )
    assert res.status_code == 422


def test_login_success(client):
    # Register
    client.post(
        "/auth/register",
        json={
            "username": "trader_bob",
            "email": "bob@talktrading.com",
            "password": "StrongPassword999!",
        },
    )

    # Login with email
    res_login = client.post(
        "/auth/login",
        data={
            "username": "bob@talktrading.com",
            "password": "StrongPassword999!",
        },
    )
    assert res_login.status_code == 200
    data = res_login.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    token = data["access_token"]

    # Verify that the issued token works on protected endpoints
    res_me = client.get(
        "/users/me/saved-posts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_me.status_code == 200
    assert isinstance(res_me.json(), list)

    # Create post using issued token
    res_post = client.post(
        "/api/v1/posts/",
        json={"caption": "Test post from real auth token", "visibility": "public"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_post.status_code == 201
    assert res_post.json()["author_id"] == data["user"]["id"]


def test_login_invalid_password(client):
    client.post(
        "/auth/register",
        json={
            "username": "trader_carol",
            "email": "carol@talktrading.com",
            "password": "CorrectPassword123!",
        },
    )

    res_fail = client.post(
        "/auth/login",
        data={
            "username": "carol@talktrading.com",
            "password": "WrongPassword999!",
        },
    )
    assert res_fail.status_code == 401
    assert "Invalid credentials" in res_fail.json()["detail"]


def test_login_nonexistent_user(client):
    res = client.post(
        "/auth/login",
        data={
            "username": "nonexistent@talktrading.com",
            "password": "Password123!",
        },
    )
    assert res.status_code == 401


def test_user_is_active_default(db_session):
    user = User(
        username="active_default_user",
        email="active_default@talktrading.com",
        hashed_password="hashed_placeholder",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.is_active is True

