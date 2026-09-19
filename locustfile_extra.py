"""
Special-purpose Locust scenarios, kept apart from locustfile.py on purpose:
Locust starts EVERY user class it finds in the file you pass with -f, so
mixing these into the main file would silently start them in the normal
test as well.

Pick one class by name:
    locust -f locustfile_extra.py --host http://127.0.0.1:8000 AuthStressUser
    locust -f locustfile_extra.py --host http://127.0.0.1:8000 NarrativeUser

With Docker (the compose "locust" service, web UI on http://localhost:8089):
    docker compose run --rm --service-ports locust \
        -f /mnt/locust/locustfile_extra.py --host http://api:8000 AuthStressUser
"""

from locust import HttpUser, between, task
from locust.exception import StopUser

# Importing these names (and only these) means Locust does not see
# MoneyNarratorUser in this module.
from locustfile import _check, _register_and_login


class AuthStressUser(HttpUser):
    """CPU worst case: a brand-new account + login on every iteration.

    Run:  locust -f locustfile_extra.py AuthStressUser
    Use a LOW user count (5-20): each iteration costs two bcrypt
    operations (~0.2-0.4 s of CPU each), so a few users already
    saturate the API container.
    """

    wait_time = between(0.5, 1.5)

    @task
    def register_then_login(self):
        _register_and_login(self, "authstress")


class NarrativeUser(HttpUser):
    """POST /narrative -- calls the real OpenRouter API.

    Run explicitly, with 1-2 users:
        locust -f locustfile_extra.py NarrativeUser
    """

    wait_time = between(10, 20)

    def on_start(self):
        self.headers = _register_and_login(self, "narrtest")
        if self.headers is None:
            raise StopUser()

        # /narrative returns 400 when the user has no transactions.
        with self.client.post(
            "/transactions",
            json={
                "type": "income",
                "category": "Salary",
                "description": "Load test income",
                "amount": "1000.00",
                "txn_date": "2026-01-01",
            },
            headers=self.headers,
            name="/transactions [POST]",
            catch_response=True,
        ) as r:
            if not _check(r, 201):
                raise StopUser()

    @task
    def generate_narrative(self):
        with self.client.post(
            "/narrative",
            json={"tone": "encouraging"},
            headers=self.headers,
            name="/narrative",
            catch_response=True,
        ) as r:
            _check(r, 200)
