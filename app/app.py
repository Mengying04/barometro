"""BARómetro: aplicación web (Streamlit).

Muestra, para un punto de la Comunidad de Madrid, el perfil por horas, el informe del local
y las recomendaciones. No repite cálculos: solo llama a perfil_horario(), informe_local() y
recomendar() (src/), además de dos consultas de informe_local para saber en qué municipio
cae el punto y qué locales del radio se dibujan en el mapa.

La pantalla va de la conclusión al detalle, en tres niveles:
  1. cabecera con buscador, titular de una frase y cuatro tarjetas (visible sin bajar);
  2. mapa y perfil por horas, lado a lado;
  3. pestañas con el detalle, el mercado, los riesgos, las comprobaciones y las fuentes.
El titular y las tarjetas solo resumen lo que ya devuelve recomendar(): no calculan nada.

Arranque (desde la raíz del repositorio):
    streamlit run app/app.py --server.address 0.0.0.0 --server.port 8501

Privacidad: las direcciones y los puntos que introduce el usuario solo viven en la memoria
de su sesión; no se escriben en ficheros, registros ni en la URL. Las estadísticas de uso
de Streamlit están desactivadas en .streamlit/config.toml.
"""

from __future__ import annotations

import html
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
# Nombre corto de cada tipo de cliente para el titular.
CLIENTE_TITULAR = {"vecinos": "vecinos", "viajeros": "viajeros",
                   "universitarios": "universitarios", "padres_ninos": "familias con niños",
                   "pacientes": "pacientes", "trabajadores": "trabajadores",
                   "deporte_eventos": "público de deporte y eventos"}

# Geocodificador de CartoCiudad (IGN). Condiciones de uso y licencia en docs/fuentes.md.
CARTOCIUDAD = "https://www.cartociudad.es/geocoder/api/geocoder"
AGENTE = "BARometro-datamad2026/0.1"

