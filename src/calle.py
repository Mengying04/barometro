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

# Dibujo de cada tipo de local, en blanco sobre un círculo de su color: una taza de café
# (cafetería), cuchillo y tenedor (restaurante), una jarra de cerveza (bar) y una hamburguesa
# (comida rápida). Los colores están comprobados por pares con el validador de paletas
# (diferencia mínima 9,3 en deuteranopia y 8,6 en tritanopia). Los mismos en el mapa, las
# leyendas, el informe y el documento descargable. Dibujos propios en una rejilla de 24;
# «{c}» es el color del tipo (para las vetas de la jarra).
DIBUJO_TIPO = {
    "cafeteria": (
        "<path d='M7 10h8v3.2a3.6 3.6 0 0 1-3.6 3.6h-.8A3.6 3.6 0 0 1 7 13.2z' fill='#fff'/>"
        "<path d='M15 11h1a1.6 1.6 0 0 1 0 3.2h-1' fill='none' stroke='#fff' stroke-width='1.4'/>"
        "<path d='M6.3 18.4h10.4' stroke='#fff' stroke-width='1.4' stroke-linecap='round'/>"
        "<path d='M9.6 5.6c-.7.8.7 1.5 0 2.5M12.6 5.6c-.7.8.7 1.5 0 2.5' fill='none' "
        "stroke='#fff' stroke-width='1.2' stroke-linecap='round'/>"),
    "restaurante": (
        "<path d='M7.4 5.6v3.6a1.9 1.9 0 0 0 3.8 0V5.6M9.3 5.6v12.8' fill='none' stroke='#fff' "
        "stroke-width='1.4' stroke-linecap='round' stroke-linejoin='round'/>"
        "<path d='M15.8 18.4V5.6c-1.7.9-2.4 3.1-2.4 5.4 0 1.2.6 1.9 1.5 1.9h.9' fill='#fff' "
        "stroke='#fff' stroke-width='1.2' stroke-linecap='round' stroke-linejoin='round'/>"),
    "bar": (
        "<path d='M14.6 10.6h1.3a1.5 1.5 0 0 1 1.5 1.5v2.3a1.5 1.5 0 0 1-1.5 1.5h-1.3' "
        "fill='none' stroke='#fff' stroke-width='1.5'/>"
        "<rect x='7' y='8.6' width='7.6' height='9.6' rx='1.1' fill='#fff'/>"
        "<path d='M6.6 9.4a2.1 2.1 0 0 1 2.2-2.9 2.4 2.4 0 0 1 4.3-.2 1.9 1.9 0 0 1 2 3.1z' "
        "fill='#fff'/>"
        "<path d='M9.5 11.4v4.8M12.1 11.4v4.8' stroke='{c}' stroke-width='1.1' "
        "stroke-linecap='round'/>"),
    "comida_rapida": (
        "<path d='M6.4 11.3a5.6 4.3 0 0 1 11.2 0z' fill='#fff'/>"
        "<rect x='5.8' y='12.4' width='12.4' height='1.7' rx='.85' fill='#fff'/>"
        "<path d='M6.4 15.1h11.2v.6a2.1 2.1 0 0 1-2.1 2.1H8.5a2.1 2.1 0 0 1-2.1-2.1z' fill='#fff'/>"
        "<path d='M9.4 8.9h.1M12 8.3h.1M14.6 8.9h.1' stroke='{c}' stroke-width='1.1' "
        "stroke-linecap='round'/>"),
}


def marca_tipo(tipo: str, px: int = 22) -> str:
    """La marca de un tipo de local (su dibujo en blanco sobre un círculo de su color), como
    SVG suelto: vale para el mapa (que va en un marco aparte, sin la hoja de estilos) y para
    las leyendas."""
    color = COLOR_TIPO.get(tipo, "#999999")
    dibujo = DIBUJO_TIPO.get(tipo, DIBUJO_TIPO["bar"]).replace("{c}", color)
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{px}' height='{px}' "
            "viewBox='0 0 24 24'><circle cx='12' cy='12' r='11' fill='" + color
            + "' stroke='#ffffff' stroke-width='1.5'/>" + dibujo + "</svg>")


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


def con_tipo(rec: dict) -> bool:
    """¿Se ha elegido tipo de local? Sin él, el resultado es general."""
    return bool(rec.get("tipo_local"))


