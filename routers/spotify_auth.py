from fastapi import APIRouter, Depends, HTTPException, status
from starlette.responses import RedirectResponse
import urllib.parse
import requests
import os
from sqlmodel import Session, select  # Imports de DB
from database import get_session
from models import Configuracion  # Importa el modelo
from services.spotify_auth_service import (
    CLIENT_ID,
    REDIRECT_URI,
    TOKEN_URL,
)

# Nota: La dependencia get_spotify_token_dependency permanece igual


router = APIRouter(prefix="/spotify", tags=["Spotify Auth"])


# 1. Endpoint para iniciar la autenticación (SIN CAMBIOS)
@router.get("/login")
def spotify_login():
    """Redirige al usuario a la página de inicio de sesión de Spotify."""
    scope = 'user-read-private user-read-email'

    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': 'true'
    }

    # !!! URL REAL DE SPOTIFY PARA AUTORIZACIÓN !!!
    AUTH_URL = "https://accounts.spotify.com/authorize"

    auth_url = AUTH_URL + '?' + urllib.parse.urlencode(params)
    return RedirectResponse(auth_url)


# 2. Endpoint de Callback (CON CAMBIOS)
@router.get("/callback")
def spotify_callback(code: str, state: str = None, session: Session = Depends(get_session)):
    """Maneja la respuesta de Spotify y obtiene el Refresh Token, guardándolo en la DB."""

    try:
        # 1. Obtener el token de Spotify (sin cambios)
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI
        }

        auth_header = requests.auth.HTTPBasicAuth(CLIENT_ID, os.getenv("SPOTIFY_CLIENT_SECRET"))

        response = requests.post(TOKEN_URL, auth=auth_header, data=data)
        response.raise_for_status()

        token_data = response.json()

        refresh_token = token_data.get('refresh_token')

        if not refresh_token:
            return {"message": "✅ Autenticación de Spotify exitosa. Token de acceso refrescado.",
                    "refresh_token_available": True}

        # 2. Persistir el Refresh Token en la base de datos (NUEVA LÓGICA)

        # Intentar obtener el registro existente
        statement = select(Configuracion).where(Configuracion.clave == 'SPOTIFY_REFRESH_TOKEN')
        db_config = session.exec(statement).first()

        if db_config:
            # Si ya existe, actualiza el valor
            db_config.valor = refresh_token
        else:
            # Si no existe, crea un nuevo registro
            db_config = Configuracion(
                clave='SPOTIFY_REFRESH_TOKEN',
                valor=refresh_token
            )

        session.add(db_config)
        session.commit()

        return {"message": "✅ Autenticación de Spotify exitosa. Refresh Token guardado en la DB.",
                "refresh_token_available": True}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Fallo de autenticación: {e}")


# 3. Función de dependencia para obtener un token fresco en otros routers (SIN CAMBIOS)
def get_spotify_token_dependency():
    """Dependencia de FastAPI para obtener un token fresco en cada solicitud."""
    # Importación local para evitar la dependencia circular (service usa router, router usa service)
    from services.spotify_auth_service import get_spotify_access_token

    try:
        return get_spotify_access_token()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Fallo al refrescar el token. Intente autenticarse de nuevo.")