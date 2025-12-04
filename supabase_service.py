from fastapi import UploadFile
from typing import Optional
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL_MAR")
SUPABASE_KEY = os.getenv("SUPABASE_KEY_MAR")


async def upload_to_bucket(file: UploadFile) -> Optional[str]:
    """Sube imagen o devuelve None si hay error/archivo vacío."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️  Credenciales Supabase no configuradas")
        return None

    try:
        # Verificar que sea un archivo válido
        if not file or not hasattr(file, 'filename') or not file.filename:
            print("⚠️  Archivo inválido o sin nombre")
            return None

        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Leer contenido
        content = await file.read()
        if len(content) == 0:
            print("⚠️  Archivo vacío")
            return None

        # Volver al inicio para futuras lecturas
        await file.seek(0)

        # Obtener extensión
        filename = file.filename.lower()
        if '.' in filename:
            ext = filename.split('.')[-1]
        else:
            ext = 'jpg'

        # Extensiones permitidas
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']
        if ext not in allowed_extensions:
            print(f"⚠️  Extensión no soportada: {ext}")
            return None

        unique_name = f"{uuid.uuid4()}.{ext}"
        file_path = f"portadas/{unique_name}"

        # Subir a Supabase
        client.storage.from_("portadas-spotrend").upload(
            path=file_path,
            file=content,
            file_options={"content-type": file.content_type or f"image/{ext}"}
        )

        public_url = client.storage.from_("portadas-spotrend").get_public_url(file_path)
        print(f"✅ Imagen subida exitosamente: {public_url}")
        return public_url

    except ImportError:
        print("⚠️  Supabase no instalado, usando modo desarrollo")
        return None
    except Exception as e:
        print(f"❌ Error subiendo imagen: {str(e)[:100]}")
        return None