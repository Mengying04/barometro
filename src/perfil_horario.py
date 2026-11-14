"""Perfil por horas: cuánta gente pasa cerca de un punto a cada hora, por tipo de cliente.

    from perfil_horario import perfil_horario
    r = perfil_horario(40.4046, -3.6106)
    r["horas"]      # 72 filas (laborable, sábado y domingo × 24 horas) × tipos de cliente
                    # (el sábado se llama «fin_de_semana»: ver supuestos.DIAS_PERFIL)
    r["franjas"]    # lo mismo agrupado en franjas del día
    r["confianza"]  # confianza de cada tipo de cliente, para el horario y la cantidad

Desde la terminal:  python src/perfil_horario.py 40.4046 -3.6106

TODO EL RESULTADO ES UNA ESTIMACIÓN («pasos» de personas por hora cerca del punto),
útil para comparar horas y tipos de cliente entre sí, no como un aforo real. Los
supuestos están en src/supuestos.py. Necesita los datos de src/procesar.py y
src/procesar_perfil.py.
"""

from __future__ import annotations

import math
import sys
from functools import lru_cache

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer

import supuestos as S
from procesar import CRS, PROC
from procesar_perfil import ENSENANZAS, col_ensenanza

DIAS = S.DIAS_PERFIL   # laborable, «fin_de_semana» (= sábado) y domingo
TIPOS = list(S.TIPOS_CLIENTE)
NOMBRE_DIA = {"laborable": "laborable", "fin_de_semana": "sábado", "domingo": "domingo"}
_A_UTM = Transformer.from_crs(4326, CRS, always_xy=True)


def vec(p: dict[int, float]) -> np.ndarray:
    v = np.zeros(24)
    for h, x in p.items():
        v[int(h) % 24] += x
    return v


# ------------------------------------------------------------------------------ datos
@lru_cache(maxsize=1)
def capas() -> dict[str, gpd.GeoDataFrame]:
    return {
        "educativos": gpd.read_parquet(PROC / "centros_educativos_alumnos.parquet"),
        "sanitarios": gpd.read_parquet(PROC / "centros_sanitarios.parquet"),
        "dea": gpd.read_parquet(PROC / "desfibriladores_horario.parquet"),
        "paradas": gpd.read_parquet(PROC / "salidas_paradas.parquet"),
        "secciones": gpd.read_parquet(PROC / "secciones_censales.parquet",
                                      columns=["cdgseccion", "poblacion", "geometry"]),
        "campus": gpd.read_parquet(PROC / "campus_universitarios.parquet"),
    }


def cerca(g: gpd.GeoDataFrame, punto, radio: float) -> gpd.GeoDataFrame:
    idx = g.sindex.query(punto.buffer(radio), predicate="intersects")
    sub = g.iloc[idx].copy()
    sub["distancia_m"] = sub.distance(punto)
    sub = sub[sub["distancia_m"] <= radio]
    sub["peso"] = sub["distancia_m"].map(lambda d: S.peso_distancia(d, radio))
    return sub


# ------------------------------------------------------------- horarios de los DEA
def mascara(abre: float, cierra: float) -> np.ndarray:
    """Horas (0-23) en las que el sitio está abierto, con media hora de margen para
    llegar y salir. Un cierre > 24 pasa a la madrugada siguiente."""
    m = np.zeros(24)
    for h in range(48):
        if h + 1 > abre - 0.5 and h < cierra + 0.5:
            m[h % 24] = 1
    return m


def con_mascara(p: np.ndarray, abre, cierra) -> np.ndarray:
    """Recorta un perfil típico a las horas de apertura conservando el total."""
    if pd.isna(abre) or pd.isna(cierra) or p.sum() == 0:
        return p
    r = p * mascara(abre, cierra)
    return r * p.sum() / r.sum() if r.sum() > 0 else p


def jornada(abre: float, cierra: float) -> np.ndarray:
    """Pasos por trabajador a partir de la hora de apertura y cierre (ver supuestos)."""
    if cierra - abre > S.JORNADA_MAX_UN_TURNO_H:
        mitad = (abre + cierra) / 2
        return 0.5 * jornada(abre, mitad) + 0.5 * jornada(mitad, cierra)
    v = np.zeros(24)
    llegada = math.floor(abre - 0.25)
    v[llegada % 24] += S.JORNADA_LLEGADA[0]
    v[(llegada + 1) % 24] += S.JORNADA_LLEGADA[1]
    v[math.floor(cierra - 0.5) % 24] += S.JORNADA_SALIDA[0]
    v[math.floor(cierra) % 24] += S.JORNADA_SALIDA[1]
    ini_comida, fin_comida = S.COMIDAS["comida"]
    if abre <= ini_comida and cierra >= fin_comida and cierra - abre >= 8:
        v[ini_comida] += S.SALEN_A_COMER
        v[ini_comida + 1] += S.SALEN_A_COMER
    return v


