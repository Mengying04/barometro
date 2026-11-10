"""Informe del local (parte A): contexto de mercado alrededor de un punto.

    from informe_local import informe_local
    inf = informe_local(40.4046, -3.6106)
    inf["bloques"]   # lista de bloques: competencia, mercado, precios, turismo, festivos,
                     # sector; cada uno con sus fuentes, fechas y si es dato o estimación

Desde la terminal:
    python src/informe_local.py 40.4046 -3.6106          # texto en Markdown
    python src/informe_local.py 40.4046 -3.6106 --json   # JSON

Cada bloque dice si su resultado es un DATO (tal como lo publica la fuente) o una
ESTIMACIÓN (calculada con supuestos, que están en src/supuestos.py). No incluye
recomendaciones de qué vender (eso es la parte B).
"""

from __future__ import annotations

import glob
import json
import math
import re
import sys
import unicodedata
from datetime import date, datetime
from functools import lru_cache

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer

import supuestos as S
from procesar import CRS, ORIG, PROC, leer_csv

PORTAL = "https://datos.comunidad.madrid/dataset"
DATO, ESTIMACION, MIXTO = "dato", "estimación", "dato + estimación"
_A_UTM = Transformer.from_crs(4326, CRS, always_xy=True)


# ------------------------------------------------------------------------- utilidades
def sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(s))
                   if unicodedata.category(c) != "Mn").upper().strip()


def norm_municipio(s: str) -> str:
    """«Acebeda, La» y «La Acebeda» → «LA ACEBEDA»; «Álamo (El)» → «EL ALAMO»."""
    s = sin_tildes(s)
    m = re.match(r"^(.*?)\s*(?:,\s*|\()\s*(LA|EL|LOS|LAS)\)?$", s)
    if m:
        s = f"{m.group(2)} {m.group(1)}"
    return re.sub(r"\s+", " ", s)


def fuente_portal(conjunto: str, periodo: str | None = None) -> dict:
    """Ficha de un conjunto del portal de la Comunidad (descargada en ficha.json)."""
    ruta = ORIG / conjunto / "ficha.json"
    f = json.loads(ruta.read_text(encoding="utf-8"))
    return {"nombre": f.get("title", conjunto),
            "enlace": f"{PORTAL}/{conjunto}",
            "licencia": f.get("license_title") or "?",
            "actualizado": (f.get("metadata_modified") or "?")[:10],
            "descargado": datetime.fromtimestamp(ruta.stat().st_mtime).date().isoformat(),
            **({"periodo": periodo} if periodo else {})}


def fuente_externa(carpeta: str, periodo: str | None = None) -> dict:
    e = json.loads((ORIG / ".fuentes_externas.json").read_text(encoding="utf-8"))[carpeta]
    return {"nombre": e["titulo"], "enlace": e["enlace"].split(" ")[0],
            "licencia": re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", e["licencia"]),
            "actualizado": e["version"], "descargado": e["fecha_descarga"],
            **({"periodo": periodo} if periodo else {})}


def bloque(clave, titulo, caracter, fuentes, resumen, datos, notas=()) -> dict:
    return {"clave": clave, "titulo": titulo, "caracter": caracter, "fuentes": fuentes,
            "resumen": resumen, "datos": datos, "notas": list(notas)}


