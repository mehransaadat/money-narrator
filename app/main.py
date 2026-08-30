from fastapi import FastAPI

from .database import Base, engine
from . import models  # noqa: F401 - imported so Base knows about the models

# Creates the database tables if they don't already exist.
# Fine for local development; a real migration tool (e.g. Alembic) would
# replace this once the schema needs to evolve safely in production.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MoneyNarrator API")


@app.get("/")
def read_root():
    """Health-check / hello-world endpoint.

    If you can see this response, the FastAPI server is running correctly.
    """
    return {"message": "MoneyNarrator API is running"}
