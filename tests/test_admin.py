from app.bootstrap import seed_admin


def _admin_headers(client, db_session):
    import os
    os.environ["ADMIN_EMAIL"] = "boss@example.com"
    os.environ["ADMIN_PASSWORD"] = "bosspass123"
    seed_admin(db_session)
    r = client.post("/login", data={"username": "boss@example.com", "password": "bosspass123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_admin_routes_require_login(client):
    assert client.get("/admin/stats").status_code == 401


def test_normal_user_gets_403(client, auth_headers):
    assert client.get("/admin/users", headers=auth_headers).status_code == 403
    assert client.get("/admin/stats", headers=auth_headers).status_code == 403


def test_seeded_admin_flag_in_me(client, db_session):
    h = _admin_headers(client, db_session)
    assert client.get("/me", headers=h).json()["is_admin"] is True


def test_admin_sees_stats_and_users(client, db_session, auth_headers):
    client.post("/transactions", headers=auth_headers, json={
        "type": "discretionary", "category": "Food", "description": "x",
        "amount": "12.50", "txn_date": "2026-01-02"})
    h = _admin_headers(client, db_session)
    stats = client.get("/admin/stats", headers=h).json()
    assert stats["total_users"] == 2 and stats["total_transactions"] == 1
    assert stats["top_expense_categories"][0]["category"] == "Food"
    users = client.get("/admin/users", headers=h).json()
    counts = {u["email"]: u["transaction_count"] for u in users}
    assert counts["fixture-user@example.com"] == 1


def test_admin_can_delete_user_but_not_self(client, db_session, auth_headers):
    h = _admin_headers(client, db_session)
    users = client.get("/admin/users", headers=h).json()
    me = next(u for u in users if u["is_admin"])
    other = next(u for u in users if not u["is_admin"])
    assert client.delete(f"/admin/users/{me['id']}", headers=h).status_code == 400
    assert client.delete(f"/admin/users/{other['id']}", headers=h).status_code == 204
    assert client.delete("/admin/users/9999", headers=h).status_code == 404


def test_description_is_optional(client, auth_headers):
    r = client.post("/transactions", headers=auth_headers, json={
        "type": "income", "category": "Salary", "amount": "100", "txn_date": "2026-01-02"})
    assert r.status_code == 201 and r.json()["description"] == "Salary"
