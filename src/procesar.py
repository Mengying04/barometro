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

RAIZ = Path(__file__).resolve().parent.parent
ORIG = RAIZ / "datos" / "originales"
PROC = RAIZ / "datos" / "procesados"
CRS = 25830
ANYO_INE = "2024"          # último año del Atlas de renta descargado
ANYO_INE_REF = "2021"      # último año en que casi todos los códigos INE casan con 2019

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


def recortar(gdf: gpd.GeoDataFrame, secciones: gpd.GeoDataFrame,
             capa: str) -> gpd.GeoDataFrame:
    """Deja solo los puntos dentro de la Comunidad y les añade sección y municipio."""
    j = gpd.sjoin(gdf, secciones[["cdgseccion", "cod_municipio", "geometry"]],
                  how="left", predicate="intersects")
    j = j[~j.index.duplicated(keep="first")]          # puntos en el borde de dos secciones
    fuera = j["cdgseccion"].isna()
    descartar(capa, "fuera de la Comunidad de Madrid", int(fuera.sum()))
    return j[~fuera].drop(columns="index_right")


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
def secciones_censales() -> gpd.GeoDataFrame:
    capa = "secciones_censales"
    s = gpd.read_file(f"zip://{ORIG / 'secciones_censales' / '558.zip'}!Seccionado_2019.shp")
    n = len(s)
    if s.crs.to_epsg() != CRS:
        s = s.to_crs(CRS)
    invalidas = int((~s.is_valid).sum())
    s["geometry"] = shapely.make_valid(s.geometry.values)
    informe.setdefault(capa, {})["notas"] = [f"{invalidas} polígono(s) inválido(s) reparado(s)"]

    # CDGSECCION («079-12-062») está completo; CDTSECCION falta en 106 polígonos.
    s["cod8"] = s["CDGSECCION"].str.replace("-", "", regex=False)
    s["cdgseccion"] = "28" + s["cod8"]
    s["cod_municipio"] = "28" + s["cod8"].str[:3]
    s["cod_distrito"] = "28" + s["cod8"].str[:5]
    assert s["cdgseccion"].is_unique and s["cdgseccion"].str.len().eq(10).all()

    csv = leer_csv(ORIG / "secciones_censales" / "secciones_censales.csv")
    csv = csv[["seccion_codigo", "municipio_nombre"]].rename(columns={"seccion_codigo": "cod8"})
    s = s.merge(csv, on="cod8", how="left")

    # INE: «2807912062 Madrid sección 12062» → código de 10 dígitos
    def ine(tabla: str, indicadores: dict[str, str]) -> pd.DataFrame:
        d = leer_csv(ORIG / "ine_adrh" / f"{tabla}.csv")
        d = d[d["Secciones"].notna() & d["Periodo"].isin([ANYO_INE, ANYO_INE_REF])]
        col = d.columns[3]
        d = d[d[col].isin(indicadores)]
        d["cdgseccion"] = d["Secciones"].str.split(" ").str[0]
        d["valor"] = num_es(d["Total"])
        d["campo"] = d[col].map(indicadores) + "_" + d["Periodo"]
        return d.pivot_table(index="cdgseccion", columns="campo", values="valor",
                             aggfunc="first")

    renta = ine("31097", {"Renta neta media por persona": "renta_neta_persona",
                          "Renta neta media por hogar": "renta_neta_hogar"})
    pobl = ine("31105", {"Población": "poblacion"})
    datos = renta.join(pobl, how="outer")
    codigos_ine = set(datos.index[datos.get(f"poblacion_{ANYO_INE}").notna()])
    s = s.merge(datos, left_on="cdgseccion", right_index=True, how="left")

    s["tiene_datos_ine"] = s[[f"renta_neta_persona_{ANYO_INE}", f"renta_neta_hogar_{ANYO_INE}",
                              f"poblacion_{ANYO_INE}"]].notna().any(axis=1)

    # Secciones posiblemente divididas después de 2019: el distrito tiene códigos INE de
    # 2024 sin polígono en 2019 y la población del código cae más de un 25 % desde 2021.
    nuevos = codigos_ine - set(s["cdgseccion"])
    distritos_nuevos = {c[:7] for c in nuevos}
    ratio = s[f"poblacion_{ANYO_INE}"] / s[f"poblacion_{ANYO_INE_REF}"]
    s["posible_division_desde_2019"] = s["cod_distrito"].isin(distritos_nuevos) & (ratio < 0.75)

    s["area_km2"] = (s.area / 1e6).round(4)
    s = s.rename(columns={f"renta_neta_persona_{ANYO_INE}": "renta_neta_persona",
                          f"renta_neta_hogar_{ANYO_INE}": "renta_neta_hogar",
                          f"poblacion_{ANYO_INE}": "poblacion"})
    s["poblacion"] = s["poblacion"].round().astype("Int64")
    s["anyo_ine"] = int(ANYO_INE)

    sin = int((~s["tiene_datos_ine"]).sum())
    informe[capa]["notas"] += [
        f"Emparejamiento: «28» + CDGSECCION sin guiones = código de 10 dígitos del INE. "
        f"{len(s) - sin} de {len(s)} polígonos con datos {ANYO_INE}; "
        f"{sin} sin datos ({100 * sin / len(s):.1f} %).",
        f"{len(nuevos)} códigos INE {ANYO_INE} con datos no tienen polígono (secciones "
        f"creadas después de 2019) en {len(distritos_nuevos)} distritos; sus datos no se usan.",
        f"{int(s['posible_division_desde_2019'].sum())} polígonos marcados como posible "
        f"división desde 2019 (estimación).",
        f"Población {ANYO_INE} total en polígonos: {int(s['poblacion'].sum()):,}; "
        f"en todos los códigos INE: {int(datos[f'poblacion_{ANYO_INE}'].sum()):,}"
        .replace(",", "."),
    ]
    guardar(s, capa, ["cdgseccion", "cod_municipio", "municipio_nombre", "cod_distrito",
                      "renta_neta_persona", "renta_neta_hogar", "poblacion", "anyo_ine",
                      "tiene_datos_ine", "posible_division_desde_2019", "area_km2"], n,
            "polígonos")
    return s[["cdgseccion", "cod_municipio", "geometry"]]


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


