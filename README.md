# MoneyNarrator API

Backend for MoneyNarrator, built with **Python + FastAPI**. This is a
backend-only project — there is no frontend yet (that comes later, in
JavaScript, once the API is complete and tested).

## Current status: Step 3 — Pydantic schemas

Added `app/schemas.py`, which defines the exact shape of data the API
accepts and returns:

- `UserCreate` — what a client sends to register (email + password)
- `UserOut` — what the API sends back for a user (never includes the
  password)
- `TransactionCreate` — what a client sends to create a transaction
- `TransactionOut` — what the API sends back for a transaction

These are used by FastAPI to automatically validate incoming requests
(rejecting bad data with a clear error) and to control exactly what shape
of JSON goes out in responses. No new endpoints yet — those come in step 4.

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
    main.py           # FastAPI app instance + the root endpoint
    database.py        # SQLAlchemy engine, session, get_db dependency
    models.py           # User and Transaction ORM models
    schemas.py           # Pydantic request/response schemas
  requirements.txt     # fastapi, uvicorn, sqlalchemy, python-dotenv, email-validator
  .env.example          # DATABASE_URL template
  .gitignore
  README.md
```

More files (auth, routers, tests) are added in the following steps.
