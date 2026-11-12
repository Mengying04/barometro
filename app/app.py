"""BARómetro: aplicación web (Streamlit).

Muestra, para un punto de la Comunidad de Madrid, el perfil por horas, el informe del local
y las recomendaciones. No repite cálculos: solo llama a perfil_horario(), informe_local() y
recomendar() (src/), a nivel_movimiento() para situar el punto frente al resto de la
Comunidad, y a dos consultas de informe_local para saber en qué municipio cae el punto y
qué locales del radio se dibujan en el mapa.

Hay dos vistas, con un selector arriba:
  - «Resumen» (por defecto), para un hostelero sin conocimientos técnicos: el nivel de
    movimiento de la zona, un titular, cuatro tarjetas con pregunta y respuesta corta, el
    mapa, la gente por horas, cómo se llega, tres avisos y tres comprobaciones, con
    palabras de la calle y números redondos;
  - «Informe completo», con todo lo técnico: confianza, dato o estimación, porqués con
    cifras, mercado, riesgos, comprobaciones, fuentes y fechas.
El resumen solo traduce lo que ya devuelven recomendar() e informe_local(): no calcula nada.

Arranque (desde la raíz del repositorio):
    streamlit run app/app.py --server.address 0.0.0.0 --server.port 8501

Una dirección que no es un portal concreto (una calle sin número, un municipio…) no se
calcula: se enseña en el mapa y se pregunta «¿Es aquí?»; solo se calcula al confirmar o al
tocar el mapa.

Privacidad: las direcciones y los puntos que introduce el usuario solo viven en la memoria
de su sesión; no se escriben en ficheros, registros ni en la URL. Las estadísticas de uso
de Streamlit están desactivadas en .streamlit/config.toml.
"""

from __future__ import annotations

import functools
import html
import os
import re
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

import altair as alt  # noqa: E402
import folium  # noqa: E402
import pandas as pd  # noqa: E402
import shapely  # noqa: E402
import streamlit as st  # noqa: E402
from streamlit_folium import st_folium  # noqa: E402

import fuentes  # noqa: E402
import informe_local as I  # noqa: E402
import perfil_horario as P  # noqa: E402
import supuestos as S  # noqa: E402
from direcciones import (ATRIBUCION_CARTOCIUDAD, coordenadas,  # noqa: E402
                         geocodificar, texto_candidato)
from movimiento import nivel_movimiento, referencia  # noqa: E402
from recomendaciones import recomendar  # noqa: E402

AVISO = ("Orientación a partir de datos abiertos y supuestos explícitos, no garantías. "
         "Toda cifra de personas es una estimación.")
EJEMPLOS = {  # coordenadas de docs/registro/2026-11-10-informe-local-parte-a.md
    "Campus de Vicálvaro": (40.4046, -3.6106),
    "Centro de Fuenlabrada": (40.283366, -3.800132),
    "Plaza Mayor de Griñón": (40.212861, -3.852623),
}
CENTRO_MADRID = (40.4168, -3.7038)
ZOOM_MAXIMO = 16

# ------------------------------------------------------------------------ colores
# Un solo juego de colores para toda la aplicación (tarjetas, gráfico, leyendas y mapa).
PRINCIPAL = "#9c3d1b"
# Tipos de cliente: paleta categórica de referencia (validada para daltonismo en pares
# contiguos), en orden fijo. El orden de apilado del gráfico es este mismo.
COLOR_CLIENTE = {"vecinos": "#2a78d6", "viajeros": "#eb6834", "universitarios": "#1baf7a",
                 "padres_ninos": "#eda100", "pacientes": "#e87ba4", "trabajadores": "#008300",
                 "deporte_eventos": "#6250d6"}
# Tipos de local en el mapa: tonos oscuros y distintos de los de cliente.
COLOR_TIPO = {"bar": "#c4302b", "restaurante": "#1c3f73", "cafeteria": "#8a5a2b",
              "comida_rapida": "#4d4d4d"}
DIA_ETIQUETA = {"Laborable": "laborable", "Sábado": "fin_de_semana"}
# ------------------------------------------------------------------------ medidas
# Cronómetro opcional (BAROMETRO_MEDIR=1): escribe en la terminal cuántas veces se ejecuta
# la página y cuánto tarda cada parte. Nunca escribe direcciones ni puntos.
MEDIR = os.environ.get("BAROMETRO_MEDIR") == "1"
_TIEMPOS: dict[str, float] = {}


class medir:
    """`with medir("mapa"):` suma el tiempo de ese bloque a la parte «mapa»."""

    def __init__(self, parte: str):
        self.parte = parte

    def __enter__(self):
        self.t0 = time.perf_counter()

    def __exit__(self, *_):
        if MEDIR:
            _TIEMPOS[self.parte] = (_TIEMPOS.get(self.parte, 0.0)
                                    + 1000 * (time.perf_counter() - self.t0))


def anotar_medidas(que: str, t_inicio: float) -> None:
    """Una línea por ejecución: qué se ha ejecutado, total y milisegundos por parte."""
    if MEDIR:
        total = 1000 * (time.perf_counter() - t_inicio)
        resto = total - sum(_TIEMPOS.values())
        partes = " ".join(f"{k}={v:.0f}" for k, v in _TIEMPOS.items())
        print(f"MEDIDA {que} total={total:.0f} {partes} resto={resto:.0f}",
              file=sys.stderr, flush=True)
        _TIEMPOS.clear()


def fragmento(nombre: str):
    """Como st.fragment: al tocar algo de dentro solo se vuelve a ejecutar esa parte, no
    toda la página. Además mide lo que tarda (si BAROMETRO_MEDIR=1)."""
    def decorar(f):
        @st.fragment
        @functools.wraps(f)
        def envuelta(*args, **kwargs):
            sola = not st.session_state.get("_en_pagina", False)
            t0 = time.perf_counter()
            with medir(nombre):
                f(*args, **kwargs)
            if sola:
                anotar_medidas(f"fragmento:{nombre}", t0)
        return envuelta
    return decorar


_T_PAGINA = time.perf_counter()

st.set_page_config(page_title="BARómetro", page_icon="☕", layout="wide",
                   initial_sidebar_state="collapsed")

