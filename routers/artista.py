from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException, File, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from datetime import datetime
from database import get_session
from models import Artista
from supabase_service import upload_to_bucket
import logging
import asyncio

router = APIRouter(prefix="/artistas", tags=["Artistas"])
logger = logging.getLogger(__name__)

# Templates
templates = Jinja2Templates(directory="templates")


# ========== ENDPOINTS HTML (NUEVOS) ==========

@router.get("/", response_class=HTMLResponse)
async def listar_artistas_html(
        request: Request,
        session: Session = Depends(get_session)
):
    """Lista artistas (HTML)"""
    try:
        await asyncio.sleep(0.01)
        artistas = session.exec(
            select(Artista).where(Artista.deleted_at == None)
        ).all()

        return templates.TemplateResponse("artistas/list.html", {
            "request": request,
            "artistas": artistas,
            "total": len(artistas)
        })

    except Exception as e:
        logger.error(f"Error listando artistas: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error al cargar artistas: {str(e)}"
        })


@router.get("/crear", response_class=HTMLResponse)
async def crear_artista_form(request: Request):
    """Formulario crear artista (HTML)"""
    return templates.TemplateResponse("artistas/create.html", {
        "request": request
    })


@router.post("/crear", response_class=RedirectResponse)
async def crear_artista_web(
        request: Request,
        nombre: str = Form(...),
        pais: str = Form(None),
        genero_principal: str = Form(None),
        popularidad: int = Form(50),
        imagen: UploadFile = File(None),
        session: Session = Depends(get_session)
):
    """Crear artista desde web"""
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
            imagen_url=url
        )

        await asyncio.sleep(0.01)
        session.add(artista)
        session.commit()

        return RedirectResponse("/artistas?success=Artista creado exitosamente", status_code=303)

    except HTTPException as e:
        return RedirectResponse(f"/artistas/crear?error={e.detail}", status_code=303)
    except Exception as e:
        session.rollback()
        logger.error(f"Error creando artista: {e}")
        return RedirectResponse(f"/artistas/crear?error=Error interno del servidor", status_code=303)


@router.get("/{id}", response_class=HTMLResponse)
async def detalle_artista_html(
        request: Request,
        id: int,
        session: Session = Depends(get_session)
):
    """Detalle artista (HTML)"""
    try:
        await asyncio.sleep(0.01)
        artista = session.get(Artista, id)
        if not artista or artista.deleted_at:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": f"Artista con ID {id} no encontrado"
            })

        return templates.TemplateResponse("artistas/detail.html", {
            "request": request,
            "artista": artista
        })

    except Exception as e:
        logger.error(f"Error obteniendo artista {id}: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error al obtener artista: {str(e)}"
        })


