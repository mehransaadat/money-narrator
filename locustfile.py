"""
Stress test for the MoneyNarrator API using Locust.

Each simulated user:
  1. Registers a brand-new account (unique email per user)
  2. Logs in to get a JWT
  3. Repeatedly creates transactions and lists them
  4. Occasionally deletes a transaction

The AI narrative endpoint is deliberately NOT included in the main load
test (see NarrativeUser below, run separately) because it calls a real,
rate-limited external AI provider -- hammering it with hundreds of
concurrent requests would just exhaust OpenRouter's free-tier limits
rather than test your own API's performance.

Run with:
    locust -f locustfile.py --host http://127.0.0.1:8000
Then open http://localhost:8089 in your browser to start a test.
"""

import random
import uuid

from locust import HttpUser, task, between


class MoneyNarratorUser(HttpUser):
    # Waits 1-3 seconds between tasks per simulated user, so the load
    # looks like real human usage rather than an unrealistic tight loop.
    wait_time = between(1, 3)

    def on_start(self):
        """Runs once per simulated user when it starts: register + log in."""
        unique_id = uuid.uuid4().hex[:10]
        self.email = f"loadtest-{unique_id}@example.com"
        self.password = "loadtestpass123"

        self.client.post(
            "/register",
            json={"email": self.email, "password": self.password},
            name="/register",
        )

        response = self.client.post(
            "/login",
            data={"username": self.email, "password": self.password},
            name="/login",
        )
        token = response.json().get("access_token", "")
        self.headers = {"Authorization": f"Bearer {token}"}
        self.created_ids = []

    @task(3)
    def create_transaction(self):
        """Weight 3: creating transactions is the most common action."""
        payload = {
            "type": random.choice(["income", "recurring", "discretionary"]),
            "category": random.choice(["Groceries", "Salary", "Dining Out", "Housing"]),
            "description": "Load test transaction",
            "amount": str(round(random.uniform(5, 500), 2)),
            "txn_date": "2026-01-15",
        }
        response = self.client.post(
            "/transactions", json=payload, headers=self.headers, name="/transactions [POST]"
        )
        if response.status_code == 201:
            self.created_ids.append(response.json()["id"])

    @task(5)
    def list_transactions(self):
        """Weight 5: listing/viewing is the most frequent read operation."""
        self.client.get(
            "/transactions", headers=self.headers, name="/transactions [GET]"
        )

    @task(1)
    def delete_transaction(self):
        """Weight 1: deleting is the least frequent action."""
        if self.created_ids:
            txn_id = self.created_ids.pop()
            self.client.delete(
                f"/transactions/{txn_id}",
                headers=self.headers,
                name="/transactions/:id [DELETE]",
            )


class NarrativeUser(HttpUser):
    """
    A separate, much lighter user class for the AI narrative endpoint.
    Run this on its own, with very few users (e.g. 1-2) and a long wait
    time, since it depends on OpenRouter's free-tier rate limits.

    Run with:
        locust -f locustfile.py --host http://127.0.0.1:8000 NarrativeUser
    """

    wait_time = between(10, 20)

    def on_start(self):
        unique_id = uuid.uuid4().hex[:10]
        self.email = f"narrtest-{unique_id}@example.com"
        self.password = "loadtestpass123"

        self.client.post(
            "/register", json={"email": self.email, "password": self.password}
        )
        response = self.client.post(
            "/login", data={"username": self.email, "password": self.password}
        )
        token = response.json().get("access_token", "")
        self.headers = {"Authorization": f"Bearer {token}"}

        # Needs at least one transaction to summarize.
        self.client.post(
            "/transactions",
            json={
                "type": "income",
                "category": "Salary",
                "description": "Load test income",
                "amount": "1000.00",
                "txn_date": "2026-01-01",
            },
            headers=self.headers,
        )

    @task
    def generate_narrative(self):
        self.client.post(
            "/narrative",
            json={"tone": "encouraging"},
            headers=self.headers,
            name="/narrative",
        )
