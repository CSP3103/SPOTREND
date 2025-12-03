from fastapi import APIRouter, Depends, HTTPException, status
import requests
from typing import List, Dict, Any
from routers.spotify_auth import get_spotify_token_dependency

router = APIRouter(prefix="/spotify/data", tags=["Spotify Data"])

API_URL = "https://api.spotify.com/v1"


@router.get("/search", response_model=List[Dict[str, Any]])
def search_track(
        query: str,
        token: str = Depends(get_spotify_token_dependency)
):
    """Busca canciones en Spotify."""
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "q": query,
        "type": "track",
        "limit": 10,
        "market": "ES"
    }

    try:
        response = requests.get(
            f"{API_URL}/search",
            headers=headers,
            params=params
        )
        response.raise_for_status()

        data = response.json()
        tracks = []

        for item in data.get('tracks', {}).get('items', []):
            track_data = {
                "spotify_id": item['id'],
                "nombre": item['name'],
                "artista": item['artists'][0]['name'] if item['artists'] else "Desconocido",
                "imagen_url": item['album']['images'][0]['url'] if item['album']['images'] else None,
                "preview_url": item.get('preview_url'),
                "album": item['album']['name'],
                "popularidad": item.get('popularity', 0)
            }
            tracks.append(track_data)

        return tracks

    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code if e.response else 500,
            detail=f"Error Spotify API: {e}"
        )


@router.get("/audio-features/{spotify_id}")
def get_audio_features(
        spotify_id: str,
        token: str = Depends(get_spotify_token_dependency)
):
    """Obtiene audio features de una canción."""
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(
            f"{API_URL}/audio-features/{spotify_id}",
            headers=headers
        )
        response.raise_for_status()

        features = response.json()
        return {
            "spotify_id": features.get("id"),
            "tempo": features.get("tempo"),
            "energy": features.get("energy"),
            "danceability": features.get("danceability"),
            "valence": features.get("valence"),
            "acousticness": features.get("acousticness"),
            "instrumentalness": features.get("instrumentalness"),
            "liveness": features.get("liveness"),
            "loudness": features.get("loudness")
        }

    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code if e.response else 500,
            detail=f"Error Spotify API: {e}"
        )


@router.get("/artist/{artist_id}")
def get_artist_info(
        artist_id: str,
        token: str = Depends(get_spotify_token_dependency)
):
    """Obtiene información de un artista."""
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(
            f"{API_URL}/artists/{artist_id}",
            headers=headers
        )
        response.raise_for_status()

        artist = response.json()
        return {
            "id": artist.get("id"),
            "nombre": artist.get("name"),
            "generos": artist.get("genres", []),
            "popularidad": artist.get("popularity"),
            "imagen_url": artist['images'][0]['url'] if artist.get('images') else None,
            "seguidores": artist.get("followers", {}).get("total", 0)
        }

    except requests.exceptions.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code if e.response else 500,
            detail=f"Error Spotify API: {e}"
        )