def centros_educativos(secc: gpd.GeoDataFrame) -> None:
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
    g = recortar(g, secc, capa)
    guardar(g, capa, ["codigo", "tipo_centro", "tipo_original", "titularidad",
                      "municipio_nombre", "distrito", "cod_municipio", "cdgseccion"], n)


# ---------------------------------------------------------------------- 2. sanitarios
def centros_sanitarios(secc: gpd.GeoDataFrame) -> None:
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
    informe.setdefault(capa, {})["notas"] = [
        f"{n} filas (una por servicio) agrupadas en {n_centros} centros por "
        f"`centro_nro_registro`; `servicios` separa los servicios con « | ».",
        f"{incoh} centros con tipo o coordenadas distintos entre sus filas "
        "(se toma el primero).",
        "No se conserva la dirección postal ni el NIF; el original no trae nombre del centro.",
    ]
    g = a_puntos(agg, agg["x"], agg["y"], capa=capa)
    g = recortar(g, secc, capa)
    guardar(g, capa, ["centro_nro_registro", "centro_tipo", "dependencia_funcional",
                      "servicios", "n_servicios", "municipio_nombre", "codigo_postal",
                      "cod_municipio", "cdgseccion"], n_centros, "centros")


# ------------------------------------------------------------------- 3. desfibriladores
def desfibriladores(secc: gpd.GeoDataFrame) -> None:
    capa = "desfibriladores"
    d = leer_csv(ORIG / "desfibriladores_externos_fuera_ambito_sanitario"
                 / "desfibriladores_externos_fuera_ambito_sanitario.csv")
    n = len(d)
    dup = d.duplicated()
    descartar(capa, "fila duplicada exacta", int(dup.sum()))
    d = d[~dup]
    g = a_puntos(d, num(d["direccion_coordenada_x"]), num(d["direccion_coordenada_y"]),
                 capa=capa)
    g = recortar(g, secc, capa)
    rep = int(g["codigo_dea"].duplicated(keep=False).sum())
    informe.setdefault(capa, {})["notas"] = [
        "`horario_acceso` se deja tal cual viene (texto libre, sin normalizar).",
        "No se conserva `direccion_ubicacion` (texto libre que a veces nombra empresas o "
        "personas) ni la dirección postal.",
    ] + ([f"{rep} filas comparten `codigo_dea` con otra distinta (se conservan)."]
         if rep else [])
    guardar(g, capa, ["codigo_dea", "tipo_establecimiento", "tipo_titularidad",
                      "horario_acceso", "municipio_nombre", "cod_municipio", "cdgseccion"], n)