def miles(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def con_signo(x: float) -> str:
    return f"{x:+,.0f}".replace(",", ".")


def dec(x: float, n: int = 1) -> str:
    """Número con coma decimal."""
    return f"{x:.{n}f}".replace(".", ",")


def redondeo(x: float) -> float:
    """Dos cifras significativas (para rangos: no aparentar más precisión)."""
    if x <= 0:
        return 0.0
    e = math.floor(math.log10(x)) - 1
    return round(x / 10 ** e) * 10 ** e


# ------------------------------------------------------------------------------ datos
@lru_cache(maxsize=1)
def capas() -> dict:
    secc = gpd.read_parquet(PROC / "secciones_censales.parquet")
    return {
        "secciones": secc,
        "censo": gpd.read_parquet(PROC / "hosteleria_madrid_capital.parquet"),
        "osm": gpd.read_parquet(PROC / "hosteleria_osm.parquet"),
        "sanitarios": gpd.read_parquet(PROC / "centros_sanitarios.parquet",
                                       columns=["codigo_postal", "geometry"]),
    }


def tipo_censo(epigrafes: str) -> str | None:
    tipos = {S.EPIGRAFE_COMPETENCIA.get(e.strip()) for e in str(epigrafes).split("|")}
    return next((t for t in S.PRIORIDAD_COMPETENCIA if t in tipos), None)


@lru_cache(maxsize=1)
def locales() -> dict[str, gpd.GeoDataFrame]:
    c = capas()
    censo = c["censo"].copy()
    censo["tipo_local"] = censo["epigrafes"].map(tipo_censo)
    osm = c["osm"].copy()
    osm["tipo_local"] = osm["tipo"].map(S.AMENITY_COMPETENCIA)
    return {"censo": censo[censo["tipo_local"].notna()],
            "osm": osm[osm["tipo_local"].notna()]}


def en_radio(g: gpd.GeoDataFrame, punto, radio: float) -> gpd.GeoDataFrame:
    idx = g.sindex.query(punto.buffer(radio), predicate="intersects")
    sub = g.iloc[idx]
    return sub[sub.distance(punto) <= radio]


@lru_cache(maxsize=64)
def media_municipio(cod_municipio: str, fuente: str, radio: float) -> float:
    """Locales a menos de `radio` de donde vive la gente del municipio: media de sus
    secciones censales (desde un punto interior) ponderada por población."""
    secc = capas()["secciones"]
    s = secc[(secc["cod_municipio"] == cod_municipio) & (secc["poblacion"].fillna(0) > 0)]
    zonas = gpd.GeoDataFrame({"pob": s["poblacion"].astype(float).to_numpy()},
                             geometry=s.representative_point().buffer(radio).to_numpy(),
                             crs=CRS)
    j = gpd.sjoin(zonas, locales()[fuente][["geometry"]], predicate="intersects")
    n = j.groupby(level=0).size().reindex(zonas.index, fill_value=0)
    return float((n * zonas["pob"]).sum() / zonas["pob"].sum())


@lru_cache(maxsize=64)
def cobertura_osm(cod_municipio: str) -> dict:
    """Locales por 1.000 habitantes: OSM en el municipio y censo en Madrid capital."""
    secc = capas()["secciones"]
    pob = secc.groupby("cod_municipio")["poblacion"].sum().astype(float)
    osm = locales()["osm"]
    o = (osm["cod_municipio"] == cod_municipio).sum() / pob[cod_municipio] * 1000
    c = len(locales()["censo"]) / pob["28079"] * 1000
    return {"osm_municipio": round(float(o), 2), "censo_madrid": round(float(c), 2),
            "relacion": round(float(o / c), 2)}


def poblacion_y_renta(punto, radio: float) -> dict:
    """Población dentro del círculo (proporcional a la superficie de cada sección) y
    renta neta media por persona de esa población."""
    secc = capas()["secciones"]
    circulo = punto.buffer(radio, quad_segs=32)
    s = secc.iloc[secc.sindex.query(circulo, predicate="intersects")]
    frac = shapely.area(shapely.intersection(s.geometry.to_numpy(), circulo)) / s.area
    pob = s["poblacion"].fillna(0).astype(float) * frac
    con_renta = s["renta_neta_persona"].notna()
    if pob[con_renta].sum() > 0:
        renta = float((s.loc[con_renta, "renta_neta_persona"] * pob[con_renta]).sum()
                      / pob[con_renta].sum())
    else:  # sin población dentro: la sección que contiene el punto
        dentro = s[s.contains(punto)]
        renta = float(dentro["renta_neta_persona"].iloc[0]) if len(dentro) else np.nan
    return {"poblacion": float(pob.sum()), "renta_persona": renta,
            "secciones": int(len(s))}


@lru_cache(maxsize=1)
def renta_comunidad() -> float:
    s = capas()["secciones"].dropna(subset=["renta_neta_persona", "poblacion"])
    return float((s["renta_neta_persona"] * s["poblacion"]).sum() / s["poblacion"].sum())


# ------------------------------------------------------------------ 1. competencia
def b_competencia(punto, radio, muni: dict) -> dict:
    madrid = muni["cod"] == "28079"
    fuente = "censo" if madrid else "osm"
    loc = en_radio(locales()[fuente], punto, radio)
    cuenta = {S.TIPOS_COMPETENCIA[t]: int((loc["tipo_local"] == t).sum())
              for t in S.TIPOS_COMPETENCIA}
    total = int(len(loc))
    area_km2 = math.pi * radio ** 2 / 1e6
    media = media_municipio(muni["cod"], fuente, radio)

    # Cocinas: siempre de OpenStreetMap (el censo no las tiene)
    osm = en_radio(locales()["osm"], punto, radio)
    con_cocina = osm["cocina"].notna()
    cocinas = (osm.loc[con_cocina, "cocina"].str.split(";").explode().str.strip()
               .value_counts().head(S.COCINAS_MAX))
    fuentes = [fuente_externa("madrid_censo_locales") if madrid
               else fuente_externa("osm_hosteleria")]
    if madrid:
        fuentes.append(fuente_externa("osm_hosteleria"))
    nombre_fuente = ("Censo de locales del Ayuntamiento de Madrid" if madrid
                     else "OpenStreetMap")
    rel = total / media if media > 0 else np.nan
    comparacion = ("sin referencia" if not np.isfinite(rel) else
                   f"{dec(rel)} veces la media del municipio")
    notas = [
        f"Fuente de los recuentos: **{nombre_fuente}**"
        + (" (registro oficial de locales abiertos)." if madrid else
           " (mapa colaborativo: puede faltar algún local, sobre todo en municipios "
           "pequeños; no hay un censo oficial abierto fuera de Madrid capital)."),
        f"Media del municipio = locales a menos de {radio:.0f} m de donde vive la gente del "
        "municipio (media de sus secciones censales ponderada por población). "
        "**Estimación** de referencia.",
        f"Tipos de cocina: solo de OpenStreetMap y **no todos los locales la indican** "
        f"({int(con_cocina.sum())} de {len(osm)} en el radio).",
    ]
    if madrid:
        notas.append("Clasificación del censo por epígrafe (src/supuestos.py): el «bar "
                     "restaurante» cuenta como bar.")
    cob = cobertura_osm(muni["cod"])
    if not madrid:
        notas.append(
            f"Cobertura de OpenStreetMap: en {muni['nombre']} registra "
            f"{dec(cob['osm_municipio'], 2)} locales por 1.000 habitantes, frente a "
            f"{dec(cob['censo_madrid'], 2)} del censo oficial en Madrid capital. "
            + ("**Probablemente faltan locales en OSM**: los números absolutos se quedan "
               "cortos, aunque la comparación con la media del municipio (que también sale "
               "de OSM) sigue siendo útil." if cob["relacion"] < S.COBERTURA_OSM_AVISO else
               "Cobertura parecida a la del censo de Madrid."))
    return bloque(
        "competencia", "Competencia en el radio", MIXTO, fuentes,
        f"{total} locales de hostelería en {radio:.0f} m ({nombre_fuente}): "
        + ", ".join(f"{k.lower()} {v}" for k, v in cuenta.items())
        + f"; {comparacion} (media: {dec(media)}).",
        {"fuente_usada": nombre_fuente, "por_tipo": cuenta, "total": total,
         "densidad_km2": round(total / area_km2, 1),
         "media_municipio": round(media, 1),
         "densidad_media_municipio_km2": round(media / area_km2, 1),
         "relacion_con_media": round(rel, 2) if np.isfinite(rel) else None,
         "cocinas_osm": {k: int(v) for k, v in cocinas.items()},
         "cobertura_osm": None if madrid else cob,
         "locales_osm_con_cocina": int(con_cocina.sum()), "locales_osm": int(len(osm))},
        notas)


# ------------------------------------------------------------- 2. mercado potencial
@lru_cache(maxsize=1)
def gasto_restauracion() -> tuple[float, str]:
    carpeta = "gasto_por_subgrupo_gasto_3_digitos_coicop_epf_base_2006"
    g = leer_csv(next((ORIG / carpeta).glob("*.csv")))
    g = g[(g["Concepto"] == "Gasto medio por persona de los hogares en restauración")
          & (g["Medida"] == "Gasto medio persona")]
    anyo = g["Año"].max()
    return float(g.loc[g["Año"] == anyo, "Valor"].iloc[0]), anyo


def b_mercado(punto, radio, pr: dict) -> dict:
    gasto, anyo = gasto_restauracion()
    rc = renta_comunidad()
    r = pr["renta_persona"] / rc if np.isfinite(pr["renta_persona"]) else 1.0
    base = pr["poblacion"] * gasto
    valores = [base * r ** e for e in S.ELASTICIDAD_RESTAURACION]
    lo = redondeo(min(valores) * (1 - S.MARGEN_POBLACION))
    hi = redondeo(max(valores) * (1 + S.MARGEN_POBLACION))
    return bloque(
        "mercado", "Mercado potencial: gasto en restauración de los vecinos", ESTIMACION,
        [fuente_portal("gasto_por_subgrupo_gasto_3_digitos_coicop_epf_base_2006",
                       f"Encuesta de Presupuestos Familiares {anyo}"),
         fuente_externa("ine_adrh", "renta y población 2024")],
        f"Entre {miles(lo)} € y {miles(hi)} € al año (estimación) gastan en bares y "
        f"restaurantes los ~{miles(pr['poblacion'])} vecinos del radio.",
        {"poblacion_radio": round(pr["poblacion"]), "gasto_persona_comunidad": gasto,
         "anyo_gasto": anyo, "renta_persona_zona": round(pr["renta_persona"]),
         "renta_persona_comunidad": round(rc), "renta_relativa": round(r, 2),
         "rango_eur_anual": [lo, hi]},
        [f"Gasto medio por persona en restauración en la Comunidad de Madrid ({anyo}): "
         f"{gasto:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
         + " (**dato**).",
         f"Renta neta media por persona de la zona: {miles(pr['renta_persona'])} € frente "
         f"a {miles(rc)} € de media en la Comunidad (×{dec(r, 2)}) (**dato** del INE, 2024; "
         "la de la zona es la media de sus secciones censales ponderada por población).",
         "Ajuste por renta (**supuesto**): gasto = población × gasto medio × (renta "
         "relativa) ^ elasticidad, con una elasticidad de "
         f"{dec(S.ELASTICIDAD_RESTAURACION[0])} a {dec(S.ELASTICIDAD_RESTAURACION[1])} (el gasto en "
         "comer fuera crece más o menos en proporción a la renta), y un "
         f"±{100 * S.MARGEN_POBLACION:.0f} % por la población. Por eso se da un rango.",
         "Es lo que gastan los vecinos en cualquier sitio, no lo que facturaría un local: "
         "parte lo gastan lejos de casa y, a la vez, el local recibe gente que no vive "
         "aquí (ver el perfil por horas)."])


# --------------------------------------------------------------- 3. gama de precios
@lru_cache(maxsize=1)
def ipc() -> tuple[dict, str]:
    i = leer_csv(next((ORIG / "ipc_base_2025").glob("*.csv")))
    i = i[(i["Territorio"] == "Comunidad de Madrid")
          & (i["Indicador"] == "Tasa de variación sobre igual periodo del año anterior")]
    ultimo = i.sort_values(["Año", "Periodo"]).iloc[-1][["Año", "Periodo"]]
    u = i[(i["Año"] == ultimo["Año"]) & (i["Periodo"] == ultimo["Periodo"])]
    tasas = {k: float(u.loc[u["Grupo"] == g, "Valor"].iloc[0]) for k, g in S.IPC_GRUPOS.items()
             if (u["Grupo"] == g).any()}
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
             "septiembre", "octubre", "noviembre", "diciembre"]
    return tasas, f"{meses[int(ultimo['Periodo'][1:]) - 1]} de {ultimo['Año']}"


