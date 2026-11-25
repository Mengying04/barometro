"""BARómetro: contraste de la «gente que pasa» con los aforos reales de peatones.

Compara el perfil por horas del modelo (perfil_horario(), gente que pasa, sin tipo de local)
con los conteos de las estaciones permanentes de peatones del Ayuntamiento de Madrid. NO
cambia ningún cálculo ni supuesto: solo llama a perfil_horario() en la posición de cada
estación y compara.

Fuentes (datos.madrid.es, CC BY 4.0, «Fuente: Ayuntamiento de Madrid»):
  - «Aforos de peatones y bicicletas» (300321-0-aforos-peatones-bicicletas): conteos por
    hora de las estaciones permanentes de peatones, con su posición.
  - «Calendario laboral» (300082-0-calendario_laboral): festivos de la ciudad de Madrid,
    para quitar los martes, miércoles y jueves festivos.
Se descargan por la API oficial del portal (CKAN, package_show) a
datos/originales/madrid_aforos_peatones/ (no se suben a GitHub).

Qué se compara (año AÑO, el último completo; ver docs/registro/2026-11-24-contraste-aforos-
peatones.md):
  a) Forma del día: correlación hora a hora (Pearson, 24 horas) en cada estación y si la
     hora punta coincide (±1 hora).
  b) Orden entre estaciones: correlación de rangos (Spearman) del total del laborable y
     cuántas estaciones quedan en el mismo tercio (alto, medio, bajo).
  c) Fin de semana: cociente sábado/laborable y domingo/laborable en el conteo y en el
     modelo.
Las cifras absolutas no se comparan como acierto: la estación cuenta un punto concreto de
una calle (a menudo una sola acera) y el modelo, toda la gente que pasa en un círculo de
300 m.

Uso:  python src/contraste_aforos.py               # descarga si falta y escribe las tablas
      python src/contraste_aforos.py --descargar   # vuelve a descargar
      python src/contraste_aforos.py --fuentes     # además, anota las fuentes en docs/fuentes.md
"""

from __future__ import annotations

import json
import sys
from datetime import date

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

import perfil_horario as P
from fecha import hoy as fecha_hoy
from descargar_datos import DIR_ORIGINALES, _abrir, actualizar_bloque, descargar
from procesar import PROC

AÑO = 2023                      # último año completo publicado (2024 llega solo a junio)
AFOROS = "300321-0-aforos-peatones-bicicletas"
CALENDARIO = "300082-0-calendario_laboral"
API = "https://datos.madrid.es/api/3/action/package_show?id="
CARPETA = DIR_ORIGINALES / "madrid_aforos_peatones"

# Tipos de día del conteo y su equivalente en el modelo (supuestos.DIAS_PERFIL)
DIAS = {"laborable": "laborable", "sabado": "fin_de_semana", "domingo": "domingo"}
DIAS_LAB = {1, 2, 3}            # martes, miércoles y jueves (lunes = 0)
MIN_DIAS = 8                    # días válidos mínimos de un tipo para usar la estación
# Limpieza de días (ver limpiar()):
HORAS_DIA = (8, 21)             # horas de día en las que un cero es sospechoso
MIN_MEDIANA_CERO = 20           # …si a esa hora la estación suele contar al menos esto
MIN_FRACCION_TOTAL = 0.2        # día con menos del 20 % del total mediano: corte de datos
HORAS_R_DIA = slice(7, 23)      # horas de 7 a 22 para la correlación «solo de día»


# ------------------------------------------------------------------- descarga
def _json(url: str) -> dict:
    with _abrir(url) as r:
        return json.load(r)


def descargar_fuentes(forzar: bool = False) -> dict:
    """Descarga la ficha y los ficheros necesarios por la API del portal. Devuelve las
    fichas (para docs/fuentes.md)."""
    CARPETA.mkdir(parents=True, exist_ok=True)
    fichas = {}
    for ident, nombre in ((AFOROS, "ficha_aforos.json"), (CALENDARIO, "ficha_calendario.json")):
        ruta = CARPETA / nombre
        if forzar or not ruta.exists():
            ruta.write_text(json.dumps(_json(API + ident)["result"], ensure_ascii=False,
                                       indent=1), encoding="utf-8")
        fichas[ident] = json.loads(ruta.read_text(encoding="utf-8"))
    quiero = {f"Aforos peatones. {AÑO}|CSV": f"peatones_{AÑO}.csv",
              "Aforos de peatones. Contenido y estructura del fichero|PDF": "estructura.pdf"}
    for r in fichas[AFOROS]["resources"]:
        clave = f"{(r.get('description') or '').strip()}|{(r.get('format') or '').upper()}"
        if clave in quiero and (forzar or not (CARPETA / quiero[clave]).exists()):
            descargar(r["url"], CARPETA / quiero[clave])
    for r in fichas[CALENDARIO]["resources"]:
        if (r.get("format") or "").upper() == "CSV" and "2013" in (r.get("description") or ""):
            if forzar or not (CARPETA / "calendario_laboral.csv").exists():
                descargar(r["url"], CARPETA / "calendario_laboral.csv")
    falta = [n for n in [*quiero.values(), "calendario_laboral.csv"] if not (CARPETA / n).exists()]
    if falta:
        raise SystemExit(f"No se han encontrado en el portal: {falta}")
    return fichas


