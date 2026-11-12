"""BARómetro: buscador de direcciones con CartoCiudad (IGN).

Lo usan la aplicación web (app/app.py) y el servidor MCP (mcp/servidor.py), con los mismos
filtros. La dirección se envía a CartoCiudad para situarla y no se guarda en ningún sitio.
Condiciones de uso y licencia (CC BY 4.0) en docs/fuentes.md.

    from direcciones import geocodificar, coordenadas
    candidatos = geocodificar("Plaza de la Constitución 1, Fuenlabrada")
    lat, lon = coordenadas(candidatos[0])

Solo usa la biblioteca estándar de Python.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

CARTOCIUDAD = "https://www.cartociudad.es/geocoder/api/geocoder"
AGENTE = "BARometro-datamad2026/0.1"

# Tipos de resultado que se aceptan. Se descartan «toponimo» y «poi»: son nombres de
# comercios y lugares que pueden incluir nombres de personas.
TIPOS_GEOCODER = {"portal", "callejero", "carretera", "poblacion", "municipio", "Codpost",
                  "codpost"}
ATRIBUCION_CARTOCIUDAD = ("Direcciones: CartoCiudad, IGN · CC BY 4.0 "
                          "[www.scne.es/productos.html#CartoCiudad]"
                          "(https://www.scne.es/productos.html#CartoCiudad)")


def _cartociudad(metodo: str, **params) -> object:
    q = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{CARTOCIUDAD}/{metodo}?{q}",
                                 headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def geocodificar(texto: str) -> list[dict]:
    """Candidatos de CartoCiudad para una dirección de la provincia de Madrid. La
    dirección se envía a CartoCiudad y no se guarda en ningún sitio."""
    datos = _cartociudad("candidates", q=texto, limit=10, provincia_filter="Madrid")
    out = []
    for c in datos or []:
        if c.get("type") not in TIPOS_GEOCODER:
            continue
        via = c.get("tip_via") if c.get("type") == "callejero" else None
        etiqueta = " ".join(x for x in (via, c.get("address")) if x)
        if c.get("muni") and c["muni"] not in etiqueta:
            etiqueta += f", {c['muni']}"
        out.append({"texto": etiqueta, "tipo": c["type"], "id": c.get("id"),
                    "q": c.get("address"), "lat": c.get("lat"), "lon": c.get("lng")})
    return out


def coordenadas(cand: dict) -> tuple[float, float] | None:
    """Las calles y poblaciones vienen sin coordenadas: se piden con «find»."""
    if cand["lat"] and cand["lon"]:
        return float(cand["lat"]), float(cand["lon"])
    d = _cartociudad("find", q=cand["q"], type=cand["tipo"], id=cand["id"])
    if isinstance(d, dict) and d.get("lat") and d.get("lng"):
        return float(d["lat"]), float(d["lng"])
    return None
