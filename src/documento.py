"""BARómetro: documento descargable (PDF), listo para imprimir o enviar.

    from documento import informe_pdf, comparacion_pdf
    pdf = informe_pdf(res, lugar, fuentes)             # bytes
    pdf = comparacion_pdf(cmp, a, b, fuentes)          # bytes

No calcula nada: escribe en un PDF lo que ya devuelven recomendar(), informe_local(),
nivel_movimiento() y comparar(), con las mismas palabras que la aplicación (src/calle.py y,
para la ficha técnica, la metodología y la nota del contraste, src/metodologia.py).

Aspecto de informe técnico, como el Informe completo de la web: secciones numeradas (01,
02…), rótulos pequeños en mayúsculas, bordes finos y radios pequeños, números tabulares
(DejaVu Sans tiene todas las cifras del mismo ancho) y tablas con los números alineados a
la derecha.

Se genera EN MEMORIA: no escribe ningún fichero ni guarda la dirección. No lleva nombres
de locales: la zona se dibuja como un esquema (el círculo de análisis, los locales por tipo
con los mismos dibujos que el mapa de la web, y las paradas), sin mapa de fondo ni rótulos.

Todo documento lleva, obligatoriamente (TEXTOS_OBLIGATORIOS): el aviso de orientación, las
fuentes con su licencia y su fecha, «Powered by CRTM», la atribución de OpenStreetMap y de
CartoCiudad y la nota de que ninguna entidad respalda el proyecto.

Usa fpdf2 (Python puro; dibuja los SVG como vectores) y la letra DejaVu Sans (app/letra),
que tiene los signos «≈», «×», «→» y «ᵉ» que usan los textos.
"""

from __future__ import annotations

import io
import math
import re
from functools import lru_cache
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import MethodReturnValue, XPos, YPos
from fpdf.fonts import FontFace

import supuestos as S
from calle import (COLOR_TIPO, FIABILIDAD, bloque_inf, comprobaciones_calle, estable,
                   frases_cuando, grupos_horas, hora_de_grupo, horas_punta,
                   marca_tipo, metrica_bloque, miles, redondo, respuestas, titular_calle)
from metodologia import (AVISO_AFOROS, FUENTE_PERFIL, filas_ficha, filas_metodologia,
                         formula_mercado, version_codigo)

RAIZ = Path(__file__).resolve().parent.parent
LETRA = RAIZ / "app" / "letra"
LOGO = RAIZ / "app" / "logo.svg"

AVISO = ("Esto es una orientación a partir de datos abiertos y supuestos explícitos, no una "
         "garantía. Toda cifra de personas es una estimación. Compruébalo siempre en persona "
         "antes de decidir.")
CRTM = ("Powered by CRTM (crtm.es). Los datos del Consorcio Regional de Transportes de "
        "Madrid se usan procesados, no en bruto.")
OSM = ("Locales, campus y mapa: © colaboradores de OpenStreetMap "
       "(openstreetmap.org/copyright), datos con licencia ODbL.")
CARTOCIUDAD = ("Direcciones: CartoCiudad, IGN · CC BY 4.0 · "
               "www.scne.es/productos.html#CartoCiudad")
NO_RESPALDO = ("Este proyecto no está respaldado ni patrocinado por ninguna de las entidades "
               "que publican los datos (Comunidad de Madrid, Ayuntamiento de Madrid, INE, "
               "IGN, CRTM, Fundación OpenStreetMap ni ninguna otra).")
ENLACES = {CRTM: "https://www.crtm.es", OSM: "https://www.openstreetmap.org/copyright",
           CARTOCIUDAD: "https://www.scne.es/productos.html#CartoCiudad"}
# Condiciones de uso que no caben en la tabla de fuentes: una línea cada una (el texto
# completo, con sus enlaces y fechas de revisión, está en docs/fuentes.md).
CONDICIONES = (
    ("CRTM", "mostrar «Powered by CRTM», citar al CRTM indicando si los datos están en bruto "
             "o procesados, conservar sus fechas y no sugerir que patrocina el proyecto."),
    ("INE", "reutilización libre citando «Fuente: Instituto Nacional de Estadística (INE)»."),
    ("CartoCiudad", "uso libre y gratuito, también comercial, citando la autoría "
                    "(CartoCiudad, IGN · CC BY 4.0); se consulta en el momento, no se "
                    "descarga."),
    ("Teselas de OpenStreetMap", "solo en el mapa de la web: atribución visible y sin "
                                 "descarga masiva, según la política de teselas de la "
                                 "Fundación OpenStreetMap; este documento no las usa."),
)
# Lo que todo documento debe llevar (lo comprueba la prueba del registro).
TEXTOS_OBLIGATORIOS = ["no una garantía", "Fuentes y licencias", "Powered by CRTM",
                       "colaboradores de OpenStreetMap", "CartoCiudad, IGN · CC BY 4.0",
                       "no está respaldado ni patrocinado", "CC BY 4.0", "descargado el"]

# Los colores de la web (app/estilo.css).
TEJA, TEJA_SUAVE, TINTA, SUAVE, TENUE, BORDE = (
    "#9c3d1b", "#d6a585", "#1f1b16", "#5c5248", "#6f655a", "#e8dfd3")
ARENA, CREMA, AZUL, OCRE_TINTA, VERDE = "#f3efe8", "#fbfaf7", "#2a78d6", "#5e4700", "#2f7d4f"
# Etiquetas de fiabilidad: fondo y tinta, como .conf-alta / .conf-media / .conf-baja.
COLOR_CONF = {"alta": ("#dcefdf", "#1b5427"), "media": ("#fbefc9", "#5e4700"),
              "baja": ("#f6dcda", "#7a1f1f")}
RADIO = 1.2         # mm: los 6 a 8 px de la web
LINEA = 0.25        # mm: el borde de 1 px
PREGUNTAS = (("quien", "A quién"), ("cuando", "A qué hora"), ("que", "Qué vender"),
             ("precio", "A qué precio"))

# Días de los gráficos por horas («fin_de_semana» es el sábado; ver supuestos.DIAS_PERFIL).
DIAS_PDF = (("laborable", "Día de diario"), ("fin_de_semana", "Sábado"),
            ("domingo", "Domingo"))


