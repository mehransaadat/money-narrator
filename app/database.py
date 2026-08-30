import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Defaults to a local SQLite file if DATABASE_URL isn't set in .env,
# so the project runs out of the box with zero extra setup.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./money_narrator.db")

# check_same_thread is only needed for SQLite; harmless to always pass it
# since it's ignored by other database backends (e.g. PostgreSQL later).
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
