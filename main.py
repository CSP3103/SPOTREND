from fastapi import FastAPI
from database import create_db_and_tables
from routers import (
    cancion, artista, benchmark, analisis,
    analisis, eliminados, comparar_spotify,
    spotify_info, recomendaciones, dashboard
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

@app.on_event("startup")
async def startup():
    try:
        create_db_and_tables()
        logger.info("✅ Base de datos y tablas creadas")
    except Exception as e:
        logger.error(f"⚠  Error creando tablas: {e}")

# Incluir todos los routers
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

@app.get("/")
def home():
    return {
        "app": "Spotrend API",
        "version": "3.0",
        "status": "✅ Online",
        "endpoints_disponibles": {
            "canciones": "/canciones",
            "artistas": "/artistas",
            "benchmarks": "/benchmarks",
            "analisis_basico": "/analisis/cancion/{id}",
            "analisis_mejorado": "/analisis-v2/cancion/{id}",
            "tendencias": "/analisis-v2/tendencias",
            "eliminados": "/eliminados/canciones",
            "comparar_spotify": "/comparar/cancion/{id}",
            "info_spotify": "/spotify/info/artista/{id}",
            "recomendaciones": "/recomendaciones/cancion/{id}",
            "dashboard": "/dashboard",
            "documentacion": "/api/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Spotrend API", "timestamp": "2024-01-15T10:30:00Z"}