from fastapi import APIRouter, Depends, HTTPException
import requests
from routers.spotify_auth import get_spotify_token_dependency

router = APIRouter(prefix="/spotify/data", tags=["Spotify Data"])


@router.get("/search")
def buscar_canciones(
        query: str,
        limit: int = 5,
        token: str = Depends(get_spotify_token_dependency)
):
    headers = {'Authorization': f'Bearer {token}'}
    params = {
        'q': query,
        'type': 'track',
        'limit': limit,
        'market': 'CO'
    }

    response = requests.get(
        'https://api.spotify.com/v1/search',
        headers=headers,
        params=params,
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()

        tracks = []
        for item in data.get('tracks', {}).get('items', []):
            track = {
                'spotify_id': item['id'],
                'nombre': item['name'],
                'artista': item['artists'][0]['name'] if item['artists'] else 'Unknown',
                'album': item['album']['name'],
                'imagen_url': item['album']['images'][0]['url'] if item['album']['images'] else None,
                'preview_url': item.get('preview_url'),
                'popularity': item.get('popularity', 0)
            }
            tracks.append(track)

        return {
            'query': query,
            'total': len(tracks),
            'tracks': tracks
        }
    else:
        raise HTTPException(response.status_code, f"Spotify API: {response.text}")


@router.get("/audio-features/{track_id}")
def obtener_audio_features(
        track_id: str,
        token: str = Depends(get_spotify_token_dependency)
):
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(
        f'https://api.spotify.com/v1/audio-features/{track_id}',
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        features = response.json()
        return {
            'tempo': features.get('tempo'),
            'energy': features.get('energy'),
            'danceability': features.get('danceability'),
            'valence': features.get('valence'),
            'acousticness': features.get('acousticness')
        }
    else:
        raise HTTPException(response.status_code, f"Spotify API: {response.text}")