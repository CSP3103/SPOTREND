from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException, File, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from datetime import datetime
from database import get_session
from models import Cancion
from supabase_service import upload_to_bucket
import logging
import asyncio

router = APIRouter(prefix="/canciones", tags=["Canciones"])
logger = logging.getLogger(__name__)

# Templates
templates = Jinja2Templates(directory="templates")


# ========== ENDPOINTS HTML (NUEVOS) ==========

@router.get("/", response_class=HTMLResponse)
async def listar_canciones_html(
        request: Request,
        session: Session = Depends(get_session)
):
    """Lista canciones (HTML)"""
    try:
        await asyncio.sleep(0.01)
        canciones = session.exec(
            select(Cancion).where(Cancion.deleted_at == None)
        ).all()

        return templates.TemplateResponse("canciones/list.html", {
            "request": request,
            "canciones": canciones,
            "total": len(canciones)
        })

    except Exception as e:
        logger.error(f"Error listando canciones: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error al cargar canciones: {str(e)}"
        })


@router.get("/crear", response_class=HTMLResponse)
async def crear_cancion_form(request: Request):
    """Formulario crear canción (HTML)"""
    return templates.TemplateResponse("canciones/create.html", {
        "request": request
    })


@router.post("/crear", response_class=RedirectResponse)
async def crear_cancion_web(
        request: Request,
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
    """Crear canción desde web"""
    try:
        if tempo < 0 or tempo > 300:
            raise HTTPException(400, "Tempo debe estar entre 0 y 300")
        if energy < 0 or energy > 1:
            raise HTTPException(400, "Energy debe estar entre 0 y 1")

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

        await asyncio.sleep(0.01)
        session.add(cancion)
        session.commit()

        return RedirectResponse("/canciones?success=Canción creada exitosamente", status_code=303)

    except HTTPException as e:
        return RedirectResponse(f"/canciones/crear?error={e.detail}", status_code=303)
    except Exception as e:
        session.rollback()
        logger.error(f"Error creando canción: {e}")
        return RedirectResponse(f"/canciones/crear?error=Error interno del servidor", status_code=303)


@router.get("/{id}", response_class=HTMLResponse)
async def detalle_cancion_html(
        request: Request,
        id: str,
        session: Session = Depends(get_session)
):
    """Detalle canción (HTML)"""
    try:
        await asyncio.sleep(0.01)
        cancion = session.get(Cancion, id)
        if not cancion or cancion.deleted_at:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": f"Canción con ID {id} no encontrada"
            })

        return templates.TemplateResponse("canciones/detail.html", {
            "request": request,
            "cancion": cancion
        })

    except Exception as e:
        logger.error(f"Error obteniendo canción {id}: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error al obtener canción: {str(e)}"
        })


@router.get("/{id}/editar", response_class=HTMLResponse)
async def editar_cancion_form(
        request: Request,
        id: str,
        session: Session = Depends(get_session)
):
    """Formulario editar canción (HTML)"""
    try:
        await asyncio.sleep(0.01)
        cancion = session.get(Cancion, id)
        if not cancion or cancion.deleted_at:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "Canción no encontrada"
            })

        return templates.TemplateResponse("canciones/edit.html", {
            "request": request,
            "cancion": cancion
        })

    except Exception as e:
        logger.error(f"Error obteniendo canción {id}: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })


@router.post("/{id}/editar", response_class=RedirectResponse)
async def procesar_editar_cancion(
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
    """Procesar edición de canción"""
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
                url = await upload_to_bucket(imagen)
                if url:
                    cancion.imagen_url = url
            except Exception as img_error:
                logger.warning(f"Error actualizando imagen: {img_error}")

        await asyncio.sleep(0.01)
        session.add(cancion)
        session.commit()

        return RedirectResponse(f"/canciones/{id}?success=Canción actualizada exitosamente", status_code=303)

    except HTTPException as e:
        return RedirectResponse(f"/canciones/{id}/editar?error={e.detail}", status_code=303)
    except Exception as e:
        session.rollback()
        logger.error(f"Error actualizando canción {id}: {e}")
        return RedirectResponse(f"/canciones/{id}/editar?error=Error interno del servidor", status_code=303)


# ========== ENDPOINTS ORIGINALES (JSON) - MANTENER TODOS ==========

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
    """API: Crear canción (JSON) - ORIGINAL"""
    try:
        if tempo < 0 or tempo > 300:
            raise HTTPException(400, "Tempo debe estar entre 0 y 300")
        if energy < 0 or energy > 1:
            raise HTTPException(400, "Energy debe estar entre 0 y 1")

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


@router.get("/api", response_model=list[Cancion])
async def listar_canciones(session: Session = Depends(get_session)):
    """API: Listar canciones (JSON) - ORIGINAL"""
    try:
        await asyncio.sleep(0.01)
        return session.exec(
            select(Cancion).where(Cancion.deleted_at == None)
        ).all()
    except Exception as e:
        logger.error(f"Error listando canciones: {e}")
        return []


@router.get("/api/{id}", response_model=Cancion)
async def obtener_cancion(id: str, session: Session = Depends(get_session)):
    """API: Obtener canción (JSON) - ORIGINAL"""
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
    """API: Actualizar canción (JSON) - ORIGINAL"""
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
    """API: Eliminar canción (JSON) - ORIGINAL"""
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
            # Aunque no haga nada, igual redirige
            return RedirectResponse("/eliminados/canciones", status_code=303)

        cancion.deleted_at = None
        session.add(cancion)
        session.commit()

        # ✔ Redirección deseada
        return RedirectResponse("/eliminados/canciones", status_code=303)

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
    """API: Actualización parcial (JSON) - ORIGINAL"""
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


@router.get("/{id}/eliminar", response_class=HTMLResponse)
async def confirmar_eliminar_cancion(
        request: Request,
        id: str,
        session: Session = Depends(get_session)
):
    """Confirmar eliminación de canción (HTML)"""
    try:
        cancion = session.get(Cancion, id)
        if not cancion:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "Canción no encontrada"
            })

        return templates.TemplateResponse("canciones/delete.html", {
            "request": request,
            "cancion": cancion
        })

    except Exception as e:
        logger.error(f"Error: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })


@router.post("/{id}", response_class=RedirectResponse)
async def eliminar_cancion_web(
        id: str,
        session: Session = Depends(get_session)
):
    """Eliminar canción desde web"""
    try:
        cancion = session.get(Cancion, id)
        if not cancion:
            return RedirectResponse("/canciones?error=Canción no encontrada", status_code=303)

        if cancion.deleted_at:
            return RedirectResponse("/canciones?error=Canción ya estaba eliminada", status_code=303)

        cancion.deleted_at = datetime.utcnow()
        session.add(cancion)
        session.commit()

        return RedirectResponse("/canciones?success=Canción eliminada exitosamente", status_code=303)

    except Exception as e:
        session.rollback()
        logger.error(f"Error eliminando canción {id}: {e}")
        return RedirectResponse(f"/canciones?error=Error eliminando canción", status_code=303)
