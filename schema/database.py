import os
from pathlib import Path

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

load_dotenv(Path(__file__).parent.parent / ".env")

# Models must be imported before create_all so SQLModel's metadata is populated
import schema.models  # noqa: F401, E402

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")

DB_LOCATION = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DB_LOCATION, echo=False, pool_pre_ping=True, pool_recycle=300)


def get_session():
    with Session(engine) as session:
        yield session


if __name__ == "__main__":
    """Create PostgreSQL database tables"""
    SQLModel.metadata.create_all(engine)
