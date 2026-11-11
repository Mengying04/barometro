"""BARómetro: genera las tablas de datos del README a partir de docs/fuentes.md.

Los títulos, enlaces, licencias y fechas se leen de docs/fuentes.md (no se escriben a
mano). Lo único que se define aquí es para qué usa la aplicación cada conjunto del
portal (USO): un conjunto que no esté en USO no se usa y no sale en la tabla.

Uso:  python src/tablas_readme.py            # muestra las tablas
      python src/tablas_readme.py --escribir  # las sustituye en README.md, entre las
                                              # marcas <!-- inicio:… --> y <!-- fin:… -->
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Para qué sirve en BARómetro cada conjunto del portal de la Comunidad de Madrid.
USO = {
    "centros_educativos": "Dónde están los colegios e institutos: padres y niños que "
                          "pasan a la entrada y a la salida",
    "spacm_estadisticas_alumnos": "Cuántos alumnos hay por municipio y enseñanza, para "
                                  "repartirlos entre los centros",
    "1925489": "Estudiantes de grado por universidad, para repartirlos entre los campus",
    "1925502": "Estudiantes de máster por universidad, para repartirlos entre los campus",
    "centros_servicios_establecimientos_sanitarios": "Pacientes que van a centros "
                                                     "sanitarios; código postal aproximado "
                                                     "del punto",
    "desfibriladores_externos_fuera_ambito_sanitario": "Sitios con mucha gente (grandes "
                                                       "centros de trabajo, instalaciones "
                                                       "deportivas, recintos) y su horario",
    "1923861": "Viajeros por estación de Cercanías, para ajustar las estaciones grandes",
    "secciones_censales": "Límites de la Comunidad y de los municipios",
    "gasto_por_subgrupo_gasto_3_digitos_coicop_epf_base_2006": "Gasto medio por persona en "
                                                               "bares y restaurantes",
    "ipc_base_2025": "Cuánto han subido los precios de la restauración y de los alimentos",
    "alojamientos_turisticos": "Alojamientos turísticos del código postal y del municipio",
    "declaraciones_actividad_viviendas_uso_turistico": "Viviendas de uso turístico "
                                                       "declaradas en el municipio",
    "festivos_regionales_locales": "Festivos regionales y locales próximos",
    "demografia_empresarial_cnae09": "Evolución de las empresas del sector hasta 2025",
    "demografia_empresarial_cnae25": "Altas y bajas de empresas del sector en 2026",
}


def bloque(texto: str, clave: str) -> str:
    m = re.search(rf"<!-- inicio:{clave} -->(.*?)<!-- fin:{clave} -->", texto, re.S)
    return m.group(1) if m else ""


def tabla_portal(fuentes: str) -> str:
    filas = {}
    for linea in bloque(fuentes, "portal").splitlines():
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        m = re.match(r"\[([^\]]+)\]\(([^)]+)\)", celdas[1]) if len(celdas) == 6 else None
        if m:
            filas[m.group(1)] = (celdas[0], m.group(2), celdas[3])
    faltan = [c for c in USO if c not in filas]
    if faltan:
        raise SystemExit(f"Conjuntos de USO que no están en docs/fuentes.md: {faltan}")
    out = ["| Conjunto del portal | Para qué sirve en BARómetro | Última modificación |",
           "|---|---|---|"]
    for ident, uso in USO.items():
        titulo, enlace, fecha = filas[ident]
        out.append(f"| [{titulo}]({enlace}) | {uso} | {fecha} |")
    return "\n".join(out)


def tabla_otras(fuentes: str) -> str:
    out = ["| Fuente | Licencia | Descarga |", "|---|---|---|"]
    for clave in ("externas", "aplicacion"):
        for trozo in re.split(r"\n### ", bloque(fuentes, clave))[1:]:
            titulo, _, resto = trozo.partition("\n")
            campos = dict(re.findall(r"- \*\*([^:*]+):\*\*\s*(.+)", resto))
            licencia = re.split(r"\. |: |; ", campos.get("Licencia", "?"))[0].rstrip(".")
            licencia = licencia[0].upper() + licencia[1:]
            enlace = re.search(r"https?://[^\s)]+", campos.get("Enlace", ""))
            nombre = f"[{titulo.strip()}]({enlace.group(0)})" if enlace else titulo.strip()
            fecha = campos.get("Fecha de descarga", "?").split(";")[0].split(" (")[0]
            out.append(f"| {nombre} | {licencia} | {fecha} |")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    fuentes = (RAIZ / "docs" / "fuentes.md").read_text(encoding="utf-8")
    tablas = {"tabla-portal": tabla_portal(fuentes), "tabla-otras": tabla_otras(fuentes)}
    if "--escribir" not in argv:
        print("\n\n".join(tablas.values()))
        return 0
    ruta = RAIZ / "README.md"
    readme = ruta.read_text(encoding="utf-8")
    for clave, tabla in tablas.items():
        patron = rf"(<!-- inicio:{clave} -->).*?(<!-- fin:{clave} -->)"
        if not re.search(patron, readme, re.S):
            raise SystemExit(f"README.md no tiene las marcas de {clave}")
        readme = re.sub(patron, lambda m: f"{m.group(1)}\n{tabla}\n{m.group(2)}", readme,
                        flags=re.S)
    ruta.write_text(readme, encoding="utf-8")
    print("README.md actualizado")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
