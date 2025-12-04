from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from database import get_session
from models import Cancion, Artista
from routers.spotify_auth import get_spotify_token_dependency
import requests
import logging
from difflib import SequenceMatcher
import asyncio

router = APIRouter(prefix="/comparar", tags=["Comparación Spotify"])
logger = logging.getLogger(__name__)

# Templates
templates = Jinja2Templates(directory="templates")

# ========== ENDPOINTS HTML ==========

@router.get("/cancion/{cancion_id}", response_class=HTMLResponse)
async def comparar_cancion_spotify_html(
    request: Request,
    cancion_id: str,
    token: str = Depends(get_spotify_token_dependency),
    session: Session = Depends(get_session)
):
    """Comparar canción con Spotify (HTML)"""
    try:
        resultado = await comparar_cancion_spotify(cancion_id, token, session)
        return templates.TemplateResponse("comparacion_spotify/comparar_cancion.html", {
            "request": request,
            "comparacion": resultado
        })
    except Exception as e:
        logger.error(f"Error comparando canción HTML: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error comparando con Spotify: {str(e)}"
        })


@router.get("/artista/{artista_id}", response_class=HTMLResponse)
async def comparar_artista_spotify_html(
    request: Request,
    artista_id: int,
    token: str = Depends(get_spotify_token_dependency),
    session: Session = Depends(get_session)
):
    """Comparar artista con Spotify (HTML)"""
    try:
        resultado = await comparar_artista_spotify(artista_id, token, session)
        return templates.TemplateResponse("comparacion_spotify/comparar_artista.html", {
            "request": request,
            "comparacion": resultado
        })
    except Exception as e:
        logger.error(f"Error comparando artista HTML: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error comparando con Spotify: {str(e)}"
        })


# ========== FUNCIONES DE COMPARACIÓN (ORIGINALES) ==========

def similitud_texto(texto1: str, texto2: str) -> float:
    if not texto1 or not texto2:
        return 0
    return SequenceMatcher(None, texto1.lower(), texto2.lower()).ratio() * 100


async def comparar_cancion_spotify(
    cancion_id: str,
    token: str,
    session: Session
):
    """Comparar canción con Spotify"""
    try:
        await asyncio.sleep(0.01)
        cancion = session.get(Cancion, cancion_id)
        if not cancion:
            raise HTTPException(404, "Canción no encontrada")

        headers = {'Authorization': f'Bearer {token}'}
        params = {
            'q': f"{cancion.nombre} {cancion.artista}",
            'type': 'track',
            'limit': 10
        }

        response = requests.get(
            'https://api.spotify.com/v1/search',
            headers=headers,
            params=params
        )

        if response.status_code != 200:
            return {
                "cancion_local": cancion,
                "error": "No se pudo conectar con Spotify",
                "comparaciones": []
            }

        comparaciones = []
        tracks = response.json().get('tracks', {}).get('items', [])

        for track in tracks[:5]:
            track_id = track['id']

            features_response = requests.get(
                f'https://api.spotify.com/v1/audio-features/{track_id}',
                headers=headers
            )

            features = {}
            if features_response.status_code == 200:
                features = features_response.json()

            sim_nombre = similitud_texto(cancion.nombre, track['name'])
            sim_artista = similitud_texto(cancion.artista, track['artists'][0]['name'])

            sim_tecnica = 0
            if features:
                tempo_diff = abs(cancion.tempo - (features.get('tempo') or 0)) / 200 * 100
                energy_diff = abs(cancion.energy - (features.get('energy') or 0)) * 100
                sim_tecnica = 100 - ((tempo_diff + energy_diff) / 2)
                if sim_tecnica < 0:
                    sim_tecnica = 0

            sim_total = (sim_nombre * 0.4) + (sim_artista * 0.4) + (sim_tecnica * 0.2)

            comparaciones.append({
                "spotify_track": {
                    "id": track_id,
                    "nombre": track['name'],
                    "artista": track['artists'][0]['name'],
                    "album": track['album']['name'],
                    "imagen": track['album']['images'][0]['url'] if track['album']['images'] else None,
                    "preview_url": track.get('preview_url'),
                    "popularity": track.get('popularity')
                },
                "similitudes": {
                    "nombre": round(sim_nombre, 1),
                    "artista": round(sim_artista, 1),
                    "tecnica": round(sim_tecnica, 1),
                    "total": round(sim_total, 1)
                },
                "match": "🎯 ALTO" if sim_total > 75 else "✅ MEDIO" if sim_total > 50 else "⚠️ BAJO"
            })

        comparaciones.sort(key=lambda x: x["similitudes"]["total"], reverse=True)

        return {
            "cancion_local": cancion,
            "total_encontrado": len(tracks),
            "mejor_match": comparaciones[0] if comparaciones else None,
            "comparaciones": comparaciones
        }

    except Exception as e:
        logger.error(f"Error comparando canción: {e}")
        return {
            "cancion_local": {"id": cancion_id, "error": "No disponible"},
            "error": str(e),
            "comparaciones": []
        }


