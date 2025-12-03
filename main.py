from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import create_db_and_tables
from routers import cancion, artista, benchmark, analisis, spotify_auth, spotify_data
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="🎧 Spotrend - App Musical Inteligente",
    description="Sistema de análisis musical basado en benchmarks",
    version="2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)


# Crear tablas al iniciar
@app.on_event("startup")
async def startup():
    try:
        create_db_and_tables()
        logger.info("✅ Base de datos y tablas creadas exitosamente")
    except Exception as e:
        logger.error(f"⚠  Error creando tablas: {e}")


# Routers
app.include_router(cancion.router)
app.include_router(artista.router)
app.include_router(benchmark.router)
app.include_router(analisis.router)
app.include_router(spotify_auth.router)
app.include_router(spotify_data.router)


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
        <head>
            <title>🎧 Spotrend - API</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    background: #1a1a1a;
                    color: white;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                }
                h1 {
                    color: #1DB954;
                }
                .endpoint {
                    background: #2a2a2a;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 8px;
                }
                a {
                    color: #1DB954;
                    text-decoration: none;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎧 Spotrend API</h1>
                <p>Sistema de análisis musical inteligente</p>

                <div class="endpoint">
                    <strong>📚 Documentación:</strong><br>
                    <a href="/api/docs">Swagger UI</a> | 
                    <a href="/api/redoc">ReDoc</a>
                </div>

                <div class="endpoint">
                    <strong>🎵 Canciones:</strong><br>
                    GET /canciones - Listar todas<br>
                    POST /canciones - Crear nueva<br>
                    GET /canciones/{id} - Obtener por ID<br>
                    PUT /canciones/{id} - Actualizar<br>
                    DELETE /canciones/{id} - Eliminar (soft)
                </div>

                <div class="endpoint">
                    <strong>👨‍🎤 Artistas:</strong><br>
                    GET /artistas - Listar todos<br>
                    POST /artistas - Crear nuevo<br>
                    GET /artistas/{id} - Obtener por ID<br>
                    PUT /artistas/{id} - Actualizar<br>
                    DELETE /artistas/{id} - Eliminar (soft)
                </div>

                <div class="endpoint">
                    <strong>📊 Benchmarks:</strong><br>
                    GET /benchmarks - Listar todos<br>
                    POST /benchmarks - Crear nuevo<br>
                    GET /benchmarks/{id} - Obtener por ID<br>
                    PUT /benchmarks/{id} - Actualizar<br>
                    DELETE /benchmarks/{id} - Eliminar (soft)
                </div>

                <div class="endpoint">
                    <strong>🔍 Análisis:</strong><br>
                    GET /analisis/cancion/{id} - Analizar canción<br>
                    GET /analisis/historial/{id} - Ver historial
                </div>
            </div>
        </body>
    </html>
    """


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Spotrend API"}


# Manejo de errores global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error no manejado en {request.url}: {exc}")
    return {
        "error": "Error interno del servidor",
        "message": str(exc)[:200]
    }