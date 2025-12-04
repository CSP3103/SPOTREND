from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException, File
from sqlmodel import Session, select
from datetime import datetime
from database import get_session
from models import Artista
from supabase_service import upload_to_bucket
import logging
import asyncio

router = APIRouter(prefix="/artistas", tags=["Artistas"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=Artista)
async def crear_artista(
        nombre: str = Form(...),
        pais: str = Form(None),
        genero_principal: str = Form(None),
        popularidad: int = Form(50),
        imagen: UploadFile = File(None),
        session: Session = Depends(get_session)
):
    try:
        if popularidad < 0 or popularidad > 100:
            raise HTTPException(400, "Popularidad debe estar entre 0 y 100")

        url = None
        if imagen:
            try:
                if hasattr(imagen, 'content_type') and imagen.content_type:
                    if not imagen.content_type.startswith('image/'):
                        logger.warning(f"Archivo no es imagen: {imagen.content_type}")
                        url = None
                    else:
                        url = await upload_to_bucket(imagen)
                        if not url:
                            logger.warning("upload_to_bucket devolvió None")
                else:
                    url = await upload_to_bucket(imagen)
            except Exception as img_error:
                logger.warning(f"Error procesando imagen: {img_error}")
                url = None

        artista = Artista(
            nombre=nombre,
            pais=pais,
            genero_principal=genero_principal,
            popularidad=popularidad,
            imagen_url=url  # Puede ser NULL
        )

        await asyncio.sleep(0.01)
        session.add(artista)
        session.commit()
        session.refresh(artista)
        return artista

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error creando artista: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.get("/", response_model=list[Artista])
async def listar_artistas(session: Session = Depends(get_session)):
    try:
        await asyncio.sleep(0.01)
        return session.exec(
            select(Artista).where(Artista.deleted_at == None)
        ).all()
    except Exception as e:
        logger.error(f"Error listando artistas: {e}")
        return []


@router.get("/{id}", response_model=Artista)
async def obtener_artista(id: int, session: Session = Depends(get_session)):
    try:
        await asyncio.sleep(0.01)
        artista = session.get(Artista, id)
        if not artista or artista.deleted_at:
            raise HTTPException(404, "Artista no encontrado")
        return artista
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo artista {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.put("/{id}", response_model=Artista)
async def actualizar_artista(
        id: int,
        nombre: str = Form(None),
        pais: str = Form(None),
        genero_principal: str = Form(None),
        popularidad: int = Form(None),
        imagen: UploadFile = File(None),
        session: Session = Depends(get_session)
):
    try:
        await asyncio.sleep(0.01)
        artista = session.get(Artista, id)
        if not artista or artista.deleted_at:
            raise HTTPException(404, "Artista no encontrado")

        if popularidad is not None and (popularidad < 0 or popularidad > 100):
            raise HTTPException(400, "Popularidad inválida")

        if nombre is not None:
            artista.nombre = nombre
        if pais is not None:
            artista.pais = pais
        if genero_principal is not None:
            artista.genero_principal = genero_principal
        if popularidad is not None:
            artista.popularidad = popularidad

        if imagen:
            try:
                if hasattr(imagen, 'content_type') and imagen.content_type:
                    if not imagen.content_type.startswith('image/'):
                        logger.warning(f"Archivo no es imagen: {imagen.content_type}")
                    else:
                        url = await upload_to_bucket(imagen)
                        if url:
                            artista.imagen_url = url
                else:
                    url = await upload_to_bucket(imagen)
                    if url:
                        artista.imagen_url = url
            except Exception as img_error:
                logger.warning(f"Error actualizando imagen: {img_error}")

        await asyncio.sleep(0.01)
        session.add(artista)
        session.commit()
        session.refresh(artista)
        return artista

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error actualizando artista {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.delete("/{id}")
async def eliminar_artista(id: int, session: Session = Depends(get_session)):
    try:
        await asyncio.sleep(0.01)
        artista = session.get(Artista, id)
        if not artista:
            raise HTTPException(404, "Artista no encontrado")

        if artista.deleted_at:
            return {"message": "Artista ya estaba eliminado", "ok": True}

        artista.deleted_at = datetime.utcnow()
        await asyncio.sleep(0.01)
        session.add(artista)
        session.commit()
        return {"message": "Artista eliminado exitosamente", "ok": True}

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error eliminando artista {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.get("/{id}/restaurar")
async def restaurar_artista(id: int, session: Session = Depends(get_session)):
    try:
        await asyncio.sleep(0.01)
        artista = session.get(Artista, id)
        if not artista:
            raise HTTPException(404, "Artista no encontrado")

        if not artista.deleted_at:
            return {"message": "Artista no estaba eliminado", "ok": True}

        artista.deleted_at = None
        await asyncio.sleep(0.01)
        session.add(artista)
        session.commit()
        return {"message": "Artista restaurado exitosamente", "ok": True}

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error restaurando artista {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.patch("/{id}")
async def actualizar_parcial_artista(
        id: int,
        nombre: str = Form(None),
        pais: str = Form(None),
        genero_principal: str = Form(None),
        popularidad: int = Form(None),
        imagen: UploadFile = File(None),
        session: Session = Depends(get_session)
):
    try:
        await asyncio.sleep(0.01)
        artista = session.get(Artista, id)
        if not artista or artista.deleted_at:
            raise HTTPException(404, "Artista no encontrado")

        updates = {}
        if nombre is not None:
            artista.nombre = nombre
            updates["nombre"] = nombre
        if pais is not None:
            artista.pais = pais
            updates["pais"] = pais
        if genero_principal is not None:
            artista.genero_principal = genero_principal
            updates["genero_principal"] = genero_principal
        if popularidad is not None:
            if popularidad < 0 or popularidad > 100:
                raise HTTPException(400, "Popularidad inválida")
            artista.popularidad = popularidad
            updates["popularidad"] = popularidad

        if imagen:
            try:
                if hasattr(imagen, 'content_type') and imagen.content_type:
                    if not imagen.content_type.startswith('image/'):
                        raise HTTPException(400, "Archivo debe ser una imagen")

                url = await upload_to_bucket(imagen)
                if url:
                    artista.imagen_url = url
                    updates["imagen_url"] = url
            except Exception as img_error:
                logger.warning(f"Error actualizando imagen: {img_error}")

        if not updates:
            return {"message": "No se proporcionaron campos para actualizar", "artista": artista}

        await asyncio.sleep(0.01)
        session.add(artista)
        session.commit()
        session.refresh(artista)

        return {
            "message": "Artista actualizado parcialmente",
            "actualizados": updates,
            "artista": artista
        }

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error actualizando parcialmente artista {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")