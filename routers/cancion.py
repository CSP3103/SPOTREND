from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException, File
from sqlmodel import Session, select
from datetime import datetime
from database import get_session
from models import Cancion
from supabase_service import upload_to_bucket
import logging
import asyncio

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
        imagen: UploadFile = File(None),
        session: Session = Depends(get_session)
):
    try:
        if tempo < 0 or tempo > 300:
            raise HTTPException(400, "Tempo debe estar entre 0 y 300")
        if energy < 0 or energy > 1:
            raise HTTPException(400, "Energy debe estar entre 0 y 1")

        url = None
        if imagen:
            try:
                # Verificar que sea una imagen válida
                if hasattr(imagen, 'content_type') and imagen.content_type:
                    if not imagen.content_type.startswith('image/'):
                        logger.warning(f"Archivo no es imagen: {imagen.content_type}")
                        url = None
                    else:
                        url = await upload_to_bucket(imagen)
                        if not url:
                            logger.warning("upload_to_bucket devolvió None")
                else:
                    # Si no tiene content_type, intentar subir igual
                    url = await upload_to_bucket(imagen)
            except Exception as img_error:
                logger.warning(f"Error procesando imagen: {img_error}")
                url = None

        cancion = Cancion(
            nombre=nombre,
            artista=artista,
            tempo=tempo,
            energy=energy,
            danceability=danceability,
            valence=valence,
            acousticness=acousticness,
            imagen_url=url  # Puede ser NULL
        )

        await asyncio.sleep(0.01)
        session.add(cancion)
        session.commit()
        session.refresh(cancion)
        return cancion

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error creando canción: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.get("/", response_model=list[Cancion])
async def listar_canciones(session: Session = Depends(get_session)):
    try:
        await asyncio.sleep(0.01)
        return session.exec(
            select(Cancion).where(Cancion.deleted_at == None)
        ).all()
    except Exception as e:
        logger.error(f"Error listando canciones: {e}")
        return []


@router.get("/{id}", response_model=Cancion)
async def obtener_cancion(id: str, session: Session = Depends(get_session)):
    try:
        await asyncio.sleep(0.01)
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
        imagen: UploadFile = File(None),
        session: Session = Depends(get_session)
):
    try:
        await asyncio.sleep(0.01)
        cancion = session.get(Cancion, id)
        if not cancion or cancion.deleted_at:
            raise HTTPException(404, "Canción no encontrada")

        if tempo is not None and (tempo < 0 or tempo > 300):
            raise HTTPException(400, "Tempo inválido")
        if energy is not None and (energy < 0 or energy > 1):
            raise HTTPException(400, "Energy inválido")

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
            try:
                if hasattr(imagen, 'content_type') and imagen.content_type:
                    if not imagen.content_type.startswith('image/'):
                        logger.warning(f"Archivo no es imagen: {imagen.content_type}")
                    else:
                        url = await upload_to_bucket(imagen)
                        if url:
                            cancion.imagen_url = url
                else:
                    url = await upload_to_bucket(imagen)
                    if url:
                        cancion.imagen_url = url
            except Exception as img_error:
                logger.warning(f"Error actualizando imagen: {img_error}")

        await asyncio.sleep(0.01)
        session.add(cancion)
        session.commit()
        session.refresh(cancion)
        return cancion

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error actualizando canción {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.delete("/{id}")
async def eliminar_cancion(id: str, session: Session = Depends(get_session)):
    try:
        await asyncio.sleep(0.01)
        cancion = session.get(Cancion, id)
        if not cancion:
            raise HTTPException(404, "Canción no encontrada")

        if cancion.deleted_at:
            return {"message": "Canción ya estaba eliminada", "ok": True}

        cancion.deleted_at = datetime.utcnow()
        await asyncio.sleep(0.01)
        session.add(cancion)
        session.commit()
        return {"message": "Canción eliminada exitosamente", "ok": True}

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error eliminando canción {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.get("/{id}/restaurar")
async def restaurar_cancion(id: str, session: Session = Depends(get_session)):
    try:
        await asyncio.sleep(0.01)
        cancion = session.get(Cancion, id)
        if not cancion:
            raise HTTPException(404, "Canción no encontrada")

        if not cancion.deleted_at:
            return {"message": "Canción no estaba eliminada", "ok": True}

        cancion.deleted_at = None
        await asyncio.sleep(0.01)
        session.add(cancion)
        session.commit()
        return {"message": "Canción restaurada exitosamente", "ok": True}

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error restaurando canción {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.patch("/{id}")
async def actualizar_parcial_cancion(
        id: str,
        nombre: str = Form(None),
        artista: str = Form(None),
        tempo: float = Form(None),
        energy: float = Form(None),
        danceability: float = Form(None),
        valence: float = Form(None),
        acousticness: float = Form(None),
        imagen: UploadFile = File(None),
        session: Session = Depends(get_session)
):
    try:
        await asyncio.sleep(0.01)
        cancion = session.get(Cancion, id)
        if not cancion or cancion.deleted_at:
            raise HTTPException(404, "Canción no encontrada")

        updates = {}
        if nombre is not None:
            cancion.nombre = nombre
            updates["nombre"] = nombre
        if artista is not None:
            cancion.artista = artista
            updates["artista"] = artista
        if tempo is not None:
            if tempo < 0 or tempo > 300:
                raise HTTPException(400, "Tempo inválido")
            cancion.tempo = tempo
            updates["tempo"] = tempo
        if energy is not None:
            if energy < 0 or energy > 1:
                raise HTTPException(400, "Energy inválido")
            cancion.energy = energy
            updates["energy"] = energy
        if danceability is not None:
            cancion.danceability = danceability
            updates["danceability"] = danceability
        if valence is not None:
            cancion.valence = valence
            updates["valence"] = valence
        if acousticness is not None:
            cancion.acousticness = acousticness
            updates["acousticness"] = acousticness

        if imagen:
            try:
                if hasattr(imagen, 'content_type') and imagen.content_type:
                    if not imagen.content_type.startswith('image/'):
                        raise HTTPException(400, "Archivo debe ser una imagen")

                url = await upload_to_bucket(imagen)
                if url:
                    cancion.imagen_url = url
                    updates["imagen_url"] = url
            except Exception as img_error:
                logger.warning(f"Error actualizando imagen: {img_error}")

        if not updates:
            return {"message": "No se proporcionaron campos para actualizar", "cancion": cancion}

        await asyncio.sleep(0.01)
        session.add(cancion)
        session.commit()
        session.refresh(cancion)

        return {
            "message": "Canción actualizada parcialmente",
            "actualizados": updates,
            "cancion": cancion
        }

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error actualizando parcialmente canción {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")