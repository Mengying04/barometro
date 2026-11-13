"""BARómetro: aplicación web (Streamlit).

Muestra, para un punto de la Comunidad de Madrid, el perfil por horas, el informe del local
y las recomendaciones. No repite cálculos: solo llama a perfil_horario(), informe_local() y
recomendar() (src/), a nivel_movimiento() para situar el punto frente al resto de la
Comunidad, y a dos consultas de informe_local para saber en qué municipio cae el punto y
qué locales del radio se dibujan en el mapa.

Pantallas:
  - Portada (sin punto elegido): fondo oscuro, el logotipo, el nombre, una frase y un
    buscador grande con sugerencias mientras se escribe; debajo, los tres ejemplos, «Usar mi
    ubicación» y tres cifras calculadas de los datos. Más abajo, «Cómo funciona» y «Fuentes
    y licencias».
  - Resultado, sobre fondo claro y con una barra superior fija (logotipo, un campo con la
    dirección analizada que se edita directamente para buscar otra, y el cambio de vista):
      · «Resumen» (por defecto), para un hostelero sin conocimientos técnicos: el nivel de
        movimiento con su aguja, un titular, cuatro tarjetas con pregunta y respuesta, el
        mapa, la gente por horas, cómo se llega, avisos y comprobaciones;
      · «Informe completo», en una sola columna y con índice: una sección por pregunta con
        la misma estructura (respuesta, fiabilidad, porqué y detalle desplegable), el perfil
        por horas, mercado, riesgos, comprobaciones y fuentes.
Ninguna de las dos vistas calcula nada: traducen lo que devuelven recomendar() e
informe_local(), con las palabras de src/calle.py.

Desde el resultado se puede además:
  - «Comparar con otra dirección»: se elige una segunda dirección con el mismo buscador y
    las mismas reglas y se enseña la comparación (src/comparar.py) lado a lado en portátil
    y apilada en móvil, con las dos curvas por horas y un resumen final sin ganador;
  - «Descargar informe»: un PDF (src/documento.py) del local o de la comparación, que se
    genera en memoria al pulsar el botón y no se guarda en el servidor.

Rejilla (app/estilo.css): un solo ancho máximo de contenido y un margen lateral simétrico
para todas las vistas; la barra, el índice, el contenido y el pie comparten bordes. En el
Informe completo cada sección tiene una columna de lectura (texto, listas y desplegables del
mismo ancho) y, al lado, un recuadro de apoyo (clase «seccion»). El pie es el mismo en todas
las vistas. Los avisos («Ojo con esto» y «Riesgos y avisos») son los de recomendar(), tal cual.

Ficheros de la interfaz (en app/): estilo.css (sistema visual), buscador.js (componente del
buscador y de la barra, montado con st.components.v2, sin iframe) y logo.svg.

Arranque (desde la raíz del repositorio):
    streamlit run app/app.py --server.address 0.0.0.0 --server.port 8501

Buscador: al elegir una sugerencia que es un portal con número se calcula directamente. Una
dirección que no es un portal concreto (una calle sin número, un municipio…) no se calcula:
se enseña en el mapa y se pregunta «¿Es aquí?»; solo se calcula al confirmar o al tocar el
mapa.

Privacidad: lo que se escribe en el buscador se envía a CartoCiudad para sugerir
direcciones. Ni eso, ni la dirección elegida, ni la ubicación del navegador (que solo se
pide si el usuario pulsa «Usar mi ubicación» y la acepta) se guardan: solo viven en la
memoria de la sesión, igual que la segunda dirección de una comparación; no se escriben en ficheros, registros ni en la URL. Las estadísticas
de uso de Streamlit están desactivadas en .streamlit/config.toml.
"""

from __future__ import annotations

import functools
import html
import math
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
import tablas_readme  # noqa: E402
from comparar import comparar  # noqa: E402
from direcciones import (ATRIBUCION_CARTOCIUDAD, coordenadas,  # noqa: E402
                         geocodificar)
from documento import comparacion_pdf, informe_pdf  # noqa: E402
from movimiento import nivel_movimiento, referencia  # noqa: E402
from calle import (CLIENTE_CALLE, COLOR_TIPO, ENTORNO_CALLE, FIABILIDAD,  # noqa: E402
                   MODO_CALLE, MOMENTO_CALLE, bloque_inf, comprobaciones_calle, dec,
                   frases_cuando, frases_precio, frases_que, frases_quien, grupos_horas,
                   hora_de_grupo, horas_punta, lista_y, mayus, metrica_bloque, miles,
                   rec_dia, redondo, respuestas, titular_calle, unas)
from procesar import PROC  # noqa: E402
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
# Tipos de local: cuatro colores bien separados también con daltonismo (comprobados por pares
# con el validador de paletas: diferencia mínima 9,3 en deuteranopia y 8,6 en tritanopia) y,
# además, una forma distinta por tipo. Los mismos en el mapa, la leyenda y el informe.
FORMA_TIPO = {  # en una rejilla de 16: círculo, cuadrado, triángulo y rombo
    "bar": "<circle cx='8' cy='8' r='6'/>",
    "restaurante": "<rect x='2.4' y='2.4' width='11.2' height='11.2' rx='1.6'/>",
    "cafeteria": "<path d='M8 1.6L14.8 13.8H1.2z'/>",
    "comida_rapida": "<path d='M8 0.9L15.1 8L8 15.1L0.9 8z'/>"}
# Transporte: un icono discreto por modo, en gris oscuro (no compite con los locales). Son
# dibujos propios (una letra o un autobús en una ficha), no los logotipos de las redes.
TINTA_MODO = "#3b342c"
MODO_ICONO = {"metro": "Metro", "cercanias": "Cercanías", "metro_ligero": "Metro Ligero",
              "emt": "Autobús", "urbanos": "Autobús", "interurbanos": "Autobús"}
LETRA_MODO = {"Metro": "M", "Cercanías": "C", "Metro Ligero": "ML"}


def marca_tipo(tipo: str, px: int = 16) -> str:
    """La marca de un tipo de local (forma y color), como SVG suelto: vale para el mapa
    (que va en un marco aparte, sin la hoja de estilos) y para las leyendas."""
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{px}' height='{px}' "
            f"viewBox='0 0 16 16' fill='{COLOR_TIPO.get(tipo, '#999999')}' stroke='#ffffff' "
            f"stroke-width='1.4' stroke-linejoin='round'>"
            f"{FORMA_TIPO.get(tipo, FORMA_TIPO['bar'])}</svg>")


def icono_modo(modo: str, px: int = 18) -> str:
    """La ficha de un modo de transporte: M, C o ML, o un autobús."""
    letra = LETRA_MODO.get(modo)
    dentro = (f"<text x='10' y='13.6' text-anchor='middle' font-family='Arial, Helvetica, "
              f"sans-serif' font-weight='700' font-size='{8 if len(letra) > 1 else 10.5}' "
              f"fill='{TINTA_MODO}' stroke='none'>{letra}</text>" if letra else
              "<rect x='5.6' y='4.6' width='8.8' height='9' rx='2' fill='none'/>"
              "<path d='M5.6 9.6h8.8M7.6 13.6v1.6M12.4 13.6v1.6' fill='none'/>")
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{px}' height='{px}' "
            f"viewBox='0 0 20 20' stroke='{TINTA_MODO}' stroke-width='1.5' "
            "stroke-linecap='round' stroke-linejoin='round'>"
            f"<rect x='1.2' y='1.2' width='17.6' height='17.6' rx='5' fill='#ffffff'/>"
            f"{dentro}</svg>")


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

AQUI = Path(__file__).resolve().parent
REPOSITORIO = "https://github.com/Mengying04/barometro"
MIN_LETRAS = 4      # letras mínimas para pedir sugerencias a CartoCiudad
MAX_SUGERENCIAS = 6

st.set_page_config(page_title="BARómetro", page_icon=str(AQUI / "logo.svg"), layout="wide",
                   initial_sidebar_state="collapsed")

# ------------------------------------------------------------------- sistema visual
TEJA, TEJA_SUAVE = PRINCIPAL, "#d6a585"
TINTA, SUAVE, TENUE, BORDE = "#1f1b16", "#5c5248", "#8a7f73", "#e8dfd3"
# Aguja del nivel de movimiento: un solo tono, de claro a oscuro (más paso, más intenso).
RAMPA_NIVEL = ["#ecd9c9", "#e3b697", "#d48b5f", "#bb5d31", "#9c3d1b"]
# Iconos propios, todos del mismo estilo: trazo de 2 px, sin relleno, en una rejilla de 24.
ICONOS = {
    "personas": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.6 2.9-6.5 6.5-6.5s6.5 2.9 6.5 6.5"/><circle cx="17.5" cy="9" r="2.5"/><path d="M17 14.5c2.6.3 4.5 2.5 4.5 5.5"/>',
    "reloj": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
    "taza": '<path d="M4 9h13v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z"/><path d="M17 10h1.5a2.5 2.5 0 0 1 0 5H17"/><path d="M8 3v3M12 3v3"/>',
    "euro": '<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5a4.5 4.5 0 1 0 0 7M7 11h6M7 13.5h5"/>',
    "pin": '<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
    "aviso": '<path d="M12 4l9 16H3z"/><path d="M12 10v4.5M12 17.4v.1"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.5v.1"/>',
    "bus": '<rect x="5" y="3.5" width="14" height="14" rx="3"/><path d="M5 11h14M8.5 17.5V20M15.5 17.5V20M8.5 14.3v.1M15.5 14.3v.1"/>',
    "casa": '<path d="M4 11l8-7 8 7v8.5H4z"/><path d="M10 19.5v-5h4v5"/>',
    "birrete": '<path d="M2.5 9.5L12 5l9.5 4.5L12 14z"/><path d="M6.5 11.8V16c0 1.2 2.5 2.5 5.5 2.5s5.5-1.3 5.5-2.5v-4.2M21.5 9.5V15"/>',
    "tienda": '<path d="M4 10v9.5h16V10"/><path d="M3 10l1.5-5.5h15L21 10a3 3 0 0 1-6 0 3 3 0 0 1-6 0 3 3 0 0 1-6 0z"/>',
    "mapa": '<path d="M3.5 6.5l5.5-2 6 2 5.5-2v13l-5.5 2-6-2-5.5 2z"/><path d="M9 4.5v13M15 6.5v13"/>',
    "duda": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.6 2.2c-.7.4-1.1 1-1.1 1.8M12 16.8v.1"/>',
    "calendario": '<rect x="4" y="5.5" width="16" height="14.5" rx="2.5"/><path d="M4 10h16M8.5 3.5v4M15.5 3.5v4"/>',
    "ok": '<circle cx="12" cy="12" r="9"/><path d="M8 12.3l2.7 2.7L16 9.5"/>',
    "lista": '<path d="M10 6.5h10M10 12h10M10 17.5h10M4 6.5l1 1 1.8-2M4 12l1 1 1.8-2M4 17.5l1 1 1.8-2"/>',
    "grafico": '<path d="M5 20v-9M10 20V5M15 20v-7M20 20V8"/>',
    "aguja": '<path d="M4 16a8 8 0 0 1 16 0"/><path d="M12 16l4-6"/>',
    "libro": '<path d="M5 4.5h11a3 3 0 0 1 3 3V20H8a3 3 0 0 1-3-3z"/><path d="M5 17a3 3 0 0 1 3-3h11"/>',
    "cesta": '<path d="M4 9h16l-1.5 10h-13z"/><path d="M8.5 9l3.5-5 3.5 5"/>',
}


