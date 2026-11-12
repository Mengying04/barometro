"""Nivel de movimiento de la zona: cuánta gente pasa por un punto frente al resto de la
Comunidad de Madrid.

    from movimiento import nivel_movimiento
    m = nivel_movimiento(perfil)      # perfil = perfil_horario(lat, lon)
    m["nivel"], m["frase"]            # «Paso medio», «pasa más gente que en 6 de cada 10…»

La referencia es una muestra de puntos: un punto interior de cada sección censal de la
Comunidad con vecinos (las secciones tienen una población parecida, unas 1.500 personas,
así que es una muestra de «sitios habitados»). Para cada uno se guarda la gente que pasa en
un día laborable según perfil_horario(). Se calcula una vez y se guarda en
datos/procesados/referencia_movimiento.parquet:

    python src/movimiento.py --generar        # unos minutos
    python src/movimiento.py 40.4046 -3.6106  # nivel de un punto

TODO ES UNA ESTIMACIÓN: compara estimaciones con estimaciones. Hay que volver a generar la
referencia si cambian los datos o los supuestos del perfil por horas. Los cortes de los
niveles están en src/supuestos.py.
"""

from __future__ import annotations

import sys
from functools import lru_cache

import numpy as np
import pandas as pd

import supuestos as S
from procesar import PROC

REFERENCIA = PROC / "referencia_movimiento.parquet"


def pasos_laborable(perfil: dict) -> int:
    """Personas que pasan cerca en un día laborable entero (suma de las 24 horas)."""
    return int(perfil["horas"].loc["laborable"]["total"].sum())


def generar() -> pd.DataFrame:
    """Calcula el perfil por horas en un punto interior de cada sección censal y guarda la
    gente que pasa en un laborable. No guarda nada más que el código de la sección, su
    población, el punto y esa cifra."""
    import geopandas as gpd

    from perfil_horario import perfil_horario
    secc = gpd.read_parquet(PROC / "secciones_censales.parquet",
                            columns=["cdgseccion", "cod_municipio", "poblacion", "geometry"])
    puntos = gpd.GeoSeries(secc.representative_point(), crs=secc.crs).to_crs(4326)
    filas = []
    for i, (f, p) in enumerate(zip(secc.itertuples(), puntos)):
        lat, lon = round(p.y, 6), round(p.x, 6)
        filas.append({"cdgseccion": f.cdgseccion, "cod_municipio": f.cod_municipio,
                      "poblacion": 0 if pd.isna(f.poblacion) else int(f.poblacion),
                      "lat": lat, "lon": lon,
                      "pasos_laborable": pasos_laborable(perfil_horario(lat, lon))})
        if (i + 1) % 500 == 0:
            print(f"  {i + 1} de {len(secc)} secciones", flush=True)
    ref = pd.DataFrame(filas)
    ref.to_parquet(REFERENCIA, index=False)
    return ref


@lru_cache(maxsize=1)
def referencia() -> np.ndarray:
    """Gente que pasa en un laborable en cada punto de la muestra (solo secciones con
    vecinos), ordenada de menos a más."""
    ref = pd.read_parquet(REFERENCIA)
    return np.sort(ref.loc[ref["poblacion"] > 0, "pasos_laborable"].to_numpy(dtype=float))


def frase_comparacion(posicion: float) -> str:
    """«pasa menos gente que en 9 de cada 10 sitios habitados de la Comunidad»."""
    donde = "sitios habitados de la Comunidad"
    medio = "pasa más o menos la misma gente que en un sitio habitado medio de la Comunidad"
    # Se redondea hacia abajo para no exagerar y para que cuadre con los cortes de los
    # niveles: «9 de cada 10» solo sale en el 10 % de arriba o en el de abajo.
    if posicion < 0.5:
        n = min(9, int(10 * (1 - posicion) + 1e-9))
        return f"pasa menos gente que en {n} de cada 10 {donde}" if n > 5 else medio
    n = min(9, int(10 * posicion + 1e-9))
    return f"pasa más gente que en {n} de cada 10 {donde}" if n > 5 else medio


def nivel_movimiento(perfil: dict) -> dict:
    """Sitúa el punto en la muestra de referencia. ESTIMACIÓN.

    Devuelve: pasos_laborable (gente que pasa en un laborable), posicion (parte de los
    sitios de referencia por los que pasa menos gente, de 0 a 1), nivel (1 a 5), nombre del
    nivel, frase de comparación, mediana de la referencia y si es «muy poco paso»."""
    pasos = pasos_laborable(perfil)
    ref = referencia()
    # Parte de la muestra con menos gente (los empates cuentan la mitad).
    posicion = float((np.searchsorted(ref, pasos, "left")
                      + np.searchsorted(ref, pasos, "right")) / 2 / len(ref))
    n = next(i for i, (corte, _) in enumerate(S.MOVIMIENTO_NIVELES, 1) if posicion < corte)
    if pasos < S.MOVIMIENTO_MINIMO_PASOS:
        n = 1
    sitios = f"{len(ref):,}".replace(",", ".")
    return {
        "pasos_laborable": pasos, "posicion": round(posicion, 3),
        "nivel": n, "nombre": S.MOVIMIENTO_NIVELES[n - 1][1],
        "niveles": [nombre for _, nombre in S.MOVIMIENTO_NIVELES],
        "frase": frase_comparacion(posicion),
        "mediana_referencia": int(np.median(ref)), "sitios_referencia": int(len(ref)),
        "muy_poco_paso": n == 1,
        "aviso": S.MOVIMIENTO_AVISO_MUY_POCO if n == 1 else None,
        "base": "estimación",
        "nota": ("Estimación: compara la gente que pasa en un día laborable a menos de "
                 f"{S.RADIO_M} m del punto con la de un punto interior de cada sección "
                 f"censal habitada de la Comunidad de Madrid ({sitios} sitios). Las dos "
                 "cifras salen del mismo perfil por horas, con sus supuestos."),
    }


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--generar":
        ref = generar()
        print(ref["pasos_laborable"].describe().to_string())
        return 0
    from perfil_horario import perfil_horario
    m = nivel_movimiento(perfil_horario(float(argv[0]), float(argv[1])))
    print(f"{m['nombre']} (nivel {m['nivel']} de 5): ~{m['pasos_laborable']} personas en un "
          f"laborable; {m['frase']}. ESTIMACIÓN.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