@st.cache_resource
def hoja_de_estilos() -> str:
    """El CSS de la página, sin comentarios ni espacios de sobra (se prepara una vez)."""
    css = """
<style>
.block-container {padding: 2.8rem 2rem 1.5rem 2rem; max-width: 1320px;}
[data-testid="stCaptionContainer"], .stButton button p {font-size: 0.95rem;}
h1, h2, h3, h4 {letter-spacing: -0.01em;}
.marca {display:flex; align-items:baseline; gap:0.8rem; flex-wrap:wrap; margin-bottom:0.2rem;}
.marca b {font-size:1.8rem; font-weight:700; color:#9c3d1b; letter-spacing:-0.02em;}
.marca span {color:#4a4038; font-size:1rem;}
.aviso {font-size:0.95rem; color:#4a4038; border-left:3px solid #c98a2b;
        padding:0.1rem 0.7rem; margin:0.3rem 0 0.6rem 0;}
.donde {font-size:1rem; color:#4a4038; margin:0.6rem 0 0 0;}
.titular {font-size:2.1rem; font-weight:700; line-height:1.2; color:#1f1b16;
          margin:0.2rem 0 1.2rem 0;}
.mov {margin:0.5rem 0 0.9rem 0; max-width:46rem;}
.mov-cab {font-size:1rem; color:#4a4038;}
.mov-cab b {font-size:1.35rem; font-weight:700; color:#1f1b16; margin-right:0.5rem;}
.mov-escala {display:grid; grid-template-columns:repeat(5, 1fr); gap:0.3rem;
             margin:0.45rem 0 0.35rem 0;}
.mov-escala div {text-align:center; font-size:0.8rem; line-height:1.2; color:#5c5248;}
.mov-escala i {display:block; height:0.7rem; border-radius:0.35rem; background:#e3dcd1;
               margin-bottom:0.25rem;}
.mov-escala i.si {background:#9c3d1b;}
.mov-escala div.aqui {color:#1f1b16; font-weight:700;}
.mov-frase {font-size:1.05rem; color:#1f1b16;}
.poco-paso {font-size:1.1rem; line-height:1.45; color:#1f1b16; background:#fbefc9;
            border-left:4px solid #c98a2b; padding:0.7rem 1rem; margin:0 0 1rem 0;}
.confirma {font-size:1.25rem; font-weight:700; color:#1f1b16; margin:0.8rem 0 0.2rem 0;}
.confirma-pie {font-size:1.05rem; color:#4a4038; margin:0 0 0.6rem 0;}
.llegar {font-size:1.15rem; line-height:1.5; margin:0.2rem 0 0.6rem 0;}
.llegar b {font-weight:700;}
.llegar div {padding:0.35rem 0;}
.seccion {font-size:1.45rem; font-weight:700; line-height:1.25; color:#1f1b16;
          margin:1.6rem 0 0.6rem 0;}

/* Tarjetas del resumen: toda la tarjeta es el botón (el botón real, invisible, la cubre). */
[class*="st-key-tarjeta_"] {position:relative; background:#ffffff; padding:1.2rem 1.3rem;}
[class*="st-key-tarjeta_"]:hover {box-shadow:0 2px 12px rgba(60,40,20,0.14);}
[class*="st-key-tarjeta_"]:focus-within {outline:3px solid #c98a2b; outline-offset:2px;}
[class*="st-key-abrir_"] {position:absolute !important; inset:0; width:auto !important;
                          z-index:5; margin:0;}
[class*="st-key-abrir_"] div {height:100%;}
[class*="st-key-abrir_"] button {width:100%; height:100%; opacity:0; cursor:pointer;}
.pregunta {font-size:1.05rem; font-weight:500; color:#5c5248;}
.respuesta {font-size:1.7rem; font-weight:700; line-height:1.2; color:#1f1b16;
            margin:0.5rem 0 0.5rem 0; min-height:4.1rem;}
.apoyo {font-size:1rem; color:#4a4038; line-height:1.35; min-height:2.7rem;}
.fiable {font-size:0.95rem; color:#4a4038; margin-top:0.6rem; white-space:nowrap;}
.fiable i {display:inline-block; width:0.7rem; height:0.7rem; border-radius:50%;
           margin-right:0.2rem; background:#d9d0c3;}
.fiable i.si {background:#1f1b16;}
.fiable span {margin-left:0.3rem;}
.ver {font-size:1rem; font-weight:600; color:#9c3d1b; margin-top:0.7rem;}

/* Explicación de la tarjeta abierta, a todo el ancho. */
.st-key-explicacion {background:#ffffff; padding:1.4rem 1.6rem;
                     border-color:#9c3d1b !important;}
.explica-titulo {font-size:1.35rem; font-weight:700; margin-bottom:0.5rem;}
.explica p {font-size:1.15rem; line-height:1.5; margin:0 0 0.5rem 0; color:#1f1b16;}
.cifra {font-size:2.8rem; font-weight:700; color:#9c3d1b; line-height:1.1;}
.cifra-pie {font-size:1.05rem; color:#4a4038; margin-top:0.3rem;}
.diez i {display:inline-block; width:1.7rem; height:1.7rem; border-radius:50%;
         margin:0 0.3rem 0.3rem 0;}
.lista-grande {font-size:1.15rem; line-height:1.5; margin:0.2rem 0 0.6rem 0;}
.lista-grande div {padding:0.35rem 0;}

.etiqueta {display:inline-block; padding:0.08rem 0.5rem; border-radius:0.6rem;
           font-size:0.8rem; font-weight:500; margin:0.35rem 0.25rem 0 0;
           background:#efe9e0; color:#4a3d32;}
.conf-alta {background:#dcefdf; color:#1b5427;}
.conf-media {background:#fbefc9; color:#5e4700;}
.conf-baja {background:#f6dcda; color:#7a1f1f;}
.punto {display:inline-block; width:0.8rem; height:0.8rem; border-radius:50%;
        margin-right:0.35rem; vertical-align:0.02rem;}
.leyenda {font-size:0.95rem; color:#4a4038; line-height:1.9;}
.leyenda b {font-weight:600; margin-right:0.5rem;}
.leyenda span {display:inline-block; margin-right:0.9rem; white-space:nowrap;}
.frase {font-size:0.95rem; color:#4a4038; margin-top:-0.4rem;}
.riesgo {font-size:1rem; margin:0.2rem 0 0 0;}
.pie {font-size:0.95rem; color:#5c5248; border-top:1px solid #e3dcd1;
      padding-top:0.8rem; margin-top:2rem;}
.pie a {color:#5c5248;}
div[data-testid="stMetric"] {padding:0;}
@media (max-width: 640px) {
  .titular {font-size:1.6rem;}
  .block-container {padding-left: 1rem; padding-right: 1rem;}
  .respuesta, .apoyo {min-height:0;}
  .cifra {font-size:2.2rem;}
  .mov-escala div {font-size:0.7rem;}
}
@media print {header, .stButton, iframe {display:none !important;}}
</style>
"""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return re.sub(r"\s+", " ", css).strip()


st.session_state["_en_pagina"] = True
st.markdown(hoja_de_estilos(), unsafe_allow_html=True)


# ----------------------------------------------------------------------------- datos
@st.cache_resource(show_spinner="Cargando los datos abiertos (solo la primera vez)…")
def cargar_datos() -> bool:
    """Carga en memoria todas las capas que usan los cálculos (una vez por proceso)."""
    P.capas()
    I.capas()
    I.locales()
    I.renta_comunidad()
    I.transporte()
    referencia()
    return True


def municipio_de(lat: float, lon: float) -> dict | None:
    """Municipio de la Comunidad en el que cae el punto, o None si está fuera."""
    x, y = I._A_UTM.transform(lon, lat)
    try:
        return I.municipio(shapely.Point(x, y))
    except ValueError:
        return None


def locales_del_radio(lat: float, lon: float, cod_municipio: str) -> pd.DataFrame:
    """Posición y tipo de los locales del radio (misma fuente que el informe); sin nombres
    (los datos procesados no los guardan)."""
    x, y = I._A_UTM.transform(lon, lat)
    fuente = "censo" if cod_municipio == "28079" else "osm"
    loc = I.en_radio(I.locales()[fuente], shapely.Point(x, y), S.RADIO_M)
    return pd.DataFrame({"lat": loc["lat"], "lon": loc["lon"], "tipo": loc["tipo_local"]})


def calcular(lat: float, lon: float) -> dict:
    perfil = P.perfil_horario(lat, lon)
    inf = I.informe_local(lat, lon, perfil=perfil)
    rec = recomendar(lat, lon, perfil=perfil, inf=inf)
    return {"perfil": perfil, "informe": inf, "rec": rec, "mov": nivel_movimiento(perfil)}


# ------------------------------------------------------------------- fuentes.md
# El buscador de direcciones (src/direcciones.py) y el lector de docs/fuentes.md
# (src/fuentes.py) se comparten con el servidor MCP.
leer_fuentes = st.cache_data(fuentes.leer_fuentes)


# ------------------------------------------------------------------- formato
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


def etiquetas(r: dict) -> str:
    c = r.get("confianza", "baja")
    base = r.get("base", "")
    return (f"<span class='etiqueta conf-{c}'>Confianza {c}</span>"
            f"<span class='etiqueta'>{html.escape(base.capitalize())}</span>")


def mostrar_rec(r: dict) -> None:
    """Una recomendación completa: texto, etiquetas y «Por qué» desplegable."""
    st.markdown(f"{r['texto']}<br>{etiquetas(r)}", unsafe_allow_html=True)
    if r.get("porque"):
        with st.expander("Por qué"):
            st.markdown("\n".join(f"- {p}" for p in r["porque"]))


def bloque_inf(inf: dict, clave: str) -> dict:
    return next(b for b in inf["bloques"] if b["clave"] == clave)


# ------------------------------------------- lecturas de recomendar() (sin cálculos)
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


