from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from routers.spotify_auth import get_spotify_token_dependency
import requests
import asyncio
import logging

router = APIRouter(prefix="/spotify-info", tags=["Spotify"])
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)

# ======================================================
#                 MENU PRINCIPAL
# ======================================================

@router.get("/", response_class=HTMLResponse)
async def menu_spotify(request: Request):
    return templates.TemplateResponse("spotify/menu.html", {"request": request})


# ======================================================
#           BUSCAR ARTISTA (FORM + RESULTADO + JSON)
# ======================================================

@router.get("/buscar-artista", response_class=HTMLResponse)
async def buscar_artista_form(request: Request):
    return templates.TemplateResponse("spotify/buscar_artista.html", {
        "request": request,
        "busqueda": None,
        "resultados": None
    })


@router.get("/buscar-artista/resultado", response_class=HTMLResponse)
async def buscar_artista_resultado(
    request: Request,
    nombre: str,
    token: str = Depends(get_spotify_token_dependency)
):
    data = await buscar_artista_api(nombre, token)
    return templates.TemplateResponse("spotify/resultados_artista.html", {
        "request": request,
        "busqueda": nombre,
        "total": data["total_resultados"],
        "resultados": data["resultados"]
    })


@router.get("/api/buscar-artista/{nombre}")
async def buscar_artista_api(
    nombre: str,
    token: str = Depends(get_spotify_token_dependency)
):
    try:
        await asyncio.sleep(0.01)

        headers = {"Authorization": f"Bearer {token}"}
        params = {"q": nombre, "type": "artist", "limit": 10, "market": "CO"}

        r = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)
        items = r.json().get("artists", {}).get("items", [])

        resultados = []
        for a in items:
            resultados.append({
                "id": a["id"],
                "nombre": a["name"],
                "seguidores": a.get("followers", {}).get("total", 0),
                "popularidad": a.get("popularity", 0),
                "generos": a.get("genres", [])[:3],
                "imagen": a["images"][0]["url"] if a.get("images") else None
            })

        return {
            "busqueda": nombre,
            "total_resultados": len(resultados),
            "resultados": resultados
        }

    except Exception as e:
        logger.error(e)
        return {"busqueda": nombre, "total_resultados": 0, "resultados": []}

# ======================================================
#                INFO ARTISTA (HTML + JSON)
# ======================================================

@router.get("/artista/{id}", response_class=HTMLResponse)
async def artista_html(request: Request, id: str, token=Depends(get_spotify_token_dependency)):
    data = await artista_api(id, token)
    return templates.TemplateResponse("spotify/artista.html", {"request": request, "info": data})


@router.get("/api/artista/{id}")
async def artista_api(id: str, token=Depends(get_spotify_token_dependency)):
    headers = {"Authorization": f"Bearer {token}"}

    r = requests.get(f"https://api.spotify.com/v1/artists/{id}", headers=headers)
    if r.status_code != 200:
        raise HTTPException(404, "Artista no encontrado")

    data = r.json()

    return {
        "id": data["id"],
        "nombre": data["name"],
        "generos": data.get("genres", []),
        "seguidores": data["followers"]["total"],
        "popularidad": data["popularity"],
        "imagen": data["images"][0]["url"] if data.get("images") else None
    }


# ======================================================
#            BUSCAR TRACK (FORM + RESULTADO + JSON)
# ======================================================

@router.get("/buscar-track", response_class=HTMLResponse)
async def buscar_track_form(request: Request):
    return templates.TemplateResponse("spotify/buscar_track.html", {
        "request": request,
        "busqueda": None,
        "resultados": None
    })


@router.get("/buscar-track/resultado", response_class=HTMLResponse)
async def buscar_track_resultado(
    request: Request,
    nombre: str,
    token=Depends(get_spotify_token_dependency)
):
    data = await buscar_track_api(nombre, token)
    return templates.TemplateResponse("spotify/resultados_track.html", {
        "request": request,
        "busqueda": nombre,
        "total": data["total_resultados"],
        "resultados": data["resultados"]
    })


@router.get("/api/buscar-track/{nombre}")
async def buscar_track_api(nombre: str, token=Depends(get_spotify_token_dependency)):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": nombre, "type": "track", "limit": 10, "market": "CO"}

    r = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)
    items = r.json().get("tracks", {}).get("items", [])

    resultados = []
    for t in items:
        resultados.append({
            "id": t["id"],
            "nombre": t["name"],
            "artista": t["artists"][0]["name"],
            "imagen": t["album"]["images"][0]["url"] if t["album"].get("images") else None
        })

    return {
        "busqueda": nombre,
        "total_resultados": len(resultados),
        "resultados": resultados
    }


# ======================================================
#                INFO TRACK (HTML + JSON)
# ======================================================

@router.get("/track/{id}", response_class=HTMLResponse)
async def track_html(request: Request, id: str, token=Depends(get_spotify_token_dependency)):
    data = await track_api(id, token)
    return templates.TemplateResponse("spotify/track.html", {"request": request, "info": data})


@router.get("/api/track/{id}")
async def track_api(id: str, token=Depends(get_spotify_token_dependency)):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"https://api.spotify.com/v1/tracks/{id}", headers=headers)

    if r.status_code != 200:
        raise HTTPException(404, "Track no encontrado")

    data = r.json()
    return {
        "id": data["id"],
        "nombre": data["name"],
        "duracion": data["duration_ms"],
        "artista": data["artists"][0]["name"],
        "imagen": data["album"]["images"][0]["url"] if data["album"].get("images") else None
    }