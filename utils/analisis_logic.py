import math

def calcular_distancia_euclidiana(features_cancion: dict, features_benchmark: dict) -> float:
    """Calcula la distancia euclidiana entre dos conjuntos de características.
    Una distancia menor significa mayor afinidad."""

    # Lista de características a comparar (expande esta lista cuando integres Spotify)
    features_list = ['tempo', 'energy']

    suma_cuadrados = 0
    for feature in features_list:
        # La diferencia entre el valor de la canción y el promedio del benchmark
        diferencia = features_cancion[feature] - features_benchmark[feature]
        suma_cuadrados += diferencia ** 2

    return math.sqrt(suma_cuadrados)


def generar_hallazgo(distancia: float, benchmark_pais: str, benchmark_genero: str) -> str:
    """Genera un hallazgo estratégico basado en la distancia calculada."""

    # Puedes ajustar estos umbrales según tus datos
    if distancia < 5.0:
        compatibilidad = "muy alta"
        accion = f"Prioriza este mercado, tu canción está perfectamente alineada con el {benchmark_genero} en {benchmark_pais}."
    elif 5.0 <= distancia < 15.0:
        compatibilidad = "buena"
        accion = f"Existe una buena oportunidad para el {benchmark_genero} en {benchmark_pais}, con ligeros ajustes en la promoción."
    else:
        compatibilidad = "media/baja"
        accion = f"El {benchmark_genero} en {benchmark_pais} tiene una baja compatibilidad. Se recomienda explorar otros mercados."

    return f"Afinidad {compatibilidad}. {accion}"


def calcular_afinidad_y_hallazgo(
        cancion_tempo: float,
        cancion_energy: float,
        benchmark_tempo: float,
        benchmark_energy: float,
        benchmark_pais: str,
        benchmark_genero: str
) -> tuple[float, str]:
    """Función principal para calcular afinidad y hallazgo."""

    # 1. Preparar datos para el cálculo
    features_c = {'tempo': cancion_tempo, 'energy': cancion_energy}
    features_b = {'tempo': benchmark_tempo, 'energy': benchmark_energy}

    # 2. Calcular la distancia
    distancia = calcular_distancia_euclidiana(features_c, features_b)

    # Para el reporte, se suele usar un valor inverso a la distancia (Afinidad)
    # Por ejemplo: Afinidad = 100 / (1 + distancia). Cuanto mayor la distancia, menor la afinidad.
    afinidad_score = 100 / (1 + distancia)

    # 3. Generar el hallazgo
    hallazgo = generar_hallazgo(distancia, benchmark_pais, benchmark_genero)

    # Devuelve el score (que será guardado como 'afinidad') y el hallazgo
    return afinidad_score, hallazgo