# ------------------------------------------------- vista Resumen: palabras de la calle
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
COLOR_OTROS = "#b8b0a4"
DIA_RESUMEN = {"Día de diario": "laborable", "Sábado": "fin_de_semana"}


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
    return any(r["texto"].startswith("Competencia alta") for r in rec["riesgos"])


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


def fiabilidad(r: dict) -> str:
    n, texto = FIABILIDAD.get(r.get("confianza"), FIABILIDAD["baja"])
    puntos = "".join(f"<i class='{'si' if i < n else ''}'></i>" for i in range(3))
    return f"<div class='fiable'>{puntos}<span>{texto}</span></div>"


def alternar(clave: str | None) -> None:
    """Abre la explicación de una tarjeta (solo una a la vez) o la cierra."""
    st.session_state["abierta"] = (None if st.session_state.get("abierta") == clave
                                   else clave)


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


def tarjetas_resumen(resp: dict) -> None:
    abierta = st.session_state.get("abierta")
    if abierta:   # la tarjeta abierta se marca con el color principal
        st.markdown(f"<style>.st-key-tarjeta_{abierta} {{border:2px solid #9c3d1b "
                    "!important;}</style>", unsafe_allow_html=True)
    for col, (clave, t) in zip(st.columns(4, gap="small"), resp.items()):
        with col, st.container(border=True, key=f"tarjeta_{clave}"):
            st.markdown(
                f"<div class='pregunta'>{t['pregunta']}</div>"
                f"<div class='respuesta'>{html.escape(t['respuesta'])}</div>"
                f"<div class='apoyo'>{html.escape(t['apoyo'])}</div>"
                + fiabilidad(t["rec"])
                + f"<div class='ver'>{'Cerrar ▴' if abierta == clave else 'Ver por qué ▾'}"
                  "</div>", unsafe_allow_html=True)
            st.button(f"Ver por qué: {t['pregunta']}", key=f"abrir_{clave}",
                      on_click=alternar, args=(clave,))


def frases_quien(rec: dict) -> list[str]:
    lab = clientes_principales(rec)
    sab = clientes_principales(rec, "fin_de_semana")
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
    if any(t == "viajeros" for t, _ in lab + sab):
        out.append("Los viajeros van al metro, al tren o al autobús: paran menos.")
    return out


def diez_clientes(rec: dict) -> None:
    """«De cada 10 posibles clientes»: diez puntos con el color de cada tipo."""
    r = rec_dia(rec["a_quien"]["recomendaciones"], "laborable")
    pesos = sorted((r[0].get("pesos") or {}).items(), key=lambda kv: -kv[1]) if r else []
    reparto = [(t, round(10 * p)) for t, p in pesos if round(10 * p) > 0]
    while sum(n for _, n in reparto) > 10:
        reparto[-1] = (reparto[-1][0], reparto[-1][1] - 1)
    otros = 10 - sum(n for _, n in reparto)
    puntos = "".join(f"<i style='background:{COLOR_CLIENTE[t]}'></i>" * n
                     for t, n in reparto) + f"<i style='background:{COLOR_OTROS}'></i>" * otros
    texto = " · ".join([f"{n} {CLIENTE_CALLE[t]}" for t, n in reparto if n]
                       + ([f"{otros} de otro tipo"] if otros else []))
    st.markdown("<div class='cifra-pie'>De cada 10 posibles clientes en un día de diario:"
                f"</div><div class='diez' style='margin-top:0.6rem'>{puntos}</div>"
                f"<div class='cifra-pie'>{texto}</div>", unsafe_allow_html=True)


def frases_cuando(rec: dict) -> list[str]:
    out = []
    g_lab = grupos_horas(rec, "laborable")
    g_sab = grupos_horas(rec, "fin_de_semana")
    if g_lab:
        out.append(f"En un día de diario hay más gente {horas_calle(g_lab)}.")
    if g_sab:
        out.append(f"Los sábados, {horas_calle(g_sab)}.")
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


def cifra_cuando(rec: dict) -> None:
    punta = rec["a_que_hora"]["detalle"]["laborable"]["horas_punta"]
    if punta:
        mejor = max(punta, key=lambda h: h["total"])
        st.markdown(f"<div class='cifra'>Unas {unas(mejor['total'])} personas</div>"
                    f"<div class='cifra-pie'>pasan cerca a las {int(mejor['hora'][:2])}, la "
                    "mejor hora de un día de diario.</div>", unsafe_allow_html=True)


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
    sobra = [LOCAL_CALLE[h["tipo"]] for h in qv["huecos"]
             if h.get("sentido") == "sobra" and h.get("tipo") in LOCAL_CALLE]
    if sobra:
        out.append(f"Ya hay muchos {lista_y(sobra[:2])} cerca: ahí cuesta más competir.")
    return out


def barras_que(rec: dict) -> None:
    mo = rec["que_vender"]["momentos"]["laborable"]
    datos = pd.DataFrame([{"momento": mayus(MOMENTO_CALLE[m]), "n": n,
                           "txt": f"unos {unas(n)}"} for m, n in mo.items() if n > 0])
    if datos.empty:
        return
    datos = datos.sort_values("n", ascending=False).head(5)
    base = alt.Chart(datos).encode(
        y=alt.Y("momento:N", sort="-x", title=None,
                axis=alt.Axis(labelFontSize=15, labelLimit=220, labelColor="#1f1b16",
                              ticks=False, domain=False)),
        x=alt.X("n:Q", axis=None, scale=alt.Scale(domain=[0, datos["n"].max() * 1.7])))
    st.markdown("<div class='cifra-pie'>Posibles clientes en un día de diario:</div>",
                unsafe_allow_html=True)
    st.altair_chart(
        (base.mark_bar(color=PRINCIPAL, cornerRadiusEnd=4, height=22)
         + base.mark_text(align="left", dx=6, fontSize=15, color="#1f1b16").encode(
             text="txt:N")).properties(height=42 * len(datos)).configure_view(strokeWidth=0),
        width="stretch")


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


def cifra_precio(inf: dict) -> None:
    v = (bloque_inf(inf, "precios")["datos"].get("ipc_interanual") or {}).get(
        "restaurantes_alojamiento")
    if v is not None and v > 0:
        st.markdown(f"<div class='cifra'>Cerca de un {round(v)} % más</div>"
                    "<div class='cifra-pie'>han subido en un año los precios de bares, "
                    "restaurantes y hoteles en la región.</div>", unsafe_allow_html=True)


