from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from database import get_session
from models import AnalisisResultado, Cancion, Benchmark
from utils.analisis_logic import calcular_afinidad_y_hallazgo
from typing import List
import uuid

# Define el modelo de entrada simple para crear un análisis (solo necesitamos los IDs)
from pydantic import BaseModel


class AnalisisCreate(BaseModel):
    cancion_id: uuid.UUID
    benchmark_id: int


router = APIRouter(prefix="/analisis", tags=["Analisis (Core de Spotrend)"])


# 1. CREATE (El endpoint crucial)
@router.post("/", response_model=AnalisisResultado, status_code=status.HTTP_201_CREATED)
def create_analisis(
        *,
        session: Session = Depends(get_session),
        analisis_data: AnalisisCreate
):
    """
    Realiza el análisis de afinidad entre una Cancion y un Benchmark,
    calcula el score y guarda el resultado estratégico.
    """
    # 1. Obtener la Canción y el Benchmark de la DB
    cancion = session.get(Cancion, analisis_data.cancion_id)
    benchmark = session.get(Benchmark, analisis_data.benchmark_id)

    if not cancion:
        raise HTTPException(status_code=404, detail="Canción no encontrada")
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark no encontrado")

    # 2. Ejecutar la Lógica de Negocio Central (Cálculo)
    afinidad_score, hallazgo_texto = calcular_afinidad_y_hallazgo(
        cancion_tempo=cancion.tempo,
        cancion_energy=cancion.energy,
        benchmark_tempo=benchmark.tempo_promedio,
        benchmark_energy=benchmark.energy_promedio,
        benchmark_pais=benchmark.pais,
        benchmark_genero=benchmark.genero
    )

    # 3. Crear y Guardar el objeto AnalisisResultado
    nuevo_analisis = AnalisisResultado(
        cancion_id=analisis_data.cancion_id,
        benchmark_id=analisis_data.benchmark_id,
        afinidad=afinidad_score,
        hallazgo=hallazgo_texto
    )

    session.add(nuevo_analisis)
    session.commit()
    session.refresh(nuevo_analisis)

    return nuevo_analisis


# 2. READ (Lista - Opcional)
@router.get("/", response_model=List[AnalisisResultado])
def read_analisis_list(*, session: Session = Depends(get_session)):
    """Obtiene la lista completa de todos los resultados de análisis."""
    analisis_results = session.exec(select(AnalisisResultado)).all()
    return analisis_results


# 3. READ (Detalle de un Análisis)
@router.get("/{analisis_id}", response_model=AnalisisResultado)
def read_analisis(*, session: Session = Depends(get_session), analisis_id: uuid.UUID):
    """Obtiene un resultado de Análisis por su ID."""
    analisis = session.get(AnalisisResultado, analisis_id)
    if not analisis:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    return analisis


# 4. DELETE
@router.delete("/{analisis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analisis(*, session: Session = Depends(get_session), analisis_id: uuid.UUID):
    """Elimina un resultado de Análisis."""
    analisis = session.get(AnalisisResultado, analisis_id)
    if not analisis:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    session.delete(analisis)
    session.commit()
    return {"ok": True}