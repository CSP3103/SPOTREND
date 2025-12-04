from fastapi import APIRouter, Depends, HTTPException
from routers.spotify_auth import get_spotify_token_dependency
import requests
import logging
import asyncio

router = APIRouter(prefix="/spotify/info", tags=["Información Spotify"])
logger = logging.getLogger(__name__)


@router.get("/artista/{artista_id}")
async def obtener_info_artista_spotify(
        artista_id: str,
        token: str = Depends(get_spotify_token_dependency)
):
    try:
        await asyncio.sleep(0.01)
        headers = {'Authorization': f'Bearer {token}'}

        response = requests.get(
            f'https://api.spotify.com/v1/artists/{artista_id}',
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            raise HTTPException(404, f"Artista no encontrado en Spotify")

        artista_data = response.json()

        top_tracks_response = requests.get(
            f'https://api.spotify.com/v1/artists/{artista_id}/top-tracks?market=CO',
            headers=headers,
            timeout=10
        )

        top_tracks = []
        if top_tracks_response.status_code == 200:
            for track in top_tracks_response.json().get('tracks', [])[:5]:
                top_tracks.append({
                    'id': track['id'],
                    'nombre': track['name'],
                    'album': track['album']['name'],
                    'popularidad': track.get('popularity'),
                    'duracion_ms': track.get('duration_ms'),
                    'preview_url': track.get('preview_url'),
                    'imagen': track['album']['images'][0]['url'] if track['album']['images'] else None
                })

        albums_response = requests.get(
            f'https://api.spotify.com/v1/artists/{artista_id}/albums?limit=5&market=CO',
            headers=headers,
            timeout=10
        )

        albums = []
        if albums_response.status_code == 200:
            for album in albums_response.json().get('items', []):
                albums.append({
                    'id': album['id'],
                    'nombre': album['name'],
                    'tipo': album['album_type'],
                    'lanzamiento': album.get('release_date'),
                    'total_tracks': album.get('total_tracks'),
                    'imagen': album['images'][0]['url'] if album['images'] else None
                })

        related_response = requests.get(
            f'https://api.spotify.com/v1/artists/{artista_id}/related-artists',
            headers=headers,
            timeout=10
        )

        related_artists = []
        if related_response.status_code == 200:
            for artist in related_response.json().get('artists', [])[:5]:
                related_artists.append({
                    'id': artist['id'],
                    'nombre': artist['name'],
                    'generos': artist.get('genres', [])[:3],
                    'popularidad': artist.get('popularity'),
                    'imagen': artist['images'][0]['url'] if artist.get('images') else None
                })

        audio_stats = {
            'tempo_promedio': 0,
            'energy_promedio': 0,
            'danceability_promedio': 0,
            'valence_promedio': 0,
            'acousticness_promedio': 0
        }

        if top_tracks:
            tempo_total = energy_total = dance_total = valence_total = acoustic_total = 0
            tracks_con_features = 0

            for track in top_tracks[:3]:
                features_response = requests.get(
                    f'https://api.spotify.com/v1/audio-features/{track["id"]}',
                    headers=headers,
                    timeout=10
                )

                if features_response.status_code == 200:
                    features = features_response.json()
                    tempo_total += features.get('tempo', 0)
                    energy_total += features.get('energy', 0)
                    dance_total += features.get('danceability', 0)
                    valence_total += features.get('valence', 0)
                    acoustic_total += features.get('acousticness', 0)
                    tracks_con_features += 1

            if tracks_con_features > 0:
                audio_stats = {
                    'tempo_promedio': round(tempo_total / tracks_con_features, 1),
                    'energy_promedio': round(energy_total / tracks_con_features, 3),
                    'danceability_promedio': round(dance_total / tracks_con_features, 3),
                    'valence_promedio': round(valence_total / tracks_con_features, 3),
                    'acousticness_promedio': round(acoustic_total / tracks_con_features, 3)
                }

        return {
            "artista": {
                "id": artista_data.get('id'),
                "nombre": artista_data.get('name'),
                "generos": artista_data.get('genres', []),
                "popularidad": artista_data.get('popularity'),
                "seguidores": artista_data.get('followers', {}).get('total', 0),
                "imagen": artista_data['images'][0]['url'] if artista_data.get('images') else None,
                "enlace_spotify": artista_data.get('external_urls', {}).get('spotify')
            },
            "estadisticas_audio": audio_stats,
            "top_tracks": {
                "total": len(top_tracks),
                "tracks": top_tracks
            },
            "discografia": {
                "total_albums": len(albums),
                "albums": albums
            },
            "artistas_relacionados": {
                "total": len(related_artists),
                "artistas": related_artists
            },
            "metadata": {
                "fuente": "Spotify API",
                "actualizado": "En tiempo real",
                "artista_id": artista_id
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo info artista {artista_id}: {e}")
        return {
            "error": "No se pudo obtener información del artista",
            "detalle": str(e)[:200],
            "artista_id": artista_id
        }


@router.get("/buscar-artista/{nombre}")
async def buscar_artista_spotify(
        nombre: str,
        token: str = Depends(get_spotify_token_dependency)
):
    try:
        await asyncio.sleep(0.01)
        headers = {'Authorization': f'Bearer {token}'}
        params = {
            'q': nombre,
            'type': 'artist',
            'limit': 10,
            'market': 'CO'
        }

        response = requests.get(
            'https://api.spotify.com/v1/search',
            headers=headers,
            params=params,
            timeout=10
        )

        if response.status_code != 200:
            raise HTTPException(500, "Error conectando con Spotify")

        artists_data = response.json().get('artists', {}).get('items', [])

        resultados = []
        for artist in artists_data:
            resultados.append({
                "id": artist['id'],
                "nombre": artist['name'],
                "generos": artist.get('genres', [])[:3],
                "popularidad": artist.get('popularity'),
                "seguidores": artist.get('followers', {}).get('total', 0),
                "imagen": artist['images'][0]['url'] if artist.get('images') else None,
                "enlace_spotify": artist.get('external_urls', {}).get('spotify')
            })

        return {
            "busqueda": nombre,
            "total_resultados": len(resultados),
            "resultados": resultados
        }

    except Exception as e:
        logger.error(f"Error buscando artista {nombre}: {e}")
        return {
            "busqueda": nombre,
            "error": "Error en la búsqueda",
            "resultados": []
        }


@router.get("/track/{track_id}")
async def obtener_info_track_spotify(
        track_id: str,
        token: str = Depends(get_spotify_token_dependency)
):
    try:
        await asyncio.sleep(0.01)
        headers = {'Authorization': f'Bearer {token}'}

        track_response = requests.get(
            f'https://api.spotify.com/v1/tracks/{track_id}',
            headers=headers,
            timeout=10
        )

        if track_response.status_code != 200:
            raise HTTPException(404, "Track no encontrado")

        track_data = track_response.json()

        features_response = requests.get(
            f'https://api.spotify.com/v1/audio-features/{track_id}',
            headers=headers,
            timeout=10
        )

        features = {}
        if features_response.status_code == 200:
            features = features_response.json()

        main_artist = track_data.get('artists', [{}])[0]
        artist_info = {
            "id": main_artist.get('id'),
            "nombre": main_artist.get('name')
        } if main_artist else {}

        return {
            "track": {
                "id": track_data.get('id'),
                "nombre": track_data.get('name'),
                "duracion_ms": track_data.get('duration_ms'),
                "popularidad": track_data.get('popularity'),
                "track_number": track_data.get('track_number'),
                "explicito": track_data.get('explicit'),
                "preview_url": track_data.get('preview_url'),
                "enlace_spotify": track_data.get('external_urls', {}).get('spotify')
            },
            "album": {
                "id": track_data.get('album', {}).get('id'),
                "nombre": track_data.get('album', {}).get('name'),
                "tipo": track_data.get('album', {}).get('album_type'),
                "lanzamiento": track_data.get('album', {}).get('release_date'),
                "imagen": track_data.get('album', {}).get('images', [{}])[0].get('url')
            },
            "artistas": [
                {
                    "id": artist.get('id'),
                    "nombre": artist.get('name'),
                    "enlace_spotify": artist.get('external_urls', {}).get('spotify')
                } for artist in track_data.get('artists', [])
            ],
            "audio_features": {
                "tempo": features.get('tempo'),
                "energy": features.get('energy'),
                "danceability": features.get('danceability'),
                "valence": features.get('valence'),
                "acousticness": features.get('acousticness'),
                "instrumentalness": features.get('instrumentalness'),
                "liveness": features.get('liveness'),
                "speechiness": features.get('speechiness'),
                "loudness": features.get('loudness'),
                "key": features.get('key'),
                "mode": features.get('mode'),
                "time_signature": features.get('time_signature')
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo track {track_id}: {e}")
        return {
            "error": "No se pudo obtener información del track",
            "track_id": track_id
        }