def b_precios(pr: dict, rc: float) -> dict:
    r = pr["renta_persona"] / rc
    gama = ("económica" if r < S.GAMA_UMBRALES[0] else
            "alta" if r > S.GAMA_UMBRALES[1] else "media")
    t, mes = ipc()
    dif = t["restaurantes_alojamiento"] - t["alimentos"]
    fmt = lambda x: f"{x:+.1f} %".replace(".", ",")
    return bloque(
        "precios", "Gama de precios y evolución de precios", MIXTO,
        [fuente_externa("ine_adrh", "renta 2024"), fuente_portal("ipc_base_2025", mes)],
        f"Gama **{gama}** (renta de la zona ×{dec(r, 2)} la media de la Comunidad). En los "
        f"últimos 12 meses (hasta {mes}) restaurantes y alojamiento {fmt(t['restaurantes_alojamiento'])} "
        f"frente a alimentos {fmt(t['alimentos'])}.",
        {"gama": gama, "renta_relativa": round(r, 2), "umbrales": S.GAMA_UMBRALES,
         "ipc_mes": mes, "ipc_interanual": t,
         "diferencia_restaurantes_menos_alimentos": round(dif, 1)},
        [f"Gama (**estimación**): económica si la renta de la zona es menor que "
         f"{dec(S.GAMA_UMBRALES[0], 2)} veces la media de la Comunidad, alta si es mayor que "
         f"{dec(S.GAMA_UMBRALES[1], 2)}, media entre medias. Se basa en la renta de los "
         "residentes: si la mayoría de los clientes no son vecinos (perfil por horas), "
         "tómese con cautela.",
         f"IPC de la Comunidad de Madrid, tasa interanual de {mes} (**dato**): "
         f"restaurantes y servicios de alojamiento {fmt(t['restaurantes_alojamiento'])}, "
         f"alimentos y bebidas no alcohólicas {fmt(t['alimentos'])}, bebidas alcohólicas "
         f"{fmt(t.get('bebidas_alcoholicas', float('nan')))}, índice general "
         f"{fmt(t['general'])}.",
         f"El portal no publica una subclase solo de restaurantes: el grupo incluye hoteles, "
         f"que han subido {fmt(t['hoteles'])}. La subida de bares y restaurantes por sí "
         "sola probablemente sea menor que la del grupo."])


