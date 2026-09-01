from fastapi import Depends, FastAPI

from .database import Base, engine
from . import models, schemas  # noqa: F401 - imported so Base knows about the models
from .dependencies import get_current_user
from .routers import auth

# Creates the database tables if they don't already exist.
# Fine for local development; a real migration tool (e.g. Alembic) would
# replace this once the schema needs to evolve safely in production.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MoneyNarrator API")

app.include_router(auth.router)


@app.get("/")
def read_root():
    """Health-check / hello-world endpoint.

    If you can see this response, the FastAPI server is running correctly.
    """
    return {"message": "MoneyNarrator API is running"}


@app.get("/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    """A simple protected endpoint to confirm auth works end-to-end:
    requires a valid Bearer token (from /login) and returns that user.
    """
    return current_user
