"""
Staged ramp-up for the Locust stress test (optional).

Load it together with the locustfile; Locust then ignores the -u / -r
flags and follows the stages below instead:

    locust -f locustfile.py,stress_shape.py --host http://api:8000

Why the ramp is slow
    Every new simulated user does register + login = 2 bcrypt operations
    (~0.2-0.4 s of CPU each on an i5-9300H). With 3 API workers that is
    only ~5-6 NEW users per second at best, so spawn rates above 5/s
    just measure "how fast can bcrypt hash", not your API.

Edit STAGES, or override without touching the file:
    STRESS_STAGES="60:20:2,180:50:3,300:100:4"
    (format: end_of_stage_in_seconds : target_users : spawn_rate_per_sec)

Safety stop
    If more than STRESS_ABORT_FAIL_RATIO (default 0.25) of the requests
    fail for STRESS_ABORT_SECONDS (default 15) seconds in a row -- or if
    every simulated user has dropped out -- the test ends by itself. The point is to find the breaking point, not to keep
    hammering a laptop that is already swapping.
"""

import os

from locust import LoadTestShape

DEFAULT_STAGES = [
    # (end_time_s, users, spawn_rate)
    (60, 20, 2),
    (180, 50, 3),
    (300, 100, 4),
    (420, 150, 4),
    (540, 200, 5),
    (660, 250, 5),
]


def _parse_stages(raw: str):
    stages = []
    for part in raw.split(","):
        end, users, rate = part.strip().split(":")
        stages.append((float(end), int(users), float(rate)))
    return stages


STAGES = _parse_stages(os.getenv("STRESS_STAGES", "")) if os.getenv("STRESS_STAGES") else DEFAULT_STAGES
ABORT_FAIL_RATIO = float(os.getenv("STRESS_ABORT_FAIL_RATIO", "0.25"))
ABORT_SECONDS = int(os.getenv("STRESS_ABORT_SECONDS", "15"))


class StagedRamp(LoadTestShape):
    def __init__(self):
        super().__init__()
        self._bad_seconds = 0
        self._last_check = 0.0

    def _should_abort(self, run_time: float) -> bool:
        # tick() is called about once a second; only count once per second.
        if run_time - self._last_check < 1:
            return False
        self._last_check = run_time

        # Users that fail to register/log in retire themselves (StopUser)
        # and Locust does not replace them. If every one is gone, the rest
        # of the schedule would just idle, so end it.
        if run_time > 20 and self.runner.user_count == 0:
            print(
                f"\nSTAGED RAMP: aborting at t={run_time:.0f}s -- no simulated "
                "users left (all of them failed to register/log in). "
                "Is the API up?"
            )
            return True

        total = self.runner.stats.total
        rps = total.current_rps
        if rps >= 5 and total.current_fail_per_sec / rps > ABORT_FAIL_RATIO:
            self._bad_seconds += 1
        else:
            self._bad_seconds = 0

        if self._bad_seconds >= ABORT_SECONDS:
            print(
                f"\nSTAGED RAMP: aborting at t={run_time:.0f}s -- more than "
                f"{ABORT_FAIL_RATIO:.0%} of requests failed for "
                f"{ABORT_SECONDS}s. Breaking point reached."
            )
            return True
        return False

    def tick(self):
        run_time = self.get_run_time()

        if self._should_abort(run_time):
            return None

        for end_time, users, spawn_rate in STAGES:
            if run_time < end_time:
                return users, spawn_rate
        return None  # all stages finished -> stop 
