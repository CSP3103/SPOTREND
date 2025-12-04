from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from database import get_session
from models import Benchmark
import logging
import asyncio

router = APIRouter(prefix="/benchmarks", tags=["Benchmarks"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=Benchmark)
async def crear_benchmark(
        pais: str,
        genero: str,
        tempo_promedio: float,
        energy_promedio: float,
        danceability_promedio: float = 0.0,
        valence_promedio: float = 0.0,
        session: Session = Depends(get_session)
):
    try:
        if tempo_promedio < 0 or tempo_promedio > 300:
            raise HTTPException(400, "Tempo promedio inválido")
        if energy_promedio < 0 or energy_promedio > 1:
            raise HTTPException(400, "Energy promedio inválido")

        benchmark = Benchmark(
            pais=pais,
            genero=genero,
            tempo_promedio=tempo_promedio,
            energy_promedio=energy_promedio,
            danceability_promedio=danceability_promedio,
            valence_promedio=valence_promedio
        )

        await asyncio.sleep(0.01)
        session.add(benchmark)
        session.commit()
        session.refresh(benchmark)
        return benchmark

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error creando benchmark: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.get("/", response_model=list[Benchmark])
async def listar_benchmarks(session: Session = Depends(get_session)):
    try:
        await asyncio.sleep(0.01)
        return session.exec(
            select(Benchmark).where(Benchmark.deleted_at == None)
        ).all()
    except Exception as e:
        logger.error(f"Error listando benchmarks: {e}")
        return []


@router.get("/{id}", response_model=Benchmark)
async def obtener_benchmark(id: int, session: Session = Depends(get_session)):
    try:
        await asyncio.sleep(0.01)
        benchmark = session.get(Benchmark, id)
        if not benchmark or benchmark.deleted_at:
            raise HTTPException(404, "Benchmark no encontrado")
        return benchmark
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo benchmark {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.put("/{id}", response_model=Benchmark)
async def actualizar_benchmark(
        id: int,
        pais: str = None,
        genero: str = None,
        tempo_promedio: float = None,
        energy_promedio: float = None,
        danceability_promedio: float = None,
        valence_promedio: float = None,
        session: Session = Depends(get_session)
):
    try:
        await asyncio.sleep(0.01)
        benchmark = session.get(Benchmark, id)
        if not benchmark or benchmark.deleted_at:
            raise HTTPException(404, "Benchmark no encontrado")

        if tempo_promedio is not None and (tempo_promedio < 0 or tempo_promedio > 300):
            raise HTTPException(400, "Tempo promedio inválido")
        if energy_promedio is not None and (energy_promedio < 0 or energy_promedio > 1):
            raise HTTPException(400, "Energy promedio inválido")

        if pais is not None:
            benchmark.pais = pais
        if genero is not None:
            benchmark.genero = genero
        if tempo_promedio is not None:
            benchmark.tempo_promedio = tempo_promedio
        if energy_promedio is not None:
            benchmark.energy_promedio = energy_promedio
        if danceability_promedio is not None:
            benchmark.danceability_promedio = danceability_promedio
        if valence_promedio is not None:
            benchmark.valence_promedio = valence_promedio

        await asyncio.sleep(0.01)
        session.add(benchmark)
        session.commit()
        session.refresh(benchmark)
        return benchmark

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error actualizando benchmark {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.delete("/{id}")
async def eliminar_benchmark(id: int, session: Session = Depends(get_session)):
    try:
        await asyncio.sleep(0.01)
        benchmark = session.get(Benchmark, id)
        if not benchmark:
            raise HTTPException(404, "Benchmark no encontrado")

        if benchmark.deleted_at:
            return {"message": "Benchmark ya estaba eliminado", "ok": True}

        benchmark.deleted_at = datetime.utcnow()
        await asyncio.sleep(0.01)
        session.add(benchmark)
        session.commit()
        return {"message": "Benchmark eliminado exitosamente", "ok": True}

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error eliminando benchmark {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.get("/{id}/restaurar")
async def restaurar_benchmark(id: int, session: Session = Depends(get_session)):
    try:
        await asyncio.sleep(0.01)
        benchmark = session.get(Benchmark, id)
        if not benchmark:
            raise HTTPException(404, "Benchmark no encontrado")

        if not benchmark.deleted_at:
            return {"message": "Benchmark no estaba eliminado", "ok": True}

        benchmark.deleted_at = None
        await asyncio.sleep(0.01)
        session.add(benchmark)
        session.commit()
        return {"message": "Benchmark restaurado exitosamente", "ok": True}

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error restaurando benchmark {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")