@router.get("/{id}/editar", response_class=HTMLResponse)
async def editar_artista_form(
        request: Request,
        id: int,
        session: Session = Depends(get_session)
):
    """Formulario editar artista (HTML)"""
    try:
        await asyncio.sleep(0.01)
        artista = session.get(Artista, id)
        if not artista or artista.deleted_at:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "Artista no encontrado"
            })

        return templates.TemplateResponse("artistas/edit.html", {
            "request": request,
            "artista": artista
        })

    except Exception as e:
        logger.error(f"Error obteniendo artista {id}: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })


@router.post("/{id}/editar", response_class=RedirectResponse)
async def procesar_editar_artista(
        id: int,
        nombre: str = Form(None),
        pais: str = Form(None),
        genero_principal: str = Form(None),
        popularidad: int = Form(None),
        imagen: UploadFile = File(None),
        session: Session = Depends(get_session)
):
    """Procesar edición de artista"""
    try:
        await asyncio.sleep(0.01)
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
            try:
                url = await upload_to_bucket(imagen)
                if url:
                    artista.imagen_url = url
            except Exception as img_error:
                logger.warning(f"Error actualizando imagen: {img_error}")

        await asyncio.sleep(0.01)
        session.add(artista)
        session.commit()

        return RedirectResponse(f"/artistas/{id}?success=Artista actualizado exitosamente", status_code=303)

    except HTTPException as e:
        return RedirectResponse(f"/artistas/{id}/editar?error={e.detail}", status_code=303)
    except Exception as e:
        session.rollback()
        logger.error(f"Error actualizando artista {id}: {e}")
        return RedirectResponse(f"/artistas/{id}/editar?error=Error interno del servidor", status_code=303)


@router.get("/{id}/eliminar", response_class=HTMLResponse)
async def confirmar_eliminar_artista(
        request: Request,
        id: int,
        session: Session = Depends(get_session)
):
    """Confirmar eliminación de artista (HTML)"""
    try:
        artista = session.get(Artista, id)
        if not artista:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "Artista no encontrado"
            })

        return templates.TemplateResponse("artistas/delete.html", {
            "request": request,
            "artista": artista
        })

    except Exception as e:
        logger.error(f"Error: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })


@router.post("/{id}", response_class=RedirectResponse)
async def eliminar_artista_web(
        id: int,
        session: Session = Depends(get_session)
):
    """Eliminar artista desde web"""
    try:
        artista = session.get(Artista, id)
        if not artista:
            return RedirectResponse("/artistas?error=Artista no encontrado", status_code=303)

        if artista.deleted_at:
            return RedirectResponse("/artistas?error=Artista ya estaba eliminado", status_code=303)

        artista.deleted_at = datetime.utcnow()
        session.add(artista)
        session.commit()

        return RedirectResponse("/artistas?success=Artista eliminado exitosamente", status_code=303)

    except Exception as e:
        session.rollback()
        logger.error(f"Error eliminando artista {id}: {e}")
        return RedirectResponse(f"/artistas?error=Error eliminando artista", status_code=303)


@router.get("/{id}/comparar", response_class=HTMLResponse)
async def comparar_artista_spotify_html(
        request: Request,
        id: int,
        session: Session = Depends(get_session)
):
    """Página para comparar artista con Spotify"""
    try:
        artista = session.get(Artista, id)
        if not artista:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "Artista no encontrado"
            })

        return templates.TemplateResponse("artistas/compare.html", {
            "request": request,
            "artista": artista
        })

    except Exception as e:
        logger.error(f"Error: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })


# ========== MANTENER ENDPOINTS ORIGINALES (JSON) ==========

@router.post("/", response_model=Artista)
async def crear_artista(
        nombre: str = Form(...),
        pais: str = Form(None),
        genero_principal: str = Form(None),
        popularidad: int = Form(50),
        imagen: UploadFile = File(None),
        session: Session = Depends(get_session)
):
    """API: Crear artista (JSON) - ORIGINAL"""
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
            imagen_url=url
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


@router.get("/api", response_model=list[Artista])
async def listar_artistas_api(session: Session = Depends(get_session)):
    """API: Listar artistas (JSON) - ORIGINAL"""
    try:
        await asyncio.sleep(0.01)
        return session.exec(
            select(Artista).where(Artista.deleted_at == None)
        ).all()
    except Exception as e:
        logger.error(f"Error listando artistas: {e}")
        return []


@router.get("/api/{id}", response_model=Artista)
async def obtener_artista_api(id: int, session: Session = Depends(get_session)):
    """API: Obtener artista (JSON) - ORIGINAL"""
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
    """API: Actualizar artista (JSON) - ORIGINAL"""
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
async def eliminar_artista_api(id: int, session: Session = Depends(get_session)):
    """API: Eliminar artista (JSON) - ORIGINAL"""
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
async def restaurar_artista_api(id: int, session: Session = Depends(get_session)):
    """API: Restaurar artista (JSON) - ORIGINAL"""
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
    """API: Actualización parcial (JSON) - ORIGINAL"""
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