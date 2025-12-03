# routers/benchmark.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import Optional, List
from datetime import datetime
import requests
import models
from database import get_session

# from routers.spotify_auth import get_spotify_token_dependency # Asumir el servicio de token

router = APIRouter(prefix="/benchmark", tags=["Benchmark (Tendencias)"])
Benchmark = models.Benchmark

API_URL = "https://api.spotify.com/v1"  # URL base de Spotify


# Esquema para la entrada del POST manual
class BenchmarkCreate(models.SQLModel):
    pais: str
    genero: str
    tempo_promedio: float
    energy_promedio: float


# 1. CREATE (POST Manual)
@router.post("/", response_model=Benchmark, status_code=status.HTTP_201_CREATED)
def create_benchmark(*, session: Session = Depends(get_session), benchmark: BenchmarkCreate):
    """Crea un Benchmark manualmente (uso de administrador)."""
    db_benchmark = Benchmark.model_validate(benchmark.model_dump())
    session.add(db_benchmark)
    session.commit()
    session.refresh(db_benchmark)
    return db_benchmark


# 2. READ (Lista de ACTIVOS) - Filtrado por Soft Delete
@router.get("/", response_model=List[Benchmark])
def read_benchmarks(*, session: Session = Depends(get_session)):
    """Obtiene la lista de Benchmarks (Tendencias) que NO están eliminadas (ACTIVOS)."""
    benchmarks = session.exec(select(Benchmark).where(Benchmark.deleted_at == None)).all()
    return benchmarks


# 3. READ (Detalle) - Con manejo de error 404
@router.get("/{benchmark_id}", response_model=Benchmark)
def read_benchmark(*, session: Session = Depends(get_session), benchmark_id: int):
    """Obtiene el detalle de un Benchmark activo por ID."""
    benchmark = session.get(Benchmark, benchmark_id)

    if not benchmark or benchmark.deleted_at:
        raise HTTPException(status_code=404, detail="Benchmark no encontrado o inactivo.")

    return benchmark


# 4. DELETE (Soft Delete y errores 404/409)
@router.delete("/{benchmark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_benchmark(*, session: Session = Depends(get_session), benchmark_id: int):
    """Elimina LÓGICAMENTE un Benchmark (Soft Delete)."""
    benchmark = session.get(Benchmark, benchmark_id)

    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark no encontrado.")

    if benchmark.deleted_at:
        raise HTTPException(status_code=409, detail="El benchmark ya fue eliminado lógicamente.")

    benchmark.deleted_at = datetime.utcnow()

    session.add(benchmark)
    session.commit()
    return


# 5. GET /history (Historial de Eliminaciones)
@router.get("/history", response_model=List[Benchmark])
def read_deleted_benchmarks(*, session: Session = Depends(get_session)):
    """Obtiene la lista de Benchmarks que están ELIMINADOS LÓGICAMENTE (Historial de Trazabilidad)."""
    benchmarks_eliminados = session.exec(select(Benchmark).where(Benchmark.deleted_at != None)).all()
    return benchmarks_eliminados


# 6. POST /restore (Recuperar Registro)
@router.post("/restore/{benchmark_id}", response_model=Benchmark)
def restore_benchmark(*, session: Session = Depends(get_session), benchmark_id: int):
    """Recupera un registro eliminado lógicamente (Pone deleted_at a NULL)."""
    benchmark = session.get(Benchmark, benchmark_id)

    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark no encontrado.")

    if benchmark.deleted_at is None:
        raise HTTPException(status_code=409, detail="El benchmark no está eliminado, no se puede restaurar.")

    benchmark.deleted_at = None

    session.add(benchmark)
    session.commit()
    session.refresh(benchmark)
    return benchmark


# 7. GENERACIÓN DE INTELIGENCIA DE MERCADO (Endpoint 20/20)
@router.post("/generate_from_spotify", response_model=Benchmark, status_code=status.HTTP_201_CREATED)
def generate_benchmark_from_spotify(
        pais: str,
        genero: str,
        # token: str = Depends(get_spotify_token_dependency), # Asume que el token se obtiene de otro router/servicio
        session: Session = Depends(get_session)
):
    """
    Genera el Benchmark calculando los promedios de las métricas de las canciones más populares 
    de un género/país, usando la API de Spotify.
    """
    token = "FAKE_SPOTIFY_TOKEN"  # USAR EL TOKEN REAL AQUÍ

    headers = {"Authorization": f"Bearer {token}"}

    # Simulación de IDs de Top Tracks (En la realidad, se usaría /search o listas de Spotify)
    track_ids = ["3e05t3L9tCjSg9XJ5dF7P3", "7mFqj1yFp9x5t9X4x4W5C4", "7k1j1S5j1A8g6J4e4D7j7E"]
    tracks_str = ",".join(track_ids)

    # 1. Obtener las Audio Features de esas canciones
    try:
        features_response = requests.get(
            f"{API_URL}/audio-features?ids={tracks_str}",
            headers=headers
        )
        features_response.raise_for_status()  # Lanza error HTTP si el status es 4xx o 5xx
        features_data = features_response.json()
    except requests.exceptions.HTTPError as e:
        # Manejo de error HTTP 500 o 401/403 de la API externa
        status_code = e.response.status_code if e.response is not None else 500
        detail = f"Fallo en la conexión o autenticación con Spotify (Error: {status_code})."
        raise HTTPException(status_code=status_code, detail=detail)

    # 2. Calcular los Promedios
    features_list = features_data.get('audio_features', [])
    valid_features = [f for f in features_list if f is not None]

    if not valid_features:
        # Manejo de error 404 (Spotify no devolvió datos)
        raise HTTPException(status_code=404,
                            detail=f"Spotify no encontró métricas válidas para el género {genero} en {pais}.")

    total_tempo = sum(f.get('tempo', 0) for f in valid_features)
    total_energy = sum(f.get('energy', 0) for f in valid_features)
    count = len(valid_features)

    avg_tempo = round(total_tempo / count, 2)
    avg_energy = round(total_energy / count, 2)

    # 3. Crear o Actualizar el Benchmark
    db_benchmark = Benchmark(
        pais=pais,
        genero=genero,
        tempo_promedio=avg_tempo,
        energy_promedio=avg_energy
    )
    session.add(db_benchmark)
    session.commit()
    session.refresh(db_benchmark)
    return db_benchmark