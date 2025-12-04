from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models import Cancion, Artista, Benchmark
import logging
import asyncio

router = APIRouter(prefix="/eliminados", tags=["Eliminados"])
logger = logging.getLogger(__name__)


@router.get("/canciones")
async def listar_canciones_eliminadas(session: Session = Depends(get_session)):
    try:
        await asyncio.sleep(0.01)
        canciones = session.exec(
            select(Cancion).where(Cancion.deleted_at != None)
        ).all()
        return {
            "total": len(canciones),
            "canciones": canciones
        }
    except Exception as e:
        logger.error(f"Error listando canciones eliminadas: {e}")
        return {"total": 0, "canciones": []}


@router.get("/artistas")
async def listar_artistas_eliminados(session: Session = Depends(get_session)):
    try:
        await asyncio.sleep(0.01)
        artistas = session.exec(
            select(Artista).where(Artista.deleted_at != None)
        ).all()
        return {
            "total": len(artistas),
            "artistas": artistas
        }
    except Exception as e:
        logger.error(f"Error listando artistas eliminados: {e}")
        return {"total": 0, "artistas": []}


@router.get("/benchmarks")
async def listar_benchmarks_eliminados(session: Session = Depends(get_session)):
    try:
        await asyncio.sleep(0.01)
        benchmarks = session.exec(
            select(Benchmark).where(Benchmark.deleted_at != None)
        ).all()
        return {
            "total": len(benchmarks),
            "benchmarks": benchmarks
        }
    except Exception as e:
        logger.error(f"Error listando benchmarks eliminados: {e}")
        return {"total": 0, "benchmarks": []}


@router.post("/restaurar-todos")
async def restaurar_todos_eliminados(session: Session = Depends(get_session)):
    try:
        await asyncio.sleep(0.01)
        canciones = session.exec(
            select(Cancion).where(Cancion.deleted_at != None)
        ).all()
        for c in canciones:
            c.deleted_at = None

        await asyncio.sleep(0.01)
        artistas = session.exec(
            select(Artista).where(Artista.deleted_at != None)
        ).all()
        for a in artistas:
            a.deleted_at = None

        await asyncio.sleep(0.01)
        benchmarks = session.exec(
            select(Benchmark).where(Benchmark.deleted_at != None)
        ).all()
        for b in benchmarks:
            b.deleted_at = None

        await asyncio.sleep(0.01)
        session.commit()

        return {
            "message": "Todos los elementos restaurados",
            "canciones_restauradas": len(canciones),
            "artistas_restaurados": len(artistas),
            "benchmarks_restaurados": len(benchmarks)
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Error restaurando todos: {e}")
        raise HTTPException(500, "Error interno del servidor")