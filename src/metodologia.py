"""BARómetro: ficha técnica, metodología y supuestos clave, y la nota del contraste con
conteos reales.

Lo usan el Informe completo de la aplicación (app/app.py) y el documento descargable
(src/documento.py), para que digan lo mismo con las mismas palabras. No calcula nada: lee
las constantes de src/supuestos.py tal cual y da formato a lo que ya se sabe.

    from metodologia import filas_ficha, filas_metodologia, formula_mercado, AVISO_AFOROS
"""

from __future__ import annotations

from pathlib import Path

import supuestos as S
from calle import con_tipo, dec, miles

RAIZ = Path(__file__).resolve().parent.parent

# Nota del contraste con conteos reales de peatones (docs/validacion.md): no cambia ningún
# cálculo ni ninguna confianza, solo avisa en «A qué hora».
AVISO_AFOROS = ("Contraste con conteos reales (Madrid capital, 2023): en día laborable, las "
                "aceras tienen más gente por la tarde de lo que dice este modelo; la hora punta "
                "de la mañana puede estar sobrevalorada. Compruébalo contando en persona.")
METODO = "Modelo por horas con supuestos explícitos"
# De dónde sale el perfil por horas (src/perfil_horario.py; detalle en docs/fuentes.md).
FUENTE_PERFIL = ("perfil por horas con datos del CRTM, del Portal de Datos Abiertos de la "
                 "Comunidad de Madrid, del INE y de OpenStreetMap")


def version_codigo() -> str | None:
    """Commit corto del código, leído de .git sin ejecutar git (None si no hay .git, como en
    la imagen de Docker)."""
    git = RAIZ / ".git"
    try:
        cabeza = (git / "HEAD").read_text(encoding="utf-8").strip()
        if not cabeza.startswith("ref:"):
            return cabeza[:7]
        ref = cabeza[4:].strip()
        if (git / ref).exists():
            return (git / ref).read_text(encoding="utf-8").strip()[:7]
        for linea in (git / "packed-refs").read_text(encoding="utf-8").splitlines():
            if linea.endswith(" " + ref):
                return linea.split()[0][:7]
    except OSError:
        pass
    return None


def coordenadas(lat: float, lon: float) -> str:
    """«40,4046° N, 3,6106° O»."""
    return (f"{dec(abs(lat), 4)}° {'N' if lat >= 0 else 'S'}, {dec(abs(lon), 4)}° "
            f"{'O' if lon < 0 else 'E'}")


def filas_ficha(lugar: str, punto: tuple[float, float] | None, municipio: str, rec: dict,
                descarga: str, fecha: str, version: str | None) -> list[tuple[str, str]]:
    """Las filas de la ficha técnica: qué se ha analizado, con qué datos y con qué versión.
    `descarga` es la fecha de descarga del portal y `fecha`, la del informe (AAAA-MM-DD)."""
    tipo = rec["tipo_local"]["clave"] if con_tipo(rec) else None
    return [
        ("Punto analizado", lugar + (f" · {coordenadas(*punto)}" if punto else "")),
        ("Municipio", municipio),
        ("Radio de análisis", f"{S.RADIO_M} m (unos 4 minutos andando)"),
        ("Tipo de local", S.TIPOS_LOCAL[tipo] if tipo else "Sin elegir (resultado general)"),
        ("Fecha de los datos", f"{descarga} (descarga del portal)"),
        ("Fecha del informe", fecha),
        ("Método", METODO),
        ("Versión", f"commit {version}" if version else f"datos del {descarga}"),
    ]


def num(x: float) -> str:
    """Un número tal como está en src/supuestos.py, con coma decimal y sin ceros de sobra
    (0.025 → «0,025»; 2.0 → «2»; 0.5 % → «0,5»)."""
    return dec(x, 3).rstrip("0").rstrip(",")