def perfil_dea(fila, dia: str) -> np.ndarray:
    """Pasos por persona y hora de un sitio del registro de desfibriladores."""
    perfil = fila["perfil"]
    lab = dia == "laborable"
    suf = {"laborable": "lab", "fin_de_semana": "fds", "domingo": "dom"}[dia]
    abre, cierra = fila[f"abre_{suf}"], fila[f"cierra_{suf}"]
    if not lab and pd.notna(fila[suf]) and not bool(fila[suf]):
        return np.zeros(24)
    tiene_rango = fila["horario_tipo"] in ("rango", "expresion") and not pd.isna(abre)

    if fila["horario_tipo"] == "eventos" or perfil == "eventos":
        p = vec(S.PERFIL_DEA[dia]["eventos"])
        f = S.EVENTOS_PROB[dia] * S.EVENTOS_OCUPACION
        return con_mascara(p, abre, cierra) * f if tiene_rango else p * f
    if perfil in ("oficina", "administracion") and tiene_rango:
        p = jornada(abre, cierra)
        return p if lab else p * S.PLANTILLA_FIN_DE_SEMANA
    if perfil == "universidad":
        p = vec(S.PERFIL_EDUCATIVO["universidad"]) * factor_educativo(dia)
        return con_mascara(p, abre, cierra) if tiene_rango else p
    p = vec(S.PERFIL_DEA[dia][perfil])
    return con_mascara(p, abre, cierra) if tiene_rango else p


# --------------------------------------------------------------- cálculo por tipo
def factor_educativo(dia: str) -> float:
    return {"laborable": 1.0, "fin_de_semana": S.EDUCATIVO_FIN_DE_SEMANA,
            "domingo": S.EDUCATIVO_DOMINGO}[dia]


def factor_hospital(dia: str) -> float:
    return {"laborable": 1.0, "fin_de_semana": S.HOSPITAL_FIN_DE_SEMANA,
            "domingo": S.HOSPITAL_DOMINGO}[dia]


def padres_ninos(c: dict, punto, radio) -> tuple[dict, int]:
    out = {d: np.zeros(24) for d in DIAS}
    e = cerca(c["educativos"], punto, radio)
    for _, f in e.iterrows():
        v = np.zeros(24)
        for ens in ENSENANZAS:
            n = f[col_ensenanza(ens)]
            if n > 0:
                v += n * (1 + S.ACOMPANANTES.get(ens, 0)) * vec(S.PERFIL_EDUCATIVO[ens])
        if f["alumnos_otros"] > 0:
            v += f["alumnos_otros"] * vec(S.PERFIL_EDUCATIVO[f["perfil_otros"]])
        for d in DIAS:
            out[d] += f["peso"] * v * factor_educativo(d)
    return out, len(e)


def pacientes(c: dict, punto, radio) -> tuple[dict, int]:
    out = {d: np.zeros(24) for d in DIAS}
    s = cerca(c["sanitarios"], punto, radio)
    n = 0
    for _, f in s.iterrows():
        pac = S.PACIENTES_DIA.get(f["centro_tipo"], S.PACIENTES_DIA_OTROS)
        if pac == 0:
            continue
        n += 1
        horario = S.HORARIO_SANITARIO.get(f["centro_tipo"], "consulta")
        for d in DIAS:
            factor = factor_hospital(d) if horario == "hospital" else 1.0
            out[d] += f["peso"] * pac * factor * vec(S.PERFIL_SANITARIO[d][horario])
    return out, n


def desde_dea(c: dict, punto, radio) -> tuple[dict, dict]:
    out = {t: {d: np.zeros(24) for d in DIAS} for t in TIPOS}
    cuenta = {t: 0 for t in TIPOS}
    for _, f in cerca(c["dea"], punto, radio).iterrows():
        cuenta[f["cliente"]] += 1
        for d in DIAS:
            out[f["cliente"]][d] += f["peso"] * f["personas_dia"] * perfil_dea(f, d)
    return out, cuenta


