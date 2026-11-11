"""Prepara los datos del perfil por horas (src/perfil_horario.py).

Genera en datos/procesados/:
  1. centros_educativos_alumnos.parquet: cada centro educativo con sus alumnos
     ESTIMADOS por enseñanza. La estadística del portal da alumnos por municipio (por
     distrito en Madrid capital), enseñanza y titularidad; se reparten a partes iguales
     entre los centros de ese territorio que imparten esa enseñanza con esa titularidad.
  1b. campus_universitarios.parquet: campus de OpenStreetMap con los estudiantes de
     cada universidad (estadística del portal) repartidos entre sus campus.
  2. desfibriladores_horario.parquet: desfibriladores útiles para el perfil (centros de
     trabajo grandes, instalaciones deportivas, recintos…), con su horario de acceso
     normalizado y fusionados cuando son del mismo sitio.
  3. salidas_paradas.parquet: número de vehículos que pasan por cada parada en cada hora
     de un laborable típico y de un sábado típico, a partir de los GTFS del CRTM, y
     personas que suben o bajan por vehículo calibradas con la demanda real.

Todos los supuestos están en src/supuestos.py.

Uso:  python src/procesar_perfil.py [educativos universidades dea gtfs]
      (sin argumentos, todos; «dea» necesita antes «universidades»)
"""

from __future__ import annotations

import json
import math
import re
import sys
import unicodedata
import zipfile
from datetime import date, timedelta
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

import supuestos as S
from descargar_datos import actualizar_bloque
from procesar import CRS, ORIG, PROC, escribir_parquet, guardar, informe, leer_csv

HOY = date.today()


def sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").upper()


# ===================================================================== 1. EDUCATIVOS
ENSENANZAS = ["E. Infantil Primer Ciclo", "E. Infantil Segundo Ciclo", "E. Primaria",
              "E.S.O.", "Bachillerato", "C.F. Grado Básico", "C.F. Grado Medio",
              "C.F. Grado Superior", "Cursos Especialización", "Educación Especial"]


def col_ensenanza(e: str) -> str:
    return "alumnos_" + re.sub(r"[^a-z0-9]+", "_", sin_tildes(e).lower()).strip("_")


def ensenanzas_de(tipo: str) -> list[str]:
    t = tipo.upper()
    out: list[str] = []
    for palabras, ens in S.ENSENANZAS_POR_PALABRA:
        if all(p in t for p in palabras):
            out += [e for e in ens if e not in out]
    # «Escuela infantil» y «casa de niños» son de 0 a 3 años: no llevan segundo ciclo.
    if any(p in t for p in ("ESCUELA INFANTIL", "ESCUELA  INFANTIL", "CASA DE NIÑOS",
                            "CASAS DE NIÑOS")):
        out = ["E. Infantil Primer Ciclo"]
    # Los centros de música/danza «integrados» o de adultos no son de régimen general.
    if any(p in t for p in ("MÚSICA", "DANZA", "ADULTOS", "PERSONAS ADULTAS",
                            "EQUIPO DE ORIENTACIÓN", "ZONA CASAS")):
        out = []
    return out


def peso_tipico(tipo: str) -> tuple[int, str]:
    t = tipo.upper()
    for palabra, n, perfil in S.PESO_TIPICO_EDUCATIVO:
        if palabra in t:
            return n, perfil
    return S.PESO_TIPICO_EDUCATIVO_OTROS


def educativos() -> None:
    capa = "centros_educativos_alumnos"
    c = gpd.read_parquet(PROC / "centros_educativos.parquet")
    a = leer_csv(ORIG / "spacm_estadisticas_alumnos"
                 / "alumnos_regimen_general_por_titularidad_y_financiacion.csv")
    curso = a["CURSO_ACADEMICO"].max()
    a = a[a["CURSO_ACADEMICO"] == curso].copy()
    a["n"] = pd.to_numeric(a["DATO"], errors="coerce").fillna(0)
    # Territorio: municipio, salvo Madrid capital, que viene por distritos.
    madrid = a["ACOD_MUNICIPIO"] == "28079"
    assert (a.loc[madrid, "DISTRITO_MUNICIPAL"] != "-").all()
    a["territorio"] = np.where(madrid, a["DISTRITO_MUNICIPAL"].str[:7], a["ACOD_MUNICIPIO"])
    nombres_distrito = {sin_tildes(x.split("-", 1)[1]): x[:7]
                        for x in a.loc[madrid, "DISTRITO_MUNICIPAL"].unique()}
    total_csv = a["n"].sum()
    desconocidas = set(a["ENSENANZA"]) - set(ENSENANZAS)
    if desconocidas:
        raise RuntimeError(f"Enseñanzas no previstas en la estadística: {desconocidas}")

    es_madrid = c["cod_municipio"] == "28079"
    c["territorio"] = np.where(
        es_madrid, c["distrito"].fillna("").map(lambda x: nombres_distrito.get(sin_tildes(x))),
        c["cod_municipio"])
    sin_distrito = int((es_madrid & c["territorio"].isna()).sum())
    c["tit_alumnos"] = c["titularidad"].map(S.TITULARIDAD_ALUMNOS)
    c["ensenanzas"] = c["tipo_original"].map(ensenanzas_de)

    filas = c[["territorio", "tit_alumnos", "ensenanzas"]].explode("ensenanzas") \
        .dropna(subset=["ensenanzas"]).reset_index(names="i")
    for e in ENSENANZAS:
        c[col_ensenanza(e)] = 0.0
    no_asignado, por_respaldo = 0.0, 0.0
    for (terr, ens, tit), n in a.groupby(["territorio", "ENSENANZA", "TCENTRO"])["n"].sum() \
            .items():
        if n <= 0:
            continue
        cand = filas[(filas["territorio"] == terr) & (filas["ensenanzas"] == ens)]
        mismos = cand[cand["tit_alumnos"] == tit]
        if mismos.empty:
            mismos = cand  # ningún centro con esa titularidad: se reparte entre todos
            por_respaldo += n if not cand.empty else 0
        if mismos.empty:
            no_asignado += n
            continue
        c.loc[mismos["i"].unique(), col_ensenanza(ens)] += n / mismos["i"].nunique()

    cols = [col_ensenanza(e) for e in ENSENANZAS]
    c[cols] = c[cols].round(1)
    c["alumnos_regimen_general"] = c[cols].sum(axis=1).round(1)
    tip = c["tipo_original"].map(peso_tipico)
    sin_rg = c["alumnos_regimen_general"] == 0
    c["alumnos_otros"] = np.where(sin_rg, tip.str[0], 0).astype(float)
    c["perfil_otros"] = np.where(sin_rg, tip.str[1], None)
    c["origen_peso"] = np.where(~sin_rg, "estadística de alumnos repartida (estimación)",
                                np.where(c["alumnos_otros"] > 0,
                                         "peso típico por tipo de centro (supuesto)",
                                         "sin alumnos (supuesto)"))
    c["alumnos_estimados"] = c["alumnos_regimen_general"] + c["alumnos_otros"]

    pct = 100 * (total_csv - no_asignado) / total_csv
    informe.setdefault(capa, {})["notas"] = [
        f"Fuente de los alumnos: «Estadísticas de alumnos» del portal "
        f"(spacm_estadisticas_alumnos), curso {curso}, alumnos de régimen general por "
        "municipio (distrito en Madrid capital), enseñanza y titularidad.",
        "No hay un conjunto con alumnos por centro: cada total se reparte a partes "
        "iguales entre los centros del territorio que imparten esa enseñanza (según "
        "su tipo) y tienen esa titularidad (pública, concertada o privada). "
        "**Estimación**: un colegio grande y uno pequeño reciben lo mismo.",
        f"Alumnos asignados: {total_csv - no_asignado:,.0f} de {total_csv:,.0f} "
        f"({pct:.1f} %); {por_respaldo:,.0f} repartidos sin respetar la titularidad "
        "(no había centros de esa titularidad con esa enseñanza en el territorio)."
        .replace(",", "."),
        f"{int((~sin_rg).sum())} centros con alumnos de la estadística; "
        f"{int((sin_rg & (c['alumnos_otros'] > 0)).sum())} con peso típico por tipo "
        f"(idiomas, música, adultos…); {int((c['alumnos_estimados'] == 0).sum())} sin "
        "alumnos (equipos de orientación, oficinas).",
    ] + ([f"{sin_distrito} centros de Madrid capital sin distrito reconocible."]
         if sin_distrito else [])
    guardar(c, capa, ["codigo", "tipo_centro", "tipo_original", "titularidad",
                      "cod_municipio", "territorio", *cols, "alumnos_regimen_general",
                      "alumnos_otros", "perfil_otros", "alumnos_estimados", "origen_peso"],
            len(c), "centros")


