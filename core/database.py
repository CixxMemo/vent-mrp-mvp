"""Database engine and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.settings import get_settings
from core.models import Base
from modules.work_orders import service as work_order_service

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    # Migrate legacy work orders to line-based structure (idempotent)
    session = SessionLocal()
    try:
        work_order_service.migrate_legacy_work_orders(session)
    finally:
        session.close()


