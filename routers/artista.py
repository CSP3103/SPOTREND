from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from database import get_session
from models import Artista
from supabase_service import upload_to_bucket
import logging

router = APIRouter(prefix="/artistas", tags=["Artistas"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=Artista)
async def crear_artista(
        nombre: str = Form(...),
        pais: str = Form(None),
        genero_principal: str = Form(None),
        popularidad: int = Form(50),
        imagen: UploadFile = None,
        session: Session = Depends(get_session)
):
    try:
        if popularidad < 0 or popularidad > 100:
            raise HTTPException(400, "Popularidad debe estar entre 0 y 100")

        url = None
        if imagen:
            if not imagen.content_type.startswith('image/'):
                raise HTTPException(400, "Archivo debe ser una imagen")
            url = await upload_to_bucket(imagen)

        artista = Artista(
            nombre=nombre,
            pais=pais,
            genero_principal=genero_principal,
            popularidad=popularidad,
            imagen_url=url
        )

        session.add(artista)
        session.commit()
        session.refresh(artista)
        logger.info(f"Artista creado: {artista.id}")
        return artista

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error creando artista: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.get("/", response_model=list[Artista])
def listar_artistas(session: Session = Depends(get_session)):
    try:
        artistas = session.exec(
            select(Artista).where(Artista.deleted_at == None)
        ).all()
        return artistas
    except Exception as e:
        logger.error(f"Error listando artistas: {e}")
        return []


@router.get("/{id}", response_model=Artista)
def obtener_artista(id: int, session: Session = Depends(get_session)):
    try:
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
        imagen: UploadFile = None,
        session: Session = Depends(get_session)
):
    try:
        artista = session.get(Artista, id)
        if not artista or artista.deleted_at:
            raise HTTPException(404, "Artista no encontrado")

        if popularidad is not None and (popularidad < 0 or popularidad > 100):
            raise HTTPException(400, "Popularidad debe estar entre 0 y 100")

        if nombre is not None:
            artista.nombre = nombre
        if pais is not None:
            artista.pais = pais
        if genero_principal is not None:
            artista.genero_principal = genero_principal
        if popularidad is not None:
            artista.popularidad = popularidad

        if imagen:
            if not imagen.content_type.startswith('image/'):
                raise HTTPException(400, "Archivo debe ser una imagen")
            url = await upload_to_bucket(imagen)
            artista.imagen_url = url

        session.add(artista)
        session.commit()
        session.refresh(artista)
        logger.info(f"Artista actualizado: {id}")
        return artista

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error actualizando artista {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.delete("/{id}")
def eliminar_artista(id: int, session: Session = Depends(get_session)):
    try:
        artista = session.get(Artista, id)
        if not artista:
            raise HTTPException(404, "Artista no encontrado")

        if artista.deleted_at:
            return {"message": "Artista ya estaba eliminado", "ok": True}

        artista.deleted_at = datetime.utcnow()
        session.add(artista)
        session.commit()
        logger.info(f"Artista eliminado (soft): {id}")
        return {"message": "Artista eliminado exitosamente", "ok": True}

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error eliminando artista {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.get("/{id}/restaurar")
def restaurar_artista(id: int, session: Session = Depends(get_session)):
    try:
        artista = session.get(Artista, id)
        if not artista:
            raise HTTPException(404, "Artista no encontrado")

        if not artista.deleted_at:
            return {"message": "Artista no estaba eliminado", "ok": True}

        artista.deleted_at = None
        session.add(artista)
        session.commit()
        logger.info(f"Artista restaurado: {id}")
        return {"message": "Artista restaurado exitosamente", "ok": True}

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error restaurando artista {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")