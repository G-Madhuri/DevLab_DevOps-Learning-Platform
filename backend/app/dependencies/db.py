from typing import Generator
from app.db.session import SessionLocal

def get_db() -> Generator:
    """
    Dependency generator for database sessions.
    Yields an active SQLAlchemy session, ensuring it is closed after request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
