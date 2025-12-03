import math


def calcular_similitud(cancion1: dict, cancion2: dict) -> float:
    """Calcula similitud entre dos canciones."""
    tempo_diff = (cancion1.get('tempo', 0) - cancion2.get('tempo', 0)) ** 2
    energy_diff = (cancion1.get('energy', 0) - cancion2.get('energy', 0)) ** 2
    dance_diff = (cancion1.get('danceability', 0) - cancion2.get('danceability', 0)) ** 2

    distancia = math.sqrt(tempo_diff + energy_diff + dance_diff)
    return max(0, 100 - distancia)


def clasificar_afinidad(distancia: float) -> str:
    if distancia < 10:
        return "ALTA"
    elif distancia < 20:
        return "MEDIA"
    else:
        return "BAJA"
