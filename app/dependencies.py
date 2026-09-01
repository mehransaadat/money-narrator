from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .auth import decode_access_token
from .database import get_db
from . import models

# tokenUrl just tells the auto-generated docs (/docs) which endpoint issues
# tokens -- it doesn't affect how this dependency validates a given token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """Resolves the Bearer token on the request into a User row, or raises 401."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    email = decode_access_token(token)
    if email is None:
        raise credentials_error

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_error

    return user
