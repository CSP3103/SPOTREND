from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from database import get_session
from models import Cancion, Artista, Benchmark
import logging
import asyncio

router = APIRouter(prefix="/eliminados", tags=["Eliminados"])
logger = logging.getLogger(__name__)

# Templates
templates = Jinja2Templates(directory="templates")


# ========== ENDPOINTS HTML ==========

@router.get("/", response_class=HTMLResponse)
async def pagina_eliminados(
        request: Request,
        session: Session = Depends(get_session)
):
    """Página principal de elementos eliminados"""
    try:
        canciones = session.exec(
            select(Cancion).where(Cancion.deleted_at != None)
        ).all()

        artistas = session.exec(
            select(Artista).where(Artista.deleted_at != None)
        ).all()

        benchmarks = session.exec(
            select(Benchmark).where(Benchmark.deleted_at != None)
        ).all()

        return templates.TemplateResponse("eliminados/index.html", {
            "request": request,
            "stats": {
                "canciones": len(canciones),
                "artistas": len(artistas),
                "benchmarks": len(benchmarks)
            },
            "total": len(canciones) + len(artistas) + len(benchmarks)
        })

    except Exception as e:
        logger.error(f"Error cargando página eliminados: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error cargando elementos eliminados: {str(e)}"
        })


@router.get("/canciones", response_class=HTMLResponse)
async def listar_canciones_eliminadas_html(
        request: Request,
        session: Session = Depends(get_session)
):
    """Canciones eliminadas (HTML)"""
    try:
        await asyncio.sleep(0.01)
        canciones = session.exec(
            select(Cancion).where(Cancion.deleted_at != None)
        ).all()

        return templates.TemplateResponse("eliminados/canciones.html", {
            "request": request,
            "eliminados": {
                "total": len(canciones),
                "canciones": canciones
            }
        })

    except Exception as e:
        logger.error(f"Error listando canciones eliminadas HTML: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error cargando canciones eliminadas: {str(e)}"
        })


@router.get("/artistas", response_class=HTMLResponse)
async def listar_artistas_eliminados_html(
        request: Request,
        session: Session = Depends(get_session)
):
    """Artistas eliminados (HTML)"""
    try:
        await asyncio.sleep(0.01)
        artistas = session.exec(
            select(Artista).where(Artista.deleted_at != None)
        ).all()

        return templates.TemplateResponse("eliminados/artistas.html", {
            "request": request,
            "eliminados": {
                "total": len(artistas),
                "artistas": artistas
            }
        })

    except Exception as e:
        logger.error(f"Error listando artistas eliminados HTML: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error cargando artistas eliminados: {str(e)}"
        })


@router.get("/benchmarks", response_class=HTMLResponse)
async def listar_benchmarks_eliminados_html(
        request: Request,
        session: Session = Depends(get_session)
):
    """Benchmarks eliminados (HTML)"""
    try:
        await asyncio.sleep(0.01)
        benchmarks = session.exec(
            select(Benchmark).where(Benchmark.deleted_at != None)
        ).all()

        return templates.TemplateResponse("eliminados/benchmarks.html", {
            "request": request,
            "eliminados": {
                "total": len(benchmarks),
                "benchmarks": benchmarks
            }
        })

    except Exception as e:
        logger.error(f"Error listando benchmarks eliminados HTML: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error cargando benchmarks eliminados: {str(e)}"
        })


@router.get("/restaurar-todos", response_class=HTMLResponse)
async def restaurar_todos_form(
        request: Request,
        session: Session = Depends(get_session)
):
    """Formulario para restaurar todos los eliminados"""
    try:
        canciones = session.exec(
            select(Cancion).where(Cancion.deleted_at != None)
        ).all()

        artistas = session.exec(
            select(Artista).where(Artista.deleted_at != None)
        ).all()

        benchmarks = session.exec(
            select(Benchmark).where(Benchmark.deleted_at != None)
        ).all()

        return templates.TemplateResponse("eliminados/restaurar.html", {
            "request": request,
            "stats": {
                "canciones": len(canciones),
                "artistas": len(artistas),
                "benchmarks": len(benchmarks)
            }
        })

    except Exception as e:
        logger.error(f"Error cargando formulario restaurar: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error cargando formulario: {str(e)}"
        })


# ========== ENDPOINTS PARA RESTAURAR ==========

@router.post("/restaurar-todos", response_class=RedirectResponse)
async def restaurar_todos_eliminados_web(
        session: Session = Depends(get_session)
):
    """Restaurar todos los elementos eliminados desde web"""
    try:
        # Restaurar canciones
        canciones = session.exec(
            select(Cancion).where(Cancion.deleted_at != None)
        ).all()
        for c in canciones:
            c.deleted_at = None

        # Restaurar artistas
        artistas = session.exec(
            select(Artista).where(Artista.deleted_at != None)
        ).all()
        for a in artistas:
            a.deleted_at = None

        # Restaurar benchmarks
        benchmarks = session.exec(
            select(Benchmark).where(Benchmark.deleted_at != None)
        ).all()
        for b in benchmarks:
            b.deleted_at = None

        session.commit()

        # Determinar dónde redirigir basado en los elementos restaurados
        if canciones and not artistas and not benchmarks:
            return RedirectResponse("/canciones?success=Todas las canciones restauradas exitosamente", status_code=303)
        elif artistas and not canciones and not benchmarks:
            return RedirectResponse("/artistas?success=Todos los artistas restaurados exitosamente", status_code=303)
        elif benchmarks and not canciones and not artistas:
            return RedirectResponse("/benchmarks?success=Todos los benchmarks restaurados exitosamente",
                                    status_code=303)
        else:
            return RedirectResponse("/dashboard?success=Todos los elementos restaurados exitosamente", status_code=303)

    except Exception as e:
        session.rollback()
        logger.error(f"Error restaurando todos: {e}")
        return RedirectResponse("/eliminados?error=Error restaurando elementos", status_code=303)


