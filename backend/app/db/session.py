import os
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///"):
    rel_path = db_url[len("sqlite:///"):]
    if not os.path.isabs(rel_path):
        repo_root = Path(__file__).resolve().parents[3]
        abs_file = (repo_root / rel_path).resolve()
        db_url = f"sqlite:///{abs_file.as_posix()}"

connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
engine = create_engine(db_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    from app.db.base import Base
    import app.models.user
    import app.models.detection

    Base.metadata.create_all(bind=engine)

    # Reconcile any missing columns in existing databases (SQLite / PostgreSQL)
    with engine.begin() as conn:
        insp = inspect(conn)
        if "detections" in insp.get_table_names():
            det_cols = {c["name"] for c in insp.get_columns("detections")}
            new_det_cols = [
                ("filename", "VARCHAR(255) DEFAULT ''"),
                ("confidence", "FLOAT DEFAULT 0.0"),
                ("processing_time_ms", "INTEGER DEFAULT 0"),
                ("model_version", "VARCHAR(100) DEFAULT ''"),
                ("metadata_json", "TEXT DEFAULT '{}'"),
            ]
            for col_name, col_type in new_det_cols:
                if col_name not in det_cols:
                    conn.execute(text(f"ALTER TABLE detections ADD COLUMN {col_name} {col_type}"))

        if "users" in insp.get_table_names():
            user_cols = {c["name"] for c in insp.get_columns("users")}
            new_user_cols = [
                ("is_active", "BOOLEAN DEFAULT 1"),
                ("organization", "VARCHAR(255) DEFAULT ''"),
            ]
            for col_name, col_type in new_user_cols:
                if col_name not in user_cols:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
