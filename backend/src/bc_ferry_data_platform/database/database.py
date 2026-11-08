"""File to establish the session for SQLAlchemy."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bc_ferry_data_platform.config.settings import settings

engine = create_engine(settings.database_url)

SessionLocal = sessionmaker( # pylint: disable=invalid-name
    autocommit=False,
    autoflush=False,
    bind=engine,
)
