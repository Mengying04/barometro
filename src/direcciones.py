"""BARómetro: buscador de direcciones con CartoCiudad (IGN).

Lo usan la aplicación web (app/app.py) y el servidor MCP (mcp/servidor.py), con los mismos
filtros. La dirección se envía a CartoCiudad para situarla y no se guarda en ningún sitio.
Condiciones de uso y licencia (CC BY 4.0) en docs/fuentes.md.

    from direcciones import geocodificar, coordenadas
    candidatos = geocodificar("Plaza de la Constitución 1, Fuenlabrada")
    lat, lon = coordenadas(candidatos[0])
    candidatos[0]["exacto"]   # True solo si es un portal con número

Una calle sin número, una localidad, un municipio o un código postal no son un punto
concreto: quien llama debe pedir el número o que el usuario confirme el sitio en el mapa
antes de calcular.

Solo usa la biblioteca estándar de Python.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request

CARTOCIUDAD = "https://www.cartociudad.es/geocoder/api/geocoder"
AGENTE = "BARometro-datamad2026/0.1"

# Tipos de resultado que se aceptan. Se descartan «toponimo» y «poi»: son nombres de
# comercios y lugares que pueden incluir nombres de personas.
TIPOS_GEOCODER = {"portal", "callejero", "carretera", "poblacion", "municipio", "Municipio",
                  "Codpost", "codpost"}
# Precisión de cada resultado. Solo un portal con número es un punto concreto: lo demás
# (una calle entera, una localidad, un municipio, un código postal) es una zona, y
# CartoCiudad devuelve un punto cualquiera de ella (el centro de la calle, por ejemplo).
PRECISION = {"portal": "portal", "callejero": "calle", "carretera": "calle",
             "poblacion": "localidad", "municipio": "municipio", "Municipio": "municipio",
             "Codpost": "codigo_postal", "codpost": "codigo_postal"}
PRECISION_TEXTO = {"portal": "portal exacto", "calle": "calle entera, sin número",
                   "localidad": "localidad entera", "municipio": "municipio entero",
                   "codigo_postal": "código postal entero"}
AVISO_NO_EXACTO = ("No es un punto concreto: las coordenadas son un punto cualquiera de la "
                   "zona. No calcules con ellas sin confirmar el sitio exacto (pide el "
                   "número del portal).")
_PARTICULAS = {"de", "del", "la", "las", "los", "el", "y", "e", "en", "a", "al"}
ATRIBUCION_CARTOCIUDAD = ("Direcciones: CartoCiudad, IGN · CC BY 4.0 "
                          "[www.scne.es/productos.html#CartoCiudad]"
                          "(https://www.scne.es/productos.html#CartoCiudad)")


def _cartociudad(metodo: str, **params) -> object:
    q = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{CARTOCIUDAD}/{metodo}?{q}",
                                 headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def _mayusculas_normales(texto: str) -> str:
    """«PLAZA CONSTITUCION 1» → «Plaza Constitucion 1». Las palabras con cifras o guiones
    (M-404) y las letras sueltas de un portal (1 A) se dejan en mayúsculas."""
    out, palabras = [], texto.split()
    for i, p in enumerate(palabras):
        tras_numero = i > 0 and any(c.isdigit() for c in palabras[i - 1])
        if any(c.isdigit() for c in p) or "-" in p or (len(p) == 1 and tras_numero):
            out.append(p.upper())
        elif (p.lower() in _PARTICULAS and 0 < i < len(palabras) - 1
              and palabras[i + 1][:1].isalpha()):   # «Calle A 3» no es una partícula
            out.append(p.lower())
        else:   # la primera letra (no un paréntesis) en mayúscula
            k = next((j for j, c in enumerate(p) if c.isalpha()), 0)
            out.append(p[:k] + p[k:k + 1].upper() + p[k + 1:].lower())
    return " ".join(out)


def _limpiar_via(via: str, tipo_via: str | None) -> str:
    """Nombre de una vía tal como lo da CartoCiudad, arreglado para leerlo: sin el tipo de
    vía repetido («PASEO PASEO»), con el artículo en su sitio («MARTIRES (DE LOS)» →
    «de los Mártires») y con mayúsculas normales."""
    via = re.sub(r"\s+", " ", via).strip()
    tv = (tipo_via or "").strip()
    while tv and via.upper().startswith(f"{tv.upper()} {tv.upper()} "):
        via = via[len(tv) + 1:]
    if tv and not via.upper().startswith(tv.upper() + " ") and via.upper() != tv.upper():
        via = f"{tv} {via}"
    m = re.search(r"\s*\(([^)]*)\)", via)
    if m and tv and all(p.lower() in _PARTICULAS for p in m.group(1).split()):
        resto = (via[:m.start()] + via[m.end():])[len(tv):].strip()
        via = f"{tv} {m.group(1)} {resto}"
    return _mayusculas_normales(via)


def _etiqueta(c: dict) -> str:
    """Texto que se enseña de un candidato, con el municipio siempre a la vista."""
    tipo, muni = PRECISION[c["type"]], (c.get("muni") or "").strip()
    direccion = (c.get("address") or "").strip()
    if tipo == "codigo_postal":
        return f"Código postal {direccion}" + (f", {muni}" if muni else "")
    if tipo == "municipio":
        return f"{muni or direccion.split(',')[0]} (municipio)"
    if tipo == "localidad":
        nombre = (c.get("poblacion") or direccion.split(",")[0]).strip()
        return (f"{nombre} (localidad)" if not muni or nombre == muni
                else f"{nombre} (localidad), {muni}")
    via, coma, lugar = direccion.rpartition(", ")
    if not coma:
        via, lugar = direccion, ""
    etiqueta = _limpiar_via(via, c.get("tip_via"))
    if lugar:
        etiqueta += f", {lugar}"
    if muni and muni not in lugar:
        etiqueta += f", {muni}"
    return etiqueta


def geocodificar(texto: str) -> list[dict]:
    """Candidatos de CartoCiudad para una dirección de la provincia de Madrid, con los
    portales exactos primero. La dirección se envía a CartoCiudad y no se guarda en
    ningún sitio.

    Cada candidato trae «precision» (portal, calle, localidad, municipio o
    codigo_postal) y «exacto»: solo es True en un portal con número. Con lo demás no se
    debe calcular sin que el usuario confirme el sitio."""
    datos = _cartociudad("candidates", q=texto, limit=10, provincia_filter="Madrid")
    out, vistos = [], set()
    for c in datos or []:
        if c.get("type") not in TIPOS_GEOCODER:
            continue
        precision = PRECISION[c["type"]]
        exacto = precision == "portal" and c.get("portalNumber") is not None
        if precision == "portal" and not exacto:   # un «portal» sin número es la calle
            precision = "calle"
        etiqueta = _etiqueta(c)
        if (etiqueta, precision) in vistos:
            continue
        vistos.add((etiqueta, precision))
        out.append({"texto": etiqueta, "tipo": c["type"], "precision": precision,
                    "precision_texto": PRECISION_TEXTO[precision], "exacto": exacto,
                    "id": c.get("id"), "q": c.get("address"),
                    "lat": c.get("lat"), "lon": c.get("lng")})
    return sorted(out, key=lambda c: not c["exacto"])   # orden estable: portales primero


def texto_candidato(c: dict) -> str:
    """Etiqueta para una lista: la dirección y, si no es un portal, qué es."""
    return c["texto"] if c["exacto"] else f"{c['texto']} · {c['precision_texto']}"


def coordenadas(cand: dict) -> tuple[float, float] | None:
    """Las calles y poblaciones vienen sin coordenadas: se piden con «find»."""
    if cand["lat"] and cand["lon"]:
        return float(cand["lat"]), float(cand["lon"])
    d = _cartociudad("find", q=cand["q"], type=cand["tipo"], id=cand["id"])
    if isinstance(d, dict) and d.get("lat") and d.get("lng"):
        return float(d["lat"]), float(d["lng"])
    return None
