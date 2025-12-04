from fastapi import APIRouter, Depends, HTTPException, Request, Form, File, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from datetime import datetime
from database import get_session
from models import Benchmark
import logging
import asyncio

router = APIRouter(prefix="/benchmarks", tags=["Benchmarks"])
logger = logging.getLogger(__name__)

# Templates
templates = Jinja2Templates(directory="templates")

# ========== ENDPOINTS HTML ==========

@router.get("/", response_class=HTMLResponse)
async def listar_benchmarks_html(
    request: Request,
    session: Session = Depends(get_session)
):
    """Lista benchmarks (HTML)"""
    try:
        await asyncio.sleep(0.01)
        benchmarks = session.exec(
            select(Benchmark).where(Benchmark.deleted_at == None)
        ).all()

        return templates.TemplateResponse("benchmarks/list.html", {
            "request": request,
            "benchmarks": benchmarks,
            "total": len(benchmarks)
        })

    except Exception as e:
        logger.error(f"Error listando benchmarks: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error al cargar benchmarks: {str(e)}"
        })


@router.get("/crear", response_class=HTMLResponse)
async def crear_benchmark_form(request: Request):
    """Formulario crear benchmark (HTML)"""
    return templates.TemplateResponse("benchmarks/create.html", {
        "request": request
    })


@router.post("/crear", response_class=RedirectResponse)
async def crear_benchmark_web(
    request: Request,
    pais: str = Form(...),
    genero: str = Form(...),
    tempo_promedio: float = Form(...),
    energy_promedio: float = Form(...),
    danceability_promedio: float = Form(0.0),
    valence_promedio: float = Form(0.0),
    session: Session = Depends(get_session)
):
    """Crear benchmark desde web"""
    try:
        if tempo_promedio < 0 or tempo_promedio > 300:
            raise HTTPException(400, "Tempo promedio inválido")
        if energy_promedio < 0 or energy_promedio > 1:
            raise HTTPException(400, "Energy promedio inválido")

        benchmark = Benchmark(
            pais=pais,
            genero=genero,
            tempo_promedio=tempo_promedio,
            energy_promedio=energy_promedio,
            danceability_promedio=danceability_promedio,
            valence_promedio=valence_promedio
        )

        await asyncio.sleep(0.01)
        session.add(benchmark)
        session.commit()

        return RedirectResponse("/benchmarks?success=Benchmark creado exitosamente", status_code=303)

    except HTTPException as e:
        return RedirectResponse(f"/benchmarks/crear?error={e.detail}", status_code=303)
    except Exception as e:
        session.rollback()
        logger.error(f"Error creando benchmark: {e}")
        return RedirectResponse(f"/benchmarks/crear?error=Error interno del servidor", status_code=303)


@router.get("/{id}", response_class=HTMLResponse)
async def detalle_benchmark_html(
    request: Request,
    id: int,
    session: Session = Depends(get_session)
):
    """Detalle benchmark (HTML)"""
    try:
        await asyncio.sleep(0.01)
        benchmark = session.get(Benchmark, id)
        if not benchmark or benchmark.deleted_at:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": f"Benchmark con ID {id} no encontrado"
            })

        return templates.TemplateResponse("benchmarks/detail.html", {
            "request": request,
            "benchmark": benchmark
        })

    except Exception as e:
        logger.error(f"Error obteniendo benchmark {id}: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error al obtener benchmark: {str(e)}"
        })


