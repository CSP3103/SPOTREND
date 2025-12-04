from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select, func
from database import get_session
from models import Cancion, Artista, Benchmark, AnalisisResultado
import logging
import random
import asyncio

router = APIRouter(prefix="/recomendaciones", tags=["Recomendaciones"])
logger = logging.getLogger(__name__)

# Templates para HTML
templates = Jinja2Templates(directory="templates")


# ========== ENDPOINTS HTML ==========
@router.get("/", response_class=HTMLResponse)
async def recomendaciones_home(request: Request):
    """
    Menú principal de Recomendaciones (HTML)
    """
    return templates.TemplateResponse("recomendaciones/home.html", {
        "request": request
    })


@router.get("/cancion/{cancion_id}", response_class=HTMLResponse)
async def recomendar_similares_html(
        request: Request,
        cancion_id: str,
        session: Session = Depends(get_session)
):
    """Recomendaciones de canciones similares (HTML)"""
    try:
        data = await recomendar_similares(cancion_id, 5, session)
        return templates.TemplateResponse("recomendaciones/cancion.html", {
            "request": request,
            "cancion_base": data["cancion_base"],
            "total_canciones_analizadas": data["total_canciones_analizadas"],
            "recomendaciones": data["recomendaciones"],
            "mensaje": data.get("mensaje")
        })
    except Exception as e:
        logger.error(f"Error HTML recomendaciones canción {cancion_id}: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"No se pudieron generar recomendaciones: {str(e)[:100]}"
        })


@router.get("/artista/{artista_id}", response_class=HTMLResponse)
async def recomendar_artistas_similares_html(
        request: Request,
        artista_id: int,
        session: Session = Depends(get_session)
):
    """Recomendaciones de artistas similares (HTML)"""
    try:
        data = await recomendar_artistas_similares(artista_id, 5, session)
        return templates.TemplateResponse("recomendaciones/artista.html", {
            "request": request,
            "artista_base": data["artista_base"],
            "recomendaciones": data["recomendaciones"],
            "mensaje": data.get("mensaje")
        })
    except Exception as e:
        logger.error(f"Error HTML recomendaciones artista {artista_id}: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"No se pudieron generar recomendaciones: {str(e)[:100]}"
        })


@router.get("/descubrimiento", response_class=HTMLResponse)
async def canciones_descubrimiento_html(
        request: Request,
        session: Session = Depends(get_session)
):
    """Canciones de descubrimiento (HTML)"""
    try:
        data = await canciones_descubrimiento(session, 6)
        return templates.TemplateResponse("recomendaciones/descubrimiento.html", {
            "request": request,
            "tipo": data["tipo"],
            "descripcion": data["descripcion"],
            "total_candidatas": data.get("total_candidatas"),
            "canciones": data["canciones"]
        })
    except Exception as e:
        logger.error(f"Error HTML descubrimiento: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error en descubrimiento: {str(e)[:100]}"
        })


@router.get("/para-benchmark/{benchmark_id}", response_class=HTMLResponse)
async def recomendar_para_benchmark_html(
        request: Request,
        benchmark_id: int,
        session: Session = Depends(get_session)
):
    """Recomendaciones para benchmark (HTML)"""
    try:
        data = await recomendar_para_benchmark(benchmark_id, session, 5)
        return templates.TemplateResponse("recomendaciones/benchmark.html", {
            "request": request,
            "benchmark": data["benchmark"],
            "total_canciones_analizadas": data["total_canciones_analizadas"],
            "canciones_recomendadas": data["canciones_recomendadas"]
        })
    except Exception as e:
        logger.error(f"Error HTML benchmark {benchmark_id}: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error generando recomendaciones: {str(e)[:100]}"
        })


# ========== FUNCIONES AUXILIARES ==========

def _generar_razon_recomendacion(base, candidato, similitud):
    razones = []

    # Protección por si atributos son None
    try:
        if getattr(base, "tempo", None) is not None and getattr(candidato, "tempo", None) is not None:
            if abs(base.tempo - candidato.tempo) < 10:
                razones.append("Tempo similar")
    except Exception:
        pass

    try:
        if getattr(base, "energy", None) is not None and getattr(candidato, "energy", None) is not None:
            if abs(base.energy - candidato.energy) < 0.2:
                razones.append("Energy similar")
    except Exception:
        pass

    try:
        if getattr(base, "artista", None) and getattr(candidato, "artista", None):
            if base.artista == candidato.artista:
                razones.append("Mismo artista")
    except Exception:
        pass

    if not razones:
        if similitud > 80:
            return "Muy similar en múltiples métricas"
        elif similitud > 60:
            return "Similitud moderada en características técnicas"
        else:
            return "Alguna similitud en características"

    return ", ".join(razones[:2])