# ================================================================= 1b. UNIVERSIDADES
# Cada universidad de la estadística: (patrón de su nombre en la estadística, patrón de
# nombre u operador en OpenStreetMap). Texto sin tildes y en mayúsculas.
UNIVERSIDADES = {
    "UCM": (r"COMPLUTENSE", r"COMPLUTENSE|\bUCM\b|CIUDAD UNIVERSITARIA"),
    "UPM": (r"POLITECNICA DE MADRID", r"UNIVERSIDAD POLITECNICA|\bUPM\b|MONTEGANCEDO"),
    "UAM": (r"AUTONOMA DE MADRID", r"AUTONOMA DE MADRID|\bUAM\b|CANTOBLANCO"),
    "UAH": (r"DE ALCALA", r"ALCALA|\bUAH\b"),
    "UC3M": (r"CARLOS III", r"CARLOS III|UC3M"),
    "URJC": (r"REY JUAN CARLOS", r"REY JUAN CARLOS|\bURJC\b"),
    "Comillas": (r"COMILLAS", r"COMILLAS|ICADE|\bICAI\b"),
    "CEU": (r"\bCEU\b", r"\bCEU\b"),
    "UEM": (r"EUROPEA DE MADRID", r"UNIVERSIDAD EUROPEA"),
    "UFV": (r"FRANCISCO DE VITORIA", r"FRANCISCO DE VITORIA"),
    "Nebrija": (r"NEBRIJA", r"NEBRIJA"),
    "UCJC": (r"CAMILO JOSE CELA", r"CAMILO JOSE CELA|\bUCJC\b"),
    "UAX": (r"ALFONSO X", r"ALFONSO X"),
    "Villanueva": (r"VILLANUEVA", r"VILLANUEVA"),
    "ESIC": (r"\bESIC\b", r"\bESIC\b"),
    "CUNEF": (r"CUNEF", r"CUNEF"),
    "UDIT": (r"UDIT", r"\bUDIT\b"),
    "UNIE": (r"INTERNACIONAL DE LA EMPRESA", r"\bUNIE\b|INTERNACIONAL DE LA EMPRESA"),
}
OSM_TEXTO = ("name", "official_name", "alt_name", "short_name", "operator")


def _geom_osm(e: dict):
    """Geometría de un elemento de Overpass (`out geom`) en EPSG:4326."""
    from shapely.geometry import LineString, Point, Polygon, box
    from shapely.ops import polygonize, unary_union
    if e["type"] == "node":
        return Point(e["lon"], e["lat"])
    if e["type"] == "way":
        c = [(p["lon"], p["lat"]) for p in e.get("geometry", [])]
        if len(c) >= 4 and c[0] == c[-1]:
            return Polygon(c)
        return LineString(c) if len(c) >= 2 else None
    lineas = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
              for m in e.get("members", []) if m.get("type") == "way"
              and m.get("role") in ("outer", "") and len(m.get("geometry", [])) >= 2]
    if lineas:
        polys = list(polygonize(unary_union(lineas)))
        if polys:
            return unary_union(polys)
    b = e.get("bounds")
    return box(b["minlon"], b["minlat"], b["maxlon"], b["maxlat"]) if b else None


def estudiantes_por_universidad() -> tuple[pd.Series, str]:
    """Grado + máster presenciales del último año de las dos tablas del portal."""
    total, anyos = {}, set()
    for conjunto, nombre in [("1925489", "estudiantes-matriculados-en-estudios-de-grado-"
                                         "presenciales-por-universidad.csv"),
                             ("1925502", "estudiantes-matriculados-en-estudios-de-master-"
                                         "presenciales-por-universidad.csv")]:
        d = leer_csv(ORIG / conjunto / nombre)
        anyo = d["Año"].max()
        anyos.add(anyo)
        d = d[(d["Año"] == anyo) & d["Concepto"].str.contains(" presenciales en la ",
                                                               regex=False)]
        for concepto, valor in zip(d["Concepto"], d["Valor"]):
            uni = sin_tildes(concepto.split(" en la universidad", 1)[1])
            clave = next((k for k, (pe, _) in UNIVERSIDADES.items()
                          if re.search(pe, uni)), None)
            if clave is None:
                raise RuntimeError(f"Universidad de la estadística sin patrón: {concepto}")
            total[clave] = total.get(clave, 0) + float(pd.to_numeric(valor, errors="coerce")
                                                       or 0)
    return pd.Series(total), "/".join(sorted(anyos))


