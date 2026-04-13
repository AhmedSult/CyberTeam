from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_sqlite_columns() -> None:
    """إضافة أعمدة جديدة لقواعد SQLite الموجودة دون Alembic."""
    if engine.dialect.name != "sqlite":
        return
    with engine.begin() as conn:
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(controls)")).fetchall()}
        if "standard_title_ar" not in cols:
            conn.execute(text("ALTER TABLE controls ADD COLUMN standard_title_ar TEXT"))
        if "objective_ar" not in cols:
            conn.execute(text("ALTER TABLE controls ADD COLUMN objective_ar TEXT"))
        if "domain_ar" not in cols:
            conn.execute(text("ALTER TABLE controls ADD COLUMN domain_ar VARCHAR(128)"))
        if "evidence_guidance_ar" not in cols:
            conn.execute(text("ALTER TABLE controls ADD COLUMN evidence_guidance_ar TEXT"))
        dcols = {row[1] for row in conn.execute(text("PRAGMA table_info(departments)")).fetchall()}
        if "code" not in dcols:
            conn.execute(text("ALTER TABLE departments ADD COLUMN code VARCHAR(32)"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
