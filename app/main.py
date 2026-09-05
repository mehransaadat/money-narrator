from fastapi import Depends, FastAPI

from .database import Base, engine
from . import models, schemas  # noqa: F401 - imported so Base knows about the models
from .dependencies import get_current_user
from .routers import auth, transactions, narrative

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MoneyNarrator API")

app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(narrative.router)


@app.get("/")
def read_root():
    """Health-check / hello-world endpoint."""
    return {"message": "MoneyNarrator API is running"}


@app.get("/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(get_current_user)):
    """A simple protected endpoint to confirm auth works end-to-end."""
    return current_user
