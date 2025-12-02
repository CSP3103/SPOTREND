import os
import uuid
from typing import Optional
from fastapi import UploadFile
from supabase import create_client, Client
from dotenv import load_dotenv
import asyncio

load_dotenv()

# Claves que leen del .env
SUPABASE_URL = os.getenv("SUPABASE_URL_MAR")
SUPABASE_KEY = os.getenv("SUPABASE_KEY_MAR")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET_MAR")

_supabase_client: Optional[Client] = None


def get_supabase_client():
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Faltan las credenciales SUPABASE_URL_MAR o SUPABASE_KEY_MAR en .env.")
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client


async def upload_to_bucket(file: UploadFile) -> str:
    client = get_supabase_client()

    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = f"portadas/{unique_filename}"

    try:
        file_content = await file.read()

        # Sube el archivo al Bucket
        client.storage.from_(SUPABASE_BUCKET).upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": file.content_type}
        )

        # Obtiene la URL pública que se guardará en la DB
        public_url = client.storage.from_(SUPABASE_BUCKET).get_public_url(file_path)

        return public_url
    except Exception as e:
        print(f"Error al subir a Supabase Storage: {e}")
        raise e