def _punta(rec: dict, dia: str, clientes: bool) -> list[dict]:
    det = rec["a_que_hora"]["detalle"].get(dia, {})
    return det.get("horas_punta_clientes" if clientes else "horas_punta") or []


def horas_punta(rec: dict, dia: str, clientes: bool = False) -> list[int]:
    """Horas punta de la gente que pasa o, con `clientes`, las de más clientes posibles del
    tipo de local elegido."""
    return [int(h["hora"][:2]) for h in _punta(rec, dia, clientes)]


def grupos_horas(rec: dict, dia: str, clientes: bool = False) -> list[list[int]]:
    """Horas punta agrupadas en tramos seguidos, ordenados por la hora más concurrida."""
    punta = _punta(rec, dia, clientes)
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


def hora_de_grupo(rec: dict, dia: str, g: list[int], clientes: bool = False) -> int:
    total = {int(h["hora"][:2]): h["total"] for h in _punta(rec, dia, clientes)}
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
                 "canas_raciones": "cañas con raciones", "cenas": "cenas", "copas": "copas",
                 "comida_llevar": "comida para llevar", "comida": "comidas a la carta"}


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


def estable(rec: dict, dia: str = "laborable") -> bool:
    """¿La hora con más clientes aguanta si los supuestos se mueven a la mitad o al doble?"""
    sens = rec["a_que_hora"]["detalle"].get(dia, {}).get("sensibilidad")
    return bool(sens is None or sens["estable"])


