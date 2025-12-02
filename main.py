
from fastapi import FastAPI
from database import create_db_and_tables
import models # Se importa para que SQLModel sepa de los modelos
from routers.benchmark import router as benchmark_router
from routers.cancion import router as cancion_router

# Nombre del Proyecto Actualizado
app = FastAPI(title="Spotrend API - Comparador de Tendencias")

# Evento de inicio: crear tablas en Supabase
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    print("FastAPI listo. Tablas inicializadas.")

# Incluir Routers
app.include_router(benchmark_router)
app.include_router(cancion_router)

# Ruta de prueba
@app.get("/")
def read_root():
    return {"message": "Spotrend API is running. Check /docs for endpoints."}