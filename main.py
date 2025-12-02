from fastapi import FastAPI
from database import create_db_and_tables
import models
from routers.benchmark import router as benchmark_router
from routers.analisis import router as analisis_router
from routers.cancion import router as cancion_router
from routers.spotify_auth import router as spotify_auth_router


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
app.include_router(analisis_router)
app.include_router(spotify_auth_router)

# Ruta de prueba
@app.get("/")
def read_root():
    return {"message": "Spotrend API is running. Check /docs for endpoints."}