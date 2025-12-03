from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from datetime import datetime
from database import get_session
from models import Benchmark

router = APIRouter(prefix="/benchmark", tags=["Benchmark"])


# CREATE manual
@router.post("/", response_model=Benchmark, status_code=status.HTTP_201_CREATED)
def create_benchmark(
        pais: str,
        genero: str,
        tempo_promedio: float,
        energy_promedio: float,
        danceability_promedio: float = 0.0,
        valence_promedio: float = 0.0,
        session: Session = Depends(get_session)
):
    """Crea benchmark manualmente."""
    db_benchmark = Benchmark(
        pais=pais,
        genero=genero,
        tempo_promedio=tempo_promedio,
        energy_promedio=energy_promedio,
        danceability_promedio=danceability_promedio,
        valence_promedio=valence_promedio
    )

    session.add(db_benchmark)
    session.commit()
    session.refresh(db_benchmark)
    return db_benchmark


# READ all activos
@router.get("/", response_model=List[Benchmark])
def read_benchmarks(session: Session = Depends(get_session)):
    """Lista benchmarks activos."""
    statement = select(Benchmark).where(Benchmark.deleted_at == None)
    return session.exec(statement).all()


# DELETE soft
@router.delete("/{benchmark_id}")
def delete_benchmark(benchmark_id: int, session: Session = Depends(get_session)):
    """Elimina benchmark lógicamente."""
    benchmark = session.get(Benchmark, benchmark_id)
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark no encontrado")

    benchmark.deleted_at = datetime.utcnow()
    session.add(benchmark)
    session.commit()
    return {"message": "Benchmark eliminado"}