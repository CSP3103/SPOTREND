from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from database import get_session
from models import Benchmark
from typing import List

router = APIRouter(prefix="/benchmark", tags=["Benchmark (Tendencias)"])


# 1. CREATE
@router.post("/", response_model=Benchmark, status_code=status.HTTP_201_CREATED)
def create_benchmark(*, session: Session = Depends(get_session), benchmark: Benchmark):
    """Crea una nueva referencia de tendencia (Benchmark)."""
    session.add(benchmark)
    session.commit()
    session.refresh(benchmark)
    return benchmark


# 2. READ (Lista)
@router.get("/", response_model=List[Benchmark])
def read_benchmarks(*, session: Session = Depends(get_session)):
    """Obtiene la lista completa de Benchmarks."""
    benchmarks = session.exec(select(Benchmark)).all()
    return benchmarks


# 3. READ (Detalle)
@router.get("/{benchmark_id}", response_model=Benchmark)
def read_benchmark(*, session: Session = Depends(get_session), benchmark_id: int):
    """Obtiene un Benchmark por su ID."""
    benchmark = session.get(Benchmark, benchmark_id)
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark no encontrado")
    return benchmark


# 4. UPDATE
@router.put("/{benchmark_id}", response_model=Benchmark)
def update_benchmark(*, session: Session = Depends(get_session), benchmark_id: int, benchmark: Benchmark):
    """Actualiza los valores promedio de un Benchmark."""
    db_benchmark = session.get(Benchmark, benchmark_id)
    if not db_benchmark:
        raise HTTPException(status_code=404, detail="Benchmark no encontrado")

    benchmark_data = benchmark.model_dump(exclude_unset=True)
    db_benchmark.sqlmodel_update(benchmark_data)

    session.add(db_benchmark)
    session.commit()
    session.refresh(db_benchmark)
    return db_benchmark


# 5. DELETE
@router.delete("/{benchmark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_benchmark(*, session: Session = Depends(get_session), benchmark_id: int):
    """Elimina un Benchmark de la base de datos."""
    benchmark = session.get(Benchmark, benchmark_id)
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark no encontrado")
    session.delete(benchmark)
    session.commit()
    return {"ok": True}