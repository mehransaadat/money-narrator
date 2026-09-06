from app.routers import narrative as narrative_module

SAMPLE_TRANSACTION = {
    "type": "income",
    "category": "Salary",
    "description": "Paycheck",
    "amount": "1000.00",
    "txn_date": "2026-01-01",
}


def test_narrative_without_token_is_rejected(client):
    response = client.post("/narrative", json={"tone": "encouraging"})

    assert response.status_code == 401


def test_narrative_without_transactions_returns_400(client, auth_headers):
    response = client.post("/narrative", json={"tone": "encouraging"}, headers=auth_headers)

    assert response.status_code == 400


def test_narrative_with_invalid_tone_rejected(client, auth_headers):
    client.post("/transactions", json=SAMPLE_TRANSACTION, headers=auth_headers)

    response = client.post(
        "/narrative", json={"tone": "not-a-real-tone"}, headers=auth_headers
    )

    assert response.status_code == 422


def test_narrative_success_returns_generated_text(client, auth_headers, monkeypatch):
    client.post("/transactions", json=SAMPLE_TRANSACTION, headers=auth_headers)

    def fake_generate_narrative(transactions, tone):
        return f"Fake narrative for tone={tone}"

    monkeypatch.setattr(narrative_module, "generate_narrative", fake_generate_narrative)

    response = client.post(
        "/narrative", json={"tone": "analyst"}, headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json() == {"narrative": "Fake narrative for tone=analyst"}


def test_narrative_uses_default_tone_when_omitted(client, auth_headers, monkeypatch):
    client.post("/transactions", json=SAMPLE_TRANSACTION, headers=auth_headers)

    captured_tone = {}

    def fake_generate_narrative(transactions, tone):
        captured_tone["value"] = tone
        return "ok"

    monkeypatch.setattr(narrative_module, "generate_narrative", fake_generate_narrative)

    response = client.post("/narrative", json={}, headers=auth_headers)

    assert response.status_code == 200
    assert captured_tone["value"] == "encouraging"


def test_narrative_missing_api_key_returns_500(client, auth_headers, monkeypatch):
    client.post("/transactions", json=SAMPLE_TRANSACTION, headers=auth_headers)

    def fake_generate_narrative(transactions, tone):
        raise RuntimeError("Missing OPENROUTER_API_KEY. Add it to your .env file.")

    monkeypatch.setattr(narrative_module, "generate_narrative", fake_generate_narrative)

    response = client.post(
        "/narrative", json={"tone": "encouraging"}, headers=auth_headers
    )

    assert response.status_code == 500


def test_narrative_provider_failure_returns_502(client, auth_headers, monkeypatch):
    client.post("/transactions", json=SAMPLE_TRANSACTION, headers=auth_headers)

    def fake_generate_narrative(transactions, tone):
        raise Exception("Something went wrong talking to the AI provider")

    monkeypatch.setattr(narrative_module, "generate_narrative", fake_generate_narrative)

    response = client.post(
        "/narrative", json={"tone": "encouraging"}, headers=auth_headers
    )

    assert response.status_code == 502


def test_narrative_only_summarizes_own_transactions(client, monkeypatch):
    # User 1 has a transaction
    client.post("/register", json={"email": "owner@example.com", "password": "pass123"})
    login1 = client.post(
        "/login", data={"username": "owner@example.com", "password": "pass123"}
    )
    headers1 = {"Authorization": f"Bearer {login1.json()['access_token']}"}
    client.post("/transactions", json=SAMPLE_TRANSACTION, headers=headers1)

    # User 2 has none -- should get 400 (nothing to summarize), never user 1's data
    client.post("/register", json={"email": "other@example.com", "password": "pass123"})
    login2 = client.post(
        "/login", data={"username": "other@example.com", "password": "pass123"}
    )
    headers2 = {"Authorization": f"Bearer {login2.json()['access_token']}"}

    def fake_generate_narrative(transactions, tone):
        # Mirrors the real generate_narrative's behavior for an empty list,
        # without actually calling the AI provider.
        if not transactions:
            raise narrative_module.NoTransactionsError()
        return "should not be reached for user 2 in this test"

    monkeypatch.setattr(narrative_module, "generate_narrative", fake_generate_narrative)

    response = client.post(
        "/narrative", json={"tone": "encouraging"}, headers=headers2
    )

    assert response.status_code == 400
