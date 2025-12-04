# routers/comparacion_local.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from database import get_session
from models import Cancion, Artista
import logging
import asyncio

router = APIRouter(prefix="/comparacion-local", tags=["Comparación Local"])
logger = logging.getLogger(__name__)

# Templates
templates = Jinja2Templates(directory="templates")

# ========== ENDPOINTS HTML ==========

@router.get("/", response_class=HTMLResponse)
async def pagina_comparacion_local(
    request: Request,
    session: Session = Depends(get_session)
):
    """Página principal de comparación local"""
    try:
        canciones = session.exec(
            select(Cancion).where(Cancion.deleted_at == None)
        ).all()

        artistas = session.exec(
            select(Artista).where(Artista.deleted_at == None)
        ).all()

        return templates.TemplateResponse("comparacion/seleccionar.html", {
            "request": request,
            "canciones": canciones,
            "artistas": artistas
        })

    except Exception as e:
        logger.error(f"Error cargando página comparación: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error cargando elementos para comparar: {str(e)}"
        })

@router.get("/canciones/{cancion1_id}/{cancion2_id}", response_class=HTMLResponse)
async def comparar_canciones_locales_html(
    request: Request,
    cancion1_id: str,
    cancion2_id: str,
    session: Session = Depends(get_session)
):
    """Comparar canciones locales (HTML)"""
    try:
        resultado = await comparar_canciones_locales(cancion1_id, cancion2_id, session)
        return templates.TemplateResponse("comparacion/comparar_canciones.html", {
            "request": request,
            "comparacion": resultado
        })

    except HTTPException as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": e.detail
        })
    except Exception as e:
        logger.error(f"Error comparando canciones HTML: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error comparando canciones: {str(e)}"
        })

@router.get("/artistas/{artista1_id}/{artista2_id}", response_class=HTMLResponse)
async def comparar_artistas_locales_html(
    request: Request,
    artista1_id: int,
    artista2_id: int,
    session: Session = Depends(get_session)
):
    """Comparar artistas locales (HTML)"""
    try:
        resultado = await comparar_artistas_locales(artista1_id, artista2_id, session)
        return templates.TemplateResponse("comparacion/comparar_artistas.html", {
            "request": request,
            "comparacion": resultado
        })

    except HTTPException as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": e.detail
        })
    except Exception as e:
        logger.error(f"Error comparando artistas HTML: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error comparando artistas: {str(e)}"
        })

@router.get("/cancion/{cancion_id}/seleccionar", response_class=HTMLResponse)
async def seleccionar_cancion_comparar(
    request: Request,
    cancion_id: str,
    session: Session = Depends(get_session)
):
    """Seleccionar otra canción para comparar"""
    try:
        cancion_base = session.get(Cancion, cancion_id)
        if not cancion_base or cancion_base.deleted_at:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "Canción no encontrada"
            })

        canciones = session.exec(
            select(Cancion).where(
                (Cancion.deleted_at == None) &
                (Cancion.id != cancion_id)
            )
        ).all()

        return templates.TemplateResponse("comparacion/seleccionar_cancion.html", {
            "request": request,
            "cancion_base": cancion_base,
            "canciones": canciones
        })

    except Exception as e:
        logger.error(f"Error seleccionando canción: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error: {str(e)}"
        })

# ========== FUNCIONES DE COMPARACIÓN (ORIGINALES) ==========