# ------------------------------------------------------------------------ 4. turismo
def codigo_postal(punto) -> str | None:
    s = capas()["sanitarios"].dropna(subset=["codigo_postal"])
    s = s[s["codigo_postal"].str.fullmatch(r"28\d{3}")]
    idx = s.sindex.query(punto.buffer(S.CP_DISTANCIA_MAX_M), predicate="intersects")
    cerca = s.iloc[idx]
    if cerca.empty:
        return None
    cerca = cerca.assign(d=cerca.distance(punto)).nsmallest(S.CP_VECINOS, "d")
    return cerca["codigo_postal"].mode().iloc[0]


def b_turismo(punto, muni: dict) -> dict:
    cp = codigo_postal(punto)
    a = leer_csv(ORIG / "alojamientos_turisticos" / "alojamientos_turisticos.csv")
    a["tipo"] = a["alojamiento_tipo"].str.strip().replace(
        {"VIVIENDAS DE USO TU": "VIVIENDA DE USO TURÍSTICO"}).str.capitalize()
    a["mun"] = a["localidad"].map(norm_municipio)
    en_mun = a[a["mun"] == norm_municipio(muni["nombre"])]
    en_cp = a[a["cdpostal"].str.strip() == cp] if cp else a.iloc[0:0]
    v = leer_csv(ORIG / "declaraciones_actividad_viviendas_uso_turistico"
                 / "declaraciones_actividad_viviendas_uso_turistico.csv")
    vut_mun = int((v["Localidad"].map(norm_municipio) == norm_municipio(muni["nombre"])).sum())
    por_tipo = lambda d: {k: int(x) for k, x in d["tipo"].value_counts().items()}
    return bloque(
        "turismo", "Turismo: alojamientos del código postal y del municipio", MIXTO,
        [fuente_portal("alojamientos_turisticos"),
         fuente_portal("declaraciones_actividad_viviendas_uso_turistico")],
        f"Código postal {cp or '?'} (aproximado): {len(en_cp)} alojamientos turísticos "
        f"inscritos. Municipio: {len(en_mun)} inscritos y {vut_mun} viviendas de uso "
        "turístico con declaración responsable.",
        {"codigo_postal_aproximado": cp, "alojamientos_cp": por_tipo(en_cp),
         "total_cp": int(len(en_cp)), "alojamientos_municipio": por_tipo(en_mun),
         "total_municipio": int(len(en_mun)), "vut_declaraciones_municipio": vut_mun},
        ["**Aproximación**: no se convierten las direcciones en coordenadas. Se cuentan los "
         "alojamientos del mismo código postal y del mismo municipio, no los del radio.",
         f"El código postal del punto es el más repetido entre los {S.CP_VECINOS} centros "
         "sanitarios más cercanos (no hay límites de códigos postales en abierto): "
         "**estimación**.",
         "Registro de alojamientos (hoteles, hostales, apartamentos y viviendas de uso "
         "turístico inscritas) y declaraciones responsables de viviendas de uso turístico "
         "(conjunto aparte, solo con municipio): son **datos**; puede haber viviendas en "
         "los dos.",
         "No se muestran los nombres de los establecimientos."])


