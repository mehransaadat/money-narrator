# MoneyNarrator API

Backend for MoneyNarrator, built with **Python + FastAPI**. This is a
backend-only project — there is no frontend yet (that comes later, in
JavaScript, once the API is complete and tested).

## Current status: Step 5 — Transactions CRUD endpoints

Added `app/routers/transactions.py`, with three endpoints, all requiring a
valid Bearer token (from `/login`) and all scoped to the logged-in user
only:

- `POST /transactions` — create a transaction (amount must be positive)
- `GET /transactions` — list your own transactions, most recent first
- `DELETE /transactions/{id}` — delete one of your own transactions
  (404 if it doesn't exist or belongs to someone else)

Each user only ever sees their own data — this is enforced in the
database query itself (`WHERE user_id = current_user.id`), not just in
the UI, so there's no way to accidentally leak another user's
transactions.

### Try it via the interactive docs

1. Authorize first (register/login, then click **Authorize** and paste
   the token — same as step 4).
2. Expand **POST /transactions**, "Try it out", fill in a JSON body like:
   ```json
   {
     "type": "discretionary",
     "category": "Dining Out",
     "description": "Lunch",
     "amount": "25.50",
     "txn_date": "2026-01-15"
   }
   ```
   Execute — you should get a 201 response with the created transaction
   (including its new `id`).
3. Expand **GET /transactions**, "Try it out", Execute — you should see
   the transaction you just created.
4. Expand **DELETE /transactions/{transaction_id}**, enter that `id`,
   Execute — should return 204. Running GET again should show it gone.

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
  requirements.txt     # fastapi, uvicorn, sqlalchemy, python-dotenv,
                        # email-validator, python-jose, bcrypt, python-multipart
  .env.example          # DATABASE_URL + SECRET_KEY template
  .gitignore
  README.md
```

More files (pytest suite, narrative endpoint) are added in the following
steps.
