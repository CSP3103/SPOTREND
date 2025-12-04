from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
import shortuuid




class Cancion(SQLModel, table=True):
    id: str = Field(default_factory=lambda: shortuuid.uuid()[:10], primary_key=True)
    nombre: str
    artista: str
    tempo: float
    energy: float
    danceability: Optional[float] = None
    valence: Optional[float] = None
    acousticness: Optional[float] = None
    imagen_url: Optional[str] = None
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    analisis: List["AnalisisResultado"] = Relationship(back_populates="cancion")


class Artista(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    pais: Optional[str] = None
    genero_principal: Optional[str] = None
    popularidad: int = 50
    imagen_url: Optional[str] = None
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None



class Benchmark(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pais: str
    genero: str
    tempo_promedio: float
    energy_promedio: float
    danceability_promedio: float = 0.0
    valence_promedio: float = 0.0
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    analisis: List["AnalisisResultado"] = Relationship(back_populates="benchmark")


class AnalisisResultado(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cancion_id: str = Field(foreign_key="cancion.id")
    benchmark_id: int = Field(foreign_key="benchmark.id")
    afinidad: float
    hallazgo: str
    creado_en: datetime = Field(default_factory=datetime.utcnow)

    cancion: Cancion = Relationship(back_populates="analisis")
    benchmark: Benchmark = Relationship(back_populates="analisis")


class Configuracion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    clave: str = Field(unique=True)
    valor: str