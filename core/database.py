"""Database engine and session management."""

from sqlalchemy import create_engine, text
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
    _migrate_work_orders_waste_factor_column()
    # Migrate legacy work orders to line-based structure (idempotent)
    session = SessionLocal()
    try:
        work_order_service.migrate_legacy_work_orders(session)
    finally:
        session.close()


def _migrate_work_orders_waste_factor_column() -> None:
    """Add work_orders.waste_factor for legacy SQLite databases (idempotent)."""
    if engine.dialect.name != "sqlite":
        return

    with engine.begin() as conn:
        columns = conn.execute(text("PRAGMA table_info(work_orders)")).fetchall()
        column_names = {row[1] for row in columns}
        if "waste_factor" not in column_names:
            conn.execute(text("ALTER TABLE work_orders ADD COLUMN waste_factor FLOAT DEFAULT 0"))
        conn.execute(text("UPDATE work_orders SET waste_factor = 0 WHERE waste_factor IS NULL"))


