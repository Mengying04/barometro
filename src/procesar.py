"""Limpia los datos de datos/originales y los guarda en datos/procesados como GeoParquet.

Reglas generales:
  - Geometría en EPSG:25830 (ETRS89 / UTM 30N, metros) y columnas lat/lon en EPSG:4326.
    Las coordenadas X/Y del portal, del censo del Ayuntamiento y de los desfibriladores
    vienen en ETRS89 (EPSG:25830); se comprobó con pruebas de distancia (ver docs/fuentes.md).
  - Se conservan solo columnas elegidas expresamente (lista blanca), sin nombres de
    titulares ni de establecimientos, NIF, teléfonos, faxes ni correos. Al final se
    comprueba que ninguna columna de salida tenga un nombre sospechoso.
  - Todo se recorta a la Comunidad de Madrid (unión de las secciones censales) y cada
    punto recibe el código de la sección censal en la que cae (`cdgseccion`, 10 dígitos
    como el INE) y el código de municipio.

Uso:  python src/procesar.py
"""

from __future__ import annotations

import io
import json
import re
import sys
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from descargar_datos import actualizar_bloque
from descargar_externas import INE_SECCIONADO

RAIZ = Path(__file__).resolve().parent.parent
ORIG = RAIZ / "datos" / "originales"
PROC = RAIZ / "datos" / "procesados"
CRS = 25830
ANYO_INE = "2024"          # último año del Atlas de renta descargado
# Los datos de renta de 2024 están referidos al seccionado del INE a 1 de enero de 2025
# (ver descargar_externas.INE_SECCIONADO).

# Columnas que nunca deben salir (por si una lista blanca se modifica sin cuidado)
PROHIBIDAS = re.compile(r"nif|tel[eé]f|fax|mail|titular(?!idad)|rotulo|r[oó]tulo|^name$|^nombre$"
                        r"|denominacion|^centro$|operator|contact|phone|ubicacion",
                        re.IGNORECASE)

informe: dict[str, dict] = {}


# ----------------------------------------------------------------------------- utilidades
def leer_csv(ruta: Path, **kw) -> pd.DataFrame:
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return pd.read_csv(ruta, sep=";", dtype=str, encoding=enc, **kw)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"No se pudo leer {ruta}")


def num(s: pd.Series) -> pd.Series:
    """Número con coma decimal (y sin separador de miles) → float."""
    return pd.to_numeric(s.str.strip().str.replace(",", ".", regex=False), errors="coerce")


def num_es(s: pd.Series) -> pd.Series:
    """Número en formato español (punto de miles, coma decimal) → float."""
    s = s.fillna("").str.strip().str.replace(".", "", regex=False).str.replace(",", ".")
    return pd.to_numeric(s, errors="coerce")


def limpiar_texto(s: pd.Series) -> pd.Series:
    return s.str.strip().replace("", pd.NA)


def a_puntos(df: pd.DataFrame, x: pd.Series, y: pd.Series, crs: int = CRS,
             capa: str = "") -> gpd.GeoDataFrame:
    """Crea puntos y descarta los que no tienen coordenadas válidas."""
    validas = x.notna() & y.notna()
    if crs != 4326:                      # en UTM, 0 o negativo = coordenada vacía
        validas &= (x > 0) & (y > 0)
    descartar(capa, "sin coordenadas", int((~validas).sum()))
    gdf = gpd.GeoDataFrame(df[validas].copy(),
                           geometry=gpd.points_from_xy(x[validas], y[validas]), crs=crs)
    return gdf.to_crs(CRS)


def descartar(capa: str, motivo: str, n: int) -> None:
    if n:
        informe.setdefault(capa, {}).setdefault("descartes", {})
        informe[capa]["descartes"][motivo] = informe[capa]["descartes"].get(motivo, 0) + n


