from fastapi import APIRouter, Depends, HTTPException, status
import requests
from typing import Dict, Any, List
from routers.spotify_auth import get_spotify_token_dependency

router = APIRouter(prefix="/spotify/data", tags=["Spotify Data"])

# !!! URL REAL DE SPOTIFY PARA LA API DE DATOS (v1) !!!
API_URL = "http://googleusercontent.com/api.spotify.com/v1"


# 1. Endpoint para buscar canciones
@router.get("/search", response_model=List[Dict[str, Any]])
def search_track(
        query: str,
        token: str = Depends(get_spotify_token_dependency)  # Usa el token fresco
):
    """Busca canciones por nombre o artista en Spotify."""
    headers = {"Authorization": f"Bearer {token}"}

    params = {
        "q": query,
        "type": "track",
        "limit": 5,
        "market": "ES"
    }

    try:
        response = requests.get(f"{API_URL}/search", headers=headers, params=params)
        response.raise_for_status()

        data = response.json()

        tracks = []
        for item in data.get('tracks', {}).get('items', []):
            tracks.append({
                "spotify_id": item['id'],
                "nombre": item['name'],
                "artista": item['artists'][0]['name'],
                "imagen_url": item['album']['images'][0]['url'] if item['album']['images'] else None,
                "preview_url": item.get('preview_url')
            })
        return tracks

    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Error en Spotify API: {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno: {e}")


# 2. Endpoint para obtener Audio Features (Tempo, Energy, etc.)
@router.get("/audio-features/{spotify_id}", response_model=Dict[str, Any])
def get_audio_features(
        spotify_id: str,
        token: str = Depends(get_spotify_token_dependency)
):
    """Obtiene las métricas de audio necesarias para el análisis(Tempo, Energy, Danceability)."""
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(f"{API_URL}/audio-features/{spotify_id}", headers=headers)
        response.raise_for_status()

        features = response.json()

        return {
            "spotify_id": features.get("id"),
            "tempo": features.get("tempo"),
            "energy": features.get("energy"),
            "danceability": features.get("danceability"),
            "valence": features.get("valence"),
            "acousticness": features.get("acousticness"),
        }

    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Error en Spotify API: {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno: {e}")