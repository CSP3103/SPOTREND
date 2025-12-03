from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from database import get_session
from models import Cancion
from supabase_service import upload_to_bucket
import logging

router = APIRouter(prefix="/canciones", tags=["Canciones"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=Cancion)
async def crear_cancion(
        nombre: str = Form(...),
        artista: str = Form(...),
        tempo: float = Form(...),
        energy: float = Form(...),
        danceability: float = Form(0.0),
        valence: float = Form(0.0),
        acousticness: float = Form(0.0),
        imagen: UploadFile = None,
        session: Session = Depends(get_session)
):
    try:
        # Validaciones básicas
        if tempo < 0 or tempo > 300:
            raise HTTPException(400, "Tempo debe estar entre 0 y 300")
        if energy < 0 or energy > 1:
            raise HTTPException(400, "Energy debe estar entre 0 y 1")

        url = None
        if imagen:
            if not imagen.content_type.startswith('image/'):
                raise HTTPException(400, "Archivo debe ser una imagen")
            url = await upload_to_bucket(imagen)

        cancion = Cancion(
            nombre=nombre,
            artista=artista,
            tempo=tempo,
            energy=energy,
            danceability=danceability,
            valence=valence,
            acousticness=acousticness,
            imagen_url=url
        )

        session.add(cancion)
        session.commit()
        session.refresh(cancion)
        logger.info(f"Canción creada: {cancion.id}")
        return cancion

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error creando canción: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.get("/", response_model=list[Cancion])
def listar_canciones(session: Session = Depends(get_session)):
    try:
        canciones = session.exec(
            select(Cancion).where(Cancion.deleted_at == None)
        ).all()
        return canciones
    except Exception as e:
        logger.error(f"Error listando canciones: {e}")
        return []


@router.get("/{id}", response_model=Cancion)
def obtener_cancion(id: str, session: Session = Depends(get_session)):
    try:
        cancion = session.get(Cancion, id)
        if not cancion or cancion.deleted_at:
            raise HTTPException(404, "Canción no encontrada")
        return cancion
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo canción {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.put("/{id}", response_model=Cancion)
async def actualizar_cancion(
        id: str,
        nombre: str = Form(None),
        artista: str = Form(None),
        tempo: float = Form(None),
        energy: float = Form(None),
        danceability: float = Form(None),
        valence: float = Form(None),
        acousticness: float = Form(None),
        imagen: UploadFile = None,
        session: Session = Depends(get_session)
):
    try:
        cancion = session.get(Cancion, id)
        if not cancion or cancion.deleted_at:
            raise HTTPException(404, "Canción no encontrada")

        # Validaciones
        if tempo is not None and (tempo < 0 or tempo > 300):
            raise HTTPException(400, "Tempo debe estar entre 0 y 300")
        if energy is not None and (energy < 0 or energy > 1):
            raise HTTPException(400, "Energy debe estar entre 0 y 1")

        # Actualizar campos si se proporcionan
        if nombre is not None:
            cancion.nombre = nombre
        if artista is not None:
            cancion.artista = artista
        if tempo is not None:
            cancion.tempo = tempo
        if energy is not None:
            cancion.energy = energy
        if danceability is not None:
            cancion.danceability = danceability
        if valence is not None:
            cancion.valence = valence
        if acousticness is not None:
            cancion.acousticness = acousticness

        if imagen:
            if not imagen.content_type.startswith('image/'):
                raise HTTPException(400, "Archivo debe ser una imagen")
            url = await upload_to_bucket(imagen)
            cancion.imagen_url = url

        session.add(cancion)
        session.commit()
        session.refresh(cancion)
        logger.info(f"Canción actualizada: {id}")
        return cancion

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error actualizando canción {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.delete("/{id}")
def eliminar_cancion(id: str, session: Session = Depends(get_session)):
    try:
        cancion = session.get(Cancion, id)
        if not cancion:
            raise HTTPException(404, "Canción no encontrada")

        if cancion.deleted_at:
            return {"message": "Canción ya estaba eliminada", "ok": True}

        cancion.deleted_at = datetime.utcnow()
        session.add(cancion)
        session.commit()
        logger.info(f"Canción eliminada (soft): {id}")
        return {"message": "Canción eliminada exitosamente", "ok": True}

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error eliminando canción {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.get("/{id}/restaurar")
def restaurar_cancion(id: str, session: Session = Depends(get_session)):
    try:
        cancion = session.get(Cancion, id)
        if not cancion:
            raise HTTPException(404, "Canción no encontrada")

        if not cancion.deleted_at:
            return {"message": "Canción no estaba eliminada", "ok": True}

        cancion.deleted_at = None
        session.add(cancion)
        session.commit()
        logger.info(f"Canción restaurada: {id}")
        return {"message": "Canción restaurada exitosamente", "ok": True}

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error restaurando canción {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")