def viajeros(c: dict, punto, radio) -> tuple[dict, int, int]:
    """Pasos de vehículos × personas por paso (calibradas con la demanda real) × peso de
    la parada, que cae más deprisa con la distancia que el de los demás sitios. Devuelve
    también cuántas paradas hay y en cuántas los pasos son estimados (línea 3 de Metro,
    reconstruida porque no tiene viajes en el GTFS)."""
    p = cerca(c["paradas"], punto, radio)
    p["peso"] = p["distancia_m"].map(lambda d: S.peso_parada(d, radio)).astype(float)
    out = {}
    for d, pre in (("laborable", "lab"), ("fin_de_semana", "sab"), ("domingo", "dom")):
        x = p[[f"{pre}_{h:02d}" for h in range(24)]].to_numpy()
        f = (p["peso"] * p[f"pp_{pre}"].astype(float)).to_numpy()[:, None]
        out[d] = (x * f).sum(axis=0)
    n_est = int(p["origen_pasos"].str.contains("estimación").sum()) \
        if "origen_pasos" in p else 0
    return out, len(p), n_est


def fraccion_ponderada(geoms: np.ndarray, punto, radio) -> np.ndarray:
    """Para cada polígono: fracción de su superficie dentro del radio, sumando por
    anillos de ANCHO_ANILLO_M y multiplicando cada anillo por su peso por distancia."""
    area = shapely.area(geoms)
    total = np.zeros(len(geoms))
    r0 = 0.0
    while r0 < radio:
        r1 = min(r0 + S.ANCHO_ANILLO_M, radio)
        anillo = punto.buffer(r1, quad_segs=32)
        if r0 > 0:
            anillo = anillo.difference(punto.buffer(r0, quad_segs=32))
        dentro = shapely.area(shapely.intersection(geoms, anillo))
        total += dentro / area * S.peso_distancia((r0 + r1) / 2, radio)
        r0 = r1
    return total


def universitarios(c: dict, punto, radio) -> tuple[dict, int, float]:
    """Estudiantes de los campus que tocan el radio, repartidos por igual en la
    superficie de cada campus (como los vecinos) y con el horario universitario."""
    cp = c["campus"]
    cp = cp.iloc[cp.sindex.query(punto.buffer(radio), predicate="intersects")]
    est = float((cp["estudiantes"].to_numpy(dtype=float)
                 * fraccion_ponderada(cp.geometry.to_numpy(), punto, radio)).sum())
    v = est * S.UNIVERSIDAD_ASISTENCIA * vec(S.PERFIL_EDUCATIVO["universidad"])
    return {d: v * factor_educativo(d) for d in DIAS}, len(cp), est


def vecinos(c: dict, punto, radio) -> tuple[dict, float]:
    """Población de las secciones que tocan el radio, proporcional a la superficie que
    queda dentro de cada anillo de 50 m y ponderada por la distancia del anillo."""
    secc = c["secciones"]
    secc = secc.iloc[secc.sindex.query(punto.buffer(radio), predicate="intersects")]
    pobl = secc["poblacion"].fillna(0).to_numpy(dtype=float)
    total = float((pobl * fraccion_ponderada(secc.geometry.to_numpy(), punto, radio)).sum())
    out = {}
    for d in DIAS:
        rep = vec(S.REPARTO_VECINOS[d])
        out[d] = total * S.PASOS_VECINO[d] * rep / rep.sum()
    return out, total


