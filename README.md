# MoneyNarrator API

Backend for MoneyNarrator, built with **Python + FastAPI**. This is a
backend-only project — there is no frontend yet (that comes later, in
JavaScript, once the API is complete and tested).

## Current status: Step 6 — pytest test suite

Added an automated test suite covering everything built in steps 2-5:

- `tests/conftest.py` — pytest fixtures: an isolated in-memory test
  database (separate from your real `money_narrator.db`) and a
  `TestClient` wired to use it, plus an `auth_headers` fixture that
  registers + logs in a throwaway user for tests that need to be
  authenticated
- `tests/test_auth.py` — 8 tests covering registration (success,
  duplicate email, invalid email) and login (success, wrong password,
  unknown email) and the `/me` endpoint (rejected without a token,
  works with one)
- `tests/test_transactions.py` — 10 tests covering create (success,
  rejected without a token, negative/zero amount rejected, invalid type
  rejected), list (only returns your own transactions), and delete
  (removes it, 404 on a missing one, can't delete someone else's)

**18 tests total, all passing.** These tests don't touch your real
database or the network — they spin up a fresh in-memory database for
each test, so running them is fast and never risks your real data.

### Run the tests

```bash
pytest -v
```

You should see all 18 tests pass. Run this any time you change the
backend to make sure nothing broke.

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
```

You'll know the virtual environment is active because your terminal prompt
will show `(venv)` at the start of the line.

## Run the server

```bash
uvicorn app.main:app --reload
```

On first run, this creates `money_narrator.db` (a SQLite file) in the
project folder, with the `users` and `transactions` tables already set up
— you'll see the file appear after starting the server. You can inspect it
with any SQLite browser if you're curious, but there's no need to for now.

Then open your browser to:

- http://127.0.0.1:8000 — should show `{"message":"MoneyNarrator API is running"}`
- http://127.0.0.1:8000/docs — FastAPI's automatic interactive API docs

Press `Ctrl+C` in the terminal to stop the server.

## Project structure so far

```
money-narrator-api/
  app/
    __init__.py
    main.py             # FastAPI app instance, root + /me endpoints
    database.py          # SQLAlchemy engine, session, get_db dependency
    models.py             # User and Transaction ORM models
    schemas.py             # Pydantic request/response schemas
    auth.py                 # password hashing + JWT create/verify
    dependencies.py          # get_current_user (reads the Bearer token)
    routers/
      __init__.py
      auth.py                # POST /register, POST /login
      transactions.py         # POST/GET/DELETE /transactions (auth-protected)
  tests/
    __init__.py
    conftest.py            # test DB fixture, test client, auth_headers fixture
    test_auth.py            # 8 tests: register, login, /me
    test_transactions.py     # 10 tests: create, list, delete
  requirements.txt     # fastapi, uvicorn, sqlalchemy, python-dotenv,
                        # email-validator, python-jose, bcrypt,
                        # python-multipart, pytest, httpx2
  .env.example          # DATABASE_URL + SECRET_KEY template
  .gitignore
  README.md
```

Next: the AI narrative endpoint (step 7) and its tests (step 8).
