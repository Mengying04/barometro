"""Descarga las fuentes externas que complementan al Portal de la Comunidad de Madrid.

Cada fuente va a su carpeta en datos/originales/ y se anota en docs/fuentes.md
(bloque «externas», sin tocar el bloque del portal):

  1. ine_adrh/            INE, Atlas de distribución de renta de los hogares,
                          provincia de Madrid (tablas 31097 renta y 31105 indicadores
                          demográficos, que incluye la población). Serie completa.
  1b. ine_seccionado/    INE, cartografía de secciones censales (seccionado a 1 de enero
                          del año que corresponde a los datos de renta).
  2. madrid_censo_locales/ Ayuntamiento de Madrid, censo de locales, actividades y
                          terrazas de hostelería y restauración (CSV + PDF de estructura).
  3. osm_hosteleria/      OpenStreetMap vía Overpass: bares, pubs, cafeterías,
                          restaurantes y comida rápida de la Comunidad de Madrid.
  4. crtm_paradas/        Consorcio Regional de Transportes: estaciones de Metro (capa de
                          red, GeoJSON WGS84) y feeds GTFS de Metro Ligero, Cercanías,
                          autobuses interurbanos, urbanos de Madrid (EMT) y urbanos de
                          otros municipios.

Uso:  python src/descargar_externas.py [ine ine_secc madrid osm crtm]
      (sin argumentos descarga las cuatro)
Solo usa la biblioteca estándar de Python.
"""

from __future__ import annotations

import csv
import io
import json
import sys
import zipfile
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


# ------------------------------------------------------- INE: cartografía de secciones
# Año del seccionado: el Atlas de renta con datos de 2024 usa las secciones vigentes a
# 1 de enero de 2025 (comprobado el 2026-11-09: casan las 4.518 secciones de Madrid con
# datos; con el seccionado de 2024 quedarían 45 sin polígono).
INE_SECCIONADO = 2025


