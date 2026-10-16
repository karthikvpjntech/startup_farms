import logging
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger("agri_smart.database")

# Format Database URL for Supabase / PostgreSQL or SQLite
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    # Convert old Heroku/Supabase postgres:// format to postgresql+psycopg://
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
}

if db_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 15}
else:
    # PostgreSQL / Supabase Pool settings
    engine_kwargs["pool_recycle"] = 300
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

# Create SQLAlchemy Engine
engine = create_engine(
    db_url,
    **engine_kwargs
)

# Enable WAL Mode, Normal Synchronous, and Fast In-Memory Temp Store for SQLite
if db_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.execute("PRAGMA cache_size = -64000")  # 64MB memory cache
        cursor.execute("PRAGMA temp_store = MEMORY")
        cursor.execute("PRAGMA busy_timeout = 5000")
        cursor.close()

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Base model for all SQLAlchemy declarative models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency providing a scoped SQLAlchemy database session.
    Automatically closes session after request lifecycle completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
