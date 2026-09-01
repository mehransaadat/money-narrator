import os
from datetime import datetime, timedelta, timezone

import bcrypt
from dotenv import load_dotenv
from jose import JWTError, jwt

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def hash_password(password: str) -> str:
    """Hash a plain-text password for storage. Never store plain passwords."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain-text password against a stored bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(subject: str) -> str:
    """Create a signed JWT containing `subject` (typically the user's email),
    with a fixed expiry, using our SECRET_KEY.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Verify and decode a JWT. Returns the subject (email) if valid, else None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
