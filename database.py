import os
from dotenv import load_dotenv
from sqlmodel import create_engine, SQLModel, Session
from typing import Generator


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("La variable de entorno DATABASE_URL no está configurada.")

engine = create_engine(DATABASE_URL, echo=False, pool_recycle=3600)

def create_db_and_tables():
    """Crea la base de datos y todas las tablas definidas en models.py"""
    SQLModel.metadata.create_all(engine)
    print("Tablas y base de datos inicializadas correctamente.")

def get_session() -> Generator[Session, None, None]:
    """Genera una sesión de base de datos para usar con FastAPI Depends"""
    with Session(engine) as session:
        yield session