"""
Locust stress test for the MoneyNarrator backend (FastAPI + PostgreSQL).

WHAT IT MEASURES
    The whole stack under HTTP load: routing, Pydantic validation, JWT
    auth, bcrypt hashing, SQLAlchemy and PostgreSQL. (db_stress_test.py
    measures PostgreSQL alone; this file measures the real API.)

USER CLASS
    MoneyNarratorUser
        Realistic traffic. Each simulated user registers + logs in ONCE
        (like a real person opening the app), then keeps reusing its JWT:
        list / create / delete transactions, GET /me, GET /.

    Two special-purpose scenarios live in locustfile_extra.py so they can
    never start by accident together with this one:
        AuthStressUser  register + login on every iteration (bcrypt / CPU worst case)
        NarrativeUser   POST /narrative (real, rate-limited OpenRouter calls)

RUN (see docker-compose.yml -- everything runs inside Docker):
    docker compose up -d --build db api
    docker compose up locust               # web UI: http://localhost:8089

    # or fully automatic, no browser, with a report:
    docker compose --profile load-test run --rm locust-headless

TUNING via environment variables (all optional)
    LOCUST_WAIT_MIN / LOCUST_WAIT_MAX   think time between tasks, seconds (1 / 3)
    LOCUST_MAX_TXNS_PER_USER            cap on live transactions per user (100)
    LOCUST_MAX_FAIL_RATIO               exit code 1 if failures exceed this (0.01)
    LOCUST_MAX_P95_MS                   exit code 1 if overall p95 exceeds this (2000)
"""

import os
import random
import uuid
from datetime import date, timedelta

from locust import HttpUser, between, events, task
from locust.exception import StopUser

WAIT_MIN = float(os.getenv("LOCUST_WAIT_MIN", "1"))
WAIT_MAX = float(os.getenv("LOCUST_WAIT_MAX", "3"))
MAX_TXNS_PER_USER = int(os.getenv("LOCUST_MAX_TXNS_PER_USER", "100"))
MAX_FAIL_RATIO = float(os.getenv("LOCUST_MAX_FAIL_RATIO", "0.01"))
MAX_P95_MS = float(os.getenv("LOCUST_MAX_P95_MS", "2000"))

PASSWORD = "loadtestpass123"
TXN_TYPES = ["income", "recurring", "discretionary"]
CATEGORIES = ["Groceries", "Salary", "Dining Out", "Housing", "Transport", "Fun"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check(response, expected_status: int) -> bool:
    """Marks a catch_response request as success/failure by status code.

    Without this, Locust only fails on 4xx/5xx *codes*; here a 200 where a
    201 is expected (or the reverse) is also reported, and the failure
    message contains the server's answer, which makes the "Failures" tab
    actually useful.
    """
    if response.status_code == expected_status:
        response.success()
        return True
    response.failure(f"HTTP {response.status_code}: {response.text[:200]}")
    return False


def _register_and_login(user: HttpUser, prefix: str) -> dict | None:
    """Registers a fresh account, logs in, returns the auth headers.

    Returns None (and records failures) if either step fails, so callers
    never continue with an empty token and flood the log with 401s.
    """
    email = f"{prefix}-{uuid.uuid4().hex[:12]}@example.com"

    with user.client.post(
        "/register",
        json={"email": email, "password": PASSWORD},
        name="/register",
        catch_response=True,
    ) as r:
        if not _check(r, 201):
            return None

    with user.client.post(
        "/login",
        data={"username": email, "password": PASSWORD},
        name="/login",
        catch_response=True,
    ) as r:
        if not _check(r, 200):
            return None
        token = r.json().get("access_token")
        if not token:
            r.failure("login response has no access_token")
            return None

    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# User classes
# ---------------------------------------------------------------------------

class MoneyNarratorUser(HttpUser):
    """Realistic user: register/login once, then normal app usage."""

    weight = 1
    wait_time = between(WAIT_MIN, WAIT_MAX)

    def on_start(self):
        self.headers = _register_and_login(self, "loadtest")
        if self.headers is None:
            # Don't keep hammering with a broken session -- the failure is
            # already recorded, just retire this simulated user.
            raise StopUser()
        self.txn_ids: list[int] = []

    @task(5)
    def list_transactions(self):
        with self.client.get(
            "/transactions",
            headers=self.headers,
            name="/transactions [GET]",
            catch_response=True,
        ) as r:
            _check(r, 200)

    @task(3)
    def create_transaction(self):
        if len(self.txn_ids) >= MAX_TXNS_PER_USER:
            # Keeps GET /transactions (which is not paginated) from getting
            # slower and slower just because a user has piled up thousands
            # of rows; the test stays about the API, not about list size.
            return self.delete_transaction()

        payload = {
            "type": random.choice(TXN_TYPES),
            "category": random.choice(CATEGORIES),
            "description": "Load test transaction",
            "amount": f"{random.uniform(5, 500):.2f}",
            "txn_date": (date.today() - timedelta(days=random.randint(0, 365))).isoformat(),
        }
        with self.client.post(
            "/transactions",
            json=payload,
            headers=self.headers,
            name="/transactions [POST]",
            catch_response=True,
        ) as r:
            if _check(r, 201):
                self.txn_ids.append(r.json()["id"])

    @task(1)
    def delete_transaction(self):
        if not self.txn_ids:
            return
        txn_id = self.txn_ids.pop(random.randrange(len(self.txn_ids)))
        with self.client.delete(
            f"/transactions/{txn_id}",
            headers=self.headers,
            name="/transactions/:id [DELETE]",
            catch_response=True,
        ) as r:
            _check(r, 204)

    @task(1)
    def whoami(self):
        with self.client.get(
            "/me", headers=self.headers, name="/me", catch_response=True
        ) as r:
            _check(r, 200)

    @task(1)
    def health_check(self):
        with self.client.get("/", name="/ [health]", catch_response=True) as r:
            _check(r, 200)


# ---------------------------------------------------------------------------
# Pass/fail verdict (useful for headless runs and CI)
# ---------------------------------------------------------------------------

@events.quitting.add_listener
def _verdict(environment, **_kwargs):
    total = environment.stats.total
    if total.num_requests == 0:
        return

    p95 = total.get_response_time_percentile(0.95) or 0
    problems = []
    if total.fail_ratio > MAX_FAIL_RATIO:
        problems.append(f"failure ratio {total.fail_ratio:.2%} > {MAX_FAIL_RATIO:.2%}")
    if p95 > MAX_P95_MS:
        problems.append(f"p95 {p95:.0f} ms > {MAX_P95_MS:.0f} ms")

    if problems:
        print("\nVERDICT: FAIL -- " + "; ".join(problems))
        environment.process_exit_code = 1
    else:
        print(f"\nVERDICT: PASS -- failures {total.fail_ratio:.2%}, p95 {p95:.0f} ms")
        