def _generar_razon_artista(base, candidato, similitud):
    razones = []

    try:
        if getattr(base, "genero_principal", None) and getattr(candidato, "genero_principal", None):
            if base.genero_principal.lower() == candidato.genero_principal.lower():
                razones.append("Mismo género")
    except Exception:
        pass

    try:
        if getattr(base, "pais", None) and getattr(candidato, "pais", None):
            if base.pais.lower() == candidato.pais.lower():
                razones.append("Mismo país")
    except Exception:
        pass

    try:
        if getattr(base, "popularidad", None) is not None and getattr(candidato, "popularidad", None) is not None:
            if abs(base.popularidad - candidato.popularidad) < 20:
                razones.append("Popularidad similar")
    except Exception:
        pass

    if razones:
        return ", ".join(razones)
    return "Alguna similitud encontrada"


# ========== ENDPOINTS ORIGINALES (JSON) ==========

@router.get("/cancion/{cancion_id}")
async def recomendar_similares(
        cancion_id: str,
        limite: int = 5,
        session: Session = Depends(get_session)
):
    try:
        await asyncio.sleep(0.01)
        cancion_base = session.get(Cancion, cancion_id)
        if not cancion_base:
            raise HTTPException(404, "Canción base no encontrada")

        await asyncio.sleep(0.01)
        canciones = session.exec(
            select(Cancion).where(
                (Cancion.deleted_at == None) &
                (Cancion.id != cancion_id)
            )
        ).all()

        if not canciones:
            return {
                "cancion_base": cancion_base,
                "mensaje": "No hay otras canciones para comparar",
                "recomendaciones": []
            }

        recomendaciones = []
        for cancion in canciones:
            # Guardar acceso seguro a atributos
            tempo_a = getattr(cancion_base, "tempo", 0) or 0
            tempo_b = getattr(cancion, "tempo", 0) or 0
            energy_a = getattr(cancion_base, "energy", 0) or 0
            energy_b = getattr(cancion, "energy", 0) or 0

            tempo_diff = abs(tempo_a - tempo_b) / 200
            energy_diff = abs(energy_a - energy_b)

            similitud_tempo = max(0, 1 - tempo_diff)
            similitud_energy = max(0, 1 - energy_diff)

            if getattr(cancion_base, "danceability", None) is not None and getattr(cancion, "danceability", None) is not None:
                dance_diff = abs(cancion_base.danceability - cancion.danceability)
                similitud_dance = max(0, 1 - dance_diff)
            else:
                similitud_dance = 0.5

            if getattr(cancion_base, "valence", None) is not None and getattr(cancion, "valence", None) is not None:
                valence_diff = abs(cancion_base.valence - cancion.valence)
                similitud_valence = max(0, 1 - valence_diff)
            else:
                similitud_valence = 0.5

            similitud_total = (
                                  similitud_tempo * 0.3 +
                                  similitud_energy * 0.3 +
                                  similitud_dance * 0.2 +
                                  similitud_valence * 0.2
                          ) * 100

            recomendaciones.append({
                "cancion": cancion,
                "similitudes": {
                    "tempo": round(similitud_tempo * 100, 1),
                    "energy": round(similitud_energy * 100, 1),
                    "danceability": round(similitud_dance * 100, 1) if getattr(cancion, "danceability", None) is not None else None,
                    "valence": round(similitud_valence * 100, 1) if getattr(cancion, "valence", None) is not None else None,
                    "total": round(similitud_total, 1)
                },
                "razon": _generar_razon_recomendacion(cancion_base, cancion, similitud_total)
            })

        recomendaciones.sort(key=lambda x: x["similitudes"]["total"], reverse=True)

        return {
            "cancion_base": cancion_base,
            "total_canciones_analizadas": len(canciones),
            "recomendaciones": recomendaciones[:limite]
        }

    except Exception as e:
        logger.error(f"Error generando recomendaciones: {e}")
        raise HTTPException(500, "Error generando recomendaciones")


@router.get("/artista/{artista_id}")
async def recomendar_artistas_similares(
        artista_id: int,
        limite: int = 5,
        session: Session = Depends(get_session)
):
    try:
        await asyncio.sleep(0.01)
        artista_base = session.get(Artista, artista_id)
        if not artista_base:
            raise HTTPException(404, "Artista base no encontrado")

        await asyncio.sleep(0.01)
        artistas = session.exec(
            select(Artista).where(
                (Artista.deleted_at == None) &
                (Artista.id != artista_id)
            )
        ).all()

        if not artistas:
            return {
                "artista_base": artista_base,
                "mensaje": "No hay otros artistas para comparar",
                "recomendaciones": []
            }

        recomendaciones = []
        for artista in artistas:
            similitud = 0

            try:
                if artista_base.genero_principal and artista.genero_principal:
                    if artista_base.genero_principal.lower() == artista.genero_principal.lower():
                        similitud += 50
            except Exception:
                pass

            try:
                if artista_base.pais and artista.pais:
                    if artista_base.pais.lower() == artista.pais.lower():
                        similitud += 30
            except Exception:
                pass

            try:
                pop_diff = abs((artista_base.popularidad or 0) - (artista.popularidad or 0))
                if pop_diff < 20:
                    similitud += 20
            except Exception:
                pass

            recomendaciones.append({
                "artista": artista,
                "similitud": similitud,
                "razon": _generar_razon_artista(artista_base, artista, similitud)
            })

        recomendaciones.sort(key=lambda x: x["similitud"], reverse=True)
        recomendaciones = [r for r in recomendaciones if r["similitud"] > 30]

        return {
            "artista_base": artista_base,
            "recomendaciones": recomendaciones[:limite]
        }

    except Exception as e:
        logger.error(f"Error recomendando artistas: {e}")
        raise HTTPException(500, "Error generando recomendaciones")