def fuente_ine_seccionado(informe: dict) -> dict:
    carpeta = DIR_ORIGINALES / "ine_seccionado"
    carpeta.mkdir(parents=True, exist_ok=True)
    nombre = f"seccionado_{INE_SECCIONADO}.zip"
    url = f"https://www.ine.es/prodyser/cartografia/{nombre}"
    print(f"  · {nombre} ...", end=" ", flush=True)
    tam = descargar(url, carpeta / nombre, timeout=600)
    with zipfile.ZipFile(carpeta / nombre) as zf:
        if zf.testzip():
            raise RuntimeError(f"{nombre}: ZIP dañado")
        shp = [n for n in zf.namelist() if n.lower().endswith(".shp")]
    if len(shp) != 1:
        raise RuntimeError(f"{nombre}: se esperaba un .shp y hay {shp}")
    (carpeta / "capa.txt").write_text(shp[0] + "\n", encoding="utf-8")
    print(f"{tam / 1e6:.1f} MB")
    informe["descargados"].append(f"ine_seccionado/{nombre} ({tam / 1e6:.1f} MB)")
    return {
        "carpeta": "ine_seccionado",
        "titulo": f"INE. Cartografía digitalizada de secciones censales, seccionado a 1 de "
                  f"enero de {INE_SECCIONADO} (toda España)",
        "enlace": "https://www.ine.es/ss/Satellite?L=es_ES&c=Page&cid=1259952026632"
                  "&p=1259952026632&pagename=ProductosYServicios%2FPYSLayout "
                  f"(fichero {url})",
        "licencia": "Reutilización libre citando la fuente: «Fuente: Instituto Nacional "
                    "de Estadística (INE)» ([aviso legal](https://www.ine.es/aviso_legal))",
        "version": f"Seccionado a 1 de enero de {INE_SECCIONADO}",
        "ficheros": [f"{nombre}: shapefile `{shp[0]}` (ETRS89 / UTM 30N, EPSG:25830); "
                     "capa.txt: ruta del .shp dentro del ZIP"],
        "notas": [f"Se usa el seccionado de {INE_SECCIONADO} y no el de {INE_SECCIONADO - 1} "
                  "porque es el que corresponde a los datos del Atlas de renta de "
                  f"{INE_SECCIONADO - 1}: casan todas las secciones de Madrid con datos.",
                  "Uso: polígonos de las secciones para la renta y la población del INE "
                  "(capa `secciones_censales` procesada). Los límites de la Comunidad y de "
                  "los municipios se toman de las secciones del portal de la Comunidad."],
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
ARCGIS_ITEMS = "https://www.arcgis.com/sharing/rest/content/items"

# Metro: la capa (junio 2026) es más reciente que su GTFS (mayo 2025), así que se usa la capa.
CRTM_CAPAS = [  # (servicio, capa, fichero, descripción)
    ("M4_Red", 0, "metro_estaciones", "Metro: estaciones (capa de red)"),
]
# Resto de modos: feeds GTFS del portal datos.crtm.es (ficheros de ArcGIS Online).
CRTM_GTFS = [  # (id del item, fichero, descripción, ficha en datos.crtm.es)
    ("aaed26cc0ff64b0c947ac0bc3e033196", "gtfs_metro_ligero.zip", "Metro Ligero / Tranvía",
     "gtfs-red-de-metro-ligero"),
    ("1a25440bf66f499bae2657ec7fb40144", "gtfs_cercanias.zip", "Cercanías (producido por Renfe)",
     "gtfs-red-de-cercanías"),
    ("885399f83408473c8d815e40c5e702b7", "gtfs_interurbanos.zip", "Autobuses interurbanos",
     "gtfs-red-de-autobuses-interurbanos"),
    ("868df0e58fca47e79b942902dffd7da0", "gtfs_emt.zip", "Autobuses urbanos de Madrid (EMT)",
     "gtfs-red-de-emt"),
    ("357e63c2904f43aeb5d8a267a64346d8", "gtfs_urbanos.zip",
     "Autobuses urbanos de otros municipios (el CRTM avisa: «datos parciales»)",
     "gtfs-red-de-autobuses-urbanos"),
]
# Ficheros de versiones anteriores de este script que ya no se usan
CRTM_OBSOLETOS = ["metro_ligero_estaciones", "cercanias_estaciones", "interurbanos_estaciones",
                  "interurbanos_postes", "emt_estaciones", "emt_postes", "urbanos_estaciones",
                  "urbanos_postes"]


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


def _resumen_gtfs(ruta: Path) -> dict:
    """Comprueba el ZIP y extrae datos básicos (paradas, vigencia, versión)."""
    with zipfile.ZipFile(ruta) as zf:
        roto = zf.testzip()
        if roto:
            raise RuntimeError(f"{ruta.name}: fichero dañado dentro del ZIP ({roto})")
        nombres = {Path(n).name: n for n in zf.namelist() if not n.endswith("/")}
        faltan = {"stops.txt", "routes.txt", "trips.txt", "stop_times.txt"} - set(nombres)
        if faltan:
            raise RuntimeError(f"{ruta.name}: no es un GTFS completo, faltan {sorted(faltan)}")

        def leer(nombre):
            with zf.open(nombres[nombre]) as f:
                return list(csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")))

        paradas = leer("stops.txt")
        tipos: dict[str, int] = {}
        for x in paradas:
            t = (x.get("location_type") or "0").strip() or "0"
            tipos[t] = tipos.get(t, 0) + 1
        sin_coord = sum(1 for x in paradas if not x.get("stop_lat") or not x.get("stop_lon"))
        vigencia = "?"
        if "calendar.txt" in nombres:
            cal = leer("calendar.txt")
            if cal:
                vigencia = (f"{min(c['start_date'] for c in cal)}–"
                            f"{max(c['end_date'] for c in cal)}")
        version = None
        if "feed_info.txt" in nombres:
            fi = leer("feed_info.txt")
            version = fi[0].get("feed_version") if fi else None
        return {"paradas": len(paradas), "tipos": tipos, "sin_coord": sin_coord,
                "lineas": len(leer("routes.txt")), "vigencia": vigencia, "version": version}


def fuente_crtm(informe: dict) -> dict:
    carpeta = DIR_ORIGINALES / "crtm_paradas"
    carpeta.mkdir(parents=True, exist_ok=True)
    ficheros, metas, versiones = [], {}, []

    for servicio, capa, nombre, desc in CRTM_CAPAS:
        url = f"{CRTM_BASE}/{servicio}/FeatureServer/{capa}"
        print(f"  · {nombre} ...", end=" ", flush=True)
        n, meta = _descargar_capa(url, carpeta / f"{nombre}.geojson")
        metas[nombre] = {"url": url, **meta}
        ed = _fecha_ms((meta.get("editingInfo") or {}).get("lastEditDate"))
        versiones.append(f"{nombre}: capa editada el {ed}")
        ficheros.append(f"{nombre}.geojson ({desc}): {_fmt(n)} estaciones")
        informe["descargados"].append(f"crtm_paradas/{nombre}.geojson ({n} elementos)")
        print(n)
    _guardar_json(metas, carpeta / "metadatos_capas.json")

    items = {}
    for item_id, nombre, desc, ficha in CRTM_GTFS:
        print(f"  · {nombre} ...", end=" ", flush=True)
        item = _json(f"{ARCGIS_ITEMS}/{item_id}?f=json")
        items[nombre] = item
        destino = carpeta / nombre
        tam = descargar(f"{ARCGIS_ITEMS}/{item_id}/data", destino, timeout=600)
        if item.get("size") and item["size"] != tam:
            raise RuntimeError(f"{nombre}: {tam} B descargados ≠ {item['size']} B del item")
        r = _resumen_gtfs(destino)
        if r["sin_coord"]:
            informe["avisos"].append(f"crtm_paradas/{nombre}: {r['sin_coord']} paradas sin "
                                     "coordenadas")
        tipos = ", ".join(f"location_type {k}: {_fmt(v)}" for k, v in sorted(r["tipos"].items()))
        ficheros.append(f"{nombre} ({desc}; original `{item.get('name')}`): "
                        f"{_fmt(r['paradas'])} registros en stops.txt ({tipos}), "
                        f"{_fmt(r['lineas'])} líneas, calendario {r['vigencia']}")
        versiones.append(f"{nombre}: publicado el {_fecha_ms(item.get('modified'))}"
                         + (f", feed_version {r['version']}" if r["version"] else ""))
        informe["descargados"].append(f"crtm_paradas/{nombre} ({tam / 1e6:.1f} MB, "
                                      f"{r['paradas']} paradas)")
        print(f"{tam / 1e6:.1f} MB, {r['paradas']} paradas")
    _guardar_json(items, carpeta / "metadatos_gtfs.json")

    for viejo in CRTM_OBSOLETOS:
        (carpeta / f"{viejo}.geojson").unlink(missing_ok=True)

    return {
        "carpeta": "crtm_paradas",
        "titulo": "Consorcio Regional de Transportes de Madrid (CRTM): estaciones y paradas "
                  "de Metro, Metro Ligero, Cercanías y autobuses interurbanos y urbanos",
        "enlace": "Portal de datos abiertos del CRTM, https://datos.crtm.es/ — Metro: ficha "
                  "«Datos abiertos: Elementos de la Red de Metro» (capa "
                  f"{CRTM_BASE}/M4_Red/FeatureServer/0); resto: fichas GTFS "
                  + ", ".join(f"https://datos.crtm.es/datasets/crtm::{f}"
                              for _, _, _, f in CRTM_GTFS)
                  + f" (ficheros servidos desde {ARCGIS_ITEMS}/<id>/data)",
        "licencia": "[Licencia de datos abiertos y estáticos del CRTM]"
                    "(https://www.crtm.es/licencia-de-uso): uso comercial y no comercial. "
                    "Obligaciones: mostrar **«Powered by CRTM»** con enlace a "
                    "[crtm.es](http://www.crtm.es/) en webs y apps; **garantizar que la "
                    "información mostrada esté siempre actualizada** (volver a ejecutar este "
                    "script); citar al CRTM como fuente indicando si son datos en bruto o "
                    "explotados; conservar los metadatos de fecha de actualización; no "
                    "sugerir que el CRTM patrocina o apoya el producto",
        "version": "; ".join(versiones),
        "ficheros": ficheros + ["metadatos_capas.json, metadatos_gtfs.json: metadatos "
                                "originales (fechas de actualización, que la licencia obliga "
                                "a conservar)"],
        "notas": [
            "Metro se toma de la capa de red porque su GTFS publicado (30/05/2025) es "
            "anterior a la capa (junio de 2026). Coordenadas de la capa en WGS84 (EPSG:4326).",
            "Los GTFS se guardan completos, sin descomprimir. Las paradas están en "
            "`stops.txt` (`stop_lat`/`stop_lon`, WGS84). `location_type`: 0 = parada o andén, "
            "1 = estación, 2 = acceso; vacío equivale a 0.",
            "gtfs_interurbanos.zip y gtfs_urbanos.zip comparten el mismo `stops.txt` (paradas "
            "de las dos redes juntas); lo que cambia son las líneas y los horarios. Para saber "
            "qué paradas usa cada red hay que cruzar `stop_times.txt` y `trips.txt`.",
            "El calendario del GTFS de Cercanías solo cubre unas semanas: hay que volver a "
            "descargarlo con frecuencia.",
        ],
    }


# ------------------------------------------------------------------------- principal
FUENTES = {"ine": fuente_ine, "ine_secc": fuente_ine_seccionado, "madrid": fuente_madrid, "osm": fuente_osm, "crtm": fuente_crtm}
ORDEN_CARPETAS = ["ine_adrh", "ine_seccionado", "madrid_censo_locales", "osm_hosteleria", "crtm_paradas"]
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