# ------------------------------------------------------------------- lectura
def _texto(s: str) -> str:
    """Algunos ficheros del portal llevan el texto en UTF-8 leído como Latin-1 («MartÃ­n»)."""
    if not isinstance(s, str):
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def _coord(s: str, enteros: int) -> float:
    """Las coordenadas vienen con puntos de miles («40.417.386», «-3.707.141»): se quitan y
    se pone la coma decimal tras los `enteros` primeros dígitos."""
    s = str(s).strip()
    signo = -1 if s.startswith("-") else 1
    d = s.lstrip("-").replace(".", "").replace(",", "")
    return signo * float(f"{d[:enteros]}.{d[enteros:]}")


def leer_aforos() -> pd.DataFrame:
    d = pd.read_csv(CARPETA / f"peatones_{AÑO}.csv", sep=";", encoding="utf-8-sig", dtype=str)
    d.columns = [_texto(c) for c in d.columns]
    d["t"] = pd.to_datetime(d["fecha"], format="%d/%m/%Y %H:%M")
    d["peatones"] = pd.to_numeric(d["peatones"], errors="coerce")
    d["lat"] = d["latitude"].map(lambda s: _coord(s, 2))
    d["lon"] = d["longitude"].map(lambda s: _coord(s, 1))
    d["obs"] = d["observaciones_direccion"].map(_texto).fillna("").str.strip()
    return d[["identificador", "t", "peatones", "lat", "lon", "obs"]]


def festivos() -> set[date]:
    c = pd.read_csv(CARPETA / "calendario_laboral.csv", sep=";", encoding="utf-8-sig", dtype=str)
    col = [x for x in c.columns if "festivo" in x.lower()][0]
    f = c[c[col].str.strip().str.lower() == "festivo"]
    return set(pd.to_datetime(f["Dia"], format="%d/%m/%Y").dt.date)


