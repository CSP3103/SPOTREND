from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from database import get_session
from models import Cancion, Artista, Benchmark, AnalisisResultado
import logging
from datetime import datetime, timedelta
import asyncio

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
logger = logging.getLogger(__name__)


@router.get("/")
async def obtener_dashboard(session: Session = Depends(get_session)):
    try:
        await asyncio.sleep(0.01)
        total_canciones = session.exec(
            select(func.count()).select_from(Cancion).where(Cancion.deleted_at == None)
        ).one()

        await asyncio.sleep(0.01)
        total_artistas = session.exec(
            select(func.count()).select_from(Artista).where(Artista.deleted_at == None)
        ).one()

        await asyncio.sleep(0.01)
        total_benchmarks = session.exec(
            select(func.count()).select_from(Benchmark).where(Benchmark.deleted_at == None)
        ).one()

        await asyncio.sleep(0.01)
        canciones_eliminadas = session.exec(
            select(func.count()).select_from(Cancion).where(Cancion.deleted_at != None)
        ).one()

        await asyncio.sleep(0.01)
        artistas_eliminados = session.exec(
            select(func.count()).select_from(Artista).where(Artista.deleted_at != None)
        ).one()

        await asyncio.sleep(0.01)
        benchmarks_eliminados = session.exec(
            select(func.count()).select_from(Benchmark).where(Benchmark.deleted_at != None)
        ).one()

        await asyncio.sleep(0.01)
        total_analisis = session.exec(
            select(func.count()).select_from(AnalisisResultado)
        ).one()

        ultimas_24h = datetime.utcnow() - timedelta(hours=24)
        await asyncio.sleep(0.01)
        analisis_recientes = session.exec(
            select(func.count()).select_from(AnalisisResultado)
            .where(AnalisisResultado.creado_en >= ultimas_24h)
        ).one()

        await asyncio.sleep(0.01)
        afinidad_promedio_result = session.exec(
            select(func.avg(AnalisisResultado.afinidad)).select_from(AnalisisResultado)
        ).one()
        afinidad_promedio = round(afinidad_promedio_result or 0, 1)

        await asyncio.sleep(0.01)
        canciones_mas_analizadas = session.exec(
            select(
                AnalisisResultado.cancion_id,
                func.count(AnalisisResultado.id).label('total_analisis')
            )
            .group_by(AnalisisResultado.cancion_id)
            .order_by(func.count(AnalisisResultado.id).desc())
            .limit(5)
        ).all()

        await asyncio.sleep(0.01)
        benchmarks_mas_usados = session.exec(
            select(
                AnalisisResultado.benchmark_id,
                func.count(AnalisisResultado.id).label('total_usos')
            )
            .group_by(AnalisisResultado.benchmark_id)
            .order_by(func.count(AnalisisResultado.id).desc())
            .limit(5)
        ).all()

        return {
            "resumen": {
                "canciones_activas": total_canciones,
                "artistas_activos": total_artistas,
                "benchmarks_activos": total_benchmarks,
                "canciones_eliminadas": canciones_eliminadas,
                "artistas_eliminados": artistas_eliminados,
                "benchmarks_eliminados": benchmarks_eliminados
            },
            "analisis": {
                "total_analisis": total_analisis,
                "analisis_ultimas_24h": analisis_recientes,
                "afinidad_promedio": f"{afinidad_promedio}%",
                "canciones_mas_analizadas": [
                    {"cancion_id": c[0], "total_analisis": c[1]}
                    for c in canciones_mas_analizadas
                ],
                "benchmarks_mas_usados": [
                    {"benchmark_id": b[0], "total_usos": b[1]}
                    for b in benchmarks_mas_usados
                ]
            },
            "estado": {
                "api": "✅ Online",
                "base_datos": "✅ Conectada",
                "spotify": "✅ Conectado" if total_analisis > 0 else "⚠️ No verificado",
                "ultima_actualizacion": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Error generando dashboard: {e}")
        return {
            "error": "No se pudo generar el dashboard",
            "detalle": str(e)[:200]
        }