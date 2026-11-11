"""BARómetro: tablas pequeñas para el informe del local (datos/procesados/informe/).

src/informe_local.py necesita siete conjuntos del portal de la Comunidad de Madrid que no
son capas geográficas (gasto, IPC, alojamientos, viviendas de uso turístico, festivos y
demografía empresarial) y las fichas de sus fuentes. Este script copia de datos/originales
solo las filas y columnas que el informe usa, para que la aplicación funcione desde un
clon del repositorio sin descargar nada.

- No calcula ni cambia valores: filtra filas y elige columnas. Los nombres de las columnas
  y los textos se dejan como en el original, y el informe aplica sus filtros igual que antes.
- No se copian nombres de establecimientos ni direcciones: de los alojamientos solo se
  guarda el tipo, la localidad y el código postal; de las viviendas de uso turístico, la
  localidad.
- fuentes.json conserva, de cada fuente, el título, la licencia, la fecha de última
  modificación y la fecha de descarga (la del fichero original).

Uso:  python src/procesar_informe.py     (después de las descargas)
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from procesar import ORIG, PROC, leer_csv

SALIDA = PROC / "informe"

# Conjuntos del portal que cita el informe (ficha.json de cada uno).
CONJUNTOS = ["gasto_por_subgrupo_gasto_3_digitos_coicop_epf_base_2006", "ipc_base_2025",
             "alojamientos_turisticos", "declaraciones_actividad_viviendas_uso_turistico",
             "festivos_regionales_locales", "demografia_empresarial_cnae09",
             "demografia_empresarial_cnae25"]


def guardar(d: pd.DataFrame, nombre: str) -> None:
    d.to_csv(SALIDA / nombre, sep=";", index=False, encoding="utf-8")
    print(f"  {nombre}: {len(d)} filas, {len(d.columns)} columnas")


def unico_csv(carpeta: str) -> Path:
    return next((ORIG / carpeta).glob("*.csv"))


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)

    # Gasto de los hogares: solo el gasto por persona en restauración.
    g = leer_csv(unico_csv("gasto_por_subgrupo_gasto_3_digitos_coicop_epf_base_2006"))
    g = g[(g["Concepto"] == "Gasto medio por persona de los hogares en restauración")
          & (g["Medida"] == "Gasto medio persona")]
    guardar(g[["Año", "Concepto", "Medida", "Valor"]], "gasto_restauracion.csv")

    # IPC: tasas interanuales de la Comunidad de Madrid, todos los grupos y meses.
    i = leer_csv(unico_csv("ipc_base_2025"))
    i = i[(i["Territorio"] == "Comunidad de Madrid")
          & (i["Indicador"] == "Tasa de variación sobre igual periodo del año anterior")]
    guardar(i[["Año", "Periodo", "Territorio", "Grupo", "Indicador", "Valor"]], "ipc.csv")

    # Alojamientos turísticos: tipo, localidad y código postal. Sin nombre ni dirección.
    a = leer_csv(ORIG / "alojamientos_turisticos" / "alojamientos_turisticos.csv")
    guardar(a[["alojamiento_tipo", "cdpostal", "localidad"]], "alojamientos_turisticos.csv")

    # Viviendas de uso turístico con declaración responsable: solo la localidad.
    v = leer_csv(ORIG / "declaraciones_actividad_viviendas_uso_turistico"
                 / "declaraciones_actividad_viviendas_uso_turistico.csv")
    guardar(v[["Localidad"]], "viviendas_uso_turistico.csv")

    # Festivos locales y regionales del año en curso.
    loc = leer_csv(ORIG / "festivos_regionales_locales" / "festivos_locales.csv")
    guardar(loc[["municipio_codigo", "entidad_codigo", "entidad_nombre", "fecha_festivo"]],
            "festivos_locales.csv")
    reg = leer_csv(ORIG / "festivos_regionales_locales" / "festivos_regionales.csv")
    guardar(reg[["fecha_festivo", "festividad"]], "festivos_regionales.csv")

    # Demografía empresarial: serie de unidades empresariales por rama.
    for carpeta, col, nombre in (
            ("demografia_empresarial_cnae09", "CNAE2009", "demografia_cnae09.csv"),
            ("demografia_empresarial_cnae25", "CNAE2025", "demografia_cnae25.csv")):
        d = leer_csv(unico_csv(carpeta))
        d = d[(d["Concepto"] == "Unidades empresariales") & (d["Indicador"] == "Serie")]
        guardar(d[["Año", "Periodo", "Concepto", col, "Medida", "Indicador", "Valor"]], nombre)

    # Fichas de las fuentes: título, licencia y fechas (se conservan tal cual).
    portal = {}
    for c in CONJUNTOS:
        ruta = ORIG / c / "ficha.json"
        f = json.loads(ruta.read_text(encoding="utf-8"))
        portal[c] = {
            "title": f.get("title", c), "license_title": f.get("license_title"),
            "license_url": f.get("license_url"),
            "metadata_modified": f.get("metadata_modified"),
            "descargado": datetime.fromtimestamp(ruta.stat().st_mtime).date().isoformat()}
    externas = json.loads((ORIG / ".fuentes_externas.json").read_text(encoding="utf-8"))
    (SALIDA / "fuentes.json").write_text(
        json.dumps({"portal": portal, "externas": externas}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"  fuentes.json: {len(portal)} conjuntos del portal, {len(externas)} externas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
