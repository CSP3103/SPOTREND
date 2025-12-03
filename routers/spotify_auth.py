from fastapi import APIRouter, Depends, HTTPException, status
from starlette.responses import RedirectResponse
import urllib.parse
import requests
import os
from sqlmodel import Session, select
from datetime import datetime
from database import get_session
from models import Configuracion
from services.spotify_auth_service import get_spotify_access_token

router = APIRouter(prefix="/spotify", tags=["Spotify Auth"])

# Variables desde .env
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
TOKEN_URL = "https://accounts.spotify.com/api/token"
AUTH_URL = "https://accounts.spotify.com/authorize"


# 🔥 AÑADE ESTA FUNCIÓN (que falta en tu archivo original)
def get_spotify_token_dependency():
    """Dependencia FastAPI para obtener token fresco."""
    try:
        return get_spotify_access_token()
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Error al refrescar token")


@router.get("/login")
def spotify_login():
    """Redirige a login de Spotify."""
    scope = 'user-read-private user-read-email'

    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': 'true'
    }

    auth_url = AUTH_URL + '?' + urllib.parse.urlencode(params)
    return RedirectResponse(auth_url)


@router.get("/callback")
def spotify_callback(code: str, session: Session = Depends(get_session)):
    """Callback de Spotify - obtiene y guarda tokens."""
    try:
        # Obtener tokens
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI
        }

        auth_header = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
        response = requests.post(TOKEN_URL, auth=auth_header, data=data)
        response.raise_for_status()

        token_data = response.json()
        refresh_token = token_data.get('refresh_token')

        if not refresh_token:
            return {"message": "✅ Autenticación exitosa sin refresh token"}

        # Guardar en DB
        statement = select(Configuracion).where(
            Configuracion.clave == 'SPOTIFY_REFRESH_TOKEN'
        )
        db_config = session.exec(statement).first()

        if db_config:
            db_config.valor = refresh_token
            db_config.actualizado_en = datetime.utcnow()
        else:
            db_config = Configuracion(
                clave='SPOTIFY_REFRESH_TOKEN',
                valor=refresh_token
            )

        session.add(db_config)
        session.commit()

        return {
            "message": "✅ Autenticación exitosa",
            "refresh_token_saved": True
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de autenticación: {e}"
        )