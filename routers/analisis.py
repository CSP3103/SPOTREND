from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from uuid import UUID
from database import get_session
from models import Cancion, Benchmark, AnalisisResultado
from services.analisis_service import calcular_afinidad, clasificar_afinidad

router = APIRouter(prefix="/analisis", tags=["Análisis"])


@router.post("/cancion-vs-benchmark/{cancion_id}/{benchmark_id}")
def analizar_cancion_vs_benchmark(
        cancion_id: UUID,
        benchmark_id: int,
        session: Session = Depends(get_session)
):
    """Analiza una canción contra un benchmark específico."""
    cancion = session.get(Cancion, cancion_id)
    benchmark = session.get(Benchmark, benchmark_id)

    if not cancion or cancion.deleted_at:
        raise HTTPException(status_code=404, detail="Canción no encontrada")
    if not benchmark or benchmark.deleted_at:
        raise HTTPException(status_code=404, detail="Benchmark no encontrado")

    afinidad = calcular_afinidad(cancion, benchmark)
    hallazgo = clasificar_afinidad(afinidad)

    resultado = AnalisisResultado(
        cancion_id=cancion.id,
        benchmark_id=benchmark.id,
        afinidad=afinidad,
        hallazgo=hallazgo
    )

    session.add(resultado)
    session.commit()
    session.refresh(resultado)

    return {
        "cancion": cancion.nombre,
        "benchmark": f"{benchmark.genero} - {benchmark.pais}",
        "afinidad": round(afinidad, 2),
        "hallazgo": hallazgo,
        "resultado_id": resultado.id
    }


@router.get("/cancion/{cancion_id}")
def obtener_analisis_cancion(cancion_id: UUID, session: Session = Depends(get_session)):
    """Obtiene todos los análisis de una canción."""
    cancion = session.get(Cancion, cancion_id)
    if not cancion or cancion.deleted_at:
        raise HTTPException(status_code=404, detail="Canción no encontrada")

    statement = select(AnalisisResultado).where(
        AnalisisResultado.cancion_id == cancion_id
    )
    resultados = session.exec(statement).all()

    return {
        "cancion": cancion,
        "total_analisis": len(resultados),
        "analisis": resultados
    }