def _rgb(c: str) -> tuple[int, int, int]:
    return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)


def _plano(t: str) -> str:
    """Texto sin Markdown ni HTML (los enlaces quedan como su texto)."""
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", str(t))
    t = re.sub(r"<[^>]+>", "", t)
    return t.replace("**", "").replace("`", "").strip()


def _sin_marcas(t: str) -> str:
    """Texto que va en una tabla con negritas (markdown de fpdf2): se rompen las parejas de
    signos que fpdf2 leería como formato («**», «__», «--», «~~»)."""
    for m in ("**", "__", "--", "~~"):
        t = t.replace(m, m[0] + "​" + m[1])
    return t


@lru_cache(maxsize=None)
def _svg_tipo(tipo: str) -> bytes:
    """El dibujo del tipo de local, el mismo SVG que el mapa de la web."""
    return marca_tipo(tipo, 24).encode("utf-8")


class _Doc(FPDF):
    """Página A4 con cabecera de marca en la primera, una línea de cabecera en las demás y
    pie con las atribuciones y el número de página en todas."""

    def __init__(self, titulo: str, corto: str):
        super().__init__(format="A4", unit="mm")
        self.titulo, self.corto, self.n_sec = titulo, corto, 0
        self.set_margins(17, 19, 17)
        self.set_auto_page_break(True, margin=18)
        self.add_font("dv", "", str(LETRA / "DejaVuSans.ttf"))
        self.add_font("dv", "B", str(LETRA / "DejaVuSans-Bold.ttf"))
        self.set_title(titulo)
        self.set_author("BARómetro")
        self.set_creator("BARómetro (datos abiertos de la Comunidad de Madrid)")
        self.set_lang("es")
        self.alias_nb_pages()
        self.add_page()

    # ---- ayudas
    @property
    def ancho(self) -> float:
        return self.w - self.l_margin - self.r_margin

    def letra(self, pt: float, negrita: bool = False, color: str = TINTA) -> None:
        self.set_font("dv", "B" if negrita else "", pt)
        self.set_text_color(*_rgb(color))

    def raya(self, y: float, x0: float | None = None, x1: float | None = None,
             color: str = BORDE) -> None:
        self.set_draw_color(*_rgb(color))
        self.set_line_width(LINEA)
        self.line(self.l_margin if x0 is None else x0, y,
                  self.w - self.r_margin if x1 is None else x1, y)

    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_y(10)
        self.letra(6.8, color=TENUE)
        self.cell(0, 4, f"BARómetro · {self.corto}", align="L")
        self.set_y(10)
        self.cell(0, 4, "Informe técnico · orientación, no garantía", align="R")
        self.raya(14.6)
        self.set_y(self.t_margin)

    def footer(self) -> None:
        self.raya(self.h - 13.2)
        self.set_y(-12.4)
        self.letra(6.5, color=TENUE)
        self.cell(0, 4, "BARómetro · Orientación, no garantía · Powered by CRTM · © colaboradores "
                        "de OpenStreetMap · CartoCiudad, IGN · CC BY 4.0", align="L")
        self.set_y(-12.4)
        self.cell(0, 4, f"{self.page_no()} / {{nb}}", align="R")

    def cabe(self, alto: float) -> None:
        """Salta de página si el bloque que viene no cabe entero."""
        if self.get_y() + alto > self.h - self.b_margin:
            self.add_page()

    def texto(self, t: str, pt: float = 9, negrita: bool = False, color: str = TINTA,
              ancho: float = 0, alto: float | None = None, x: float | None = None,
              enlace: str = "") -> None:
        self.letra(pt, negrita, color)
        if x is not None:
            self.set_x(x)
        self.multi_cell(ancho, alto or pt * 0.48, _plano(t), new_x=XPos.LMARGIN,
                        new_y=YPos.NEXT, align="L", link=enlace)

    def alto_texto(self, t: str, pt: float, ancho: float, negrita: bool = False,
                   alto: float | None = None) -> float:
        self.letra(pt, negrita)
        return self.multi_cell(ancho, alto or pt * 0.48, _plano(t), dry_run=True,
                               output=MethodReturnValue.HEIGHT)

    def rotulo(self, t: str, color: str = TENUE, x: float | None = None,
               ancho: float = 0) -> None:
        """Rótulo pequeño en mayúsculas, con algo de espacio entre letras (.rotulo)."""
        self.letra(6.6, True, color)
        self.set_char_spacing(0.35)
        if x is not None:
            self.set_x(x)
        self.cell(ancho, 4, t.upper(), new_x=XPos.LEFT if x is not None else XPos.LMARGIN,
                  new_y=YPos.NEXT)
        self.set_char_spacing(0)

    def seccion(self, t: str, alto: float = 22) -> None:
        """Título de sección numerado (01, 02…) con una línea fina encima. `alto` es lo que
        ocupa con su primer bloque: si no cabe, la sección empieza en la página siguiente
        (un título no se queda solo al pie)."""
        self.n_sec += 1
        self.cabe(alto)
        self.ln(4)
        y = self.get_y()
        self.raya(y)
        self.set_xy(self.l_margin, y + 2.6)
        self.letra(10.5, True, TEJA)
        self.cell(10, 6.4, f"{self.n_sec:02d}")
        self.letra(13.5, True)
        self.cell(0, 6.4, t, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def fuente(self, t: str, tipo: str = "") -> None:
        """La línea pequeña y gris del final de cada sección («Fuente: …»)."""
        self.ln(1)
        self.texto(f"Fuente: {t}" + (f" · {tipo}" if tipo else ""), 6.8, color=TENUE)

    def vinetas(self, items: list[str], pt: float = 8.3, color: str = SUAVE,
                numeradas: bool = False) -> None:
        for i, it in enumerate(items, 1):
            self.cabe(self.alto_texto(it, pt, self.ancho - 7) + 1)
            y = self.get_y()
            if numeradas:
                self.letra(pt, True, TEJA)
            else:
                self.letra(pt, color=TENUE)
            self.set_x(self.l_margin)
            self.cell(6, pt * 0.48, f"{i:02d}" if numeradas else "–")
            self.set_xy(self.l_margin + 7, y)
            self.letra(pt, color=color)
            self.multi_cell(self.ancho - 7, pt * 0.48, _plano(it), new_x=XPos.LMARGIN,
                            new_y=YPos.NEXT, align="L")
            self.ln(0.9 if numeradas else 0.6)

    def caja(self, t: str, rotulo: str = "", color: str = TENUE, pt: float = 8.2,
             fondo: str | None = None, x: float | None = None,
             ancho: float | None = None) -> None:
        """Caja de borde fino y radio pequeño, con un rótulo opcional (aviso, nota…)."""
        x = self.l_margin if x is None else x
        ancho = self.ancho if ancho is None else ancho
        alto = self.alto_texto(t, pt, ancho - 7) + 5 + (4.6 if rotulo else 0)
        self.cabe(alto + 2)
        y = self.get_y()
        self.set_draw_color(*_rgb(BORDE))
        self.set_line_width(LINEA)
        if fondo:
            self.set_fill_color(*_rgb(fondo))
        self.rect(x, y, ancho, alto, style="DF" if fondo else "D", round_corners=True,
                  corner_radius=RADIO)
        self.set_xy(x + 3.5, y + 2.5)
        if rotulo:
            self.rotulo(rotulo, color, x=x + 3.5)
            self.set_xy(x + 3.5, y + 2.5 + 4.6)
        self.letra(pt, color=TINTA)
        self.multi_cell(ancho - 7, pt * 0.48, _plano(t), new_x=XPos.LMARGIN,
                        new_y=YPos.NEXT, align="L")
        self.set_y(y + alto + 2.5)

    def etiqueta(self, conf: str | None, texto: str, x: float, y: float) -> float:
        """Etiqueta rectangular de fiabilidad (.conf-alta / media / baja). Devuelve su ancho."""
        fondo, tinta = COLOR_CONF.get(conf or "baja", COLOR_CONF["baja"])
        self.letra(6.2, True, tinta)
        self.set_char_spacing(0.3)
        w = self.get_string_width(texto.upper()) + 3.2
        self.set_fill_color(*_rgb(fondo))
        self.rect(x, y, w, 4, style="F", round_corners=True, corner_radius=0.5)
        self.set_xy(x, y)
        self.cell(w, 4, texto.upper(), align="C")
        self.set_char_spacing(0)
        return w

    def linea_fiabilidad(self, r: dict) -> None:
        """La fiabilidad de una recomendación: etiqueta y, al lado, confianza y base."""
        self.cabe(6)
        y = self.get_y()
        conf = r.get("confianza", "baja")
        w = self.etiqueta(conf, FIABILIDAD.get(conf, FIABILIDAD["baja"])[1], self.l_margin, y)
        self.set_xy(self.l_margin + w + 2, y)
        self.letra(7.4, color=SUAVE)
        self.cell(0, 4, f"Confianza {conf} · {r.get('base', '')}", new_x=XPos.LMARGIN,
                  new_y=YPos.NEXT)

    def tabla(self, cabecera: list[str] | None, filas: list[list[str]], anchos: tuple,
              alinear: tuple | None = None, pt: float = 7.6, negrita: tuple = (),
              colores: dict | None = None, grupos: dict | None = None,
              markdown: bool = False, compacta: bool = False) -> None:
        """Tabla de líneas finas: cabecera en rótulo, columnas de números a la derecha
        («RIGHT» en `alinear`), `negrita` y `colores` por columna, y filas de grupo (una
        celda a todo el ancho) en `grupos` = {posición: texto}."""
        alinear = alinear or ("LEFT",) * len(anchos)
        colores = colores or {}
        grupos = grupos or {}
        self.set_draw_color(*_rgb(BORDE))
        self.set_line_width(LINEA)
        self.set_fill_color(255, 255, 255)
        self.letra(pt)
        pad = (0.9, 1.6, 0.9, 1.6) if compacta else (1.5, 1.8, 1.5, 1.8)
        cab = FontFace(family="dv", emphasis="BOLD", size_pt=6.4, color=_rgb(TENUE),
                       fill_color=_rgb(CREMA))
        with self.table(col_widths=anchos, text_align=alinear, v_align="TOP",
                        borders_layout="HORIZONTAL_LINES", line_height=pt * 0.47,
                        padding=pad, headings_style=cab, cell_fill_mode="NONE",
                        first_row_as_headings=bool(cabecera), markdown=markdown,
                        width=self.ancho) as t:
            if cabecera:
                fila = t.row()
                for c in cabecera:
                    fila.cell(c.upper())
            for i, f in enumerate(filas):
                if i in grupos:
                    t.row().cell(grupos[i], colspan=len(anchos), style=FontFace(
                        family="dv", emphasis="BOLD", size_pt=pt, color=_rgb(TINTA),
                        fill_color=_rgb(ARENA)))
                fila = t.row()
                for j, c in enumerate(f):
                    fila.cell(c, style=FontFace(
                        family="dv", emphasis="BOLD" if j in negrita else None,
                        size_pt=pt, color=_rgb(colores.get(j, TINTA))))
        self.ln(1.5)

    def marca(self, subtitulo: str, titulo: str, ficha: list[tuple[str, str]]) -> None:
        """Cabecera de la primera página: logotipo, nombre, título y ficha técnica."""
        y = self.get_y() - 4
        try:
            self.image(str(LOGO), x=self.l_margin, y=y, w=12)
        except Exception:       # sin el dibujo, un cuadrado del color de la marca
            self.set_fill_color(*_rgb(TEJA))
            self.rect(self.l_margin, y, 12, 12, style="F", round_corners=True,
                      corner_radius=RADIO)
        self.set_xy(self.l_margin + 15, y + 0.6)
        self.letra(18, True)
        self.cell(0, 7, "BARómetro", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_x(self.l_margin + 15)
        self.letra(8.2, color=SUAVE)
        self.cell(0, 4.4, subtitulo, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_xy(self.l_margin, y + 1.2)
        self.rotulo("Informe técnico", x=self.w - self.r_margin - 40, ancho=40)
        self.set_xy(self.w - self.r_margin - 60, y + 5.6)
        self.letra(7.4, color=SUAVE)
        self.cell(60, 4, "Datos abiertos de la Comunidad de Madrid", align="R")
        self.set_y(y + 16)
        self.raya(self.get_y(), color=TINTA)
        self.ln(5)
        self.texto(titulo, 15.5, True, alto=7)
        self.ln(3.5)
        self.rotulo("Ficha técnica")
        self.ln(0.5)
        self.tabla(None, [[k, v] for k, v in ficha], (30, 70), pt=8, negrita=(0,),
                   colores={0: SUAVE})
        self.ln(1)
        self.caja(AVISO, "Orientación, no garantía", pt=8)

    # ---- gráficos
    def _ejes(self, x: float, y0: float, w: float, alto: float, tope: float,
              eje_y: str) -> None:
        """Rejilla horizontal clara, cifras del eje y, marcas cada 3 horas y títulos de eje."""
        self.set_xy(x, y0 - 8.4)
        self.letra(5.8, color=TENUE)
        self.cell(w, 3, eje_y)
        for frac in (0.25, 0.5, 0.75, 1.0):
            yy = y0 + alto * (1 - frac)
            self.raya(yy, x + 9, x + w, "#efe8de")
            if frac in (0.5, 1.0):
                self.set_xy(x, yy - 1.5)
                self.letra(5.8, color=TENUE)
                self.cell(8.2, 3, miles(tope * frac), align="R")
        self.raya(y0 + alto, x + 9, x + w, TENUE)
        paso = (w - 9) / 24
        self.set_draw_color(*_rgb(TENUE))
        for hh in range(0, 25, 3):
            xx = x + 9 + hh * paso
            self.line(xx, y0 + alto, xx, y0 + alto + 0.8)
            if hh < 24:
                self.set_xy(xx - 3, y0 + alto + 1)
                self.letra(5.8, color=TENUE)
                self.cell(6, 2.8, f"{hh}", align="C")
        self.set_xy(x + 9, y0 + alto + 3.8)
        self.letra(5.8, color=TENUE)
        self.cell(w - 9, 2.8, "Hora del día", align="C")

    def barras_horas(self, horas: list[float], punta: set[int], mejores: list[int],
                     x: float, y: float, w: float, h: float, titulo: str,
                     eje_y: str = "Personas por hora (≈)") -> None:
        """Gente por horas: una barra por hora; las horas punta, en el color de la marca."""
        self.set_xy(x, y)
        self.letra(7.8, True)
        self.cell(w, 4, titulo)
        y0, alto = y + 13, h - 21
        tope = max(max(horas), 1)
        self._ejes(x, y0, w, alto, tope, eje_y)
        paso = (w - 9) / 24
        for hh, v in enumerate(horas):
            self.set_fill_color(*_rgb(TEJA if hh in punta else TEJA_SUAVE))
            bh = alto * v / tope
            if bh > 0.05:
                self.rect(x + 9 + hh * paso + paso * 0.14, y0 + alto - bh, paso * 0.72, bh,
                          style="F")
            if hh in mejores:
                self.set_xy(x + 9 + hh * paso - 3, y0 + alto - bh - 3.4)
                self.letra(6, True)
                self.cell(paso + 6, 3, f"{hh} h", align="C")

    def lineas_horas(self, a: list[float], b: list[float], x: float, y: float, w: float,
                     h: float, titulo: str) -> None:
        """Dos curvas superpuestas: A en línea continua (teja) y B en discontinua (azul)."""
        self.set_xy(x, y)
        self.letra(7.8, True)
        self.cell(w, 4, titulo)
        y0, alto = y + 13, h - 21
        tope = max(max(a), max(b), 1)
        self._ejes(x, y0, w, alto, tope, "Personas por hora (≈)")
        paso = (w - 9) / 24
        for serie, color, raya in ((a, TEJA, None), (b, AZUL, (1.6, 1.0))):
            self.set_draw_color(*_rgb(color))
            self.set_line_width(0.55)
            if raya:
                self.set_dash_pattern(*raya)
            for hh in range(23):
                self.line(x + 9 + (hh + 0.5) * paso, y0 + alto * (1 - serie[hh] / tope),
                          x + 9 + (hh + 1.5) * paso, y0 + alto * (1 - serie[hh + 1] / tope))
            self.set_dash_pattern()
        self.set_line_width(LINEA)

    def tres_graficos(self, series: list, titulo_dia, eje_y: str, h: float = 48) -> None:
        """Los tres días (diario, sábado, domingo) en fila. `series` da, por día, los
        argumentos de barras_horas."""
        self.cabe(h + 2)
        y = self.get_y()
        ancho = (self.ancho - 2 * 6) / 3
        for i, (dia, nombre) in enumerate(DIAS_PDF):
            horas, punta, mejores = series[i]
            self.barras_horas(horas, punta, mejores, self.l_margin + i * (ancho + 6), y,
                              ancho, h, titulo_dia(dia, nombre), eje_y)
        self.set_y(y + h + 1)

    def marca_local(self, tipo: str, cx: float, cy: float, d: float) -> None:
        """La marca de un tipo de local: el mismo dibujo y color que en el mapa de la web."""
        if tipo not in COLOR_TIPO:
            tipo = "bar"
        self.image(io.BytesIO(_svg_tipo(tipo)), x=cx - d / 2, y=cy - d / 2, w=d, h=d)

    def parada(self, cx: float, cy: float, d: float = 2.1) -> None:
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(*_rgb("#3b342c"))
        self.set_line_width(0.3)
        self.rect(cx - d / 2, cy - d / 2, d, d, style="DF", round_corners=True,
                  corner_radius=0.3)

    def punto_central(self, cx: float, cy: float, d: float = 3.6) -> None:
        self.set_fill_color(*_rgb(TEJA))
        self.set_draw_color(255, 255, 255)
        self.set_line_width(0.5)
        self.ellipse(cx - d / 2, cy - d / 2, d, d, style="DF")

    def esquema_zona(self, punto: tuple[float, float], locs, paradas, x: float, y: float,
                     lado: float) -> None:
        """Indicación de la zona, sin mapa de fondo ni nombres: el círculo de análisis, los
        locales por tipo (con sus dibujos) y las paradas, con el norte arriba."""
        cx, cy, r = x + lado / 2, y + lado / 2, lado / 2 - 2
        esc = r / S.RADIO_M
        self.set_fill_color(*_rgb(CREMA))
        self.set_draw_color(*_rgb(TEJA))
        self.set_line_width(0.35)
        self.ellipse(cx - r, cy - r, 2 * r, 2 * r, style="DF")
        self.set_draw_color(*_rgb(BORDE))
        self.set_line_width(0.2)
        self.set_dash_pattern(0.8, 0.8)
        for f in (1 / 3, 2 / 3):
            self.ellipse(cx - r * f, cy - r * f, 2 * r * f, 2 * r * f, style="D")
        self.line(cx - r, cy, cx + r, cy)
        self.line(cx, cy - r, cx, cy + r)
        self.set_dash_pattern()
        lat0, lon0 = punto
        kx = 111320 * math.cos(math.radians(lat0))

        def xy(lat, lon):
            return cx + (lon - lon0) * kx * esc, cy - (lat - lat0) * 110540 * esc
        if paradas is not None:
            for f in paradas.itertuples():
                px, py = xy(f.lat, f.lon)
                if math.hypot(px - cx, py - cy) <= r:
                    self.parada(px, py)
        if locs is not None:
            for f in locs.itertuples():
                px, py = xy(f.lat, f.lon)
                if math.hypot(px - cx, py - cy) <= r + 0.5:
                    self.marca_local(f.tipo, px, py, 3.4)
        self.punto_central(cx, cy)
        self.letra(6.2, True, TENUE)
        self.set_xy(cx - 5, y - 2.6)
        self.cell(10, 3, "N", align="C")
        self.letra(5.8, color=TENUE)
        for f in (1 / 3, 2 / 3, 1):
            self.set_xy(cx + r * f * 0.7071 + 0.4, cy + r * f * 0.7071 - 0.6)
            self.cell(10, 2.6, f"{round(S.RADIO_M * f)} m")
        self.set_xy(x, y + lado + 0.6)
        self.letra(6.4, color=TENUE)
        self.cell(lado, 3, f"Círculo de {S.RADIO_M} m · anillos cada 100 m · norte arriba",
                  align="C")


# ------------------------------------------------------------------- fuentes
def _licencia_corta(t: str) -> str:
    """El nombre de la licencia (lo que va antes de la primera explicación)."""
    m = re.match(r"\[([^\]]+)\]\(", t)
    if m:
        return m[1]
    corta = re.split(r"[.;:](?:\s|$)", _plano(t))[0]
    return corta[0].upper() + corta[1:]


def _datos_corto(t: str) -> str:
    """La versión de los datos en pocas palabras: la primera parte o, si son varios
    ficheros con su fecha cada uno, del primero al último."""
    t = _plano(t)
    fechas = sorted(set(re.findall(r"\d{4}-\d\d-\d\d", t)))
    if t.count(";") >= 2 and len(fechas) > 2:
        return f"Varios ficheros, del {fechas[0]} al {fechas[-1]}"
    corta = re.split(r";\s", t)[0]
    corta = re.sub(r"(\d{4}-\d\d-\d\d)T[\d:]+Z", r"\1", corta)
    return corta[0].upper() + corta[1:]


def _descarga_corta(t: str) -> str:
    t = _plano(t)
    return t if re.fullmatch(r"\d{4}-\d\d-\d\d", t) else \
        re.split(r" \(|;", t)[0].capitalize()


def _bloque_fuentes(d: _Doc, fu: dict) -> None:
    """Fuentes con licencia y fechas en una tabla, las condiciones en una línea cada una y
    las atribuciones obligatorias."""
    d.seccion("Fuentes y licencias", 40)
    usados = [f for f in fu["portal"] if f.get("En uso", True)]
    sin_uso = [f for f in fu["portal"] if not f.get("En uso", True)]
    d.texto(f"Portal de Datos Abiertos de la Comunidad de Madrid (datos.comunidad.madrid), "
            f"descargado el {fu['portal_descarga']}: {len(usados)} conjuntos en uso, todos "
            "con licencia CC BY 4.0. Las otras fuentes, con su licencia y sus fechas, van "
            "debajo; el detalle completo está en docs/fuentes.md.", 8, color=SUAVE)
    d.ln(2)
    filas, grupos = [], {0: "Portal de Datos Abiertos de la Comunidad de Madrid · "
                            "conjuntos en uso"}
    for f in usados:
        filas.append([f["Conjunto"], "CC BY 4.0", f["Última modificación"],
                      fu["portal_descarga"]])
    if sin_uso:
        grupos[len(filas)] = "Descargada, no se usa en los cálculos"
        for f in sin_uso:
            filas.append([f["Conjunto"], "CC BY 4.0", f["Última modificación"],
                          fu["portal_descarga"]])
    grupos[len(filas)] = "Otras fuentes"
    for e in fu["externas"] + fu["aplicacion"]:
        filas.append([e["titulo"], _licencia_corta(e.get("Licencia", "?")),
                      _datos_corto(e.get("Versión de los datos", "?")),
                      _descarga_corta(e.get("Fecha de descarga", "?"))])
    d.tabla(["Fuente", "Licencia", "Fecha de los datos", "Fecha de descarga"], filas,
            (50, 19, 17, 14), ("LEFT", "LEFT", "RIGHT", "RIGHT"), pt=6.8, grupos=grupos,
            colores={1: SUAVE}, compacta=True)
    d.ln(1)
    d.cabe(30)
    d.rotulo("Condiciones de uso")
    d.ln(0.5)
    for quien, cond in CONDICIONES:
        y = d.get_y()
        d.letra(7.4, True)
        w = d.get_string_width(quien + ": ") + 0.5
        d.cabe(4)
        d.cell(w, 3.6, quien + ":")
        d.set_xy(d.l_margin + w, y)
        d.letra(7.4, color=SUAVE)
        d.multi_cell(d.ancho - w, 3.6, cond, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
        d.ln(0.6)
    d.ln(2)
    d.cabe(40)
    d.rotulo("Atribuciones")
    d.ln(0.5)
    for t in (CRTM, OSM, CARTOCIUDAD):
        d.texto(t, 8.2, enlace=ENLACES[t])
        d.ln(1)
    d.texto(NO_RESPALDO, 8.2, True)
    d.ln(2.5)
    d.caja(AVISO, "Orientación, no garantía", pt=8)


# ------------------------------------------------------------------- informe
def _rejilla_respuestas(d: _Doc, resp: dict) -> None:
    """Las cuatro respuestas en cuadrícula de dos por dos, con borde fino."""
    hueco, pad = 4, 3.5
    col = (d.ancho - hueco) / 2
    dentro = col - 2 * pad
    cajas = list(resp.values())
    for fila in (cajas[:2], cajas[2:]):
        altos = []
        for t in fila:
            apoyo = t["apoyo"] + "." if t["apoyo"] else ""
            altos.append(4.6 + d.alto_texto(t["respuesta"], 11, dentro, True, 5)
                         + (d.alto_texto(apoyo, 7.6, dentro, alto=3.7) + 1 if apoyo else 0)
                         + 6.5)
        alto = max(altos) + 2 * pad - 2
        d.cabe(alto + hueco)
        y = d.get_y()
        for i, t in enumerate(fila):
            x = d.l_margin + i * (col + hueco)
            d.set_draw_color(*_rgb(BORDE))
            d.set_line_width(LINEA)
            d.rect(x, y, col, alto, style="D", round_corners=True, corner_radius=RADIO)
            d.set_xy(x + pad, y + pad)
            d.rotulo(t["pregunta"], x=x + pad, ancho=dentro)
            d.set_xy(x + pad, d.get_y() + 0.6)
            d.letra(11, True, TEJA)
            d.multi_cell(dentro, 5, t["respuesta"], new_x=XPos.LEFT, new_y=YPos.NEXT,
                         align="L")
            if t["apoyo"]:
                d.set_xy(x + pad, d.get_y() + 1)
                d.letra(7.6, color=SUAVE)
                d.multi_cell(dentro, 3.7, t["apoyo"] + ".", new_x=XPos.LEFT,
                             new_y=YPos.NEXT, align="L")
            conf = t["rec"].get("confianza", "baja")
            d.etiqueta(conf, FIABILIDAD.get(conf, FIABILIDAD["baja"])[1], x + pad,
                       y + alto - pad - 4)
        d.set_y(y + alto + hueco)


def _fiable(r: dict) -> str:
    return (f"Fiabilidad: {FIABILIDAD.get(r.get('confianza'), FIABILIDAD['baja'])[1].lower()} "
            f"(confianza {r.get('confianza', 'baja')}; {r.get('base', '')}).")


def _ficha(lugar: str, punto, municipio: str, rec: dict, fu: dict) -> list[tuple[str, str]]:
    return filas_ficha(lugar, punto, municipio, rec, fu["portal_descarga"], rec["fecha"],
                       version_codigo())


def informe_pdf(res: dict, lugar: str, fu: dict, punto: tuple[float, float] | None = None,
                locs=None, paradas=None) -> bytes:
    """El informe de un local, en PDF. `res` es {"perfil", "informe", "rec", "mov"}; `locs`
    y `paradas` (posición y tipo, sin nombres) solo sirven para el esquema de la zona."""
    rec, inf, perfil, mov = res["rec"], res["informe"], res["perfil"], res["mov"]
    resp = respuestas(rec, inf)
    tipo = rec.get("tipo_local")
    d = _Doc("BARómetro: informe del local", f"Informe del local · {lugar}")
    d.marca("¿Habrá negocio aquí? Mira los datos antes de firmar.", lugar,
            _ficha(lugar, punto, inf["municipio"]["nombre"], rec, fu))

    d.seccion("Resumen", 60)
    d.texto(titular_calle(rec, mov), 12.5, True, TEJA, alto=6)
    d.ln(2.5)
    if not tipo:
        d.caja(S.AVISO_GENERAL, "Resultado general", OCRE_TINTA)
    _rejilla_respuestas(d, resp)

    d.seccion("Nivel de movimiento", 30)
    y = d.get_y()
    for i in range(5):      # cinco tramos, como la aguja; el del nivel, marcado
        d.set_fill_color(*_rgb(["#ecd9c9", "#e3b697", "#d48b5f", "#bb5d31", "#9c3d1b"][i]
                               if i < mov["nivel"] else "#eee7dd"))
        d.rect(d.l_margin + i * 11, y + 1.4, 10.4, 3, style="F")
    d.set_xy(d.l_margin + 60, y)
    d.letra(12, True, TEJA)
    d.cell(d.get_string_width(mov["nombre"]) + 2, 6, mov["nombre"])
    d.letra(8.5, color=SUAVE)
    d.cell(0, 6, f"nivel {mov['nivel']} de 5", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    d.ln(2)
    d.tabla(["Indicador", "Valor", "Tipo"],
            [["Personas que pasan cerca en un día laborable",
              f"≈{redondo(mov['pasos_laborable'])}", "Estimación"]],
            (62, 20, 18), ("LEFT", "RIGHT", "LEFT"), pt=7.8, negrita=(1,),
            colores={1: TEJA, 2: SUAVE})
    d.texto(f"{mov['frase'][0].upper()}{mov['frase'][1:]}.", 8.3, color=SUAVE)
    if mov["muy_poco_paso"]:
        d.ln(1.5)
        d.caja(mov["aviso"], "Aviso", OCRE_TINTA)

    for clave, titulo in PREGUNTAS:
        t = resp[clave]
        r = t["rec"]
        d.seccion(titulo, 34)
        d.rotulo(t["pregunta"].strip("¿?"))
        d.texto(t["respuesta"], 12, True, TEJA, alto=5.8)
        d.ln(1)
        if clave == "cuando" and tipo:
            d.texto(" ".join(frases_cuando(rec)[:3]), 8.3, color=SUAVE)
            d.ln(1.5)
        if clave == "cuando":
            d.caja(AVISO_AFOROS, "Contraste con conteos reales", OCRE_TINTA, pt=7.8)
        d.ln(0.5)
        d.rotulo("Por qué")
        d.texto(r["texto"], 8.6, True)
        d.ln(1.2)
        d.vinetas(r.get("porque", []))
        d.ln(0.6)
        d.linea_fiabilidad(r)

    d.seccion("Perfil por horas", 84)
    d.rotulo("Gente que pasa")
    d.texto("Personas que pasan cerca cada hora (estimación). En color más oscuro, las horas "
            "con más gente. Cada gráfico tiene su propia escala. El domingo sirve también, "
            "de forma aproximada, para los festivos.", 8, color=SUAVE)
    d.ln(2.5)
    d.tres_graficos(
        [([float(v) for v in perfil["horas"].loc[dia]["total"]], set(horas_punta(rec, dia)),
          [hora_de_grupo(rec, dia, g) for g in grupos_horas(rec, dia)[:2]])
         for dia, _ in DIAS_PDF], lambda dia, nombre: nombre, "Personas por hora (≈)")
    d.fuente(FUENTE_PERFIL + ". Elaboración propia", "Estimación")

    if tipo:
        d.ln(3)
        d.cabe(76)
        d.rotulo("Clientes posibles")
        d.texto(f"Para {S.TIPOS_LOCAL_CORTO[tipo['clave']]}: {tipo['unidad']} (estimación). "
                "Los vecinos cuentan aunque no pasen por delante: van a propósito. En color más "
                "oscuro, las horas con más clientes. Los supuestos están en src/supuestos.py "
                "(«TIPO DE LOCAL»).", 8, color=SUAVE)
        d.ln(2.5)
        d.tres_graficos(
            [([float(v) for v in rec["clientes_por_hora"][dia]["total"]],
              set(horas_punta(rec, dia, True)),
              [hora_de_grupo(rec, dia, g, True) for g in grupos_horas(rec, dia, True)[:2]])
             for dia, _ in DIAS_PDF],
            lambda dia, nombre: nombre + ("" if estable(rec, dia) else " (cambia con poco)"),
            "Visitas posibles por hora (≈)")
        d.fuente(FUENTE_PERFIL + " y supuestos del tipo de local (src/supuestos.py). "
                 "Elaboración propia", "Estimación")

    _seccion_zona(d, inf, punto, locs, paradas)

    d.seccion("Mercado", 40)
    filas = []
    for b in inf["bloques"]:
        if b["clave"] == "accesos":        # cómo se llega: ya está en «La zona»
            continue
        try:
            etq, valor, frase = metrica_bloque(b)
        except (KeyError, TypeError, ValueError, IndexError):
            etq, valor, frase = b["titulo"], "—", ""
        filas.append([f"**{_sin_marcas(b['titulo'])}**\n{_sin_marcas(etq)}",
                      f"**{_sin_marcas(valor)}**", _sin_marcas(frase),
                      _sin_marcas(b["caracter"].capitalize())])
    d.tabla(["Indicador", "Valor", "Detalle", "Tipo"], filas, (36, 15, 37, 12),
            ("LEFT", "RIGHT", "LEFT", "LEFT"), pt=7.4, colores={1: TEJA, 2: SUAVE, 3: SUAVE},
            markdown=True)
    d.fuente("informe del local (src/informe_local.py) con los conjuntos de «Fuentes y "
             "licencias»", "Dato y estimación, según la fila")

    d.seccion("Riesgos y avisos", 26)
    for r in rec["riesgos"]:
        bien = r.get("clave") == "ninguno"
        d.caja(r["texto"] + " " + _fiable(r), "Sin novedad" if bien else "Aviso",
               VERDE if bien else OCRE_TINTA)

    d.seccion("Qué comprobar en persona", 30)
    d.texto("Antes de decidir, compruébalo en persona:", 8.6, True)
    d.ln(1.5)
    d.vinetas(comprobaciones_calle(rec), 8.6, TINTA, numeradas=True)

    _seccion_metodologia(d, rec, mov)
    _bloque_fuentes(d, fu)
    return bytes(d.output())


def _seccion_zona(d: _Doc, inf: dict, punto, locs, paradas) -> None:
    """La zona: el esquema a la izquierda; a la derecha, los locales por tipo (con los
    dibujos del mapa) en una tabla pequeña y cómo se llega (una sola vez)."""
    d.seccion("La zona", 86)
    y = d.get_y() + 1
    lado = 60
    comp = bloque_inf(inf, "competencia")["datos"]
    if punto is not None:
        d.esquema_zona(punto, locs, paradas, d.l_margin, y + 2.5, lado)
    x2 = d.l_margin + lado + 9
    w2 = d.ancho - lado - 9
    d.set_xy(x2, y)
    d.rotulo(f"Locales a menos de {S.RADIO_M} m", x=x2, ancho=w2)
    por_tipo = comp.get("comparacion_por_tipo", {})
    yy = d.get_y() + 0.8
    d.raya(yy, x2, x2 + w2)
    for tipo, nombre in S.TIPOS_COMPETENCIA.items():
        d.marca_local(tipo, x2 + 2.2, yy + 2.9, 4)
        d.set_xy(x2 + 6, yy + 0.8)
        d.letra(8, color=TINTA)
        d.cell(w2 - 20, 4.2, nombre)
        d.letra(8, True)
        d.cell(14, 4.2, f"{por_tipo.get(tipo, {}).get('radio', 0)}", align="R")
        yy += 5.8
        d.raya(yy, x2, x2 + w2)
    d.set_xy(x2 + 6, yy + 0.8)
    d.letra(8, True)
    d.cell(w2 - 20, 4.2, "Total")
    d.cell(14, 4.2, f"{comp['total']}", align="R")
    yy += 5.8
    d.raya(yy, x2, x2 + w2, TENUE)
    # Leyenda de lo demás: el punto analizado y las paradas.
    d.punto_central(x2 + 2.2, yy + 3.6, 2.8)
    d.set_xy(x2 + 6, yy + 1.6)
    d.letra(7.2, color=SUAVE)
    d.cell(26, 4, "Punto analizado")
    d.parada(x2 + 36, yy + 3.6)
    d.set_xy(x2 + 39, yy + 1.6)
    d.cell(w2 - 39, 4, "Parada de transporte")
    d.set_xy(x2, yy + 7.6)
    d.letra(7, color=TENUE)
    d.multi_cell(w2, 3.4, "Esquema sin mapa de fondo y sin nombres. Fuente de los locales: "
                 f"{comp['fuente_usada']}.", new_x=XPos.LEFT, new_y=YPos.NEXT, align="L")
    acc = bloque_inf(inf, "accesos")
    d.set_xy(x2, d.get_y() + 3)
    d.rotulo("Cómo se llega", x=x2, ancho=w2)
    d.set_x(x2)
    d.letra(9.5, True, TEJA)
    d.multi_cell(w2, 4.6, acc["datos"]["nivel"], new_x=XPos.LEFT, new_y=YPos.NEXT, align="L")
    d.set_xy(x2, d.get_y() + 0.6)
    d.letra(7.6, color=SUAVE)
    d.multi_cell(w2, 3.7, _plano(acc["resumen"]), new_x=XPos.LEFT, new_y=YPos.NEXT,
                 align="L")
    d.set_y(max(d.get_y(), y + lado + 7))
    d.fuente(f"{comp['fuente_usada']}; paradas del CRTM. Elaboración propia", "Dato")


def _seccion_metodologia(d: _Doc, rec: dict, mov: dict) -> None:
    """Metodología y supuestos clave: la misma tabla y la misma fórmula que el Informe
    completo de la web, leídas de src/supuestos.py sin cambiar nada."""
    d.seccion("Metodología y supuestos clave", 50)
    d.tabla(["Parámetro", "Valor", "De dónde sale"],
            [list(f) for f in filas_metodologia(rec, mov)], (25, 45, 30), pt=7.2,
            negrita=(0,), colores={2: SUAVE})
    d.ln(1)
    d.cabe(24)
    d.rotulo("Mercado potencial")
    d.ln(0.6)
    d.caja(formula_mercado("ᵉ"), fondo=CREMA, pt=8)
    d.texto("El resto de los supuestos, cada uno con su porqué, está en src/supuestos.py y en "
            "el README del repositorio.", 8, color=SUAVE)
    d.fuente("src/supuestos.py del repositorio, sin cambios", "Estimación")


# ---------------------------------------------------------------- comparación
def comparacion_pdf(cmp: dict, a: dict, b: dict, fu: dict) -> bytes:
    """La comparación de dos locales (resultado de comparar()), en PDF."""
    na, nb = cmp["locales"]["a"], cmp["locales"]["b"]
    d = _Doc("BARómetro: comparación de dos locales", f"Comparación · {na} · {nb}")
    rec = a["rec"]
    ficha = _ficha("", None, "", rec, fu)
    ficha = ([("Local A", na), ("Local B", nb)]
             + [f for f in ficha if f[0] not in ("Punto analizado", "Municipio")])
    ficha.insert(2, ("Radio de análisis", ficha.pop(2)[1] + " en cada uno"))
    d.marca("¿Habrá negocio aquí? · Comparación de dos locales", f"{na}  ·  {nb}", ficha)

    d.seccion("Resumen", 40)
    d.texto("Esta comparación no dice qué local es mejor: dice en qué se diferencian.", 8.3,
            color=SUAVE)
    d.texto((f"Tipo de local: {cmp['tipo_local']['nombre']}." if cmp.get("tipo_local") else
             S.AVISO_GENERAL), 8.3, color=SUAVE)
    d.ln(2)
    for frase in cmp["resumen"]:
        d.cabe(8)
        y = d.get_y()
        d.set_fill_color(*_rgb(TEJA))
        d.rect(d.l_margin, y + 1.2, 1.1, 1.1, style="F")
        d.texto(frase, 9.3, x=d.l_margin + 4, ancho=d.ancho - 4)
        d.ln(1.4)

    d.seccion("Aspecto por aspecto", 46)
    col = (d.ancho - 6) / 2
    y_cab = y_fin = d.get_y()
    for i, (nombre, color) in enumerate(((na, TEJA), (nb, AZUL))):
        x = d.l_margin + i * (col + 6)
        d.set_fill_color(*_rgb(color))
        d.rect(x, y_cab + 0.3, 4.2, 4.2, style="F", round_corners=True, corner_radius=0.5)
        d.set_xy(x, y_cab + 0.3)
        d.letra(7.5, True, "#ffffff")
        d.cell(4.2, 4.2, "AB"[i], align="C")
        d.set_xy(x + 6, y_cab)
        d.letra(9, True, color)
        d.multi_cell(col - 6, 4.6, nombre, align="L")
        y_fin = max(y_fin, d.get_y())
    d.set_y(y_fin + 2)
    for f in cmp["filas"]:
        lados = []
        for lado in ("a", "b"):
            c = f[lado]
            det = c["detalle"] + ("\n" + "\n".join("– " + t for t in c["lista"])
                                  if c.get("lista") else "")
            lados.append((c["titulo"], det))
        alto = max(d.alto_texto(t, 10, col, True, 4.8)
                   + (d.alto_texto(det, 7.6, col, alto=3.7) if det else 0)
                   for t, det in lados) + d.alto_texto(f["veredicto"], 8.2, d.ancho - 6) + 15
        d.cabe(alto)
        d.raya(d.get_y())
        d.ln(2)
        d.rotulo(f["aspecto"] + (f" · {f['fiabilidad_texto']}" if f["fiabilidad_texto"]
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
                d.letra(7.6, color=SUAVE)
                d.multi_cell(col, 3.7, _plano(det), new_x=XPos.LEFT, new_y=YPos.NEXT, align="L")
            fin = max(fin, d.get_y())
        d.set_y(fin + 1.4)
        d.texto("→ " + f["veredicto"], 8.2, True, TEJA if f["mejor"] else SUAVE)
        d.ln(2.2)
    d.raya(d.get_y())
    d.ln(1.5)
    d.texto("▲ marca el que sale mejor en ese aspecto. " + cmp["nota"], 7.2, color=TENUE)

    d.seccion("Perfil por horas", 76)
    d.rotulo("Gente que pasa")
    d.texto(f"Personas que pasan cerca cada hora (estimación). Línea continua: A · {na}. "
            f"Línea discontinua: B · {nb}.", 8, color=SUAVE)
    d.ln(2.5)
    d.cabe(50)
    y = d.get_y()
    ancho = (d.ancho - 2 * 6) / 3
    for i, (dia, nombre) in enumerate(DIAS_PDF):
        d.lineas_horas(cmp["personas_por_hora"]["a"][dia], cmp["personas_por_hora"]["b"][dia],
                       d.l_margin + i * (ancho + 6), y, ancho, 48, nombre)
    d.set_y(y + 49)
    d.fuente(FUENTE_PERFIL + ". Elaboración propia", "Estimación")

    _bloque_fuentes(d, fu)
    return bytes(d.output())