def ico(nombre: str) -> str:
    return f"<span class='ico'><svg viewBox='0 0 24 24'>{ICONOS[nombre]}</svg></span>"


@st.cache_resource
def fichero_interfaz(nombre: str) -> str:
    """Texto de un fichero de app/ (se lee una vez por proceso)."""
    return (AQUI / nombre).read_text(encoding="utf-8")


@st.cache_resource
def hoja_de_estilos() -> str:
    """El CSS de la página, sin comentarios ni espacios de sobra (se prepara una vez)."""
    css = re.sub(r"/\*.*?\*/", "", fichero_interfaz("estilo.css"), flags=re.S)
    return "<style>" + re.sub(r"\s+", " ", css).strip() + "</style>"


def logo_svg() -> str:
    return re.sub(r"\s+", " ", fichero_interfaz("logo.svg")).strip()


def aguja_svg(nivel: int | None) -> str:
    """El indicador de marca: un barómetro de cinco tramos con su aguja. Solo dibuja el
    nivel (1 a 5) que da nivel_movimiento(); la aguja apunta al centro de su tramo."""
    arcos = []
    for i in range(5):
        a0, a1 = math.radians(180 - 36 * i - 1.6), math.radians(180 - 36 * (i + 1) + 1.6)
        color = RAMPA_NIVEL[i] if nivel is None or i < nivel else "#eee7dd"
        arcos.append(f"<path d='M{100 + 80 * math.cos(a0):.1f} {100 - 80 * math.sin(a0):.1f}"
                     f"A80 80 0 0 1 {100 + 80 * math.cos(a1):.1f} "
                     f"{100 - 80 * math.sin(a1):.1f}' stroke='{color}'/>")
    giro = 36 * (nivel - 0.5) if nivel else 90
    return ("<svg viewBox='0 0 200 112' aria-hidden='true'>"
            f"<g fill='none' stroke-width='20'>{''.join(arcos)}</g>"
            f"<g class='aguja-g' style='--giro:{giro:.0f}deg'>"
            f"<path d='M100 94.5L100 105.5L34 100z' fill='{TINTA}'/></g>"
            f"<circle cx='100' cy='100' r='10' fill='{TINTA}'/>"
            "<circle cx='100' cy='100' r='3.5' fill='#fff'/></svg>")


st.session_state["_en_pagina"] = True
st.markdown(hoja_de_estilos(), unsafe_allow_html=True)

# El buscador y la barra: un componente propio, sin iframe (hereda la letra y los estilos).
BUSCADOR = st.components.v2.component("barometro_buscador", js=fichero_interfaz("buscador.js"),
                                      isolate_styles=False)


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


def paradas_del_radio(lat: float, lon: float) -> pd.DataFrame:
    """Posición y modo de las paradas con servicio del radio (la misma capa que usan el
    perfil y el bloque «accesos»); sin nombres. En Metro y Metro Ligero, cada acceso de la
    estación que cae dentro del círculo. Solo sirve para dibujarlas en el mapa."""
    x, y = I._A_UTM.transform(lon, lat)
    punto = shapely.Point(x, y)
    par = I.en_radio(I.transporte()[0], punto, S.RADIO_M)[["red", "geometry"]]
    par = par.explode(index_parts=False)
    par = par[par.distance(punto) <= S.RADIO_M]
    lons, lats = I._A_UTM.transform(par.geometry.x.to_numpy(), par.geometry.y.to_numpy(),
                                    direction="INVERSE")
    return pd.DataFrame({"lat": lats, "lon": lons, "modo": par["red"].map(MODO_ICONO).to_numpy()}
                        ).drop_duplicates().reset_index(drop=True)


def calcular(lat: float, lon: float) -> dict:
    perfil = P.perfil_horario(lat, lon)
    inf = I.informe_local(lat, lon, perfil=perfil)
    rec = recomendar(lat, lon, perfil=perfil, inf=inf)
    return {"perfil": perfil, "informe": inf, "rec": rec, "mov": nivel_movimiento(perfil)}


# ------------------------------------------------------------------- fuentes.md
# El buscador de direcciones (src/direcciones.py) y el lector de docs/fuentes.md
# (src/fuentes.py) se comparten con el servidor MCP.
leer_fuentes = st.cache_data(fuentes.leer_fuentes)


@st.cache_data
def cifras_portada() -> dict:
    """Las tres cifras de la portada, calculadas (no escritas a mano):
    - conjuntos del portal de la Comunidad de Madrid anotados en docs/fuentes.md que la
      aplicación usa (los que tienen un uso declarado en src/tablas_readme.py);
    - zonas analizadas: secciones censales de los datos procesados;
    - municipios cubiertos: municipios distintos de esas secciones."""
    ids = {m.group(1) for f in leer_fuentes()["portal"]
           if (m := re.search(r"\[([^\]]+)\]", f["Ficha"]))}
    secc = pd.read_parquet(PROC / "secciones_censales.parquet",
                           columns=["cdgseccion", "cod_municipio"])
    return {"conjuntos": len(ids & set(tablas_readme.USO)),
            "zonas": int(secc["cdgseccion"].nunique()),
            "municipios": int(secc["cod_municipio"].nunique())}


# ------------------------------------------------------------------- formato


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


# ------------------------------------------- lecturas de recomendar() (sin cálculos)


# ------------------------------------------------- vista Resumen: palabras de la calle
COLOR_OTROS = "#b8b0a4"
DIA_RESUMEN = {"Día de diario": "laborable", "Sábado": "fin_de_semana"}


def fiabilidad(r: dict) -> str:
    n, texto = FIABILIDAD.get(r.get("confianza"), FIABILIDAD["baja"])
    puntos = "".join(f"<i class='{'si' if i < n else ''}'></i>" for i in range(3))
    return f"<div class='fiable'>{puntos}<span>{texto}</span></div>"


def alternar(clave: str | None) -> None:
    """Abre la explicación de una tarjeta (solo una a la vez) o la cierra."""
    st.session_state["abierta"] = (None if st.session_state.get("abierta") == clave
                                   else clave)


ICONO_PREGUNTA = {"quien": "personas", "cuando": "reloj", "que": "taza", "precio": "euro"}


def tarjetas_resumen(resp: dict) -> None:
    abierta = st.session_state.get("abierta")
    if abierta:   # la tarjeta abierta se marca con el color de acento
        st.markdown(f"<style>.st-key-tarjeta_{abierta} {{outline:2px solid {TEJA};}}</style>",
                    unsafe_allow_html=True)
    for col, (clave, t) in zip(st.columns(4), resp.items()):
        with col, st.container(border=True, key=f"tarjeta_{clave}"):
            st.markdown(
                f"<div class='pregunta'>{ico(ICONO_PREGUNTA[clave])}{t['pregunta']}</div>"
                f"<div class='respuesta'>{html.escape(t['respuesta'])}</div>"
                f"<div class='apoyo'>{html.escape(t['apoyo'])}</div>"
                + fiabilidad(t["rec"])
                + f"<div class='ver'>{'Cerrar ▴' if abierta == clave else 'Ver por qué ▾'}"
                  "</div>", unsafe_allow_html=True)
            st.button(f"Ver por qué: {t['pregunta']}", key=f"abrir_{clave}",
                      on_click=alternar, args=(clave,))


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


def cifra_cuando(rec: dict) -> None:
    punta = rec["a_que_hora"]["detalle"]["laborable"]["horas_punta"]
    if punta:
        mejor = max(punta, key=lambda h: h["total"])
        st.markdown(f"<div class='cifra'>Unas {unas(mejor['total'])} personas</div>"
                    f"<div class='cifra-pie'>pasan cerca a las {int(mejor['hora'][:2])}, la "
                    "mejor hora de un día de diario.</div>", unsafe_allow_html=True)


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


def barras_que_mini(rec: dict) -> None:
    """Lo mismo que barras_que(), para una columna estrecha: una barra fina por momento, con
    su nombre y su cifra encima. El largo de cada barra es su parte del momento mayor."""
    mo = sorted(((m, n) for m, n in rec["que_vender"]["momentos"]["laborable"].items()
                 if n > 0), key=lambda kv: -kv[1])[:5]
    if not mo:
        return
    tope = mo[0][1]
    st.markdown(
        "<div class='lado-t'>Posibles clientes en un día de diario</div><div class='mini'>"
        + "".join(f"<div><span>{html.escape(mayus(MOMENTO_CALLE[m]))}</span>"
                  f"<span>unos {unas(n)}</span><i style='width:{100 * n / tope:.0f}%'></i></div>"
                  for m, n in mo) + "</div>", unsafe_allow_html=True)


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


def avisos_calle(rec: dict) -> list[tuple[str, str]]:
    """Los avisos del sitio (icono y frase), tal como los da recomendar(): ya vienen
    ordenados por importancia, como mucho tres, cada uno con la cifra de este punto; si no
    hay ninguno, una sola frase en positivo."""
    return [(ICONO_RIESGO.get(r["clave"], "aviso"), r["texto"]) for r in rec["riesgos"]]