def filas_metodologia(rec: dict, mov: dict) -> list[tuple[str, str, str]]:
    """Parámetro, valor y de dónde sale: los valores se leen de src/supuestos.py tal cual
    (no se cambia ninguno)."""
    tipo = rec["tipo_local"]["clave"] if con_tipo(rec) else None
    nombre_tipo = S.TIPOS_LOCAL_CORTO[tipo] if tipo else ""
    cortes = [c for c, _ in S.MOVIMIENTO_NIVELES[:-1]]
    if tipo:
        tasas = [v for cli in S.TASA_PARADA[tipo].values() for v in cli.values() if v > 0]
        tasa = (f"Entre el {num(100 * min(tasas))} % y el {num(100 * max(tasas))} % de "
                f"los pasos de cada hora, según el cliente y la hora ({nombre_tipo})")
        v = S.VISITAS_VECINO[tipo]
        visitas = (f"{num(v['laborable'])} en laborable, {num(v['fin_de_semana'])} en sábado "
                   f"y {num(v['domingo'])} en domingo, por vecino y día ({nombre_tipo})")
    else:
        tasa = visitas = "Solo con un tipo de local elegido"
    return [
        ("Radio de análisis", f"{S.RADIO_M} m", "Supuesto: unos 4 minutos andando (RADIO_M)"),
        ("Peso por distancia", f"1 en el punto, baja en línea recta hasta "
                               f"{dec(S.PESO_BORDE, 2)} en el borde del radio",
         "Supuesto (PESO_BORDE)"),
        ("Propensión a pararse a consumir", "; ".join(
            f"{S.TIPOS_CLIENTE[c].lower()} {dec(p, 1)}" for c, p in S.PROPENSION_CONSUMO.items()),
         "Supuesto: a quién orientar la oferta; no cambia la gente que pasa "
         "(PROPENSION_CONSUMO)"),
        ("Tasa de parada de la gente que pasa", tasa, "Supuesto (TASA_PARADA)"),
        ("Visitas de los vecinos que van a propósito", visitas,
         "Supuesto contrastado con el gasto en restauración de la EPF (VISITAS_VECINO)"),
        ("Límite de esas visitas", f"Las de los cinco tipos de local, como mucho el "
                                   f"{dec(100 * S.PARTE_GASTO_CERCA_DE_CASA, 0)} % del gasto "
                                   "medio por persona en restauración",
         "Supuesto (PARTE_GASTO_CERCA_DE_CASA); lo comprueba src/comprobar_datos.py con la EPF"),
        ("Sensibilidad del horario de clientes",
         "Se repite con las tasas de parada y las visitas × " + " y × ".join(
             num(f) for f in S.SENSIBILIDAD_FACTORES) + ". «Cambia con poco» si la hora "
         "con más clientes pasa a otra franja, a más de una hora, y cambian dos de las tres "
         "horas con más clientes", "Criterio (SENSIBILIDAD_FACTORES)"),
        ("Cortes del nivel de movimiento",
         "Percentiles " + ", ".join(f"{dec(100 * c, 0)}" for c in cortes[:-1])
         + f" y {dec(100 * cortes[-1], 0)} de {miles(mov['sitios_referencia'])} sitios de "
         f"referencia; «Muy poco paso» siempre por debajo de "
         f"{miles(S.MOVIMIENTO_MINIMO_PASOS)} personas al día",
         "Elección (MOVIMIENTO_NIVELES, MOVIMIENTO_MINIMO_PASOS)"),
    ]


def formula_mercado(exponente: str = "<sup>e</sup>") -> str:
    """La fórmula del mercado potencial. `exponente` es cómo se escribe la «e» elevada
    (HTML en la aplicación; «ᵉ» en el PDF)."""
    e0, e1 = S.ELASTICIDAD_RESTAURACION
    return ("Gasto anual de los vecinos en restauración = población del radio × gasto medio "
            "por persona en restauración (EPF, Comunidad de Madrid) × (renta de la zona ÷ "
            f"renta media de la Comunidad){exponente}, con e entre {dec(e0, 1)} y "
            f"{dec(e1, 1)}, y ±{dec(100 * S.MARGEN_POBLACION, 0)} % por la población. Se da "
            "como rango (estimación).")
