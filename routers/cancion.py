from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlmodel import Session, select
from database import get_session
from models import Cancion
from supabase_service import upload_to_bucket
from typing import Optional, List
import uuid

router = APIRouter(prefix="/cancion", tags=["Cancion (Prototipo)"])


# 1. CREATE (¡Con Subida de Imagen!)
@router.post("/", response_model=Cancion, status_code=status.HTTP_201_CREATED)
async def create_cancion_con_imagen(
        session: Session = Depends(get_session),
        # Datos de texto del formulario
        nombre: str = Form(...),
        artista: str = Form(...),
        tempo: float = Form(...),
        energy: float = Form(...),
        spotify_id: Optional[str] = Form(None),
        # El archivo de imagen (UploadFile)
        imagen: UploadFile = File(...)
):
    """
    Crea una nueva Cancion (Prototipo), sube la imagen al Bucket y guarda la URL.
    """

    if not imagen.filename:
        raise HTTPException(status_code=400, detail="La imagen de portada es obligatoria.")

    try:
        # 1. Subir la imagen al Bucket y obtener la URL
        imagen_url = await upload_to_bucket(imagen)

        # 2. Crear el objeto Cancion con todos los datos y la URL
        nueva_cancion = Cancion(
            nombre=nombre,
            artista=artista,
            tempo=tempo,
            energy=energy,
            spotify_id=spotify_id,
            imagen_url=imagen_url
        )

        # 3. Guardar en la DB
        session.add(nueva_cancion)
        session.commit()
        session.refresh(nueva_cancion)

        return nueva_cancion

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Fallo al procesar la canción o subir la imagen: {e}")


# 2. READ (Lista)
@router.get("/", response_model=List[Cancion])
def read_canciones(*, session: Session = Depends(get_session)):
    """Obtiene la lista completa de Canciones (Prototipos)."""
    canciones = session.exec(select(Cancion)).all()
    return canciones


# 3. READ (Detalle)
@router.get("/{cancion_id}", response_model=Cancion)
def read_cancion(*, session: Session = Depends(get_session), cancion_id: uuid.UUID):
    """Obtiene una Canción por su ID."""
    cancion = session.get(Cancion, cancion_id)
    if not cancion:
        raise HTTPException(status_code=404, detail="Canción no encontrada")
    return cancion


# 4. DELETE
@router.delete("/{cancion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cancion(*, session: Session = Depends(get_session), cancion_id: uuid.UUID):
    """Elimina una Canción de la base de datos."""
    cancion = session.get(Cancion, cancion_id)
    if not cancion:
        raise HTTPException(status_code=404, detail="Canción no encontrada")
    session.delete(cancion)
    session.commit()
    return {"ok": True}