def eje_horas(cada: int, con_h: bool) -> alt.X:
    """Eje de horas legible en un móvil: una etiqueta cada «cada» horas, en horizontal."""
    return alt.X("hora:O", title=None, scale=alt.Scale(paddingInner=0.22),
                 axis=alt.Axis(values=list(range(0, 24, cada)), labelAngle=0, labelFontSize=13,
                               labelExpr="datum.value + ' h'" if con_h else "datum.value",
                               labelColor=SUAVE, labelPadding=8, ticks=False,
                               domainColor=BORDE))


def eje_personas() -> alt.Y:
    return alt.Y("personas:Q", title=None,
                 axis=alt.Axis(labelExpr="replace(format(datum.value, ',.0f'), ',', '.')",
                               labelFontSize=12, labelColor=TENUE, gridColor="#f0e9df",
                               tickCount=4, domain=False, ticks=False))


def grafico_resumen(perfil: dict, rec: dict, dia: str) -> list[tuple[str, str]]:
    """Gente por horas, de un vistazo: una barra por hora con el total y las horas punta
    (las de recomendar()) en el color de acento. Devuelve las entradas de la leyenda."""
    horas = perfil["horas"].loc[dia]
    punta = set(horas_punta(rec, dia))
    tipos = horas[list(COLOR_CLIENTE)]
    grupos = ["Horas con más gente", "Resto del día"]
    datos = pd.DataFrame({"hora": list(horas.index),
                          "personas": horas["total"].astype(float).to_numpy()})
    datos["grupo"] = [grupos[0] if h in punta else grupos[1] for h in datos["hora"]]
    datos["txt"] = [f"unas {unas(n)}" if n >= 1 else "casi nadie" for n in datos["personas"]]
    datos["quien"] = [mayus(CLIENTE_CALLE[tipos.loc[h].idxmax()]) if n >= 1 else "—"
                      for h, n in zip(datos["hora"], datos["personas"])]
    datos["cuando"] = [f"{h} h" for h in datos["hora"]]
    barras = alt.Chart(datos).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=eje_horas(3, True), y=eje_personas(),
        color=alt.Color("grupo:N", legend=None,
                        scale=alt.Scale(domain=grupos, range=[TEJA, TEJA_SUAVE])),
        tooltip=[alt.Tooltip("cuando:N", title="Hora"),
                 alt.Tooltip("txt:N", title="Personas"),
                 alt.Tooltip("quien:N", title="Sobre todo")])
    capas = barras
    mejores = [hora_de_grupo(rec, dia, g) for g in grupos_horas(rec, dia)[:2]]
    if mejores:
        marca = pd.DataFrame([{"hora": h, "personas": float(horas["total"].loc[h]),
                               "txt": f"{h} h"} for h in mejores])
        capas = barras + alt.Chart(marca).mark_text(
            dy=-9, fontSize=14, fontWeight=700, color=TINTA).encode(
            x="hora:O", y="personas:Q", text="txt:N")
    st.altair_chart(capas.properties(height=300, padding={"top": 14, "left": 2, "right": 6,
                                                          "bottom": 2})
                    .configure_view(strokeWidth=0), width="stretch")
    return [(grupos[0], TEJA), (grupos[1], TEJA_SUAVE)]


def indicador_movimiento(mov: dict) -> str:
    """La aguja del nivel de movimiento, con los nombres de los dos extremos."""
    return (f"<div class='ver-aguja' role='img' aria-label='Nivel {mov['nivel']} de 5: "
            f"{html.escape(mov['nombre'])}'>{aguja_svg(mov['nivel'])}"
            f"<div class='ver-extremos'><span>{html.escape(mov['niveles'][0])}</span>"
            f"<span>{html.escape(mov['niveles'][-1])}</span></div></div>")


def veredicto(lugar: str, mov: dict, titular: str) -> str:
    """El bloque de marca del resultado: aguja, nivel en grande, comparación y titular."""
    return ("<div class='veredicto'>" + indicador_movimiento(mov)
            + f"<div><div class='donde'>{ico('pin')}{html.escape(lugar)}</div>"
            "<div class='ver-etq'>Movimiento de la zona <span class='etiqueta'>Estimación"
            "</span></div>"
            f"<div class='ver-nivel n{mov['nivel']}'>{html.escape(mov['nombre'])}</div>"
            f"<div class='ver-frase'>Por aquí {html.escape(mov['frase'])}.</div></div>"
            f"<div class='titular'>{html.escape(titular)}</div></div>")


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


ORDEN_MODOS = ("Metro", "Cercanías", "Metro Ligero")
MAX_LINEAS_VISTAS = 4


def linea_llegar(inf: dict) -> str:
    """Cómo se llega, de un vistazo: una línea por modo con su icono, sus líneas principales
    y la distancia a la parada más cercana, y el número de líneas de autobús. Solo enseña lo
    que ya trae el bloque «accesos» del informe (a menos de ACCESOS_RADIO_LEJOS_M metros)."""
    lejos = bloque_inf(inf, "accesos")["datos"]["lejos"]
    filas = []
    for modo in ORDEN_MODOS:
        v = lejos.get(modo)
        if not v:
            continue
        n = v["nombres_lineas"]
        lineas = "".join(f"<span class='linea'>{html.escape(x)}</span>"
                         for x in n[:MAX_LINEAS_VISTAS])
        if len(n) > MAX_LINEAS_VISTAS:
            lineas += f"<span class='linea'>+{len(n) - MAX_LINEAS_VISTAS}</span>"
        filas.append(f"<div>{icono_modo(modo, 22)}<span class='m-nombre'>{modo}</span>"
                     f"{lineas}<span class='lejos'>a {miles(v['distancia_m'])} m</span></div>")
    buses = [v for m, v in lejos.items() if m not in ORDEN_MODOS]
    if buses:
        n = sum(v["lineas"] for v in buses)
        filas.append(f"<div>{icono_modo('Autobús', 22)}<span class='m-nombre'>Autobús</span>"
                     f"<span>{n} {'línea' if n == 1 else 'líneas'}</span><span class='lejos'>"
                     f"a {miles(min(v['distancia_m'] for v in buses))} m</span></div>")
    if not filas:
        return ""
    return ("<div class='modos'>" + "".join(filas) + "</div><div class='modos-pie'>Paradas a "
            f"menos de {S.ACCESOS_RADIO_LEJOS_M} m (unos {S.ACCESOS_MINUTOS_LEJOS} minutos "
            "andando) y distancia a la más cercana. El detalle está en el Informe completo."
            "</div>")


