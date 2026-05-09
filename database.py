import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

URL_DATABASE = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/lectureagent"
)
engine = create_engine(
    URL_DATABASE,
    echo=False #true for debug
)
SessionLocal = sessionmaker(engine)
Base = declarative_base()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()