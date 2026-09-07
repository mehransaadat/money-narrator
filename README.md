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

Next: Docker + stress testing, then the JavaScript frontend.
