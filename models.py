from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
import datetime
import uuid


class Benchmark(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pais: str = Field(index=True)
    genero: str = Field(index=True)
    tempo_promedio: float
    energy_promedio: float
    creado_en: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    analisis: List["AnalisisResultado"] = Relationship(back_populates="benchmark")


class Cancion(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    nombre: str
    artista: str
    tempo: float
    energy: float
    imagen_url: Optional[str] = Field(default=None)  # URL del Bucket (Requisito Multimedia)
    spotify_id: Optional[str] = Field(default=None)
    creado_en: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    analisis: List["AnalisisResultado"] = Relationship(back_populates="cancion")


class AnalisisResultado(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)

    cancion_id: uuid.UUID = Field(foreign_key="cancion.id", index=True)
    benchmark_id: int = Field(foreign_key="benchmark.id", index=True)

    afinidad: float  # Resultado del cálculo
    hallazgo: str  # Mensaje estratégico (Función de Hallazgos)
    creado_en: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    cancion: Cancion = Relationship(back_populates="analisis")
    benchmark: Benchmark = Relationship(back_populates="analisis")

class Configuracion(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)
    clave: str = Field(index=True, unique=True)
    valor: str