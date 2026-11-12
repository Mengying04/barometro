"""BARómetro: resumen de los tres puntos de prueba, para comparar resultados.

Calcula el perfil, el informe, las recomendaciones y el nivel de movimiento de los tres
ejemplos de la aplicación y enseña, de cada uno, unas pocas cifras legibles y una huella
(SHA-256) de todo el resultado. Dos entornos dan los mismos resultados si las huellas
coinciden. No cambia ningún dato: solo llama a las funciones de siempre.

Sirve para:
  - comprobar que la aplicación da lo mismo en otro entorno (por ejemplo, dentro del
    contenedor de Docker);
  - ver de un vistazo qué cambia cuando se actualizan los datos (el flujo de GitHub Actions
    lo ejecuta antes y después y pone las dos tablas en la propuesta de cambios).

Uso:  python src/resumen_ejemplos.py              # tabla en Markdown
      python src/resumen_ejemplos.py --huellas    # solo «nombre huella», una línea por punto
"""

from __future__ import annotations

import hashlib
import json
import sys

import pandas as pd

import informe_local as I
import perfil_horario as P
from movimiento import nivel_movimiento
from recomendaciones import recomendar

# Los mismos puntos que EJEMPLOS en app/app.py
# (coordenadas de docs/registro/2026-11-10-informe-local-parte-a.md).
EJEMPLOS = {
    "Campus de Vicálvaro": (40.4046, -3.6106),
    "Centro de Fuenlabrada": (40.283366, -3.800132),
    "Plaza Mayor de Griñón": (40.212861, -3.852623),
}


def _plano(x):
    """Convierte el resultado en algo que json sabe escribir siempre igual."""
    if isinstance(x, (pd.DataFrame, pd.Series)):
        return json.loads(x.to_json(orient="split", double_precision=10))
    if isinstance(x, dict):
        return {str(k): _plano(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)):
        return [_plano(v) for v in (sorted(x, key=str) if isinstance(x, set) else x)]
    if hasattr(x, "item") and not isinstance(x, (str, bytes)):   # números de numpy
        try:
            return x.item()
        except (ValueError, AttributeError):
            pass
    if isinstance(x, float):
        return round(x, 10)
    if x is None or isinstance(x, (str, int, bool)):
        return x
    return str(x)


def calcular(lat: float, lon: float) -> dict:
    perfil = P.perfil_horario(lat, lon)
    inf = I.informe_local(lat, lon, perfil=perfil)
    rec = recomendar(lat, lon, perfil=perfil, inf=inf)
    return {"perfil": perfil, "informe": inf, "rec": rec, "mov": nivel_movimiento(perfil)}


def huella(res: dict) -> str:
    texto = json.dumps(_plano(res), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def fila(nombre: str, res: dict) -> dict:
    bloques = {b["clave"]: b["datos"] for b in res["informe"]["bloques"]}
    lab = [r for r in res["rec"]["a_quien"]["recomendaciones"] if r.get("dia") == "laborable"]
    pesos = sorted((lab[0].get("pesos") or {}).items(), key=lambda kv: -kv[1]) if lab else []
    return {
        "Punto": nombre,
        "Movimiento": res["mov"]["nombre"],
        "Pasan en un laborable (≈)": f"{res['mov']['pasos_laborable']:,.0f}".replace(",", "."),
        "Clientes principales": ", ".join(f"{t} {100 * p:.0f} %" for t, p in pesos[:3]),
        "Locales en el radio": bloques["competencia"]["total"],
        "Precios": bloques["precios"]["gama_ajustada"]["gama"]["semana"],
        "Transporte": bloques["accesos"]["nivel"],
        "Huella": huella(res)[:12],
    }


def main(argv: list[str]) -> int:
    resultados = {n: calcular(*xy) for n, xy in EJEMPLOS.items()}
    if "--huellas" in argv:
        for n, r in resultados.items():
            print(f"{n}\t{huella(r)}")
        return 0
    filas = [fila(n, r) for n, r in resultados.items()]
    columnas = list(filas[0])
    print("| " + " | ".join(columnas) + " |")
    print("|" + "---|" * len(columnas))
    for f in filas:
        print("| " + " | ".join(str(f[c]) for c in columnas) + " |")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
