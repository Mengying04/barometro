"""Recomendaciones (parte B): a quién vender, a qué hora, qué vender y a qué precio.

    from recomendaciones import recomendar
    rec = recomendar(40.4046, -3.6106)

Desde la terminal:
    python src/recomendaciones.py 40.4046 -3.6106          # Markdown
    python src/recomendaciones.py 40.4046 -3.6106 --json   # JSON

Combina el perfil por horas (src/perfil_horario.py) y el informe del local
(src/informe_local.py). Cada recomendación lleva:
  - porque:    los datos concretos que la apoyan;
  - confianza: alta, media o baja, derivada de la de sus datos;
  - base:      «dato» o «estimación».
Son ORIENTACIONES, no garantías. Los valores y supuestos nuevos están en
src/supuestos.py, sección «RECOMENDACIONES». No se nombra ningún local.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date

import numpy as np
import pandas as pd
import shapely

import supuestos as S
from fecha import hoy
from informe_local import (_A_UTM, a_markdown as _md_informe, dec, en_radio, informe_local,
                           locales)
from perfil_horario import DIAS, TIPOS, horas_punta, perfil_horario

NIVELES = ["baja", "media", "alta"]
NOMBRE_DIA = {"laborable": "laborable", "fin_de_semana": "sábado", "domingo": "domingo"}
FRANJAS = list(S.FRANJAS)


# ------------------------------------------------------------------------- utilidades
def pct(x: float) -> str:
    return f"{100 * x:.0f} %"


def miles(x: float) -> str:
    return f"{x:,.0f}".replace(",", ".")


def conf_min(*niveles: str) -> str:
    """La confianza de una recomendación es la del dato más débil en que se apoya."""
    v = [n for n in niveles if n]
    return min(v, key=NIVELES.index) if v else "baja"


def conf_tipo(t: str, aspecto: str) -> str:
    return S.CONFIANZA_A_RECOMENDACION[S.CONFIANZA[t][aspecto][0]]


def rec(texto: str, porque: list[str], confianza: str, base: str, **extra) -> dict:
    return {"texto": texto, "porque": porque, "confianza": confianza, "base": base, **extra}


def nombre(t: str) -> str:
    return S.TIPOS_CLIENTE[t]


def bloque(inf: dict, clave: str) -> dict:
    return next(b for b in inf["bloques"] if b["clave"] == clave)


def por_hora(franjas: pd.DataFrame, dia: str) -> pd.Series:
    """Gente media por hora en cada franja (las franjas tienen distinto número de horas)."""
    f = franjas.loc[dia]["total"]
    return pd.Series({k: f[k] / len(S.FRANJAS[k]) for k in FRANJAS})


# ----------------------------------------------------- horarios de OSM (opening_hours)
_DIAS_OSM = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


def _dias(spec: str) -> set[str] | None:
    out = set()
    for parte in spec.split(","):
        parte = parte.strip()
        if parte in ("PH", "SH"):
            continue
        m = re.fullmatch(r"(Mo|Tu|We|Th|Fr|Sa|Su)(?:-(Mo|Tu|We|Th|Fr|Sa|Su))?", parte)
        if not m:
            return None
        a = _DIAS_OSM.index(m.group(1))
        b = _DIAS_OSM.index(m.group(2)) if m.group(2) else a
        idx = range(a, b + 1) if a <= b else [*range(a, 7), *range(0, b + 1)]
        out |= {_DIAS_OSM[i] for i in idx}
    return out


def horas_abierto(texto, dia: str) -> set[int] | None:
    """Horas (0-23) en que abre un local el día `dia` («We», «Sa»…) según opening_hours.
    Interpreta los formatos habituales; devuelve None si no lo entiende."""
    if texto is None or (isinstance(texto, float) and np.isnan(texto)):
        return None
    t = str(texto).strip()
    if t == "24/7":
        return set(range(24))
    abierto: set[int] | None = None
    for regla in t.split(";"):
        regla = regla.strip()
        if not regla:
            continue
        m = re.fullmatch(r"((?:[A-Za-z]{2}(?:-[A-Za-z]{2})?)(?:\s*,\s*[A-Za-z]{2}"
                         r"(?:-[A-Za-z]{2})?)*)?\s*(.*)", regla)
        dias_txt, horas_txt = (m.group(1) or "").strip(), m.group(2).strip()
        dias = _dias(dias_txt) if dias_txt else set(_DIAS_OSM)
        if dias is None:
            return None
        if dia not in dias:
            continue
        if horas_txt in ("off", "closed"):
            abierto = set()
            continue
        hs = set()
        for tramo in horas_txt.split(","):
            mm = re.fullmatch(r"\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\+?\s*", tramo)
            if not mm:
                return None
            a = int(mm.group(1)) + int(mm.group(2)) / 60
            b = int(mm.group(3)) + int(mm.group(4)) / 60
            if b <= a:
                b += 24
            hs |= {int(h) % 24 for h in np.arange(np.floor(a), np.ceil(b)) if h + 1 > a}
        abierto = hs
    return abierto


def horarios_competencia(punto, radio: float, dia: str) -> dict:
    """Para cada franja, qué parte de los locales de OSM del radio con horario conocido
    abre en alguna hora de la franja."""
    osm = en_radio(locales()["osm"], punto, radio)
    hs = [horas_abierto(x, S.DIA_OSM[dia]) for x in osm["horario_osm"]]
    conocidos = [h for h in hs if h is not None]
    out = {"locales_osm": len(osm), "con_horario": len(conocidos), "por_franja": {}}
    if len(conocidos) >= S.HORARIOS_MINIMO_LOCALES:
        for f, horas in S.FRANJAS.items():
            out["por_franja"][f] = sum(1 for h in conocidos if h & set(horas)) / len(conocidos)
    return out


# ============================================================================ A QUIÉN
def a_quien(perfil: dict) -> dict:
    fr = perfil["franjas"]
    tabla, recs = {}, []
    for d in DIAS:
        tabla[d] = {}
        for f in FRANJAS:
            fila = fr.loc[(d, f)]
            tot = fila["total"]
            pesos = (fila[TIPOS] / tot).sort_values(ascending=False) if tot > 0 else None
            tabla[d][f] = {"personas": int(tot), "clientes": [] if pesos is None else [
                {"tipo": t, "nombre": nombre(t), "peso": round(float(p), 3)}
                for t, p in pesos.items() if p >= S.PESO_MINIMO_CLIENTE]}
        dia_tot = fr.loc[d][TIPOS].sum()
        if dia_tot.sum() == 0:
            continue
        paso = dia_tot / dia_tot.sum()
        clientes = dia_tot * pd.Series(S.PROPENSION_CONSUMO)[TIPOS]
        pesos = (clientes / clientes.sum()).sort_values(ascending=False)
        principales = [t for t, p in pesos.items() if p >= S.PESO_MINIMO_CLIENTE][:3]
        mejor_franja = {t: fr.loc[d][t].idxmax() for t in principales}
        recs.append(rec(
            f"En {NOMBRE_DIA[d]}, orientar la oferta sobre todo a "
            + ", ".join(f"{nombre(t).lower()} ({pct(pesos[t])})" for t in principales)
            + ".",
            [f"{nombre(t)}: {pct(paso[t])} de la gente que pasa cerca en el día "
             f"(~{miles(dia_tot[t])} pasos) y {pct(pesos[t])} de los clientes posibles "
             f"(propensión a pararse {dec(S.PROPENSION_CONSUMO[t])}); su franja fuerte "
             f"es «{mejor_franja[t]}»." for t in principales],
            conf_min(*(conf_tipo(t, "cantidad") for t in principales
                       if pesos[t] >= S.PESO_CONFIANZA_FRANJA)), "estimación",
            dia=d, pesos={t: round(float(pesos[t]), 3) for t in principales}))
    return {"recomendaciones": recs, "por_franja": tabla,
            "nota": "Tres tipos de día: laborable (martes a jueves típico), sábado y "
                    "domingo, cada uno con el horario real de transporte de ese día y sus "
                    "supuestos. El domingo sirve también, de forma aproximada, para los "
                    "festivos."}


# ========================================================================= A QUÉ HORA
def a_que_hora(perfil: dict, punto, radio: float) -> dict:
    fr = perfil["franjas"]
    recs, detalle = [], {}
    for d in DIAS:
        ph = por_hora(fr, d)
        if ph.max() <= 0:
            continue
        rel = ph / ph.max()
        clase = {f: ("abrir" if r >= S.APERTURA_ABRIR else
                     "valorar" if r >= S.APERTURA_VALORAR else "no compensa")
                 for f, r in rel.items()}
        comp = horarios_competencia(punto, radio, d)
        punta = horas_punta(perfil, d, 3)
        abrir = [f for f in FRANJAS if clase[f] == "abrir"]
        valorar = [f for f in FRANJAS if clase[f] == "valorar"]
        tipos_abrir = {t for f in abrir for t in TIPOS
                       if fr.loc[(d, f)]["total"] > 0
                       and fr.loc[(d, f)][t] / fr.loc[(d, f)]["total"]
                       >= S.PESO_CONFIANZA_FRANJA}
        conf = conf_min(*(conf_tipo(t, "horario") for t in tipos_abrir))
        porque = [f"«{f}»: ~{miles(ph[f])} personas por hora ({pct(rel[f])} de la mejor "
                  "franja)" for f in FRANJAS]
        porque.append("Horas punta: " + "; ".join(
            f"{r.hora} (~{miles(r.total)}; {r.reparto})" for r in punta.itertuples()))
        recs.append(rec(
            f"En {NOMBRE_DIA[d]}, conviene abrir en: " + ", ".join(abrir)
            + (f"; valorar: {', '.join(valorar)}" if valorar else "")
            + f". Horas punta: {', '.join(punta['hora'])}.",
            porque, conf, "estimación", dia=d, clase=clase))
        if comp["por_franja"]:
            huecos = [f for f in abrir if comp["por_franja"][f] < S.HUECO_HORARIO]
            porque_c = [f"«{f}»: abre el {pct(v)} de los {comp['con_horario']} locales "
                        "con horario en OpenStreetMap" for f, v in comp["por_franja"].items()]
            texto = (f"Posible hueco horario en {NOMBRE_DIA[d]}: " + ", ".join(huecos)
                     + " (hay movimiento y abren pocos locales)." if huecos else
                     f"En {NOMBRE_DIA[d]} la competencia con horario conocido cubre las "
                     "franjas con movimiento: no se ve un hueco horario claro.")
            recs.append(rec(texto, porque_c + [
                f"Solo {comp['con_horario']} de {comp['locales_osm']} locales de OSM del "
                "radio tienen horario: muestra pequeña."], "baja", "dato + estimación",
                dia=d))
        else:
            recs.append(rec(
                f"No hay datos suficientes para comparar con el horario de la competencia "
                f"en {NOMBRE_DIA[d]}.",
                [f"Solo {comp['con_horario']} de {comp['locales_osm']} locales de "
                 "OpenStreetMap del radio indican su horario (mínimo "
                 f"{S.HORARIOS_MINIMO_LOCALES}); el censo de Madrid no tiene horarios."],
                "baja", "dato", dia=d))
        detalle[d] = {"personas_por_hora": ph.round().to_dict(), "clase": clase,
                      "competencia": comp, "horas_punta": punta.to_dict("records")}
    return {"recomendaciones": recs, "detalle": detalle}


# ======================================================================== QUÉ VENDER
def momentos(perfil: dict) -> dict:
    """Gente de cada momento de consumo por día, según TABLA_MOMENTOS."""
    fr = perfil["franjas"]
    out = {}
    for d in DIAS:
        tot = {m: 0.0 for m in S.MOMENTOS}
        aporte = {m: [] for m in S.MOMENTOS}
        for (t, f), ms in S.TABLA_MOMENTOS.items():
            n = float(fr.loc[(d, f)][t]) * S.PROPENSION_CONSUMO[t] / len(ms)
            if n <= 0:
                continue
            for m in ms:
                if d != "laborable":   # sábado y domingo
                    m = S.MOMENTO_SOLO_LABORABLE.get(m, m)
                tot[m] += n
                aporte[m].append((t, f, n))
        out[d] = {"total": tot, "aporte": aporte}
    return out


def huecos_competencia(inf: dict) -> list[dict]:
    comp = bloque(inf, "competencia")["datos"]
    cob = comp.get("cobertura_osm")
    osm_bajo = bool(cob) and cob["relacion"] < S.COBERTURA_OSM_AVISO
    es_censo = comp["fuente_usada"].startswith("Censo")
    nombres = {"sirven_comidas": "locales que sirven comidas", "bar": "bares",
               "cafeteria": "cafeterías", "comida_rapida": "locales de comida rápida"}
    conf = "baja" if osm_bajo else "media"
    contexto = (f"En conjunto el radio tiene {comp['total']} locales, ×"
                f"{dec(comp['relacion_con_media'], 2)} la media del municipio: parte de la "
                "diferencia se explica por eso.") if comp["relacion_con_media"] else None
    out, comparados = [], 0
    for k, n in nombres.items():   # nunca «restaurantes» a secas (ver supuestos)
        v = comp["comparacion_por_tipo"][k]
        if v["media_municipio"] < S.HUECO_MEDIA_MINIMA or v["relacion"] is None:
            continue
        comparados += 1
        porque = [f"{v['radio']} {n} en {S.RADIO_M} m frente a {dec(v['media_municipio'])} "
                  f"de media en un punto habitado del municipio (×{dec(v['relacion'], 2)}); "
                  f"fuente: {comp['fuente_usada']}."]
        if contexto:
            porque.append(contexto)
        if osm_bajo:
            porque.append("OpenStreetMap tiene pocos locales en este municipio (cobertura "
                          f"×{dec(cob['relacion'], 2)} frente al censo de Madrid): la "
                          "comparación es orientativa.")
        if v["relacion"] < S.HUECO_FALTA:
            out.append(rec(f"Posible hueco: hay menos {n} que en un punto típico del "
                           "municipio.", porque, conf, "dato + estimación", tipo=k,
                           sentido="falta"))
        elif v["relacion"] > S.HUECO_SATURACION:
            out.append(rec(f"Oferta abundante de {n}: competir en ese formato puede ser "
                           "más difícil.", porque, conf, "dato + estimación", tipo=k,
                           sentido="sobra"))
    if not comparados:
        out.append(rec("No se pueden buscar huecos de competencia: en un punto típico del "
                       "municipio hay menos de un local de cada tipo en "
                       f"{S.RADIO_M} m según {comp['fuente_usada']}.",
                       [f"{comp['total']} locales en el radio frente a "
                        f"{dec(comp['media_municipio'])} de media."]
                       + (["Con la cobertura baja de OpenStreetMap en el municipio, faltan "
                           "datos para comparar: hay que contar los locales en persona."]
                          if osm_bajo else []), "baja", "dato + estimación"))
    elif not out:
        out.append(rec("Sin huecos ni saturaciones claras frente a la media del municipio.",
                       ["Ningún tipo de local se aleja lo bastante de la media."], conf,
                       "dato + estimación"))
    return out


def que_vender(perfil: dict, inf: dict) -> dict:
    mo = momentos(perfil)
    recs = []
    for d in DIAS:
        tot = pd.Series(mo[d]["total"])
        if tot.max() <= 0:
            continue
        orden = tot.sort_values(ascending=False)
        for m, n in orden.items():
            if n < S.MOMENTO_RECOMENDAR * orden.iloc[0] or n <= 0:
                break
            agrupado: dict = {}
            for t, f, x in mo[d]["aporte"][m]:
                agrupado[(t, f)] = agrupado.get((t, f), 0.0) + x
            ap = sorted(((t, f, x) for (t, f), x in agrupado.items()), key=lambda y: -y[2])
            principales = [y for y in ap[:3] if y[2] >= S.APORTE_MINIMO]
            por_tipo = pd.Series([x for _, _, x in ap], index=[t for t, _, _ in ap]) \
                .groupby(level=0).sum() / n
            fuertes = [t for t, p in por_tipo.items() if p >= S.PESO_CONFIANZA_FRANJA]
            conf = conf_min("media", *(conf_tipo(t, "cantidad") for t in fuertes))
            recs.append(rec(
                f"{NOMBRE_DIA[d].capitalize()}: {S.MOMENTOS[m].lower()} "
                f"(~{miles(n)} clientes posibles; {pct(n / tot.sum())} del total de "
                "momentos del día).",
                [f"{nombre(t)} en «{f}»: ~{miles(x)} clientes posibles"
                 for t, f, x in principales]
                + ["Clientes posibles = gente que pasa × propensión a pararse (viajeros "
                   "0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla "
                   "TABLA_MOMENTOS de src/supuestos.py (supuesto)."],
                conf, "estimación", dia=d, momento=m))
    huecos = huecos_competencia(inf)
    # Cruce: hueco de comidas y momento de comida o cena recomendado
    falta_comidas = any(h.get("tipo") == "sirven_comidas" and h.get("sentido") == "falta"
                        for h in huecos)
    momentos_comida = {r["momento"] for r in recs} & {"menu_del_dia", "cenas"}
    if falta_comidas and momentos_comida:
        recs.append(rec(
            "La oferta de comidas del radio está por debajo de lo habitual y hay público "
            "para " + " y ".join(S.MOMENTOS[m].lower() for m in sorted(momentos_comida))
            + ": es la combinación que más apunta a una oportunidad (a comprobar).",
            [h["porque"][0] for h in huecos if h.get("tipo") == "sirven_comidas"]
            + ["Ver los momentos recomendados arriba."],
            conf_min("media", *(h["confianza"] for h in huecos
                                if h.get("tipo") == "sirven_comidas")),
            "dato + estimación"))

    comp = bloque(inf, "competencia")["datos"]
    n_osm, con = comp["locales_osm"], comp["locales_osm_con_cocina"]
    if n_osm >= S.COCINAS_MINIMO_LOCALES and con / n_osm > S.COCINAS_MINIMA_FRACCION:
        cocinas = {"texto": "Cocinas presentes en el radio (OpenStreetMap): "
                   + ", ".join(f"{k} ({v})" for k, v in comp["cocinas_osm"].items()) + ".",
                   "porque": [f"{con} de {n_osm} locales de OSM indican su cocina."],
                   "confianza": "media", "base": "dato"}
    else:
        cocinas = {"texto": "No hay datos suficientes sobre tipos de cocina en el radio.",
                   "porque": [f"Solo {con} de {n_osm} locales de OpenStreetMap indican su "
                              f"cocina (hacen falta al menos {S.COCINAS_MINIMO_LOCALES} "
                              f"locales y más del {pct(S.COCINAS_MINIMA_FRACCION)})."],
                   "confianza": "baja", "base": "dato"}
    return {"recomendaciones": recs, "huecos": huecos, "cocinas": cocinas,
            "momentos": {d: {m: round(v) for m, v in mo[d]["total"].items()} for d in DIAS}}


# ======================================================================= A QUÉ PRECIO
def a_que_precio(perfil: dict, inf: dict) -> dict:
    p = bloque(inf, "precios")["datos"]
    aj = p["gama_ajustada"]
    rep = aj["reparto_semana"]
    peso_vecinos = rep.get("vecinos", 0.0)
    conf = "media" if peso_vecinos >= 0.5 else "baja"
    t = p["ipc_interanual"]
    fmt = lambda x: f"{x:+.1f} %".replace(".", ",")
    recs = [
        rec(f"Gama orientativa: {aj['gama']['semana']} (ajustada a la clientela); por la "
            f"renta de los vecinos sería {p['gama']}.",
            [f"Renta de los vecinos: ×{dec(p['renta_relativa'], 2)} la media de la Comunidad "
             f"→ gama {p['gama']}.",
             "Peso de cada cliente en la semana (gente × propensión a pararse): " + ", ".join(
                 f"{nombre(k).lower()} {pct(v)}" for k, v in
                 sorted(rep.items(), key=lambda x: -x[1]) if v >= 0.05) + ".",
             f"Laborable: {aj['gama']['laborable']} ({dec(aj['valor']['laborable'], 2)}); "
             f"sábado: {aj['gama']['fin_de_semana']} "
             f"({dec(aj['valor']['fin_de_semana'], 2)}); domingo: {aj['gama']['domingo']} "
             f"({dec(aj['valor']['domingo'], 2)}); escala de 1 (económica) a 3 (alta).",
             "Las gamas de universitarios, viajeros, trabajadores y deporte son supuestos "
             "(src/supuestos.py, GAMA_CLIENTE)."], conf, "estimación"),
        rec(f"Precios del sector: en los últimos 12 meses (hasta {p['ipc_mes']}) "
            f"restaurantes y alojamiento {fmt(t['restaurantes_alojamiento'])} frente a "
            f"alimentos {fmt(t['alimentos'])}: el sector ha subido precios por encima de la "
            "materia prima. Puede servir de referencia al revisar la carta, no como regla.",
            [f"IPC de la Comunidad de Madrid (portal): restaurantes y servicios de "
             f"alojamiento {fmt(t['restaurantes_alojamiento'])}, alimentos y bebidas no "
             f"alcohólicas {fmt(t['alimentos'])}, bebidas alcohólicas "
             f"{fmt(t.get('bebidas_alcoholicas', float('nan')))}, índice general "
             f"{fmt(t['general'])}.",
             f"**Aviso:** el grupo incluye hoteles, que han subido {fmt(t['hoteles'])}; la "
             "subida propia de bares y restaurantes probablemente sea menor."],
            "media", "dato"),
        rec("No se dan precios en euros: no hay datos abiertos de cartas. Conviene comprobar "
            "en persona los precios de 3 a 5 locales del radio (café, caña, menú del día, "
            "ración) antes de fijar los propios.",
            ["Ninguna fuente abierta del proyecto publica precios de cartas."], "alta",
            "dato"),
    ]
    return {"recomendaciones": recs}


# ============================================================= RIESGOS Y COMPROBACIONES
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def de_cada(p: float) -> str:
    """Una proporción dicha como se dice en la calle: 0,26 → «1 de cada 4». Se elige la
    fracción sencilla más cercana (solo para decirlo; la cifra exacta va en el porqué)."""
    fracciones = [(a, b) for b in range(2, 6) for a in range(1, b)] \
        + [(1, b) for b in range(6, 11)] + [(9, 10)]
    a, b = min(fracciones, key=lambda f: (abs(p - f[0] / f[1]), f[1]))
    return f"{a} de cada {b}"


def veces(rel: float) -> str:
    """«×2,07» dicho con palabras: «el doble», «el triple» o «2,6 veces»."""
    return {2.0: "el doble de", 3.0: "el triple de"}.get(round(rel, 1), f"{dec(rel)} veces")


def _y(xs: list[str]) -> str:
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1]


def riesgos(perfil: dict, inf: dict) -> list[dict]:
    """Avisos del sitio: cada uno sale de los datos de ese punto y lo dice con su cifra, en
    lenguaje sencillo. Van ordenados por importancia (S.ORDEN_RIESGOS) y como mucho se dan
    S.MAX_RIESGOS; si no hay ninguno, se dice en positivo. Cada aviso lleva su «clave»."""
    out = []
    muni = inf["municipio"]["nombre"]
    comp = bloque(inf, "competencia")["datos"]
    rel = comp["relacion_con_media"]
    n = comp["total"]
    locales_txt = "1 bar o restaurante" if n == 1 else f"{n} bares y restaurantes"
    if comp["media_municipio"] < S.HUECO_MEDIA_MINIMA:
        out.append(rec(f"En {muni} hay tan pocos bares (menos de 1 de media en un círculo "
                       f"como este) que no podemos decir si {locales_txt} a menos de "
                       f"{S.RADIO_M} m {'es' if n == 1 else 'son'} mucha o poca competencia.",
                       [f"{n} locales en el radio frente a "
                        f"{dec(comp['media_municipio'])} de media ({comp['fuente_usada']}); "
                        "con tan pocos locales la comparación no dice nada."],
                       "baja", "dato + estimación", clave="competencia_sin_valorar"))
    elif rel is not None and rel > S.RIESGO_COMPETENCIA:
        out.append(rec(f"Ya hay {locales_txt} a menos de {S.RADIO_M} m: {veces(rel)} lo "
                       f"normal en {muni}.",
                       [f"{n} locales en el radio, ×{dec(rel, 2)} la media del municipio.",
                        f"Fuente: {comp['fuente_usada']}."],
                       "baja" if comp.get("cobertura_osm") else "media",
                       "dato + estimación", clave="competencia_alta"))
    cob = comp.get("cobertura_osm")
    if cob and cob["relacion"] < S.COBERTURA_OSM_AVISO:
        out.append(rec(f"Seguramente hay más de {locales_txt} cerca: el mapa colaborativo que "
                       f"usamos recoge en {muni} {dec(cob['osm_municipio'])} locales por cada "
                       f"1.000 vecinos, y el censo oficial de Madrid capital, "
                       f"{dec(cob['censo_madrid']).removesuffix(',0')}.",
                       [f"OSM registra {dec(cob['osm_municipio'], 2)} locales por 1.000 "
                        f"habitantes en el municipio, frente a {dec(cob['censo_madrid'], 2)} "
                        "del censo oficial de Madrid capital.",
                        "Por eso la competencia real probablemente es mayor que la contada."],
                       "media", "dato", clave="cobertura_baja"))
    # Festivos: solo los de los próximos S.RIESGO_FESTIVO_DIAS días, diciendo cuál y cuándo.
    hoy_ = hoy()
    cerca = [p for p in bloque(inf, "festivos")["datos"]["proximos"]
             if (date.fromisoformat(p["fecha"]) - hoy_).days <= S.RIESGO_FESTIVO_DIAS]
    if cerca:
        def cual(p: dict) -> str:
            f = date.fromisoformat(p["fecha"])
            que = (f"fiesta local en {p['ambito']}" if p["festivo"] == "local"
                   else p["ambito"])
            return f"el {p['dia']} {f.day} de {MESES[f.month - 1]} ({que})"
        uno = len(cerca) == 1
        out.append(rec(f"{'Viene un festivo' if uno else 'Vienen festivos'}: "
                       f"{_y([cual(p) for p in cerca])}. "
                       f"{'Ese día' if uno else 'Esos días'} pasa menos gente de diario "
                       "(trabajadores, estudiantes) y la zona se parece más a un domingo.",
                       [f"{p['fecha']} ({p['dia']}): "
                        + (f"fiesta local ({p['ambito']})" if p["festivo"] == "local"
                           else p["ambito"]) for p in cerca]
                       + [f"Solo se avisa de los festivos de los próximos "
                          f"{S.RIESGO_FESTIVO_DIAS} días; el resto está en el bloque "
                          "«Festivos» del informe."],
                       "alta", "dato", clave="festivos"))
    lab = perfil["horas"].loc["laborable"][TIPOS].sum()
    peso_est = {t: lab[t] / lab.sum() for t in ("universitarios", "padres_ninos")} \
        if lab.sum() > 0 else {}
    for t, p in sorted(peso_est.items(), key=lambda kv: -kv[1]):
        if p >= S.RIESGO_ESTUDIANTES:
            uni = t == "universitarios"
            out.append(rec(f"Aquí {de_cada(p)} personas que pasan en un día de diario son "
                           f"{'universitarios' if uni else 'familias del colegio'}: en "
                           f"vacaciones {'de la universidad' if uni else 'escolares'} "
                           "(Navidad, Semana Santa, julio y agosto) lo notarás.",
                           [f"{nombre(t)} son el {pct(p)} de la gente de un laborable "
                            "(estimación); sin clase ese público desaparece.",
                            f"Periodo lectivo típico ({'universidad' if uni else 'colegios'}): "
                            f"{S.PERIODO_LECTIVO[t]}.",
                            "El portal de la Comunidad no publica el calendario escolar: el "
                            "periodo lectivo es un supuesto (src/supuestos.py)."],
                           "media", "estimación",
                           clave="sin_clase_universidad" if uni else "sin_clase_colegios"))
    if not out:
        return [rec("No vemos nada especial que vigilar en esta zona.",
                    ["Ninguna de las reglas de aviso se cumple aquí: la competencia no es "
                     "alta, el peso de colegios y universidad es pequeño y no hay festivos "
                     f"en los próximos {S.RIESGO_FESTIVO_DIAS} días."], "media",
                    "estimación", clave="ninguno")]
    out.sort(key=lambda r: S.ORDEN_RIESGOS.index(r["clave"].replace("_universidad", "")
                                                 .replace("_colegios", "")))
    return out[:S.MAX_RIESGOS]


def comprobaciones(perfil: dict, inf: dict, hora: dict, vender: dict) -> list[str]:
    lab = perfil["horas"].loc["laborable"]
    punta = horas_punta(perfil, "laborable", 1)
    pesos = lab[TIPOS].sum() / max(lab[TIPOS].sum().sum(), 1)
    comp = bloque(inf, "competencia")["datos"]
    out = []
    if len(punta):
        h = punta.iloc[0]
        out.append(f"Contar durante 15 minutos la gente que pasa por delante del local en la "
                   f"hora punta de un laborable ({h['hora']}) y comparar con la estimación "
                   f"(~{miles(h['total'] / 4)} personas en 15 minutos); repetirlo en una "
                   "hora floja.")
    out.append("Anotar en 3 a 5 locales del radio el precio del café, la caña, el menú del "
               "día y una ración, y si tienen menú del día.")
    out.append("Comprobar a qué hora abren y cierran de verdad los bares y restaurantes del "
               "radio (los datos abiertos casi no traen horarios).")
    if pesos.get("viajeros", 0) >= S.PESO_MINIMO_CLIENTE:
        out.append("Ver por qué acera sale la gente del metro o de las paradas de autobús y "
                   "si pasa por delante del local o va hacia otro lado.")
    if pesos.get("universitarios", 0) >= S.PESO_MINIMO_CLIENTE:
        out.append("Consultar el calendario académico y los horarios de clase del campus, y "
                   "si dentro hay cafetería o comedor (competencia que no está en el censo).")
    if pesos.get("padres_ninos", 0) >= S.PESO_MINIMO_CLIENTE:
        out.append("Observar la salida de los colegios (14:00 y 16:00-17:00) y si las familias "
                   "se quedan a merendar por la zona.")
    if comp.get("cobertura_osm"):
        out.append("Recorrer el radio y contar los bares, cafeterías y restaurantes reales: "
                   f"OpenStreetMap solo tiene {comp['total']}.")
    out.append("Preguntar a un hostelero de la zona qué días y meses flojean (agosto, fiestas "
               "locales, puentes) y cuánto pesa la terraza en su negocio.")
    nombres = {"sirven_comidas": "locales que sirven comidas", "bar": "bares",
               "cafeteria": "cafeterías", "comida_rapida": "comida rápida"}
    huecos = [nombres[h["tipo"]] for h in vender["huecos"] if h.get("sentido") == "falta"]
    if huecos:
        out.append("Confirmar los posibles huecos (" + ", ".join(huecos) + ") recorriendo el "
                   "radio y preguntando si hubo locales de ese tipo que cerraron y por qué.")
    lo, hi = S.COMPROBACIONES
    return out[:hi] if len(out) >= lo else out


# ========================================================================== principal
def recomendar(lat: float, lon: float, radio: float = S.RADIO_M,
               perfil: dict | None = None, inf: dict | None = None) -> dict:
    """Recomendaciones para un bar o restaurante en el punto (ORIENTACIÓN).

    `perfil` e `inf` son los resultados de perfil_horario() e informe_local() para el
    mismo punto y radio; si se pasan (por ejemplo, desde la aplicación web), no se
    vuelven a calcular."""
    if perfil is None:
        perfil = perfil_horario(lat, lon, radio)
    if inf is None:
        inf = informe_local(lat, lon, radio, perfil=perfil)
    x, y = _A_UTM.transform(lon, lat)
    punto = shapely.Point(x, y)
    hora = a_que_hora(perfil, punto, radio)
    vender = que_vender(perfil, inf)
    return {
        "punto": {"lat": lat, "lon": lon}, "radio_m": radio, "municipio": inf["municipio"],
        "fecha": hoy().isoformat(),
        "aviso": "Orientaciones a partir de datos abiertos y supuestos explícitos, no "
                 "garantías. Toda cifra de personas es una estimación.",
        "a_quien": a_quien(perfil),
        "a_que_hora": hora,
        "que_vender": vender,
        "a_que_precio": a_que_precio(perfil, inf),
        "riesgos": riesgos(perfil, inf),
        "comprobar_en_persona": comprobaciones(perfil, inf, hora, vender),
    }


def _md_rec(r: dict) -> list[str]:
    out = [f"- **{r['texto']}** *(confianza {r['confianza']}; {r['base']})*"]
    out += [f"  - {p}" for p in r["porque"]]
    return out


def a_markdown(r: dict) -> str:
    m = r["municipio"]
    out = [f"## Recomendaciones · {r['punto']['lat']}, {r['punto']['lon']} · {m['nombre']} "
           f"· radio {r['radio_m']:.0f} m", "", f"> {r['aviso']}", ""]
    out += ["### A quién vender", ""]
    for x in r["a_quien"]["recomendaciones"]:
        out += _md_rec(x)
    out += ["", "Clientes principales por franja (peso ≥ "
            f"{pct(S.PESO_MINIMO_CLIENTE)}, estimación):", "",
            "| Franja | Laborable | Sábado | Domingo |", "|---|---|---|---|"]
    t = r["a_quien"]["por_franja"]
    celda = lambda c: ", ".join(f"{x['nombre']} {pct(x['peso'])}" for x in c["clientes"]) \
        + f" (~{miles(c['personas'])})" if c["clientes"] else "—"
    for f in FRANJAS:
        out.append(f"| {f} | {celda(t['laborable'][f])} | {celda(t['fin_de_semana'][f])} "
                   f"| {celda(t['domingo'][f])} |")
    out += ["", f"*{r['a_quien']['nota']}*", "", "### A qué hora", ""]
    for x in r["a_que_hora"]["recomendaciones"]:
        out += _md_rec(x)
    out += ["", "### Qué vender", "", "Momentos de consumo:", ""]
    for x in r["que_vender"]["recomendaciones"]:
        out += _md_rec(x)
    out += ["", "Huecos de competencia (con «locales que sirven comidas», no «restaurantes» "
            "a secas):", ""]
    for x in r["que_vender"]["huecos"] or [rec("Sin huecos ni saturaciones claras.", [],
                                               "media", "dato + estimación")]:
        out += _md_rec(x)
    out += ["", "Tipos de cocina:", ""] + _md_rec(r["que_vender"]["cocinas"])
    out += ["", "### A qué precio", ""]
    for x in r["a_que_precio"]["recomendaciones"]:
        out += _md_rec(x)
    out += ["", "### Riesgos y avisos", ""]
    for x in r["riesgos"]:
        out += _md_rec(x)
    out += ["", "### Qué comprobar en persona", ""]
    out += [f"{i}. {c}" for i, c in enumerate(r["comprobar_en_persona"], 1)]
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    lat, lon = float(argv[0]), float(argv[1])
    r = recomendar(lat, lon)
    if "--json" in argv:
        print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
    else:
        print(a_markdown(r))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
