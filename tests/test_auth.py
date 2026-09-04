def test_register_new_user_succeeds(client):
    response = client.post(
        "/register", json={"email": "user@example.com", "password": "secret123"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "user@example.com"
    assert "id" in body
    assert "password" not in body  # never leak the password, hashed or not


def test_register_duplicate_email_fails(client):
    payload = {"email": "dup@example.com", "password": "secret123"}
    client.post("/register", json=payload)

    response = client.post("/register", json=payload)

    assert response.status_code == 400


def test_register_invalid_email_rejected(client):
    response = client.post(
        "/register", json={"email": "not-an-email", "password": "secret123"}
    )

    assert response.status_code == 422


def test_login_with_correct_credentials_succeeds(client):
    client.post("/register", json={"email": "a@example.com", "password": "correct"})

    response = client.post(
        "/login", data={"username": "a@example.com", "password": "correct"}
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_with_wrong_password_fails(client):
    client.post("/register", json={"email": "b@example.com", "password": "correct"})

    response = client.post(
        "/login", data={"username": "b@example.com", "password": "wrong"}
    )

    assert response.status_code == 401


def test_login_with_unknown_email_fails(client):
    response = client.post(
        "/login", data={"username": "nobody@example.com", "password": "whatever"}
    )

    assert response.status_code == 401


def test_me_without_token_is_rejected(client):
    response = client.get("/me")

    assert response.status_code == 401


def test_me_with_valid_token_returns_user(client, auth_headers):
    response = client.get("/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["email"] == "fixture-user@example.com"