def recortar(gdf: gpd.GeoDataFrame, limites: gpd.GeoDataFrame, secc_ine: gpd.GeoDataFrame,
             capa: str) -> gpd.GeoDataFrame:
    """Deja solo los puntos dentro de la Comunidad (secciones del portal), les añade el
    municipio según el portal y la sección censal del INE en la que caen."""
    j = gpd.sjoin(gdf, limites[["cod_municipio", "geometry"]], how="left",
                  predicate="intersects")
    j = j[~j.index.duplicated(keep="first")].drop(columns="index_right")
    fuera = j["cod_municipio"].isna()
    descartar(capa, "fuera de la Comunidad de Madrid", int(fuera.sum()))
    j = j[~fuera]
    k = gpd.sjoin(j, secc_ine[["cdgseccion", "geometry"]], how="left", predicate="intersects")
    k = k[~k.index.duplicated(keep="first")].drop(columns="index_right")
    sin = int(k["cdgseccion"].isna().sum())
    otro_mun = int((k["cdgseccion"].notna()
                    & (k["cdgseccion"].str[:5] != k["cod_municipio"])).sum())
    notas = informe.setdefault(capa, {}).setdefault("notas", [])
    if sin:
        notas.append(f"{sin} puntos dentro de la Comunidad no caen en ningún polígono del "
                     "INE (diferencias de borde); quedan sin `cdgseccion`.")
    if otro_mun:
        notas.append(f"{otro_mun} puntos tienen una sección del INE de otro municipio que el "
                     "del portal (diferencias de borde entre las dos cartografías).")
    return k


def escribir_parquet(gdf: gpd.GeoDataFrame, destino: Path, intentos: int = 3) -> None:
    """Genera el GeoParquet en memoria y lo escribe con reintentos.

    En la carpeta compartida con el Mac, pyarrow falla a veces al escribir directamente
    («[Errno 14] Bad address»); escribir los bytes desde Python evita el problema."""
    buf = io.BytesIO()
    gdf.to_parquet(buf, index=False)
    datos = buf.getvalue()
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix(".parquet.part")
    for i in range(1, intentos + 1):
        try:
            tmp.write_bytes(datos)
            tmp.replace(destino)
            return
        except OSError:
            if i == intentos:
                raise
            time.sleep(1)


def guardar(gdf: gpd.GeoDataFrame, capa: str, columnas: list[str], n_origen: int,
            unidad: str = "filas") -> None:
    gdf = gdf.copy()
    puntos = gdf.geometry if gdf.geom_type.eq("Point").all() else gdf.representative_point()
    wgs = gpd.GeoSeries(puntos, crs=CRS).to_crs(4326)
    gdf["lon"], gdf["lat"] = wgs.x.round(6), wgs.y.round(6)
    gdf = gdf[columnas + ["lat", "lon", "geometry"]].reset_index(drop=True)
    malas = [c for c in gdf.columns if PROHIBIDAS.search(c)]
    if malas:
        raise RuntimeError(f"{capa}: columnas con posibles datos personales: {malas}")
    assert gdf.crs.to_epsg() == CRS
    escribir_parquet(gdf, PROC / f"{capa}.parquet")
    r = informe.setdefault(capa, {})
    r.update(origen=n_origen, unidad=unidad, final=len(gdf),
             columnas=[c for c in gdf.columns if c != "geometry"] + ["geometry"])
    print(f"  {capa}: {n_origen} {unidad} → {len(gdf)}")


# --------------------------------------------------------------------- 5. secciones
def limites_portal() -> gpd.GeoDataFrame:
    """Secciones del portal de la Comunidad (seccionado 2019): solo para los límites de la
    Comunidad y de los municipios."""
    s = gpd.read_file(f"zip://{ORIG / 'secciones_censales' / '558.zip'}!Seccionado_2019.shp")
    if s.crs.to_epsg() != CRS:
        s = s.to_crs(CRS)
    s["geometry"] = shapely.make_valid(s.geometry.values)
    # CDGSECCION («079-12-062») está completo; CDTSECCION falta en 106 polígonos.
    s["cod_municipio"] = "28" + s["CDGSECCION"].str[:3]
    return s[["cod_municipio", "geometry"]]


