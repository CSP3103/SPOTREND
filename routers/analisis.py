from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from database import get_session
from models import Cancion, Benchmark, AnalisisResultado
import math
import logging
from datetime import datetime, timedelta
import asyncio

router = APIRouter(prefix="/analisis-v2", tags=["Análisis Mejorado"])
logger = logging.getLogger(__name__)


def calcular_afinidad_completa(cancion: Cancion, benchmark: Benchmark) -> dict:
    tempo_diff = abs(cancion.tempo - benchmark.tempo_promedio)
    energy_diff = abs(cancion.energy - benchmark.energy_promedio)
    dance_diff = abs((cancion.danceability or 0) - benchmark.danceability_promedio)
    valence_diff = abs((cancion.valence or 0) - benchmark.valence_promedio)

    distancia = math.sqrt(
        tempo_diff ** 2 +
        energy_diff ** 2 +
        dance_diff ** 2 +
        valence_diff ** 2
    )

    max_distancia = math.sqrt(200 ** 2 + 1 ** 2 + 1 ** 2 + 1 ** 2)
    afinidad_porcentaje = max(0, 100 - (distancia / max_distancia * 100))

    if afinidad_porcentaje > 80:
        nivel = "🎵 EXCELENTE"
        recomendacion = "Perfecto para este mercado"
    elif afinidad_porcentaje > 60:
        nivel = "✅ BUENO"
        recomendacion = "Funcionaría bien"
    elif afinidad_porcentaje > 40:
        nivel = "⚠️ REGULAR"
        recomendacion = "Podría mejorar"
    else:
        nivel = "❌ BAJO"
        recomendacion = "No es el mercado objetivo"

    return {
        "benchmark": f"{benchmark.genero} ({benchmark.pais})",
        "distancia": round(distancia, 2),
        "afinidad": round(afinidad_porcentaje, 1),
        "nivel": nivel,
        "recomendacion": recomendacion,
        "metricas": {
            "tempo_diff": round(tempo_diff, 2),
            "energy_diff": round(energy_diff, 3),
            "dance_diff": round(dance_diff, 3),
            "valence_diff": round(valence_diff, 3)
        }
    }


@router.get("/cancion/{cancion_id}")
async def analizar_cancion_completo_v2(
        cancion_id: str,
        session: Session = Depends(get_session)
):
    try:
        await asyncio.sleep(0.01)
        cancion = session.get(Cancion, cancion_id)
        if not cancion:
            raise HTTPException(404, "Canción no encontrada")

        await asyncio.sleep(0.01)
        benchmarks = session.exec(
            select(Benchmark).where(Benchmark.deleted_at == None)
        ).all()

        if not benchmarks:
            return {
                "cancion": cancion,
                "error": "No hay benchmarks configurados",
                "analisis": []
            }

        resultados = []
        for benchmark in benchmarks:
            analisis = calcular_afinidad_completa(cancion, benchmark)

            registro = AnalisisResultado(
                cancion_id=cancion_id,
                benchmark_id=benchmark.id,
                afinidad=analisis["afinidad"],
                hallazgo=analisis["nivel"]
            )
            session.add(registro)
            resultados.append(analisis)

        await asyncio.sleep(0.01)
        session.commit()

        resultados_ordenados = sorted(resultados, key=lambda x: x["afinidad"], reverse=True)

        return {
            "cancion": {
                "id": cancion.id,
                "nombre": cancion.nombre,
                "artista": cancion.artista,
                "tempo": cancion.tempo,
                "energy": cancion.energy,
                "danceability": cancion.danceability,
                "valence": cancion.valence
            },
            "resumen": {
                "total_benchmarks": len(benchmarks),
                "mejor_afinidad": resultados_ordenados[0] if resultados_ordenados else None,
                "peor_afinidad": resultados_ordenados[-1] if resultados_ordenados else None,
                "afinidad_promedio": round(sum(r["afinidad"] for r in resultados) / len(resultados),
                                           1) if resultados else 0
            },
            "analisis": resultados_ordenados
        }

    except Exception as e:
        session.rollback()
        logger.error(f"Error en análisis: {e}")
        raise HTTPException(500, f"Error en análisis: {str(e)[:100]}")


@router.get("/tendencias")
async def analizar_tendencias_v2(
        session: Session = Depends(get_session)
):
    try:
        fecha_limite = datetime.utcnow() - timedelta(days=7)

        await asyncio.sleep(0.01)
        analisis_recientes = session.exec(
            select(AnalisisResultado)
            .where(AnalisisResultado.creado_en >= fecha_limite)
        ).all()

        if not analisis_recientes:
            return {"message": "No hay análisis recientes", "tendencias": []}

        tendencias = {}
        for a in analisis_recientes:
            benchmark_id = a.benchmark_id
            if benchmark_id not in tendencias:
                await asyncio.sleep(0.01)
                benchmark = session.get(Benchmark, benchmark_id)
                tendencias[benchmark_id] = {
                    "benchmark": f"{benchmark.genero} ({benchmark.pais})" if benchmark else f"ID {benchmark_id}",
                    "total_analisis": 0,
                    "afinidad_promedio": 0,
                    "niveles": {"EXCELENTE": 0, "BUENO": 0, "REGULAR": 0, "BAJO": 0}
                }

            tendencias[benchmark_id]["total_analisis"] += 1
            tendencias[benchmark_id]["afinidad_promedio"] += a.afinidad

            if a.afinidad > 80:
                nivel = "EXCELENTE"
            elif a.afinidad > 60:
                nivel = "BUENO"
            elif a.afinidad > 40:
                nivel = "REGULAR"
            else:
                nivel = "BAJO"

            tendencias[benchmark_id]["niveles"][nivel] += 1

        for key in tendencias:
            if tendencias[key]["total_analisis"] > 0:
                tendencias[key]["afinidad_promedio"] = round(
                    tendencias[key]["afinidad_promedio"] / tendencias[key]["total_analisis"],
                    1
                )

        lista_tendencias = list(tendencias.values())
        lista_tendencias.sort(key=lambda x: x["afinidad_promedio"], reverse=True)

        return {
            "periodo": "Últimos 7 días",
            "total_analisis": len(analisis_recientes),
            "tendencias": lista_tendencias[:5]
        }

    except Exception as e:
        logger.error(f"Error analizando tendencias: {e}")
        return {"error": str(e), "tendencias": []}