"""BARómetro: las respuestas dichas con palabras de la calle.

Traduce a frases cortas lo que devuelven recomendar(), informe_local() y
nivel_movimiento(). No calcula nada: solo elige palabras y redondea para enseñar. Lo usan
la aplicación web (app/app.py), la comparación de dos locales (src/comparar.py), el
documento descargable (src/documento.py) y el servidor MCP, para decir lo mismo con las
mismas palabras en todas partes.
"""

from __future__ import annotations

import re

import pandas as pd

import supuestos as S

# Tipos de local: cuatro colores bien separados también con daltonismo; los mismos en el
# mapa, las leyendas, el informe y el documento descargable.
COLOR_TIPO = {"bar": "#0072B2", "restaurante": "#D55E00", "cafeteria": "#009E73",
              "comida_rapida": "#B5338A"}


def miles(n: float) -> str:
    """Entero con punto de miles: 12345 → «12.345»."""
    return f"{round(n):,}".replace(",", ".")


def dec(x: float, d: int = 1) -> str:
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def redondo(n: float) -> str:
    """Redondeo para cifras estimadas: dos cifras significativas («≈5.000»)."""
    if n >= 100:
        n = round(n, -len(str(int(n))) + 2)
    return miles(n)


def lista_y(xs: list[str]) -> str:
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1]


def bloque_inf(inf: dict, clave: str) -> dict:
    return next(b for b in inf["bloques"] if b["clave"] == clave)


def horas_punta(rec: dict, dia: str) -> list[int]:
    return [int(h["hora"][:2]) for h in rec["a_que_hora"]["detalle"][dia]["horas_punta"]]


def grupos_horas(rec: dict, dia: str) -> list[list[int]]:
    """Horas punta agrupadas en tramos seguidos, ordenados por la hora más concurrida."""
    punta = rec["a_que_hora"]["detalle"][dia]["horas_punta"]
    total = {int(h["hora"][:2]): h["total"] for h in punta}
    grupos: list[list[int]] = []
    for h in sorted(total):
        if grupos and h == grupos[-1][-1] + 1:
            grupos[-1].append(h)
        else:
            grupos.append([h])
    return sorted(grupos, key=lambda g: -max(total[h] for h in g))


def tramo(g: list[int]) -> str:
    return f"{g[0]} h" if len(g) == 1 else f"{g[0]}–{g[-1] + 1} h"


def hora_de_grupo(rec: dict, dia: str, g: list[int]) -> int:
    total = {int(h["hora"][:2]): h["total"]
             for h in rec["a_que_hora"]["detalle"][dia]["horas_punta"]}
    return max(g, key=lambda h: total[h])


def rec_dia(recs: list[dict], dia: str) -> list[dict]:
    return [r for r in recs if r.get("dia") == dia]


def clientes_principales(rec: dict, dia: str = "laborable") -> list[tuple[str, float]]:
    """Tipos de cliente que destaca la recomendación «a quién» (como mucho dos)."""
    r = rec_dia(rec["a_quien"]["recomendaciones"], dia)
    pesos = sorted((r[0].get("pesos") or {}).items(), key=lambda kv: -kv[1]) if r else []
    fuertes = [kv for kv in pesos if kv[1] >= 0.25][:2]
    return fuertes or pesos[:1]


# Esta vista no calcula nada: traduce a frases cortas lo que devuelven recomendar() e
# informe_local(). Las cifras se redondean solo para mostrarlas.
CLIENTE_CALLE = {"vecinos": "vecinos", "viajeros": "viajeros",
                 "universitarios": "universitarios", "padres_ninos": "familias con niños",
                 "pacientes": "pacientes", "trabajadores": "trabajadores",
                 "deporte_eventos": "gente del deporte"}


ARTICULO = {"padres_ninos": "las", "deporte_eventos": "la"}   # el resto, «los»


MOMENTO_CALLE = {"desayuno": "desayunos", "almuerzo": "almuerzos a media mañana",
                 "menu_del_dia": "menú del día", "merienda": "meriendas",
                 "canas_raciones": "cañas con raciones", "cenas": "cenas", "copas": "copas"}