st.set_page_config(page_title="BARómetro", page_icon="☕", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
.block-container {padding-top: 2.6rem; padding-bottom: 1rem; max-width: 1280px;}
h1, h2, h3, h4 {letter-spacing: -0.01em;}
.marca {display:flex; align-items:baseline; gap:0.8rem; flex-wrap:wrap; margin-bottom:0.2rem;}
.marca b {font-size:1.7rem; font-weight:700; color:#9c3d1b; letter-spacing:-0.02em;}
.marca span {color:#5c5248; font-size:0.98rem;}
.aviso {font-size:0.82rem; color:#5c5248; border-left:3px solid #c98a2b;
        padding:0.1rem 0.6rem; margin:0.1rem 0 0.4rem 0;}
.donde {font-size:0.85rem; color:#5c5248; margin:0.3rem 0 0 0;}
.titular {font-size:1.5rem; font-weight:650; line-height:1.3; color:#1f1b16;
          margin:0.15rem 0 0.7rem 0;}
.tarjeta-cab {font-size:0.78rem; font-weight:600; text-transform:uppercase;
              letter-spacing:0.06em; color:#7a6f64;}
.tarjeta-cab .ico {font-size:1.15rem; margin-right:0.35rem; vertical-align:-0.1rem;}
.tarjeta-res {font-size:1.45rem; font-weight:700; line-height:1.2; color:#1f1b16;
              margin:0.35rem 0 0.25rem 0; min-height:3.5rem;}
.tarjeta-apoyo {font-size:0.88rem; color:#4a4038; line-height:1.35; min-height:2.4rem;}
.etiqueta {display:inline-block; padding:0.08rem 0.5rem; border-radius:0.6rem;
           font-size:0.75rem; font-weight:500; margin:0.35rem 0.25rem 0 0;
           background:#efe9e0; color:#4a3d32;}
.conf-alta {background:#dcefdf; color:#1b5427;}
.conf-media {background:#fbefc9; color:#5e4700;}
.conf-baja {background:#f6dcda; color:#7a1f1f;}
.punto {display:inline-block; width:0.7rem; height:0.7rem; border-radius:50%;
        margin-right:0.3rem; vertical-align:0.05rem;}
.leyenda {font-size:0.82rem; color:#4a4038; line-height:1.8;}
.leyenda b {font-weight:600; margin-right:0.5rem;}
.leyenda span {display:inline-block; margin-right:0.8rem; white-space:nowrap;}
.frase {font-size:0.88rem; color:#4a4038; margin-top:-0.4rem;}
.riesgo {font-size:1rem; margin:0.2rem 0 0 0;}
.pie {font-size:0.78rem; color:#6b6157; border-top:1px solid #e3dcd1;
      padding-top:0.6rem; margin-top:1.5rem;}
.pie a {color:#6b6157;}
div[data-testid="stMetric"] {padding:0;}
@media (max-width: 640px) {
  .titular {font-size:1.25rem;}
  .tarjeta-res, .tarjeta-apoyo {min-height:0;}
}
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


# ------------------------------------------------- resumen (solo lee recomendar())
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


def frase_competencia(rec: dict, inf: dict) -> str:
    comp = bloque_inf(inf, "competencia")["datos"]
    huecos = rec["que_vender"]["huecos"]
    textos_riesgo = " ".join(r["texto"] for r in rec["riesgos"])
    falta = [h["tipo"] for h in huecos if h.get("sentido") == "falta"]
    al_menos = "al menos " if comp.get("cobertura_osm") else ""
    if "sirven_comidas" in falta:
        return "pocos locales que sirven comidas"
    if falta:
        return "pocos " + S.TIPOS_COMPETENCIA[falta[0]].lower()
    if textos_riesgo.startswith("Competencia alta") or "Competencia alta" in textos_riesgo:
        return f"mucha competencia ({al_menos}{comp['total']} locales en {S.RADIO_M} m)"
    return f"{al_menos}{comp['total']} locales de hostelería en {S.RADIO_M} m"


def titular(rec: dict, inf: dict) -> str:
    """Una frase que resume el punto a partir de las recomendaciones."""
    quien = [CLIENTE_TITULAR[t] for t, _ in clientes_principales(rec)]
    grupos = grupos_horas(rec, "laborable")[:2]
    horas = sorted(hora_de_grupo(rec, "laborable", g) for g in grupos)
    partes = [f"Zona de {lista_y(quien)}"] if quien else ["Zona con poco movimiento"]
    if horas:
        partes.append("con hora punta hacia " + lista_y([f"las {h}" for h in horas]))
    frase = ", ".join(partes) + " y " + frase_competencia(rec, inf) + "."
    return frase[0].upper() + frase[1:]


def tarjeta(icono: str, titulo: str, respuesta: str, apoyo: str, r: dict,
            porque: callable) -> None:
    with st.container(border=True):
        st.markdown(
            f"<div class='tarjeta-cab'><span class='ico'>{icono}</span>{titulo}</div>"
            f"<div class='tarjeta-res'>{respuesta}</div>"
            f"<div class='tarjeta-apoyo'>{apoyo}</div>{etiquetas(r)}",
            unsafe_allow_html=True)
        with st.expander("Por qué"):
            porque()


def porque_de(recs: list[dict], extra: str | None = None) -> callable:
    def mostrar():
        for r in recs:
            st.markdown(f"**{r['texto']}**")
            if r.get("porque"):
                st.markdown("\n".join(f"- {p}" for p in r["porque"]))
        if extra:
            st.caption(extra)
    return mostrar


def tarjetas(rec: dict, inf: dict) -> None:
    c = st.columns(4, gap="small")
    # ---- a quién
    aq = rec["a_quien"]["recomendaciones"]
    lab = rec_dia(aq, "laborable")
    principales = clientes_principales(rec)
    resp = " y ".join(
        f"<span class='punto' style='background:{COLOR_CLIENTE[t]}'></span>"
        f"{S.TIPOS_CLIENTE[t] if i == 0 else S.TIPOS_CLIENTE[t].lower()}"
        for i, (t, _) in enumerate(principales)) or "Sin datos"
    sab = clientes_principales(rec, "fin_de_semana")
    apoyo = ("≈" + " y ≈".join(f"{round(100 * p)} %" for _, p in principales)
             + " de los clientes posibles en laborable"
             + (f" · sábado: {lista_y([S.TIPOS_CLIENTE[t].lower() for t, _ in sab])}"
                if sab else ""))
    with c[0]:
        tarjeta("👥", "A quién", resp, apoyo, lab[0] if lab else aq[0],
                porque_de(aq, rec["a_quien"]["nota"]))
    # ---- a qué hora
    hr = rec["a_que_hora"]["recomendaciones"]
    g_lab = sorted(grupos_horas(rec, "laborable"))
    g_sab = sorted(grupos_horas(rec, "fin_de_semana"))
    hueco = [r for r in hr if r["texto"].startswith("Posible hueco horario")]
    apoyo = "Horas punta de un laborable"
    if g_sab:
        apoyo += " · sábado: " + ", ".join(tramo(g) for g in g_sab)
    if hueco:
        apoyo += " · posible hueco en " + hueco[0]["texto"].split(": ", 1)[1].split(" (")[0]
    with c[1]:
        tarjeta("🕗", "A qué hora", " · ".join(tramo(g) for g in g_lab) or "Sin datos",
                apoyo, rec_dia(hr, "laborable")[0] if rec_dia(hr, "laborable") else hr[0],
                porque_de(hr))
    # ---- qué vender
    qv = rec["que_vender"]
    v_lab = rec_dia(qv["recomendaciones"], "laborable")
    v_sab = rec_dia(qv["recomendaciones"], "fin_de_semana")
    oportunidad = [r for r in qv["recomendaciones"] if "dia" not in r]
    resp = S.MOMENTOS[v_lab[0]["momento"]] if v_lab else "Sin datos"
    if oportunidad:
        momento = oportunidad[0]["texto"].split("público para ")[1].split(":")[0]
        apoyo = f"Oportunidad a comprobar: {momento} (pocos locales de comidas)"
    else:
        apoyo = " · ".join(
            ([f"Luego {S.MOMENTOS[v_lab[1]['momento']].lower()}"] if len(v_lab) > 1 else [])
            + ([f"sábado: {S.MOMENTOS[v_sab[0]['momento']].lower()}"] if v_sab else []))
    with c[2]:
        tarjeta("🍽️", "Qué vender", resp, apoyo,
                v_lab[0] if v_lab else qv["cocinas"],
                porque_de(qv["recomendaciones"] + qv["huecos"] + [qv["cocinas"]]))
    # ---- a qué precio
    pr = rec["a_que_precio"]["recomendaciones"]
    gama = bloque_inf(inf, "precios")["datos"]["gama_ajustada"]["gama"]["semana"]
    ipc = bloque_inf(inf, "precios")["datos"].get("ipc_interanual") or {}
    apoyo = "Sin precios en euros: compara 3–5 cartas cerca"
    v = ipc.get("restaurantes_alojamiento")
    if v is not None:
        apoyo = (f"Sector {v:+.1f} % en 12 meses (IPC)".replace(".", ",")
                 + " · sin precios en euros: compara 3–5 cartas cerca")
    with c[3]:
        tarjeta("💶", "A qué precio", f"Gama {gama}", apoyo, pr[0], porque_de(pr))


# ------------------------------------------------------------------ mapa y gráfico
def mapa(lat, lon, locs: pd.DataFrame | None, alto: int = 400) -> dict | None:
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
    return st_folium(m, height=alto, use_container_width=True,
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
def pestana_detalle(rec: dict, perfil: dict, dia_txt: str) -> None:
    dia = DIA_ETIQUETA[dia_txt]
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

# ------------------------------------------------------- nivel 1: cabecera y buscador
st.markdown("<div class='marca'><b>BARómetro</b><span>Qué vender, a quién, a qué hora y a "
            "qué precio en un bar o restaurante de la Comunidad de Madrid, con datos "
            "abiertos.</span></div>", unsafe_allow_html=True)
cb = st.columns([2.6, 0.7, 1.45, 1.55, 1.55], gap="small", vertical_alignment="bottom")
with cb[0]:
    texto = st.text_input("Dirección", placeholder="Escribe una dirección: Calle Mayor 1, "
                          "Getafe", label_visibility="collapsed", key="texto",
                          on_change=pedir_busqueda,
                          help="La dirección se envía al geocodificador de CartoCiudad "
                               "(IGN) para situarla en el mapa. No se guarda.")
with cb[1]:
    if st.button("Buscar", type="primary", width="stretch"):
        pedir_busqueda()
for col, (nombre_ej, (la, lo)) in zip(cb[2:], EJEMPLOS.items()):
    with col:
        activo = st.session_state.get("ejemplo") == nombre_ej
        if st.button(nombre_ej, width="stretch", type="primary" if activo else "secondary"):
            elegir_punto(la, lo, nombre_ej)
            st.rerun()

if st.session_state.pop("buscar", False) and texto.strip():
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
    cc = st.columns([3.2, 1.2], vertical_alignment="bottom")
    with cc[0]:
        i = st.selectbox("Resultados de CartoCiudad", range(len(cand)),
                         format_func=lambda k: cand[k]["texto"])
    with cc[1]:
        analizar = st.button("Analizar esta dirección", type="primary", width="stretch")
    st.caption("La dirección se envía a CartoCiudad para situarla y no se guarda. "
               + ATRIBUCION_CARTOCIUDAD)
    if analizar:
        try:
            xy = coordenadas(cand[i])
        except Exception:
            xy = None
        if xy:
            elegir_punto(*xy)
            st.session_state.pop("candidatos", None)
            st.rerun()
        else:
            st.error("CartoCiudad no ha devuelto la posición de esa dirección.")

st.markdown(f"<div class='aviso'>⚠️ {AVISO}</div>", unsafe_allow_html=True)

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


def atender_clic(salida: dict | None) -> None:
    clic = (salida or {}).get("last_clicked")
    if clic:
        nuevo = (round(clic["lat"], 6), round(clic["lng"], 6))
        if nuevo != st.session_state.get("ultimo_clic"):
            st.session_state["ultimo_clic"] = nuevo
            if nuevo != punto:
                elegir_punto(*nuevo)
                st.rerun()


if not res:
    st.info("Busca una dirección, prueba un ejemplo o haz clic en el mapa para elegir el "
            "punto.")
    atender_clic(mapa(None, None, None, alto=460))
else:
    rec, perfil, inf = res["rec"], res["perfil"], res["informe"]
    comp = bloque_inf(inf, "competencia")
    lugar = st.session_state.get("ejemplo") or "Punto elegido"
    st.markdown(f"<div class='donde'>📍 {html.escape(lugar)} · {muni['nombre']} · radio de "
                f"{S.RADIO_M} m · calculado en {dec(st.session_state['segundos'])} s</div>",
                unsafe_allow_html=True)
    st.markdown(f"<div class='titular'>{html.escape(titular(rec, inf))}</div>",
                unsafe_allow_html=True)
    tarjetas(rec, inf)

    # ------------------------------------------------- nivel 2: mapa y perfil por horas
    st.markdown("#### Dónde y cuándo")
    cm, cg = st.columns([1, 1.25], gap="medium")
    with cm:
        locs = locales_del_radio(*punto, muni["cod"])
        atender_clic(mapa(*punto, locs, alto=400))
        leyenda("Locales", [(n, COLOR_TIPO[t]) for t, n in S.TIPOS_COMPETENCIA.items()],
                f"<span>◯ radio de {S.RADIO_M} m</span>"
                f"<span>fuente: {comp['datos']['fuente_usada']}</span>")
        st.caption("Haz clic en el mapa para analizar otro punto.")
    with cg:
        dia_txt = st.segmented_control("Día", list(DIA_ETIQUETA), default="Laborable",
                                       label_visibility="collapsed", key="dia",
                                       help="El perfil no modela el domingo aparte.") \
            or "Laborable"
        grafico_perfil(perfil, rec, DIA_ETIQUETA[dia_txt])
        presentes = perfil["horas"].loc[DIA_ETIQUETA[dia_txt]][list(COLOR_CLIENTE)].sum()
        leyenda("Clientes", [(S.TIPOS_CLIENTE[t], c) for t, c in COLOR_CLIENTE.items()
                             if presentes[t] > 0],
                "<span>«punta»: horas punta</span>")

    # ------------------------------------------------------ nivel 3: pestañas
    st.markdown("#### Detalle")
    tabs = st.tabs(["Detalle de las recomendaciones", "Mercado", "Riesgos y avisos",
                    "Qué comprobar en persona", "Fuentes y licencias"])
    with tabs[0]:
        pestana_detalle(rec, perfil, dia_txt)
    with tabs[1]:
        bloques = inf["bloques"]
        for fila in range(0, len(bloques), 3):
            cols = st.columns(3, gap="small")
            for col, b in zip(cols, bloques[fila:fila + 3]):
                with col:
                    bloque_mercado(b)
    with tabs[2]:
        pestana_riesgos(rec, inf)
    with tabs[3]:
        pestana_comprobar(rec)
    with tabs[4]:
        pestana_fuentes(fu)

if not res:
    with st.expander("Fuentes y licencias"):
        pestana_fuentes(fu)

# --------------------------------------------------------------------- pie
st.markdown(
    "<div class='pie'>"
    "Powered by <a href='https://www.crtm.es'>CRTM</a> · "
    "© <a href='https://www.openstreetmap.org/copyright'>colaboradores de OpenStreetMap</a>"
    " (ODbL) · Direcciones: CartoCiudad, IGN · CC BY 4.0 "
    "<a href='https://www.scne.es/productos.html#CartoCiudad'>"
    "www.scne.es/productos.html#CartoCiudad</a> · "
    f"Datos del portal descargados el {fu['portal_descarga']} · "
    "Sin respaldo de las entidades que publican los datos · "
    "BARómetro, prototipo para DATAMAD 2026: orientación, no garantías"
    "</div>", unsafe_allow_html=True)