# ------------------------------------------------------------------------ 5. festivos
def b_festivos(muni: dict) -> dict:
    hoy = date.today()
    fin = date(hoy.year + (hoy.month + S.FESTIVOS_MESES - 1) // 12,
               (hoy.month + S.FESTIVOS_MESES - 1) % 12 + 1, min(hoy.day, 28))
    loc = leer_csv(ORIG / "festivos_regionales_locales" / "festivos_locales.csv")
    reg = leer_csv(ORIG / "festivos_regionales_locales" / "festivos_regionales.csv")
    loc = loc[loc["municipio_codigo"] == muni["cod"][2:]]
    filas = [{"fecha": f, "festivo": "local", "ambito": e if c != "00" else muni["nombre"]}
             for f, c, e in zip(loc["fecha_festivo"], loc["entidad_codigo"],
                                loc["entidad_nombre"])]
    filas += [{"fecha": f, "festivo": "regional o nacional", "ambito": n}
              for f, n in zip(reg["fecha_festivo"], reg["festividad"])]
    d = pd.DataFrame(filas).drop_duplicates()
    d["fecha"] = pd.to_datetime(d["fecha"]).dt.date
    anyo_max = max(d["fecha"]).year
    proximos = d[(d["fecha"] >= hoy) & (d["fecha"] <= fin)].sort_values("fecha")
    notas = ["Festivos regionales y locales publicados en el portal (**dato**)."]
    orientacion = []
    if fin.year > anyo_max:
        notas.append(f"El portal solo publica los festivos de {anyo_max}: los de "
                     f"{anyo_max + 1} aún no están. Como orientación se indica cuándo "
                     f"fueron en {anyo_max} los que caerían antes del {fin.strftime('%d/%m/%Y')} "
                     "(**estimación**: muchas fiestas cambian de fecha cada año).")
        x = d[d["fecha"] < date(anyo_max, fin.month, fin.day)].sort_values("fecha")
        orientacion = [{"fecha_2026": r.fecha.isoformat(), "festivo": r.festivo,
                        "ambito": r.ambito} for r in x.itertuples()]
    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    prox = [{"fecha": r.fecha.isoformat(), "dia": dias[r.fecha.weekday()],
             "festivo": r.festivo, "ambito": r.ambito} for r in proximos.itertuples()]
    locales_txt = [p for p in prox if p["festivo"] == "local"]
    return bloque(
        "festivos", f"Festivos de los próximos {S.FESTIVOS_MESES} meses", MIXTO,
        [fuente_portal("festivos_regionales_locales", f"año {anyo_max}")],
        f"{len(prox)} festivos publicados hasta el 31/12/{anyo_max} "
        f"({len(locales_txt)} {'local' if len(locales_txt) == 1 else 'locales'}); los de "
        f"{anyo_max + 1} aún no están publicados."
        if fin.year > anyo_max else f"{len(prox)} festivos en los próximos 12 meses.",
        {"desde": hoy.isoformat(), "hasta": fin.isoformat(), "proximos": prox,
         "orientacion_siguiente_anyo": orientacion,
         "festivos_locales_del_anyo": [{"fecha": r.fecha.isoformat(), "ambito": r.ambito}
                                       for r in d[d["festivo"] == "local"]
                                       .sort_values("fecha").itertuples()]},
        notas)


