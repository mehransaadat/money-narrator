"""Startup helpers: a tiny schema upgrade and the admin account seed."""
import os

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from . import models
from .auth import hash_password, verify_password
from .database import engine


def upgrade_schema() -> None:
    """create_all() never alters existing tables, so databases created before
    the admin feature (users table without is_admin) get the column added here.
    """
    insp = inspect(engine)
    if "users" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("users")}
    if "is_admin" not in cols:
        default = "FALSE" if engine.dialect.name == "postgresql" else "0"
        with engine.begin() as conn:
            conn.execute(
                text(f"ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT {default}")
            )


def seed_admin(db: Session) -> None:
    """Make sure the admin from ADMIN_EMAIL / ADMIN_PASSWORD (in .env) exists.
    Does nothing when those variables are not set.
    """
    email = os.getenv("ADMIN_EMAIL", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "")
    if not email or not password:
        return
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        db.add(models.User(email=email, hashed_password=hash_password(password), is_admin=True))
    else:
        user.is_admin = True
        if not verify_password(password, user.hashed_password):
            user.hashed_password = hash_password(password)
    db.commit()