def leer_ine(tabla: str, indicadores: dict[str, str]) -> pd.DataFrame:
    """Atlas de renta: «2807912062 Madrid sección 12062» → código de 10 dígitos."""
    d = leer_csv(ORIG / "ine_adrh" / f"{tabla}.csv")
    d = d[d["Secciones"].notna() & (d["Periodo"] == ANYO_INE)]
    col = d.columns[3]
    d = d[d[col].isin(indicadores)]
    d["cdgseccion"] = d["Secciones"].str.split(" ").str[0]
    d["valor"] = num_es(d["Total"])
    d["campo"] = d[col].map(indicadores)
    return d.pivot_table(index="cdgseccion", columns="campo", values="valor", aggfunc="first")


def secciones_censales(limites: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    capa = "secciones_censales"
    carpeta = ORIG / "ine_seccionado"
    shp = (carpeta / "capa.txt").read_text(encoding="utf-8").strip()
    s = gpd.read_file(f"zip://{carpeta / f'seccionado_{INE_SECCIONADO}.zip'}!{shp}",
                      where="CPRO='28'")
    n = len(s)
    if s.crs.to_epsg() != CRS:
        s = s.to_crs(CRS)
    invalidas = int((~s.is_valid).sum())
    s["geometry"] = shapely.make_valid(s.geometry.values)
    s = s.rename(columns={"CUSEC": "cdgseccion", "CUMUN": "cod_municipio",
                          "NMUN": "municipio_nombre", "CUDIS": "cod_distrito"})
    assert s["cdgseccion"].is_unique and s["cdgseccion"].str.len().eq(10).all()

    # Recorte al límite de la Comunidad según el portal (diferencias de borde mínimas)
    area_antes = s.area.sum()
    limite = shapely.union_all(limites.geometry.values)
    s = gpd.clip(s, limite)
    s = s[~s.is_empty & s.geom_type.isin(["Polygon", "MultiPolygon"])]
    descartar(capa, "fuera de la Comunidad de Madrid", n - len(s))
    recorte = 100 * (1 - s.area.sum() / area_antes)

    # Municipio del portal en el que cae cada sección (comprobación)
    rp = gpd.GeoDataFrame(s[["cdgseccion", "cod_municipio"]],
                          geometry=s.representative_point(), crs=CRS)
    m = gpd.sjoin(rp, limites, how="left", predicate="intersects")
    m = m[~m.index.duplicated()]
    distinto = int((m["cod_municipio_left"] != m["cod_municipio_right"]).sum())

    renta = leer_ine("31097", {"Renta neta media por persona": "renta_neta_persona",
                               "Renta neta media por hogar": "renta_neta_hogar"})
    pobl = leer_ine("31105", {"Población": "poblacion"})
    datos = renta.join(pobl, how="outer")
    s = s.merge(datos, left_on="cdgseccion", right_index=True, how="left")
    s["tiene_datos_ine"] = s[["renta_neta_persona", "renta_neta_hogar", "poblacion"]] \
        .notna().any(axis=1)
    s["poblacion"] = s["poblacion"].round().astype("Int64")
    s["anyo_ine"] = int(ANYO_INE)
    s["seccionado"] = INE_SECCIONADO
    s["area_km2"] = (s.area / 1e6).round(4)

    con_dato = datos["poblacion"].dropna()
    sin_poligono = sorted(set(con_dato.index) - set(s["cdgseccion"]))
    sin = int((~s["tiene_datos_ine"]).sum())
    informe.setdefault(capa, {})["notas"] = informe.setdefault(capa, {}).get("notas", []) + [
        f"Polígonos: cartografía del INE, seccionado a 1 de enero de {INE_SECCIONADO} "
        f"({n} secciones de la provincia de Madrid); {invalidas} inválidos reparados.",
        f"Emparejamiento: `CUSEC` de la cartografía = código de 10 dígitos del Atlas de renta "
        f"(«2807912062 Madrid sección 12062»). {len(s) - sin} de {len(s)} polígonos con "
        f"datos {ANYO_INE}; {sin} sin datos ({100 * sin / len(s):.1f} %). "
        f"{len(sin_poligono)} secciones INE con datos sin polígono.",
        f"Población {ANYO_INE} en polígonos: {int(s['poblacion'].sum()):,}; total de las "
        f"secciones INE con dato: {int(con_dato.sum()):,}.".replace(",", "."),
        f"Recorte al límite de la Comunidad del portal: se pierde un {recorte:.3f} % del área "
        f"(diferencias de borde entre cartografías).",
        f"{distinto} secciones cuyo punto interior cae en otro municipio según el portal.",
    ]
    guardar(s, capa, ["cdgseccion", "cod_municipio", "municipio_nombre", "cod_distrito",
                      "renta_neta_persona", "renta_neta_hogar", "poblacion", "anyo_ine",
                      "seccionado", "tiene_datos_ine", "area_km2"], n, "polígonos")
    return s[["cdgseccion", "geometry"]]


# --------------------------------------------------------------------- 1. educativos
def tipo_educativo(t: str) -> str:
    t = t.upper()
    if "FORMACIÓN PROFESIONAL" in t or "FORMACION PROFESIONAL" in t:
        return "formación profesional"
    if "SECUNDARIA" in t:
        return "secundaria"
    if "PRIMARIA" in t:
        return "primaria"
    if "INFANTIL" in t or "CASA DE NIÑOS" in t or "CASAS DE NIÑOS" in t:
        return "infantil"
    return "otros"


def centros_educativos(lim: gpd.GeoDataFrame, secc: gpd.GeoDataFrame) -> None:
    capa = "centros_educativos"
    d = leer_csv(ORIG / capa / f"{capa}.csv")
    n = len(d)
    situ = d["SITUACIÓN"].str.strip()
    for v, k in situ[situ != "ALTA"].value_counts().items():
        descartar(capa, f"situación {v}", int(k))
    d = d[situ == "ALTA"]
    d["tipo_centro"] = d["TIPO_EXT"].map(tipo_educativo)
    d = d.rename(columns={"CODIGO": "codigo", "TIPO_EXT": "tipo_original",
                          "TITULARIDAD": "titularidad", "MUNICIPIO": "municipio_nombre",
                          "DISTRITO": "distrito"})
    g = a_puntos(d, num(d["UTM_X"]), num(d["UTM_Y"]), capa=capa)
    g = recortar(g, lim, secc, capa)
    guardar(g, capa, ["codigo", "tipo_centro", "tipo_original", "titularidad",
                      "municipio_nombre", "distrito", "cod_municipio", "cdgseccion"], n)


# ---------------------------------------------------------------------- 2. sanitarios
def centros_sanitarios(lim: gpd.GeoDataFrame, secc: gpd.GeoDataFrame) -> None:
    capa = "centros_sanitarios"
    d = leer_csv(ORIG / "centros_servicios_establecimientos_sanitarios"
                 / "centros_servicios_establecimientos_sanitarios.csv")
    n = len(d)
    n_centros = d["centro_nro_registro"].nunique()
    d["x"], d["y"] = num(d["localizacion_coordenada_x"]), num(d["localizacion_coordenada_y"])
    # ¿Algún centro con atributos distintos entre sus filas?
    var = d.groupby("centro_nro_registro")[["centro_tipo", "x", "y"]].nunique()
    incoh = int((var > 1).any(axis=1).sum())
    agg = d.groupby("centro_nro_registro").agg(
        centro_tipo=("centro_tipo", "first"),
        dependencia_funcional=("dependecia_funcional", "first"),
        municipio_nombre=("municipio_nombre", "first"),
        codigo_postal=("direccion_codigo_postal", "first"),
        x=("x", "first"), y=("y", "first"),
        servicios=("oferta_asistecial", lambda s: " | ".join(sorted(set(s.dropna())))),
        n_servicios=("oferta_asistecial", "nunique"),
    ).reset_index()
    informe.setdefault(capa, {})["notas"] = informe.setdefault(capa, {}).get("notas", []) + [
        f"{n} filas (una por servicio) agrupadas en {n_centros} centros por "
        f"`centro_nro_registro`; `servicios` separa los servicios con « | ».",
        f"{incoh} centros con tipo o coordenadas distintos entre sus filas "
        "(se toma el primero).",
        "No se conserva la dirección postal ni el NIF; el original no trae nombre del centro.",
    ]
    g = a_puntos(agg, agg["x"], agg["y"], capa=capa)
    g = recortar(g, lim, secc, capa)
    guardar(g, capa, ["centro_nro_registro", "centro_tipo", "dependencia_funcional",
                      "servicios", "n_servicios", "municipio_nombre", "codigo_postal",
                      "cod_municipio", "cdgseccion"], n_centros, "centros")


# ------------------------------------------------------------------- 3. desfibriladores
def desfibriladores(lim: gpd.GeoDataFrame, secc: gpd.GeoDataFrame) -> None:
    capa = "desfibriladores"
    d = leer_csv(ORIG / "desfibriladores_externos_fuera_ambito_sanitario"
                 / "desfibriladores_externos_fuera_ambito_sanitario.csv")
    n = len(d)
    dup = d.duplicated()
    descartar(capa, "fila duplicada exacta", int(dup.sum()))
    d = d[~dup]
    g = a_puntos(d, num(d["direccion_coordenada_x"]), num(d["direccion_coordenada_y"]),
                 capa=capa)
    g = recortar(g, lim, secc, capa)
    rep = int(g["codigo_dea"].duplicated(keep=False).sum())
    informe.setdefault(capa, {})["notas"] = informe.setdefault(capa, {}).get("notas", []) + [
        "`horario_acceso` se deja tal cual viene (texto libre, sin normalizar).",
        "No se conserva `direccion_ubicacion` (texto libre que a veces nombra empresas o "
        "personas) ni la dirección postal.",
    ] + ([f"{rep} filas comparten `codigo_dea` con otra distinta (se conservan)."]
         if rep else [])
    guardar(g, capa, ["codigo_dea", "tipo_establecimiento", "tipo_titularidad",
                      "horario_acceso", "municipio_nombre", "cod_municipio", "cdgseccion"], n)


# ---------------------------------------------------------------------- 4. farmacias
def farmacias(lim: gpd.GeoDataFrame, secc: gpd.GeoDataFrame) -> None:
    capa = "farmacias"
    d = leer_csv(ORIG / "oficinas_farmacia" / "oficinas_farmacia.csv")
    n = len(d)
    d = d.rename(columns={"MUNICIPIO_NOMBRE": "municipio_nombre"})
    g = a_puntos(d, num(d["LOCALIZACION_COORDENADA_X"]), num(d["LOCALIZACION_COORDENADA_Y"]),
                 capa=capa)
    g = recortar(g, lim, secc, capa)
    guardar(g, capa, ["municipio_nombre", "cod_municipio", "cdgseccion"], n)


# -------------------------------------------------------------------- 6. hostelería OSM
def hosteleria_osm(lim: gpd.GeoDataFrame, secc: gpd.GeoDataFrame) -> None:
    capa = "hosteleria_osm"
    elementos = json.loads((ORIG / "osm_hosteleria" / "osm_hosteleria.json")
                           .read_text(encoding="utf-8"))["elements"]
    n = len(elementos)
    filas = []
    for e in elementos:
        t = e.get("tags", {})
        c = e if "lat" in e else e.get("center", {})
        filas.append({"osm_tipo": e["type"], "osm_id": e["id"], "tipo": t.get("amenity"),
                      "cocina": t.get("cuisine"), "horario_osm": t.get("opening_hours"),
                      "comida_osm": t.get("food"), "lon": c.get("lon"), "lat": c.get("lat")})
    d = pd.DataFrame(filas)
    g = a_puntos(d.drop(columns=["lat", "lon"]), d["lon"], d["lat"], crs=4326, capa=capa)
    g = recortar(g, lim, secc, capa)
    informe.setdefault(capa, {})["notas"] = informe.setdefault(capa, {}).get("notas", []) + [
        "`tipo` = etiqueta amenity (restaurant, bar, cafe, fast_food, pub). `cocina` = "
        "etiqueta cuisine tal cual (puede llevar varios valores separados por «;»).",
        "Vías y relaciones (edificios) se representan por su punto central.",
        "`horario_osm` = etiqueta opening_hours tal cual (la tienen pocos locales); "
        "`comida_osm` = etiqueta food (casi nunca está).",
        "No se conserva el nombre del local ni etiquetas de contacto.",
    ]
    guardar(g, capa, ["osm_tipo", "osm_id", "tipo", "cocina", "horario_osm", "comida_osm",
                      "cod_municipio", "cdgseccion"], n, "elementos")


# ------------------------------------------------------- 7. hostelería Madrid capital
CATEGORIA_CNAE = {"561": "restauración", "563": "bares y establecimientos de bebidas"}


def hosteleria_madrid(lim: gpd.GeoDataFrame, secc: gpd.GeoDataFrame) -> None:
    capa = "hosteleria_madrid_capital"
    carpeta = ORIG / "madrid_censo_locales"
    a = leer_csv(carpeta / "actividades.csv", usecols=[
        "id_local", "desc_distrito_local", "desc_barrio_local", "coordenada_x_local",
        "coordenada_y_local", "coordenada_x_agrupacion", "coordenada_y_agrupacion",
        "id_ndp_edificio", "desc_situacion_local", "id_division", "id_epigrafe",
        "desc_epigrafe"])
    h = a[a["id_division"] == "56"]
    n = h["id_local"].nunique()
    abiertos = h["desc_situacion_local"].str.strip() == "Abierto"
    for v, k in h[~abiertos].drop_duplicates("id_local")["desc_situacion_local"] \
            .value_counts().items():
        descartar(capa, f"local {v.strip().lower()}", int(k))
    h = h[abiertos]

    # Fuera catering y comedores colectivos (CNAE 562): no compiten con un bar abierto al
    # público. Los locales que además tienen otra actividad de la división 56 se quedan,
    # sin el epígrafe 562.
    es_562 = h["id_epigrafe"].fillna("").str.startswith("562")
    con_publico = set(h.loc[~es_562, "id_local"])
    solo_562 = set(h.loc[es_562, "id_local"]) - con_publico
    mixtos = set(h.loc[es_562, "id_local"]) & con_publico
    descartar(capa, "solo catering o comedor colectivo (CNAE 562)", len(solo_562))
    h = h[~es_562]

    loc = h.groupby("id_local").agg(
        distrito=("desc_distrito_local", "first"), barrio=("desc_barrio_local", "first"),
        x=("coordenada_x_local", "first"), y=("coordenada_y_local", "first"),
        xa=("coordenada_x_agrupacion", "first"), ya=("coordenada_y_agrupacion", "first"),
        id_ndp_edificio=("id_ndp_edificio", "first"),
        epigrafes=("id_epigrafe", lambda s: " | ".join(sorted(set(s.dropna())))),
        desc_epigrafes=("desc_epigrafe", lambda s: " | ".join(sorted(set(s.dropna()
                                                                          .str.strip())))),
    ).reset_index()
    loc["n_epigrafes"] = loc["epigrafes"].str.count(r"\|") + 1
    loc["categoria"] = loc["epigrafes"].map(
        lambda e: " | ".join(sorted({CATEGORIA_CNAE.get(x[:3], "otros")
                                     for x in e.split(" | ")})))
    for c in ("distrito", "barrio"):
        loc[c] = limpiar_texto(loc[c])

    # Coordenadas: las del local; si faltan (=0), las de su agrupación (mercado, centro
    # comercial) o la media de los demás locales del mismo edificio (estimación).
    x, y = num(loc["x"]), num(loc["y"])
    loc["origen_coordenadas"] = np.where((x > 0) & (y > 0), "local", None)
    xa, ya = num(loc["xa"]), num(loc["ya"])
    usa_agr = loc["origen_coordenadas"].isna() & (xa > 0) & (ya > 0)
    x, y = x.where(~usa_agr, xa), y.where(~usa_agr, ya)
    loc.loc[usa_agr, "origen_coordenadas"] = "agrupación"

    todos = leer_csv(carpeta / "locales.csv", usecols=["id_ndp_edificio", "coordenada_x_local",
                                                       "coordenada_y_local"])
    todos["x"], todos["y"] = num(todos["coordenada_x_local"]), num(todos["coordenada_y_local"])
    edif = todos[(todos["x"] > 0) & (todos["y"] > 0)].groupby("id_ndp_edificio")[["x", "y"]] \
        .mean()
    falta = loc["origen_coordenadas"].isna()
    xe = loc["id_ndp_edificio"].map(edif["x"])
    ye = loc["id_ndp_edificio"].map(edif["y"])
    usa_edif = falta & xe.notna()
    x, y = x.where(~usa_edif, xe), y.where(~usa_edif, ye)
    loc.loc[usa_edif, "origen_coordenadas"] = "edificio (estimación)"
    x, y = x.where(loc["origen_coordenadas"].notna()), y.where(loc["origen_coordenadas"].notna())

    # Terrazas (una fila por terraza; un local puede tener varias)
    t = leer_csv(carpeta / "terrazas.csv", usecols=["id_local", "desc_situacion_terraza",
                                                    "desc_periodo_terraza"])
    ta = t[t["desc_situacion_terraza"].str.strip() == "Abierta"]
    per = ta.groupby("id_local")["desc_periodo_terraza"].agg(
        lambda s: " | ".join(sorted(set(s.str.strip()))))
    susp = set(t.loc[t["desc_situacion_terraza"].str.strip() != "Abierta", "id_local"])
    loc["tiene_terraza"] = loc["id_local"].isin(per.index)
    loc["terraza_periodo"] = loc["id_local"].map(per)
    loc["terraza_suspendida"] = loc["id_local"].isin(susp) & ~loc["tiene_terraza"]

    ter_fuera = len(set(t["id_local"]) - set(loc["id_local"]))
    informe.setdefault(capa, {})["notas"] = informe.setdefault(capa, {}).get("notas", []) + [
        "Hostelería y restauración = división CNAE 56 (servicios de comidas y bebidas) sin "
        "catering ni comedores colectivos (562), que no compiten con un bar abierto al "
        "público. `categoria` distingue restauración (561) y bares (563). No incluye "
        "alojamiento (55) ni discotecas (93).",
        f"{len(mixtos)} locales con catering o comedor colectivo y además otra actividad de "
        "hostelería se conservan, sin el epígrafe 562.",
        "Coordenadas: " + ", ".join(f"{k} {v}" for k, v in
                                    loc["origen_coordenadas"].fillna("sin coordenadas")
                                    .value_counts().items()) + ".",
        f"`tiene_terraza`: terraza en situación «Abierta» en el fichero de terrazas. "
        f"{ter_fuera} id_local del fichero de terrazas no están entre los locales "
        "de hostelería abiertos.",
        "No se conserva el rótulo (puede ser un nombre de persona).",
    ]
    g = a_puntos(loc, x, y, capa=capa)
    g = recortar(g, lim, secc, capa)
    guardar(g, capa, ["id_local", "categoria", "epigrafes", "desc_epigrafes", "n_epigrafes",
                      "tiene_terraza", "terraza_periodo", "terraza_suspendida",
                      "origen_coordenadas", "distrito", "barrio", "cod_municipio",
                      "cdgseccion"], n, "locales")


# -------------------------------------------------------------------------- principal
def escribir_fuentes() -> None:
    lineas = ["## Datos procesados", "",
              "Generados con `src/procesar.py` en `datos/procesados/<capa>.parquet` "
              "(GeoParquet, geometría en EPSG:25830 y columnas `lat`/`lon` en EPSG:4326).",
              "",
              "- Sistema de coordenadas de origen: las X/Y del portal (centros educativos, "
              "sanitarios, farmacias, desfibriladores) y del censo de locales están en "
              "ETRS89 / UTM 30N (EPSG:25830). Comprobado el 2026-11-09: los desfibriladores "
              "traen también lon/lat y coinciden a 0 m; con ED50 (EPSG:23030) habría ~234 m "
              "de desfase. Los demás se contrastaron por distancia al vecino más cercano "
              "(desfibriladores, OSM, farmacias del censo).",
              "- Dos cartografías de secciones censales, cada una con un uso:",
              "  - **Secciones del portal de la Comunidad** (`secciones_censales/558.zip`, "
              "seccionado 2019): límite de la Comunidad para recortar todas las capas y "
              "límites municipales (`cod_municipio` de cada punto).",
              f"  - **Cartografía del INE** (`ine_seccionado/`, seccionado a 1 de enero de "
              f"{INE_SECCIONADO}): polígonos de la capa `secciones_censales` con la renta y "
              f"la población del Atlas de renta de {ANYO_INE}, y `cdgseccion` de cada punto "
              "(sección del INE en la que cae, para cruzarlo con la renta).",
              "- No se conservan nombres de titulares ni de establecimientos, NIF, teléfonos, "
              "faxes ni correos.",
              "",
              "| Capa | Origen | Final | Descartes |",
              "|---|---|---|---|"]
    for capa, r in informe.items():
        desc = "; ".join(f"{k}: {v}" for k, v in r.get("descartes", {}).items()) or "—"
        lineas.append(f"| {capa} | {r['origen']:,} {r['unidad']} | {r['final']:,} | {desc} |"
                      .replace(",", "."))
    lineas.append("")
    for capa, r in informe.items():
        if r.get("notas"):
            lineas += [f"**{capa}**", ""] + [f"- {x}" for x in r["notas"]] + [""]
    lineas += [
        "**Estimaciones** (supuestos explícitos):",
        "",
        "- `hosteleria_madrid_capital.origen_coordenadas = \"edificio (estimación)\"`: el "
        "local no tiene coordenadas propias y se le asigna la media de los demás locales del "
        "mismo edificio (mismo `id_ndp_edificio`, es decir, el mismo número de portal).",
        "",
    ]
    actualizar_bloque("procesados", lineas)


def main() -> int:
    print("Procesando…")
    lim = limites_portal()
    secc = secciones_censales(lim)
    for f in (centros_educativos, centros_sanitarios, desfibriladores, farmacias,
              hosteleria_osm, hosteleria_madrid):
        f(lim, secc)
    escribir_fuentes()
    (PROC / "informe_procesado.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n================ RESUMEN ================")
    for capa, r in informe.items():
        print(f"\n{capa}: {r['origen']} {r['unidad']} → {r['final']}")
        for k, v in r.get("descartes", {}).items():
            print(f"  descartadas por {k}: {v}")
        for x in r.get("notas", []):
            print(f"  · {x}")
        print(f"  columnas: {', '.join(r['columnas'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
