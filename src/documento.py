"""BARómetro: documento descargable (PDF), listo para imprimir o enviar.

    from documento import informe_pdf, comparacion_pdf
    pdf = informe_pdf(res, lugar, fuentes)             # bytes
    pdf = comparacion_pdf(cmp, a, b, fuentes)          # bytes

No calcula nada: escribe en un PDF lo que ya devuelven recomendar(), informe_local(),
nivel_movimiento() y comparar(), con las mismas palabras que la aplicación (src/calle.py).

Se genera EN MEMORIA: no escribe ningún fichero ni guarda la dirección. No lleva nombres
de locales: la zona se dibuja como un esquema (el círculo de análisis, los locales por tipo
y las paradas), sin mapa de fondo ni rótulos.

Todo documento lleva, obligatoriamente (TEXTOS_OBLIGATORIOS): el aviso de orientación, las
fuentes con su licencia y su fecha, «Powered by CRTM», la atribución de OpenStreetMap y de
CartoCiudad y la nota de que ninguna entidad respalda el proyecto.

Usa fpdf2 (Python puro) y la letra DejaVu Sans (app/letra), que tiene los signos «≈», «×»
y «→» que usan los textos.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import MethodReturnValue, XPos, YPos

import supuestos as S
from calle import (COLOR_TIPO, FIABILIDAD, bloque_inf, comprobaciones_calle, dec,
                   grupos_horas, hora_de_grupo, horas_punta, metrica_bloque, miles,
                   redondo, respuestas, titular_calle)

RAIZ = Path(__file__).resolve().parent.parent
LETRA = RAIZ / "app" / "letra"
LOGO = RAIZ / "app" / "logo.svg"

AVISO = ("Esto es una orientación a partir de datos abiertos y supuestos explícitos, no una "
         "garantía. Toda cifra de personas es una estimación. Compruébalo siempre en persona "
         "antes de decidir.")
CRTM = ("Powered by CRTM (https://www.crtm.es). Los datos del Consorcio Regional de "
        "Transportes de Madrid se usan procesados, no en bruto.")
OSM = ("Locales, campus y mapa: © colaboradores de OpenStreetMap "
       "(https://www.openstreetmap.org/copyright), datos con licencia ODbL.")
CARTOCIUDAD = ("Direcciones: CartoCiudad, IGN · CC BY 4.0 · "
               "www.scne.es/productos.html#CartoCiudad")
NO_RESPALDO = ("Este proyecto no está respaldado ni patrocinado por ninguna de las entidades "
               "que publican los datos (Comunidad de Madrid, Ayuntamiento de Madrid, INE, "
               "IGN, CRTM, Fundación OpenStreetMap ni ninguna otra).")
# Lo que todo documento debe llevar (lo comprueba la prueba del registro).
TEXTOS_OBLIGATORIOS = ["no una garantía", "Fuentes y licencias", "Powered by CRTM",
                       "colaboradores de OpenStreetMap", "CartoCiudad, IGN · CC BY 4.0",
                       "no está respaldado ni patrocinado", "CC BY 4.0", "descargado el"]

TEJA, TEJA_SUAVE, TINTA, SUAVE, TENUE, BORDE = (
    "#9c3d1b", "#d6a585", "#1f1b16", "#5c5248", "#8a7f73", "#e8dfd3")
OCRE_FONDO, ARENA, AZUL = "#fdf3d7", "#f3efe8", "#2a78d6"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
PREGUNTAS = (("quien", "a_quien", "A quién"), ("cuando", "a_que_hora", "A qué hora"),
             ("que", "que_vender", "Qué vender"), ("precio", "a_que_precio", "A qué precio"))


def _rgb(c: str) -> tuple[int, int, int]:
    return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)


def _plano(t: str) -> str:
    """Texto sin Markdown ni HTML (los enlaces quedan como su texto)."""
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", str(t))
    t = re.sub(r"<[^>]+>", "", t)
    return t.replace("**", "").replace("`", "").strip()


def _fecha(iso: str) -> str:
    a, m, d = (int(x) for x in iso[:10].split("-"))
    return f"{d} de {MESES[m - 1]} de {a}"


class _Doc(FPDF):
    """Página A4 con cabecera de marca y pie con las atribuciones en todas las páginas."""

    def __init__(self, titulo: str):
        super().__init__(format="A4", unit="mm")
        self.titulo = titulo
        self.set_margins(17, 17, 17)
        self.set_auto_page_break(True, margin=17)
        self.add_font("dv", "", str(LETRA / "DejaVuSans.ttf"))
        self.add_font("dv", "B", str(LETRA / "DejaVuSans-Bold.ttf"))
        self.set_title(titulo)
        self.set_author("BARómetro")
        self.set_creator("BARómetro (datos abiertos de la Comunidad de Madrid)")
        self.set_lang("es")
        self.add_page()

    # ---- ayudas
    @property
    def ancho(self) -> float:
        return self.w - self.l_margin - self.r_margin

    def letra(self, pt: float, negrita: bool = False, color: str = TINTA) -> None:
        self.set_font("dv", "B" if negrita else "", pt)
        self.set_text_color(*_rgb(color))

    def footer(self) -> None:
        self.set_y(-12)
        self.letra(6.5, color=TENUE)
        self.cell(0, 4, "BARómetro · Orientación, no garantía · Powered by CRTM · © colaboradores "
                        "de OpenStreetMap · CartoCiudad, IGN · CC BY 4.0", align="L")
        self.set_y(-12)
        self.cell(0, 4, f"{self.page_no()}", align="R")

    def cabe(self, alto: float) -> None:
        """Salta de página si el bloque que viene no cabe entero."""
        if self.get_y() + alto > self.h - self.b_margin:
            self.add_page()

    def texto(self, t: str, pt: float = 9, negrita: bool = False, color: str = TINTA,
              ancho: float = 0, alto: float | None = None, x: float | None = None) -> None:
        self.letra(pt, negrita, color)
        if x is not None:
            self.set_x(x)
        self.multi_cell(ancho, alto or pt * 0.48, _plano(t), new_x=XPos.LMARGIN,
                        new_y=YPos.NEXT, align="L")

    def alto_texto(self, t: str, pt: float, ancho: float, negrita: bool = False) -> float:
        self.letra(pt, negrita)
        return self.multi_cell(ancho, pt * 0.48, _plano(t), dry_run=True,
                               output=MethodReturnValue.HEIGHT)

    def seccion(self, t: str, alto: float = 22) -> None:
        """Título de sección. `alto` es lo que ocupa con su primer bloque: si no cabe, la
        sección empieza en la página siguiente (un título no se queda solo al pie)."""
        self.cabe(alto)
        self.ln(4)
        y = self.get_y()
        self.set_fill_color(*_rgb(TEJA))
        self.rect(self.l_margin, y + 0.6, 1.4, 5.2, style="F")
        self.set_x(self.l_margin + 3.5)
        self.letra(13, True)
        self.cell(0, 6.4, t, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1.5)

    def vinetas(self, items: list[str], pt: float = 8.5, color: str = SUAVE,
                numeradas: bool = False) -> None:
        for i, it in enumerate(items, 1):
            self.cabe(self.alto_texto(it, pt, self.ancho - 6) + 1)
            y = self.get_y()
            self.letra(pt, color=color)
            self.set_x(self.l_margin + 1)
            self.cell(5, pt * 0.48, f"{i}." if numeradas else "•")
            self.set_xy(self.l_margin + 6, y)
            self.multi_cell(self.ancho - 6, pt * 0.48, _plano(it), new_x=XPos.LMARGIN,
                            new_y=YPos.NEXT, align="L")
            self.ln(0.8)

    def caja(self, t: str, fondo: str = OCRE_FONDO, pt: float = 8.5) -> None:
        alto = self.alto_texto(t, pt, self.ancho - 8) + 5
        self.cabe(alto + 2)
        y = self.get_y()
        self.set_fill_color(*_rgb(fondo))
        self.rect(self.l_margin, y, self.ancho, alto, style="F", round_corners=True,
                  corner_radius=2)
        self.set_xy(self.l_margin + 4, y + 2.5)
        self.letra(pt)
        self.multi_cell(self.ancho - 8, pt * 0.48, _plano(t), new_x=XPos.LMARGIN,
                        new_y=YPos.NEXT, align="L")
        self.set_y(y + alto + 2.5)

    def etiqueta(self, t: str) -> None:
        self.letra(7, True, TENUE)
        self.cell(0, 4, t.upper(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def marca(self, subtitulo: str, lineas: list[str]) -> None:
        """Cabecera de la primera página: logotipo, nombre, título y datos del documento."""
        y = self.get_y()
        try:
            self.image(str(LOGO), x=self.l_margin, y=y, w=11)
        except Exception:       # sin el dibujo, un cuadrado del color de la marca
            self.set_fill_color(*_rgb(TEJA))
            self.rect(self.l_margin, y, 11, 11, style="F", round_corners=True,
                      corner_radius=2.5)
        self.set_xy(self.l_margin + 14, y + 0.5)
        self.letra(17, True)
        self.cell(0, 6.5, "BARómetro", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_x(self.l_margin + 14)
        self.letra(8.5, color=SUAVE)
        self.cell(0, 4.5, subtitulo, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(5)
        for i, l in enumerate(lineas):
            self.texto(l, 13 if i == 0 else 8.5, i == 0, TINTA if i == 0 else SUAVE)
            self.ln(0.6)
        self.ln(2)
        self.caja(AVISO)

    # ---- dibujos
    def barras_horas(self, horas: list[float], punta: set[int], mejores: list[int],
                     x: float, y: float, w: float, h: float, titulo: str) -> None:
        """Gente por horas: una barra por hora; las horas punta, en el color de la marca."""
        self.set_xy(x, y)
        self.letra(8, True)
        self.cell(w, 4, titulo)
        y0, alto = y + 6, h - 12
        tope = max(max(horas), 1)
        self.set_draw_color(*_rgb(BORDE))
        self.set_line_width(0.15)
        for frac in (0.5, 1.0):
            yy = y0 + alto * (1 - frac)
            self.line(x + 9, yy, x + w, yy)
            self.set_xy(x, yy - 1.5)
            self.letra(6, color=TENUE)
            self.cell(8.5, 3, miles(tope * frac), align="R")
        paso = (w - 9) / 24
        for hh, v in enumerate(horas):
            self.set_fill_color(*_rgb(TEJA if hh in punta else TEJA_SUAVE))
            bh = alto * v / tope
            if bh > 0.05:
                self.rect(x + 9 + hh * paso + paso * 0.12, y0 + alto - bh, paso * 0.76, bh,
                          style="F")
            if hh in mejores:
                self.set_xy(x + 9 + hh * paso - 3, y0 + alto - bh - 3.6)
                self.letra(6.5, True)
                self.cell(paso + 6, 3, f"{hh} h", align="C")
            if hh % 3 == 0:
                self.set_xy(x + 9 + hh * paso - 2, y0 + alto + 0.8)
                self.letra(6, color=TENUE)
                self.cell(paso + 4, 3, f"{hh} h", align="C")
        self.line(x + 9, y0 + alto, x + w, y0 + alto)

    def lineas_horas(self, a: list[float], b: list[float], x: float, y: float, w: float,
                     h: float, titulo: str) -> None:
        """Dos curvas superpuestas: A en línea continua (teja) y B en discontinua (azul)."""
        self.set_xy(x, y)
        self.letra(8, True)
        self.cell(w, 4, titulo)
        y0, alto = y + 6, h - 12
        tope = max(max(a), max(b), 1)
        self.set_draw_color(*_rgb(BORDE))
        self.set_line_width(0.15)
        for frac in (0.5, 1.0):
            yy = y0 + alto * (1 - frac)
            self.line(x + 9, yy, x + w, yy)
            self.set_xy(x, yy - 1.5)
            self.letra(6, color=TENUE)
            self.cell(8.5, 3, miles(tope * frac), align="R")
        self.line(x + 9, y0 + alto, x + w, y0 + alto)
        paso = (w - 9) / 23
        for hh in range(0, 24, 3):
            self.set_xy(x + 9 + hh * paso - 4, y0 + alto + 0.8)
            self.cell(8, 3, f"{hh} h", align="C")
        for serie, color, raya in ((a, TEJA, None), (b, AZUL, (1.6, 1.0))):
            self.set_draw_color(*_rgb(color))
            self.set_line_width(0.55)
            if raya:
                self.set_dash_pattern(*raya)
            for hh in range(23):
                self.line(x + 9 + hh * paso, y0 + alto * (1 - serie[hh] / tope),
                          x + 9 + (hh + 1) * paso, y0 + alto * (1 - serie[hh + 1] / tope))
            self.set_dash_pattern()
        self.set_line_width(0.2)

    def forma(self, tipo: str, cx: float, cy: float, r: float) -> None:
        """La marca de un tipo de local: la misma forma y color que en el mapa."""
        self.set_fill_color(*_rgb(COLOR_TIPO.get(tipo, "#999999")))
        self.set_draw_color(255, 255, 255)
        self.set_line_width(0.2)
        if tipo == "restaurante":
            self.rect(cx - r * 0.85, cy - r * 0.85, r * 1.7, r * 1.7, style="DF")
        elif tipo == "cafeteria":
            self.polygon([(cx, cy - r), (cx + r, cy + r * 0.8), (cx - r, cy + r * 0.8)],
                         style="DF")
        elif tipo == "comida_rapida":
            self.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], style="DF")
        else:
            self.ellipse(cx - r, cy - r, 2 * r, 2 * r, style="DF")

    def esquema_zona(self, punto: tuple[float, float], locs, paradas, x: float, y: float,
                     lado: float) -> None:
        """Indicación de la zona, sin mapa de fondo ni nombres: el círculo de análisis, los
        locales por tipo y las paradas, con el norte arriba."""
        cx, cy, r = x + lado / 2, y + lado / 2, lado / 2 - 2
        esc = r / S.RADIO_M
        self.set_fill_color(*_rgb("#fbf6f0"))
        self.set_draw_color(*_rgb(TEJA))
        self.set_line_width(0.4)
        self.ellipse(cx - r, cy - r, 2 * r, 2 * r, style="DF")
        self.set_draw_color(*_rgb(BORDE))
        self.set_line_width(0.15)
        self.set_dash_pattern(0.8, 0.8)
        for f in (1 / 3, 2 / 3):
            self.ellipse(cx - r * f, cy - r * f, 2 * r * f, 2 * r * f, style="D")
        self.set_dash_pattern()
        lat0, lon0 = punto
        kx = 111320 * math.cos(math.radians(lat0))

        def xy(lat, lon):
            return cx + (lon - lon0) * kx * esc, cy - (lat - lat0) * 110540 * esc
        if paradas is not None:
            self.set_fill_color(255, 255, 255)
            self.set_draw_color(*_rgb("#3b342c"))
            self.set_line_width(0.25)
            for f in paradas.itertuples():
                px, py = xy(f.lat, f.lon)
                if math.hypot(px - cx, py - cy) <= r:
                    self.rect(px - 1, py - 1, 2, 2, style="DF", round_corners=True,
                              corner_radius=0.5)
        if locs is not None:
            for f in locs.itertuples():
                px, py = xy(f.lat, f.lon)
                if math.hypot(px - cx, py - cy) <= r + 0.5:
                    self.forma(f.tipo, px, py, 1.25)
        self.set_fill_color(*_rgb(TEJA))
        self.set_draw_color(255, 255, 255)
        self.set_line_width(0.5)
        self.ellipse(cx - 1.8, cy - 1.8, 3.6, 3.6, style="DF")
        self.letra(6, color=TENUE)
        self.set_xy(cx - 5, y - 2.2)
        self.cell(10, 3, "N", align="C")
        self.set_xy(x, y + lado - 0.5)
        self.cell(lado, 3, f"Círculo de {S.RADIO_M} m · anillos cada 100 m", align="C")


def _bloque_fuentes(d: _Doc, fu: dict) -> None:
    """Fuentes con licencia y fecha, y las atribuciones obligatorias."""
    d.seccion("Fuentes y licencias")
    d.texto(f"Portal de Datos Abiertos de la Comunidad de Madrid (datos.comunidad.madrid), "
            f"descargado el {fu['portal_descarga']}:", 8.5, True)
    d.ln(1)
    d.vinetas([f"{f['Conjunto']} · Licencia: {_plano(f['Licencia'])} (CC BY 4.0) · última "
               f"modificación {f['Última modificación']}" for f in fu["portal"]], 7.5)
    d.ln(1)
    d.texto("Otras fuentes:", 8.5, True)
    d.ln(1)
    d.vinetas([f"{e['titulo']} · Licencia: {_plano(e.get('Licencia', '?'))} · Datos: "
               f"{_plano(e.get('Versión de los datos', '?'))} · descargado el "
               f"{_plano(e.get('Fecha de descarga', '?'))}"
               for e in fu["externas"] + fu["aplicacion"]], 7.5)
    d.ln(1)
    d.cabe(40)
    d.etiqueta("Atribuciones")
    d.ln(0.5)
    for t in (CRTM, OSM, CARTOCIUDAD):
        d.texto(t, 8.5)
        d.ln(1)
    d.texto(NO_RESPALDO, 8.5, True)
    d.ln(2)
    d.caja(AVISO)


def _fiable(r: dict) -> str:
    return (f"Fiabilidad: {FIABILIDAD.get(r.get('confianza'), FIABILIDAD['baja'])[1].lower()} "
            f"(confianza {r.get('confianza', 'baja')}; {r.get('base', '')}).")


def informe_pdf(res: dict, lugar: str, fu: dict, punto: tuple[float, float] | None = None,
                locs=None, paradas=None) -> bytes:
    """El informe de un local, en PDF. `res` es {"perfil", "informe", "rec", "mov"}; `locs`
    y `paradas` (posición y tipo, sin nombres) solo sirven para el esquema de la zona."""
    rec, inf, perfil, mov = res["rec"], res["informe"], res["perfil"], res["mov"]
    resp = respuestas(rec, inf)
    d = _Doc("BARómetro: informe del local")
    d.marca("Informe del local · qué ofrecer, a quién, a qué hora y a qué precio",
            [lugar, f"{inf['municipio']['nombre']} · radio de análisis de {S.RADIO_M} m · "
                    f"informe del {_fecha(rec['fecha'])}"])

    d.seccion("Resumen")
    d.texto(titular_calle(rec, mov), 12.5, True, TEJA)
    d.ln(2)
    col = (d.ancho - 6) / 2
    y_fila = d.get_y()
    for i, t in enumerate(resp.values()):
        x = d.l_margin + (i % 2) * (col + 6)
        if i % 2 == 0:
            y_fila = d.get_y()
        d.set_xy(x, y_fila)
        d.letra(7.5, color=SUAVE)
        d.cell(col, 4, t["pregunta"], new_x=XPos.LEFT, new_y=YPos.NEXT)
        d.letra(10.5, True, TEJA)
        d.multi_cell(col, 5, t["respuesta"], new_x=XPos.LEFT, new_y=YPos.NEXT, align="L")
        d.letra(7.5, color=SUAVE)
        d.multi_cell(col, 3.8, (t["apoyo"] + ". " if t["apoyo"] else "")
                     + FIABILIDAD.get(t["rec"].get("confianza"), FIABILIDAD["baja"])[1] + ".",
                     new_x=XPos.LEFT, new_y=YPos.NEXT, align="L")
        if i % 2 == 0:
            y_izq = d.get_y()
        else:
            d.set_y(max(y_izq, d.get_y()) + 3)

    d.seccion("Nivel de movimiento")
    y = d.get_y()
    for i in range(5):      # cinco tramos, como la aguja; el del nivel, marcado
        d.set_fill_color(*_rgb(["#ecd9c9", "#e3b697", "#d48b5f", "#bb5d31", "#9c3d1b"][i]
                               if i < mov["nivel"] else "#eee7dd"))
        d.rect(d.l_margin + i * 11, y + 1, 10, 3.2, style="F")
    d.set_xy(d.l_margin + 59, y - 0.6)
    d.letra(12, True, TEJA)
    d.cell(0, 6, f"{mov['nombre']} (nivel {mov['nivel']} de 5)", new_x=XPos.LMARGIN,
           new_y=YPos.NEXT)
    d.ln(1.5)
    d.texto(f"≈{redondo(mov['pasos_laborable'])} personas pasan cerca en un día laborable "
            f"(estimación); {mov['frase']}.", 9)
    if mov["muy_poco_paso"]:
        d.ln(1.5)
        d.caja(mov["aviso"])

    d.seccion("Las cuatro respuestas")
    for clave, bloque, titulo in PREGUNTAS:
        t = resp[clave]
        r = t["rec"]
        d.cabe(30)
        d.etiqueta(titulo)
        d.texto(t["respuesta"], 11, True, TEJA)
        d.ln(0.8)
        d.texto(r["texto"], 8.8, True)
        d.ln(1)
        d.vinetas(r.get("porque", []))
        d.texto(_fiable(r), 8, color=SUAVE)
        d.ln(3.5)

    d.seccion("Gente por horas", 72)
    d.texto("Personas que pasan cerca cada hora (estimación). En color más oscuro, las horas "
            "con más gente. El sábado representa el fin de semana.", 8.5, color=SUAVE)
    d.ln(2)
    d.cabe(48)
    y = d.get_y()
    ancho = (d.ancho - 8) / 2
    for i, (dia, nombre) in enumerate((("laborable", "Día de diario"),
                                       ("fin_de_semana", "Sábado"))):
        horas = [float(v) for v in perfil["horas"].loc[dia]["total"]]
        mejores = [hora_de_grupo(rec, dia, g) for g in grupos_horas(rec, dia)[:2]]
        d.barras_horas(horas, set(horas_punta(rec, dia)), mejores,
                       d.l_margin + i * (ancho + 8), y, ancho, 42, nombre)
    d.set_y(y + 44)

    d.seccion("La zona", 82)
    d.cabe(64)
    y = d.get_y()
    lado = 56
    comp = bloque_inf(inf, "competencia")["datos"]
    if punto is not None:
        d.esquema_zona(punto, locs, paradas, d.l_margin, y + 2, lado)
    x2 = d.l_margin + lado + 8
    w2 = d.ancho - lado - 8
    d.set_xy(x2, y)
    d.letra(8.5, True)
    d.multi_cell(w2, 4.2, f"{comp['total']} bares y restaurantes a menos de {S.RADIO_M} m",
                 new_x=XPos.LEFT, new_y=YPos.NEXT, align="L")
    por_tipo = comp.get("comparacion_por_tipo", {})
    for tipo, nombre in S.TIPOS_COMPETENCIA.items():
        yy = d.get_y() + 0.8
        d.forma(tipo, x2 + 1.6, yy + 2, 1.4)
        d.set_xy(x2 + 5, yy)
        d.letra(8, color=SUAVE)
        d.cell(w2 - 5, 4, f"{nombre}: {por_tipo.get(tipo, {}).get('radio', 0)}",
               new_x=XPos.LEFT, new_y=YPos.NEXT)
    d.set_xy(x2, d.get_y() + 1.5)
    d.letra(7.5, color=TENUE)
    d.multi_cell(w2, 3.6, "Esquema sin mapa de fondo y sin nombres: el punto analizado en el "
                 "centro, los locales por tipo y, en blanco, las paradas de transporte. "
                 f"Fuente de los locales: {comp['fuente_usada']}.", new_x=XPos.LEFT,
                 new_y=YPos.NEXT)
    d.set_xy(x2, d.get_y() + 2)
    d.letra(8.5, True)
    d.multi_cell(w2, 4.2, f"Cómo se llega: {bloque_inf(inf, 'accesos')['datos']['nivel']}",
                 new_x=XPos.LEFT, new_y=YPos.NEXT, align="L")
    d.set_x(x2)
    d.letra(8, color=SUAVE)
    d.multi_cell(w2, 3.9, _plano(bloque_inf(inf, "accesos")["resumen"]), new_x=XPos.LEFT,
                 new_y=YPos.NEXT)
    d.set_y(max(d.get_y(), y + lado + 6))

    d.seccion("Mercado", 42)
    for b in inf["bloques"]:
        try:
            etq, valor, frase = metrica_bloque(b)
        except (KeyError, TypeError, ValueError, IndexError):
            etq, valor, frase = b["titulo"], "—", ""
        d.cabe(16)
        d.texto(f"{b['titulo']} ({b['caracter']})", 8.5, True)
        d.texto(f"{etq}: {valor}", 9.5, True, TEJA)
        if frase:
            d.texto(frase, 8, color=SUAVE)
        d.ln(2.2)

    d.seccion("Ojo con esto")
    for r in rec["riesgos"]:
        d.caja(r["texto"] + " " + _fiable(r),
               "#e6f3ea" if r.get("clave") == "ninguno" else OCRE_FONDO)

    d.seccion("Antes de decidir, compruébalo en persona")
    d.vinetas(comprobaciones_calle(rec), 9, TINTA, numeradas=True)

    _bloque_fuentes(d, fu)
    return bytes(d.output())


def comparacion_pdf(cmp: dict, a: dict, b: dict, fu: dict) -> bytes:
    """La comparación de dos locales (resultado de comparar()), en PDF."""
    na, nb = cmp["locales"]["a"], cmp["locales"]["b"]
    d = _Doc("BARómetro: comparación de dos locales")
    d.marca("Comparación de dos locales",
            [f"{na}  ·  {nb}",
             f"Radio de análisis de {S.RADIO_M} m en cada uno · informe del "
             f"{_fecha(a['rec']['fecha'])}"])
    d.seccion("Resumen")
    d.texto("Esta comparación no dice qué local es mejor: dice en qué se diferencian.", 8.5,
            color=SUAVE)
    d.ln(1.5)
    for frase in cmp["resumen"]:
        d.texto(frase, 9.5)
        d.ln(1.2)

    d.seccion("Aspecto por aspecto")
    col = (d.ancho - 6) / 2
    y_cab = y_fin = d.get_y()
    for i, (nombre, color) in enumerate(((na, TEJA), (nb, AZUL))):
        d.set_xy(d.l_margin + i * (col + 6), y_cab)
        d.letra(9, True, color)
        d.multi_cell(col, 4.4, ("A · " if i == 0 else "B · ") + nombre, align="L")
        y_fin = max(y_fin, d.get_y())
    d.set_y(y_fin + 2)
    for f in cmp["filas"]:
        lados = []
        for lado in ("a", "b"):
            c = f[lado]
            det = c["detalle"] + ("\n" + "\n".join("• " + t for t in c["lista"])
                                  if c.get("lista") else "")
            lados.append((c["titulo"], det))
        alto = max(d.alto_texto(t, 10, col, True) + (d.alto_texto(det, 7.8, col) if det else 0)
                   for t, det in lados) + d.alto_texto(f["veredicto"], 8.3, d.ancho - 6) + 14
        d.cabe(alto)
        d.set_draw_color(*_rgb(BORDE))
        d.set_line_width(0.2)
        d.line(d.l_margin, d.get_y(), d.w - d.r_margin, d.get_y())
        d.ln(2)
        d.etiqueta(f["aspecto"] + (f" · {f['fiabilidad_texto']}" if f["fiabilidad_texto"]
                                   else ""))
        y = d.get_y() + 0.5
        fin = y
        for i, (t, det) in enumerate(lados):
            x = d.l_margin + i * (col + 6)
            d.set_xy(x, y)
            d.letra(10, True, TEJA if f["mejor"] == "ab"[i] else TINTA)
            d.multi_cell(col, 4.8, ("▲ " if f["mejor"] == "ab"[i] else "") + t,
                         new_x=XPos.LEFT, new_y=YPos.NEXT, align="L")
            if det:
                d.letra(7.8, color=SUAVE)
                d.multi_cell(col, 3.75, _plano(det), new_x=XPos.LEFT, new_y=YPos.NEXT, align="L")
            fin = max(fin, d.get_y())
        d.set_y(fin + 1.2)
        d.texto("→ " + f["veredicto"], 8.3, True, TEJA if f["mejor"] else SUAVE)
        d.ln(2)
    d.texto("▲ marca el que sale mejor en ese aspecto. " + cmp["nota"], 7.5, color=TENUE)

    d.seccion("Gente por horas", 72)
    d.texto(f"Personas que pasan cerca cada hora (estimación). Línea continua: A · {na}. "
            f"Línea discontinua: B · {nb}.", 8.5, color=SUAVE)
    d.ln(2)
    d.cabe(48)
    y = d.get_y()
    ancho = (d.ancho - 8) / 2
    for i, (dia, nombre) in enumerate((("laborable", "Día de diario"),
                                       ("fin_de_semana", "Sábado"))):
        d.lineas_horas(cmp["personas_por_hora"]["a"][dia], cmp["personas_por_hora"]["b"][dia],
                       d.l_margin + i * (ancho + 8), y, ancho, 42, nombre)
    d.set_y(y + 44)

    _bloque_fuentes(d, fu)
    return bytes(d.output())
