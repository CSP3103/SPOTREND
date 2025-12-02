import os
import requests
from dotenv import load_dotenv
from sqlmodel import Session, select
# Imports necesarios para leer la DB
from models import Configuracion
from database import get_session
from typing import Generator

# Asegúrate de cargar las variables de entorno
load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

# !!! URL REAL DE SPOTIFY PARA TOKEN EXCHANGE !!!
TOKEN_URL = "https://accounts.spotify.com/api/token"


# --- Función para obtener el Refresh Token de la DB (NUEVO) ---
def get_refresh_token_from_db() -> str:
    """Busca el Refresh Token persistente en la tabla Configuracion."""

    # Creamos una sesión temporal para esta operación
    session_generator: Generator[Session, None, None] = get_session()
    session = next(session_generator)

    try:
        statement = select(Configuracion).where(Configuracion.clave == 'SPOTIFY_REFRESH_TOKEN')
        config = session.exec(statement).first()

        if not config or not config.valor:
            raise ValueError("Refresh Token no disponible. Debe autenticarse primero en /spotify/login.")

        return config.valor
    finally:
        # Siempre cerramos la sesión
        session.close()


# 1. Función para obtener un nuevo Access Token usando el Refresh Token
def refresh_access_token(refresh_token: str) -> str:
    """Solicita un nuevo Access Token a Spotify usando un Refresh Token caducado."""

    # ... (El cuerpo de esta función no cambia)
    auth_header = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }

    response = requests.post(TOKEN_URL, auth=auth_header, data=data)
    response.raise_for_status()

    token_data = response.json()

    return token_data['access_token']


# 2. Función para obtener el token que se usará en las peticiones de datos
def get_spotify_access_token():
    """Devuelve un Access Token válido (lee el Refresh Token de la DB y refresca)."""

    # 1. Obtener el Refresh Token persistente de la DB
    refresh_token = get_refresh_token_from_db()

    # 2. Usar el token para obtener uno nuevo (Access Token)
    try:
        new_access_token = refresh_access_token(refresh_token)
        return new_access_token
    except Exception as e:
        print(f"Error al refrescar el token de Spotify: {e}")
        raise e