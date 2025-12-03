from math import sqrt
from typing import Dict, List
from models import Cancion, Benchmark


def calcular_afinidad(cancion: Cancion, benchmark: Benchmark) -> float:
    """Calcula afinidad entre canción y benchmark."""
    tempo_diff = (cancion.tempo - benchmark.tempo_promedio) ** 2
    energy_diff = (cancion.energy - benchmark.energy_promedio) ** 2

    # Opcional: añadir otras métricas
    if cancion.danceability and benchmark.danceability_promedio:
        tempo_diff += (cancion.danceability - benchmark.danceability_promedio) ** 2

    return sqrt(tempo_diff + energy_diff)


def clasificar_afinidad(distancia: float) -> str:
    """Clasifica la afinidad en ALTO/MEDIO/BAJO."""
    if distancia < 5:
        return "ALTO"
    elif distancia < 15:
        return "MEDIO"
    return "BAJO"


def comparar_con_benchmarks(cancion: Cancion, benchmarks: List[Benchmark]):
    """Compara canción con múltiples benchmarks."""
    mejor = None
    mejor_distancia = float("inf")

    for b in benchmarks:
        d = calcular_afinidad(cancion, b)
        if d < mejor_distancia:
            mejor_distancia = d
            mejor = b

    return {
        "benchmark": mejor,
        "afinidad": mejor_distancia,
        "hallazgo": clasificar_afinidad(mejor_distancia)
    }


def comparar_canciones(a: Cancion, b: Cancion):
    """Compara dos canciones manuales."""
    # Simulación de distancia
    tempo_diff = (a.tempo - b.tempo) ** 2
    energy_diff = (a.energy - b.energy) ** 2
    distancia = sqrt(tempo_diff + energy_diff)

    return {
        "afinidad": distancia,
        "hallazgo": clasificar_afinidad(distancia)
    }

