from fastapi import UploadFile, HTTPException
from typing import Optional
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL_MAR")
SUPABASE_KEY = os.getenv("SUPABASE_KEY_MAR")


async def upload_to_bucket(file: UploadFile) -> str:
    """Sube imagen o devuelve placeholder."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return f"https://placehold.co/400x400?text={file.filename or 'Imagen'}"

    try:
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_KEY)

        ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        unique_name = f"{uuid.uuid4()}.{ext}"
        file_path = f"portadas/{unique_name}"

        content = await file.read()

        client.storage.from_("portadas-spotrend").upload(
            path=file_path,
            file=content,
            file_options={"content-type": file.content_type or "image/jpeg"}
        )

        public_url = client.storage.from_("portadas-spotrend").get_public_url(file_path)
        print(f"✅ Imagen subida: {public_url}")
        return public_url

    except Exception as e:
        print(f"⚠  Error subiendo imagen: {e}")
        return f"https://placehold.co/400x400?text=Error"