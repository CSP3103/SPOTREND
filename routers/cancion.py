from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException
from sqlmodel import Session, select
from uuid import UUID
from datetime import datetime
from database import get_session
from models import Cancion
from supabase_service import upload_to_bucket

router = APIRouter(prefix="/canciones", tags=["Canciones"])


# CREATE
@router.post("/", response_model=Cancion)
async def crear_cancion(
        nombre: str = Form(...),
        artista: str = Form(...),
        tempo: float = Form(...),
        energy: float = Form(...),
        danceability: float = Form(0.0),
        valence: float = Form(0.0),
        acousticness: float = Form(0.0),
        imagen: UploadFile | None = None,
        session: Session = Depends(get_session)
):
    """Crea una nueva canción manual."""
    url = None
    if imagen:
        url = await upload_to_bucket(imagen)

    nueva = Cancion(
        nombre=nombre,
        artista=artista,
        tempo=tempo,
        energy=energy,
        danceability=danceability,
        valence=valence,
        acousticness=acousticness,
        imagen_url=url
    )

    session.add(nueva)
    session.commit()
    session.refresh(nueva)
    return nueva


# READ ALL (activas)
@router.get("/", response_model=list[Cancion])
def listar_canciones(session: Session = Depends(get_session)):
    """Lista todas las canciones activas (no eliminadas)."""
    statement = select(Cancion).where(Cancion.deleted_at == None)
    return session.exec(statement).all()


# READ ONE
@router.get("/{id}", response_model=Cancion)
def obtener_cancion(id: UUID, session: Session = Depends(get_session)):
    """Obtiene una canción por ID."""
    cancion = session.get(Cancion, id)
    if not cancion or cancion.deleted_at:
        raise HTTPException(status_code=404, detail="Canción no encontrada")
    return cancion


# UPDATE
@router.put("/{id}", response_model=Cancion)
async def actualizar_cancion(
        id: UUID,
        nombre: str = Form(...),
        artista: str = Form(...),
        tempo: float = Form(...),
        energy: float = Form(...),
        imagen: UploadFile | None = None,
        session: Session = Depends(get_session)
):
    """Actualiza una canción existente."""
    cancion = session.get(Cancion, id)
    if not cancion or cancion.deleted_at:
        raise HTTPException(status_code=404, detail="Canción no encontrada")

    # Actualizar campos
    cancion.nombre = nombre
    cancion.artista = artista
    cancion.tempo = tempo
    cancion.energy = energy

    if imagen:
        cancion.imagen_url = await upload_to_bucket(imagen)

    session.add(cancion)
    session.commit()
    session.refresh(cancion)
    return cancion


# DELETE (soft)
@router.delete("/{id}")
def eliminar_cancion(id: UUID, session: Session = Depends(get_session)):
    """Elimina lógicamente una canción."""
    cancion = session.get(Cancion, id)
    if not cancion:
        raise HTTPException(status_code=404, detail="Canción no encontrada")

    cancion.deleted_at = datetime.utcnow()
    session.add(cancion)
    session.commit()
    return {"message": "Canción eliminada lógicamente"}


# LIST DELETED
@router.get("/eliminadas/", response_model=list[Cancion])
def listar_eliminadas(session: Session = Depends(get_session)):
    """Lista canciones eliminadas lógicamente."""
    statement = select(Cancion).where(Cancion.deleted_at != None)
    return session.exec(statement).all()


# RESTORE
@router.post("/restaurar/{id}", response_model=Cancion)
def restaurar_cancion(id: UUID, session: Session = Depends(get_session)):
    """Restaura una canción eliminada."""
    cancion = session.get(Cancion, id)
    if not cancion:
        raise HTTPException(status_code=404, detail="Canción no encontrada")

    if not cancion.deleted_at:
        raise HTTPException(status_code=400, detail="Canción no está eliminada")

    cancion.deleted_at = None
    session.add(cancion)
    session.commit()
    session.refresh(cancion)
    return cancion