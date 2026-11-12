"""BARómetro: lee las fuentes, enlaces, licencias y fechas de docs/fuentes.md.

Lo usan la aplicación web y el servidor MCP para citar las fuentes tal como están
anotadas, sin escribirlas a mano en otro sitio.

    from fuentes import leer_fuentes
    f = leer_fuentes()
    f["portal"]      # conjuntos del portal de la Comunidad de Madrid
    f["externas"]    # INE, Ayuntamiento de Madrid, OpenStreetMap y CRTM
    f["aplicacion"]  # servicios que se consultan en el momento (CartoCiudad, teselas)

Solo usa la biblioteca estándar de Python.
"""

from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def leer_fuentes() -> dict:
    """Fuentes, enlaces, licencias y fechas tal como están en docs/fuentes.md."""
    texto = (RAIZ / "docs" / "fuentes.md").read_text(encoding="utf-8")

    def bloque(clave):
        m = re.search(rf"<!-- inicio:{clave} -->(.*?)<!-- fin:{clave} -->", texto, re.S)
        return m.group(1) if m else ""

    portal = bloque("portal")
    descarga = re.search(r"Fecha de descarga:\s*([\d-]+)", portal)
    filas = []
    for linea in portal.splitlines():
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if len(celdas) == 6 and celdas[1].startswith("["):
            filas.append({"Conjunto": celdas[0], "Ficha": celdas[1], "Licencia": celdas[2],
                          "Última modificación": celdas[3]})

    def secciones(txt):
        out = []
        for trozo in re.split(r"\n### ", txt)[1:]:
            titulo, _, resto = trozo.partition("\n")
            campos = dict(re.findall(r"- \*\*([^:*]+):\*\*\s*(.+)", resto))
            out.append({"titulo": titulo.strip(), **campos})
        return out

    return {"portal": filas, "portal_descarga": descarga.group(1) if descarga else "?",
            "externas": secciones(bloque("externas")),
            "aplicacion": secciones(bloque("aplicacion"))}
