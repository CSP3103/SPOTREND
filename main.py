from fastapi import FastAPI
from database import create_db_and_tables
# from fastapi.staticfiles import StaticFiles  # COMENTA ESTA LÍNEA
# from fastapi.templating import Jinja2Templates  # COMENTA ESTA LÍNEA
from routers import cancion, artista, analisis, benchmark, spotify_auth, spotify_data

app = FastAPI(title="Spotrend API - Comparador de Tendencias Musicales")

# COMENTA TEMPORALMENTE ESTAS 2 LÍNEAS:
# app.mount("/static", StaticFiles(directory="static"), name="static")
# templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    print("✅ FastAPI listo. Tablas inicializadas.")

# Incluir routers
app.include_router(cancion.router)
app.include_router(artista.router)
app.include_router(analisis.router)
app.include_router(benchmark.router)
app.include_router(spotify_auth.router)
app.include_router(spotify_data.router)

@app.get("/")
def read_root():
    return {"message": "🎧 Spotrend API is running. Check /docs for endpoints."}