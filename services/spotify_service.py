import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")


def get_spotify_token() -> str:
    """Obtiene token de Spotify con client credentials."""
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("❌ Faltan credenciales Spotify")

    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()

    headers = {
        'Authorization': f'Basic {auth_b64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {'grant_type': 'client_credentials'}

    response = requests.post(
        'https://accounts.spotify.com/api/token',
        headers=headers,
        data=data,
        timeout=10
    )

    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Error Spotify: {response.status_code}")