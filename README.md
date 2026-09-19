# MoneyNarrator API

Backend for MoneyNarrator, built with **Python + FastAPI**. This is a
backend-only project — there is no frontend yet (that comes later, in
JavaScript, once the API is complete and tested).

## Current status: Step 8 — Tests for the narrative endpoint (mocked AI provider)

Added `tests/test_narrative.py` — 8 tests covering the `/narrative`
endpoint, using pytest's `monkeypatch` to replace the real
`generate_narrative` function with a fake one. This means these tests:

- Never make a real network call to OpenRouter (fast, free, and don't
  depend on your internet connection or API key)
- Still verify the endpoint's actual logic: auth is required, a 400 is
  returned when there are no transactions, invalid tones are rejected
  by Pydantic, the default tone is used when omitted, provider errors
  turn into the right HTTP status codes (500 for a config problem, 502
  for a provider failure), and a user only ever gets a report about
  their own transactions

**26 tests total, all passing.**

### Run all the tests

```bash
pytest -v
```

## Requirements

- Python 3.11 or newer (`python --version` to check)

## Setup (run once)

```bash
# 1. Create a virtual environment
python -m venv venv

# 2. Activate it
#    Windows (PowerShell):
venv\Scripts\Activate.ps1
#    Windows (cmd.exe):
venv\Scripts\activate.bat
#    macOS / Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your .env file
cp .env.example .env
# then edit .env and fill in SECRET_KEY and OPENROUTER_API_KEY
```

## Run the server

```bash
uvicorn app.main:app --reload
```

- http://127.0.0.1:8000 — health check
- http://127.0.0.1:8000/docs — interactive API docs

## Run the tests

```bash
pytest -v
```

26 tests total: 8 auth, 10 transactions, 8 narrative (see step 8 above).
All run fast and never touch the network or a real database file.

## Using the AI narrative endpoint manually

### Tones available

`encouraging` (default) &middot; `analyst` &middot; `blunt` &middot; `storyteller`

### Setup: add your OpenRouter key

1. Copy `.env.example` to `.env` if you haven't already.
2. Get a free key at https://openrouter.ai (Settings → Keys → Create
   Key) — no credit card required.
3. Put it in `.env` as `OPENROUTER_API_KEY=...`.

### Try it via the interactive docs

1. Authorize (register/login, click **Authorize**, paste the token).
2. Add at least one transaction via **POST /transactions** — the
   narrative endpoint has nothing to summarize otherwise and returns a
   400 error.
3. Expand **POST /narrative**, "Try it out", body:
   ```json
   { "tone": "encouraging" }
   ```
   Execute — you should get back a written report based on your real
   transactions. This calls the real AI provider, so it takes a few
   seconds and requires your `OPENROUTER_API_KEY` to be set.
4. Try the other tones (`analyst`, `blunt`, `storyteller`) to see how
   the report changes.

## Project structure so far

```
money-narrator-api/
  app/
    __init__.py
    main.py             # FastAPI app instance, wires up all routers
    database.py          # SQLAlchemy engine, session, get_db dependency
    models.py             # User and Transaction ORM models
    schemas.py             # Pydantic request/response schemas
    auth.py                 # password hashing + JWT create/verify
    dependencies.py          # get_current_user (reads the Bearer token)
    routers/
      __init__.py
      auth.py                # POST /register, POST /login
      transactions.py         # POST/GET/DELETE /transactions
      narrative.py             # POST /narrative
    services/
      __init__.py
      ai_service.py            # aggregation + OpenRouter call
  tests/
    __init__.py
    conftest.py            # test DB fixture, test client, auth_headers fixture
    test_auth.py            # 8 tests: register, login, /me
    test_transactions.py     # 10 tests: create, list, delete
    test_narrative.py        # 8 tests: narrative endpoint (AI call mocked)
  requirements.txt     # fastapi, uvicorn, sqlalchemy, python-dotenv,
                        # email-validator, python-jose, bcrypt,
                        # python-multipart, pytest, httpx2, openai
  .env.example          # DATABASE_URL + SECRET_KEY + OPENROUTER_API_KEY template
  .gitignore
  README.md
```

## Running with Docker

Once you have Docker Desktop installed and running:

```bash
docker compose up --build
```

This builds the image and starts the API at http://127.0.0.1:8000 —
exactly the same endpoints as running it locally, just inside a
container. Press `Ctrl+C` to stop it.

To run it without docker-compose (plain Docker):

```bash
docker build -t money-narrator-api .
docker run -p 8000:8000 --env-file .env money-narrator-api
```

## Stress testing with Locust

`locustfile.py` simulates realistic traffic against the running API: each
simulated user registers and logs in **once**, then keeps listing /
creating / deleting transactions and calling `/me`. Every response is
checked against its expected status code (201 / 200 / 204), so the
"Failures" tab shows the real reason a request failed.

### 1. Give Docker the right resources (once)

Copy `wslconfig.example` to `C:\Users\<you>\.wslconfig`, then run
`wsl --shutdown` in PowerShell and restart Docker Desktop. This gives
Docker 8 GB of RAM and 6 of the 8 CPU threads. (If Docker Desktop uses the
Hyper-V backend instead of WSL 2, set the same values under
Settings -> Resources.)

