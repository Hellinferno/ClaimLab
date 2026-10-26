"""SQLAlchemy database engine and session management."""
from pathlib import Path
from sqlalchemy import create_engine
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

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
