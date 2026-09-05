# MoneyNarrator API

Backend for MoneyNarrator, built with **Python + FastAPI**. This is a
backend-only project — there is no frontend yet (that comes later, in
JavaScript, once the API is complete and tested).

## Current status: Step 7 — AI narrative endpoint

Added:
- `app/services/ai_service.py` — aggregates a user's transactions
  (totals, spending by category, recent transactions) and calls an AI
  provider through OpenRouter's free model router to generate a written
  report
- `app/routers/narrative.py` — `POST /narrative`, an auth-protected
  endpoint that summarizes the **logged-in user's own transactions**
  (fetched from the database, not sent by the client) in a selectable
  tone

### Tones available

`encouraging` (default) &middot; `analyst` &middot; `blunt` &middot; `storyteller`

### Setup: add your OpenRouter key

1. Copy `.env.example` to `.env` if you haven't already.
2. Get a free key at https://openrouter.ai (Settings → Keys → Create
   Key) — no credit card required. This is the same key from the
   Next.js version of this project, if you still have it.
3. Put it in `.env` as `OPENROUTER_API_KEY=...`.

### Try it via the interactive docs

1. Authorize (register/login, click **Authorize**, paste the token).
2. Add at least one transaction via **POST /transactions** (see step 5
   instructions below) — the narrative endpoint has nothing to
   summarize otherwise and returns a 400 error.
3. Expand **POST /narrative**, "Try it out", body:
   ```json
   { "tone": "encouraging" }
   ```
   Execute — you should get back a written report based on your real
   transactions.
4. Try the other tones (`analyst`, `blunt`, `storyteller`) to see how
   the report changes.

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

18 tests covering auth and transactions (see step 6 below). Narrative
endpoint tests come in step 8.

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
  requirements.txt     # fastapi, uvicorn, sqlalchemy, python-dotenv,
                        # email-validator, python-jose, bcrypt,
                        # python-multipart, pytest, httpx2, openai
  .env.example          # DATABASE_URL + SECRET_KEY + OPENROUTER_API_KEY template
  .gitignore
  README.md
```

Next: pytest tests for the narrative endpoint with the AI call mocked
(step 8), then the JavaScript frontend (step 9).
