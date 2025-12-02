from fastapi import APIRouter, HTTPException, status
from starlette.responses import RedirectResponse
import urllib.parse
import requests
import os
from services.spotify_auth_service import (
    CLIENT_ID,
    REDIRECT_URI,
    SPOTIFY_REFRESH_TOKEN,
    TOKEN_URL,
    get_spotify_access_token  # Importamos la función para refrescar
)

router = APIRouter(prefix="/spotify", tags=["Spotify Auth"])


# 1. Endpoint para iniciar la autenticación
@router.get("/login")
def spotify_login():
    """Redirige al usuario a la página de inicio de sesión de Spotify."""
    # Permisos que solicita tu app (para leer datos de canciones)
    scope = 'user-read-private user-read-email'

    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': 'true'
    }

    # !!! IMPORTANTE !!!
    # REEMPLAZA ESTA URL MARCADOR CON LA URL REAL DE SPOTIFY PARA AUTORIZACIÓN
    AUTH_URL = "https://accounts.spotify.com/authorize"

    auth_url = AUTH_URL + '?' + urllib.parse.urlencode(params)
    return RedirectResponse(auth_url)


# 2. Endpoint de Callback (donde Spotify devuelve el código)
@router.get("/callback")
def spotify_callback(code: str, state: str = None):
    """Maneja la respuesta de Spotify y obtiene el Refresh Token."""
    # Necesitamos acceder a la variable global definida en el servicio
    global SPOTIFY_REFRESH_TOKEN

    try:
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI
        }

        # El Client Secret debe ser enviado
        auth_header = requests.auth.HTTPBasicAuth(CLIENT_ID, os.getenv("SPOTIFY_CLIENT_SECRET"))

        # Usamos TOKEN_URL definida en el servicio
        response = requests.post(TOKEN_URL, auth=auth_header, data=data)
        response.raise_for_status()

        token_data = response.json()

        # ¡Guardamos el Refresh Token de larga duración!
        global SPOTIFY_REFRESH_TOKEN
        SPOTIFY_REFRESH_TOKEN = token_data.get('refresh_token')

        return {"message": "✅ Autenticación de Spotify exitosa. Refresh Token guardado.",
                "refresh_token_available": True}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Fallo de autenticación: {e}")


# 3. Función de dependencia para obtener un token fresco en otros routers
def get_spotify_token_dependency():
    """Dependencia de FastAPI para obtener un token fresco en cada solicitud."""
    try:
        return get_spotify_access_token()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Fallo al refrescar el token")