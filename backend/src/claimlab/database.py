"""SQLAlchemy database engine and session management."""
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from claimlab.config import settings

# Ensure SQLite data directory exists
if settings.DATABASE_URL.startswith("sqlite:///"):
    raw_path = settings.DATABASE_URL.replace("sqlite:///", "")
    if raw_path != ":memory:":
        db_file = Path(raw_path).resolve()
        db_file.parent.mkdir(parents=True, exist_ok=True)

# SQLite configuration with check_same_thread=False for multi-threaded FastAPI
connect_args = {"check_same_thread": False, "timeout": 30}
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=(settings.APP_ENV == "development_debug"),
)

# Enable Foreign Keys and WAL mode for SQLite
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