@router.get("/{id}/editar", response_class=HTMLResponse)
async def editar_benchmark_form(
    request: Request,
    id: int,
    session: Session = Depends(get_session)
):
    """Formulario editar benchmark (HTML)"""
    try:
        await asyncio.sleep(0.01)
        benchmark = session.get(Benchmark, id)
        if not benchmark or benchmark.deleted_at:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "Benchmark no encontrado"
            })

        return templates.TemplateResponse("benchmarks/edit.html", {
            "request": request,
            "benchmark": benchmark
        })

    except Exception as e:
        logger.error(f"Error obteniendo benchmark {id}: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })


@router.post("/{id}/editar", response_class=RedirectResponse)
async def procesar_editar_benchmark(
    id: int,
    pais: str = Form(None),
    genero: str = Form(None),
    tempo_promedio: float = Form(None),
    energy_promedio: float = Form(None),
    danceability_promedio: float = Form(None),
    valence_promedio: float = Form(None),
    session: Session = Depends(get_session)
):
    """Procesar edición de benchmark"""
    try:
        await asyncio.sleep(0.01)
        benchmark = session.get(Benchmark, id)
        if not benchmark or benchmark.deleted_at:
            raise HTTPException(404, "Benchmark no encontrado")

        if tempo_promedio is not None and (tempo_promedio < 0 or tempo_promedio > 300):
            raise HTTPException(400, "Tempo promedio inválido")
        if energy_promedio is not None and (energy_promedio < 0 or energy_promedio > 1):
            raise HTTPException(400, "Energy promedio inválido")

        if pais is not None:
            benchmark.pais = pais
        if genero is not None:
            benchmark.genero = genero
        if tempo_promedio is not None:
            benchmark.tempo_promedio = tempo_promedio
        if energy_promedio is not None:
            benchmark.energy_promedio = energy_promedio
        if danceability_promedio is not None:
            benchmark.danceability_promedio = danceability_promedio
        if valence_promedio is not None:
            benchmark.valence_promedio = valence_promedio

        await asyncio.sleep(0.01)
        session.add(benchmark)
        session.commit()

        return RedirectResponse(f"/benchmarks/{id}?success=Benchmark actualizado exitosamente", status_code=303)

    except HTTPException as e:
        return RedirectResponse(f"/benchmarks/{id}/editar?error={e.detail}", status_code=303)
    except Exception as e:
        session.rollback()
        logger.error(f"Error actualizando benchmark {id}: {e}")
        return RedirectResponse(f"/benchmarks/{id}/editar?error=Error interno del servidor", status_code=303)


@router.get("/{id}/eliminar", response_class=HTMLResponse)
async def confirmar_eliminar_benchmark(
    request: Request,
    id: int,
    session: Session = Depends(get_session)
):
    """Confirmar eliminación de benchmark (HTML)"""
    try:
        benchmark = session.get(Benchmark, id)
        if not benchmark:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "Benchmark no encontrado"
            })

        return templates.TemplateResponse("benchmarks/delete.html", {
            "request": request,
            "benchmark": benchmark
        })

    except Exception as e:
        logger.error(f"Error: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })


@router.post("/{id}", response_class=RedirectResponse)
async def eliminar_benchmark_web(
    id: int,
    session: Session = Depends(get_session)
):
    """Eliminar benchmark desde web"""
    try:
        benchmark = session.get(Benchmark, id)
        if not benchmark:
            return RedirectResponse("/benchmarks?error=Benchmark no encontrado", status_code=303)

        if benchmark.deleted_at:
            return RedirectResponse("/benchmarks?error=Benchmark ya estaba eliminado", status_code=303)

        benchmark.deleted_at = datetime.utcnow()
        session.add(benchmark)
        session.commit()

        return RedirectResponse("/benchmarks?success=Benchmark eliminado exitosamente", status_code=303)

    except Exception as e:
        session.rollback()
        logger.error(f"Error eliminando benchmark {id}: {e}")
        return RedirectResponse(f"/benchmarks?error=Error eliminando benchmark", status_code=303)


@router.get("/{id}/analizar", response_class=HTMLResponse)
async def analizar_benchmark_html(
    request: Request,
    id: int,
    session: Session = Depends(get_session)
):
    """Página para analizar canciones con este benchmark"""
    try:
        benchmark = session.get(Benchmark, id)
        if not benchmark:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "Benchmark no encontrado"
            })

        return templates.TemplateResponse("benchmarks/analizar.html", {
            "request": request,
            "benchmark": benchmark
        })

    except Exception as e:
        logger.error(f"Error: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })


# ========== ENDPOINTS ORIGINALES (JSON) ==========

@router.post("/", response_model=Benchmark)
async def crear_benchmark(
    pais: str = Form(...),
    genero: str = Form(...),
    tempo_promedio: float = Form(...),
    energy_promedio: float = Form(...),
    danceability_promedio: float = Form(0.0),
    valence_promedio: float = Form(0.0),
    session: Session = Depends(get_session)
):
    """API: Crear benchmark (JSON) - ORIGINAL"""
    try:
        if tempo_promedio < 0 or tempo_promedio > 300:
            raise HTTPException(400, "Tempo promedio inválido")
        if energy_promedio < 0 or energy_promedio > 1:
            raise HTTPException(400, "Energy promedio inválido")

        benchmark = Benchmark(
            pais=pais,
            genero=genero,
            tempo_promedio=tempo_promedio,
            energy_promedio=energy_promedio,
            danceability_promedio=danceability_promedio,
            valence_promedio=valence_promedio
        )

        await asyncio.sleep(0.01)
        session.add(benchmark)
        session.commit()
        session.refresh(benchmark)
        return benchmark

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error creando benchmark: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.get("/api", response_model=list[Benchmark])
async def listar_benchmarks(session: Session = Depends(get_session)):
    """API: Listar benchmarks (JSON) - ORIGINAL"""
    try:
        await asyncio.sleep(0.01)
        return session.exec(
            select(Benchmark).where(Benchmark.deleted_at == None)
        ).all()
    except Exception as e:
        logger.error(f"Error listando benchmarks: {e}")
        return []


@router.get("/api/{id}", response_model=Benchmark)
async def obtener_benchmark(id: int, session: Session = Depends(get_session)):
    """API: Obtener benchmark (JSON) - ORIGINAL"""
    try:
        await asyncio.sleep(0.01)
        benchmark = session.get(Benchmark, id)
        if not benchmark or benchmark.deleted_at:
            raise HTTPException(404, "Benchmark no encontrado")
        return benchmark
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo benchmark {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.put("/{id}", response_model=Benchmark)
async def actualizar_benchmark(
    id: int,
    pais: str = None,
    genero: str = None,
    tempo_promedio: float = None,
    energy_promedio: float = None,
    danceability_promedio: float = None,
    valence_promedio: float = None,
    session: Session = Depends(get_session)
):
    """API: Actualizar benchmark (JSON) - ORIGINAL"""
    try:
        await asyncio.sleep(0.01)
        benchmark = session.get(Benchmark, id)
        if not benchmark or benchmark.deleted_at:
            raise HTTPException(404, "Benchmark no encontrado")

        if tempo_promedio is not None and (tempo_promedio < 0 or tempo_promedio > 300):
            raise HTTPException(400, "Tempo promedio inválido")
        if energy_promedio is not None and (energy_promedio < 0 or energy_promedio > 1):
            raise HTTPException(400, "Energy promedio inválido")

        if pais is not None:
            benchmark.pais = pais
        if genero is not None:
            benchmark.genero = genero
        if tempo_promedio is not None:
            benchmark.tempo_promedio = tempo_promedio
        if energy_promedio is not None:
            benchmark.energy_promedio = energy_promedio
        if danceability_promedio is not None:
            benchmark.danceability_promedio = danceability_promedio
        if valence_promedio is not None:
            benchmark.valence_promedio = valence_promedio

        await asyncio.sleep(0.01)
        session.add(benchmark)
        session.commit()
        session.refresh(benchmark)
        return benchmark

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error actualizando benchmark {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.delete("/{id}")
async def eliminar_benchmark(id: int, session: Session = Depends(get_session)):
    """API: Eliminar benchmark (JSON) - ORIGINAL"""
    try:
        await asyncio.sleep(0.01)
        benchmark = session.get(Benchmark, id)
        if not benchmark:
            raise HTTPException(404, "Benchmark no encontrado")

        if benchmark.deleted_at:
            return {"message": "Benchmark ya estaba eliminado", "ok": True}

        benchmark.deleted_at = datetime.utcnow()
        await asyncio.sleep(0.01)
        session.add(benchmark)
        session.commit()
        return {"message": "Benchmark eliminado exitosamente", "ok": True}

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error eliminando benchmark {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")


@router.get("/{id}/restaurar")
async def restaurar_benchmark(id: int, session: Session = Depends(get_session)):
    """API: Restaurar benchmark con redirección"""
    try:
        await asyncio.sleep(0.01)
        benchmark = session.get(Benchmark, id)

        if not benchmark:
            raise HTTPException(404, "Benchmark no encontrado")

        if not benchmark.deleted_at:
            # Ya restaurado → redirige igual
            return RedirectResponse("/benchmarks", status_code=303)

        benchmark.deleted_at = None
        session.add(benchmark)
        session.commit()

        # ✔ Redirige al listado de eliminados
        return RedirectResponse("/benchmarks", status_code=303)

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error restaurando benchmark {id}: {e}")
        raise HTTPException(500, "Error interno del servidor")
