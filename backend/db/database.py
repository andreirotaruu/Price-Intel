from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

from backend.config import load_project_env

load_project_env()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()
