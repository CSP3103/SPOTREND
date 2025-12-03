# routers/cancion.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlmodel import Session, select
from typing import Optional, List
import uuid
from datetime import datetime  # Necesario para datetime.utcnow()
import models
from database import get_session

# from services.supabase_service import upload_to_bucket # Asumir servicio de subida de imagen

router = APIRouter(prefix="/cancion", tags=["Cancion (Prototipo)"])
Cancion = models.Cancion


# Esquema para la entrada del POST
class CancionCreate(SQLModel):
    nombre: str
    artista: str
    tempo: float
    energy: float
    spotify_id: Optional[str] = None


# 1. CREATE (POST) - Inserta la canción con métricas e imagen
@router.post("/", response_model=Cancion, status_code=status.HTTP_201_CREATED)
def create_cancion(
        data: CancionCreate = Depends(CancionCreate.as_form),  # Permite recibir JSON o Form-data
        imagen: UploadFile = File(None),
        session: Session = Depends(get_session)
):
    # Manejo de error HTTP 400 Bad Request
    if not data.tempo or not data.energy:
        raise HTTPException(status_code=400, detail="Faltan métricas de audio (tempo o energy).")

    try:
        cancion_in = Cancion.model_validate(data.model_dump())
        cancion_in.imagen_url = None  # Placeholder para el URL

        # Lógica para subir la imagen y obtener el URL (Ejemplo)
        # if imagen:
        #     file_url = upload_to_bucket(imagen.file, imagen.filename)
        #     cancion_in.imagen_url = file_url

        session.add(cancion_in)
        session.commit()
        session.refresh(cancion_in)
        return cancion_in
    except Exception as e:
        # Manejo de error 500 para fallos inesperados (ej. Base de Datos)
        raise HTTPException(status_code=500, detail=f"Error al crear la canción: {e}")


# 2. READ (Lista de ACTIVOS) - Filtrado por Soft Delete
@router.get("/", response_model=List[Cancion])
def read_canciones(*, session: Session = Depends(get_session)):
    """Obtiene la lista de Canciones (Prototipos) que NO están eliminadas (ACTIVOS)."""
    # Filtramos donde deleted_at es NULL
    canciones = session.exec(select(Cancion).where(Cancion.deleted_at == None)).all()
    return canciones


# 3. READ (Detalle) - Con manejo de error 404
@router.get("/{cancion_id}", response_model=Cancion)
def read_cancion(*, session: Session = Depends(get_session), cancion_id: uuid.UUID):
    """Obtiene el detalle de una Canción activa por ID."""
    cancion = session.get(Cancion, cancion_id)

    # Manejo de error HTTP 404: No encontrado o inactivo
    if not cancion or cancion.deleted_at:
        raise HTTPException(status_code=404, detail="Canción no encontrada o inactiva.")

    return cancion


# 4. DELETE (Soft Delete y errores 404/409)
@router.delete("/{cancion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cancion(*, session: Session = Depends(get_session), cancion_id: uuid.UUID):
    """Elimina LÓGICAMENTE una Canción (Soft Delete), asegurando trazabilidad."""
    cancion = session.get(Cancion, cancion_id)

    if not cancion:
        raise HTTPException(status_code=404, detail="Canción no encontrada.")

    if cancion.deleted_at:
        # Manejo de error HTTP 409 (Conflicto)
        raise HTTPException(status_code=409, detail="La canción ya fue eliminada lógicamente.")

    # Aplicar Soft Delete
    cancion.deleted_at = datetime.utcnow()

    session.add(cancion)
    session.commit()
    return


# === NUEVOS ENDPOINTS PARA TRAZABILIDAD Y RECUPERACIÓN ===

# 5. GET /history (Historial de Eliminaciones)
@router.get("/history", response_model=List[Cancion])
def read_deleted_canciones(*, session: Session = Depends(get_session)):
    """Obtiene la lista de Canciones que están ELIMINADAS LÓGICAMENTE (Historial de Trazabilidad)."""
    canciones_eliminadas = session.exec(select(Cancion).where(Cancion.deleted_at != None)).all()
    return canciones_eliminadas


# 6. POST /restore (Recuperar Registro)
@router.post("/restore/{cancion_id}", response_model=Cancion)
def restore_cancion(*, session: Session = Depends(get_session), cancion_id: uuid.UUID):
    """Recupera un registro eliminado lógicamente (Pone deleted_at a NULL)."""
    cancion = session.get(Cancion, cancion_id)

    if not cancion:
        raise HTTPException(status_code=404, detail="Canción no encontrada.")

    if cancion.deleted_at is None:
        # Manejo de error HTTP 409
        raise HTTPException(status_code=409, detail="La canción no está eliminada, no se puede restaurar.")

    # Restaurar: Poner deleted_at a NULL
    cancion.deleted_at = None

    session.add(cancion)
    session.commit()
    session.refresh(cancion)
    return cancion