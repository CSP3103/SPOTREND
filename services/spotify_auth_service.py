import os
import requests
from dotenv import load_dotenv

# Asegúrate de cargar las variables de entorno
load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

# !!! IMPORTANTE !!!
# REEMPLAZA ESTA URL MARCADOR CON LA URL REAL DE SPOTIFY PARA TOKEN EXCHANGE
TOKEN_URL = "https://accounts.spotify.com/api/token"

# Variable global para almacenar el Refresh Token de larga duración
SPOTIFY_REFRESH_TOKEN = None


# 1. Función para obtener un nuevo Access Token usando el Refresh Token
def refresh_access_token(refresh_token: str) -> str:
    """Solicita un nuevo Access Token a Spotify usando un Refresh Token caducado."""

    # Spotify requiere las credenciales codificadas en Basic Auth
    auth_header = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }

    response = requests.post(TOKEN_URL, auth=auth_header, data=data)
    response.raise_for_status()  # Lanza excepción si el estado HTTP es 4xx/5xx

    token_data = response.json()

    # Esta función solo devuelve el nuevo token de acceso (Access Token)
    return token_data['access_token']


# 2. Función para obtener el token que se usará en las peticiones de datos
def get_spotify_access_token():
    """Devuelve un Access Token válido (refresca si es necesario)."""

    global SPOTIFY_REFRESH_TOKEN

    if not SPOTIFY_REFRESH_TOKEN:
        raise ValueError("Refresh Token no disponible. Debe autenticarse primero en /spotify/login.")

    try:
        # Llamamos al refresh cada vez (simplificado)
        new_access_token = refresh_access_token(SPOTIFY_REFRESH_TOKEN)
        return new_access_token
    except Exception as e:
        print(f"Error al refrescar el token de Spotify: {e}")
        raise e