FRANJA_CALLE = {"primera hora de la mañana": "a primera hora",
                "media mañana": "a media mañana", "mediodía": "a mediodía",
                "media tarde": "a media tarde", "tarde-noche": "al caer la tarde",
                "noche": "de noche"}


PRECIO_CALLE = {"económica": "económicos", "media": "medios", "alta": "altos"}


FIABILIDAD = {"alta": (3, "Bastante fiable"), "media": (2, "Orientativo"),
              "baja": (1, "Poco fiable, compruébalo")}


LOCAL_CALLE = {"sirven_comidas": "sitios para comer", "bar": "bares",
               "cafeteria": "cafeterías", "comida_rapida": "locales de comida rápida"}


def unas(n: float) -> str:
    """Número redondo para leer de un vistazo: 2.084 → «2.000», 580 → «600»."""
    paso = 500 if n >= 1000 else 50 if n >= 100 else 10 if n >= 20 else 1
    return miles(max(paso, round(n / paso) * paso))


def horas_calle(grupos: list[list[int]]) -> str:
    """Tramos de horas punta en palabras: «de 8 a 10 y a las 14»."""
    def uno(g):
        if len(g) > 1:
            return f"de {g[0]} a {g[-1] + 1}"
        return "a la 1" if g[0] == 1 else f"a las {g[0]}"
    return lista_y([uno(g) for g in sorted(grupos)])


def mayus(t: str) -> str:
    return t[0].upper() + t[1:] if t else t


def oportunidad_comidas(rec: dict) -> list[str]:
    """Momentos (menú del día, cenas) que recomendar() señala como oportunidad."""
    textos = [r["texto"] for r in rec["que_vender"]["recomendaciones"] if "dia" not in r]
    return [m for m in ("menu_del_dia", "cenas")
            if any(S.MOMENTOS[m].lower() in t for t in textos)]


def ofertas(rec: dict) -> list[str]:
    """Los dos momentos que se enseñan: el primero del día de diario y la oportunidad de
    comidas si la hay; si no, el segundo del día de diario."""
    lab = [r["momento"] for r in rec_dia(rec["que_vender"]["recomendaciones"], "laborable")]
    out = lab[:1]
    for m in oportunidad_comidas(rec) + lab[1:]:
        if m not in out:
            out.append(m)
    return out[:2]


def competencia_alta(rec: dict) -> bool:
    return any(r["clave"] == "competencia_alta" for r in rec["riesgos"])


def titular_calle(rec: dict, mov: dict) -> str:
    """Una sola idea, doce palabras como mucho."""
    if mov["muy_poco_paso"]:
        return "Muy poco paso: por aquí casi no pasa gente andando"
    of = lista_y([MOMENTO_CALLE[m] for m in ofertas(rec)])
    if not of:
        return "Por aquí pasa poca gente"
    if oportunidad_comidas(rec):
        return f"Buena zona para {of}"
    if competencia_alta(rec):
        return f"Zona de {MOMENTO_CALLE[ofertas(rec)[0]]}, con mucha competencia cerca"
    return f"Aquí encajan sobre todo {of}"


