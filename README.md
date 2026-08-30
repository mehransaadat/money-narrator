# MoneyNarrator API

Backend for MoneyNarrator, built with **Python + FastAPI**. This is a
backend-only project — there is no frontend yet (that comes later, in
JavaScript, once the API is complete and tested).

## Current status: Step 1 — Project skeleton

A minimal FastAPI app with a single health-check endpoint, to confirm the
project, virtual environment, and dependencies are all working before any
real features are added.

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
  requirements.txt     # fastapi, uvicorn
  .gitignore
  README.md
```

More files (`database.py`, `models.py`, `schemas.py`, routers, tests) are
added in the following steps.