`docker-compose.yml` splits that budget: `db` 2 CPUs / 2.5 GB,
`api` 3 CPUs / 3 GB (3 uvicorn workers), `locust` 1 CPU / 1 GB.

### 2. Web UI (manual control)

```bash
docker compose up -d --build db api
docker compose up locust
```

Open http://localhost:8089, enter users + spawn rate, click **Start**.

Keep the spawn rate at **5 users/s or less**: every new user costs two
bcrypt operations (register + login), which is what limits how fast users
can be added on this CPU.

### 3. Automatic staged run (recommended)

```bash
docker compose --profile load-test run --rm locust-headless
```

Follows the stages in `stress_shape.py` (20 -> 50 -> 100 -> 150 -> 200 ->
250 users, ~11 minutes), stops early if the API starts failing, and writes
`results/report.html` plus CSV files. Override the stages without editing
code, e.g. a 3-minute smoke run:

```bash
docker compose --profile load-test run --rm -e STRESS_STAGES="60:10:2,180:30:3" locust-headless
```

The run ends with `VERDICT: PASS/FAIL` (failures above 1 % or p95 above
2000 ms; adjust with `LOCUST_MAX_FAIL_RATIO` / `LOCUST_MAX_P95_MS`) and
the container's exit code follows it.

### Other scenarios (`locustfile_extra.py`)

```bash
# bcrypt / CPU worst case: new account + login on every iteration (5-20 users)
docker compose run --rm --service-ports locust -f /mnt/locust/locustfile_extra.py --host http://api:8000 AuthStressUser

# AI narrative endpoint: real OpenRouter calls, use 1-2 users only
docker compose run --rm --service-ports locust -f /mnt/locust/locustfile_extra.py --host http://api:8000 NarrativeUser
```

### Changing the number of API workers

```bash
API_WORKERS=4 docker compose up -d api
```

### What to look for

- **Response time climbing with users** is normal up to a point; a sharp
  cliff is the breaking point. Compare `/transactions [GET]` (pure
  database + JSON) against `/register` and `/login` (bcrypt, CPU).
- **Failures** -- open the Failures tab. `HTTP 500` together with
  `QueuePool limit ... reached` in `docker compose logs api` means
  SQLAlchemy's default pool (5 + 10 connections per worker) is too small
  for the request threads; raise `pool_size` / `max_overflow` in
  `app/database.py`.
- Check RAM/CPU during a run with `docker stats`.

### Cleaning up test data

Each run leaves its users in PostgreSQL. Remove them with:

```bash
docker compose exec db psql -U moneynarrator -c "DELETE FROM transactions WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'loadtest-%@example.com' OR email LIKE 'authstress-%@example.com' OR email LIKE 'narrtest-%@example.com'); DELETE FROM users WHERE email LIKE 'loadtest-%@example.com' OR email LIKE 'authstress-%@example.com' OR email LIKE 'narrtest-%@example.com';"
```

## Database-only stress test (bypasses the backend entirely)

The Locust test above measures your **whole API stack** under load
(FastAPI routing, JWT auth, bcrypt hashing, and the database all
together). `db_stress_test.py` instead connects **directly to
PostgreSQL** with `psycopg2` — no HTTP requests, no FastAPI, no
Pydantic, no bcrypt — to measure the database's own performance in
isolation.

By default it simulates **1000 concurrent users**, each doing:
1. `INSERT` one row into `users`
2. `INSERT` 5 rows into `transactions`
3. `SELECT` them back
4. `DELETE` about half of them

### Run it

```bash
docker compose --profile stress-test run --rm db-stress-test
```

This only starts `db` (if not already running) and the stress-test
script — it does **not** start or touch the `api` service at all.

### Reading the results

The script prints a summary like:
```
Total simulated users  : 1000
Successful              : 1000
Errors                  : 0
Total wall-clock time   : 4.82s
Throughput               : 207.5 simulated users/sec
Average latency per operation (successful runs only):
  INSERT users         : 3.21 ms
  INSERT transactions  : 9.84 ms  (for 5 rows)
  SELECT               : 1.05 ms
  DELETE               : 2.40 ms
```

- **Throughput** (simulated users/sec) is the headline number — how
  many complete user workflows PostgreSQL can process per second on
  your machine, with zero API overhead.
- **Errors** should be 0. If you see connection errors, PostgreSQL's
  `max_connections` (set to 300 in `docker-compose.yml` for this
  service) may need to be raised further, or `STRESS_MAX_CONCURRENT`
  lowered.
- Try changing the number of simulated users via an environment
  variable, e.g. for 2000 users:
  ```bash
  docker compose --profile stress-test run --rm -e STRESS_USERS=2000 db-stress-test
  ```

This number is a ceiling for your database alone; your actual API will
be slower than this because of the auth/hashing/routing overhead the
Locust test captures instead. Together, the two tests answer different
questions: `db_stress_test.py` answers "how fast is my database, at
most?" and Locust answers "how does my actual API behave under
realistic use?"

Next: the JavaScript frontend.
