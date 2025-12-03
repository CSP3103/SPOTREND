from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models import Cancion, Benchmark, AnalisisResultado
import math
import logging

router = APIRouter(prefix="/analisis", tags=["Análisis"])
logger = logging.getLogger(__name__)


def calcular_afinidad(cancion: Cancion, benchmark: Benchmark) -> float:
    try:
        tempo_diff = (cancion.tempo - benchmark.tempo_promedio) ** 2
        energy_diff = (cancion.energy - benchmark.energy_promedio) ** 2
        distancia = math.sqrt(tempo_diff + energy_diff)
        return round(distancia, 2)
    except Exception as e:
        logger.error(f"Error calculando afinidad: {e}")
        return 100.0  # Valor por defecto alto


@router.get("/cancion/{cancion_id}")
def analizar_cancion(cancion_id: str, session: Session = Depends(get_session)):
    try:
        # Verificar canción
        cancion = session.get(Cancion, cancion_id)
        if not cancion or cancion.deleted_at:
            raise HTTPException(404, "Canción no encontrada o eliminada")

        # Obtener benchmarks activos
        benchmarks = session.exec(
            select(Benchmark).where(Benchmark.deleted_at == None)
        ).all()

        if not benchmarks:
            raise HTTPException(404, "No hay benchmarks disponibles")

        resultados = []
        for b in benchmarks:
            afinidad = calcular_afinidad(cancion, b)

            if afinidad < 10:
                hallazgo = "ALTO"
            elif afinidad < 20:
                hallazgo = "MEDIO"
            else:
                hallazgo = "BAJO"

            # Guardar en base de datos
            analisis = AnalisisResultado(
                cancion_id=cancion_id,
                benchmark_id=b.id,
                afinidad=afinidad,
                hallazgo=hallazgo
            )
            session.add(analisis)

            resultados.append({
                "benchmark_id": b.id,
                "benchmark": f"{b.genero} - {b.pais}",
                "tempo_promedio": b.tempo_promedio,
                "energy_promedio": b.energy_promedio,
                "afinidad": afinidad,
                "hallazgo": hallazgo
            })

        session.commit()

        # Ordenar por afinidad (menor es mejor)
        resultados_ordenados = sorted(resultados, key=lambda x: x["afinidad"])

        return {
            "cancion_id": cancion.id,
            "cancion": cancion.nombre,
            "artista": cancion.artista,
            "tempo": cancion.tempo,
            "energy": cancion.energy,
            "total_benchmarks": len(benchmarks),
            "mejores_3": resultados_ordenados[:3],
            "todos_resultados": resultados_ordenados
        }

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error en análisis de canción {cancion_id}: {e}")
        raise HTTPException(500, f"Error en análisis: {str(e)[:100]}")


@router.get("/historial/{cancion_id}")
def obtener_historial_analisis(cancion_id: str, session: Session = Depends(get_session)):
    try:
        cancion = session.get(Cancion, cancion_id)
        if not cancion or cancion.deleted_at:
            raise HTTPException(404, "Canción no encontrada")

        historiales = session.exec(
            select(AnalisisResultado).where(AnalisisResultado.cancion_id == cancion_id)
        ).all()

        return {
            "cancion": cancion.nombre,
            "total_analisis": len(historiales),
            "analisis": historiales
        }

    except Exception as e:
        logger.error(f"Error obteniendo historial para {cancion_id}: {e}")
        raise HTTPException(500, "Error interno del servidor")