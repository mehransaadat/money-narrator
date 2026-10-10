from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .bootstrap import seed_admin, upgrade_schema
from .database import Base, SessionLocal, engine
from . import models, schemas  # noqa: F401 - imported so Base knows about the models
from .dependencies import get_current_user
from .routers import admin, auth, transactions, narrative

Base.metadata.create_all(bind=engine)
upgrade_schema()
with SessionLocal() as _db:
    seed_admin(_db)

app = FastAPI(title="MoneyNarrator API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(narrative.router)
app.include_router(admin.router)


@app.get("/")
def read_root():
    """Health-check / hello-world endpoint."""
    return {"message": "MoneyNarrator API is running"}


@app.get("/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    """A simple protected endpoint to confirm auth works end-to-end."""
    return current_user


# The website itself: open http://127.0.0.1:8000/app/ after starting the server.
_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if _FRONTEND_DIR.is_dir():
    app.mount("/app", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
