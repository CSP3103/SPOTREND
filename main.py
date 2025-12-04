from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from database import create_db_and_tables
from routers import (
    cancion, artista, benchmark, analisis,
    analisis, eliminados, comparar_spotify,
    spotify_info, recomendaciones, dashboard, comparacion_local
)
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="🎧 Spotrend - Plataforma Musical Inteligente",
    description="Análisis, comparación y recomendaciones musicales",
    version="3.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configuración para templates
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup():
    try:
        create_db_and_tables()
        logger.info("✅ Base de datos y tablas creadas")
    except Exception as e:
        logger.error(f"⚠  Error creando tablas: {e}")

# Incluir todos los routers (ESTOS YA MANEJAN SUS HTML)
app.include_router(cancion.router)
app.include_router(artista.router)
app.include_router(benchmark.router)
app.include_router(analisis.router)
app.include_router(analisis.router)
app.include_router(eliminados.router)
app.include_router(comparar_spotify.router)
app.include_router(spotify_info.router)
app.include_router(recomendaciones.router)
app.include_router(dashboard.router)
app.include_router(comparacion_local.router)

# SOLO LA PÁGINA PRINCIPAL
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Menú principal"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app": "Spotrend",
        "version": "3.0"
    })

# Mantener el endpoint JSON para la API
@app.get("/api")
def api_home():
    return {
        "app": "Spotrend API",
        "version": "3.0",
        "status": "✅ Online",
        "endpoints": {
            "canciones": "/canciones",
            "artistas": "/artistas",
            "benchmarks": "/benchmarks",
            "analisis": "/analisis-v2/cancion/{id}",
            "recomendaciones": "/recomendaciones/cancion/{id}",
            "comparar_spotify": "/comparar/cancion/{id}",
            "dashboard": "/dashboard",
            "documentacion": "/api/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Spotrend API"}