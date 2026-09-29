import pytest


def test_signup_success(test_client):
    """Test successful user signup"""
    response = test_client.post(
        "/auth/signup",
        json={"email": "newuser@example.com", "password": "SecurePass123"},
    )
    assert response.status_code == 201
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_signup_duplicate_email(test_client):
    """Test signup with duplicate email"""
    test_client.post(
        "/auth/signup",
        json={"email": "duplicate@example.com", "password": "SecurePass123"},
    )

    response = test_client.post(
        "/auth/signup",
        json={"email": "duplicate@example.com", "password": "AnotherPass123"},
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_signup_invalid_email(test_client):
    """Test signup with invalid email format"""
    response = test_client.post(
        "/auth/signup",
        json={"email": "invalid-email", "password": "SecurePass123"},
    )
    assert response.status_code == 422


def test_signup_weak_password(test_client):
    """Test signup with password that's too short"""
    response = test_client.post(
        "/auth/signup",
        json={"email": "user@example.com", "password": "short"},
    )
    assert response.status_code == 422


def test_login_success(test_client):
    """Test successful login"""
    test_client.post(
        "/auth/signup",
        json={"email": "user@example.com", "password": "SecurePass123"},
    )

    response = test_client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "SecurePass123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_invalid_email(test_client):
    """Test login with non-existent email"""
    response = test_client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "AnyPassword123"},
    )
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


def test_login_invalid_password(test_client):
    """Test login with incorrect password"""
    test_client.post(
        "/auth/signup",
        json={"email": "user@example.com", "password": "CorrectPass123"},
    )

    response = test_client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "WrongPass123"},
    )
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


def test_protected_endpoint_without_auth(test_client):
    """Test accessing protected endpoint without authentication"""
    response = test_client.get("/auth/me")
    assert response.status_code == 403


def test_get_current_user(test_client, auth_headers):
    """Test getting current authenticated user info"""
    response = test_client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
    assert "id" in response.json()


def test_invalid_token(test_client):
    """Test using invalid/malformed JWT"""
    response = test_client.get(
        "/auth/me", headers={"Authorization": "Bearer invalid.token.here"}
    )
    assert response.status_code == 401