def universidades() -> None:
    capa = "campus_universitarios"
    res = json.loads((ORIG / "osm_universidades" / "osm_universidades.json")
                     .read_text(encoding="utf-8"))
    filas = []
    for e in res["elements"]:
        tags = e.get("tags", {})
        filas.append({"osm_id": f"{e['type']}/{e['id']}",
                      "texto": sin_tildes(" | ".join(tags.get(k, "") for k in OSM_TEXTO)),
                      "geometry": _geom_osm(e)})
    g = gpd.GeoDataFrame(filas, crs=4326).dropna(subset=["geometry"]).to_crs(CRS)
    n = len(g)
    g["geometry"] = g.geometry.make_valid()
    # Puntos y líneas → círculo de la superficie mínima
    r_min = math.sqrt(S.CAMPUS_SUPERFICIE_MINIMA_HA * 1e4 / math.pi)
    no_area = ~g.geom_type.isin(["Polygon", "MultiPolygon", "GeometryCollection"])
    g.loc[no_area, "geometry"] = g.loc[no_area].geometry.centroid.buffer(r_min)
    g["geometry"] = g.geometry.map(lambda x: shapely.union_all(
        [p for p in getattr(x, "geoms", [x]) if p.geom_type in ("Polygon", "MultiPolygon")]))

    excluir = g["texto"].map(lambda t: any(p in f" {t}" for p in S.CAMPUS_EXCLUIR))
    informe.setdefault(capa, {}).setdefault("descartes", {})[
        "no es un centro de estudios (residencia, museo, oficinas, instituto…)"] = \
        int(excluir.sum())
    g = g[~excluir].reset_index(drop=True)
    g["universidad"] = g["texto"].map(lambda t: next(
        (k for k, (_, po) in UNIVERSIDADES.items() if re.search(po, t)), None))
    por_texto = int(g["universidad"].notna().sum())
    # Sin nombre reconocible: la universidad del recinto que lo contiene
    sin = g[g["universidad"].isna()]
    con = g[g["universidad"].notna()]
    dentro = gpd.sjoin(sin.assign(geometry=sin.representative_point()),
                       con[["universidad", "geometry"]], predicate="within")
    dentro = dentro[~dentro.index.duplicated()]
    g.loc[dentro.index, "universidad"] = dentro["universidad_right"]
    por_recinto = len(dentro)
    g["universidad"] = g["universidad"].fillna("otros")

    # Unión en campus: elementos de la misma universidad a menos de CAMPUS_UNION_M
    campus = []
    for uni, sub in g.groupby("universidad"):
        if uni == "otros":   # centros distintos: cada uno es su propio campus
            grupos = [sub.loc[[i]] for i in sub.index]
        else:
            zonas = shapely.union_all(sub.buffer(S.CAMPUS_UNION_M / 2).to_numpy())
            zonas = list(getattr(zonas, "geoms", [zonas]))
            rp = sub.representative_point()
            grupos = [sub[rp.within(z)] for z in zonas]
        for x in grupos:
            if x.empty:
                continue
            geom = shapely.union_all(x.geometry.to_numpy())
            campus.append({"universidad": uni, "n_elementos_osm": len(x),
                           "osm_ids": " ".join(x["osm_id"]), "geometry": geom})
    c = gpd.GeoDataFrame(campus, crs=CRS)
    c["superficie_ha"] = (c.area / 1e4).round(2)
    c["peso_reparto"] = np.sqrt(np.maximum(c["superficie_ha"], S.CAMPUS_SUPERFICIE_MINIMA_HA))

    est, curso = estudiantes_por_universidad()
    suma = c[c["universidad"] != "otros"].groupby("universidad")["peso_reparto"].transform("sum")
    c["estudiantes"] = np.where(
        c["universidad"] == "otros", float(S.CAMPUS_SIN_DATOS_ESTUDIANTES),
        c["universidad"].map(est).fillna(0) * c["peso_reparto"] / suma)
    c["estudiantes"] = c["estudiantes"].round()
    c["origen_estudiantes"] = np.where(
        c["universidad"] == "otros", "peso típico (supuesto)",
        "estadística del portal repartida por superficie (estimación)")
    c["nombre_universidad"] = c["universidad"].map(
        lambda u: "otro centro de estudios superiores" if u == "otros" else u)
    sin_campus = sorted(set(est.index) - set(c["universidad"]))
    asignados = c.loc[c["universidad"] != "otros", "estudiantes"].sum()
    resumen = c[c["universidad"] != "otros"].groupby("universidad").agg(
        campus=("estudiantes", "size"), estudiantes=("estudiantes", "sum"))
    informe[capa]["notas"] = [
        "Ubicación: elementos `amenity=university` de OpenStreetMap (polígonos; los "
        f"puntos se tratan como un círculo de {S.CAMPUS_SUPERFICIE_MINIMA_HA:g} ha).",
        f"Asignación a universidad: {por_texto} por su nombre u operador, {por_recinto} por "
        "estar dentro del recinto de una universidad; el resto son «otros» centros de "
        f"estudios superiores con {S.CAMPUS_SIN_DATOS_ESTUDIANTES} estudiantes al día "
        "(**supuesto**).",
        f"Estudiantes: Grado + máster presenciales por universidad, año {curso} de las "
        "tablas 1925489 y 1925502 del portal (datos provisionales): "
        + f"{asignados:,.0f} de {est.sum():,.0f}".replace(",", ".")
        + " colocados en algún campus.",
        f"Reparto entre campus de la misma universidad (unidos si están a menos de "
        f"{S.CAMPUS_UNION_M} m): proporcional a la raíz cuadrada de la superficie "
        "(**estimación**, ver src/supuestos.py).",
        "Campus por universidad: " + "; ".join(
            f"{u} {int(r.campus)} ({r.estudiantes:,.0f})".replace(",", ".")
            for u, r in resumen.iterrows()) + ".",
    ] + ([f"Universidades de la estadística sin ningún campus en OSM (sus estudiantes no "
          f"se colocan): {', '.join(sin_campus)}."] if sin_campus else [])
    guardar(c, capa, ["universidad", "nombre_universidad", "estudiantes", "origen_estudiantes",
                      "superficie_ha", "peso_reparto", "n_elementos_osm", "osm_ids"], n,
            "elementos OSM")


