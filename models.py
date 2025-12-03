import uuid
from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime  # Necesario para el Soft Delete


# =========================================================================
# CLASE DE ASOCIACIÓN N:M (AnalisisResultado)
# =========================================================================

class AnalisisResultado(SQLModel, table=True):
    """
    Tabla de Unión N:M que almacena el resultado de la comparación entre una Canción y un Benchmark.
    """
    id: Optional[int] = Field(default=None, primary_key=True)

    # Claves Foráneas (Relaciones 1:N)
    cancion_id: uuid.UUID = Field(foreign_key="cancion.id", index=True)
    benchmark_id: int = Field(foreign_key="benchmark.id", index=True)

    # Métricas del Análisis
    afinidad: float = Field(description="Distancia Euclidiana, 0 es idéntico.")
    hallazgo: str = Field(description="ALTO, MEDIO, BAJO (clasificación de afinidad).")

    creado_en: datetime = Field(default_factory=datetime.utcnow)

    # Relaciones de vuelta (Back Populates)
    cancion: "Cancion" = Relationship(back_populates="analisis")
    benchmark: "Benchmark" = Relationship(back_populates="analisis")


# =========================================================================
# CLASE DE REFERENCIA (Benchmark) - Incluye Soft Delete
# =========================================================================

class Benchmark(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pais: str = Field(index=True)
    genero: str = Field(index=True)
    tempo_promedio: float
    energy_promedio: float
    creado_en: datetime = Field(default_factory=datetime.utcnow)

    # === CAMPO DE ELIMINACIÓN LÓGICA (Trazabilidad) ===
    deleted_at: Optional[datetime] = Field(default=None)

    analisis: List[AnalisisResultado] = Relationship(back_populates="benchmark")


# =========================================================================
# CLASE DE PROTOTIPO (Cancion) - Incluye Soft Delete
# =========================================================================

class Cancion(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    nombre: str
    artista: str
    tempo: float
    energy: float
    imagen_url: Optional[str] = Field(default=None)
    spotify_id: Optional[str] = Field(default=None)
    creado_en: datetime = Field(default_factory=datetime.utcnow)

    # === CAMPO DE ELIMINACIÓN LÓGICA (Trazabilidad) ===
    deleted_at: Optional[datetime] = Field(default=None)

    analisis: List[AnalisisResultado] = Relationship(back_populates="cancion")

class Configuracion(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)
    clave: str = Field(index=True, unique=True)
    valor: str