"""Database Session Dependency for FastAPI."""
from collections.abc import Generator

from sqlalchemy.orm import Session

from .database import SessionLocal


def get_session() -> Generator[Session, None, None]:
    """Provide a database session to the FastAPI route."""
    with SessionLocal() as session:
        yield session