# ============================================================ 2. HORARIO DE LOS DEA
_DIAS_LV = re.compile(r"\bL\s*[-/A]\s*V\b|\bL\s+A\s+V\b|LUNES\s+A\s+VIERNES|DE\s+L\s+A\s+V\b"
                      r"|\bL\s*-\s*J\b|LUNES\s+A\s+JUEVES|\bL\s*A\s*J\b")
_DIAS_TODOS = re.compile(r"\bL\s*[-/A]\s*D\b|LUNES\s+A\s+DOMINGO|TODOS\s+LOS\s+DIAS"
                         r"|\bL\s*-\s*S\b|LUNES\s+A\s+SABADO|DIARIO")
_FINDE = re.compile(r"\bS\s*[-Y/]\s*D\b|SABADO|DOMINGO|FIN(ES)?\s+DE\s+SEMANA|FESTIVO"
                    r"|\bSD\b|\bS\b\s*\d")
_HORA = r"(\d{1,2})(?:\s*[:.,H]\s*(\d{2}))?\s*(?:H\b|HORAS|HRS?\b)?\.?"
_RANGO = re.compile(_HORA + r"\s*(?:-|–|A\b|HASTA)\s*" + _HORA)


def _a_horas(h: str, m: str | None) -> float | None:
    h = int(h)
    m = int(m) if m else 0
    if h > 24 or m > 59:
        return None
    return h + m / 60


def _rangos(texto: str) -> list[tuple[float, float]]:
    out = []
    t = re.sub(r"(\d{1,2})(\d{2})\b", r"\1:\2", texto)  # 1800 → 18:00
    for m in _RANGO.finditer(t):
        a, b = _a_horas(m.group(1), m.group(2)), _a_horas(m.group(3), m.group(4))
        if a is None or b is None or a == b:
            continue
        if b < a:      # cierra pasada la medianoche (p. ej. de 5 a 0:30)
            b += 24
        out.append((a, b))
    return out


def normalizar_horario(texto) -> dict:
    """Interpreta el texto libre de horario_acceso.

    Devuelve {tipo, abre_lab, cierra_lab, abre_fds, cierra_fds, fds}, donde tipo es
    vacio | vehiculo | 24h | eventos | rango | expresion | no_interpretable, las horas
    van en decimal (8.5 = 8:30; un cierre > 24 = pasada la medianoche) y fds dice si
    abre el fin de semana (True/False) o None si el texto no lo aclara."""
    r = {"tipo": "no_interpretable", "abre_lab": np.nan, "cierra_lab": np.nan,
         "abre_fds": np.nan, "cierra_fds": np.nan, "fds": None}
    if texto is None or (isinstance(texto, float) and np.isnan(texto)) or not str(texto).strip():
        r["tipo"] = "vacio"
        return r
    t = sin_tildes(str(texto)).strip()
    if any(sin_tildes(p) in t for p in S.DEA_PALABRAS_VEHICULO):
        r["tipo"] = "vehiculo"
        return r
    if re.search(r"\b24\s*(H|HORAS|/7|X7)?\b|PERMANENTE|SIEMPRE|CONTINUO", t) \
            and not _rangos(t):
        r.update(tipo="24h", fds=True)
        return r
    if re.search(r"EVENTO|PARTIDO|COMPETICI|ESPECTACULO|FUNCION", t):
        r["tipo"] = "eventos"
        return r

    # Separar la parte de fin de semana («L-V 9-21 / S-D 10-14»)
    partes = re.split(r"/{1,3}|;|\|", t)
    lab, fds = [], []
    for p in partes:
        (fds if _FINDE.search(p) and not _DIAS_LV.search(p) else lab).append(p)
    # Caso «L-V 7-23  S-D 9-15» sin separador
    if len(partes) == 1:
        m = _FINDE.search(t)
        if m and _DIAS_LV.search(t[:m.start()]):
            lab, fds = [t[:m.start()]], [t[m.start():]]
    rl = [x for p in lab for x in _rangos(p)]
    rf = [x for p in fds for x in _rangos(p)]
    if rl:
        r.update(tipo="rango", abre_lab=min(a for a, _ in rl), cierra_lab=max(b for _, b in rl))
    else:
        for palabra, (a, b) in S.HORARIO_EXPRESIONES.items():
            if palabra.upper() in t:
                r.update(tipo="expresion", abre_lab=a, cierra_lab=b, fds=False)
                break
    if r["tipo"] == "no_interpretable":
        return r
    if rf:
        r.update(abre_fds=min(a for a, _ in rf), cierra_fds=max(b for _, b in rf), fds=True)
    elif re.search(r"CERRADO\s+(S|FIN)", t) or (_DIAS_LV.search(t) and not _FINDE.search(t)):
        r["fds"] = False
    elif _DIAS_TODOS.search(t):
        r.update(abre_fds=r["abre_lab"], cierra_fds=r["cierra_lab"], fds=True)
    return r


def fusionar(g: gpd.GeoDataFrame, distancia: float) -> gpd.GeoDataFrame:
    """Une en un sitio los puntos del mismo tipo a menos de `distancia` metros
    (componentes conexas); se queda con el primero de cada grupo y cuenta cuántos hay."""
    g = g.reset_index(drop=True)
    grupo = np.arange(len(g))
    for _, sub in g.groupby("tipo_establecimiento"):
        idx = sub.index.to_numpy()
        pares = gpd.sjoin(sub[["geometry"]], sub[["geometry"]].assign(
            geometry=sub.buffer(distancia)), predicate="within")
        # unión-búsqueda sencilla
        padre = {i: i for i in idx}

        def raiz(i):
            while padre[i] != i:
                padre[i] = padre[padre[i]]
                i = padre[i]
            return i
        for i, j in zip(pares.index, pares["index_right"]):
            ri, rj = raiz(i), raiz(j)
            if ri != rj:
                padre[max(ri, rj)] = min(ri, rj)
        for i in idx:
            grupo[i] = raiz(i)
    g["grupo"] = grupo
    g["n_dea"] = g.groupby("grupo")["grupo"].transform("size")
    return g.drop_duplicates("grupo").drop(columns="grupo")


