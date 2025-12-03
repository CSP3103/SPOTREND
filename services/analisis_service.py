import math
from typing import List, Dict, Any, TYPE_CHECKING
from models import Cancion, Benchmark  # Importamos los modelos para tipado
from datetime import datetime

# Usamos TYPE_CHECKING para evitar dependencia circular
if TYPE_CHECKING:
    from models import Cancion, Benchmark


# =========================================================================
# CLASE AUXILIAR DE DATOS
# =========================================================================

class ObjetoAAnalizar:
    """
    Clase simple para estandarizar la extracción de métricas, ya sea de una Cancion
    o un Benchmark, facilitando el cálculo.
    """

    def __init__(self, **kwargs):
        # Maneja los campos de Cancion (tempo, energy) o Benchmark (tempo_promedio, energy_promedio)
        self.tempo = kwargs.get('tempo', kwargs.get('tempo_promedio', 0.0))
        self.energy = kwargs.get('energy', kwargs.get('energy_promedio', 0.0))
        # Aseguramos que el objeto tiene la información de contexto para el hallazgo
        self.pais = kwargs.get('pais', 'N/A')
        self.genero = kwargs.get('genero', 'N/A')


# =========================================================================
# LÓGICA CENTRAL: DISTANCIA EUCLIDIANA Y AFINIDAD
# (Basado en tu código original)
# =========================================================================

def calcular_distancia_euclidiana(obj1: ObjetoAAnalizar, obj2: ObjetoAAnalizar) -> float:
    """Calcula la distancia euclidiana entre dos puntos (Tempo y Energy)."""

    # La diferencia entre el valor de la canción y el promedio del benchmark
    diferencia_tempo = (obj1.tempo - obj2.tempo) ** 2
    diferencia_energy = (obj1.energy - obj2.energy) ** 2

    distancia = math.sqrt(diferencia_tempo + diferencia_energy)

    return round(distancia, 4)


def generar_hallazgo(distancia: float, benchmark_pais: str, benchmark_genero: str) -> str:
    """
    Genera un hallazgo estratégico basado en la distancia calculada.
    (Basado en tus umbrales, los hemos ajustado ligeramente para consistencia con valores reales).
    """

    # Estos umbrales pueden ajustarse según el contexto de tu data,
    # pero son funcionales para demostrar la lógica.
    if distancia < 10.0:
        compatibilidad = "ALTA"
        accion = f"Tu canción está alineada con el {benchmark_genero} en {benchmark_pais}. Prioriza este mercado."
    elif 10.0 <= distancia < 20.0:
        compatibilidad = "MEDIA"
        accion = f"Existe una buena oportunidad en el {benchmark_genero} en {benchmark_pais}, pero considera ligeros ajustes rítmicos."
    else:
        compatibilidad = "BAJA"
        accion = f"El {benchmark_genero} en {benchmark_pais} tiene baja compatibilidad. Se recomienda explorar otras tendencias."

    return f"{compatibilidad}: {accion}"


def calcular_afinidad_y_hallazgo(
        cancion: ObjetoAAnalizar,
        benchmark: ObjetoAAnalizar,
) -> tuple[float, str]:
    """Función principal que devuelve el score de afinidad y el hallazgo estratégico."""

    # 1. Calcular la distancia
    distancia = calcular_distancia_euclidiana(cancion, benchmark)

    # 2. Tu métrica de afinidad (Inverso de la distancia)
    # Guardamos el score basado en tu fórmula: Afinidad = 100 / (1 + distancia)
    afinidad_score = round(100 / (1 + distancia), 2)

    # 3. Generar el hallazgo
    hallazgo = generar_hallazgo(distancia, benchmark.pais, benchmark.genero)

    # Devolvemos la afinidad (score) y el texto del hallazgo.
    return afinidad_score, hallazgo


# =========================================================================
# LÓGICA AVANZADA: SIMILITUD ENTRE CANCIONES (Hallazgo Avanzado)
# =========================================================================

def encontrar_canciones_similares(
        cancion_prototipo: Cancion,
        todas_las_canciones: List[Cancion],
        top_n: int = 3
) -> List[Dict[str, Any]]:
    """
    Compara la canción prototipo con otras canciones en el historial (DB)
    para encontrar los prototipos más similares, cumpliendo el requisito de 'Relacionar con otros artistas'.
    """
    similitudes = []

    # 1. Preparamos el Prototipo
    prototipo_analisis = ObjetoAAnalizar(tempo=cancion_prototipo.tempo, energy=cancion_prototipo.energy)

    for otra_cancion in todas_las_canciones:
        # Evitar compararse consigo misma o con canciones eliminadas lógicamente
        if otra_cancion.id == cancion_prototipo.id or otra_cancion.deleted_at is not None:
            continue

        # 2. Preparamos la canción a comparar
        otra_cancion_analisis = ObjetoAAnalizar(tempo=otra_cancion.tempo, energy=otra_cancion.energy)

        # 3. Calculamos la afinidad
        distancia = calcular_distancia_euclidiana(prototipo_analisis, otra_cancion_analisis)

        # Usamos tu misma fórmula para dar un score de 0 a 100
        afinidad_score = round(100 / (1 + distancia), 2)

        # Generamos un hallazgo simplificado
        hallazgo_texto = f"Afinidad del {afinidad_score}%. Muy similar al prototipo de {otra_cancion.artista}." if afinidad_score > 80 else f"Afinidad del {afinidad_score}%. Baja similitud rítmica."

        similitudes.append({
            "artista": otra_cancion.artista,
            "nombre": otra_cancion.nombre,
            "imagen_url": otra_cancion.imagen_url,
            "distancia": distancia,
            "afinidad_score": afinidad_score,
            "hallazgo_texto": hallazgo_texto
        })

    # Ordenamos por la afinidad (score más alto es mejor)
    similitudes.sort(key=lambda x: x['afinidad_score'], reverse=True)

    return similitudes[:top_n]