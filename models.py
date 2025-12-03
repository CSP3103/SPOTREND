import uuid
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime


# ====================================================
#   MODELO ARTISTA (manual, creado por el usuario)
# ====================================================
class Artista(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True)
    pais: Optional[str] = Field(default=None)
    genero_principal: Optional[str] = Field(default=None)
    popularidad: Optional[int] = Field(default=50)
    imagen_url: Optional[str] = Field(default=None)
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)

    # Relación 1:N → Canciones
    canciones: List["Cancion"] = Relationship(back_populates="artista_ref")


# ====================================================
#   MODELO CANCIÓN (manual o vía Spotify)
# ====================================================
class Cancion(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    nombre: str = Field(index=True)
    artista: str  # nombre escrito por usuario
    artista_id: Optional[int] = Field(default=None, foreign_key="artista.id")

    # Audio features
    tempo: float
    energy: float
    danceability: Optional[float] = Field(default=None)
    valence: Optional[float] = Field(default=None)
    acousticness: Optional[float] = Field(default=None)

    # URLs
    imagen_url: Optional[str] = Field(default=None)
    spotify_id: Optional[str] = Field(default=None, index=True)

    # Timestamps
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)

    # Relaciones
    artista_ref: Optional[Artista] = Relationship(back_populates="canciones")
    analisis: List["AnalisisResultado"] = Relationship(back_populates="cancion")


# ====================================================
#       BENCHMARK (tendencia promedio por país/género)
# ====================================================
class Benchmark(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pais: str = Field(index=True)
    genero: str = Field(index=True)

    # Promedios
    tempo_promedio: float
    energy_promedio: float
    danceability_promedio: float = Field(default=0.0)
    valence_promedio: float = Field(default=0.0)

    creado_en: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)

    # Relación con análisis
    analisis: List["AnalisisResultado"] = Relationship(back_populates="benchmark")


# ====================================================
#   ANALISIS: Relación N:M Canción <-> Benchmark
# ====================================================
class AnalisisResultado(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cancion_id: uuid.UUID = Field(foreign_key="cancion.id")
    benchmark_id: int = Field(foreign_key="benchmark.id")

    # Resultado de la comparación
    afinidad: float
    hallazgo: str  # ALTO / MEDIO / BAJO

    creado_en: datetime = Field(default_factory=datetime.utcnow)

    # Relaciones
    cancion: Cancion = Relationship(back_populates="analisis")
    benchmark: Benchmark = Relationship(back_populates="analisis")


# ====================================================
#           CONFIGURACION (global del sistema)
# ====================================================
class Configuracion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    clave: str = Field(unique=True, index=True)
    valor: str
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)