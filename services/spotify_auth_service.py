import os
import requests
from dotenv import load_dotenv
from sqlmodel import Session, select
from models import Configuracion
from database import engine

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
TOKEN_URL = "https://accounts.spotify.com/api/token"


def get_refresh_token_from_db() -> str:
    """Obtiene refresh token desde la base de datos."""
    with Session(engine) as session:
        statement = select(Configuracion).where(
            Configuracion.clave == 'SPOTIFY_REFRESH_TOKEN'
        )
        config = session.exec(statement).first()

        if not config or not config.valor:
            raise ValueError(
                "❌ Refresh Token no disponible. "
                "Debes autenticarte primero en: /spotify/login"
            )

        return config.valor


def refresh_access_token(refresh_token: str) -> str:
    """Obtiene nuevo access token usando refresh token."""
    auth_header = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }

    response = requests.post(TOKEN_URL, auth=auth_header, data=data)

    if response.status_code != 200:
        raise ValueError(f"Error al refrescar token: {response.status_code}")

    token_data = response.json()
    return token_data['access_token']


def get_spotify_access_token() -> str:
    """Devuelve access token válido."""
    try:
        refresh_token = get_refresh_token_from_db()
        access_token = refresh_access_token(refresh_token)
        return access_token
    except Exception as e:
        print(f"❌ Error en get_spotify_access_token: {str(e)}")
        raise