def respuestas(rec: dict, inf: dict) -> dict:
    """Pregunta, respuesta corta, línea de apoyo y recomendación de la que sale la
    fiabilidad, para cada una de las cuatro tarjetas."""
    aq = rec["a_quien"]["recomendaciones"]
    hr = rec["a_que_hora"]["recomendaciones"]
    qv = rec["que_vender"]
    pr = rec["a_que_precio"]["recomendaciones"]
    lab = clientes_principales(rec)
    sab = clientes_principales(rec, "fin_de_semana")
    g_sab = grupos_horas(rec, "fin_de_semana")
    v_lab = rec_dia(qv["recomendaciones"], "laborable")
    v_sab = rec_dia(qv["recomendaciones"], "fin_de_semana")
    gama = bloque_inf(inf, "precios")["datos"]["gama_ajustada"]["gama"]["semana"]
    return {
        "quien": {
            "pregunta": "¿Quién pasa por aquí?",
            "respuesta": mayus(lista_y([CLIENTE_CALLE[t] for t, _ in lab])) or "Poca gente",
            "apoyo": f"Los sábados, sobre todo {CLIENTE_CALLE[sab[0][0]]}" if sab else "",
            "rec": (rec_dia(aq, "laborable") or aq)[0]},
        "cuando": {
            "pregunta": "¿Cuándo hay más gente?",
            "respuesta": mayus(horas_calle(grupos_horas(rec, "laborable"))) or "Sin datos",
            "apoyo": f"Los sábados, {horas_calle(g_sab)}" if g_sab else "",
            "rec": (rec_dia(hr, "laborable") or hr)[0]},
        "que": {
            "pregunta": "¿Qué conviene ofrecer?",
            "respuesta": mayus(lista_y([MOMENTO_CALLE[m] for m in ofertas(rec)]))
            or "Sin datos",
            "apoyo": f"Los sábados, {MOMENTO_CALLE[v_sab[0]['momento']]}" if v_sab else "",
            "rec": v_lab[0] if v_lab else qv["cocinas"]},
        "precio": {
            "pregunta": "¿A qué precios?",
            "respuesta": mayus(PRECIO_CALLE.get(gama, gama)),
            "apoyo": "Mira antes los precios de la zona",
            "rec": pr[0]},
    }


def frases_quien(rec: dict) -> list[str]:
    lab = clientes_principales(rec)
    sab = clientes_principales(rec, "fin_de_semana")
    dom = clientes_principales(rec, "domingo")
    out = []
    if lab:
        out.append(f"En un día de diario pasan sobre todo "
                   f"{lista_y([CLIENTE_CALLE[t] for t, _ in lab])}.")
    r = rec_dia(rec["a_quien"]["recomendaciones"], "laborable")
    fuerte = {}
    for p in (r[0]["porque"] if r else []):
        m = re.match(r"([^:]+): .*franja fuerte es «([^»]+)»", p)
        if m:
            fuerte[m.group(1)] = m.group(2)
    cuando = [f"{ARTICULO.get(t, 'los')} {CLIENTE_CALLE[t]}, "
              f"{FRANJA_CALLE[fuerte[S.TIPOS_CLIENTE[t]]]}"
              for t, _ in lab if fuerte.get(S.TIPOS_CLIENTE[t]) in FRANJA_CALLE]
    if cuando:
        out.append(mayus("; ".join(cuando)) + ".")
    if sab:
        out.append(f"Los sábados pasan sobre todo "
                   f"{lista_y([CLIENTE_CALLE[t] for t, _ in sab])}.")
    if dom:
        out.append(f"Los domingos, sobre todo "
                   f"{lista_y([CLIENTE_CALLE[t] for t, _ in dom])}.")
    if any(t == "viajeros" for t, _ in lab + sab + dom):
        out.append("Los viajeros van al metro, al tren o al autobús: paran menos.")
    return out


def frases_cuando(rec: dict) -> list[str]:
    out = []
    g_lab = grupos_horas(rec, "laborable")
    g_sab = grupos_horas(rec, "fin_de_semana")
    if g_lab:
        out.append(f"En un día de diario hay más gente {horas_calle(g_lab)}.")
    if g_sab:
        out.append(f"Los sábados, {horas_calle(g_sab)}.")
    g_dom = grupos_horas(rec, "domingo")
    if g_dom:
        out.append(f"Los domingos, {horas_calle(g_dom)}.")
    hueco = [r for r in rec["a_que_hora"]["recomendaciones"]
             if r["texto"].startswith("Posible hueco horario") and r.get("dia") == "laborable"]
    if hueco:
        franja = hueco[0]["texto"].split(": ", 1)[1].split(" (")[0].split(",")[0]
        if franja in FRANJA_CALLE:
            out.append(f"{mayus(FRANJA_CALLE[franja])} hay gente y abren pocos locales. "
                       "Puede ser un hueco.")
    clase = rec["a_que_hora"]["detalle"]["laborable"]["clase"]
    flojas = [f for f, c in clase.items() if c != "abrir" and f in FRANJA_CALLE]
    if flojas:
        out.append(f"{mayus(FRANJA_CALLE[flojas[-1]])} pasa muy poca gente.")
    return out