# ------------------------------------------------------------------ mapa y gráfico
def marcador(lat: float, lon: float, svg: str, px: int) -> folium.Marker:
    """Una marca del mapa (un SVG propio), sin ventana, sin nombre y sin atrapar los clics."""
    return folium.Marker((lat, lon), interactive=False, keyboard=False,
                         icon=folium.DivIcon(html=svg, icon_size=(px, px),
                                             icon_anchor=(px // 2, px // 2), class_name="bm-m"))


def construir_mapa(lat, lon, locs: pd.DataFrame | None, zoom: int = 16,
                   paradas: pd.DataFrame | None = None) -> folium.Map:
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
        if paradas is not None:   # debajo de los locales: fichas discretas, sin nombres
            for f in paradas.itertuples():
                px = 13 if f.modo == "Autobús" else 18
                marcador(f.lat, f.lon, icono_modo(f.modo, px), px).add_to(m)
        if locs is not None:
            for f in locs.itertuples():   # sin ventanas ni nombres: el tipo, por color y forma
                marcador(f.lat, f.lon, marca_tipo(f.tipo, 16), 16).add_to(m)
        folium.CircleMarker((lat, lon), radius=9, weight=3, color="#ffffff",
                            fill=True, fill_color=PRINCIPAL, fill_opacity=1,
                            interactive=False).add_to(m)
    return m


def mapa(lat, lon, locs: pd.DataFrame | None, alto: int = 400,
         zoom: int = 16, paradas: pd.DataFrame | None = None) -> dict | None:
    """Dibuja el mapa. El objeto del mapa se construye una sola vez por punto y se guarda
    en la sesión. Solo vuelve al servidor el último clic: mover el mapa o hacer zoom no
    provoca ninguna recarga."""
    guardado = st.session_state.get("mapa_obj")
    clave = (lat, lon, zoom, locs is None)
    if not guardado or guardado[0] != clave:
        guardado = (clave, construir_mapa(lat, lon, locs, zoom, paradas))
        st.session_state["mapa_obj"] = guardado
    return st_folium(guardado[1], height=alto, use_container_width=True,
                     returned_objects=["last_clicked"], key="mapa")


def leyenda(titulo: str, items: list[tuple[str, str]], extra: str = "") -> None:
    st.markdown(
        f"<div class='leyenda'><b>{titulo}</b>" + "".join(
            f"<span><i class='punto' style='background:{c}'></i>{n}</span>"
            for n, c in items) + extra + "</div>", unsafe_allow_html=True)


def leyenda_mapa(paradas: pd.DataFrame | None = None, cuenta: dict | None = None) -> str:
    """Leyenda de los locales (los cuatro tipos, con su forma y su color) y, si se dan, de las
    paradas del mapa. Con «cuenta», cada tipo lleva su número (informe)."""
    out = f"<div class='leyenda rejilla{' cuenta' if cuenta else ''}'>" + "".join(
        f"<span>{marca_tipo(t)}{n}" + (f"<b>{miles(cuenta[t])}</b>" if cuenta else "")
        + "</span>" for t, n in S.TIPOS_COMPETENCIA.items()) + "</div>"
    modos = [m for m in (*ORDEN_MODOS, "Autobús")
             if paradas is not None and (paradas["modo"] == m).any()]
    if modos:
        out += "<div class='leyenda rejilla modos-ley'>" + "".join(
            f"<span>{icono_modo(m, 18)}{m}</span>" for m in modos) + "</div>"
    return out


def grafico_perfil(perfil: dict, rec: dict, dia: str) -> None:
    orden = list(COLOR_CLIENTE)
    h = perfil["horas"].loc[dia][orden].reset_index()
    largo = h.melt(id_vars="hora", var_name="tipo", value_name="personas")
    largo["cliente"] = largo["tipo"].map(S.TIPOS_CLIENTE)
    largo["orden"] = largo["tipo"].map({t: i for i, t in enumerate(orden)})
    barras = alt.Chart(largo).mark_bar(stroke="#ffffff", strokeWidth=1).encode(
        x=eje_horas(2, False), y=eje_personas(),
        color=alt.Color("cliente:N", legend=None,
                        scale=alt.Scale(domain=[S.TIPOS_CLIENTE[t] for t in orden],
                                        range=[COLOR_CLIENTE[t] for t in orden])),
        order=alt.Order("orden:Q", sort="ascending"),
        tooltip=[alt.Tooltip("hora:O", title="Hora"), alt.Tooltip("cliente:N", title="Cliente"),
                 alt.Tooltip("personas:Q", title="Personas (≈)", format=",.0f")],
    )
    tot = perfil["horas"].loc[dia]["total"]
    punta = pd.DataFrame([{"hora": hh, "personas": float(tot.loc[hh]), "txt": "punta"}
                          for hh in horas_punta(rec, dia)])
    marcas = alt.Chart(punta).mark_text(dy=-9, fontSize=12, fontWeight=700,
                                        color=TINTA).encode(
        x="hora:O", y="personas:Q", text="txt:N")
    st.altair_chart((barras + marcas).properties(
        height=330, padding={"top": 14, "left": 2, "right": 6, "bottom": 2})
        .configure_view(strokeWidth=0), width="stretch")


def elegir_punto(lat: float, lon: float, ejemplo: str | None = None,
                 lugar: str | None = None) -> None:
    """Fija el punto que se va a analizar. «lugar» es el texto que se enseña (la dirección
    elegida, «Tu ubicación»…): solo vive en la sesión."""
    st.session_state["punto"] = (round(lat, 6), round(lon, 6))
    st.session_state["ejemplo"] = ejemplo
    st.session_state["lugar"] = lugar
    st.session_state.pop("resultado", None)
    st.session_state["abierta"] = None
    st.session_state["todas_comprobaciones"] = False
    st.session_state.pop("pendiente", None)
    quitar_comparacion()
    buscador_nuevo()


# ------------------------------------------------------------ comparar dos locales
# La segunda dirección vive, como la primera, solo en la sesión: «cmp_fase» dice qué se
# está viendo («elegir»: el buscador de la segunda dirección; «ver»: la comparación),
# «cmp_b» guarda el segundo punto con su resultado y «cmp_pendiente», una dirección que no
# es un portal y falta confirmar en el mapa. Al cambiar la primera dirección se borra todo.
AZUL_B = "#2a78d6"   # el segundo local, en el gráfico y en las cabeceras


def quitar_comparacion() -> None:
    for clave in ("cmp_fase", "cmp_b", "cmp_pendiente"):
        st.session_state.pop(clave, None)


def abrir_comparacion() -> None:
    """Abre la comparación: si ya hay segunda dirección, la enseña; si no, la pide."""
    st.session_state["cmp_fase"] = "ver" if st.session_state.get("cmp_b") else "elegir"


def cambiar_segunda() -> None:
    st.session_state.pop("cmp_b", None)
    st.session_state.pop("cmp_pendiente", None)
    st.session_state["cmp_fase"] = "elegir"
    buscador_nuevo()


def cerrar_comparacion() -> None:
    """Vuelve al resultado de la primera dirección; la segunda se conserva en la sesión."""
    st.session_state["cmp_fase"] = None
    st.session_state.pop("cmp_pendiente", None)


def elegir_b(lat: float, lon: float, lugar: str | None = None) -> None:
    """Fija la segunda dirección (las mismas reglas que la primera)."""
    st.session_state["cmp_b"] = {"punto": (round(lat, 6), round(lon, 6)),
                                 "lugar": lugar or "El segundo punto elegido"}
    st.session_state["cmp_fase"] = "ver"
    st.session_state.pop("cmp_pendiente", None)
    buscador_nuevo()


def dejar_pendiente_b(cand: dict, lat: float, lon: float) -> None:
    """Segunda dirección que no es un portal concreto: no se calcula hasta confirmarla."""
    st.session_state["cmp_pendiente"] = {"lat": round(lat, 6), "lon": round(lon, 6),
                                         "texto": cand["texto"],
                                         "precision": cand["precision"]}
    buscador_nuevo()


def confirmar_pendiente_b() -> None:
    p = st.session_state.get("cmp_pendiente")
    if p:
        elegir_b(p["lat"], p["lon"], p["texto"])


def buscador_nuevo() -> None:
    """Vacía el buscador (se monta de nuevo) y olvida las últimas sugerencias."""
    st.session_state["n_busca"] = st.session_state.get("n_busca", 0) + 1
    st.session_state.pop("_sug", None)


def volver_al_inicio() -> None:
    for clave in ("resultado", "pendiente", "lugar"):
        st.session_state.pop(clave, None)
    st.session_state.update(punto=None, ejemplo=None, abierta=None, vista="Resumen")
    quitar_comparacion()
    buscador_nuevo()


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
    quitar_comparacion()
    buscador_nuevo()


def confirmar_pendiente() -> None:
    p = st.session_state.get("pendiente")
    if p:
        elegir_punto(p["lat"], p["lon"], lugar=p["texto"])


# ------------------------------------------------------ buscador en tiempo real
PRIVACIDAD = ("Lo que escribes se envía a CartoCiudad para sugerir direcciones; no se guarda. "
              "Tu ubicación solo se usa si pulsas el botón y la aceptas; tampoco se guarda. "
              "Direcciones: CartoCiudad, IGN · CC BY 4.0 "
              "<a href='https://www.scne.es/productos.html#CartoCiudad' target='_blank' "
              "rel='noopener'>www.scne.es/productos.html#CartoCiudad</a>")


def sugerencias(q: str) -> dict:
    """Candidatos de CartoCiudad para lo que se está escribiendo, con las mismas reglas de
    siempre (geocodificar(): solo Madrid, sin nombres de comercios ni de lugares). Solo se
    recuerda la última consulta, en la sesión, para no repetirla al elegir."""
    if len(q) < MIN_LETRAS:
        return {"q": "", "cands": [], "estado": ""}
    ultima = st.session_state.get("_sug")
    if not ultima or ultima["q"] != q:
        try:
            ultima = {"q": q, "cands": geocodificar(q)[:MAX_SUGERENCIAS], "estado": "ok"}
        except Exception:
            ultima = {"q": q, "cands": [], "estado": "error"}
        st.session_state["_sug"] = ultima
    return ultima


def _nada() -> None:
    """Las órdenes del componente se atienden al volver a ejecutar, no en un callback."""


@fragmento("buscador")
def parte_buscador(modo: str, direccion: str = "", vista: str = "",
                   secciones: tuple = (), segundo: bool = False) -> None:
    """El buscador con sugerencias (portada) o la barra fija con el buscador dentro
    (resultado). Mientras se escribe solo se vuelve a ejecutar esta parte. Con «segundo»,
    es el buscador de la segunda dirección de una comparación: el mismo componente y las
    mismas reglas, pero lo elegido va al segundo punto."""
    clave = f"busca_{'b' if segundo else modo}_{st.session_state.get('n_busca', 0)}"
    elegir, pendiente_de = ((elegir_b, dejar_pendiente_b) if segundo
                            else (elegir_punto, dejar_pendiente))
    # Mientras se elige la segunda dirección, los avisos salen en su buscador, no en la barra.
    calla = modo == "barra" and st.session_state.get("cmp_fase") == "elegir"
    q = ((st.session_state.get(clave) or {}).get("q") or "").strip()
    sug = sugerencias(q)
    datos = {
        "modo": modo, "minimo": MIN_LETRAS, "q": sug["q"], "estado": sug["estado"],
        "sugerencias": [{"t": c["texto"], "nota": "" if c["exacto"] else
                         mayus(c["precision_texto"]) + ": confirmarás el sitio en el mapa"}
                        for c in sug["cands"]],
        "mensaje": "" if calla else st.session_state.pop("mensaje", ""),
        "placeholder": "Escribe la otra dirección" if segundo else
        "Escribe la dirección del local" if modo == "portada" else "Escribe otra dirección",
        "placeholder_corto": "Otra dirección" if segundo or modo != "portada"
        else "Dirección del local"}
    if modo == "portada":
        datos.update(ejemplos=list(EJEMPLOS), privacidad=PRIVACIDAD)
    else:
        datos.update(logo=logo_svg(), direccion=direccion, vista=vista,
                     vistas=VISTAS if vista else [],
                     secciones=[{"id": i, "t": t} for i, t in secciones],
                     ir_a=st.session_state.get("ir_a"))
    r = BUSCADOR(key=clave, data=datos, on_q_change=_nada, on_elegida_change=_nada,
                 on_ejemplo_change=_nada, on_ubicacion_change=_nada, on_inicio_change=_nada,
                 on_vista_change=_nada, on_fuentes_change=_nada)
    if r.fuentes:   # enlace «Fuentes y licencias» del pie
        if st.session_state.get("resultado"):
            ir_a_fuentes()
        else:       # sin resultado (dirección sin confirmar): las fuentes están en la portada
            volver_al_inicio()
        st.rerun()
    if r.ejemplo in EJEMPLOS:
        if segundo:
            elegir_b(*EJEMPLOS[r.ejemplo], r.ejemplo)
        else:
            elegir_punto(*EJEMPLOS[r.ejemplo], r.ejemplo)
        st.rerun()
    if r.ubicacion:   # solo llega si el usuario ha pulsado el botón y ha dado permiso
        elegir(float(r.ubicacion["lat"]), float(r.ubicacion["lon"]), lugar="Tu ubicación")
        st.rerun()
    if r.elegida and r.elegida.get("q") == sug["q"] and sug["cands"]:
        cand = sug["cands"][min(int(r.elegida.get("i", 0)), len(sug["cands"]) - 1)]
        try:
            xy = coordenadas(cand)
        except Exception:
            xy = None
        if xy and cand["exacto"]:
            elegir(*xy, lugar=cand["texto"])
        elif xy:   # una calle sin número, un municipio…: no se calcula hasta confirmar
            pendiente_de(cand, *xy)
        else:
            st.session_state["mensaje"] = ("No hemos podido situar esa dirección. Prueba con "
                                           "otra.")
        st.rerun()
    if r.inicio:
        volver_al_inicio()
        st.rerun()
    if r.vista in VISTAS and (r.vista != st.session_state.get("vista")
                              or st.session_state.get("cmp_fase")):
        st.session_state["vista"] = r.vista
        st.session_state.pop("ir_a", None)
        cerrar_comparacion()   # desde la comparación, las vistas vuelven al primer local
        st.rerun()


# ------------------------------------------------------------------ mercado


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
    with st.container(border=True, key=f"caja_m_{b['clave']}"):
        try:
            etiqueta, valor, frase = metrica_bloque(b)
        except (KeyError, TypeError, ValueError, IndexError):
            etiqueta, valor, frase = b["titulo"], "—", ""
        # Competencia: los locales del radio por tipo, con las marcas del mapa.
        por_tipo = b["datos"].get("comparacion_por_tipo", {}) if b["clave"] == "competencia" \
            else {}
        cuenta = ({t: por_tipo[t]["radio"] for t in S.TIPOS_COMPETENCIA}
                  if all(t in por_tipo for t in S.TIPOS_COMPETENCIA) else None)
        st.markdown(
            f"<div class='caja-t'>{html.escape(b['titulo'])} <span class='etiqueta'>"
            f"{html.escape(b['caracter'].capitalize())}</span></div>"
            f"<div class='m-etq'>{html.escape(etiqueta)}</div>"
            f"<div class='m-valor'>{html.escape(valor)}</div>"
            + (f"<div class='frase'>{html.escape(frase)}</div>" if frase else "")
            + (leyenda_mapa(cuenta=cuenta) if cuenta else ""), unsafe_allow_html=True)
        avisos = [n for n in b["notas"] if es_aviso(n)]
        with st.expander("Detalle, notas y fuentes" + (" · con avisos" if avisos else "")):
            st.markdown(b["resumen"])
            tabla_bloque(b)
            for n in b["notas"]:
                (st.warning if es_aviso(n) else st.caption)(n)
            st.caption("Fuentes: " + "; ".join(
                f"[{f['nombre']}]({f['enlace']}) ({f['licencia']}"
                + (f"; {f['periodo']}" if f.get("periodo") else "")
                + f"; descargado el {f['descargado']})" for f in b["fuentes"]))


# ------------------------------------------------------------------ riesgos
ICONO_RIESGO = {"sin_clase_universidad": "birrete", "sin_clase_colegios": "birrete",
                "competencia_alta": "tienda", "festivos": "calendario",
                "cobertura_baja": "mapa", "competencia_sin_valorar": "duda", "ninguno": "ok"}


def nota(icono: str, cuerpo_html: str, clase: str = "") -> str:
    """Un aviso con su icono y su color (ocre: atención; verde: sin novedad)."""
    return f"<div class='nota {clase}'>{ico(icono)}<div>{cuerpo_html}</div></div>"


def seccion_riesgos(rec: dict, inf: dict) -> None:
    """Los avisos del sitio (los mismos del Resumen, con su fiabilidad y su porqué) y, al
    lado, los avisos sobre los datos."""
    with seccion("riesgos") as lado:
        for r in rec["riesgos"]:
            icono = ICONO_RIESGO.get(r["clave"], "aviso")
            st.markdown(nota(icono, f"{html.escape(r['texto'])}<br>{etiquetas(r)}",
                             "bien" if icono == "ok" else ""), unsafe_allow_html=True)
            if r.get("porque"):
                with st.expander("Por qué"):
                    st.markdown("\n".join(f"- {p}" for p in r["porque"]))
    with lado:
        avisos = [es_aviso(n) for b in inf["bloques"] for n in b["notas"] if es_aviso(n)]
        st.markdown("<div class='lado-t'>Avisos sobre los datos</div>", unsafe_allow_html=True)
        st.markdown("\n".join(
            f"- {a}" for a in dict.fromkeys(
                avisos + ["El domingo no se modela aparte: «sábado» representa el fin de "
                          "semana.",
                          "Toda cifra de personas y de gasto es una estimación con supuestos "
                          "explícitos (src/supuestos.py)."])))
        st.caption("El texto completo de cada aviso está en la sección Mercado, en «Detalle, "
                   "notas y fuentes».")


# ------------------------------------------- informe: una sección por pregunta
SECCIONES = (("movimiento", "Nivel de movimiento"), ("quien", "A quién"),
             ("hora", "A qué hora"), ("vender", "Qué vender"), ("precio", "A qué precio"),
             ("perfil", "Perfil por horas"), ("mercado", "Mercado"),
             ("riesgos", "Riesgos y avisos"), ("comprobar", "Qué comprobar en persona"),
             ("fuentes", "Fuentes y licencias"))
ICONO_SECCION = {"movimiento": "aguja", "quien": "personas", "hora": "reloj", "vender": "taza",
                 "precio": "euro", "perfil": "grafico", "mercado": "cesta", "riesgos": "aviso",
                 "comprobar": "lista", "fuentes": "libro", "como-funciona": "info"}


def cabecera_seccion(clave: str, titulo: str | None = None, primera: bool = False) -> str:
    titulo = titulo or dict(SECCIONES)[clave]
    return (f"<div class='sec{' primera' if primera else ''}' id='{clave}'>"
            f"{ico(ICONO_SECCION[clave])}<b>{html.escape(titulo)}</b></div>")


class seccion:
    """Rejilla de una sección: a la izquierda, la columna de lectura (texto, listas y
    desplegables, todos del mismo ancho); a la derecha, un recuadro de apoyo con la cifra
    clave, un gráfico pequeño o la fiabilidad. En pantallas estrechas, uno debajo de otro
    (app/estilo.css). Uso:
        with seccion("quien") as lado:
            ...   # columna de lectura
        with lado:
            ...   # recuadro de apoyo"""

    def __init__(self, clave: str):
        self.fila = st.container(key=f"sec_{clave}")
        with self.fila:
            self.texto = st.container(key=f"texto_{clave}")
            self.lado = st.container(key=f"lado_{clave}")

    def __enter__(self):
        self.texto.__enter__()
        return self.lado

    def __exit__(self, *a):
        return self.texto.__exit__(*a)


def rec_detalle(r: dict) -> None:
    """Una recomendación dentro de un detalle desplegable: texto, etiquetas y sus motivos."""
    st.markdown(f"{r['texto']}<br>{etiquetas(r)}", unsafe_allow_html=True)
    if r.get("porque"):
        st.caption("\n".join(f"- {p}" for p in r["porque"]))


def seccion_pregunta(clave: str, t: dict, detalle, figura=None, pie: str = "") -> None:
    """Las cuatro preguntas tienen la misma estructura: respuesta en grande, porqué (la
    recomendación principal con sus motivos) y un detalle desplegable con todas las
    recomendaciones; al lado, la cifra clave o un gráfico pequeño y la fiabilidad."""
    r = t["rec"]
    st.markdown(cabecera_seccion(clave), unsafe_allow_html=True)
    with seccion(clave) as lado:
        st.markdown(
            f"<div class='resp-grande'>{html.escape(t['respuesta'])}</div>"
            + (f"<div class='resp-apoyo'>{html.escape(t['apoyo'])}</div>" if t["apoyo"] else "")
            + f"<div>{etiquetas(r)}</div><div class='porque-t'>Por qué</div>",
            unsafe_allow_html=True)
        st.markdown(f"**{r['texto']}**" + "".join(f"\n- {p}" for p in r.get("porque", [])))
        with st.expander("Detalle: todas las recomendaciones"):
            detalle()
        if pie:
            st.caption(pie)
    with lado:
        if figura:
            figura()
        st.markdown("<div class='lado-t'>Fiabilidad</div>" + fiabilidad(r),
                    unsafe_allow_html=True)


def por_dias(recs: list[dict], extra: tuple[str, list[dict]] | None = None) -> None:
    """Recomendaciones en pestañas: laborable, sábado y, si hace falta, una más."""
    nombres = ["Laborable", "Sábado"] + ([extra[0]] if extra else [])
    grupos = [rec_dia(recs, "laborable"), rec_dia(recs, "fin_de_semana")] \
        + ([extra[1]] if extra else [])
    for tab, grupo in zip(st.tabs(nombres), grupos):
        with tab:
            for r in grupo:
                rec_detalle(r)
            if not grupo:
                st.caption("Sin recomendaciones.")


def detalle_quien(rec: dict) -> None:
    for r in rec["a_quien"]["recomendaciones"]:
        rec_detalle(r)
    st.markdown("**Clientes por franja**")
    filas = []
    for f in S.FRANJAS:
        fila = {"Franja": f}
        for d, et in (("laborable", "Laborable"), ("fin_de_semana", "Sábado")):
            c = rec["a_quien"]["por_franja"][d][f]
            fila[et] = ", ".join(
                f"{x['nombre']} {100 * x['peso']:.0f} %" for x in c["clientes"]) or "—"
        filas.append(fila)
    st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")


def seccion_perfil(rec: dict, perfil: dict) -> None:
    st.markdown(cabecera_seccion("perfil")
                + "<div class='resp-apoyo'>Personas que pasan cerca cada hora, por tipo de "
                  "cliente (≈, estimación).</div>", unsafe_allow_html=True)
    dia_txt = st.segmented_control("Día", list(DIA_ETIQUETA), default="Laborable",
                                   label_visibility="collapsed", key="dia_informe",
                                   help="El perfil no modela el domingo aparte.") \
        or "Laborable"
    dia = DIA_ETIQUETA[dia_txt]
    with st.container(border=True, key="caja_perfil"):
        grafico_perfil(perfil, rec, dia)
        presentes = perfil["horas"].loc[dia][list(COLOR_CLIENTE)].sum()
        leyenda("Clientes", [(S.TIPOS_CLIENTE[t], c) for t, c in COLOR_CLIENTE.items()
                             if presentes[t] > 0], "<span>«punta»: horas punta</span>")
    with st.expander(f"Perfil por franjas · {dia_txt.lower()} (≈ personas, estimación)"):
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
    with seccion("comprobar") as lado:
        st.markdown(texto_lista)
        with st.expander("Copiar la lista"):
            st.code(texto_lista, language=None, wrap_lines=True)
    with lado:
        st.markdown(f"<div class='lado-t'>Para llevar al local</div><div class='cifra'>"
                    f"{len(lista)}</div><div class='cifra-pie'>comprobaciones para hacer en "
                    "persona antes de decidir: los datos abiertos no ven la calle.</div>",
                    unsafe_allow_html=True)
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
    with seccion("fuentes") as lado:
        st.markdown("**Otras fuentes:**")
        for e in fu["externas"] + fu["aplicacion"]:
            st.markdown(f"- **{e['titulo']}**  \n"
                        f"  Enlace: {e.get('Enlace', '?')}  \n"
                        f"  Licencia: {e.get('Licencia', '?')}  \n"
                        f"  Datos: {e.get('Versión de los datos', '?')} · descargado el "
                        f"{e.get('Fecha de descarga', '?')}")
    with lado:
        st.markdown("<div class='lado-t'>Atribuciones</div>", unsafe_allow_html=True)
        st.markdown(
            "**Powered by [CRTM](https://www.crtm.es)**. Los datos del Consorcio Regional de "
            "Transportes de Madrid (paradas, horarios GTFS y demanda de viajeros) se usan "
            "**procesados**: se calculan a partir de ellos los pasos de vehículos por hora y "
            "las personas por vehículo, no se muestran en bruto.\n\n"
            "Locales, campus y mapa: © [colaboradores de OpenStreetMap]"
            "(https://www.openstreetmap.org/copyright), datos con licencia "
            "[ODbL](https://opendatacommons.org/licenses/odbl/). ¿Ves un error en el mapa? "
            "[Infórmalo a OpenStreetMap](https://www.openstreetmap.org/fixthemap).\n\n"
            + ATRIBUCION_CARTOCIUDAD + ".\n\n"
            "Este proyecto **no está respaldado ni patrocinado por ninguna de las entidades** "
            "que publican los datos (Comunidad de Madrid, Ayuntamiento de Madrid, INE, IGN, "
            "CRTM, Fundación OpenStreetMap ni ninguna otra).")


# =========================================================================== página
cargar_datos()
fu = leer_fuentes()
VISTAS = ["Resumen", "Informe completo"]
AVISO_SENCILLO = ("Esto es una orientación con datos públicos, no una garantía. "
                  "Compruébalo siempre en persona.")
st.session_state.setdefault("vista", "Resumen")


def orientacion(texto: str) -> str:
    """El aviso de orientación, siempre visible encima del resultado."""
    return f"<div class='orienta'>{ico('info')}<span>{texto}</span></div>"


def ir_a_fuentes() -> None:
    """Abre el Informe completo por la sección de fuentes."""
    st.session_state["vista"] = "Informe completo"
    st.session_state["ir_a"] = {"id": "fuentes", "n": time.time()}


# El resultado del punto actual (perfil, informe, recomendaciones, municipio y locales del
# radio) se calcula una vez y se guarda en la sesión hasta que cambia el punto
# (elegir_punto lo borra). No se guarda en disco ni en ninguna caché compartida.
punto = st.session_state.get("punto")
res = st.session_state.get("resultado") if punto else None
if punto and res is None:
    muni_nuevo = municipio_de(*punto)
    if muni_nuevo is None:
        st.session_state["mensaje"] = "Ese punto está fuera de la Comunidad de Madrid. Elige otro."
        st.session_state["punto"] = punto = None
    else:
        hueco = st.empty()   # estado de carga: la aguja se mueve mientras se calcula
        hueco.markdown(f"<div class='cargando'>{aguja_svg(None)}<div>Mirando la zona…</div>"
                       "</div>", unsafe_allow_html=True)
        with medir("cálculo"):
            t0 = time.perf_counter()
            res = {**calcular(*punto), "muni": muni_nuevo,
                   "locs": locales_del_radio(*punto, muni_nuevo["cod"]),
                   "paradas": paradas_del_radio(*punto)}
            st.session_state["resultado"] = res
            st.session_state["segundos"] = time.perf_counter() - t0
        hueco.empty()
# El segundo punto de una comparación se calcula igual y también vive solo en la sesión.
b_cmp = st.session_state.get("cmp_b") if res else None
if b_cmp and "res" not in b_cmp:
    muni_b = municipio_de(*b_cmp["punto"])
    if muni_b is None:
        st.session_state["mensaje"] = ("Ese punto está fuera de la Comunidad de Madrid. "
                                       "Elige otro.")
        st.session_state.pop("cmp_b", None)
        st.session_state["cmp_fase"] = "elegir"
        b_cmp = None
    else:
        hueco = st.empty()
        hueco.markdown(f"<div class='cargando'>{aguja_svg(None)}<div>Mirando la segunda "
                       "zona…</div></div>", unsafe_allow_html=True)
        with medir("cálculo"):
            b_cmp["res"] = {**calcular(*b_cmp["punto"]), "muni": muni_b}
        hueco.empty()
cmp_fase = st.session_state.get("cmp_fase") if res else None
pendiente = None if punto else st.session_state.get("pendiente")
muni = res["muni"] if res else None
vista = st.session_state["vista"] if st.session_state["vista"] in VISTAS else "Resumen"


def lugar_analizado() -> str:
    """Cómo se nombra el punto: el ejemplo, la dirección elegida o «el punto elegido»,
    siempre con el municipio."""
    lugar = (st.session_state.get("ejemplo") or st.session_state.get("lugar")
             or "El punto que has elegido")
    return lugar if muni["nombre"] in lugar else f"{lugar} ({muni['nombre']})"


def lugar_b() -> str:
    """Cómo se nombra el segundo punto de la comparación."""
    m = b_cmp["res"]["muni"]["nombre"]
    return b_cmp["lugar"] if m in b_cmp["lugar"] else f"{b_cmp['lugar']} ({m})"


def acciones() -> None:
    """Los dos botones del resultado: comparar con otra dirección y descargar el informe.
    El PDF se genera en memoria al pulsar el botón; no se guarda en el servidor."""
    lugar, este, donde = lugar_analizado(), res, punto
    with st.container(key="acciones", horizontal=True):
        if st.button("Ver la comparación" if b_cmp else "Comparar con otra dirección",
                     key="btn_comparar", icon=":material/compare_arrows:"):
            abrir_comparacion()
            st.rerun()
        st.download_button(
            "Descargar informe (PDF)", key="btn_pdf", icon=":material/download:",
            data=lambda: informe_pdf(este, lugar, fu, donde, este["locs"], este.get("paradas")),
            file_name="barometro_informe.pdf", mime="application/pdf")


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
def parte_mapa(lat, lon, locs, alto: int, zoom: int = 16, paradas=None,
               segundo: bool = False) -> None:
    """El mapa. Un clic elige otro punto y, solo entonces, se recalcula la página. Con
    «segundo», el clic elige el segundo punto de la comparación."""
    clic = (mapa(lat, lon, locs, alto=alto, zoom=zoom, paradas=paradas)
            or {}).get("last_clicked")
    if clic:
        nuevo = (round(clic["lat"], 6), round(clic["lng"], 6))
        if nuevo != st.session_state.get("ultimo_clic"):
            st.session_state["ultimo_clic"] = nuevo
            if segundo:
                elegir_b(*nuevo)
                st.rerun()
            elif nuevo != st.session_state.get("punto"):
                elegir_punto(*nuevo)
                st.rerun()


@fragmento("gráfico")
def parte_grafico(perfil: dict, rec: dict) -> None:
    """Título, selector de día, gráfico por horas y leyenda."""
    dia_txt = st.session_state.get("dia_resumen") or "Día de diario"
    st.markdown("<div class='caja-t'>Así se mueve la gente en un "
                f"{dia_txt.lower()}</div><div class='caja-s'>Personas que pasan cerca, hora a "
                "hora (estimación).</div>", unsafe_allow_html=True)
    st.segmented_control("Día", list(DIA_RESUMEN), default="Día de diario",
                         label_visibility="collapsed", key="dia_resumen")
    leyenda("", grafico_resumen(perfil, rec, DIA_RESUMEN[dia_txt]))


@fragmento("comprobaciones")
def parte_comprobaciones(rec: dict) -> None:
    lista = comprobaciones_calle(rec)
    todas = st.session_state.get("todas_comprobaciones", False)
    st.markdown(f"<div class='seccion'>{ico('lista')}Antes de decidir, compruébalo tú</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='pasos-lista'>" + "".join(
        f"<div><i>{n}</i><span>{html.escape(c)}</span></div>"
        for n, c in enumerate(lista if todas else lista[:3], 1)) + "</div>",
        unsafe_allow_html=True)
    if len(lista) > 3:
        st.button("Ver solo las tres primeras" if todas else
                  f"Ver las {len(lista)} comprobaciones", key="ver_comprobaciones",
                  on_click=lambda: st.session_state.update(todas_comprobaciones=not todas))


def vista_resumen(rec: dict, perfil: dict, inf: dict) -> None:
    mov = res["mov"]
    st.markdown(veredicto(lugar_analizado(), mov, titular_calle(rec, mov)),
                unsafe_allow_html=True)
    if mov["muy_poco_paso"]:
        st.markdown(nota("aviso", html.escape(mov["aviso"])), unsafe_allow_html=True)
    acciones()
    parte_tarjetas(rec, inf, mov["muy_poco_paso"])

    # ------------------------------------------------------- mapa y gente por horas
    cm, cg = st.columns(2)
    with cm, st.container(border=True, key="caja_mapa"):
        st.markdown("<div class='caja-t'>Los bares y restaurantes que ya hay cerca</div>"
                    f"<div class='caja-s'>El círculo marca {S.RADIO_M} metros; también se ven "
                    "las paradas de transporte. Toca el mapa para mirar otro sitio.</div>",
                    unsafe_allow_html=True)
        parte_mapa(*punto, res["locs"], 380, paradas=res.get("paradas"))
        st.markdown(leyenda_mapa(res.get("paradas")), unsafe_allow_html=True)
    with cg, st.container(border=True, key="caja_grafico"):
        parte_grafico(perfil, rec)

    # ------------------------------------------- cómo se llega y qué hay más lejos
    transporte, entorno = frases_llegar(inf)
    st.markdown(f"<div class='seccion'>{ico('bus')}Cómo se llega y qué hay un poco más lejos"
                "</div>", unsafe_allow_html=True)
    modos = linea_llegar(inf)
    if modos:   # con paradas cerca: el nivel y, en vez de la frase, la línea con iconos
        transporte = f"<b>{html.escape(bloque_inf(inf, 'accesos')['datos']['nivel'])}</b>{modos}"
    st.markdown(f"<div class='llegar'><div>{ico('bus')}<span>{transporte}</span></div>"
                f"<div>{ico('casa')}<span>{entorno}</span></div></div>",
                unsafe_allow_html=True)

    # --------------------------------------------------- avisos y comprobaciones
    with st.container(key="dos_avisos"):   # dos columnas iguales en portátil
        with st.container(key="col_avisos"):
            st.markdown(f"<div class='seccion'>{ico('aviso')}Ojo con esto</div>",
                        unsafe_allow_html=True)
            st.markdown("".join(nota(icono, html.escape(frase), "bien" if icono == "ok" else "")
                                for icono, frase in avisos_calle(rec)), unsafe_allow_html=True)
        with st.container(key="col_comprobar"):
            parte_comprobaciones(rec)


# ------------------------------------------------------------ vista Informe completo
@fragmento("informe")
def parte_informe(rec: dict, perfil: dict, inf: dict) -> None:
    """El informe en una sola columna, una sección detrás de otra (el índice de la barra
    salta entre ellas). Cambiar de día en el perfil vuelve a ejecutar solo esta parte."""
    mov = res["mov"]
    resp = respuestas(rec, inf)
    aq, hr, qv, pr = (rec["a_quien"], rec["a_que_hora"], rec["que_vender"],
                      rec["a_que_precio"])
    with st.container(key="informe"):
        st.markdown(
            orientacion(AVISO) + f"<div class='donde' style='margin-top:1rem'>{ico('pin')}{html.escape(lugar_analizado())} · radio de "
            f"{S.RADIO_M} m · calculado en {dec(st.session_state['segundos'])} s</div>",
            unsafe_allow_html=True)
        acciones()
        st.markdown(cabecera_seccion("movimiento", primera=True), unsafe_allow_html=True)
        with seccion("movimiento") as lado:
            st.markdown(
                f"<div class='resp-grande'>{html.escape(mov['nombre'])}</div>"
                f"<div class='resp-apoyo'>Nivel {mov['nivel']} de 5</div>"
                "<div><span class='etiqueta'>Estimación</span></div>"
                "<div class='porque-t'>Por qué</div>", unsafe_allow_html=True)
            st.markdown(
                f"**Nivel de movimiento: {mov['nombre']}** (nivel {mov['nivel']} de 5). "
                f"≈{redondo(mov['pasos_laborable'])} personas pasan cerca en un día laborable; "
                f"{mov['frase']} (por encima del {100 * mov['posicion']:.0f} % de "
                f"{miles(mov['sitios_referencia'])} sitios de referencia, cuya mediana es "
                f"≈{redondo(mov['mediana_referencia'])}).")
            if mov["muy_poco_paso"]:
                st.markdown(nota("aviso", html.escape(mov["aviso"])), unsafe_allow_html=True)
            with st.expander(f"Detalle: cómo se calcula y por qué {S.RADIO_M} metros"):
                st.markdown(
                    f"{mov['nota']} Por qué {S.RADIO_M} metros: es lo que se anda en unos 4 "
                    "minutos, la distancia a la que alguien se desvía para tomar algo de "
                    "paso; por eso el perfil y las recomendaciones solo miran ese círculo. El "
                    f"transporte se mira además a {S.ACCESOS_RADIO_LEJOS_M} m y el entorno a "
                    f"{S.ENTORNO_RADIO_M // 1000} km, solo como contexto (sección Mercado).")
        with lado:
            st.markdown(
                indicador_movimiento(mov)
                + f"<div class='cifra'>≈{redondo(mov['pasos_laborable'])}</div>"
                "<div class='cifra-pie'>personas pasan cerca en un día laborable "
                "(estimación).</div>", unsafe_allow_html=True)

        seccion_pregunta("quien", resp["quien"], lambda: detalle_quien(rec),
                         lambda: diez_clientes(rec), aq["nota"])
        seccion_pregunta("hora", resp["cuando"], lambda: por_dias(hr["recomendaciones"]),
                         lambda: cifra_cuando(rec))
        seccion_pregunta("vender", resp["que"], lambda: por_dias(
            qv["recomendaciones"],
            ("Huecos y cocinas", [r for r in qv["recomendaciones"] if "dia" not in r]
             + qv["huecos"] + [qv["cocinas"]])), lambda: barras_que_mini(rec))
        seccion_pregunta("precio", resp["precio"],
                         lambda: [rec_detalle(r) for r in pr["recomendaciones"]] and None,
                         lambda: cifra_precio(inf))

        seccion_perfil(rec, perfil)

        st.markdown(cabecera_seccion("mercado"), unsafe_allow_html=True)
        with st.container(key="mercado"):   # dos columnas en portátil (app/estilo.css)
            for b in inf["bloques"]:
                bloque_mercado(b)
        st.markdown(cabecera_seccion("riesgos"), unsafe_allow_html=True)
        seccion_riesgos(rec, inf)
        st.markdown(cabecera_seccion("comprobar"), unsafe_allow_html=True)
        pestana_comprobar(rec)
        st.markdown(cabecera_seccion("fuentes"), unsafe_allow_html=True)
        pestana_fuentes(fu)


# ------------------------------------------------------------ vista Comparación
def lado_cmp(f: dict, lado: str, nombre: str, aguja: str = "") -> str:
    c = f[lado]
    mejor = f["mejor"] == lado
    lista = ("<ul>" + "".join(f"<li>{html.escape(x)}</li>" for x in c["lista"]) + "</ul>"
             if c.get("lista") else "")
    return (f"<div class='cmp-lado {lado}{' mejor' if mejor else ''}'>"
            f"<div class='cmp-quien'><i>{lado.upper()}</i>{html.escape(nombre)}</div>"
            + aguja + f"<div class='cmp-tit'>{html.escape(c['titulo'])}</div>"
            + (f"<div class='cmp-det'>{html.escape(c['detalle'])}</div>" if c["detalle"]
               else "") + lista
            + ("<div class='cmp-marca'>Sale mejor aquí</div>" if mejor else "") + "</div>")


def fila_cmp(f: dict, na: str, nb: str, agujas: tuple[str, str] = ("", "")) -> str:
    """Una fila de la comparación: el aspecto, los dos locales lado a lado (apilados en el
    móvil) y, debajo, cuál sale mejor o por qué no decide."""
    return (f"<div class='cmp-fila' id='cmp-{f['clave']}'><div class='cmp-asp'>"
            f"{html.escape(f['aspecto'])}"
            + (f"<span class='etiqueta conf-{f['fiabilidad']}'>"
               f"{html.escape(f['fiabilidad_texto'])}</span>" if f["fiabilidad"] else "")
            + "</div><div class='cmp-lados'>" + lado_cmp(f, "a", na, agujas[0])
            + lado_cmp(f, "b", nb, agujas[1]) + "</div>"
            f"<div class='cmp-ver{' decide' if f['mejor'] else ''}'>"
            f"{ico('ok' if f['mejor'] else 'info')}<span>{html.escape(f['veredicto'])}</span>"
            "</div></div>")


@fragmento("gráfico de la comparación")
def parte_grafico_cmp(c: dict) -> None:
    """Gente por horas de los dos locales, con las dos curvas superpuestas: A en línea
    continua y B en discontinua (no se distinguen solo por el color)."""
    na, nb = c["locales"]["a"], c["locales"]["b"]
    dia_txt = st.session_state.get("dia_cmp") or "Día de diario"
    st.markdown(f"<div class='caja-t'>Gente por horas en un {dia_txt.lower()}</div>"
                "<div class='caja-s'>Personas que pasan cerca de cada local, hora a hora "
                "(estimación).</div>", unsafe_allow_html=True)
    st.segmented_control("Día", list(DIA_RESUMEN), default="Día de diario",
                         label_visibility="collapsed", key="dia_cmp")
    dia = DIA_RESUMEN[dia_txt]
    datos = pd.DataFrame(
        [{"hora": h, "personas": float(v), "local": nombre, "cuando": f"{h} h",
          "txt": f"unas {unas(v)}" if v >= 1 else "casi nadie"}
         for lado, nombre in (("a", f"A · {na}"), ("b", f"B · {nb}"))
         for h, v in enumerate(c["personas_por_hora"][lado][dia])])
    orden = [f"A · {na}", f"B · {nb}"]
    base = alt.Chart(datos).encode(
        x=alt.X("hora:Q", title=None, scale=alt.Scale(domain=[0, 23], nice=False),
                axis=alt.Axis(values=list(range(0, 24, 3)), labelExpr="datum.value + ' h'",
                              labelFontSize=13, labelColor=SUAVE, labelPadding=8,
                              ticks=False, grid=False, domainColor=BORDE)),
        y=eje_personas(),
        color=alt.Color("local:N", legend=None,
                        scale=alt.Scale(domain=orden, range=[TEJA, AZUL_B])),
        tooltip=[alt.Tooltip("local:N", title="Local"), alt.Tooltip("cuando:N", title="Hora"),
                 alt.Tooltip("txt:N", title="Personas")])
    lineas = base.mark_line(strokeWidth=3).encode(
        strokeDash=alt.StrokeDash("local:N", legend=None,
                                  scale=alt.Scale(domain=orden, range=[[1, 0], [6, 4]])))
    puntos = base.mark_point(size=42, filled=True, opacity=1).encode(
        shape=alt.Shape("local:N", legend=None,
                        scale=alt.Scale(domain=orden, range=["circle", "square"])))
    st.altair_chart((lineas + puntos).properties(
        height=320, padding={"top": 14, "left": 2, "right": 10, "bottom": 2})
        .configure_view(strokeWidth=0), width="stretch")
    st.markdown(
        "<div class='leyenda cmp-ley'>"
        f"<span><i class='raya a'></i>A · {html.escape(na)} (línea continua)</span>"
        f"<span><i class='raya b'></i>B · {html.escape(nb)} (línea discontinua)</span></div>",
        unsafe_allow_html=True)


def vista_comparacion() -> None:
    """Los dos locales lado a lado, fila a fila, con las dos curvas por horas y un resumen
    final de dos o tres frases. No calcula nada: enseña lo que devuelve comparar()."""
    a = {**res, "nombre": lugar_analizado()}
    b = {**b_cmp["res"], "nombre": lugar_b()}
    c = comparar(a, b)
    na, nb = a["nombre"], b["nombre"]
    st.markdown(
        orientacion(html.escape(c["aviso"]))
        + "<div class='cmp-cab'><div class='cmp-etq'>Comparación de dos locales</div>"
        f"<div class='cmp-nombres'><span class='a'><i>A</i>{html.escape(na)}</span>"
        f"<span class='b'><i>B</i>{html.escape(nb)}</span></div></div>",
        unsafe_allow_html=True)
    with st.container(key="acciones", horizontal=True):
        st.button("Volver al resumen", key="btn_volver", on_click=cerrar_comparacion,
                  icon=":material/arrow_back:")
        st.button("Cambiar la segunda dirección", key="btn_cambiar", on_click=cambiar_segunda,
                  icon=":material/edit_location_alt:")
        st.download_button(
            "Descargar comparación (PDF)", key="btn_pdf_cmp", icon=":material/download:",
            data=lambda: comparacion_pdf(c, a, b, fu),
            file_name="barometro_comparacion.pdf", mime="application/pdf")
    agujas = tuple(f"<div class='cmp-aguja'>{aguja_svg(x['mov']['nivel'])}</div>"
                   for x in (a, b))
    filas = c["filas"]
    st.markdown("<div class='cmp'>" + "".join(
        fila_cmp(f, na, nb, agujas if f["clave"] == "movimiento" else ("", ""))
        for f in filas[:-1]) + "</div>", unsafe_allow_html=True)
    with st.container(border=True, key="caja_cmp_grafico"):
        parte_grafico_cmp(c)
    st.markdown("<div class='cmp'>" + fila_cmp(filas[-1], na, nb) + "</div>"
                f"<div class='seccion' style='margin-top:var(--hueco)'>{ico('lista')}"
                "En resumen</div>", unsafe_allow_html=True)
    st.markdown("<div class='cmp-resumen'>" + "".join(
        f"<p>{html.escape(x)}</p>" for x in c["resumen"])
        + f"<p class='pie-cmp'>{html.escape(c['nota'])}</p></div>", unsafe_allow_html=True)


def elegir_segunda() -> None:
    """Pantalla para elegir la segunda dirección: el mismo buscador y las mismas reglas
    (un portal se calcula; una calle sin número se confirma antes en el mapa)."""
    pend = st.session_state.get("cmp_pendiente")
    with st.container(key="caja_comparar"):
        st.markdown(
            "<div class='cmp-elegir-t'>Comparar con otra dirección</div>"
            f"<div class='cmp-elegir-s'>Ya tienes «{html.escape(lugar_analizado())}». Escribe "
            "la segunda dirección y las pondremos lado a lado.</div>", unsafe_allow_html=True)
        if not pend:
            parte_buscador("portada", segundo=True)
        st.button("Cancelar", key="btn_cancelar_cmp", on_click=cerrar_comparacion)
    if pend:   # no es un portal: no se calcula hasta confirmar el sitio
        with st.container(border=True, key="caja_confirma"):
            st.markdown(
                "<div class='confirma'>¿Es aquí? Si no, toca el mapa en el sitio exacto."
                f"</div><div class='confirma-pie'>«{html.escape(pend['texto'])}» "
                f"{QUE_ES[pend['precision']]}. Hemos puesto el punto en un sitio cualquiera "
                "de esa zona y todavía no hemos calculado nada.</div>",
                unsafe_allow_html=True)
            st.button("Sí, es aquí", type="primary", key="confirmar_b",
                      on_click=confirmar_pendiente_b)
            parte_mapa(pend["lat"], pend["lon"], None, 460, ZOOM_PENDIENTE[pend["precision"]],
                       segundo=True)


# ------------------------------------------------------------------------ portada
def portada() -> None:
    """Pantalla inicial: el nombre, una frase y el buscador; debajo, tres cifras."""
    c = cifras_portada()
    logo = logo_svg()
    st.markdown(
        f"<div class='pt-nav'><span class='marca'>{logo}<b>BARómetro</b></span><nav>"
        "<a href='#como-funciona'>Cómo funciona</a>"
        "<a href='#fuentes'>Fuentes<span class='ancho'> y licencias</span></a>"
        f"<a href='{REPOSITORIO}' target='_blank' rel='noopener'>Repositorio</a>"
        "</nav></div>", unsafe_allow_html=True)
    with st.container(key="portada"):
        st.markdown(
            f"<div class='pt-marca'>{logo}<b><i>BAR</i>ómetro</b></div>"
            "<div class='pt-frase'>Te ayuda a decidir qué ofrecer en tu bar o restaurante, "
            "según la zona.</div>", unsafe_allow_html=True)
        parte_buscador("portada")
        st.markdown(
            "<div class='pt-cifras'>"
            f"<div><b>{miles(c['conjuntos'])}</b><span>conjuntos de datos abiertos de la "
            "Comunidad de Madrid en uso</span></div>"
            f"<div><b>{miles(c['zonas'])}</b><span>zonas analizadas (secciones censales)"
            "</span></div>"
            f"<div><b>{miles(c['municipios'])}</b><span>municipios cubiertos</span></div>"
            f"</div><div class='pt-aviso'>{AVISO_SENCILLO}</div>", unsafe_allow_html=True)
    st.markdown(
        cabecera_seccion("como-funciona", "Cómo funciona", primera=True)
        + "<div class='pasos' style='margin-top:1rem'>"
        "<div class='paso'><i>1</i><b>Escribe la dirección</b><span>Pon la calle y el número "
        "de tu local, o usa tu ubicación.</span></div>"
        "<div class='paso'><i>2</i><b>Miramos la zona</b><span>Con datos abiertos vemos "
        f"quién pasa a menos de {S.RADIO_M} metros, a qué horas y qué bares hay ya."
        "</span></div>"
        "<div class='paso'><i>3</i><b>Lee el resumen</b><span>Qué ofrecer, a quién, a qué "
        "hora y a qué precios. Es una orientación: compruébalo siempre en persona."
        "</span></div></div>", unsafe_allow_html=True)
    st.markdown(cabecera_seccion("fuentes"), unsafe_allow_html=True)
    pestana_fuentes(fu)


# ------------------------------------------------------------------- qué se enseña
if res or pendiente:   # resultado sobre fondo claro, con la barra fija arriba
    st.markdown("<style>.block-container {padding-top:5rem;} @media (max-width:640px) "
                "{.block-container {padding-top:7.4rem;}}</style>", unsafe_allow_html=True)
if res and cmp_fase == "ver" and b_cmp:   # la comparación: ninguna vista marcada en la barra
    parte_buscador("barra", lugar_analizado(), "Comparación")
    vista_comparacion()
elif res and cmp_fase == "elegir":
    parte_buscador("barra", lugar_analizado(), "Comparación")
    elegir_segunda()
elif res:
    parte_buscador("barra", lugar_analizado(), vista,
                   SECCIONES if vista == "Informe completo" else ())
    if vista == "Resumen":   # solo se construye la vista que se está viendo
        st.markdown(orientacion(AVISO_SENCILLO), unsafe_allow_html=True)
        vista_resumen(res["rec"], res["perfil"], res["informe"])
    else:
        parte_informe(res["rec"], res["perfil"], res["informe"])
elif pendiente:
    # Dirección que no es un portal: no se calcula nada hasta que se confirma el sitio.
    parte_buscador("barra", f"«{pendiente['texto']}»: sin confirmar")
    with st.container(border=True, key="caja_confirma"):
        st.markdown(
            "<div class='confirma'>¿Es aquí? Si no, toca el mapa en el sitio exacto.</div>"
            f"<div class='confirma-pie'>«{html.escape(pendiente['texto'])}» "
            f"{QUE_ES[pendiente['precision']]}. Hemos puesto el punto en un sitio cualquiera "
            "de esa zona y todavía no hemos calculado nada. También puedes escribir la "
            "dirección con el número del portal.</div>", unsafe_allow_html=True)
        st.button("Sí, es aquí", type="primary", key="confirmar", on_click=confirmar_pendiente)
        parte_mapa(pendiente["lat"], pendiente["lon"], None, 460,
                   ZOOM_PENDIENTE[pendiente["precision"]])
else:
    portada()

# --------------------------------------------------------------------- pie
# El mismo pie en todas las vistas: una franja a todo el ancho, del color de la barra. El
# enlace «Fuentes y licencias» lo atiende app/buscador.js (lleva a esa sección; desde el
# Resumen, abre antes el Informe completo).
st.markdown(
    "<footer class='pie-bm'><div class='pie-dentro'>"
    f"<div class='pie-marca'><span class='marca'>{logo_svg()}<b>BARómetro</b></span>"
    "<p>Te ayuda a decidir qué ofrecer en tu bar o restaurante, según la zona.</p>"
    "<p class='tenue'>Prototipo para el datathon DATAMAD 2026 de la Comunidad de Madrid.</p>"
    "</div>"
    "<div class='pie-col'><b>Atribuciones</b><ul>"
    "<li>Powered by <a href='https://www.crtm.es' target='_blank' rel='noopener'>CRTM</a></li>"
    "<li>© <a href='https://www.openstreetmap.org/copyright' target='_blank' rel='noopener'>"
    "colaboradores de OpenStreetMap</a></li>"
    "<li>Direcciones: CartoCiudad, IGN · CC BY 4.0 · "
    "<a href='https://www.scne.es/productos.html#CartoCiudad' target='_blank' rel='noopener'>"
    "www.scne.es/productos.html#CartoCiudad</a></li></ul></div>"
    "<div class='pie-col'><b>Datos</b><ul>"
    f"<li>Descargados el {html.escape(fu['portal_descarga'])}</li>"
    "<li><a href='#fuentes' data-ir='fuentes'>Fuentes y licencias</a></li>"
    f"<li><a href='{REPOSITORIO}' target='_blank' rel='noopener'>Repositorio</a></li>"
    "</ul></div>"
    f"<div class='pie-legal'><p>{AVISO_SENCILLO} Toda cifra de personas es una estimación."
    "</p><p>Este proyecto no está respaldado ni patrocinado por ninguna de las entidades que "
    "publican los datos.</p></div>"
    "</div></footer>", unsafe_allow_html=True)
st.session_state["_en_pagina"] = False
anotar_medidas("página", _T_PAGINA)