# ---------------------------------------------------------------------- 4. farmacias
def farmacias(secc: gpd.GeoDataFrame) -> None:
    capa = "farmacias"
    d = leer_csv(ORIG / "oficinas_farmacia" / "oficinas_farmacia.csv")
    n = len(d)
    d = d.rename(columns={"MUNICIPIO_NOMBRE": "municipio_nombre"})
    g = a_puntos(d, num(d["LOCALIZACION_COORDENADA_X"]), num(d["LOCALIZACION_COORDENADA_Y"]),
                 capa=capa)
    g = recortar(g, secc, capa)
    guardar(g, capa, ["municipio_nombre", "cod_municipio", "cdgseccion"], n)


# -------------------------------------------------------------------- 6. hostelería OSM
def hosteleria_osm(secc: gpd.GeoDataFrame) -> None:
    capa = "hosteleria_osm"
    elementos = json.loads((ORIG / "osm_hosteleria" / "osm_hosteleria.json")
                           .read_text(encoding="utf-8"))["elements"]
    n = len(elementos)
    filas = []
    for e in elementos:
        t = e.get("tags", {})
        c = e if "lat" in e else e.get("center", {})
        filas.append({"osm_tipo": e["type"], "osm_id": e["id"], "tipo": t.get("amenity"),
                      "cocina": t.get("cuisine"), "lon": c.get("lon"), "lat": c.get("lat")})
    d = pd.DataFrame(filas)
    g = a_puntos(d.drop(columns=["lat", "lon"]), d["lon"], d["lat"], crs=4326, capa=capa)
    g = recortar(g, secc, capa)
    informe.setdefault(capa, {})["notas"] = [
        "`tipo` = etiqueta amenity (restaurant, bar, cafe, fast_food, pub). `cocina` = "
        "etiqueta cuisine tal cual (puede llevar varios valores separados por «;»).",
        "Vías y relaciones (edificios) se representan por su punto central.",
        "No se conserva el nombre del local ni etiquetas de contacto.",
    ]
    guardar(g, capa, ["osm_tipo", "osm_id", "tipo", "cocina", "cod_municipio",
                      "cdgseccion"], n, "elementos")


# ------------------------------------------------------- 7. hostelería Madrid capital
CATEGORIA_CNAE = {"561": "restauración", "562": "catering y comedores colectivos",
                  "563": "bares y establecimientos de bebidas"}


def hosteleria_madrid(secc: gpd.GeoDataFrame) -> None:
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
    informe.setdefault(capa, {})["notas"] = [
        "Hostelería y restauración = división CNAE 56 (servicios de comidas y bebidas): "
        "`categoria` distingue restauración (561), catering y comedores colectivos (562) y "
        "bares (563). No incluye alojamiento (55) ni discotecas (93).",
        "Coordenadas: " + ", ".join(f"{k} {v}" for k, v in
                                    loc["origen_coordenadas"].fillna("sin coordenadas")
                                    .value_counts().items()) + ".",
        f"`tiene_terraza`: terraza en situación «Abierta» en el fichero de terrazas. "
        f"{ter_fuera} id_local del fichero de terrazas no están entre los locales "
        "de hostelería abiertos.",
        "No se conserva el rótulo (puede ser un nombre de persona).",
    ]
    g = a_puntos(loc, x, y, capa=capa)
    g = recortar(g, secc, capa)
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
              "- Recorte a la Comunidad de Madrid con la unión de las secciones censales; "
              "cada punto lleva `cdgseccion` (10 dígitos, como el INE) y `cod_municipio`.",
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
        "- `secciones_censales.posible_division_desde_2019`: se marca una sección de 2019 "
        "cuando su distrito tiene códigos INE de 2024 sin polígono (secciones nuevas) y su "
        "población cae más de un 25 % entre 2021 y 2024. Supuesto: esa caída se debe a que "
        "parte de la sección pasó a otra nueva, así que sus datos de 2024 solo cubren una "
        "parte del polígono.",
        "- `hosteleria_madrid_capital.origen_coordenadas = \"edificio (estimación)\"`: el "
        "local no tiene coordenadas propias y se le asigna la media de los demás locales del "
        "mismo edificio (mismo `id_ndp_edificio`, es decir, el mismo número de portal).",
        "",
    ]
    actualizar_bloque("procesados", lineas)


def main() -> int:
    print("Procesando…")
    secc = secciones_censales()
    for f in (centros_educativos, centros_sanitarios, desfibriladores, farmacias,
              hosteleria_osm, hosteleria_madrid):
        f(secc)
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