async def comparar_artista_spotify(
    artista_id: int,
    token: str,
    session: Session
):
    """Comparar artista con Spotify"""
    try:
        await asyncio.sleep(0.01)
        artista = session.get(Artista, artista_id)
        if not artista:
            raise HTTPException(404, "Artista no encontrado")

        headers = {'Authorization': f'Bearer {token}'}
        params = {
            'q': artista.nombre,
            'type': 'artist',
            'limit': 10
        }

        response = requests.get(
            'https://api.spotify.com/v1/search',
            headers=headers,
            params=params
        )

        if response.status_code != 200:
            return {
                "artista_local": artista,
                "error": "No se pudo conectar con Spotify",
                "comparaciones": []
            }

        comparaciones = []
        artists = response.json().get('artists', {}).get('items', [])

        for artist in artists[:5]:
            sim_nombre = similitud_texto(artista.nombre, artist['name'])

            sim_genero = 0
            if artista.genero_principal and artist.get('genres'):
                genero_local = artista.genero_principal.lower()
                for genero_spotify in artist['genres']:
                    if genero_local in genero_spotify.lower():
                        sim_genero = 100
                        break

            sim_total = (sim_nombre * 0.8) + (sim_genero * 0.2)

            comparaciones.append({
                "spotify_artist": {
                    "id": artist['id'],
                    "nombre": artist['name'],
                    "generos": artist.get('genres', []),
                    "popularity": artist.get('popularity'),
                    "seguidores": artist.get('followers', {}).get('total', 0),
                    "imagen": artist['images'][0]['url'] if artist.get('images') else None
                },
                "similitudes": {
                    "nombre": round(sim_nombre, 1),
                    "genero": round(sim_genero, 1),
                    "total": round(sim_total, 1)
                },
                "match": "🎯 ALTO" if sim_total > 80 else "✅ MEDIO" if sim_total > 50 else "⚠️ BAJO"
            })

        comparaciones.sort(key=lambda x: x["similitudes"]["total"], reverse=True)

        return {
            "artista_local": artista,
            "total_encontrado": len(artists),
            "mejor_match": comparaciones[0] if comparaciones else None,
            "comparaciones": comparaciones
        }

    except Exception as e:
        logger.error(f"Error comparando artista: {e}")
        return {
            "artista_local": {"id": artista_id, "error": "No disponible"},
            "error": str(e),
            "comparaciones": []
        }


# ========== ENDPOINTS ORIGINALES (JSON) ==========

@router.get("/api/cancion/{cancion_id}")
async def comparar_cancion_spotify_api(
    cancion_id: str,
    token: str = Depends(get_spotify_token_dependency),
    session: Session = Depends(get_session)
):
    """API: Comparar canción con Spotify (JSON) - ORIGINAL"""
    return await comparar_cancion_spotify(cancion_id, token, session)


@router.get("/api/artista/{artista_id}")
async def comparar_artista_spotify_api(
    artista_id: int,
    token: str = Depends(get_spotify_token_dependency),
    session: Session = Depends(get_session)
):
    """API: Comparar artista con Spotify (JSON) - ORIGINAL"""
    return await comparar_artista_spotify(artista_id, token, session)