def dea() -> None:
    capa = "desfibriladores_horario"
    d = gpd.read_parquet(PROC / "desfibriladores.parquet")
    n = len(d)
    h = pd.DataFrame([normalizar_horario(x) for x in d["horario_acceso"]], index=d.index)
    d = d.join(h.rename(columns={"tipo": "horario_tipo"}))
    resumen_horario = d["horario_tipo"].value_counts().to_dict()

    # Desfibriladores de centros educativos que no están junto a ningún centro del
    # listado (universidades, academias…): se tratan como centros educativos que faltan.
    ce = gpd.read_parquet(PROC / "centros_educativos.parquet")
    edu = d[d["tipo_establecimiento"] == "Centro educativo"]
    cerca = gpd.sjoin_nearest(edu[["geometry"]], ce[["geometry"]], how="left",
                              max_distance=S.DEA_EDUCATIVO_DISTANCIA_M, distance_col="dist")
    huerfanos = cerca[cerca["dist"].isna()].index.unique()
    # Los que están junto a un campus universitario no se cuentan: sus estudiantes ya
    # salen del campus (capa campus_universitarios).
    campus = gpd.read_parquet(PROC / "campus_universitarios.parquet")
    junto = gpd.sjoin_nearest(d.loc[huerfanos, ["geometry"]], campus[["geometry"]],
                              how="inner", max_distance=S.DEA_EDUCATIVO_CAMPUS_M)
    en_campus = junto.index.unique()
    huerfanos = huerfanos.difference(en_campus)

    d["cliente"] = d["tipo_establecimiento"].map(lambda t: S.DEA_TIPOS.get(t, (None,))[0])
    d["personas_dia"] = d["tipo_establecimiento"].map(
        lambda t: S.DEA_TIPOS.get(t, (None, 0))[1]).astype(float)
    d["perfil"] = d["tipo_establecimiento"].map(lambda t: S.DEA_TIPOS.get(t, (0, 0, None))[2])
    d.loc[huerfanos, ["cliente", "personas_dia", "perfil"]] = \
        [S.DEA_EDUCATIVO_CLIENTE, float(S.DEA_EDUCATIVO_PESO), S.DEA_EDUCATIVO_PERFIL]

    descartes = {
        "en un vehículo (autobús)": d["horario_tipo"].eq("vehiculo"),
        f"«Centro educativo» junto a un campus universitario (a menos de "
        f"{S.DEA_EDUCATIVO_CAMPUS_M} m)": d.index.isin(en_campus),
        "tipo sin uso en el perfil (Otros, transporte, aeropuertos, colegio ya listado)":
            d["cliente"].isna(),
    }
    usar = pd.Series(True, index=d.index)
    for motivo, m in descartes.items():
        m = m & usar
        informe.setdefault(capa, {}).setdefault("descartes", {})[motivo] = int(m.sum())
        usar &= ~m
    d = d[usar]
    antes = len(d)
    edu = d["cliente"] == S.DEA_EDUCATIVO_CLIENTE
    d = pd.concat([fusionar(d[~edu], S.DEA_FUSION_M),
                   fusionar(d[edu], 3 * S.DEA_FUSION_M)])
    d = gpd.GeoDataFrame(d, crs=CRS)
    informe[capa]["descartes"]["fusionados con otro del mismo sitio"] = antes - len(d)
    informe[capa]["notas"] = [
        "Interpretación de `horario_acceso` (todas las filas): "
        + ", ".join(f"{k} {v}" for k, v in resumen_horario.items()) + ". "
        "rango = horas leídas del texto; expresion = «horario de oficina», «comercial», "
        "«lectivo»…; 24h y vacío usan el horario típico del tipo de establecimiento.",
        f"{len(huerfanos)} desfibriladores de «Centro educativo» sin ningún centro del "
        f"listado a menos de {S.DEA_EDUCATIVO_DISTANCIA_M} m ni campus universitario a "
        f"menos de {S.DEA_EDUCATIVO_CAMPUS_M} m (academias, centros de estudios que no "
        "están en ninguna lista): se cuentan como «universitarios» con "
        f"{S.DEA_EDUCATIVO_PESO} usuarios al día y horario universitario (**supuesto**), "
        f"fusionando los que están a menos de {3 * S.DEA_FUSION_M} m.",
        f"Los del mismo tipo a menos de {S.DEA_FUSION_M} m se fusionan en un solo sitio "
        "(`n_dea` = cuántos había).",
        "`cliente`, `personas_dia` y `perfil` salen de src/supuestos.py (**estimación**).",
    ]
    d["fds"] = d["fds"].astype("boolean")
    # No se guarda el texto libre de horario_acceso: ya está interpretado en las columnas
    # siguientes y alguna vez nombra el establecimiento.
    guardar(d, capa, ["codigo_dea", "tipo_establecimiento", "horario_tipo",
                      "abre_lab", "cierra_lab", "abre_fds", "cierra_fds", "fds", "cliente",
                      "personas_dia", "perfil", "n_dea", "cod_municipio", "cdgseccion"], n)


# ========================================================================== 3. GTFS
REDES = {  # fichero: (red, modo para VIAJEROS_POR_PASO)
    "gtfs_metro.zip": "metro",
    "gtfs_metro_ligero.zip": "metro_ligero",
    "gtfs_cercanias.zip": "cercanias",
    "gtfs_emt.zip": "emt",
    "gtfs_interurbanos.zip": "interurbanos",
    "gtfs_urbanos.zip": "urbanos",
}


def _segundos(s: pd.Series) -> np.ndarray:
    p = s.str.strip().str.split(":", expand=True).astype(int)
    return (p[0] * 3600 + p[1] * 60 + p[2]).to_numpy()


class Gtfs:
    def __init__(self, ruta: Path):
        self.zf = zipfile.ZipFile(ruta)
        self.nombres = {Path(n).name: n for n in self.zf.namelist() if not n.endswith("/")}

    def leer(self, nombre: str, **kw) -> pd.DataFrame:
        if nombre not in self.nombres:
            return pd.DataFrame()
        with self.zf.open(self.nombres[nombre]) as f:
            return pd.read_csv(f, dtype=str, encoding="utf-8-sig", **kw)


