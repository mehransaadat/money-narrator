# MoneyNarrator API

Backend for MoneyNarrator, built with **Python + FastAPI**. This is a
backend-only project — there is no frontend yet (that comes later, in
JavaScript, once the API is complete and tested).

## Current status: Step 4 — Auth endpoints (register, login, JWT)

Added:
- `app/auth.py` — password hashing (bcrypt) and JWT creation/verification
- `app/dependencies.py` — `get_current_user`, a reusable dependency that
  reads the `Authorization: Bearer <token>` header and resolves it to a
  logged-in user (or raises 401)
- `app/routers/auth.py` — two endpoints:
  - `POST /register` — create an account (email + password)
  - `POST /login` — exchange email + password for a JWT access token
- `GET /me` in `main.py` — a protected test endpoint that only works with
  a valid token, to prove the whole auth flow works end-to-end

### Try it via the interactive docs

1. Start the server and open http://127.0.0.1:8000/docs
2. Expand **POST /register**, click "Try it out", enter an email/password, execute
3. Expand **POST /login**, "Try it out", fill in the same email as
   `username` and your password, execute — copy the `access_token` from
   the response
4. Click the green **Authorize** button near the top of the page, paste
   the token, and click Authorize
5. Expand **GET /me**, "Try it out", execute — it should return your
   account instead of a 401 error

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
  requirements.txt     # fastapi, uvicorn, sqlalchemy, python-dotenv,
                        # email-validator, python-jose, bcrypt, python-multipart
  .env.example          # DATABASE_URL + SECRET_KEY template
  .gitignore
  README.md
```

More files (transactions router, pytest suite, narrative endpoint) are
added in the following steps.