def explicacion(clave: str, resp: dict, rec: dict, inf: dict) -> None:
    """Explicación de la tarjeta abierta: a todo el ancho, debajo de la fila."""
    frases = {"quien": lambda: frases_quien(rec), "cuando": lambda: frases_cuando(rec),
              "que": lambda: frases_que(rec), "precio": lambda: frases_precio(inf)}[clave]()
    figura = {"quien": lambda: diez_clientes(rec), "cuando": lambda: cifra_cuando(rec),
              "que": lambda: barras_que(rec), "precio": lambda: cifra_precio(inf)}[clave]
    t = resp[clave]
    with st.container(border=True, key="explicacion"):
        st.markdown(f"<div class='explica-titulo'>{t['pregunta']} "
                    f"{html.escape(t['respuesta'])}</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([3, 2], gap="large")
        with c1:
            st.markdown("<div class='explica'>" + "".join(
                f"<p>{html.escape(f)}</p>" for f in frases[:4]) + "</div>"
                + fiabilidad(t["rec"]), unsafe_allow_html=True)
        with c2:
            figura()
        st.button("Cerrar", key="cerrar_explicacion", on_click=alternar, args=(clave,))


def avisos_calle(rec: dict, inf: dict) -> list[str]:
    """Como mucho tres avisos, de una línea, con lo más importante primero."""
    total = bloque_inf(inf, "competencia")["datos"]["total"]
    out = []
    for r in sorted(rec["riesgos"], key=lambda r: icono_y_orden(r["texto"])[0]):
        t, ico = r["texto"], icono_y_orden(r["texto"])[1]
        if t.startswith("Periodos sin clase"):
            cuando = "de la universidad" if "universitarios" in t else "escolares"
            frase = f"En vacaciones {cuando} pasa mucha menos gente."
        elif t.startswith("Competencia alta"):
            frase = f"Ya hay muchos bares y restaurantes cerca: {total}."
        elif t.startswith("Cobertura baja"):
            frase = "Puede haber más locales de los que salen en el mapa."
        elif t.startswith("No se puede valorar"):
            frase = "No sabemos si aquí hay mucha o poca competencia."
        elif t.startswith("Festivos"):
            frase = "Vienen festivos: esos días cambia la gente que pasa."
        else:
            continue
        if f"{ico} {frase}" not in out:
            out.append(f"{ico} {frase}")
    return out[:3] or ["✅ No vemos nada especial, pero compruébalo en persona."]


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


def grafico_resumen(perfil: dict, rec: dict, dia: str) -> list[tuple[str, str]]:
    """Gente por horas con pocos colores: los tipos con poco peso se juntan en «Otros».
    Devuelve las entradas de la leyenda."""
    horas = perfil["horas"].loc[dia]
    suma = horas[list(COLOR_CLIENTE)].sum()
    grandes = [t for t in COLOR_CLIENTE if suma.sum() > 0 and suma[t] / suma.sum() >= 0.05]
    tabla = horas[grandes].copy()
    resto = [t for t in COLOR_CLIENTE if t not in grandes]
    hay_otros = bool(resto) and float(horas[resto].sum().sum()) > 0
    if hay_otros:
        tabla["otros"] = horas[resto].sum(axis=1)
    nombres = {**{t: mayus(CLIENTE_CALLE[t]) for t in grandes}, "otros": "Otros"}
    colores = {**{t: COLOR_CLIENTE[t] for t in grandes}, "otros": COLOR_OTROS}
    orden = list(tabla.columns)
    largo = tabla.reset_index().melt(id_vars="hora", var_name="tipo", value_name="personas")
    largo["quien"] = largo["tipo"].map(nombres)
    largo["orden"] = largo["tipo"].map({t: i for i, t in enumerate(orden)})
    largo["txt"] = largo["personas"].map(lambda n: f"unas {unas(n)}" if n >= 1 else "casi nadie")
    barras = alt.Chart(largo).mark_bar(stroke="#fbfaf7", strokeWidth=0.6).encode(
        x=alt.X("hora:O", title="Hora del día",
                axis=alt.Axis(labelAngle=0, labelFontSize=13, titleFontSize=14,
                              labelColor="#4a4038", labelOverlap=True)),
        y=alt.Y("personas:Q", title="Personas que pasan cerca",
                axis=alt.Axis(labelExpr="replace(format(datum.value, ',.0f'), ',', '.')",
                              labelFontSize=13, titleFontSize=14, labelColor="#4a4038",
                              gridColor="#ece6dc", tickCount=5)),
        color=alt.Color("quien:N", legend=None,
                        scale=alt.Scale(domain=[nombres[t] for t in orden],
                                        range=[colores[t] for t in orden])),
        order=alt.Order("orden:Q", sort="ascending"),
        tooltip=[alt.Tooltip("hora:O", title="Hora"), alt.Tooltip("quien:N", title="Quién"),
                 alt.Tooltip("txt:N", title="Personas")])
    capas = barras
    mejores = [hora_de_grupo(rec, dia, g) for g in grupos_horas(rec, dia)[:2]]
    if mejores:
        marca = pd.DataFrame([{"hora": h, "total": float(horas["total"].loc[h]),
                               "txt": "más gente"} for h in mejores])
        capas = barras + alt.Chart(marca).mark_text(
            dy=-10, fontSize=13, fontWeight=600, color="#1f1b16").encode(
            x="hora:O", y="total:Q", text="txt:N")
    st.altair_chart(capas.properties(height=360).configure_view(strokeWidth=0),
                    width="stretch")
    return [(nombres[t], colores[t]) for t in orden]


def escala_movimiento(mov: dict) -> str:
    """Nivel de movimiento de la zona: nombre, escala de cinco niveles y comparación."""
    celdas = "".join(
        f"<div class='{'aqui' if i == mov['nivel'] else ''}'>"
        f"<i class='{'si' if i <= mov['nivel'] else ''}'></i>{html.escape(n)}</div>"
        for i, n in enumerate(mov["niveles"], 1))
    return ("<div class='mov'><div class='mov-cab'>"
            f"<b>{html.escape(mov['nombre'])}</b><span class='etiqueta'>Estimación</span>"
            "</div>"
            f"<div class='mov-escala' role='img' aria-label='Nivel {mov['nivel']} de 5: "
            f"{html.escape(mov['nombre'])}'>{celdas}</div>"
            f"<div class='mov-frase'>Por aquí {html.escape(mov['frase'])}.</div></div>")


MODO_CALLE = {"Metro": "metro", "Cercanías": "tren de Cercanías",
              "Metro Ligero": "metro ligero", "Autobús urbano": "autobús urbano",
              "Autobús interurbano": "autobús interurbano"}
ENTORNO_CALLE = {
    "aislado": "Es un sitio aislado: casi no vive nadie cerca.",
    "borde": "Está en el borde de un barrio: justo al lado vive poca gente, pero un poco "
             "más lejos sí.",
    "dentro": "Está dentro de una zona con vecinos."}


def frases_llegar(inf: dict) -> list[str]:
    """Cómo se llega y qué hay un poco más lejos, en dos o tres frases sencillas. Solo
    traduce los bloques «accesos» y «entorno» del informe."""
    a = bloque_inf(inf, "accesos")["datos"]
    e = bloque_inf(inf, "entorno")["datos"]
    cerca = [MODO_CALLE[m] for m in a["cerca"]]
    lejos = [MODO_CALLE[m] for m in a["lejos"] if m not in a["cerca"]]
    lejos_txt = f"A unos {S.ACCESOS_MINUTOS_LEJOS} minutos andando"
    if cerca:
        transporte = (f"A menos de 4 minutos andando hay {lista_y(cerca)}."
                      + (f" {lejos_txt}, también {lista_y(lejos)}." if lejos else ""))
    elif lejos:
        transporte = (f"No hay paradas a menos de 4 minutos andando. {lejos_txt} hay "
                      f"{lista_y(lejos)}.")
    else:
        transporte = f"No hay paradas ni a {S.ACCESOS_MINUTOS_LEJOS} minutos andando."
    out = [f"<b>{html.escape(a['nivel'])}.</b> {transporte}"]
    vecinos = (f"viven unas {redondo(e['vecinos'])} personas" if e["vecinos"] >= 20
               else "no vive casi nadie")
    locales = ("no hay ningún bar ni restaurante" if e["locales"] == 0 else
               "hay 1 bar o restaurante" if e["locales"] == 1 else
               f"hay {miles(e['locales'])} bares y restaurantes")
    out.append(f"<b>A {e['minutos_andando']} minutos andando</b> {vecinos} y {locales}. "
               f"{ENTORNO_CALLE[e['tipo']]}")
    return out


# ------------------------------------------------------------------ mapa y gráfico
def construir_mapa(lat, lon, locs: pd.DataFrame | None, zoom: int = 16) -> folium.Map:
    zoom = zoom if lat is not None else 10
    centro = (lat, lon) if lat is not None else CENTRO_MADRID
    # Zoom máximo 16: a partir de 17 las teselas de OpenStreetMap rotulan los nombres de
    # bares y comercios, y la aplicación no debe mostrar nombres de locales.
    m = folium.Map(location=centro, zoom_start=zoom, tiles=None, control_scale=True,
                   max_zoom=ZOOM_MAXIMO)
    folium.TileLayer(
        tiles="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr='© <a href="https://www.openstreetmap.org/copyright">colaboradores de '
             'OpenStreetMap</a>', max_zoom=ZOOM_MAXIMO).add_to(m)
    if lat is not None:
        folium.Circle((lat, lon), radius=S.RADIO_M, color=PRINCIPAL, weight=2,
                      fill=True, fill_opacity=0.06, interactive=False).add_to(m)
        if locs is not None:
            for f in locs.itertuples():   # sin ventanas ni nombres: solo el tipo por color
                folium.CircleMarker((f.lat, f.lon), radius=5, weight=1.5, color="#ffffff",
                                    fill=True, fill_color=COLOR_TIPO.get(f.tipo, "#999999"),
                                    fill_opacity=0.95, interactive=False).add_to(m)
        folium.CircleMarker((lat, lon), radius=9, weight=3, color="#ffffff",
                            fill=True, fill_color=PRINCIPAL, fill_opacity=1,
                            interactive=False).add_to(m)
    return m


def mapa(lat, lon, locs: pd.DataFrame | None, alto: int = 400,
         zoom: int = 16) -> dict | None:
    """Dibuja el mapa. El objeto del mapa se construye una sola vez por punto y se guarda
    en la sesión. Solo vuelve al servidor el último clic: mover el mapa o hacer zoom no
    provoca ninguna recarga."""
    guardado = st.session_state.get("mapa_obj")
    clave = (lat, lon, zoom, locs is None)
    if not guardado or guardado[0] != clave:
        guardado = (clave, construir_mapa(lat, lon, locs, zoom))
        st.session_state["mapa_obj"] = guardado
    return st_folium(guardado[1], height=alto, use_container_width=True,
                     returned_objects=["last_clicked"], key="mapa")


def leyenda(titulo: str, items: list[tuple[str, str]], extra: str = "") -> None:
    st.markdown(
        f"<div class='leyenda'><b>{titulo}</b>" + "".join(
            f"<span><i class='punto' style='background:{c}'></i>{n}</span>"
            for n, c in items) + extra + "</div>", unsafe_allow_html=True)


def grafico_perfil(perfil: dict, rec: dict, dia: str) -> None:
    orden = list(COLOR_CLIENTE)
    h = perfil["horas"].loc[dia][orden].reset_index()
    largo = h.melt(id_vars="hora", var_name="tipo", value_name="personas")
    largo["cliente"] = largo["tipo"].map(S.TIPOS_CLIENTE)
    largo["orden"] = largo["tipo"].map({t: i for i, t in enumerate(orden)})
    barras = alt.Chart(largo).mark_bar(stroke="#fbfaf7", strokeWidth=0.6).encode(
        x=alt.X("hora:O", title="Hora", axis=alt.Axis(labelAngle=0, labelColor="#5c5248")),
        y=alt.Y("personas:Q", title="Personas que pasan cerca (≈)",
                axis=alt.Axis(labelExpr="replace(format(datum.value, ',.0f'), ',', '.')",
                              labelColor="#5c5248", gridColor="#ece6dc")),
        color=alt.Color("cliente:N", legend=None,
                        scale=alt.Scale(domain=[S.TIPOS_CLIENTE[t] for t in orden],
                                        range=[COLOR_CLIENTE[t] for t in orden])),
        order=alt.Order("orden:Q", sort="ascending"),
        tooltip=[alt.Tooltip("hora:O", title="Hora"), alt.Tooltip("cliente:N", title="Cliente"),
                 alt.Tooltip("personas:Q", title="Personas (≈)", format=",.0f")],
    )
    tot = perfil["horas"].loc[dia]["total"]
    punta = pd.DataFrame([{"hora": hh, "total": float(tot.loc[hh]), "txt": "punta"}
                          for hh in horas_punta(rec, dia)])
    marcas = alt.Chart(punta).mark_text(dy=-9, fontSize=11, fontWeight=600,
                                        color="#1f1b16").encode(
        x="hora:O", y="total:Q", text="txt:N")
    flechas = alt.Chart(punta).mark_tick(color="#1f1b16", thickness=2, size=14).encode(
        x="hora:O", y="total:Q")
    st.altair_chart((barras + flechas + marcas).properties(height=330)
                    .configure_view(strokeWidth=0), width="stretch")


def elegir_punto(lat: float, lon: float, ejemplo: str | None = None) -> None:
    st.session_state["punto"] = (round(lat, 6), round(lon, 6))
    st.session_state["ejemplo"] = ejemplo
    st.session_state.pop("resultado", None)
    st.session_state["abierta"] = None
    st.session_state["todas_comprobaciones"] = False
    st.session_state.pop("pendiente", None)


# Zoom del mapa al enseñar un resultado del buscador que no es un portal.
ZOOM_PENDIENTE = {"calle": 16, "localidad": 14, "municipio": 13, "codigo_postal": 14}
QUE_ES = {"calle": "es una calle entera, sin número",
          "localidad": "es una localidad entera, no una dirección",
          "municipio": "es un municipio entero, no una dirección",
          "codigo_postal": "es un código postal entero, no una dirección"}


def dejar_pendiente(cand: dict, lat: float, lon: float) -> None:
    """Un resultado que no es un portal concreto no se calcula: se guarda como pendiente
    de confirmar y se borra el punto anterior."""
    st.session_state["pendiente"] = {"lat": round(lat, 6), "lon": round(lon, 6),
                                     "texto": cand["texto"], "precision": cand["precision"]}
    st.session_state["punto"] = None
    st.session_state["ejemplo"] = None
    st.session_state.pop("resultado", None)
    st.session_state["abierta"] = None


def confirmar_pendiente() -> None:
    p = st.session_state.get("pendiente")
    if p:
        elegir_punto(p["lat"], p["lon"])
        st.session_state.pop("candidatos", None)


def pedir_busqueda() -> None:
    st.session_state["buscar"] = True


# ------------------------------------------------------------------ mercado
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


AVISOS = {  # nota del informe → aviso corto para la pestaña de riesgos
    "Probablemente faltan locales": "OpenStreetMap no recoge todos los locales: la "
                                    "competencia real es mayor.",
    "incluye hoteles": "El IPC de restauración incluye hoteles: la subida de bares y "
                       "restaurantes probablemente es menor.",
    "aún no están": "Los festivos del año que viene aún no están publicados.",
    "Limitación importante": "Los datos del sector mezclan hostelería con comercio y "
                             "transporte.",
}


def es_aviso(nota: str) -> str | None:
    return next((corto for clave, corto in AVISOS.items() if clave in nota), None)


def tabla_bloque(b: dict) -> None:
    d = b["datos"]
    if b["clave"] == "competencia":
        nombres = {**S.TIPOS_COMPETENCIA, "sirven_comidas": "Sirven comidas"}
        st.dataframe(pd.DataFrame([
            {"Tipo": nombres[k], "En el radio": v["radio"],
             "Media del municipio": v["media_municipio"],
             "Relación": v["relacion"]} for k, v in d["comparacion_por_tipo"].items()]),
            hide_index=True, width="stretch")
    elif b["clave"] == "turismo":
        st.markdown(f"- Código postal {d['codigo_postal_aproximado']}: "
                    + (", ".join(f"{a} {n}" for a, n in d["alojamientos_cp"].items())
                       or "ninguno")
                    + "\n- Municipio: "
                    + (", ".join(f"{a} {n}" for a, n in
                                 d["alojamientos_municipio"].items()) or "ninguno"))
    elif b["clave"] == "festivos":
        st.markdown("\n".join(f"- {p['fecha']} ({p['dia']}): {p['ambito']}"
                              for p in d["proximos"]) or "Sin festivos próximos.")
    elif b["clave"] == "accesos" and d["lejos"]:
        def celda(v):
            return f"{v['lineas']} líneas · {miles(v['vehiculos_dia'])} vehículos" if v else "—"
        st.dataframe(pd.DataFrame([
            {"Modo": m, f"A menos de {d['radio_cerca_m']} m": celda(d["cerca"].get(m)),
             f"A menos de {d['radio_lejos_m']} m": celda(v),
             "Parada más cercana": f"{v['distancia_m']} m"}
            for m, v in d["lejos"].items()]), hide_index=True, width="stretch")
        est = sorted({f"la línea {n} de {m}" for m, v in d["lejos"].items()
                      for n in v.get("lineas_estimadas", [])})
        st.caption("Vehículos en un día laborable típico, sumando los dos sentidos."
                   + (f" Los de {lista_y(est)} son una estimación: no tiene viajes en los "
                      "horarios publicados y se le pone la frecuencia media de líneas "
                      "parecidas." if est else ""))


def bloque_mercado(b: dict) -> None:
    with st.container(border=True):
        try:
            etiqueta, valor, frase = metrica_bloque(b)
        except (KeyError, TypeError, ValueError, IndexError):
            etiqueta, valor, frase = b["titulo"], "—", ""
        st.markdown(f"**{b['titulo']}** <span class='etiqueta'>"
                    f"{html.escape(b['caracter'].capitalize())}</span>",
                    unsafe_allow_html=True)
        st.metric(etiqueta, valor)
        if frase:
            st.markdown(f"<div class='frase'>{html.escape(frase)}</div>",
                        unsafe_allow_html=True)
        avisos = [n for n in b["notas"] if es_aviso(n)]
        with st.expander("Detalle, notas y fuentes" + (" ⚠️" if avisos else "")):
            st.markdown(b["resumen"])
            tabla_bloque(b)
            for n in b["notas"]:
                (st.warning if es_aviso(n) else st.caption)(n)
            st.caption("Fuentes: " + "; ".join(
                f"[{f['nombre']}]({f['enlace']}) ({f['licencia']}"
                + (f"; {f['periodo']}" if f.get("periodo") else "")
                + f"; descargado el {f['descargado']})" for f in b["fuentes"]))


# ------------------------------------------------------------------ riesgos
PRIORIDAD_RIESGO = [  # lo que más cambia el negocio, primero
    ("Periodos sin clase", "🎓"), ("Competencia alta", "🏪"), ("Cobertura baja", "🗺️"),
    ("No se puede valorar", "❔"), ("Festivos", "📅"), ("Sin riesgos", "✅")]


def icono_y_orden(texto: str) -> tuple[int, str]:
    for i, (clave, ico) in enumerate(PRIORIDAD_RIESGO):
        if texto.startswith(clave):
            return i, ico
    return len(PRIORIDAD_RIESGO), "⚠️"


def pestana_riesgos(rec: dict, inf: dict) -> None:
    for r in sorted(rec["riesgos"], key=lambda r: icono_y_orden(r["texto"])[0]):
        ico = icono_y_orden(r["texto"])[1]
        titulo, _, resto = r["texto"].partition(": ")
        st.markdown(f"<div class='riesgo'>{ico} <b>{html.escape(titulo)}</b>"
                    + (f": {html.escape(resto)}" if resto else "")
                    + f"<br>{etiquetas(r)}</div>", unsafe_allow_html=True)
        if r.get("porque"):
            with st.expander("Por qué"):
                st.markdown("\n".join(f"- {p}" for p in r["porque"]))
    st.markdown("##### Avisos sobre los datos")
    avisos = [es_aviso(n) for b in inf["bloques"] for n in b["notas"] if es_aviso(n)]
    st.markdown("\n".join(
        f"- ⚠️ {a}" for a in dict.fromkeys(
            avisos + ["El domingo no se modela aparte: «sábado» representa el fin de "
                      "semana.",
                      "Toda cifra de personas y de gasto es una estimación con supuestos "
                      "explícitos (src/supuestos.py)."])))
    st.caption("El texto completo de cada aviso está en la pestaña Mercado, en «Detalle, "
               "notas y fuentes».")


# --------------------------------------------------------------- detalle y fuentes
def pestana_detalle(rec: dict, perfil: dict) -> None:
    st.caption(rec["a_quien"]["nota"])
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("##### 👥 A quién")
        for r in rec["a_quien"]["recomendaciones"]:
            mostrar_rec(r)
        with st.expander("Clientes por franja"):
            filas = []
            for f in S.FRANJAS:
                fila = {"Franja": f}
                for d, et in (("laborable", "Laborable"), ("fin_de_semana", "Sábado")):
                    c = rec["a_quien"]["por_franja"][d][f]
                    fila[et] = ", ".join(
                        f"{x['nombre']} {100 * x['peso']:.0f} %" for x in c["clientes"]) or "—"
                filas.append(fila)
            st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
        st.markdown("##### 🕗 A qué hora")
        t1, t2 = st.tabs(["Laborable", "Sábado"])
        for tab, d in ((t1, "laborable"), (t2, "fin_de_semana")):
            with tab:
                for r in rec_dia(rec["a_que_hora"]["recomendaciones"], d):
                    mostrar_rec(r)
    with c2:
        st.markdown("##### 🍽️ Qué vender")
        qv = rec["que_vender"]
        t1, t2, t3 = st.tabs(["Laborable", "Sábado", "Huecos y cocinas"])
        with t1:
            for r in rec_dia(qv["recomendaciones"], "laborable"):
                mostrar_rec(r)
        with t2:
            for r in rec_dia(qv["recomendaciones"], "fin_de_semana"):
                mostrar_rec(r)
        with t3:
            for r in ([r for r in qv["recomendaciones"] if "dia" not in r]
                      + qv["huecos"] + [qv["cocinas"]]):
                mostrar_rec(r)
        st.markdown("##### 💶 A qué precio")
        for r in rec["a_que_precio"]["recomendaciones"]:
            mostrar_rec(r)
    st.markdown("##### Perfil por horas (≈ personas, estimación)")
    dia_txt = st.segmented_control("Día", list(DIA_ETIQUETA), default="Laborable",
                                   label_visibility="collapsed", key="dia_informe",
                                   help="El perfil no modela el domingo aparte.") \
        or "Laborable"
    dia = DIA_ETIQUETA[dia_txt]
    grafico_perfil(perfil, rec, dia)
    presentes = perfil["horas"].loc[dia][list(COLOR_CLIENTE)].sum()
    leyenda("Clientes", [(S.TIPOS_CLIENTE[t], c) for t, c in COLOR_CLIENTE.items()
                         if presentes[t] > 0], "<span>«punta»: horas punta</span>")
    st.markdown(f"##### Perfil por franjas · {dia_txt.lower()} (≈ personas, estimación)")
    fr = perfil["franjas"].loc[dia].rename(columns={**S.TIPOS_CLIENTE, "total": "Total"})
    fr.index = fr.index.astype(str)
    st.dataframe(fr.round(0), width="stretch")
    conf = perfil["confianza"][["nombre", "confianza_horario", "confianza_cantidad"]]
    with st.expander("Confianza de cada tipo de cliente"):
        st.dataframe(conf.rename(columns={"nombre": "Tipo", "confianza_horario": "Horario",
                                          "confianza_cantidad": "Cantidad"}),
                     hide_index=True, width="stretch")


def pestana_comprobar(rec: dict) -> None:
    lista = rec["comprobar_en_persona"]
    texto_lista = "\n".join(f"{i}. {c}" for i, c in enumerate(lista, 1))
    st.markdown(texto_lista)
    with st.expander("Copiar o descargar la lista"):
        st.code(texto_lista, language=None, wrap_lines=True)
        st.download_button("Descargar la lista (.txt)", texto_lista.encode("utf-8"),
                           file_name="barometro_comprobaciones.txt", mime="text/plain")


def pestana_fuentes(fu: dict) -> None:
    st.markdown(f"**Portal de Datos Abiertos de la Comunidad de Madrid** (descargado el "
                f"{fu['portal_descarga']}):")
    tabla = pd.DataFrame([{
        "Conjunto": f["Conjunto"],
        "Ficha": (re.search(r"\((https?://[^)]+)\)", f["Ficha"]) or [None, None])[1],
        "Licencia": f["Licencia"], "Última modificación": f["Última modificación"]}
        for f in fu["portal"]])
    st.dataframe(tabla, hide_index=True, width="stretch", column_config={
        "Ficha": st.column_config.LinkColumn("Ficha", display_text=r".*/dataset/(.*)")})
    st.markdown("**Otras fuentes:**")
    for e in fu["externas"] + fu["aplicacion"]:
        st.markdown(f"- **{e['titulo']}**  \n"
                    f"  Enlace: {e.get('Enlace', '?')}  \n"
                    f"  Licencia: {e.get('Licencia', '?')}  \n"
                    f"  Datos: {e.get('Versión de los datos', '?')} · descargado el "
                    f"{e.get('Fecha de descarga', '?')}")
    st.markdown(
        "**Powered by [CRTM](https://www.crtm.es)**. Los datos del Consorcio Regional de "
        "Transportes de Madrid (paradas, horarios GTFS y demanda de viajeros) se usan "
        "**procesados**: se calculan a partir de ellos los pasos de vehículos por hora y las "
        "personas por vehículo, no se muestran en bruto.\n\n"
        "Locales, campus y mapa: © [colaboradores de OpenStreetMap]"
        "(https://www.openstreetmap.org/copyright), datos con licencia "
        "[ODbL](https://opendatacommons.org/licenses/odbl/). ¿Ves un error en el mapa? "
        "[Infórmalo a OpenStreetMap](https://www.openstreetmap.org/fixthemap).\n\n"
        + ATRIBUCION_CARTOCIUDAD + ".\n\n"
        "Este proyecto **no está respaldado ni patrocinado por ninguna de las entidades** que "
        "publican los datos (Comunidad de Madrid, Ayuntamiento de Madrid, INE, IGN, CRTM, "
        "Fundación OpenStreetMap ni ninguna otra).")


# =========================================================================== página
cargar_datos()
fu = leer_fuentes()
VISTAS = ["Resumen", "Informe completo"]
AVISO_SENCILLO = ("Esto es una orientación con datos públicos, no una garantía. "
                  "Compruébalo siempre en persona.")


def abrir_informe_en(pestana: str | None) -> None:
    """Las pestañas se vuelven a montar (clave nueva) abiertas por la que se pide."""
    st.session_state["pestana_inicial"] = pestana
    st.session_state["pestanas_n"] = st.session_state.get("pestanas_n", 0) + 1


def ir_a_informe() -> None:
    st.session_state["vista"] = "Informe completo"
    abrir_informe_en("Fuentes y licencias")


# ---------------------------------------------------- cabecera, vistas y buscador
ca = st.columns([3, 1.3], vertical_alignment="bottom")
with ca[0]:
    st.markdown("<div class='marca'><b>BARómetro</b><span>Te ayuda a decidir qué ofrecer en "
                "tu bar o restaurante, según la zona.</span></div>", unsafe_allow_html=True)
with ca[1]:
    st.session_state.setdefault("vista", "Resumen")
    vista = st.segmented_control("Vista", VISTAS, key="vista", on_change=abrir_informe_en,
                                 args=(None,), label_visibility="collapsed",
                                 width="stretch") or "Resumen"
cb = st.columns([2.6, 0.7, 1.45, 1.55, 1.55], gap="small", vertical_alignment="bottom")
with cb[0]:
    texto = st.text_input("Dirección del local", placeholder="Escribe la dirección del local",
                          label_visibility="collapsed", key="texto",
                          on_change=pedir_busqueda)
with cb[1]:
    if st.button("Buscar", type="primary", width="stretch"):
        pedir_busqueda()
for col, (nombre_ej, (la, lo)) in zip(cb[2:], EJEMPLOS.items()):
    with col:
        activo = st.session_state.get("ejemplo") == nombre_ej
        st.button(nombre_ej, width="stretch", type="primary" if activo else "secondary",
                  on_click=elegir_punto, args=(la, lo, nombre_ej))

if st.session_state.pop("buscar", False) and texto.strip():
    try:
        st.session_state["candidatos"] = geocodificar(texto.strip())
    except Exception:
        st.session_state["candidatos"] = None
        st.error("Ahora no podemos buscar direcciones. Prueba más tarde o toca el mapa.")
cand = st.session_state.get("candidatos")
if cand == []:
    st.info("No encontramos esa dirección en Madrid. Prueba a escribirla de otra forma.")
elif cand:
    cc = st.columns([3.2, 1.2], vertical_alignment="bottom")
    with cc[0]:
        i = st.selectbox("Elige tu dirección", range(len(cand)),
                         format_func=lambda k: texto_candidato(cand[k]))
    with cc[1]:
        analizar = st.button("Ver esta dirección", type="primary", width="stretch")
    st.caption("La dirección se envía a CartoCiudad para situarla y no se guarda. "
               + ATRIBUCION_CARTOCIUDAD)
    if analizar:
        try:
            xy = coordenadas(cand[i])
        except Exception:
            xy = None
        if xy and cand[i]["exacto"]:
            elegir_punto(*xy)
            st.session_state.pop("candidatos", None)
            st.rerun()
        elif xy:   # una calle sin número, un municipio…: no se calcula hasta confirmar
            dejar_pendiente(cand[i], *xy)
            st.rerun()
        else:
            st.error("No hemos podido situar esa dirección. Prueba con otra o toca el mapa.")

st.markdown(f"<div class='aviso'>{AVISO_SENCILLO if vista == 'Resumen' else AVISO}</div>",
            unsafe_allow_html=True)

# El resultado del punto actual (perfil, informe, recomendaciones, municipio y locales del
# radio) se calcula una vez y se guarda en la sesión hasta que cambia el punto
# (elegir_punto lo borra). No se guarda en disco ni en ninguna caché compartida.
punto = st.session_state.get("punto")
pendiente = None if punto else st.session_state.get("pendiente")
res = st.session_state.get("resultado") if punto else None
if punto and res is None:
    muni_nuevo = municipio_de(*punto)
    if muni_nuevo is None:
        st.error("Ese punto está fuera de la Comunidad de Madrid. Elige otro.")
    else:
        with st.spinner("Mirando la zona…"), medir("cálculo"):
            t0 = time.perf_counter()
            res = {**calcular(*punto), "muni": muni_nuevo,
                   "locs": locales_del_radio(*punto, muni_nuevo["cod"])}
            st.session_state["resultado"] = res
            st.session_state["segundos"] = time.perf_counter() - t0
muni = res["muni"] if res else None


# ------------------------------------------------------------------- vista Resumen
# Cada parte que cambia sola es un fragmento: al tocarla se vuelve a ejecutar solo ella.
@fragmento("tarjetas")
def parte_tarjetas(rec: dict, inf: dict, atenuadas: bool = False) -> None:
    """Las cuatro tarjetas y, debajo, la explicación de la que esté abierta. Con muy poco
    paso se atenúan: sus respuestas valen poco si casi no pasa nadie."""
    if atenuadas:
        st.markdown("<style>[class*='st-key-tarjeta_'], .st-key-explicacion "
                    "{opacity:0.5;}</style>", unsafe_allow_html=True)
    resp = respuestas(rec, inf)
    tarjetas_resumen(resp)
    abierta = st.session_state.get("abierta")
    if abierta in resp:
        explicacion(abierta, resp, rec, inf)


@fragmento("mapa")
def parte_mapa(lat, lon, locs, alto: int, zoom: int = 16) -> None:
    """El mapa. Un clic elige otro punto y, solo entonces, se recalcula la página."""
    clic = (mapa(lat, lon, locs, alto=alto, zoom=zoom) or {}).get("last_clicked")
    if clic:
        nuevo = (round(clic["lat"], 6), round(clic["lng"], 6))
        if nuevo != st.session_state.get("ultimo_clic"):
            st.session_state["ultimo_clic"] = nuevo
            if nuevo != st.session_state.get("punto"):
                elegir_punto(*nuevo)
                st.rerun()


@fragmento("gráfico")
def parte_grafico(perfil: dict, rec: dict) -> None:
    """Título, selector de día, gráfico por horas y leyenda."""
    dia_txt = st.session_state.get("dia_resumen") or "Día de diario"
    st.markdown("<div class='seccion'>Así se mueve la gente en un "
                f"{dia_txt.lower()}</div>", unsafe_allow_html=True)
    st.segmented_control("Día", list(DIA_RESUMEN), default="Día de diario",
                         label_visibility="collapsed", key="dia_resumen")
    leyenda("", grafico_resumen(perfil, rec, DIA_RESUMEN[dia_txt]))


@fragmento("comprobaciones")
def parte_comprobaciones(rec: dict) -> None:
    lista = comprobaciones_calle(rec)
    todas = st.session_state.get("todas_comprobaciones", False)
    st.markdown("<div class='seccion'>Antes de decidir, compruébalo tú</div>"
                "<div class='lista-grande'>" + "".join(
                    f"<div><b>{n}.</b> {html.escape(c)}</div>"
                    for n, c in enumerate(lista if todas else lista[:3], 1))
                + "</div>", unsafe_allow_html=True)
    if len(lista) > 3:
        st.button("Ver solo las tres primeras" if todas else
                  f"Ver las {len(lista)} comprobaciones", key="ver_comprobaciones",
                  on_click=lambda: st.session_state.update(todas_comprobaciones=not todas))


def vista_resumen(rec: dict, perfil: dict, inf: dict) -> None:
    lugar = st.session_state.get("ejemplo") or "El punto que has elegido"
    mov = res["mov"]
    st.markdown(f"<div class='donde'>📍 {html.escape(lugar)} ({muni['nombre']})</div>"
                + escala_movimiento(mov)
                + f"<div class='titular'>{html.escape(titular_calle(rec, mov))}</div>"
                + (f"<div class='poco-paso'>{html.escape(mov['aviso'])}</div>"
                   if mov["muy_poco_paso"] else ""), unsafe_allow_html=True)
    parte_tarjetas(rec, inf, mov["muy_poco_paso"])

    # ------------------------------------------------------- mapa y gente por horas
    cm, cg = st.columns([1, 1.25], gap="large")
    with cm:
        st.markdown("<div class='seccion'>Los bares y restaurantes que ya hay cerca</div>",
                    unsafe_allow_html=True)
        parte_mapa(*punto, res["locs"], 400)
        leyenda("", [(n, COLOR_TIPO[t]) for t, n in S.TIPOS_COMPETENCIA.items()])
        st.markdown(f"<div class='leyenda'>El círculo marca {S.RADIO_M} metros. Toca el "
                    "mapa para mirar otro sitio.</div>", unsafe_allow_html=True)
    with cg:
        parte_grafico(perfil, rec)

    # ------------------------------------------- cómo se llega y qué hay más lejos
    st.markdown("<div class='seccion'>Cómo se llega y qué hay un poco más lejos</div>"
                "<div class='llegar'>" + "".join(f"<div>{f}</div>" for f in frases_llegar(inf))
                + "</div>", unsafe_allow_html=True)

    # --------------------------------------------------- avisos y comprobaciones
    st.markdown("<div class='seccion'>Ojo con esto</div><div class='lista-grande'>"
                + "".join(f"<div>{html.escape(a)}</div>" for a in avisos_calle(rec, inf))
                + "</div>", unsafe_allow_html=True)
    parte_comprobaciones(rec)


# ------------------------------------------------------------ vista Informe completo
PESTANAS = ["Detalle de las recomendaciones", "Mercado", "Riesgos y avisos",
            "Qué comprobar en persona", "Fuentes y licencias"]


@fragmento("informe")
def parte_informe(rec: dict, perfil: dict, inf: dict) -> None:
    """Las pestañas del informe. Cambiar de pestaña no va al servidor: lo hace el
    navegador. Cambiar de día en el detalle vuelve a ejecutar solo esta parte."""
    tabs = st.tabs(PESTANAS, key=f"pestanas_{st.session_state.get('pestanas_n', 0)}",
                   default=st.session_state.get("pestana_inicial"))
    with tabs[0]:
        pestana_detalle(rec, perfil)
    with tabs[1]:
        bloques = inf["bloques"]
        for fila in range(0, len(bloques), 2):
            for col, b in zip(st.columns(2, gap="medium"), bloques[fila:fila + 2]):
                with col:
                    bloque_mercado(b)
    with tabs[2]:
        pestana_riesgos(rec, inf)
    with tabs[3]:
        pestana_comprobar(rec)
    with tabs[4]:
        pestana_fuentes(fu)


def vista_informe(rec: dict, perfil: dict, inf: dict) -> None:
    lugar = st.session_state.get("ejemplo") or "Punto elegido"
    st.markdown(f"<div class='donde'>📍 {html.escape(lugar)} · {muni['nombre']} · radio de "
                f"{S.RADIO_M} m · calculado en {dec(st.session_state['segundos'])} s</div>",
                unsafe_allow_html=True)
    mov = res["mov"]
    st.markdown(
        f"**Nivel de movimiento: {mov['nombre']}** (nivel {mov['nivel']} de 5) "
        "<span class='etiqueta'>Estimación</span><br>"
        f"≈{redondo(mov['pasos_laborable'])} personas pasan cerca en un día laborable; "
        f"{html.escape(mov['frase'])} (por encima del {100 * mov['posicion']:.0f} % de "
        f"{miles(mov['sitios_referencia'])} sitios de referencia, cuya mediana es "
        f"≈{redondo(mov['mediana_referencia'])})."
        + (f"<br>⚠️ {html.escape(mov['aviso'])}" if mov["muy_poco_paso"] else ""),
        unsafe_allow_html=True)
    st.caption(
        f"{mov['nota']} Por qué {S.RADIO_M} metros: es lo que se anda en unos 4 minutos, la "
        "distancia a la que alguien se desvía para tomar algo de paso; por eso el perfil y "
        f"las recomendaciones solo miran ese círculo. El transporte se mira además a "
        f"{S.ACCESOS_RADIO_LEJOS_M} m y el entorno a {S.ENTORNO_RADIO_M // 1000} km, solo "
        "como contexto (pestaña Mercado).")
    parte_informe(rec, perfil, inf)


# Solo se construye la vista que se está viendo.
if res and vista == "Resumen":
    vista_resumen(res["rec"], res["perfil"], res["informe"])
elif res:
    vista_informe(res["rec"], res["perfil"], res["informe"])
elif pendiente:
    # Dirección que no es un portal: no se calcula nada hasta que se confirma el sitio.
    st.markdown(
        f"<div class='confirma'>¿Es aquí? Si no, toca el mapa en el sitio exacto.</div>"
        f"<div class='confirma-pie'>«{html.escape(pendiente['texto'])}» "
        f"{QUE_ES[pendiente['precision']]}. Hemos puesto el punto en un sitio cualquiera de "
        "esa zona y todavía no hemos calculado nada. También puedes escribir la dirección "
        "con el número del portal.</div>", unsafe_allow_html=True)
    st.button("Sí, es aquí", type="primary", key="confirmar", on_click=confirmar_pendiente)
    parte_mapa(pendiente["lat"], pendiente["lon"], None, 460,
               ZOOM_PENDIENTE[pendiente["precision"]])
elif vista == "Resumen":
    st.info("Escribe la dirección de tu local, prueba un ejemplo o toca el mapa.")
    parte_mapa(None, None, None, 460)
else:
    st.info("Elige primero un sitio en la vista Resumen. Aquí debajo tienes las fuentes.")
    pestana_fuentes(fu)

# --------------------------------------------------------------------- pie
st.markdown(
    "<div class='pie'>"
    "Powered by <a href='https://www.crtm.es'>CRTM</a> · "
    "© <a href='https://www.openstreetmap.org/copyright'>colaboradores de OpenStreetMap</a>"
    " · Direcciones: CartoCiudad, IGN · CC BY 4.0 "
    "<a href='https://www.scne.es/productos.html#CartoCiudad'>"
    "www.scne.es/productos.html#CartoCiudad</a> · "
    f"Datos descargados el {fu['portal_descarga']} · "
    "Sin respaldo de las entidades que publican los datos · "
    "BARómetro, prototipo para DATAMAD 2026"
    "</div>", unsafe_allow_html=True)
st.button("Fuentes y licencias", key="ir_fuentes", type="tertiary", on_click=ir_a_informe)
st.session_state["_en_pagina"] = False
anotar_medidas("página", _T_PAGINA)
