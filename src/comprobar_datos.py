"""BARómetro: comprobación de calidad de los datos procesados.

Mira los ficheros de datos/procesados que el repositorio publica y se detiene (código de
salida 1) si algo se sale de lo esperado:

  1. Filas: cada capa tiene un número de filas dentro de un margen razonable.
  2. Columnas y contenido prohibidos: ninguna columna de nombres, teléfonos, correos,
     direcciones postales o NIF, y ningún correo ni teléfono dentro de los textos.
  3. Población: el total de las secciones censales cuadra (con la referencia, entre
     ficheros y sin secciones repetidas).
  4. Transporte: las seis redes tienen paradas, líneas y servicio en laborable y en sábado.
  5. Mapa: todos los puntos caen dentro de la Comunidad de Madrid (con margen).

No cambia ningún dato. Lo usa el flujo de GitHub Actions que actualiza los datos cada
semana (.github/workflows/actualizar-datos.yml) antes de proponer los cambios, y se puede
ejecutar a mano:

    python src/comprobar_datos.py                 # comprueba datos/procesados
    python src/comprobar_datos.py --dir OTRA      # comprueba otra carpeta de procesados
    python src/comprobar_datos.py --markdown      # el informe, como tabla en Markdown

Si una comprobación falla porque la fuente ha cambiado de verdad (por ejemplo, un censo
nuevo con más población), hay que mirar el dato y, si es correcto, cambiar aquí la
referencia a mano: es una decisión de quien revisa, no del flujo.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
PROC = RAIZ / "datos" / "procesados"

# ----------------------------------------------------------------------- 1. filas
# Fichero → (mínimo, máximo) de filas. Entre paréntesis, las filas a 2026-11-12. Los márgenes
# son anchos donde la fuente crece sola (el IPC añade filas cada mes; la demografía de 2026,
# cada trimestre) y estrechos donde no debería cambiar (las secciones censales cambian una
# vez al año, y poco).
FILAS = {
    "secciones_censales.parquet": (4_400, 4_650),                 # 4.518
    "referencia_movimiento.parquet": (4_400, 4_650),              # 4.518
    "centros_educativos_alumnos.parquet": (3_400, 4_300),         # 3.851
    "centros_sanitarios.parquet": (13_500, 18_000),               # 15.737
    "desfibriladores_horario.parquet": (2_700, 3_900),            # 3.258
    "hosteleria_madrid_capital.parquet": (15_000, 19_500),        # 17.143
    "hosteleria_osm.parquet": (13_000, 18_500),                   # 15.665
    "campus_universitarios.parquet": (70, 130),                   # 98
    "salidas_paradas.parquet": (13_500, 17_000),                  # 15.207
    "lineas_paradas.parquet": (30_000, 43_000),                   # 36.484
    "informe/alojamientos_turisticos.csv": (6_500, 10_500),       # 8.335
    "informe/viviendas_uso_turistico.csv": (800, 1_800),          # 1.164
    "informe/festivos_locales.csv": (250, 430),                   # 338
    "informe/festivos_regionales.csv": (8, 16),                   # 12
    "informe/demografia_cnae09.csv": (6_000, 7_000),              # 6.432 (serie cerrada)
    "informe/demografia_cnae25.csv": (150, 2_500),                # 192 (crece cada trimestre)
    "informe/ipc.csv": (24_000, 60_000),                          # 26.355 (crece cada mes)
    "informe/gasto_restauracion.csv": (8, 40),                    # 10
}
# Ficheros que no son tablas, pero tienen que estar.
OTROS = ("salidas_paradas_dias.json", "informe/fuentes.json")

# ------------------------------------------------- 2. columnas y contenido prohibidos
# Una columna se rechaza si alguna de las palabras de su nombre (separadas por «_») es una de
# estas, o si el nombre contiene «razon_social» o «e_mail»…
PROHIBIDAS = {"nombre", "nombres", "name", "apellido", "apellidos", "titular", "rotulo",
              "denominacion", "telefono", "telefonos", "tlf", "tel", "movil", "fax", "email",
              "correo", "mail", "web", "url", "nif", "cif", "dni", "direccion", "domicilio",
              "contacto", "responsable", "director", "propietario"}
PROHIBIDAS_SEGUIDAS = ("razon_social", "e_mail")
# … salvo estas, que son nombres de municipios o de universidades, no de personas ni de
# locales.
PERMITIDAS = {"municipio_nombre", "entidad_nombre", "nombre_universidad"}
CORREO = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# Teléfono español: nueve cifras que empiezan por 6, 7, 8 o 9, con o sin prefijo y separadores.
TELEFONO = re.compile(r"(?<![\d.,])(?:\+34|0034)?[ ]?[6-9]\d{2}[ .-]?\d{3}[ .-]?\d{3}(?![\d.,])")
# Columnas de identificadores y códigos: pueden tener nueve cifras sin ser un teléfono.
IDENTIFICADORES = re.compile(r"^(osm_ids?|id_.*|.*_id|codigo.*|cod_.*|cdg.*|cdpostal|"
                             r"centro_nro_registro|municipio_codigo|entidad_codigo)$")

# -------------------------------------------------------------------- 3. población
POBLACION_REFERENCIA = 6_995_318     # INE, Atlas de renta, datos de 2024
POBLACION_MARGEN = 0.03              # ±3 %: más que eso en un año no es creíble
MUNICIPIOS = 179

# ------------------------------------------------------------------- 4. transporte
# Red → mínimo de paradas con servicio (la mitad, más o menos, de las de 2026-11-12: menos
# que eso es señal de un fichero de horarios cortado).
REDES = {"metro": 145, "metro_ligero": 28, "cercanias": 46, "emt": 2_400,
         "urbanos": 1_500, "interurbanos": 3_300}

# ------------------------------------------------------------------------ 5. mapa
# Caja que contiene la Comunidad de Madrid, con unos 10 km de margen. Las paradas tienen una
# caja más ancha: los autobuses interurbanos del Consorcio llegan a pueblos de Toledo,
# Cuenca, Guadalajara, Ávila y Segovia (a 2026-11-12, seis paradas fuera de la caja estrecha).
LAT = (39.75, 41.30)
LON = (-4.75, -2.90)
CAJA_ANCHA = {"salidas_paradas.parquet": ((39.30, 41.60), (-5.30, -2.40))}


def miles(n: float) -> str:
    return f"{n:,.0f}".replace(",", ".")


def leer(ruta: Path) -> pd.DataFrame:
    if ruta.suffix == ".parquet":
        return pd.read_parquet(ruta)
    return pd.read_csv(ruta, sep=";", dtype=str)   # todos los CSV del informe usan «;»


class Informe:
    """Lista de comprobaciones con su resultado."""

    def __init__(self) -> None:
        self.filas: list[tuple[bool, str, str]] = []

    def anotar(self, bien: bool, que: str, detalle: str) -> bool:
        self.filas.append((bool(bien), que, detalle))
        return bool(bien)

    @property
    def fallos(self) -> int:
        return sum(1 for bien, _, _ in self.filas if not bien)


def comprobar_filas(d: Path, tablas: dict[str, pd.DataFrame], inf: Informe) -> None:
    for nombre, (minimo, maximo) in FILAS.items():
        ruta = d / nombre
        if not ruta.exists():
            inf.anotar(False, f"Filas de {nombre}", "el fichero no existe")
            continue
        try:
            t = tablas[nombre] = leer(ruta)
        except Exception as e:   # un fichero cortado o corrupto también es un fallo
            inf.anotar(False, f"Filas de {nombre}", f"no se puede leer: {e}")
            continue
        inf.anotar(minimo <= len(t) <= maximo, f"Filas de {nombre}",
                   f"{miles(len(t))} (se esperan entre {miles(minimo)} y {miles(maximo)})")
    for nombre in OTROS:
        ruta = d / nombre
        try:
            vacio = not json.loads(ruta.read_text(encoding="utf-8"))
            inf.anotar(not vacio, f"Fichero {nombre}", "vacío" if vacio else "presente")
        except (OSError, ValueError) as e:
            inf.anotar(False, f"Fichero {nombre}", f"falta o no se puede leer: {e}")


def comprobar_prohibidos(tablas: dict[str, pd.DataFrame], inf: Informe) -> None:
    malas, correos, telefonos = [], [], []
    for nombre, t in tablas.items():
        for col in t.columns:
            c = str(col).lower()
            if c not in PERMITIDAS and (PROHIBIDAS & set(re.split(r"[^a-z0-9ñ]+", c))
                                        or any(x in c for x in PROHIBIDAS_SEGUIDAS)):
                malas.append(f"{nombre}: {col}")
            if c == "geometry" or not (t[col].dtype == object or str(t[col].dtype) in
                                       ("str", "string")):
                continue
            textos = t[col].dropna()
            textos = textos[textos.map(lambda v: isinstance(v, str))]
            if textos.empty:
                continue
            if textos.str.contains(CORREO).any():
                correos.append(f"{nombre}: {col}")
            if not IDENTIFICADORES.match(c) and textos.str.contains(TELEFONO).any():
                telefonos.append(f"{nombre}: {col}")
    inf.anotar(not malas, "Columnas prohibidas (nombres, teléfonos, correos…)",
               "; ".join(malas) or "ninguna")
    inf.anotar(not correos, "Correos dentro de los textos", "; ".join(correos) or "ninguno")
    inf.anotar(not telefonos, "Teléfonos dentro de los textos",
               "; ".join(telefonos) or "ninguno")


def comprobar_poblacion(tablas: dict[str, pd.DataFrame], inf: Informe) -> None:
    s = tablas.get("secciones_censales.parquet")
    if s is None or "poblacion" not in s:
        inf.anotar(False, "Población total", "no hay secciones censales con población")
        return
    total = float(s["poblacion"].sum())
    desvio = total / POBLACION_REFERENCIA - 1
    inf.anotar(abs(desvio) <= POBLACION_MARGEN, "Población total de las secciones",
               f"{miles(total)} ({100 * desvio:+.2f} % respecto a "
               f"{miles(POBLACION_REFERENCIA)}; margen ±{100 * POBLACION_MARGEN:.0f} %)")
    malas = int((s["poblacion"].isna() | (s["poblacion"] < 0)).sum())
    inf.anotar(malas == 0, "Secciones sin población o con población negativa", str(malas))
    repetidas = int(s["cdgseccion"].duplicated().sum())
    inf.anotar(repetidas == 0, "Secciones censales repetidas", str(repetidas))
    municipios = int(s["cod_municipio"].nunique())
    inf.anotar(municipios == MUNICIPIOS, "Municipios con secciones",
               f"{municipios} (se esperan {MUNICIPIOS})")
    r = tablas.get("referencia_movimiento.parquet")
    if r is not None and "poblacion" in r:
        total_r = float(r["poblacion"].sum())
        inf.anotar(total_r == total and len(r) == len(s),
                   "La referencia de movimiento cuadra con las secciones",
                   f"{miles(total_r)} personas en {miles(len(r))} sitios, frente a "
                   f"{miles(total)} en {miles(len(s))} secciones")
        vacios = int(r["pasos_laborable"].isna().sum())
        inf.anotar(vacios == 0 and float(r["pasos_laborable"].median()) > 0,
                   "Referencia de movimiento sin huecos",
                   f"{vacios} sitios sin valor; mediana "
                   f"{miles(float(r['pasos_laborable'].median()))} personas")


def comprobar_transporte(d: Path, tablas: dict[str, pd.DataFrame], inf: Informe) -> None:
    p = tablas.get("salidas_paradas.parquet")
    lin = tablas.get("lineas_paradas.parquet")
    try:
        dias = json.loads((d / "salidas_paradas_dias.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        dias = {}
    for red, minimo in REDES.items():
        pr = p[p["red"] == red] if p is not None else pd.DataFrame()
        lr = lin[lin["red"] == red] if lin is not None else pd.DataFrame()
        paradas = len(pr)
        lab = float(pr["total_lab"].sum()) if paradas else 0.0
        sab = float(pr["total_sab"].sum()) if paradas else 0.0
        lineas = int(lr["id_linea"].nunique()) if len(lr) else 0
        vehiculos = float(lr["vehiculos_lab"].sum()) if len(lr) else 0.0
        fechas = dias.get(red, {})
        bien = (paradas >= minimo and lab > 0 and sab > 0 and lineas > 0 and vehiculos > 0
                and bool(fechas.get("laborable")) and bool(fechas.get("sabado")))
        inf.anotar(bien, f"Red «{red}» con servicio",
                   f"{miles(paradas)} paradas (mínimo {miles(minimo)}), {lineas} líneas, "
                   f"{miles(lab)} pasos en laborable ({fechas.get('laborable', 'sin día')}) y "
                   f"{miles(sab)} en sábado ({fechas.get('sabado', 'sin día')})")
    if p is not None:
        otras = sorted(set(p["red"]) - set(REDES))
        inf.anotar(not otras, "Redes desconocidas", ", ".join(otras) or "ninguna")


def comprobar_mapa(tablas: dict[str, pd.DataFrame], inf: Informe) -> None:
    fuera = []
    for nombre, t in tablas.items():
        if "lat" in t and "lon" in t:
            lat, lon = t["lat"].astype(float), t["lon"].astype(float)
            caja_lat, caja_lon = CAJA_ANCHA.get(nombre, (LAT, LON))
            n = int((~(lat.between(*caja_lat) & lon.between(*caja_lon))).sum())
            if n:
                fuera.append(f"{nombre}: {n}")
    inf.anotar(not fuera, "Puntos fuera de la Comunidad de Madrid",
               "; ".join(fuera) or "ninguno")


def comprobar(d: Path = PROC) -> Informe:
    inf = Informe()
    tablas: dict[str, pd.DataFrame] = {}
    comprobar_filas(d, tablas, inf)
    comprobar_prohibidos(tablas, inf)
    comprobar_poblacion(tablas, inf)
    comprobar_transporte(d, tablas, inf)
    comprobar_mapa(tablas, inf)
    return inf


def main(argv: list[str]) -> int:
    d = Path(argv[argv.index("--dir") + 1]).resolve() if "--dir" in argv else PROC
    inf = comprobar(d)
    if "--markdown" in argv:
        print("| | Comprobación | Resultado |\n|---|---|---|")
        for bien, que, detalle in inf.filas:
            print(f"| {'✅' if bien else '❌'} | {que} | {detalle} |")
    else:
        for bien, que, detalle in inf.filas:
            print(f"{'  bien' if bien else ' FALLO'}  {que}: {detalle}")
    print(f"\n{len(inf.filas)} comprobaciones, {inf.fallos} con fallo."
          + ("" if inf.fallos else " Los datos están dentro de lo esperado."))
    return 1 if inf.fallos else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