def respuestas(rec: dict, inf: dict) -> dict:
    """Pregunta, respuesta corta, línea de apoyo y recomendación de la que sale la
    fiabilidad, para cada una de las cuatro tarjetas. Con tipo de local, la de la hora
    pregunta «¿Cuándo tendrías más clientes?» y recuerda en el apoyo cuándo pasa más gente;
    sin él, pregunta «¿Cuándo pasa más gente?» (resultado general). Sin cifras de clientes."""
    aq = rec["a_quien"]["recomendaciones"]
    hr = rec["a_que_hora"]["recomendaciones"]
    qv = rec["que_vender"]
    pr = rec["a_que_precio"]["recomendaciones"]
    lab = clientes_principales(rec)
    sab = clientes_principales(rec, "fin_de_semana")
    tipo = con_tipo(rec)
    g_sab = grupos_horas(rec, "fin_de_semana", tipo)
    v_lab = rec_dia(qv["recomendaciones"], "laborable")
    v_sab = rec_dia(qv["recomendaciones"], "fin_de_semana")
    gama = bloque_inf(inf, "precios")["datos"]["gama_ajustada"]["gama"]["semana"]
    if tipo:
        g_paso = grupos_horas(rec, "laborable")
        cuando = {
            "pregunta": "¿Cuándo tendrías más clientes?",
            "respuesta": mayus(horas_calle(grupos_horas(rec, "laborable", True)))
            or "Sin datos",
            "apoyo": (f"Pasa más gente {horas_calle(g_paso)}" if g_paso else "")
            + ("" if estable(rec) else ". Cambia con poco: compruébalo"),
            "rec": (rec_dia(hr, "laborable") or hr)[0]}
    else:
        cuando = {
            "pregunta": "¿Cuándo pasa más gente?",
            "respuesta": mayus(horas_calle(grupos_horas(rec, "laborable"))) or "Sin datos",
            "apoyo": f"Los sábados, {horas_calle(g_sab)}" if g_sab else "",
            "rec": (rec_dia(hr, "laborable") or hr)[0]}
    return {
        "quien": {
            "pregunta": "¿Quién te compraría?" if tipo else "¿Quién pasa por aquí?",
            "respuesta": mayus(lista_y([CLIENTE_CALLE[t] for t, _ in lab])) or "Poca gente",
            "apoyo": f"Los sábados, sobre todo {CLIENTE_CALLE[sab[0][0]]}" if sab else "",
            "rec": (rec_dia(aq, "laborable") or aq)[0]},
        "cuando": cuando,
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


def comparacion_franjas(rec: dict, dia: str = "laborable") -> str:
    """«Más clientes a mediodía que a primera hora»: la franja de la hora con más clientes
    posibles frente a la de la hora con más gente de paso (o, si es la misma, frente a la
    siguiente franja con más clientes). Cada franja vale lo que su mejor hora, para que diga
    lo mismo que las horas punta. Si la diferencia es pequeña, lo dice. Sin cifras."""
    det = rec["a_que_hora"]["detalle"].get(dia, {})
    ch = det.get("clientes_por_hora")
    if not ch or max(ch) <= 0:
        return ""
    franja_de = {h: f for f, hs in S.FRANJAS.items() for h in hs}
    pico = {f: max(ch[h] for h in hs) for f, hs in S.FRANJAS.items()}
    mejor = franja_de[max(range(24), key=lambda h: ch[h])]
    punta = det.get("horas_punta") or []
    paso = franja_de[int(max(punta, key=lambda x: x["total"])["hora"][:2])] if punta else None
    otra = paso if paso and paso != mejor else max(
        (f for f in pico if f != mejor and pico[f] > 0), key=pico.get, default=None)
    if not otra or mejor not in FRANJA_CALLE or otra not in FRANJA_CALLE:
        return ""
    if (pico[mejor] - pico[otra]) / pico[mejor] < S.COMPARAR_DIFERENCIA_PEQUENA:
        return (f"{mayus(FRANJA_CALLE[mejor])} y {FRANJA_CALLE[otra]}, parecidos: la "
                "diferencia es pequeña.")
    return (f"Más clientes {FRANJA_CALLE[mejor]} que {FRANJA_CALLE[otra]}"
            + (f", aunque {FRANJA_CALLE[otra]} pasa más gente" if otra == paso else "")
            + ".")


def frases_cuando(rec: dict) -> list[str]:
    out = []
    tipo = con_tipo(rec)
    g_lab = grupos_horas(rec, "laborable")
    g_sab = grupos_horas(rec, "fin_de_semana")
    if tipo:
        corto = S.TIPOS_LOCAL_CORTO[rec["tipo_local"]["clave"]]
        c_lab = grupos_horas(rec, "laborable", True)
        if c_lab:
            out.append(f"Para {corto}, en un día de diario tendrías más clientes "
                       f"{horas_calle(c_lab)}.")
        comp = comparacion_franjas(rec)
        if comp:
            out.append(comp)
        if g_lab:
            out.append(f"Pasa más gente {horas_calle(g_lab)}: no es lo mismo pasar que entrar.")
        c_sab = grupos_horas(rec, "fin_de_semana", True)
        c_dom = grupos_horas(rec, "domingo", True)
        if c_sab:
            out.append(f"Los sábados, más clientes {horas_calle(c_sab)}; los domingos, "
                       f"{horas_calle(c_dom)}." if c_dom else
                       f"Los sábados, más clientes {horas_calle(c_sab)}.")
        flojos = [d for d in ("laborable", "fin_de_semana", "domingo") if not estable(rec, d)]
        if flojos:
            dias = {"laborable": "los días de diario", "fin_de_semana": "los sábados",
                    "domingo": "los domingos"}
            out.insert(1, f"Ojo: {lista_y([dias[d] for d in flojos])}, la hora con más "
                          "clientes cambia si los supuestos cambian un poco. Es poco fiable: "
                          "cuenta tú los clientes.")
        return out
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
    out.append("Es la gente que pasa, no los clientes: elige el tipo de local para saber "
               "cuándo tendrías más clientes.")
    return out


def frases_que(rec: dict) -> list[str]:
    qv = rec["que_vender"]
    lab = [MOMENTO_CALLE[r["momento"]] for r in rec_dia(qv["recomendaciones"], "laborable")]
    sab = [MOMENTO_CALLE[r["momento"]] for r in rec_dia(qv["recomendaciones"], "fin_de_semana")]
    out = []
    if lab and con_tipo(rec):
        corto = S.TIPOS_LOCAL_CORTO[rec["tipo_local"]["clave"]]
        out.append(f"En {corto}, en un día de diario lo que más tendrías es {lab[0]}"
                   + (f"; después, {lista_y(lab[1:3])}." if len(lab) > 1 else "."))
    elif lab:
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
    gc = grupos_horas(rec, "laborable", True)
    hora_c = (f"a las {hora_de_grupo(rec, 'laborable', gc[0], True)}" if gc
              else "en la mejor hora")
    otra = hora if hora != hora_c else "en una hora floja"
    calle = {
        "Contar los clientes": f"Cuenta los clientes de dos o tres locales como el tuyo "
                               f"{hora_c} y {otra}: ¿hay más cuando dice la estimación?",
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
