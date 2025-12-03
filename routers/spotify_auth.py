from fastapi import APIRouter, HTTPException
from services.spotify_service import get_spotify_token

router = APIRouter(prefix="/spotify/auth", tags=["Spotify Auth"])

def get_spotify_token_dependency():
    """Dependencia para spotify_data.py"""
    try:
        return get_spotify_token()
    except Exception as e:
        raise HTTPException(401, f"Error token Spotify: {str(e)}")

@router.get("/token")
def obtener_token():
    try:
        token = get_spotify_token()
        return {
            "status": "✅ Token válido",
            "token": token[:50] + "...",
            "length": len(token)
        }
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@router.get("/test")
def test_spotify():
    try:
        token = get_spotify_token()
        return {"status": "✅ Spotify CONECTADO", "token": "Disponible"}
    except Exception as e:
        return {"status": "❌ Spotify FALLÓ", "error": str(e)}