# ---------------------------------------------------------------------- 6. sector
@lru_cache(maxsize=1)
def demografia() -> tuple[pd.DataFrame, pd.DataFrame]:
    out = []
    for carpeta, col in (("demografia_empresarial_cnae09", "CNAE2009"),
                         ("demografia_empresarial_cnae25", "CNAE2025")):
        d = leer_csv(next((ORIG / carpeta).glob("*.csv")))
        d = d[(d["Concepto"] == "Unidades empresariales") & (d["Indicador"] == "Serie")]
        d = d.rename(columns={col: "rama"})
        d["valor"] = pd.to_numeric(d["Valor"].str.replace(",", "."), errors="coerce")
        d["trimestre"] = d["Año"] + d["Periodo"]
        out.append(d)
    return out[0], out[1]


def b_sector() -> dict:
    d09, d25 = demografia()
    rama = "Servicios de distribución y hostelería"

    def serie(d, medida):
        x = d[d["rama"].str.startswith(rama) & (d["Medida"] == medida)]
        return x.set_index("trimestre")["valor"].sort_index()

    def total(d, medida):
        x = d[d["Medida"] == medida]
        return x.groupby("trimestre")["valor"].sum().sort_index()

    fin09 = serie(d09, "Total al final del trimestre")
    nac09, mue09 = serie(d09, "Nacimientos"), serie(d09, "Muertes")
    tot09 = total(d09, "Total al final del trimestre")
    ult = fin09.index[-1]
    hace1 = f"{int(ult[:4]) - 1}{ult[4:]}"
    pre = f"2019{ult[4:]}"
    var1 = 100 * (fin09[ult] / fin09[hace1] - 1)
    var_pre = 100 * (fin09[ult] / fin09[pre] - 1)
    var1_tot = 100 * (tot09[ult] / tot09[hace1] - 1)
    ult4 = fin09.index[-4:]
    nac, mue = nac09[ult4].sum(), mue09[ult4].sum()

    # 2026 (CNAE-2025): el cambio de clasificación mueve empresas entre ramas («saldo
    # interno»); lo comparable es el saldo externo (altas − bajas + entradas − salidas de
    # la Comunidad), frente a los mismos trimestres del año anterior (CNAE-2009).
    fin25 = serie(d25, "Total al final del trimestre")
    nac25, mue25 = serie(d25, "Nacimientos"), serie(d25, "Muertes")
    ext25, int25 = serie(d25, "Saldo externo"), serie(d25, "Saldo interno")
    s26 = list(fin25.index)
    previos = [f"{int(x[:4]) - 1}{x[4:]}" for x in s26]
    ext09 = serie(d09, "Saldo externo")
    saldo26, saldo25 = float(ext25.sum()), float(ext09.reindex(previos).sum())

    estado = ("crecen" if var1 > 1 else "bajan" if var1 < -1 else "se mantienen")
    fmt = lambda x: f"{x:+.1f} %".replace(".", ",")
    tri = lambda t: f"{t[5]}º trimestre de {t[:4]}"
    return bloque(
        "sector", "Salud del sector (Comunidad de Madrid)", DATO,
        [fuente_portal("demografia_empresarial_cnae09", f"2009–{ult[:4]}"),
         fuente_portal("demografia_empresarial_cnae25", f"{s26[0][:4]}, trimestres "
                                                        f"{', '.join(t[4:] for t in s26)}")],
        f"Las empresas de distribución y hostelería de la Comunidad {estado}: "
        f"{fmt(var1)} en el último año hasta el {tri(ult)} ({fmt(var_pre)} frente a "
        f"2019). En {s26[0][:4]} ({', '.join(x[4:] for x in s26)}) el saldo de altas y "
        f"bajas es de {con_signo(saldo26)} empresas, frente a {con_signo(saldo25)} en los "
        f"mismos trimestres de {int(s26[0][:4]) - 1}.",
        {"rama": rama, "ultimo_trimestre_cnae09": ult,
         "unidades_fin": int(fin09[ult]), "variacion_anual_pct": round(var1, 1),
         "variacion_anual_total_economia_pct": round(var1_tot, 1),
         "variacion_vs_2019_pct": round(var_pre, 1),
         "nacimientos_ultimos_4_trimestres": int(nac),
         "muertes_ultimos_4_trimestres": int(mue),
         "trimestres_2026": s26, "unidades_fin_2026": int(fin25.iloc[-1]),
         "saldo_externo_2026": int(saldo26), "saldo_externo_mismos_trimestres_2025":
             int(saldo25), "reclasificacion_saldo_interno_2026": int(int25.sum()),
         "nacimientos_2026": int(nac25.sum()), "muertes_2026": int(mue25.sum()),
         "serie_anual_cuarto_trimestre": {t[:4]: int(v) for t, v in fin09.items()
                                         if t.endswith("T4")}},
        [f"**Limitación importante**: el portal agrupa la hostelería con el comercio y el "
         f"transporte en «{rama}». No hay datos abiertos de empresas solo de hostelería; "
         "tampoco los afiliados a la Seguridad Social por municipio la separan.",
         f"Último año (serie CNAE-2009): {miles(nac)} altas y {miles(mue)} bajas; el total "
         f"de la economía madrileña varió {fmt(var1_tot)}.",
         f"En 2026 cambia la clasificación (CNAE-2025) y {miles(-int25.sum())} empresas "
         "pasan de esta rama a otras («saldo interno»): no son cierres. Por eso para 2026 "
         "se compara el saldo externo (altas − bajas ± traslados de sede) con los mismos "
         "trimestres del año anterior, y no el total.",
         "Es un dato de toda la Comunidad, no de la zona."])