def frases_que(rec: dict) -> list[str]:
    qv = rec["que_vender"]
    lab = [MOMENTO_CALLE[r["momento"]] for r in rec_dia(qv["recomendaciones"], "laborable")]
    sab = [MOMENTO_CALLE[r["momento"]] for r in rec_dia(qv["recomendaciones"], "fin_de_semana")]
    out = []
    if lab:
        out.append(f"En un día de diario encajan sobre todo {lista_y(lab[:3])}.")
    op = oportunidad_comidas(rec)
    if op:
        out.append(f"Hay pocos sitios para comer cerca y gente para "
                   f"{lista_y([MOMENTO_CALLE[m] for m in op])}. Puede ser una oportunidad.")
    if sab:
        out.append(f"Los sábados, sobre todo {lista_y(sab[:2])}.")
    dom = [MOMENTO_CALLE[r["momento"]] for r in rec_dia(qv["recomendaciones"], "domingo")]
    if dom:
        out.append(f"Los domingos, sobre todo {lista_y(dom[:2])}.")
    sobra = [LOCAL_CALLE[h["tipo"]] for h in qv["huecos"]
             if h.get("sentido") == "sobra" and h.get("tipo") in LOCAL_CALLE]
    if sobra:
        out.append(f"Ya hay muchos {lista_y(sobra[:2])} cerca: ahí cuesta más competir.")
    return out


def frases_precio(inf: dict) -> list[str]:
    d = bloque_inf(inf, "precios")["datos"]
    renta = {"económica": "ganan menos que la media de la región",
             "media": "ganan más o menos como la media de la región",
             "alta": "ganan más que la media de la región"}
    ajustada = d["gama_ajustada"]["gama"]["semana"]
    out = []
    if d["gama"] in renta:
        out.append(f"Los vecinos de la zona {renta[d['gama']]}.")
    if ajustada != d["gama"]:
        out.append("Pero mucha de la gente que pasa no vive aquí.")
    out.append(f"Por eso encajan precios {PRECIO_CALLE.get(ajustada, ajustada)}.")
    out.append("No tenemos las cartas de los bares de la zona: míralas tú.")
    return out


def comprobaciones_calle(rec: dict) -> list[str]:
    """La lista de recomendar(), en el mismo orden, dicha con palabras sencillas."""
    g = grupos_horas(rec, "laborable")
    hora = f"a las {hora_de_grupo(rec, 'laborable', g[0])}" if g else "en la mejor hora"
    calle = {
        "Contar durante": f"Cuenta la gente que pasa por delante {hora}, durante 15 minutos.",
        "Anotar en": "Apunta el precio del café, la caña y el menú en tres bares cercanos.",
        "Comprobar a qué hora": "Mira a qué hora abren y cierran los bares de la zona.",
        "Ver por qué acera": "Fíjate por dónde sale la gente del metro o del autobús.",
        "Consultar el calendario": "Pregunta cuándo hay clase en el campus y si tiene "
                                   "cafetería dentro.",
        "Observar la salida": "Mira si las familias se quedan a merendar al salir del "
                              "colegio.",
        "Recorrer el radio": "Date una vuelta y cuenta los bares que hay de verdad.",
        "Preguntar a un hostelero": "Pregunta a otro hostelero qué meses flojea la zona.",
        "Confirmar los posibles huecos": "Pregunta si cerraron locales como el tuyo, y por "
                                         "qué.",
    }
    return [next((frase for clave, frase in calle.items() if c.startswith(clave)), c)
            for c in rec["comprobar_en_persona"]]