def servicios_activos(cal: pd.DataFrame, cd: pd.DataFrame, dia: date) -> set[str]:
    ds = dia.strftime("%Y%m%d")
    col = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
           "sunday"][dia.weekday()]
    act = set()
    if not cal.empty:
        act = set(cal.loc[(cal["start_date"] <= ds) & (cal["end_date"] >= ds)
                          & (cal[col] == "1"), "service_id"])
    if not cd.empty:
        x = cd[cd["date"] == ds]
        act |= set(x.loc[x["exception_type"] == "1", "service_id"])
        act -= set(x.loc[x["exception_type"] == "2", "service_id"])
    return act


def elegir_dias(cal: pd.DataFrame, cd: pd.DataFrame, trips: pd.DataFrame) -> dict:
    fechas = pd.concat([cal.get("start_date", pd.Series(dtype=str)),
                        cal.get("end_date", pd.Series(dtype=str)),
                        cd.get("date", pd.Series(dtype=str))]).dropna()
    ini = pd.to_datetime(fechas.min()).date()
    fin = pd.to_datetime(fechas.max()).date()
    largo = 7 * S.GTFS_SEMANAS_MUESTRA
    desde = max(ini, min(HOY, fin - timedelta(days=largo - 1)))
    viajes = trips.groupby("service_id").size()
    cand = {"laborable": [], "sabado": []}
    for k in range(largo):
        dia = desde + timedelta(days=k)
        if dia > fin:
            break
        tipo = "laborable" if dia.weekday() in (1, 2, 3) else \
            "sabado" if dia.weekday() == 5 else None
        if tipo:
            n = int(viajes.reindex(list(servicios_activos(cal, cd, dia))).sum())
            cand[tipo].append((n, dia))
    out = {}
    for tipo, lista in cand.items():
        lista = sorted(x for x in lista if x[0] > 0)
        if not lista:
            raise RuntimeError(f"Sin días con servicio de tipo {tipo}")
        out[tipo] = lista[(len(lista) - 1) // 2]  # mediana (la inferior si son pares)
    return out


def salidas_por_hora(g: Gtfs, servicios: set[str], trips: pd.DataFrame,
                     st: pd.DataFrame, freq: pd.DataFrame, expandir: bool) -> pd.DataFrame:
    """Pasos de vehículos por parada y hora (0-23) para los servicios dados."""
    t = set(trips.loc[trips["service_id"].isin(servicios), "trip_id"])
    x = st[st["trip_id"].isin(t)]
    if expandir:
        fx = freq[freq["trip_id"].isin(t)]
        plantilla = x[x["trip_id"].isin(set(fx["trip_id"]))]
        normales = x[~x["trip_id"].isin(set(fx["trip_id"]))]
        partes = [pd.DataFrame({"stop_id": normales["stop_id"],
                                "hora": normales["seg"] // 3600 % 24})]
        ini_viaje = plantilla.groupby("trip_id")["seg"].transform("min")
        plantilla = plantilla.assign(desfase=plantilla["seg"] - ini_viaje)
        for _, f in fx.iterrows():
            salidas = np.arange(f["ini"], f["fin"], f["headway"])
            p = plantilla[plantilla["trip_id"] == f["trip_id"]]
            tiempos = (salidas[None, :] + p["desfase"].to_numpy()[:, None])
            partes.append(pd.DataFrame({
                "stop_id": np.repeat(p["stop_id"].to_numpy(), len(salidas)),
                "hora": (tiempos.ravel() // 3600) % 24}))
        x = pd.concat(partes, ignore_index=True)
    else:
        x = pd.DataFrame({"stop_id": x["stop_id"], "hora": x["seg"] // 3600 % 24})
    tabla = x.groupby(["stop_id", "hora"]).size().unstack(fill_value=0)
    return tabla.reindex(columns=range(24), fill_value=0)


def geometria_accesos(stops: pd.DataFrame) -> pd.DataFrame:
    """Geometría de cada parada en EPSG:4326: sus accesos a la calle si la estación los
    tiene en el GTFS (Metro, Metro Ligero) y, si no, el punto de la parada."""
    from shapely.geometry import MultiPoint, Point
    s = stops.copy()
    for c in ("stop_lat", "stop_lon"):
        s[c] = pd.to_numeric(s[c], errors="coerce")
    lt = s.get("location_type", pd.Series("0", index=s.index)).fillna("0").str.strip()
    padre = s.get("parent_station", pd.Series(pd.NA, index=s.index))
    acc = s[(lt == "2") & padre.notna() & s["stop_lat"].notna()]
    accesos = {k: list(zip(v["stop_lon"], v["stop_lat"]))
               for k, v in acc.groupby(padre[acc.index])}
    filas = []
    for i, f in s[lt.isin(["0", ""])].iterrows():
        if pd.isna(f["stop_lat"]) or pd.isna(f["stop_lon"]):
            geom, con = None, False
        else:
            # La estación de un andén: su parent_station o, en Metro, «par_X» → «est_X»
            est = padre[i] if pd.notna(padre[i]) else str(f["stop_id"]).replace("par_", "est_", 1)
            if est in accesos:
                geom, con = MultiPoint(accesos[est]), True
            else:
                geom, con = Point(f["stop_lon"], f["stop_lat"]), False
        filas.append({"stop_id": f["stop_id"], "stop_name": f.get("stop_name"),
                      "geometry": geom, "con_accesos": con})
    return pd.DataFrame(filas)


def demanda_tipica() -> tuple[dict, str]:
    """Viajeros de un laborable típico y de un sábado típico por columna del Excel."""
    d = pd.read_excel(ORIG / "crtm_paradas" / "crtm_demanda_diaria.xlsx",
                      sheet_name="diaria", header=1)
    d = d.rename(columns={d.columns[1]: "fecha"})
    d["fecha"] = pd.to_datetime(d["fecha"], errors="coerce")
    d = d.dropna(subset=["fecha"])
    fin = d["fecha"].max()
    d = d[d["fecha"] > fin - pd.Timedelta(weeks=S.DEMANDA_SEMANAS)]
    out = {}
    for tipo, dias in {"lab": [1, 2, 3], "sab": [5]}.items():
        x = d[d["fecha"].dt.weekday.isin(dias)]
        tot = x["Total"].astype(float)
        x = x[tot >= S.DEMANDA_DESCARTE * tot.median()]
        out[tipo] = {c: float(x[c].astype(float).median()) for c in
                     set(S.DEMANDA_COLUMNA.values())}
    periodo = f"{(fin - pd.Timedelta(weeks=S.DEMANDA_SEMANAS)).date()} a {fin.date()}"
    return out, periodo


def _norm_estacion(s: str) -> str:
    s = sin_tildes(s)
    for x in ("MADRID-", " C.", " CERCANIAS", " P.V.", "-CLARA CAMPOAMOR"):
        s = s.replace(x, "")
    return re.sub(r"\s+", " ", s).strip(" .-")


def calibrar(gdf: gpd.GeoDataFrame) -> list[str]:
    """Añade pp_lab y pp_sab: personas que suben o bajan por cada vehículo que para."""
    hl, hs = [f"lab_{h:02d}" for h in range(24)], [f"sab_{h:02d}" for h in range(24)]
    gdf["pp_lab"] = gdf["red"].map(S.VIAJEROS_POR_PASO).astype(float)
    gdf["pp_sab"] = gdf["pp_lab"]
    gdf["origen_pp"] = "supuesto (sin demanda publicada)"
    try:
        dem, periodo = demanda_tipica()
    except (OSError, ValueError, KeyError) as e:
        return [f"**Sin calibrar** (no se pudo leer la demanda del CRTM: {e}); se usan los "
                "valores de respaldo de src/supuestos.py."]
    notas = [f"Calibración con la demanda diaria del CRTM ({periodo}; mediana de martes a "
             "jueves y de sábados, sin festivos): personas por paso = 2 × viajeros del día / "
             "pasos de vehículos del día en el GTFS. **Estimación**: igual en todas las "
             "paradas de la red."]
    col_red = gdf["red"].map(S.DEMANDA_COLUMNA)
    for tipo, cols in (("lab", hl), ("sab", hs)):
        pasos = gdf.assign(pasos=gdf[cols].sum(axis=1)).groupby(col_red)["pasos"].sum()
        factor = {c: 2 * dem[tipo][c] / pasos[c] for c in pasos.index}
        con = col_red.notna()
        gdf.loc[con, f"pp_{tipo}"] = col_red[con].map(factor)
        notas.append(("Laborable" if tipo == "lab" else "Sábado") + ": " + "; ".join(
            f"{c} {dem[tipo][c]:,.0f} viajeros / {pasos[c]:,.0f} pasos → "
            f"{factor[c]:.1f} personas por paso".replace(",", ".") for c in pasos.index))
    gdf.loc[col_red.notna(), "origen_pp"] = "demanda de la red (CRTM)"

    # Estaciones de Cercanías con dato propio: se corrige la media de la red con la
    # proporción entre la estación y la red (mismo año del dato por estación).
    try:
        e = leer_csv(ORIG / "1923861" / "viajeros-subidos-y-bajados-en-trenes-de-cercanias-"
                                        "por-estaciones.csv")
    except OSError:
        return notas
    e["v"] = pd.to_numeric(e["Valor"], errors="coerce")
    e = e[e["v"].notna()]
    anyo = e["Año"].max()
    e = e[e["Año"] == anyo]
    e["est"] = e["Concepto"].str.split(" en la estación de ", n=1).str[1].map(_norm_estacion)
    mens = pd.read_excel(ORIG / "crtm_paradas" / "crtm_demanda_diaria.xlsx",
                         sheet_name="mensual", header=1)
    mens = mens.rename(columns={mens.columns[1]: "anyo"})
    red_anual = 2 * mens.loc[mens["anyo"] == float(anyo), "Renfe Cercanías"].astype(float).sum()
    cer = gdf["red"] == "cercanias"
    pasos_dia = (5 * gdf.loc[cer, hl].sum(axis=1) + 2 * gdf.loc[cer, hs].sum(axis=1)) / 7
    pp_red = red_anual / 365 / pasos_dia.sum() if red_anual else np.nan
    nombres = gdf.loc[cer, "parada"].map(_norm_estacion)
    usadas, ambiguas = [], []
    for est, v in zip(e["est"], e["v"]):
        m = nombres[nombres == est]
        if m.empty:
            m = nombres[nombres.map(lambda x: est in x.split("-"))]
        if len(m) != 1:
            ambiguas.append(est)
            continue
        i = m.index[0]
        if pasos_dia[i] <= 0 or not np.isfinite(pp_red):
            continue
        ratio = (v / 365 / pasos_dia[i]) / pp_red
        gdf.loc[i, ["pp_lab", "pp_sab"]] *= ratio
        gdf.loc[i, "origen_pp"] = f"estación de Cercanías ({anyo})"
        usadas.append(f"{est} ×{ratio:.2f}")
    notas.append(f"Cercanías: {len(usadas)} estaciones con viajeros subidos y bajados propios "
                 f"(portal, conjunto 1923861, año {anyo}); su valor es el de la red "
                 "multiplicado por la proporción entre la estación y la media de la red: "
                 + ", ".join(usadas) + "."
                 + (f" Sin emparejar (sin dato o nombre ambiguo): {', '.join(ambiguas)}."
                    if ambiguas else ""))
    return notas


def gtfs() -> None:
    capa = "salidas_paradas"
    carpeta = ORIG / "crtm_paradas"
    resultados, notas, dias_usados = [], [], {}
    for fichero, red in REDES.items():
        print(f"  · {fichero} …", flush=True)
        g = Gtfs(carpeta / fichero)
        cal, cd = g.leer("calendar.txt"), g.leer("calendar_dates.txt")
        trips = g.leer("trips.txt", usecols=["trip_id", "service_id"])
        st = g.leer("stop_times.txt", usecols=["trip_id", "departure_time", "arrival_time",
                                               "stop_id"])
        hora = st["departure_time"].where(st["departure_time"].notna()
                                          & st["departure_time"].str.strip().ne(""),
                                          st["arrival_time"])
        st = st.assign(seg=_segundos(hora.fillna("0:0:0")))[["trip_id", "stop_id", "seg"]]
        # Viajes de relleno: interurbanos y urbanos traen viajes (servicio «9999_…») con
        # todas las paradas a las 01:00:00. Se descartan los de 3 o más paradas que duran
        # menos de un minuto: no son horarios reales.
        dur = st.groupby("trip_id")["seg"].agg(["min", "max", "size"])
        relleno = set(dur.index[(dur["size"] >= 3) & (dur["max"] - dur["min"] < 60)])
        st = st[~st["trip_id"].isin(relleno)]
        trips = trips[~trips["trip_id"].isin(relleno)]
        freq = g.leer("frequencies.txt")
        expandir = False
        if not freq.empty:
            # Si cada viaje tiene una sola fila de frecuencias, el fichero solo describe
            # el intervalo de paso de viajes que ya están todos en stop_times (caso EMT).
            # Si un viaje tiene varias filas, es una plantilla que hay que repetir (Metro).
            filas_por_viaje = len(freq) / freq["trip_id"].nunique()
            expandir = filas_por_viaje > 1.2
            if expandir:
                freq = freq.assign(ini=_segundos(freq["start_time"]),
                                   fin=_segundos(freq["end_time"]),
                                   headway=freq["headway_secs"].astype(int))
        dias = elegir_dias(cal, cd, trips)
        dias_usados[red] = {k: v[1].isoformat() for k, v in dias.items()}
        todas = g.leer("stops.txt", usecols=lambda c: c in {
            "stop_id", "stop_name", "stop_lat", "stop_lon", "location_type", "parent_station"})
        paradas = geometria_accesos(todas)
        tablas = {}
        for tipo, (_, dia) in dias.items():
            tablas[tipo] = salidas_por_hora(g, servicios_activos(cal, cd, dia), trips, st,
                                            freq, expandir)
        lab = tablas["laborable"].add_prefix("lab_h")
        sab = tablas["sabado"].add_prefix("sab_h")
        t = lab.join(sab, how="outer").fillna(0).astype(int).reset_index()
        t = t.merge(paradas, on="stop_id", how="left")
        sin = int(t["geometry"].isna().sum())
        t = t.dropna(subset=["geometry"])
        t["red"] = red
        resultados.append(t)
        notas.append(f"{red}: laborable {dias_usados[red]['laborable']}, sábado "
                     f"{dias_usados[red]['sabado']}"
                     + (" (viajes-plantilla de frequencies.txt expandidos)" if expandir else "")
                     + (f"; {len(relleno)} viajes de relleno descartados (todas las paradas "
                        "a la misma hora)" if relleno else "")
                     + (f"; {sin} paradas sin coordenadas" if sin else "")
                     + (f"; {int(t['con_accesos'].sum())} con la posición de sus accesos"
                        if t["con_accesos"].any() else "")
                     + f"; {len(t)} paradas con servicio; "
                     f"{int(t.filter(like='lab_h').sum().sum()):,} pasos en laborable"
                     .replace(",", "."))
    t = pd.concat(resultados, ignore_index=True)
    n = len(t)
    t = t.rename(columns={**{f"lab_h{h}": f"lab_{h:02d}" for h in range(24)},
                          **{f"sab_h{h}": f"sab_{h:02d}" for h in range(24)}})
    hl, hs = [f"lab_{h:02d}" for h in range(24)], [f"sab_{h:02d}" for h in range(24)]
    t["total_lab"], t["total_sab"] = t[hl].sum(axis=1), t[hs].sum(axis=1)
    gdf = gpd.GeoDataFrame(t, geometry="geometry", crs=4326).to_crs(CRS)
    gdf = gdf.rename(columns={"stop_name": "parada"})
    notas_cal = calibrar(gdf)
    informe.setdefault(capa, {})["notas"] = [
        "Pasos de vehículos (cada vez que un tren o autobús para en la parada) por hora, "
        "en un laborable típico (`lab_00`…`lab_23`) y un sábado típico (`sab_00`…`sab_23`). "
        "Las horas de más de 24:00 del GTFS se pasan a la madrugada (25:30 → 1).",
        "Día típico: entre los martes, miércoles y jueves (y entre los sábados) de las "
        f"{S.GTFS_SEMANAS_MUESTRA} primeras semanas de vigencia a partir de hoy, el de "
        "número de viajes mediano (evita festivos y días especiales).",
        "Metro: GTFS de mayo de 2025 (el más reciente publicado; su calendario terminó el "
        "27/05/2026), así que se usa un día dentro de su vigencia. **Estimación**: se supone "
        "que las frecuencias actuales son parecidas.",
        "Interurbanos y urbanos comparten `stops.txt`: cada red cuenta solo sus vehículos.",
        "Geometría: la parada; en Metro y Metro Ligero, el conjunto de accesos de la "
        "estación (`location_type` 2 del GTFS), para medir la distancia a la salida más "
        "cercana a la calle.",
    ] + notas + notas_cal
    guardar(gdf, capa, ["red", "stop_id", "parada", *hl, *hs, "total_lab", "total_sab",
                        "pp_lab", "pp_sab", "origen_pp", "con_accesos"], n, "paradas")
    (PROC / "salidas_paradas_dias.json").write_text(
        json.dumps(dias_usados, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------- principal
def escribir_fuentes() -> None:
    lineas = ["## Datos para el perfil por horas", "",
              "Generados con `src/procesar_perfil.py` en `datos/procesados/` (GeoParquet, "
              "EPSG:25830, con `lat`/`lon`). Supuestos en `src/supuestos.py`.", ""]
    for capa, r in informe.items():
        lineas.append(f"**{capa}** ({r['origen']:,} {r['unidad']} → {r['final']:,})"
                      .replace(",", "."))
        lineas.append("")
        for k, v in r.get("descartes", {}).items():
            lineas.append(f"- Descartados por {k}: {v}")
        lineas += [f"- {x}" for x in r.get("notas", [])] + [""]
    actualizar_bloque("perfil", lineas)


PASOS = {"educativos": educativos, "universidades": universidades, "dea": dea, "gtfs": gtfs}


def main(argv: list[str]) -> int:
    elegidos = argv or list(PASOS)
    previo = PROC / "informe_perfil.json"
    try:
        guardado = json.loads(previo.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        guardado = {}
    for p in elegidos:
        print(p)
        PASOS[p]()
    # Conserva en el informe las capas que no se han regenerado ahora
    capas = {"educativos": "centros_educativos_alumnos",
             "universidades": "campus_universitarios", "dea": "desfibriladores_horario",
             "gtfs": "salidas_paradas"}
    for p, capa in capas.items():
        if p not in elegidos and capa in guardado:
            informe[capa] = guardado[capa]
    orden = [capas[p] for p in PASOS if capas[p] in informe]
    ordenado = {c: informe[c] for c in orden}
    informe.clear()
    informe.update(ordenado)
    previo.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
    escribir_fuentes()
    for capa, r in informe.items():
        print(f"\n{capa}: {r['origen']} → {r['final']}")
        for k, v in r.get("descartes", {}).items():
            print(f"  descartadas por {k}: {v}")
        for x in r.get("notas", []):
            print(f"  · {x}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