# ------------------------------------------------------------------- limpieza
def limpiar(d: pd.DataFrame, fest: set[date]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Días válidos por estación (una fila por estación y día, 24 columnas de horas) y el
    recuento de días quitados por motivo. Un día se quita si:
      - le falta alguna hora o tiene horas repetidas o vacías («huecos»);
      - tiene un cero en una hora de día (8 a 21) en la que la estación suele contar al
        menos MIN_MEDIANA_CERO peatones («ceros sospechosos»);
      - su total es menor que MIN_FRACCION_TOTAL del total mediano de ese tipo de día en esa
        estación («corte de datos»).
    Solo cuentan martes, miércoles y jueves no festivos, sábados no festivos y domingos."""
    d = d.copy()
    d["dia"] = d["t"].dt.date
    d["hora"] = d["t"].dt.hour
    dw = d["t"].dt.day_of_week
    d["tipo"] = np.select([dw.isin(DIAS_LAB), dw == 5, dw == 6],
                          ["laborable", "sabado", "domingo"], "otro")
    d.loc[d["dia"].isin(fest) & (d["tipo"] != "domingo"), "tipo"] = "festivo"
    d = d[d["tipo"].isin(DIAS)]
    motivos = []
    rep = d.duplicated(["identificador", "t"], keep=False)
    tabla = (d[~rep].pivot_table(index=["identificador", "dia", "tipo"], columns="hora",
                                 values="peatones", aggfunc="first"))
    tabla = tabla.reindex(columns=range(24))
    dias_rep = set(d.loc[rep, ["identificador", "dia"]].itertuples(index=False, name=None))
    huecos = tabla.isna().any(axis=1) | pd.Series(
        [(i, di) in dias_rep for i, di, _ in tabla.index], index=tabla.index)
    motivos.append(("huecos", huecos))
    ok = tabla[~huecos]
    med_h = ok.groupby(level=["identificador", "tipo"]).median()
    dia_h = ok.loc[:, HORAS_DIA[0]:HORAS_DIA[1]]
    ref = med_h.loc[:, HORAS_DIA[0]:HORAS_DIA[1]].reindex(
        pd.MultiIndex.from_arrays([dia_h.index.get_level_values(0),
                                   dia_h.index.get_level_values(2)])).to_numpy()
    ceros = pd.Series(((dia_h.to_numpy() == 0) & (ref >= MIN_MEDIANA_CERO)).any(axis=1),
                      index=ok.index)
    motivos.append(("ceros sospechosos", ceros.reindex(tabla.index, fill_value=False)))
    ok = ok[~ceros]
    tot = ok.sum(axis=1)
    med_t = tot.groupby(level=["identificador", "tipo"]).transform("median")
    corte = tot < MIN_FRACCION_TOTAL * med_t
    motivos.append(("corte de datos", corte.reindex(tabla.index, fill_value=False)))
    ok = ok[~corte]
    quitados = pd.DataFrame({m: s.groupby(level="tipo").sum() for m, s in motivos}).fillna(0)
    quitados["válidos"] = ok.groupby(level="tipo").size()
    quitados["total"] = tabla.groupby(level="tipo").size()
    return ok, quitados.astype(int).reindex(list(DIAS))


# ------------------------------------------------------------------- comparación
def estaciones(d: pd.DataFrame) -> pd.DataFrame:
    """Una fila por estación: posición, tipo de punto (acera par o impar, calle peatonal o
    sin dato) y distrito (de las secciones censales del proyecto; sin nombres de calle)."""
    e = d.groupby("identificador").agg(lat=("lat", "first"), lon=("lon", "first"),
                                       obs=("obs", "first"))
    g = gpd.read_parquet(PROC / "secciones_censales.parquet").to_crs(25830)
    pts = gpd.GeoDataFrame(e, geometry=[shapely.Point(x, y) for x, y in
                                         zip(e["lon"], e["lat"])], crs=4326).to_crs(25830)
    j = gpd.sjoin(pts, g[["cod_distrito", "geometry"]], how="left", predicate="within")
    e["distrito"] = j["cod_distrito"].astype(str).str[-2:].groupby(level=0).first()
    e["punto"] = e["obs"].replace({"": "sin dato"}).str.lower()
    return e.drop(columns="obs")


def modelo(e: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Gente que pasa por hora del modelo en la posición de cada estación (24 × estación),
    para cada tipo de día. Sin tipo de local: perfil_horario(), tal cual."""
    out = {t: {} for t in DIAS}
    cache = {}
    for ident, f in e.iterrows():
        clave = (round(f["lat"], 6), round(f["lon"], 6))
        if clave not in cache:
            cache[clave] = P.perfil_horario(*clave)["horas"]["total"]
        for t, dm in DIAS.items():
            out[t][ident] = cache[clave].loc[dm].astype(float).to_numpy()
    return {t: pd.DataFrame(v, index=range(24)) for t, v in out.items()}


def comparar(ok: pd.DataFrame, mod: dict[str, pd.DataFrame], e: pd.DataFrame) -> dict:
    medias = {t: ok.xs(t, level="tipo").groupby(level="identificador").mean().T
              for t in DIAS}
    n_dias = {t: ok.xs(t, level="tipo").groupby(level="identificador").size() for t in DIAS}
    filas = []
    for ident in e.index:
        fila = {"estacion": ident.replace("PERM_", "").replace("_PM0", "-"),
                "distrito": e.at[ident, "distrito"], "punto": e.at[ident, "punto"]}
        for t in DIAS:
            n = int(n_dias[t].get(ident, 0))
            fila[f"dias_{t}"] = n
            if n < MIN_DIAS:
                continue
            c, m = medias[t][ident].to_numpy(), mod[t][ident].to_numpy()
            fila[f"r_{t}"] = float(np.corrcoef(c, m)[0, 1])
            # Solo las horas de día: sin el contraste noche/día, que infla la r de 24 horas.
            fila[f"rdia_{t}"] = float(np.corrcoef(c[HORAS_R_DIA], m[HORAS_R_DIA])[0, 1])
            hc, hm = int(np.argmax(c)), int(np.argmax(m))
            fila[f"punta_conteo_{t}"], fila[f"punta_modelo_{t}"] = hc, hm
            fila[f"punta_ok_{t}"] = min(abs(hc - hm), 24 - abs(hc - hm)) <= 1
            fila[f"total_conteo_{t}"], fila[f"total_modelo_{t}"] = float(c.sum()), float(m.sum())
        filas.append(fila)
    t = pd.DataFrame(filas).set_index("estacion")
    for x in ("sabado", "domingo"):
        for q in ("conteo", "modelo"):
            t[f"{x}/lab_{q}"] = t[f"total_{q}_{x}"] / t[f"total_{q}_laborable"]
    lab = t.dropna(subset=["total_conteo_laborable"])
    # Spearman = Pearson entre los rangos (sin scipy, que el proyecto no usa)
    rho = lab["total_conteo_laborable"].rank().corr(lab["total_modelo_laborable"].rank())
    terc = pd.DataFrame({q: pd.qcut(lab[f"total_{q}_laborable"].rank(method="first"), 3,
                                    labels=["bajo", "medio", "alto"])
                         for q in ("conteo", "modelo")})
    t["tercio_conteo"], t["tercio_modelo"] = terc["conteo"], terc["modelo"]
    return {"tabla": t, "spearman": float(rho), "n_lab": len(lab),
            "mismo_tercio": int((terc["conteo"] == terc["modelo"]).sum()),
            "medias": medias, "modelo": mod}


# ------------------------------------------------------------------- tablas
def _f(x, nd=2):
    return "—" if x is None or (isinstance(x, float) and np.isnan(x)) else \
        f"{x:.{nd}f}".replace(".", ",")


def _miles(x):
    return "—" if x is None or np.isnan(x) else f"{round(x):,}".replace(",", ".")


def informe(r: dict, quitados: pd.DataFrame) -> str:
    t = r["tabla"]
    out = [f"## Días quitados ({AÑO})", "",
           "| Tipo de día | Días-estación | Huecos | Ceros sospechosos | Corte de datos | Válidos |",
           "|---|---|---|---|---|---|"]
    for tipo, q in quitados.iterrows():
        out.append(f"| {tipo} | {q['total']} | {q['huecos']} | {q['ceros sospechosos']} | "
                   f"{q['corte de datos']} | {q['válidos']} |")
    out += ["", "## a) Forma del día (correlación hora a hora y hora punta)", "",
            "| Estación | Distrito | Punto | Días lab. | r lab. | r lab. 7–22 h | Punta conteo / modelo (lab.) "
            "| r sáb. | Punta sáb. | r dom. | Punta dom. |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for est, f in t.iterrows():
        def punta(x):
            if np.isnan(f.get(f"punta_conteo_{x}", np.nan)):
                return "—"
            return (f"{int(f[f'punta_conteo_{x}'])} / {int(f[f'punta_modelo_{x}'])} h "
                    + ("✓" if f[f"punta_ok_{x}"] else "✗"))
        out.append(f"| {est} | {f['distrito']} | {f['punto']} | {int(f['dias_laborable'])} | "
                   f"{_f(f.get('r_laborable'))} | {_f(f.get('rdia_laborable'))} | {punta('laborable')} | {_f(f.get('r_sabado'))} | "
                   f"{punta('sabado')} | {_f(f.get('r_domingo'))} | {punta('domingo')} |")
    res = ["", "**Resumen de la forma del día:**", ""]
    for x, nom in (("laborable", "Laborable"), ("sabado", "Sábado"), ("domingo", "Domingo")):
        v = t[f"r_{x}"].dropna()
        p = t[f"punta_ok_{x}"].dropna().astype(bool)
        vd = t[f"rdia_{x}"].dropna()
        res.append(f"- {nom}: {len(v)} estaciones; r mediana {_f(v.median())} (de {_f(v.min())} "
                   f"a {_f(v.max())}); r ≥ 0,7 en {int((v >= 0.7).sum())}; solo de 7 a 22 h, "
                   f"r mediana {_f(vd.median())}; hora punta a ±1 h en {int(p.sum())} de {len(p)}.")
    out += res
    out += ["", "## b) Orden entre estaciones (total del laborable)", "",
            f"Spearman entre el total del conteo y el del modelo: **{_f(r['spearman'])}** "
            f"({r['n_lab']} estaciones). Mismo tercio (alto, medio, bajo): "
            f"**{r['mismo_tercio']} de {r['n_lab']}**.", "",
            "| Estación | Peatones/día (conteo) | Gente que pasa/día (modelo, 300 m) | Tercio conteo | Tercio modelo |",
            "|---|---|---|---|---|"]
    for est, f in t.sort_values("total_conteo_laborable", ascending=False).iterrows():
        if np.isnan(f["total_conteo_laborable"]):
            continue
        out.append(f"| {est} | {_miles(f['total_conteo_laborable'])} | "
                   f"{_miles(f['total_modelo_laborable'])} | {f['tercio_conteo']} | "
                   f"{f['tercio_modelo']} |")
    out += ["", "Las cifras no se comparan entre sí como acierto: la estación cuenta un punto "
            "de una calle (a menudo una sola acera) y el modelo, toda la gente que pasa en un "
            "círculo de 300 m.", "",
            "## c) Fin de semana (cociente frente al laborable)", "",
            "| Estación | Sáb./lab. conteo | Sáb./lab. modelo | Dom./lab. conteo | Dom./lab. modelo |",
            "|---|---|---|---|---|"]
    for est, f in t.iterrows():
        out.append(f"| {est} | {_f(f.get('sabado/lab_conteo'))} | {_f(f.get('sabado/lab_modelo'))} | "
                   f"{_f(f.get('domingo/lab_conteo'))} | {_f(f.get('domingo/lab_modelo'))} |")
    for x, nom in (("sabado", "Sábado"), ("domingo", "Domingo")):
        c, m = t[f"{x}/lab_conteo"].dropna(), t[f"{x}/lab_modelo"].dropna()
        both = t[[f"{x}/lab_conteo", f"{x}/lab_modelo"]].dropna()
        out.append(f"\n- {nom}/laborable: mediana {_f(c.median())} en el conteo y "
                   f"{_f(m.median())} en el modelo; el modelo da un cociente menor que el "
                   f"conteo en {int((both.iloc[:, 1] < both.iloc[:, 0]).sum())} de {len(both)} "
                   f"estaciones.")
    return "\n".join(out)


def anotar_fuentes(fichas: dict) -> None:
    a, c = fichas[AFOROS], fichas[CALENDARIO]
    cob = a.get("temporal_coverage") or [{}]
    hoy = fecha_hoy().isoformat()
    actualizar_bloque("contraste", [
        "## Fuentes del contraste con aforos de peatones (no las usa la aplicación)", "",
        "Solo las usa [`src/contraste_aforos.py`](../src/contraste_aforos.py) para contrastar "
        "la gente que pasa del modelo con conteos reales. Se descargan con la API del portal "
        "(CKAN, `package_show`) en `datos/originales/madrid_aforos_peatones/` y no se suben a "
        "GitHub.", "",
        f"### {a['title']} (Ayuntamiento de Madrid)", "",
        f"- Ficha: https://datos.madrid.es/dataset/{AFOROS}",
        f"- Licencia: {a.get('license_title')}. Citar: «Fuente: Ayuntamiento de Madrid».",
        f"- Datos: estaciones permanentes de peatones, un conteo por estación y hora; "
        f"cobertura publicada {cob[0].get('start', '?')} a {cob[0].get('end', '?')} (el "
        "último trimestre publicado es provisional). Se usa el año "
        f"{AÑO} (`peatones_{AÑO}.csv`) y la estructura del fichero (`estructura.pdf`).",
        "- Aviso de la ficha: entre agosto de 2021 y septiembre de 2022 se cambiaron los "
        "detectores y no se recomienda comparar datos de antes y después.",
        f"- Ficha modificada el {a.get('metadata_modified', '?')[:10]}; descargado el {hoy}.", "",
        f"### {c['title']} (Ayuntamiento de Madrid)", "",
        f"- Ficha: https://datos.madrid.es/dataset/{CALENDARIO}",
        f"- Licencia: {c.get('license_title')}. Citar: «Fuente: Ayuntamiento de Madrid».",
        f"- Datos: festivos de la ciudad de Madrid de 2013 a 2027 (`calendario_laboral.csv`); "
        f"se usan los de {AÑO}.",
        f"- Ficha modificada el {c.get('metadata_modified', '?')[:10]}; descargado el {hoy}."])


def main(argv: list[str]) -> int:
    fichas = descargar_fuentes(forzar="--descargar" in argv)
    if "--fuentes" in argv:
        anotar_fuentes(fichas)
    d = leer_aforos()
    ok, quitados = limpiar(d, festivos())
    e = estaciones(d)
    r = comparar(ok, modelo(e), e)
    print(informe(r, quitados))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
