from fastapi import UploadFile, HTTPException, status
from typing import Optional
import uuid
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Claves del .env
SUPABASE_URL = os.getenv("SUPABASE_URL_MAR")
SUPABASE_KEY = os.getenv("SUPABASE_KEY_MAR")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET_MAR")

_supabase_client: Optional[Client] = None


def get_supabase_client():
    """Obtiene el cliente de Supabase (Singleton)."""
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Faltan credenciales de Supabase en .env")
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client


async def upload_to_bucket(file: UploadFile) -> str:
    """Sube archivo a Supabase Storage y retorna URL pública."""
    client = get_supabase_client()

    if not SUPABASE_BUCKET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bucket no configurado"
        )

    # Generar nombre único
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'dat'
    unique_filename = f"{uuid.uuid4()}.{ext}"
    file_path = f"portadas/{unique_filename}"

    try:
        # Leer contenido
        file_content = await file.read()

        # Subir a Supabase
        client.storage.from_(SUPABASE_BUCKET).upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": file.content_type}
        )

        # Obtener URL pública
        public_url = client.storage.from_(SUPABASE_BUCKET).get_public_url(file_path)
        return public_url

    except Exception as e:
        print(f"Error al subir a Supabase: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Fallo al subir imagen: {str(e)}"
        )