@router.post("/canciones/restaurar-todas", response_class=RedirectResponse)
async def restaurar_todas_canciones_web(
        session: Session = Depends(get_session)
):
    """Restaurar todas las canciones eliminadas"""
    try:
        canciones = session.exec(
            select(Cancion).where(Cancion.deleted_at != None)
        ).all()

        for c in canciones:
            c.deleted_at = None

        session.commit()

        return RedirectResponse("/canciones?success=Todas las canciones restauradas exitosamente", status_code=303)

    except Exception as e:
        session.rollback()
        logger.error(f"Error restaurando canciones: {e}")
        return RedirectResponse("/eliminados/canciones?error=Error restaurando canciones", status_code=303)


@router.post("/artistas/restaurar-todos", response_class=RedirectResponse)
async def restaurar_todos_artistas_web(
        session: Session = Depends(get_session)
):
    """Restaurar todos los artistas eliminados"""
    try:
        artistas = session.exec(
            select(Artista).where(Artista.deleted_at != None)
        ).all()

        for a in artistas:
            a.deleted_at = None

        session.commit()

        return RedirectResponse("/artistas?success=Todos los artistas restaurados exitosamente", status_code=303)

    except Exception as e:
        session.rollback()
        logger.error(f"Error restaurando artistas: {e}")
        return RedirectResponse("/eliminados/artistas?error=Error restaurando artistas", status_code=303)


@router.post("/benchmarks/restaurar-todos", response_class=RedirectResponse)
async def restaurar_todos_benchmarks_web(
        session: Session = Depends(get_session)
):
    """Restaurar todos los benchmarks eliminados"""
    try:
        benchmarks = session.exec(
            select(Benchmark).where(Benchmark.deleted_at != None)
        ).all()

        for b in benchmarks:
            b.deleted_at = None

        session.commit()

        return RedirectResponse("/benchmarks?success=Todos los benchmarks restaurados exitosamente", status_code=303)

    except Exception as e:
        session.rollback()
        logger.error(f"Error restaurando benchmarks: {e}")
        return RedirectResponse("/eliminados/benchmarks?error=Error restaurando benchmarks", status_code=303)


# ========== ENDPOINTS ORIGINALES (JSON) ==========

@router.get("/api/canciones")
async def listar_canciones_eliminadas(session: Session = Depends(get_session)):
    """API: Listar canciones eliminadas (JSON) - ORIGINAL"""
    try:
        await asyncio.sleep(0.01)
        canciones = session.exec(
            select(Cancion).where(Cancion.deleted_at != None)
        ).all()
        return {
            "total": len(canciones),
            "canciones": canciones
        }
    except Exception as e:
        logger.error(f"Error listando canciones eliminadas: {e}")
        return {"total": 0, "canciones": []}


@router.get("/api/artistas")
async def listar_artistas_eliminados(session: Session = Depends(get_session)):
    """API: Listar artistas eliminados (JSON) - ORIGINAL"""
    try:
        await asyncio.sleep(0.01)
        artistas = session.exec(
            select(Artista).where(Artista.deleted_at != None)
        ).all()
        return {
            "total": len(artistas),
            "artistas": artistas
        }
    except Exception as e:
        logger.error(f"Error listando artistas eliminados: {e}")
        return {"total": 0, "artistas": []}


@router.get("/api/benchmarks")
async def listar_benchmarks_eliminados(session: Session = Depends(get_session)):
    """API: Listar benchmarks eliminados (JSON) - ORIGINAL"""
    try:
        await asyncio.sleep(0.01)
        benchmarks = session.exec(
            select(Benchmark).where(Benchmark.deleted_at != None)
        ).all()
        return {
            "total": len(benchmarks),
            "benchmarks": benchmarks
        }
    except Exception as e:
        logger.error(f"Error listando benchmarks eliminados: {e}")
        return {"total": 0, "benchmarks": []}


@router.post("/api/restaurar-todos")
async def restaurar_todos_eliminados(session: Session = Depends(get_session)):
    """API: Restaurar todos los elementos (JSON) - ORIGINAL"""
    try:
        await asyncio.sleep(0.01)

        # Restaurar canciones
        canciones = session.exec(
            select(Cancion).where(Cancion.deleted_at != None)
        ).all()
        for c in canciones:
            c.deleted_at = None

        # Restaurar artistas
        await asyncio.sleep(0.01)
        artistas = session.exec(
            select(Artista).where(Artista.deleted_at != None)
        ).all()
        for a in artistas:
            a.deleted_at = None

        # Restaurar benchmarks
        await asyncio.sleep(0.01)
        benchmarks = session.exec(
            select(Benchmark).where(Benchmark.deleted_at != None)
        ).all()
        for b in benchmarks:
            b.deleted_at = None

        await asyncio.sleep(0.01)
        session.commit()

        return {
            "message": "Todos los elementos restaurados",
            "canciones_restauradas": len(canciones),
            "artistas_restaurados": len(artistas),
            "benchmarks_restaurados": len(benchmarks)
        }
    except Exception as e:
        session.rollback()
        logger.error(f"Error restaurando todos: {e}")
        raise HTTPException(500, "Error interno del servidor")