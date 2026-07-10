from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create database engine
# Pool configuration is optimized for production workloads
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Session local factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
