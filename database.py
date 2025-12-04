import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("⚠  Usando SQLite temporal")
    DATABASE_URL = "sqlite:///./spotrend.db"

engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    try:
        SQLModel.metadata.create_all(engine)
        print("✅ Base de datos lista :)")
    except Exception as e:
        print(f"⚠  Error creando tablas: {e}")

def get_session():
    try:
        with Session(engine) as session:
            yield session
    except SQLAlchemyError as e:
        print(f"❌ Error DB: {e}")
        raise