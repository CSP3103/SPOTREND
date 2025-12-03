# routers/analisis.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from typing import List, Dict, Any
import uuid
import models
from database import get_session
import services.analisis_service as analisis_service  # Importamos el motor

# from services.spotify_service import fetch_audio_features # Asumir un servicio para Spotify

router = APIRouter(prefix="/analisis", tags=["Analisis y Hallazgos"])
templates = Jinja2Templates(directory="templates")  # Inicializar Jinja2

Cancion = models.Cancion
Benchmark = models.Benchmark
AnalisisResultado = models.AnalisisResultado


# =========================================================================
# 1. FUNCIÓN PRINCIPAL: CANCION VS BENCHMARK (Guarda Relación N:M y Reporte HTML)
# =========================================================================

@router.post("/run/{cancion_id}/{benchmark_id}", response_class=templates.TemplateResponse)
def run_analisis(
        request: Request,
        cancion_id: uuid.UUID,
        benchmark_id: int,
        session: Session = Depends(get_session)
):
    """
    Ejecuta el análisis de Distancia Euclidiana, guarda el resultado (relación N:M) 
    y genera un Reporte HTML de Hallazgos.
    """
    # 1. Obtener los recursos y manejar errores 404/Soft Delete
    cancion = session.get(Cancion, cancion_id)
    benchmark = session.get(Benchmark, benchmark_id)

    if not cancion or cancion.deleted_at:
        raise HTTPException(status_code=404, detail="Canción prototipo no encontrada o inactiva.")
    if not benchmark or benchmark.deleted_at:
        raise HTTPException(status_code=404, detail="Benchmark (Tendencia) no encontrado o inactivo.")

    # 2. Preparar objetos para el servicio de análisis
    cancion_obj = analisis_service.ObjetoAAnalizar(
        tempo=cancion.tempo, energy=cancion.energy,
        pais="N/A", genero="N/A"  # No se usa el contexto aquí
    )
    benchmark_obj = analisis_service.ObjetoAAnalizar(
        tempo_promedio=benchmark.tempo_promedio,
        energy_promedio=benchmark.energy_promedio,
        pais=benchmark.pais, genero=benchmark.genero  # Contexto para el hallazgo
    )

    # 3. Ejecutar el Motor de Cálculo
    afinidad_score, hallazgo_texto = analisis_service.calcular_afinidad_y_hallazgo(
        cancion_obj, benchmark_obj
    )

    # 4. Guardar la relación N:M y el resultado
    nuevo_analisis = AnalisisResultado(
        cancion_id=cancion_id,
        benchmark_id=benchmark_id,
        afinidad=afinidad_score,
        hallazgo=hallazgo_texto
    )
    session.add(nuevo_analisis)
    session.commit()
    session.refresh(nuevo_analisis)

    # 5. Generar Reporte HTML (Jinja2)
    context = {
        "request": request,
        "cancion": cancion,
        "benchmark": benchmark,
        "afinidad": afinidad_score,
        "hallazgo": hallazgo_texto,
        "analisis_id": nuevo_analisis.id
    }
    return templates.TemplateResponse("reporte.html", context)


# =========================================================================
# 2. HALLAZGO AVANZADO: SIMILITUD ENTRE ARTISTAS (Requiere Hallazgo Opcional)
# =========================================================================

@router.get("/similares/{cancion_id}", response_model=List[Dict[str, Any]])
def get_canciones_similares(
        cancion_id: uuid.UUID,
        session: Session = Depends(get_session)
):
    """
    Compara la canción prototipo contra todas las demás canciones en la DB (activas)
    para encontrar los prototipos rítmicos más cercanos ("Artistas Similares").
    """
    cancion_prototipo = session.get(Cancion, cancion_id)

    if not cancion_prototipo or cancion_prototipo.deleted_at:
        raise HTTPException(status_code=404, detail="Canción prototipo no encontrada o inactiva.")

    # Obtener todas las canciones activas para el catálogo
    todas_las_canciones = session.exec(select(Cancion)).all()

    # Ejecutar la lógica avanzada del servicio
    similares = analisis_service.encontrar_canciones_similares(
        cancion_prototipo, todas_las_canciones, top_n=5
    )

    return similares


# =========================================================================
# 3. ANÁLISIS RÁPIDO: CANCION VS CANCION (Al Vuelo, sin guardar) - Requisito Vs Song
# =========================================================================

@router.post("/vs_song")
def run_quick_vs_song(
        spotify_id_a: str,
        spotify_id_b: str,
        # token: str = Depends(get_spotify_token_dependency), # Requerido
        session: Session = Depends(get_session)
):
    """
    Compara dos canciones usando sus IDs de Spotify 'al vuelo' sin guardar nada en la DB.
    """
    token = "FAKE_TOKEN"  # Usar token real

    # 1. Simulación de obtención de features de Spotify (Necesitas un servicio real)
    features_a = {'tempo': 120.5, 'energy': 0.85, 'pais': 'Global', 'genero': 'Pop'}
    features_b = {'tempo': 125.0, 'energy': 0.70, 'pais': 'Global', 'genero': 'Reggaeton'}

    # Manejo de error 404 si Spotify no devuelve features
    if not features_a or not features_b:
        raise HTTPException(status_code=404, detail="No se pudieron obtener métricas de Spotify para uno o ambos IDs.")

    # 2. Preparar objetos para el análisis
    obj_a = analisis_service.ObjetoAAnalizar(**features_a)
    obj_b = analisis_service.ObjetoAAnalizar(**features_b)

    # 3. Ejecutar el Motor de Cálculo
    afinidad_score, hallazgo_texto = analisis_service.calcular_afinidad_y_hallazgo(
        obj_a, obj_b
    )

    return {
        "cancion_a": spotify_id_a,
        "cancion_b": spotify_id_b,
        "distancia_euclidiana": analisis_service.calcular_distancia_euclidiana(obj_a, obj_b),
        "afinidad_score": afinidad_score,
        "hallazgo": hallazgo_texto
    }


# =========================================================================
# 4. CRUD BÁSICO DE ANALISIS RESULTADO (Para consultar el historial)
# =========================================================================

@router.get("/", response_model=List[AnalisisResultado])
def read_analisis_resultados(*, session: Session = Depends(get_session)):
    """Obtiene el historial completo de todos los análisis realizados (Relaciones N:M)."""
    resultados = session.exec(select(AnalisisResultado)).all()
    return resultados


@router.delete("/{analisis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analisis(*, session: Session = Depends(get_session), analisis_id: int):
    """Elimina un registro de análisis del historial (Hard Delete es aceptable aquí)."""
    analisis = session.get(AnalisisResultado, analisis_id)

    if not analisis:
        raise HTTPException(status_code=404, detail="Análisis no encontrado.")

    session.delete(analisis)
    session.commit()
    return