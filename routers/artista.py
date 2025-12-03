from fastapi import APIRouter, Depends, UploadFile, Form, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from database import get_session
from models import Artista
from supabase_service import upload_to_bucket

router = APIRouter(prefix="/artistas", tags=["Artistas"])


# CREATE
@router.post("/", response_model=Artista)
async def crear_artista(
        nombre: str = Form(...),
        pais: str = Form(None),
        genero_principal: str = Form(None),
        popularidad: int = Form(50),
        imagen: UploadFile | None = None,
        session: Session = Depends(get_session)
):
    """Crea un artista manual."""
    url = None
    if imagen:
        url = await upload_to_bucket(imagen)

    nuevo = Artista(
        nombre=nombre,
        pais=pais,
        genero_principal=genero_principal,
        popularidad=popularidad,
        imagen_url=url
    )

    session.add(nuevo)
    session.commit()
    session.refresh(nuevo)
    return nuevo


# READ ALL
@router.get("/", response_model=list[Artista])
def listar_artistas(session: Session = Depends(get_session)):
    """Lista artistas activos."""
    statement = select(Artista).where(Artista.deleted_at == None)
    return session.exec(statement).all()


# READ ONE
@router.get("/{id}", response_model=Artista)
def obtener_artista(id: int, session: Session = Depends(get_session)):
    """Obtiene artista por ID."""
    artista = session.get(Artista, id)
    if not artista or artista.deleted_at:
        raise HTTPException(status_code=404, detail="Artista no encontrado")
    return artista


# UPDATE
@router.put("/{id}", response_model=Artista)
async def actualizar_artista(
        id: int,
        nombre: str = Form(...),
        pais: str = Form(None),
        genero_principal: str = Form(None),
        imagen: UploadFile | None = None,
        session: Session = Depends(get_session)
):
    """Actualiza artista."""
    artista = session.get(Artista, id)
    if not artista or artista.deleted_at:
        raise HTTPException(status_code=404, detail="Artista no encontrado")

    artista.nombre = nombre
    artista.pais = pais
    artista.genero_principal = genero_principal

    if imagen:
        artista.imagen_url = await upload_to_bucket(imagen)

    session.add(artista)
    session.commit()
    session.refresh(artista)
    return artista


# DELETE (soft)
@router.delete("/{id}")
def eliminar_artista(id: int, session: Session = Depends(get_session)):
    """Elimina lógicamente artista."""
    artista = session.get(Artista, id)
    if not artista:
        raise HTTPException(status_code=404, detail="Artista no encontrado")

    artista.deleted_at = datetime.utcnow()
    session.add(artista)
    session.commit()
    return {"message": "Artista eliminado lógicamente"}


# LIST DELETED
@router.get("/eliminados/", response_model=list[Artista])
def listar_artistas_eliminados(session: Session = Depends(get_session)):
    """Lista artistas eliminados."""
    statement = select(Artista).where(Artista.deleted_at != None)
    return session.exec(statement).all()


# RESTORE
@router.post("/restaurar/{id}", response_model=Artista)
def restaurar_artista(id: int, session: Session = Depends(get_session)):
    """Restaura artista eliminado."""
    artista = session.get(Artista, id)
    if not artista:
        raise HTTPException(status_code=404, detail="Artista no encontrado")

    if not artista.deleted_at:
        raise HTTPException(status_code=400, detail="Artista no está eliminado")

    artista.deleted_at = None
    session.add(artista)
    session.commit()
    session.refresh(artista)
    return artista