MODO_CALLE = {"Metro": "metro", "Cercanías": "tren de Cercanías",
              "Metro Ligero": "metro ligero", "Autobús urbano": "autobús urbano",
              "Autobús interurbano": "autobús interurbano"}


ENTORNO_CALLE = {
    "aislado": "Es un sitio aislado: casi no vive nadie cerca.",
    "borde": "Está en el borde de un barrio: justo al lado vive poca gente, pero un poco "
             "más lejos sí.",
    "dentro": "Está dentro de una zona con vecinos."}


def metrica_bloque(b: dict) -> tuple[str, str, str]:
    """Cifra clave y una frase de cada bloque del informe (solo formato)."""
    d = b["datos"]
    k = b["clave"]
    if k == "competencia":
        rel = d.get("relacion_con_media")
        frase = (f"≈×{dec(rel)} la media del municipio · " if rel is not None else "") \
            + f"{d['sirven_comidas']} sirven comidas · fuente: {d['fuente_usada']}"
        return f"Locales de hostelería en {S.RADIO_M} m", miles(d["total"]), frase
    if k == "mercado":
        a, z = d["rango_eur_anual"]

        def eur(x):
            return f"{dec(x / 1e6)} M€" if x >= 1e6 else f"{miles(round(x, -3) / 1e3)} mil €"
        val = (f"≈{dec(a / 1e6)}–{dec(z / 1e6)} M€" if a >= 1e6
               else f"≈{eur(a)} – {eur(z)}")
        return ("Gasto anual de los vecinos en restauración", val,
                f"≈{redondo(d['poblacion_radio'])} vecinos en {S.RADIO_M} m · renta "
                f"×{dec(d['renta_relativa'], 2)} la media de la Comunidad")
    if k == "precios":
        ipc = d["ipc_interanual"]
        return ("Gama de precios (ajustada a la clientela)",
                d["gama_ajustada"]["gama"]["semana"].capitalize(),
                f"IPC en 12 meses: restaurantes y alojamiento {ipc['restaurantes_alojamiento']:+.1f} %"
                f", alimentos {ipc['alimentos']:+.1f} % ({d['ipc_mes']})".replace(".", ","))
    if k == "turismo":
        return ("Alojamientos turísticos del código postal", miles(d["total_cp"]),
                f"CP ≈{d['codigo_postal_aproximado']} · municipio: "
                f"{miles(d['total_municipio'])} inscritos y "
                f"{miles(d['vut_declaraciones_municipio'])} viviendas turísticas declaradas")
    if k == "festivos":
        prox = d["proximos"]
        if not prox:
            return "Próximo festivo", "—", "Sin festivos publicados en los próximos meses"
        f0 = pd.Timestamp(prox[0]["fecha"])
        meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct",
                 "nov", "dic"]
        return ("Próximo festivo", f"{f0.day} {meses[f0.month - 1]}",
                f"{prox[0]['dia'].capitalize()} · {len(prox)} festivos publicados por delante")
    if k == "sector":
        return ("Empresas de distribución y hostelería, último año",
                f"{d['variacion_anual_pct']:+.1f} %".replace(".", ","),
                "Toda la Comunidad · la rama incluye comercio y transporte")
    if k == "accesos":
        modos = lista_y(list(d["cerca"])) if d["cerca"] else "ninguna parada"
        return ("Transporte público", d["nivel"],
                f"A menos de {d['radio_cerca_m']} m: {modos} · "
                f"{sum(v['lineas'] for v in d['lejos'].values())} líneas a menos de "
                f"{d['radio_lejos_m']} m")
    if k == "entorno":
        return (f"Vecinos a {d['radio_m'] // 1000} km (unos {d['minutos_andando']} min "
                "andando)", f"≈{redondo(d['vecinos'])}",
                f"{miles(d['locales'])} locales de hostelería a esa distancia · a "
                f"{S.RADIO_M} m: ≈{redondo(d['vecinos_radio_analisis'])} vecinos y "
                f"{d['locales_radio_analisis']} locales · solo contexto")
    return b["titulo"], "—", ""
