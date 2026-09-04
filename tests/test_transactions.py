SAMPLE_TRANSACTION = {
    "type": "discretionary",
    "category": "Dining Out",
    "description": "Lunch",
    "amount": "25.50",
    "txn_date": "2026-01-15",
}


def test_create_transaction_without_token_is_rejected(client):
    response = client.post("/transactions", json=SAMPLE_TRANSACTION)

    assert response.status_code == 401


def test_create_transaction_with_token_succeeds(client, auth_headers):
    response = client.post(
        "/transactions", json=SAMPLE_TRANSACTION, headers=auth_headers
    )

    assert response.status_code == 201
    body = response.json()
    assert body["category"] == "Dining Out"
    assert body["amount"] == "25.50"
    assert "id" in body


def test_create_transaction_with_negative_amount_rejected(client, auth_headers):
    bad_transaction = {**SAMPLE_TRANSACTION, "amount": "-5.00"}

    response = client.post("/transactions", json=bad_transaction, headers=auth_headers)

    assert response.status_code == 422


def test_create_transaction_with_zero_amount_rejected(client, auth_headers):
    bad_transaction = {**SAMPLE_TRANSACTION, "amount": "0"}

    response = client.post("/transactions", json=bad_transaction, headers=auth_headers)

    assert response.status_code == 422


def test_create_transaction_with_invalid_type_rejected(client, auth_headers):
    bad_transaction = {**SAMPLE_TRANSACTION, "type": "not-a-real-type"}

    response = client.post("/transactions", json=bad_transaction, headers=auth_headers)

    assert response.status_code == 422


def test_list_transactions_returns_only_own_transactions(client):
    # User 1 creates a transaction
    client.post("/register", json={"email": "user1@example.com", "password": "pass123"})
    login1 = client.post(
        "/login", data={"username": "user1@example.com", "password": "pass123"}
    )
    headers1 = {"Authorization": f"Bearer {login1.json()['access_token']}"}
    client.post("/transactions", json=SAMPLE_TRANSACTION, headers=headers1)

    # User 2 should see an empty list, not user 1's transaction
    client.post("/register", json={"email": "user2@example.com", "password": "pass123"})
    login2 = client.post(
        "/login", data={"username": "user2@example.com", "password": "pass123"}
    )
    headers2 = {"Authorization": f"Bearer {login2.json()['access_token']}"}

    response = client.get("/transactions", headers=headers2)

    assert response.status_code == 200
    assert response.json() == []


def test_list_transactions_returns_created_ones(client, auth_headers):
    client.post("/transactions", json=SAMPLE_TRANSACTION, headers=auth_headers)
    client.post(
        "/transactions",
        json={**SAMPLE_TRANSACTION, "category": "Housing", "amount": "300.00"},
        headers=auth_headers,
    )

    response = client.get("/transactions", headers=auth_headers)

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_delete_transaction_removes_it(client, auth_headers):
    created = client.post(
        "/transactions", json=SAMPLE_TRANSACTION, headers=auth_headers
    ).json()

    delete_response = client.delete(f"/transactions/{created['id']}", headers=auth_headers)
    list_response = client.get("/transactions", headers=auth_headers)

    assert delete_response.status_code == 204
    assert list_response.json() == []


def test_delete_nonexistent_transaction_returns_404(client, auth_headers):
    response = client.delete("/transactions/99999", headers=auth_headers)

    assert response.status_code == 404


def test_cannot_delete_another_users_transaction(client):
    client.post("/register", json={"email": "owner@example.com", "password": "pass123"})
    owner_login = client.post(
        "/login", data={"username": "owner@example.com", "password": "pass123"}
    )
    owner_headers = {"Authorization": f"Bearer {owner_login.json()['access_token']}"}
    created = client.post(
        "/transactions", json=SAMPLE_TRANSACTION, headers=owner_headers
    ).json()

    client.post("/register", json={"email": "intruder@example.com", "password": "pass123"})
    intruder_login = client.post(
        "/login", data={"username": "intruder@example.com", "password": "pass123"}
    )
    intruder_headers = {"Authorization": f"Bearer {intruder_login.json()['access_token']}"}

    response = client.delete(f"/transactions/{created['id']}", headers=intruder_headers)

    assert response.status_code == 404
