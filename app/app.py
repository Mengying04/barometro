"""BARómetro: aplicación web (Streamlit).

Muestra, para un punto de la Comunidad de Madrid, el perfil por horas, el informe del local
y las recomendaciones. No repite cálculos: solo llama a perfil_horario(), informe_local() y
recomendar() (src/), además de dos consultas de informe_local para saber en qué municipio
cae el punto y qué locales del radio se dibujan en el mapa.

Arranque (desde la raíz del repositorio):
    streamlit run app/app.py --server.address 0.0.0.0 --server.port 8501

Privacidad: las direcciones y los puntos que introduce el usuario solo viven en la memoria
de su sesión; no se escriben en ficheros, registros ni en la URL. Las estadísticas de uso
de Streamlit están desactivadas en .streamlit/config.toml.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

import altair as alt  # noqa: E402
import folium  # noqa: E402
import pandas as pd  # noqa: E402
import shapely  # noqa: E402
import streamlit as st  # noqa: E402
from streamlit_folium import st_folium  # noqa: E402

import informe_local as I  # noqa: E402
import perfil_horario as P  # noqa: E402
import supuestos as S  # noqa: E402
from recomendaciones import recomendar  # noqa: E402

AVISO = ("Orientación a partir de datos abiertos y supuestos explícitos, no garantías. "
         "Toda cifra de personas es una estimación.")
EJEMPLOS = {  # coordenadas de docs/registro/2026-11-10-informe-local-parte-a.md
    "Campus de Vicálvaro (URJC)": (40.4046, -3.6106),
    "Centro de Fuenlabrada": (40.283366, -3.800132),
    "Plaza Mayor de Griñón": (40.212861, -3.852623),
}
CENTRO_MADRID = (40.4168, -3.7038)
ZOOM_MAXIMO = 16
COLOR_TIPO = {"bar": "#d95f02", "restaurante": "#1b9e77", "cafeteria": "#7570b3",
              "comida_rapida": "#e7298a"}
COLOR_CLIENTE = {"padres_ninos": "#66a61e", "universitarios": "#7570b3",
                 "pacientes": "#e7298a", "trabajadores": "#1f78b4",
                 "deporte_eventos": "#e6ab02", "viajeros": "#d95f02", "vecinos": "#1b9e77"}
DIA_ETIQUETA = {"Laborable": "laborable", "Sábado": "fin_de_semana"}

# Geocodificador de CartoCiudad (IGN). Condiciones de uso y licencia en docs/fuentes.md.
CARTOCIUDAD = "https://www.cartociudad.es/geocoder/api/geocoder"
AGENTE = "BARometro-datamad2026/0.1"

st.set_page_config(page_title="BARómetro", page_icon="☕", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1200px;}
.etiqueta {display:inline-block; padding:0.1rem 0.5rem; border-radius:0.6rem;
           font-size:0.8rem; margin-right:0.3rem; background:#f1ece7; color:#5a3a2a;}
.conf-alta {background:#dff0e0; color:#1d5e2a;}
.conf-media {background:#fff1cc; color:#6b5200;}
.conf-baja {background:#f8dcdc; color:#7a1f1f;}
.leyenda span {display:inline-block; margin-right:0.9rem; font-size:0.85rem;}
.leyenda i {display:inline-block; width:0.75rem; height:0.75rem; border-radius:50%;
            margin-right:0.3rem; vertical-align:middle;}
@media print {header, .stButton, iframe {display:none !important;}}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------------- datos
@st.cache_resource(show_spinner="Cargando los datos abiertos (solo la primera vez)…")
def cargar_datos() -> bool:
    """Carga en memoria todas las capas que usan los cálculos (una vez por proceso)."""
    P.capas()
    I.capas()
    I.locales()
    I.renta_comunidad()
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
    return {"perfil": perfil, "informe": inf, "rec": rec}


# ----------------------------------------------------------------- geocodificación
# Tipos de resultado que se aceptan. Se descartan «toponimo» y «poi»: son nombres de
# comercios y lugares que pueden incluir nombres de personas.
TIPOS_GEOCODER = {"portal", "callejero", "carretera", "poblacion", "municipio", "Codpost",
                  "codpost"}
ATRIBUCION_CARTOCIUDAD = ("Direcciones: CartoCiudad, IGN · CC BY 4.0 "
                          "[www.scne.es/productos.html#CartoCiudad]"
                          "(https://www.scne.es/productos.html#CartoCiudad)")


def _cartociudad(metodo: str, **params) -> object:
    q = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{CARTOCIUDAD}/{metodo}?{q}",
                                 headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def geocodificar(texto: str) -> list[dict]:
    """Candidatos de CartoCiudad para una dirección de la provincia de Madrid. La
    dirección se envía a CartoCiudad y no se guarda en ningún sitio."""
    datos = _cartociudad("candidates", q=texto, limit=10, provincia_filter="Madrid")
    out = []
    for c in datos or []:
        if c.get("type") not in TIPOS_GEOCODER:
            continue
        via = c.get("tip_via") if c.get("type") == "callejero" else None
        etiqueta = " ".join(x for x in (via, c.get("address")) if x)
        if c.get("muni") and c["muni"] not in etiqueta:
            etiqueta += f", {c['muni']}"
        out.append({"texto": etiqueta, "tipo": c["type"], "id": c.get("id"),
                    "q": c.get("address"), "lat": c.get("lat"), "lon": c.get("lng")})
    return out


def coordenadas(cand: dict) -> tuple[float, float] | None:
    """Las calles y poblaciones vienen sin coordenadas: se piden con «find»."""
    if cand["lat"] and cand["lon"]:
        return float(cand["lat"]), float(cand["lon"])
    d = _cartociudad("find", q=cand["q"], type=cand["tipo"], id=cand["id"])
    if isinstance(d, dict) and d.get("lat") and d.get("lng"):
        return float(d["lat"]), float(d["lng"])
    return None


# ------------------------------------------------------------------- fuentes.md
@st.cache_data
def leer_fuentes() -> dict:
    """Fuentes, enlaces, licencias y fechas tal como están en docs/fuentes.md."""
    texto = (RAIZ / "docs" / "fuentes.md").read_text(encoding="utf-8")

    def bloque(clave):
        m = re.search(rf"<!-- inicio:{clave} -->(.*?)<!-- fin:{clave} -->", texto, re.S)
        return m.group(1) if m else ""

    portal = bloque("portal")
    descarga = re.search(r"Fecha de descarga:\s*([\d-]+)", portal)
    filas = []
    for linea in portal.splitlines():
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if len(celdas) == 6 and celdas[1].startswith("["):
            filas.append({"Conjunto": celdas[0], "Ficha": celdas[1], "Licencia": celdas[2],
                          "Última modificación": celdas[3]})

    def secciones(txt):
        out = []
        for trozo in re.split(r"\n### ", txt)[1:]:
            titulo, _, resto = trozo.partition("\n")
            campos = dict(re.findall(r"- \*\*([^:*]+):\*\*\s*(.+)", resto))
            out.append({"titulo": titulo.strip(), **campos})
        return out

    return {"portal": filas, "portal_descarga": descarga.group(1) if descarga else "?",
            "externas": secciones(bloque("externas")),
            "aplicacion": secciones(bloque("aplicacion"))}


# --------------------------------------------------------------------- presentación
def etiquetas(r: dict) -> str:
    c = r.get("confianza", "baja")
    return (f"<span class='etiqueta conf-{c}'>Confianza {c}</span>"
            f"<span class='etiqueta'>{r.get('base', '')}</span>")


def mostrar_rec(r: dict, clave: str) -> None:
    st.markdown(f"{r['texto']}<br>{etiquetas(r)}", unsafe_allow_html=True)
    if r.get("porque"):
        with st.expander("Por qué"):
            st.markdown("\n".join(f"- {p}" for p in r["porque"]))


def tarjeta(titulo: str, recs: list[dict], clave: str, extra=None) -> None:
    with st.container(border=True):
        st.markdown(f"#### {titulo}")
        for i, r in enumerate(recs):
            mostrar_rec(r, f"{clave}{i}")
        if extra:
            extra()


def tarjeta_pestanas(titulo: str, pestanas: dict[str, list[dict]], clave: str) -> None:
    """Tarjeta con pestañas (por ejemplo, laborable y sábado) para que no sea muy larga."""
    with st.container(border=True):
        st.markdown(f"#### {titulo}")
        for (nombre, recs), tab in zip(pestanas.items(), st.tabs(list(pestanas))):
            with tab:
                for i, r in enumerate(recs):
                    mostrar_rec(r, f"{clave}{nombre}{i}")


def mapa(lat, lon, locs: pd.DataFrame | None) -> dict | None:
    zoom = 16 if lat is not None else 10
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
        folium.Circle((lat, lon), radius=S.RADIO_M, color="#9c3d1b", weight=2,
                      fill=True, fill_opacity=0.06, interactive=False).add_to(m)
        if locs is not None:
            for f in locs.itertuples():   # sin ventanas ni nombres: solo el tipo por color
                folium.CircleMarker((f.lat, f.lon), radius=5, weight=1, color="#333333",
                                    fill=True, fill_color=COLOR_TIPO.get(f.tipo, "#999999"),
                                    fill_opacity=0.9, interactive=False).add_to(m)
        folium.CircleMarker((lat, lon), radius=9, weight=3, color="#ffffff",
                            fill=True, fill_color="#9c3d1b", fill_opacity=1,
                            interactive=False).add_to(m)
    return st_folium(m, height=430, use_container_width=True,
                     returned_objects=["last_clicked"], key="mapa")


def elegir_punto(lat: float, lon: float) -> None:
    st.session_state["punto"] = (round(lat, 6), round(lon, 6))
    st.session_state.pop("resultado", None)


# =========================================================================== página
st.title("BARómetro")
st.markdown("Para cualquier punto de la Comunidad de Madrid: **a quién vender, a qué hora, "
            "qué vender y a qué precio** en un bar o restaurante, con datos abiertos.")
st.warning(AVISO, icon="⚠️")

cargar_datos()

# ---------------------------------------------------------------- elegir el punto
st.subheader("1. Elige un punto")
c1, c2 = st.columns([3, 2])
with c1:
    with st.form("buscador", clear_on_submit=False, border=False):
        texto = st.text_input("Dirección", placeholder="Por ejemplo: Calle Mayor 1, Getafe",
                              help="La dirección se envía al geocodificador de CartoCiudad "
                                   "(IGN) para situarla en el mapa. No se guarda.")
        buscar = st.form_submit_button("Buscar")
    if buscar and texto.strip():
        try:
            st.session_state["candidatos"] = geocodificar(texto.strip())
        except Exception:
            st.session_state["candidatos"] = None
            st.error("No se ha podido consultar CartoCiudad. Prueba más tarde o haz clic en "
                     "el mapa.")
    cand = st.session_state.get("candidatos")
    if cand == []:
        st.info("No se ha encontrado esa dirección en la provincia de Madrid.")
    elif cand:
        i = st.selectbox("Resultados", range(len(cand)),
                         format_func=lambda k: cand[k]["texto"])
        if st.button("Analizar esta dirección"):
            try:
                xy = coordenadas(cand[i])
            except Exception:
                xy = None
            if xy:
                elegir_punto(*xy)
                st.session_state.pop("candidatos", None)
            else:
                st.error("CartoCiudad no ha devuelto la posición de esa dirección.")
    st.caption(ATRIBUCION_CARTOCIUDAD)
with c2:
    st.markdown("**Ejemplos**")
    for nombre_ej, (la, lo) in EJEMPLOS.items():
        if st.button(nombre_ej, width="stretch"):
            elegir_punto(la, lo)
st.caption("También puedes hacer clic en el mapa para elegir el punto.")

punto = st.session_state.get("punto")
muni = municipio_de(*punto) if punto else None
if punto and muni is None:
    st.error("Ese punto está fuera de la Comunidad de Madrid: no se calcula nada. Elige otro.")

if punto and muni and "resultado" not in st.session_state:
    with st.spinner("Calculando el perfil, el informe y las recomendaciones…"):
        t0 = time.perf_counter()
        st.session_state["resultado"] = calcular(*punto)
        st.session_state["segundos"] = time.perf_counter() - t0
res = st.session_state.get("resultado") if (punto and muni) else None

# ----------------------------------------------------------------------------- mapa
st.subheader("2. Mapa")
locs = locales_del_radio(*punto, muni["cod"]) if res else None
salida = mapa(*(punto if punto else (None, None)), locs)
clic = (salida or {}).get("last_clicked")
if clic:
    nuevo = (round(clic["lat"], 6), round(clic["lng"], 6))
    if nuevo != st.session_state.get("ultimo_clic"):
        st.session_state["ultimo_clic"] = nuevo
        if nuevo != punto:
            elegir_punto(*nuevo)
            st.rerun()
if res:
    comp = next(b for b in res["informe"]["bloques"] if b["clave"] == "competencia")
    st.markdown(
        "<div class='leyenda'>" + "".join(
            f"<span><i style='background:{COLOR_TIPO[t]}'></i>{n}</span>"
            for t, n in S.TIPOS_COMPETENCIA.items())
        + f"<span>· círculo de {S.RADIO_M} m · fuente de los locales: "
          f"{comp['datos']['fuente_usada']}</span></div>", unsafe_allow_html=True)
    st.caption(f"{muni['nombre']} · calculado en {st.session_state['segundos']:.1f} s")

if not res:
    st.info("Elige un punto con el buscador, un ejemplo o un clic en el mapa.")
else:
    rec = res["rec"]
    perfil = res["perfil"]
    inf = res["informe"]

    # ---------------------------------------------------------------- resumen
    st.subheader("3. Resumen")
    st.caption(rec["a_quien"]["nota"])
    fila1 = st.columns(2)
    fila2 = st.columns(2)
    with fila1[0]:
        def tabla_franjas():
            with st.expander("Clientes por franja"):
                filas = []
                for f in S.FRANJAS:
                    fila = {"Franja": f}
                    for d, etiqueta in (("laborable", "Laborable"), ("fin_de_semana", "Sábado")):
                        c = rec["a_quien"]["por_franja"][d][f]
                        fila[etiqueta] = ", ".join(
                            f"{x['nombre']} {100 * x['peso']:.0f} %" for x in c["clientes"]) or "—"
                    filas.append(fila)
                st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
        tarjeta("A quién", rec["a_quien"]["recomendaciones"], "quien", tabla_franjas)
    with fila1[1]:
        hr = rec["a_que_hora"]["recomendaciones"]
        tarjeta_pestanas("A qué hora", {
            "Laborable": [r for r in hr if r.get("dia") == "laborable"],
            "Sábado": [r for r in hr if r.get("dia") == "fin_de_semana"]}, "hora")
    with fila2[0]:
        qv = rec["que_vender"]
        tarjeta_pestanas("Qué vender", {
            "Laborable": [r for r in qv["recomendaciones"] if r.get("dia") == "laborable"],
            "Sábado": [r for r in qv["recomendaciones"] if r.get("dia") == "fin_de_semana"],
            "Huecos y cocinas": [r for r in qv["recomendaciones"] if "dia" not in r]
                                + qv["huecos"] + [qv["cocinas"]]}, "vender")
    with fila2[1]:
        tarjeta("A qué precio", rec["a_que_precio"]["recomendaciones"], "precio")
    with st.container(border=True):
        st.markdown("#### Riesgos y avisos")
        for i, r in enumerate(rec["riesgos"]):
            mostrar_rec(r, f"riesgo{i}")

    # ---------------------------------------------------------------- perfil
    st.subheader("4. Perfil por horas")
    dia_txt = st.radio("Día", list(DIA_ETIQUETA), horizontal=True,
                       help="El perfil no modela el domingo aparte.")
    dia = DIA_ETIQUETA[dia_txt]
    h = perfil["horas"].loc[dia][P.TIPOS].reset_index()
    largo = h.melt(id_vars="hora", var_name="tipo", value_name="personas")
    largo["cliente"] = largo["tipo"].map(S.TIPOS_CLIENTE)
    orden = [S.TIPOS_CLIENTE[t] for t in P.TIPOS]
    graf = alt.Chart(largo).mark_bar().encode(
        x=alt.X("hora:O", title="Hora"),
        y=alt.Y("personas:Q", title="Personas que pasan cerca (estimación)"),
        color=alt.Color("cliente:N", title="Tipo de cliente",
                        scale=alt.Scale(domain=orden,
                                        range=[COLOR_CLIENTE[t] for t in P.TIPOS]),
                        legend=alt.Legend(orient="bottom", columns=4)),
        order=alt.Order("tipo:N"),
        tooltip=[alt.Tooltip("hora:O", title="Hora"), alt.Tooltip("cliente:N", title="Cliente"),
                 alt.Tooltip("personas:Q", title="Personas", format=",.0f")],
    ).properties(height=340)
    st.altair_chart(graf, width="stretch")
    fr = perfil["franjas"].loc[dia].rename(columns={**S.TIPOS_CLIENTE, "total": "Total"})
    fr.index = fr.index.astype(str)
    st.dataframe(fr, width="stretch")
    conf = perfil["confianza"][["nombre", "confianza_horario", "confianza_cantidad"]]
    with st.expander("Confianza de cada tipo de cliente"):
        st.dataframe(conf.rename(columns={"nombre": "Tipo", "confianza_horario": "Horario",
                                          "confianza_cantidad": "Cantidad"}),
                     hide_index=True, width="stretch")

    # ---------------------------------------------------------------- mercado
    st.subheader("5. Mercado")
    AVISOS = ("Probablemente faltan locales", "incluye hoteles", "aún no están",
              "Limitación importante")
    for b in inf["bloques"]:
        with st.container(border=True):
            st.markdown(f"#### {b['titulo']}")
            st.markdown(f"<span class='etiqueta'>{b['caracter']}</span>",
                        unsafe_allow_html=True)
            st.markdown(b["resumen"])
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
            for n in b["notas"]:
                (st.warning if any(a in n for a in AVISOS) else st.caption)(n)
            st.caption("Fuentes: " + "; ".join(
                f"[{f['nombre']}]({f['enlace']}) ({f['licencia']}"
                + (f"; {f['periodo']}" if f.get("periodo") else "")
                + f"; descargado el {f['descargado']})" for f in b["fuentes"]))

    # ---------------------------------------------------------------- comprobar
    st.subheader("6. Qué comprobar en persona")
    lista = rec["comprobar_en_persona"]
    st.markdown("\n".join(f"{i}. {c}" for i, c in enumerate(lista, 1)))
    texto_lista = "\n".join(f"{i}. {c}" for i, c in enumerate(lista, 1))
    st.code(texto_lista, language=None, wrap_lines=True)
    st.download_button("Descargar la lista (.txt)", texto_lista.encode("utf-8"),
                       file_name="barometro_comprobaciones.txt", mime="text/plain")

# ------------------------------------------------------------- fuentes y licencias
st.subheader("7. Fuentes y licencias")
fu = leer_fuentes()
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
    "Este proyecto **no está respaldado ni patrocinado por ninguna de las entidades** que "
    "publican los datos (Comunidad de Madrid, Ayuntamiento de Madrid, INE, IGN, CRTM, "
    "Fundación OpenStreetMap ni ninguna otra).")
st.caption("BARómetro · prototipo para DATAMAD 2026 · " + AVISO)