# ------------------------------------------------------------------------ principal
def perfil_horario(lat: float, lon: float, radio: float = S.RADIO_M) -> dict:
    """Tabla de 24 horas por tipo de cliente para laborable, sábado («fin_de_semana») y
    domingo (ESTIMACIÓN).

    Devuelve un diccionario con:
      horas:     DataFrame con índice (dia, hora) y una columna por tipo de cliente +
                 «total»; valores = personas que pasan cerca en esa hora (estimación).
      franjas:   lo mismo sumado por franjas del día.
      confianza: confianza de cada tipo de cliente para el horario y para la cantidad,
                 y por qué.
      elementos: cuántos elementos de cada fuente hay dentro del radio.
      punto, radio_m.
    """
    x, y = _A_UTM.transform(lon, lat)
    punto = shapely.Point(x, y)
    c = capas()
    res = {t: {d: np.zeros(24) for d in DIAS} for t in TIPOS}

    pn, n_edu = padres_ninos(c, punto, radio)
    un, n_campus, est_campus = universitarios(c, punto, radio)
    pa, n_san = pacientes(c, punto, radio)
    dea, n_dea = desde_dea(c, punto, radio)
    vi, n_par, n_par_est = viajeros(c, punto, radio)
    ve, pob = vecinos(c, punto, radio)
    for d in DIAS:
        res["padres_ninos"][d] += pn[d]
        res["universitarios"][d] += un[d]
        res["pacientes"][d] += pa[d]
        res["viajeros"][d] += vi[d]
        res["vecinos"][d] += ve[d]
        for t in TIPOS:
            res[t][d] += dea[t][d]

    filas = []
    for d in DIAS:
        for h in range(24):
            filas.append({"dia": d, "hora": h, **{t: res[t][d][h] for t in TIPOS}})
    horas = pd.DataFrame(filas).set_index(["dia", "hora"])
    horas["total"] = horas[TIPOS].sum(axis=1)
    horas = horas.round().astype(int)

    franja_de = {h: f for f, hs in S.FRANJAS.items() for h in hs}
    franjas = horas.reset_index()
    franjas["franja"] = pd.Categorical(franjas["hora"].map(franja_de),
                                       categories=list(S.FRANJAS), ordered=True)
    franjas = franjas.groupby(["dia", "franja"], observed=False)[TIPOS + ["total"]].sum()

    confianza = pd.DataFrame(
        [{"tipo": t, "nombre": S.TIPOS_CLIENTE[t],
          "confianza_horario": S.CONFIANZA[t]["horario"][0],
          "confianza_cantidad": S.CONFIANZA[t]["cantidad"][0],
          "motivo_horario": S.CONFIANZA[t]["horario"][1],
          "motivo_cantidad": S.CONFIANZA[t]["cantidad"][1]} for t in TIPOS]).set_index("tipo")

    return {
        "punto": {"lat": lat, "lon": lon},
        "radio_m": radio,
        "horas": horas,
        "franjas": franjas,
        "confianza": confianza,
        "elementos": {
            "centros educativos": n_edu,
            "campus universitarios": n_campus,
            "estudiantes matriculados ponderados por superficie y distancia":
                round(est_campus),
            "centros sanitarios con público": n_san,
            "sitios del registro de desfibriladores": sum(n_dea.values()),
            **{f"  de ellos {S.TIPOS_CLIENTE[t].lower()}": v for t, v in n_dea.items() if v},
            "paradas de transporte (por red)": n_par,
            **({"  de ellas con trenes estimados (línea 3 de Metro, sin viajes en los "
                "horarios publicados)": n_par_est} if n_par_est else {}),
            "población estimada dentro del radio (ponderada por distancia)": round(pob),
        },
        "es_estimacion": True,
    }


def horas_punta(r: dict, dia: str, n: int = 3) -> pd.DataFrame:
    """Las n horas con más movimiento de un tipo de día y qué tipo de cliente pesa más."""
    h = r["horas"].loc[dia]
    top = h[h["total"] > 0].nlargest(n, "total")
    out = []
    for hora, f in top.iterrows():
        partes = f[TIPOS].sort_values(ascending=False)
        out.append({
            "hora": f"{hora:02d}:00-{hora:02d}:59",
            "total": int(f["total"]),
            "principal": S.TIPOS_CLIENTE[partes.index[0]],
            "reparto": ", ".join(f"{S.TIPOS_CLIENTE[t]} {100 * v / f['total']:.0f} %"
                                 for t, v in partes.items() if v / f["total"] >= 0.05),
        })
    return pd.DataFrame(out)


def _nombres(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={**S.TIPOS_CLIENTE, "total": "Total"})


def main(argv: list[str]) -> int:
    lat, lon = float(argv[0]), float(argv[1])
    radio = float(argv[2]) if len(argv) > 2 else S.RADIO_M
    r = perfil_horario(lat, lon, radio)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)
    print(f"Punto {lat}, {lon} · radio {radio:.0f} m · ESTIMACIÓN (personas que pasan "
          "cerca por hora)\n")
    for k, v in r["elementos"].items():
        print(f"  {k}: {v}")
    for d in DIAS:
        print(f"\n=== {NOMBRE_DIA[d]}: por horas")
        print(_nombres(r["horas"].loc[d]).to_string())
        print(f"\n=== {NOMBRE_DIA[d]}: por franjas")
        print(_nombres(r["franjas"].loc[d]).to_string())
        print(f"\n=== {NOMBRE_DIA[d]}: horas con más movimiento")
        print(horas_punta(r, d).to_string(index=False))
    print("\n=== Confianza")
    print(r["confianza"][["nombre", "confianza_horario", "confianza_cantidad"]].to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
