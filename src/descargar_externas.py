"""Descarga las fuentes externas que complementan al Portal de la Comunidad de Madrid.

Cada fuente va a su carpeta en datos/originales/ y se anota en docs/fuentes.md
(bloque «externas», sin tocar el bloque del portal):

  1. ine_adrh/            INE, Atlas de distribución de renta de los hogares,
                          provincia de Madrid (tablas 31097 renta y 31105 indicadores
                          demográficos, que incluye la población). Serie completa.
  2. madrid_censo_locales/ Ayuntamiento de Madrid, censo de locales, actividades y
                          terrazas de hostelería y restauración (CSV + PDF de estructura).
  3. osm_hosteleria/      OpenStreetMap vía Overpass: bares, pubs, cafeterías,
                          restaurantes y comida rápida de la Comunidad de Madrid.
  4. crtm_paradas/        Consorcio Regional de Transportes: estaciones de Metro, Metro
                          Ligero y Cercanías; estaciones y postes (paradas) de autobuses
                          interurbanos, urbanos de Madrid (EMT) y urbanos de otros
                          municipios. GeoJSON en WGS84.

Uso:  python src/descargar_externas.py [ine madrid osm crtm]
      (sin argumentos descarga las cuatro)
Solo usa la biblioteca estándar de Python.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
from datetime import date, datetime, timezone
from pathlib import Path

from descargar_datos import (DIR_ORIGINALES, Bloqueado, _abrir, actualizar_bloque,
                             contar_filas_csv, descargar)


def _fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _json(url: str, datos: bytes | None = None, timeout: int = 120):
    with _abrir(url, datos, timeout) as r:
        return json.load(r)


def _fecha_ms(ms) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date().isoformat() if ms else "?"


def _guardar_json(obj, ruta: Path) -> None:
    ruta.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- INE
INE_TABLAS = {
    31097: "Indicadores de renta media y mediana",
    31105: "Indicadores demográficos",
}
INE_OPERACION = 353  # Atlas de distribución de renta de los hogares (ADRH)


def fuente_ine(informe: dict) -> dict:
    carpeta = DIR_ORIGINALES / "ine_adrh"
    carpeta.mkdir(parents=True, exist_ok=True)
    tablas = {t["Id"]: t for t in _json(
        f"https://servicios.ine.es/wstempus/js/ES/TABLAS_OPERACION/{INE_OPERACION}")
        if t["Id"] in INE_TABLAS}
    _guardar_json(list(tablas.values()), carpeta / "ficha_tablas.json")

    ficheros, anyos, modif = [], set(), set()
    for tid, nombre in INE_TABLAS.items():
        destino = carpeta / f"{tid}.csv"
        tam = descargar(f"https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/{tid}.csv", destino)
        texto = destino.read_text(encoding="utf-8-sig", errors="replace")
        # Comprobación: la primera serie debe ser de un municipio de Madrid (código 28xxx)
        if not texto.split("\n", 2)[1].startswith("28"):
            informe["avisos"].append(f"ine_adrh/{tid}.csv: no parece de la provincia de Madrid")
        anyos |= {l.rsplit(";", 2)[1] for l in texto.splitlines()[1:] if l.count(";") >= 2}
        n = contar_filas_csv(destino)
        ficheros.append(f"{tid}.csv ({nombre}): {_fmt(n)} filas")
        modif.add(_fecha_ms(tablas.get(tid, {}).get("Ultima_Modificacion")))
        informe["descargados"].append(f"ine_adrh/{tid}.csv ({tam / 1e6:.1f} MB, {n} filas)")
    anyos = sorted(a for a in anyos if a.isdigit())
    return {
        "carpeta": "ine_adrh",
        "titulo": "INE. Atlas de distribución de renta de los hogares (ADRH), "
                  "provincia de Madrid, por municipio, distrito y sección censal",
        "enlace": "https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C"
                  "&cid=1254736177088&idp=1254735976608",
        "licencia": "Reutilización libre citando la fuente: «Fuente: Instituto Nacional "
                    "de Estadística (INE)» ([aviso legal](https://www.ine.es/aviso_legal))",
        "version": f"Años {anyos[0]}–{anyos[-1]} (último disponible: **{anyos[-1]}**); "
                   f"tablas actualizadas el {', '.join(sorted(modif))}",
        "ficheros": ficheros,
        "notas": ["Se descarga la serie completa; el análisis usará el último año. "
                  "La población está en la tabla 31105, indicador «Población».",
                  "Los valores usan coma decimal y punto de miles; «..» o vacío = "
                  "dato no disponible (secreto estadístico)."],
    }


# ------------------------------------------------------------- Ayuntamiento de Madrid
MADRID_DATASET = "200085-0-censo-locales"
MADRID_RECURSOS = {"Locales", "Actividades", "Terrazas"}  # nombres en la descripción


def fuente_madrid(informe: dict) -> dict:
    carpeta = DIR_ORIGINALES / "madrid_censo_locales"
    carpeta.mkdir(parents=True, exist_ok=True)
    ficha = _json(f"https://datos.madrid.es/api/3/action/package_show?id={MADRID_DATASET}")
    ficha = ficha["result"]
    _guardar_json(ficha, carpeta / "ficha.json")

    ficheros = []
    for r in ficha["resources"]:
        desc = (r.get("description") or "").strip()
        formato = (r.get("format") or "").upper()
        # CSV pedidos y sus PDF de estructura (no el del fichero «con licencias»)
        if not ((formato == "CSV" and desc in MADRID_RECURSOS)
                or (formato == "PDF" and "licencia" not in desc.lower())):
            continue
        nombre = urllib.parse.unquote(Path(urllib.parse.urlsplit(r["url"]).path).name)
        if formato == "CSV":
            nombre = f"{desc.lower()}.csv"  # el nombre original lleva fecha y cambia a diario
        destino = carpeta / nombre
        print(f"  · {formato:4} {nombre} ...", end=" ", flush=True)
        tam = descargar(r["url"], destino, timeout=300)
        if r.get("size") and abs(r["size"] - tam) > max(1024, 0.01 * r["size"]):
            informe["avisos"].append(
                f"madrid_censo_locales/{nombre}: {tam} B ≠ {r['size']} B declarados")
        if formato == "CSV":
            n = contar_filas_csv(destino)
            ficheros.append(f"{nombre} ({desc}; original "
                            f"`{Path(urllib.parse.urlsplit(r['url']).path).name}`): "
                            f"{_fmt(n)} filas")
            print(f"{tam / 1e6:.1f} MB, {n} filas")
        else:
            ficheros.append(f"{nombre} ({desc})")
            print(f"{tam / 1e6:.1f} MB")
        informe["descargados"].append(f"madrid_censo_locales/{nombre} ({tam / 1e6:.1f} MB)")
    return {
        "carpeta": "madrid_censo_locales",
        "titulo": ficha["title"],
        "enlace": f"https://datos.madrid.es/dataset/{MADRID_DATASET}",
        "licencia": f"{ficha.get('license_title')}. Citar: «Fuente: Ayuntamiento de Madrid»",
        "version": f"Actualización diaria; ficheros del {ficha.get('metadata_modified', '?')[:10]}",
        "ficheros": ficheros,
        "notas": ["No se descargan las copias JSON/XML (mismo contenido) ni el fichero "
                  "«Locales con información de licencia»."],
    }


# ---------------------------------------------------------------------- OpenStreetMap
OVERPASS = "https://overpass-api.de/api/interpreter"
OSM_COMUNIDAD = 349055  # relación «Comunidad de Madrid» (admin_level=4)
OSM_AMENITIES = ["bar", "pub", "cafe", "restaurant", "fast_food"]
OSM_CONSULTA = f"""[out:json][timeout:600];
area({3600000000 + OSM_COMUNIDAD})->.cm;
nwr["amenity"~"^({'|'.join(OSM_AMENITIES)})$"](area.cm);
out center tags;"""


def fuente_osm(informe: dict) -> dict:
    carpeta = DIR_ORIGINALES / "osm_hosteleria"
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "consulta.overpassql").write_text(OSM_CONSULTA + "\n", encoding="utf-8")
    destino = carpeta / "osm_hosteleria.json"
    datos = urllib.parse.urlencode({"data": OSM_CONSULTA}).encode()
    tam = descargar(OVERPASS, destino, datos=datos, timeout=660)
    res = json.loads(destino.read_text(encoding="utf-8"))
    if res.get("remark"):  # Overpass avisa aquí de timeouts o límites de memoria
        raise RuntimeError(f"Overpass devolvió un aviso (datos incompletos): {res['remark']}")
    elementos = res["elements"]
    por_tipo: dict[str, int] = {}
    for e in elementos:
        a = e.get("tags", {}).get("amenity", "?")
        por_tipo[a] = por_tipo.get(a, 0) + 1
    con_cocina = sum(1 for e in elementos if "cuisine" in e.get("tags", {}))
    sin_coord = sum(1 for e in elementos if "lat" not in e and "center" not in e)
    if sin_coord:
        informe["avisos"].append(f"osm_hosteleria: {sin_coord} elementos sin coordenadas")
    fecha_osm = res.get("osm3s", {}).get("timestamp_osm_base", "?")
    informe["descargados"].append(f"osm_hosteleria/osm_hosteleria.json ({tam / 1e6:.1f} MB, "
                                  f"{len(elementos)} elementos)")
    desglose = ", ".join(f"{k} {_fmt(v)}" for k, v in sorted(por_tipo.items(),
                                                              key=lambda x: -x[1]))
    return {
        "carpeta": "osm_hosteleria",
        "titulo": "OpenStreetMap: bares, pubs, cafeterías, restaurantes y comida rápida "
                  "de la Comunidad de Madrid (API Overpass)",
        "enlace": "https://www.openstreetmap.org/copyright",
        "licencia": "Open Database License (ODbL) 1.0. Citar: «© colaboradores de "
                    "OpenStreetMap» con enlace a https://www.openstreetmap.org/copyright",
        "version": f"Datos OSM a {fecha_osm}",
        "ficheros": [f"osm_hosteleria.json: {_fmt(len(elementos))} elementos ({desglose}); "
                     f"{_fmt(con_cocina)} con etiqueta `cuisine`",
                     "consulta.overpassql: consulta usada"],
        "notas": ["Se incluye `amenity=pub` porque en España muchos bares están etiquetados "
                  "así; se puede filtrar después.",
                  "Nodos con `lat`/`lon`; vías y relaciones con su punto central (`center`).",
                  "Una base de datos derivada que se publique debe mantener la licencia ODbL."],
    }


# -------------------------------------------------------------------------------- CRTM
CRTM_BASE = "https://services5.arcgis.com/UxADft6QPcvFyDU1/arcgis/rest/services"
CRTM_CAPAS = [  # (servicio, capa, fichero, descripción)
    ("M4_Red", 0, "metro_estaciones", "Metro: estaciones"),
    ("M10_Red", 0, "metro_ligero_estaciones", "Metro Ligero / Tranvía: estaciones"),
    ("M5_Red", 0, "cercanias_estaciones", "Cercanías: estaciones"),
    ("M8_Red", 0, "interurbanos_estaciones", "Autobuses interurbanos: estaciones (paradas)"),
    ("M8_Red", 1, "interurbanos_postes", "Autobuses interurbanos: postes"),
    ("M6_Red", 0, "emt_estaciones", "Autobuses urbanos de Madrid (EMT): estaciones (paradas)"),
    ("M6_Red", 1, "emt_postes", "Autobuses urbanos de Madrid (EMT): postes"),
    ("M9_Red", 0, "urbanos_estaciones",
     "Autobuses urbanos de otros municipios: estaciones (paradas)"),
    ("M9_Red", 1, "urbanos_postes", "Autobuses urbanos de otros municipios: postes"),
]


def _descargar_capa(url_capa: str, destino: Path) -> tuple[int, dict]:
    meta = _json(f"{url_capa}?f=json")
    esperado = _json(f"{url_capa}/query?where=1%3D1&returnCountOnly=true&f=json")["count"]
    paso = meta.get("maxRecordCount") or 1000
    features, offset = [], 0
    while True:
        q = urllib.parse.urlencode({"where": "1=1", "outFields": "*", "outSR": 4326,
                                    "f": "geojson", "orderByFields": "OBJECTID",
                                    "resultOffset": offset, "resultRecordCount": paso})
        lote = _json(f"{url_capa}/query?{q}", timeout=300)
        features += lote.get("features", [])
        offset += paso
        if not lote.get("properties", {}).get("exceededTransferLimit") and \
                not lote.get("exceededTransferLimit"):
            if len(lote.get("features", [])) < paso:
                break
    if len(features) != esperado:
        raise RuntimeError(f"{url_capa}: {len(features)} elementos ≠ {esperado} esperados")
    _guardar_json({"type": "FeatureCollection", "features": features}, destino)
    return len(features), meta


def fuente_crtm(informe: dict) -> dict:
    carpeta = DIR_ORIGINALES / "crtm_paradas"
    carpeta.mkdir(parents=True, exist_ok=True)
    ficheros, metas, ediciones = [], {}, set()
    for servicio, capa, nombre, desc in CRTM_CAPAS:
        url = f"{CRTM_BASE}/{servicio}/FeatureServer/{capa}"
        print(f"  · {nombre} ...", end=" ", flush=True)
        n, meta = _descargar_capa(url, carpeta / f"{nombre}.geojson")
        metas[nombre] = {"url": url, **meta}
        ed = (meta.get("editingInfo") or {}).get("lastEditDate")
        ediciones.add(_fecha_ms(ed))
        ficheros.append(f"{nombre}.geojson ({desc}): {_fmt(n)}")
        informe["descargados"].append(f"crtm_paradas/{nombre}.geojson ({n} elementos)")
        print(n)
    _guardar_json(metas, carpeta / "metadatos_capas.json")
    return {
        "carpeta": "crtm_paradas",
        "titulo": "Consorcio Regional de Transportes de Madrid (CRTM): estaciones y paradas "
                  "de Metro, Metro Ligero, Cercanías y autobuses interurbanos y urbanos",
        "enlace": "Portal de datos abiertos del CRTM, https://datos.crtm.es/ (fichas "
                  "«Datos abiertos: Elementos de la Red de …»; capas servidas desde "
                  f"{CRTM_BASE})",
        "licencia": "[Licencia de datos abiertos y estáticos del CRTM]"
                    "(https://www.crtm.es/licencia-de-uso): uso comercial y no comercial. "
                    "Obligaciones: mostrar **«Powered by CRTM»** con enlace a "
                    "[crtm.es](http://www.crtm.es/) en webs y apps; **garantizar que la "
                    "información mostrada esté siempre actualizada** (volver a ejecutar este "
                    "script); citar al CRTM como fuente indicando si son datos en bruto o "
                    "explotados; conservar los metadatos de fecha de actualización; no "
                    "sugerir que el CRTM patrocina o apoya el producto",
        "version": f"Última edición de las capas: {', '.join(sorted(ediciones))}",
        "ficheros": ficheros,
        "notas": ["Coordenadas en WGS84 (EPSG:4326). «Estación» de autobús = parada lógica; "
                  "«poste» = punto físico de parada (puede haber varios por estación).",
                  "Comprobado el 2026-11-09 en el catálogo de datos.crtm.es "
                  "(https://datos.crtm.es/data.json): estas capas son las versiones vigentes "
                  "de las fichas de red (modificadas el 2026-06-04/05).",
                  "El portal publica también feeds GTFS más recientes (29/10/2026) para EMT, "
                  "autobuses interurbanos, autobuses urbanos («datos parciales»), Cercanías y "
                  "Metro Ligero; el GTFS de Metro es de 30/05/2025, anterior a su capa. "
                  "**Pendiente:** se descargan desde www.arcgis.com, bloqueada por el "
                  "cortafuegos del entorno el 2026-11-09."],
    }


# ------------------------------------------------------------------------- principal
FUENTES = {"ine": fuente_ine, "madrid": fuente_madrid, "osm": fuente_osm, "crtm": fuente_crtm}
ORDEN_CARPETAS = ["ine_adrh", "madrid_censo_locales", "osm_hosteleria", "crtm_paradas"]
ESTADO = DIR_ORIGINALES / ".fuentes_externas.json"  # para no perder las ya descargadas


def escribir_fuentes(entradas: dict) -> None:
    lineas = ["## Fuentes externas", "",
              "Descargadas con `src/descargar_externas.py` en `datos/originales/<carpeta>/`.",
              ""]
    for carpeta in ORDEN_CARPETAS:
        e = entradas.get(carpeta)
        if not e:
            continue
        lineas += [f"### {e['titulo']}", "",
                   f"- **Carpeta:** `datos/originales/{e['carpeta']}/`",
                   f"- **Enlace:** {e['enlace']}",
                   f"- **Licencia:** {e['licencia']}",
                   f"- **Fecha de descarga:** {e['fecha_descarga']}",
                   f"- **Versión de los datos:** {e['version']}",
                   "- **Ficheros:**"]
        lineas += [f"  - {f}" for f in e["ficheros"]]
        lineas += [f"- {n}" for n in e.get("notas", [])]
        lineas.append("")
    actualizar_bloque("externas", lineas)


def main(argv: list[str]) -> int:
    elegidas = argv or list(FUENTES)
    informe = {"descargados": [], "fallos": [], "avisos": [], "bloqueadas": set()}
    try:
        entradas = json.loads(ESTADO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        entradas = {}
    for clave in elegidas:
        print(f"\n{clave}")
        try:
            e = FUENTES[clave](informe)
        except Bloqueado as ex:
            informe["bloqueadas"].add(str(ex))
            informe["fallos"].append(f"{clave}: bloqueado por el cortafuegos ({ex})")
            continue
        except Exception as ex:
            informe["fallos"].append(f"{clave}: {ex}")
            continue
        e["fecha_descarga"] = date.today().isoformat()
        entradas[e["carpeta"]] = e
        ESTADO.write_text(json.dumps(entradas, ensure_ascii=False, indent=2), encoding="utf-8")
    escribir_fuentes(entradas)

    print("\n================ RESUMEN ================")
    print(f"Ficheros descargados: {len(informe['descargados'])}")
    for x in informe["descargados"]:
        print(f"  - {x}")
    for clave, titulo in [("fallos", "Fallos"), ("avisos", "Avisos")]:
        print(f"{titulo}: {len(informe[clave])}")
        for x in informe[clave]:
            print(f"  - {x}")
    print(f"Direcciones bloqueadas: {', '.join(sorted(informe['bloqueadas'])) or 'ninguna'}")
    return 1 if informe["fallos"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