# ------------------------------------------------------------------------ principal
def municipio(punto) -> dict:
    secc = capas()["secciones"]
    s = secc.iloc[secc.sindex.query(punto, predicate="intersects")]
    if s.empty:
        raise ValueError("El punto no está en la Comunidad de Madrid")
    f = s.iloc[0]
    return {"cod": f["cod_municipio"], "nombre": f["municipio_nombre"],
            "seccion": f["cdgseccion"]}


def informe_local(lat: float, lon: float, radio: float = S.RADIO_M) -> dict:
    """Informe de contexto (parte A) para un punto. Cada bloque lleva su carácter (dato o
    estimación), sus fuentes con fecha y sus notas."""
    x, y = _A_UTM.transform(lon, lat)
    punto = shapely.Point(x, y)
    muni = municipio(punto)
    pr = poblacion_y_renta(punto, radio)
    rc = renta_comunidad()
    return {
        "punto": {"lat": lat, "lon": lon}, "radio_m": radio, "municipio": muni,
        "fecha_informe": date.today().isoformat(),
        "bloques": [b_competencia(punto, radio, muni), b_mercado(punto, radio, pr),
                    b_precios(pr, rc), b_turismo(punto, muni), b_festivos(muni),
                    b_sector()],
    }


def a_markdown(inf: dict) -> str:
    m = inf["municipio"]
    out = [f"## Punto {inf['punto']['lat']}, {inf['punto']['lon']} · {m['nombre']} "
           f"({m['cod']}) · radio {inf['radio_m']:.0f} m", ""]
    for b in inf["bloques"]:
        out += [f"### {b['titulo']} · *{b['caracter']}*", "", b["resumen"], ""]
        d = b["datos"]
        if b["clave"] == "competencia":
            out.append("| Tipo | Locales |\n|---|---|")
            out += [f"| {k} | {v} |" for k, v in d["por_tipo"].items()]
            out += [f"| **Total** | **{d['total']}** |", "",
                    f"Densidad: {dec(d['densidad_km2'], 0)} locales/km² frente a "
                    f"{dec(d['densidad_media_municipio_km2'], 0)} de media en el municipio "
                    f"(×{dec(d['relacion_con_media'] or 0, 2)}).", ""]
            if d["cocinas_osm"]:
                out += ["Cocinas en OSM: " + ", ".join(f"{k} ({v})" for k, v in
                                                       d["cocinas_osm"].items()) + ".", ""]
        elif b["clave"] == "turismo":
            for k, t in (("alojamientos_cp", f"Código postal {d['codigo_postal_aproximado']}"),
                         ("alojamientos_municipio", "Municipio")):
                out.append(f"- {t}: " + (", ".join(f"{a} {n}" for a, n in d[k].items())
                                         or "ninguno"))
            out.append("")
        elif b["clave"] == "festivos":
            out += [f"- {p['fecha']} ({p['dia']}): {p['ambito']} ({p['festivo']})"
                    for p in d["proximos"]]
            if d["orientacion_siguiente_anyo"]:
                loc = [o for o in d["orientacion_siguiente_anyo"] if o["festivo"] == "local"]
                out.append("- Orientación para el año siguiente (fiestas locales de 2026): "
                           + (", ".join(f"{o['fecha_2026']} ({o['ambito']})" for o in loc)
                              or "sin fiestas locales en ese periodo"))
            out.append("")
        out += [f"- {n}" for n in b["notas"]]
        out += ["", "Fuentes: " + "; ".join(
            f"[{f['nombre']}]({f['enlace']}) ({f['licencia']}; "
            + (f"{f['periodo']}; " if f.get("periodo") else "")
            + f"descargado el {f['descargado']})" for f in b["fuentes"]), ""]
    return "\n".join(out)


def main(argv: list[str]) -> int:
    lat, lon = float(argv[0]), float(argv[1])
    inf = informe_local(lat, lon)
    if "--json" in argv:
        print(json.dumps(inf, ensure_ascii=False, indent=2, default=str))
    else:
        print(a_markdown(inf))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