@router.get("/descubrimiento")
async def canciones_descubrimiento(
        session: Session = Depends(get_session),
        limite: int = 5
):
    try:
        await asyncio.sleep(0.01)
        subquery = (
            select(
                AnalisisResultado.cancion_id,
                func.avg(AnalisisResultado.afinidad).label('avg_afinidad')
            )
            .group_by(AnalisisResultado.cancion_id)
            .having(func.count(AnalisisResultado.id) > 0)
            .subquery()
        )

        canciones_con_afinidad = session.exec(
            select(Cancion, subquery.c.avg_afinidad)
            .join(subquery, Cancion.id == subquery.c.cancion_id)
            .where(Cancion.deleted_at == None)
            .order_by(subquery.c.avg_afinidad.desc())
            .limit(limite * 3)
        ).all()

        if not canciones_con_afinidad:
            todas_canciones = session.exec(
                select(Cancion).where(Cancion.deleted_at == None).limit(limite * 2)
            ).all()
            canciones_seleccionadas = random.sample(todas_canciones, min(limite, len(todas_canciones)))
        else:
            canciones = [c[0] for c in canciones_con_afinidad]
            canciones_seleccionadas = random.sample(canciones, min(limite, len(canciones)))

        return {
            "tipo": "Descubrimiento",
            "descripcion": "Canciones con buen rendimiento en análisis",
            "total_candidatas": len(canciones_seleccionadas),
            "canciones": canciones_seleccionadas
        }

    except Exception as e:
        logger.error(f"Error en descubrimiento: {e}")
        await asyncio.sleep(0.01)
        canciones_recientes = session.exec(
            select(Cancion)
            .where(Cancion.deleted_at == None)
            .order_by(Cancion.creado_en.desc())
            .limit(limite)
        ).all()

        return {
            "tipo": "Descubrimiento (fallback)",
            "descripcion": "Canciones más recientes",
            "canciones": canciones_recientes
        }


@router.get("/para-benchmark/{benchmark_id}")
async def recomendar_para_benchmark(
        benchmark_id: int,
        session: Session = Depends(get_session),
        limite: int = 5
):
    try:
        await asyncio.sleep(0.01)
        benchmark = session.get(Benchmark, benchmark_id)
        if not benchmark:
            raise HTTPException(404, "Benchmark no encontrado")

        await asyncio.sleep(0.01)
        canciones = session.exec(
            select(Cancion).where(Cancion.deleted_at == None)
        ).all()

        recomendaciones = []
        for cancion in canciones:
            tempo_diff = abs((getattr(cancion, "tempo", 0) or 0) - (benchmark.tempo_promedio or 0))
            energy_diff = abs((getattr(cancion, "energy", 0) or 0) - (benchmark.energy_promedio or 0))

            distancia = (tempo_diff / 200 * 100 * 0.5) + (energy_diff * 100 * 0.5)
            afinidad = max(0, 100 - distancia)

            if afinidad > 60:
                recomendaciones.append({
                    "cancion": cancion,
                    "afinidad_con_benchmark": round(afinidad, 1),
                    "explicacion": f"Ideal para {benchmark.genero} en {benchmark.pais}",
                    "metricas_comparadas": {
                        "tempo_cancion": getattr(cancion, "tempo", None),
                        "tempo_benchmark": benchmark.tempo_promedio,
                        "energy_cancion": getattr(cancion, "energy", None),
                        "energy_benchmark": benchmark.energy_promedio
                    }
                })

        recomendaciones.sort(key=lambda x: x["afinidad_con_benchmark"], reverse=True)

        return {
            "benchmark": f"{benchmark.genero} ({benchmark.pais})",
            "total_canciones_analizadas": len(canciones),
            "canciones_recomendadas": recomendaciones[:limite]
        }

    except Exception as e:
        logger.error(f"Error recomendando para benchmark: {e}")
        raise HTTPException(500, "Error generando recomendaciones")