async def comparar_canciones_locales(
    cancion1_id: str,
    cancion2_id: str,
    session: Session
):
    """Compara dos canciones locales entre sí"""
    try:
        await asyncio.sleep(0.01)

        # Obtener ambas canciones
        cancion1 = session.get(Cancion, cancion1_id)
        cancion2 = session.get(Cancion, cancion2_id)

        if not cancion1 or cancion1.deleted_at:
            raise HTTPException(404, f"Canción 1 (ID: {cancion1_id}) no encontrada")
        if not cancion2 or cancion2.deleted_at:
            raise HTTPException(404, f"Canción 2 (ID: {cancion2_id}) no encontrada")

        comparaciones = []
        puntuacion_total = 0
        max_puntuacion = 100

        # 1. Comparar artista (40 puntos)
        mismo_artista = cancion1.artista.lower() == cancion2.artista.lower()
        puntuacion_artista = 40 if mismo_artista else 0
        comparaciones.append({
            "atributo": "Artista",
            "cancion1": cancion1.artista,
            "cancion2": cancion2.artista,
            "coincide": mismo_artista,
            "puntuacion": puntuacion_artista,
            "peso": "Alto (40%)"
        })
        puntuacion_total += puntuacion_artista

        # 2. Comparar tempo (20 puntos)
        tempo_diff = abs(cancion1.tempo - cancion2.tempo)
        similitud_tempo = max(0, 20 - (tempo_diff / 50 * 20))
        comparaciones.append({
            "atributo": "Tempo (BPM)",
            "cancion1": round(cancion1.tempo, 1),
            "cancion2": round(cancion2.tempo, 1),
            "diferencia": round(tempo_diff, 1),
            "puntuacion": round(similitud_tempo, 1),
            "peso": "Medio (20%)"
        })
        puntuacion_total += similitud_tempo

        # 3. Comparar energy (15 puntos)
        energy_diff = abs(cancion1.energy - cancion2.energy)
        similitud_energy = max(0, 15 - (energy_diff * 15))
        comparaciones.append({
            "atributo": "Energy",
            "cancion1": round(cancion1.energy, 3),
            "cancion2": round(cancion2.energy, 3),
            "diferencia": round(energy_diff, 3),
            "puntuacion": round(similitud_energy, 1),
            "peso": "Medio (15%)"
        })
        puntuacion_total += similitud_energy

        # 4. Comparar danceability si existen (10 puntos)
        if cancion1.danceability is not None and cancion2.danceability is not None:
            dance_diff = abs(cancion1.danceability - cancion2.danceability)
            similitud_dance = max(0, 10 - (dance_diff * 10))
            comparaciones.append({
                "atributo": "Danceability",
                "cancion1": round(cancion1.danceability, 3),
                "cancion2": round(cancion2.danceability, 3),
                "diferencia": round(dance_diff, 3),
                "puntuacion": round(similitud_dance, 1),
                "peso": "Bajo (10%)"
            })
            puntuacion_total += similitud_dance
        else:
            comparaciones.append({
                "atributo": "Danceability",
                "cancion1": cancion1.danceability or "No definido",
                "cancion2": cancion2.danceability or "No definido",
                "puntuacion": 5,
                "peso": "Bajo (10%) - No comparable"
            })
            puntuacion_total += 5

        # 5. Comparar valence si existen (10 puntos)
        if cancion1.valence is not None and cancion2.valence is not None:
            valence_diff = abs(cancion1.valence - cancion2.valence)
            similitud_valence = max(0, 10 - (valence_diff * 10))
            comparaciones.append({
                "atributo": "Valence",
                "cancion1": round(cancion1.valence, 3),
                "cancion2": round(cancion2.valence, 3),
                "diferencia": round(valence_diff, 3),
                "puntuacion": round(similitud_valence, 1),
                "peso": "Bajo (10%)"
            })
            puntuacion_total += similitud_valence
        else:
            comparaciones.append({
                "atributo": "Valence",
                "cancion1": cancion1.valence or "No definido",
                "cancion2": cancion2.valence or "No definido",
                "puntuacion": 5,
                "peso": "Bajo (10%) - No comparable"
            })
            puntuacion_total += 5

        # 6. Comparar acousticness si existen (5 puntos)
        if cancion1.acousticness is not None and cancion2.acousticness is not None:
            acoustic_diff = abs(cancion1.acousticness - cancion2.acousticness)
            similitud_acoustic = max(0, 5 - (acoustic_diff * 5))
            comparaciones.append({
                "atributo": "Acousticness",
                "cancion1": round(cancion1.acousticness, 3),
                "cancion2": round(cancion2.acousticness, 3),
                "diferencia": round(acoustic_diff, 3),
                "puntuacion": round(similitud_acoustic, 1),
                "peso": "Muy bajo (5%)"
            })
            puntuacion_total += similitud_acoustic
        else:
            comparaciones.append({
                "atributo": "Acousticness",
                "cancion1": cancion1.acousticness or "No definido",
                "cancion2": cancion2.acousticness or "No definido",
                "puntuacion": 2.5,
                "peso": "Muy bajo (5%) - No comparable"
            })
            puntuacion_total += 2.5

        # Calcular porcentaje final
        porcentaje_similitud = round((puntuacion_total / max_puntuacion) * 100, 1)

        # Determinar nivel
        if porcentaje_similitud > 80:
            nivel = "🎵 MUY SIMILARES"
            explicacion = "Canciones muy parecidas en características musicales"
        elif porcentaje_similitud > 60:
            nivel = "✅ SIMILARES"
            explicacion = "Canciones con varias características en común"
        elif porcentaje_similitud > 40:
            nivel = "⚠️ MODERADAMENTE SIMILARES"
            explicacion = "Algunas similitudes, pero diferencias notables"
        else:
            nivel = "❌ DIFERENTES"
            explicacion = "Canciones con características distintas"

        # Generar insight
        insight = _generar_insight_canciones(cancion1, cancion2, comparaciones)

        return {
            "cancion1": {
                "id": cancion1.id,
                "nombre": cancion1.nombre,
                "artista": cancion1.artista,
                "tempo": cancion1.tempo,
                "energy": cancion1.energy,
                "danceability": cancion1.danceability,
                "valence": cancion1.valence,
                "acousticness": cancion1.acousticness,
                "imagen_url": cancion1.imagen_url
            },
            "cancion2": {
                "id": cancion2.id,
                "nombre": cancion2.nombre,
                "artista": cancion2.artista,
                "tempo": cancion2.tempo,
                "energy": cancion2.energy,
                "danceability": cancion2.danceability,
                "valence": cancion2.valence,
                "acousticness": cancion2.acousticness,
                "imagen_url": cancion2.imagen_url
            },
            "comparacion": {
                "porcentaje_similitud": porcentaje_similitud,
                "nivel": nivel,
                "explicacion": explicacion,
                "puntuacion_total": round(puntuacion_total, 1),
                "max_puntuacion": max_puntuacion,
                "detalles": comparaciones
            },
            "insight": insight
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparando canciones locales: {e}")
        raise HTTPException(500, "Error en comparación")

async def comparar_artistas_locales(
    artista1_id: int,
    artista2_id: int,
    session: Session
):
    """Compara dos artistas locales entre sí"""
    try:
        await asyncio.sleep(0.01)

        # Obtener ambos artistas
        artista1 = session.get(Artista, artista1_id)
        artista2 = session.get(Artista, artista2_id)

        if not artista1 or artista1.deleted_at:
            raise HTTPException(404, f"Artista 1 (ID: {artista1_id}) no encontrado")
        if not artista2 or artista2.deleted_at:
            raise HTTPException(404, f"Artista 2 (ID: {artista2_id}) no encontrado")

        # Comparar atributos
        comparaciones = []

        # 1. Comparar género
        if artista1.genero_principal and artista2.genero_principal:
            mismo_genero = artista1.genero_principal.lower() == artista2.genero_principal.lower()
            comparaciones.append({
                "atributo": "Género principal",
                "artista1": artista1.genero_principal,
                "artista2": artista2.genero_principal,
                "coincide": mismo_genero,
                "puntuacion": 50 if mismo_genero else 0
            })
        else:
            comparaciones.append({
                "atributo": "Género principal",
                "artista1": artista1.genero_principal or "No definido",
                "artista2": artista2.genero_principal or "No definido",
                "coincide": "No comparable",
                "puntuacion": 25
            })

        # 2. Comparar país
        if artista1.pais and artista2.pais:
            mismo_pais = artista1.pais.lower() == artista2.pais.lower()
            comparaciones.append({
                "atributo": "País",
                "artista1": artista1.pais,
                "artista2": artista2.pais,
                "coincide": mismo_pais,
                "puntuacion": 30 if mismo_pais else 0
            })
        else:
            comparaciones.append({
                "atributo": "País",
                "artista1": artista1.pais or "No definido",
                "artista2": artista2.pais or "No definido",
                "coincide": "No comparable",
                "puntuacion": 15
            })

        # 3. Comparar popularidad (diferencia porcentual)
        diff_popularidad = abs(artista1.popularidad - artista2.popularidad)
        similitud_popularidad = max(0, 100 - diff_popularidad) * 0.2  # 20% del total

        comparaciones.append({
            "atributo": "Popularidad",
            "artista1": f"{artista1.popularidad}/100",
            "artista2": f"{artista2.popularidad}/100",
            "diferencia": diff_popularidad,
            "puntuacion": round(similitud_popularidad, 1)
        })

        # 4. Contar canciones de cada artista
        from sqlmodel import select
        canciones_artista1 = session.exec(
            select(Cancion).where(
                (Cancion.deleted_at == None) &
                (Cancion.artista.ilike(f"%{artista1.nombre}%"))
            )
        ).all()

        canciones_artista2 = session.exec(
            select(Cancion).where(
                (Cancion.deleted_at == None) &
                (Cancion.artista.ilike(f"%{artista2.nombre}%"))
            )
        ).all()

        comparaciones.append({
            "atributo": "Canciones en sistema",
            "artista1": len(canciones_artista1),
            "artista2": len(canciones_artista2),
            "coincide": len(canciones_artista1) > 0 and len(canciones_artista2) > 0,
            "puntuacion": 10 if (len(canciones_artista1) > 0 and len(canciones_artista2) > 0) else 0
        })

        # Calcular puntuación total
        puntuacion_total = sum(comp["puntuacion"] for comp in comparaciones)
        max_puntuacion = 100
        porcentaje_similitud = round((puntuacion_total / max_puntuacion) * 100, 1)

        # Determinar nivel de similitud
        if porcentaje_similitud > 75:
            nivel = "🎯 MUY SIMILARES"
            explicacion = "Artistas muy parecidos en características"
        elif porcentaje_similitud > 50:
            nivel = "✅ SIMILARES"
            explicacion = "Artistas con varias características en común"
        elif porcentaje_similitud > 25:
            nivel = "⚠️ POCO SIMILARES"
            explicacion = "Algunas similitudes, pero muchas diferencias"
        else:
            nivel = "❌ MUY DIFERENTES"
            explicacion = "Artistas con características muy distintas"

        recomendacion = _generar_recomendacion_artistas(artista1, artista2, porcentaje_similitud)

        return {
            "artista1": {
                "id": artista1.id,
                "nombre": artista1.nombre,
                "genero_principal": artista1.genero_principal,
                "pais": artista1.pais,
                "popularidad": artista1.popularidad,
                "total_canciones": len(canciones_artista1),
                "imagen_url": artista1.imagen_url
            },
            "artista2": {
                "id": artista2.id,
                "nombre": artista2.nombre,
                "genero_principal": artista2.genero_principal,
                "pais": artista2.pais,
                "popularidad": artista2.popularidad,
                "total_canciones": len(canciones_artista2),
                "imagen_url": artista2.imagen_url
            },
            "comparacion": {
                "porcentaje_similitud": porcentaje_similitud,
                "nivel": nivel,
                "explicacion": explicacion,
                "puntuacion_total": round(puntuacion_total, 1),
                "max_puntuacion": max_puntuacion,
                "detalles": comparaciones
            },
            "recomendacion": recomendacion
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparando artistas locales: {e}")
        raise HTTPException(500, "Error en comparación")

def _generar_insight_canciones(cancion1, cancion2, comparaciones):
    """Genera un insight basado en la comparación"""
    insights = []

    # Verificar si son del mismo artista
    if cancion1.artista.lower() == cancion2.artista.lower():
        insights.append(f"Ambas son de {cancion1.artista}")

    # Comparar tempo
    tempo_diff = abs(cancion1.tempo - cancion2.tempo)
    if tempo_diff < 10:
        insights.append("Tempo muy similar")
    elif tempo_diff > 50:
        insights.append("Tempo muy diferente")

    # Comparar energy
    energy_diff = abs(cancion1.energy - cancion2.energy)
    if energy_diff < 0.2:
        insights.append("Nivel de energía similar")

    if cancion1.danceability and cancion2.danceability:
        dance_diff = abs(cancion1.danceability - cancion2.danceability)
        if dance_diff < 0.2:
            insights.append("Bailabilidad similar")

    if not insights:
        return "Canciones con características mixtas"

    return ". ".join(insights) + "."

def _generar_recomendacion_artistas(artista1, artista2, similitud):
    if similitud > 75:
        return f"¡{artista1.nombre} y {artista2.nombre} son muy similares! Podrían colaborar."
    elif similitud > 50:
        return f"{artista1.nombre} y {artista2.nombre} comparten características. Buen match."
    elif similitud > 25:
        return f"Algunas similitudes entre {artista1.nombre} y {artista2.nombre}, pero son distintos."
    else:
        return f"{artista1.nombre} y {artista2.nombre} son bastante diferentes entre sí."

# ========== ENDPOINTS ORIGINALES (JSON) ==========

@router.get("/api/artistas/{artista1_id}/{artista2_id}")
async def comparar_artistas_locales_api(
    artista1_id: int,
    artista2_id: int,
    session: Session = Depends(get_session)
):
    """API: Comparar artistas locales (JSON) - ORIGINAL"""
    return await comparar_artistas_locales(artista1_id, artista2_id, session)

@router.get("/api/canciones/{cancion1_id}/{cancion2_id}")
async def comparar_canciones_locales_api(
    cancion1_id: str,
    cancion2_id: str,
    session: Session = Depends(get_session)
):
    """API: Comparar canciones locales (JSON) - ORIGINAL"""
    return await comparar_canciones_locales(cancion1_id, cancion2_id, session)

@router.get("/api/artista-con-spotify/{artista_id}")
async def comparar_artista_con_spotify(
    artista_id: int,
    session: Session = Depends(get_session)
):
    """API: Wrapper para comparación con Spotify"""
    return {
        "message": "Usa el endpoint /comparar/artista/{id} para comparar con Spotify",
        "endpoint": f"/comparar/artista/{artista_id}",
        "descripcion": "Compara tu artista local con artistas similares en Spotify"
    }

@router.get("/api/cancion-con-spotify/{cancion_id}")
async def comparar_cancion_con_spotify(
    cancion_id: str,
    session: Session = Depends(get_session)
):
    """API: Wrapper para comparación con Spotify"""
    return {
        "message": "Usa el endpoint /comparar/cancion/{id} para comparar con Spotify",
        "endpoint": f"/comparar/cancion/{cancion_id}",
        "descripcion": "Compara tu canción local con canciones similares en Spotify"
    }