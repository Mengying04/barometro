"""BARómetro: servidor MCP (Model Context Protocol), en local por stdio.

Permite que un asistente (Claude Desktop, Claude Code u otro cliente MCP) consulte
BARómetro. Expone cinco herramientas que solo llaman a las funciones que ya existen en
src/, sin repetir cálculos:

  - recomendar_local(lat, lon)   → recomendar()
  - comparar_locales(lat1, lon1, lat2, lon2) → comparar() (src/comparar.py)
  - perfil_por_horas(lat, lon)   → perfil_horario()
  - informe_de_zona(lat, lon)    → informe_local()
  - buscar_direccion(texto)      → geocodificar() y coordenadas() (CartoCiudad)

recomendar_local y perfil_por_horas añaden el nivel de movimiento de la zona
(nivel_movimiento(), src/movimiento.py). buscar_direccion dice si cada resultado es un
portal exacto o una calle o zona entera, con un aviso.

Arranque (lo lanza el cliente MCP; no hace falta arrancarlo a mano):
    python mcp/servidor.py

Cada respuesta lleva el aviso de que es una orientación con estimaciones, las fuentes con
su licencia y fecha (leídas de docs/fuentes.md) y «Powered by CRTM».

Privacidad: el servidor no guarda las direcciones ni los puntos consultados. No escribe
ficheros ni registros con ellos y no tiene caché por punto. Nunca devuelve nombres de
locales: los datos procesados no los tienen y el buscador descarta nombres de comercios.

Usa el SDK oficial de Python (paquete `mcp`, versión 2): su clase MCPServer es la que en
la versión 1 se llamaba FastMCP.
"""

from __future__ import annotations

import contextlib
import json
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from mcp.server.mcpserver import MCPServer  # noqa: E402
from mcp.server.mcpserver.exceptions import ToolError  # noqa: E402

AVISO = ("Orientación a partir de datos abiertos y supuestos explícitos, no garantías. Toda "
         "cifra de personas es una estimación. No estima la facturación ni da precios en "
         "euros. Conviene comprobarlo en persona antes de decidir.")
ATRIBUCION = ("Powered by CRTM (https://www.crtm.es): los datos del Consorcio Regional de "
              "Transportes de Madrid se usan procesados, no en bruto. © colaboradores de "
              "OpenStreetMap (ODbL). Datos del Portal de Datos Abiertos de la Comunidad de "
              "Madrid (CC BY 4.0), del Ayuntamiento de Madrid (CC BY 4.0) y del INE. "
              "Este proyecto no está respaldado por ninguna de esas entidades.")
FUERA = ("Ese punto está fuera de la Comunidad de Madrid. BARómetro solo tiene datos de la "
         "Comunidad de Madrid: no se ha calculado nada. Prueba con otro punto o busca la "
         "dirección con buscar_direccion.")

# Fuentes que usa cada herramienta (identificadores de docs/fuentes.md).
PORTAL_PERFIL = ["centros_educativos", "spacm_estadisticas_alumnos",
                 "centros_servicios_establecimientos_sanitarios",
                 "desfibriladores_externos_fuera_ambito_sanitario", "1925489", "1925502",
                 "1923861", "secciones_censales"]
EXTERNAS_PERFIL = ["ine_adrh", "ine_seccionado", "osm_universidades", "crtm_paradas"]

servidor = MCPServer(
    "barometro",
    title="BARómetro",
    instructions=(
        "BARómetro orienta sobre qué vender, a quién, a qué hora y a qué precio en un bar o "
        "restaurante de la Comunidad de Madrid, con datos abiertos. Si el usuario da una "
        "dirección, usa primero buscar_direccion para obtener las coordenadas y después "
        "recomendar_local. Si duda entre dos sitios, usa comparar_locales y no declares "
        "un ganador. Si buscar_direccion no devuelve un portal exacto (una calle sin "
        "número, un municipio…), no calcules: pide antes el número o que confirmen el "
        "sitio. Mira primero el nivel de movimiento de la zona: si es «Muy poco paso», "
        "dilo con claridad antes de recomendar nada. Presenta siempre los resultados como una orientación con "
        "estimaciones, nunca como una garantía, y menciona las fuentes y «Powered by CRTM». "
        "No hay nombres de locales ni precios en euros."),
    log_level="WARNING")


# ------------------------------------------------------------------------- apoyo
@lru_cache(maxsize=1)
def _modulos():
    """Carga los módulos de cálculo la primera vez. Todo lo que escriban va a la salida de
    errores: la salida estándar es el canal del protocolo."""
    with contextlib.redirect_stdout(sys.stderr):
        import comparar
        import direcciones
        import fuentes
        import informe_local
        import movimiento
        import perfil_horario
        import recomendaciones
        import supuestos
    return {"comparar": comparar, "direcciones": direcciones, "fuentes": fuentes,
            "informe": informe_local,
            "perfil": perfil_horario, "rec": recomendaciones, "supuestos": supuestos,
            "movimiento": movimiento}


def _municipio(lat: float, lon: float) -> dict:
    """Municipio del punto. Error claro si las coordenadas no valen o caen fuera."""
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ToolError("Coordenadas no válidas: lat debe estar entre -90 y 90 y lon entre "
                        "-180 y 180, en grados decimales (por ejemplo, 40.4046 y -3.6106).")
    import shapely
    inf = _modulos()["informe"]
    x, y = inf._A_UTM.transform(lon, lat)
    try:
        return inf.municipio(shapely.Point(x, y))
    except ValueError:
        raise ToolError(FUERA) from None


@lru_cache(maxsize=1)
def _fuentes_md() -> dict:
    return _modulos()["fuentes"].leer_fuentes()


def _sin_enlaces(texto: str) -> str:
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", texto).replace("**", "")


def _fuentes(portal: list[str], externas: list[str], aplicacion: list[str] = ()) -> list[dict]:
    """Fuentes con su licencia y sus fechas, tal como están en docs/fuentes.md."""
    f = _fuentes_md()
    out = []
    for fila in f["portal"]:
        m = re.match(r"\[([^\]]+)\]\(([^)]+)\)", fila["Ficha"])
        if m and m.group(1) in portal:
            out.append({"nombre": fila["Conjunto"], "enlace": m.group(2),
                        "licencia": fila["Licencia"] + " (CC BY 4.0). Fuente: Comunidad de "
                                    "Madrid, Portal de Datos Abiertos",
                        "datos": f"última modificación {fila['Última modificación']}",
                        "descargado": f["portal_descarga"]})
    for bloque, carpetas in (("externas", externas), ("aplicacion", aplicacion)):
        for e in f[bloque]:
            clave = (re.search(r"datos/originales/([^/`]+)", e.get("Carpeta", "")) or [0, ""])[1]
            if clave in carpetas or any(c in e["titulo"] for c in carpetas if c[0].isupper()):
                enlace = re.search(r"https?://[^\s)]+", e.get("Enlace", ""))
                out.append({"nombre": e["titulo"], "enlace": enlace.group(0) if enlace else "",
                            "licencia": _sin_enlaces(e.get("Licencia", "?")),
                            "datos": _sin_enlaces(e.get("Versión de los datos", "?")),
                            "descargado": e.get("Fecha de descarga", "?")})
    return out


def _fuentes_informe(inf: dict) -> list[dict]:
    """Fuentes que citan los bloques del informe, sin repetir."""
    out, vistas = [], set()
    for b in inf["bloques"]:
        for f in b["fuentes"]:
            if f["nombre"] not in vistas:
                vistas.add(f["nombre"])
                out.append({"nombre": f["nombre"], "enlace": f["enlace"],
                            "licencia": f["licencia"],
                            "datos": _sin_enlaces(f["actualizado"]),
                            "descargado": f["descargado"]})
    return out


def _unir(*listas: list[dict]) -> list[dict]:
    out, vistas = [], set()
    for lista in listas:
        for f in lista:
            if f["nombre"] not in vistas:
                vistas.add(f["nombre"])
                out.append(f)
    return out


def _respuesta(contenido: dict, fuentes: list[dict]) -> dict:
    """Envoltorio común: aviso, contenido, fuentes y atribución. Se pasa por JSON para
    que solo lleve tipos sencillos (los números de numpy pasan a números normales)."""
    r = {"aviso": AVISO, **contenido, "fuentes": fuentes, "atribucion": ATRIBUCION}
    return json.loads(json.dumps(r, ensure_ascii=False, default=_a_json))


def _a_json(valor):
    """Convierte lo que JSON no sabe escribir (números de numpy, fechas)."""
    return valor.item() if hasattr(valor, "item") else str(valor)


def _calcular(lat: float, lon: float, que: str) -> tuple[dict, dict, dict | None, dict | None]:
    """Municipio, perfil y, si hacen falta, informe y recomendaciones del punto."""
    muni = _municipio(lat, lon)
    m = _modulos()
    with contextlib.redirect_stdout(sys.stderr):
        perfil = m["perfil"].perfil_horario(lat, lon)
        inf = m["informe"].informe_local(lat, lon, perfil=perfil) if que != "perfil" else None
        rec = (m["rec"].recomendar(lat, lon, perfil=perfil, inf=inf)
               if que == "recomendar" else None)
    return muni, perfil, inf, rec


def _movimiento(perfil: dict) -> dict:
    """Nivel de movimiento de la zona frente al resto de la Comunidad (estimación)."""
    return _modulos()["movimiento"].nivel_movimiento(perfil)


# ------------------------------------------------------------------ herramientas
@servidor.tool(title="Recomendaciones para un local")
def recomendar_local(lat: float, lon: float) -> dict[str, Any]:
    """Recomendaciones para un bar o restaurante situado en un punto de la Comunidad de
    Madrid: a quién vender, a qué hora, qué vender y a qué precio.

    Es la herramienta principal: úsala cuando alguien pregunte qué le conviene ofrecer en
    un local, a qué público o en qué horario. Necesita la latitud y la longitud en grados
    decimales (WGS84); si solo tienes una dirección, obtén antes las coordenadas con
    buscar_direccion.

    Devuelve cuatro respuestas (a_quien, a_que_hora, que_vender, a_que_precio). Cada
    recomendación trae su texto, su «porque» con las cifras, su «confianza» (alta, media o
    baja) y su «base» (dato o estimación). Incluye además los «riesgos»: como mucho tres
    avisos propios de ese sitio, ordenados por importancia, cada uno con su cifra y en
    lenguaje sencillo (peso de colegios o de universidad, competencia, festivos de los
    próximos 30 días con su fecha); si no hay ninguno, una sola frase que lo dice. Dalos
    tal cual, sin añadir avisos genéricos. Trae también una lista de cosas que comprobar
    en persona. Las recomendaciones por día traen «dia»: «laborable» (un día de diario),
    «fin_de_semana» (el sábado; el nombre es antiguo) o «domingo» (vale también, de forma
    aproximada, para los festivos). Analiza un círculo de 300 metros alrededor del punto.

    Trae también «nivel_de_movimiento»: cuánta gente pasa en un día laborable frente a
    los sitios habitados de la Comunidad, en cinco niveles (de «Muy poco paso» a
    «Muchísimo paso»), con una frase de comparación. Es una estimación. Si es «Muy poco
    paso», empieza por ahí y da su «aviso»: BARómetro mide el negocio de paso y un local
    al que se va a propósito o en coche no se puede valorar con estos datos; las cuatro
    respuestas valen entonces muy poco.

    Es una orientación con estimaciones, no una garantía: no estima la facturación ni da
    precios en euros, y no nombra locales. Si el punto está fuera de la Comunidad de
    Madrid, devuelve un error."""
    muni, perfil, inf, rec = _calcular(lat, lon, "recomendar")
    contenido = {k: rec[k] for k in ("radio_m", "a_quien", "a_que_hora", "que_vender",
                                     "a_que_precio", "riesgos", "comprobar_en_persona")}
    return _respuesta(
        {"municipio": muni["nombre"], "fecha": rec["fecha"],
         "nivel_de_movimiento": _movimiento(perfil), **contenido},
        _unir(_fuentes_informe(inf), _fuentes(PORTAL_PERFIL, EXTERNAS_PERFIL)))


@servidor.tool(title="Comparar dos locales")
def comparar_locales(lat1: float, lon1: float, lat2: float, lon2: float) -> dict[str, Any]:
    """Compara dos puntos de la Comunidad de Madrid como sitio para un bar o restaurante,
    aspecto por aspecto, con el mismo contenido que la comparación de la aplicación.

    Úsala cuando alguien dude entre dos locales o dos direcciones. Necesita la latitud y
    la longitud de los dos puntos en grados decimales (WGS84); si solo tienes direcciones,
    obtén antes las coordenadas de cada una con buscar_direccion (solo portales exactos).
    El primero es el local «a» y el segundo, el «b».

    Devuelve «filas», una por aspecto: nivel de movimiento, gente que pasa en un día de
    diario, en un sábado y en un domingo, quién pasa, horas punta, qué conviene ofrecer,
    gama de precios, competencia a menos de 300 metros y frente a su municipio, cómo se
    llega y los avisos de cada sitio. Cada fila trae lo que se sabe de «a» y de «b», su
    «fiabilidad», «mejor» («a», «b» o nada) y un «veredicto» en una frase. «mejor» solo se
    marca cuando la diferencia pasa del 15 % y la fiabilidad no es baja; si no, el
    veredicto dice «diferencia pequeña, no decide» o por qué no se puede comparar (por
    ejemplo, locales contados con fuentes distintas). En quién pasa y en la gama de precios
    no hay mejor ni peor. Trae también «personas_por_hora» de los dos sitios (laborable,
    sábado y domingo) y un «resumen» de dos o tres frases.

    No declares un ganador: di en qué sale mejor cada uno, repite los veredictos tal cual
    (incluidos los que no deciden) y recuerda que es una orientación con estimaciones, no
    una garantía, y que conviene comprobarlo en persona en los dos sitios. No nombra
    locales ni guarda los puntos. Si alguno está fuera de la Comunidad de Madrid, devuelve
    un error."""
    lados = []
    for n, (lat, lon) in enumerate(((lat1, lon1), (lat2, lon2)), 1):
        try:
            muni, perfil, inf, rec = _calcular(lat, lon, "recomendar")
        except ToolError as e:
            raise ToolError(f"Local {n}: {e}") from None
        lados.append({"nombre": f"Local {n} ({muni['nombre']})", "perfil": perfil,
                      "informe": inf, "rec": rec, "mov": _movimiento(perfil),
                      "municipio": muni["nombre"], "lat": lat, "lon": lon})
    c = _modulos()["comparar"].comparar(*lados)
    return _respuesta(
        {"fecha": lados[0]["rec"]["fecha"], "radio_m": lados[0]["rec"]["radio_m"],
         "locales": {k: {"nombre": x["nombre"], "municipio": x["municipio"],
                         "lat": x["lat"], "lon": x["lon"]}
                     for k, x in zip("ab", lados)},
         "filas": c["filas"], "resumen": c["resumen"],
         "personas_por_hora": {k: {"laborable": v["laborable"], "sabado": v["fin_de_semana"],
                                   "domingo": v["domingo"]}
                               for k, v in c["personas_por_hora"].items()},
         "nota": c["nota"], "aviso_comparacion": c["aviso"]},
        _unir(_fuentes_informe(lados[0]["informe"]), _fuentes_informe(lados[1]["informe"]),
              _fuentes(PORTAL_PERFIL, EXTERNAS_PERFIL)))


@servidor.tool(title="Gente que pasa cerca, por horas")
def perfil_por_horas(lat: float, lon: float) -> dict[str, Any]:
    """Estimación de cuánta gente pasa cerca de un punto de la Comunidad de Madrid, por
    franja del día y por tipo de cliente, en un día laborable, en un sábado y en un
    domingo.

    Úsala cuando la pregunta sea cuándo hay más movimiento o qué tipo de gente pasa
    (vecinos, viajeros del transporte público, universitarios, padres y niños, pacientes,
    trabajadores, deporte y eventos). Necesita la latitud y la longitud en grados
    decimales (WGS84).

    Devuelve, para «laborable», «sabado» y «domingo», las personas que pasan en cada franja
    (primera hora de la mañana, media mañana, mediodía, media tarde, tarde-noche y noche)
    por tipo de cliente y en total, el total de cada hora de 0 a 23 y la confianza de
    cada tipo de cliente, separada en horario y cantidad. Incluye
    «nivel_de_movimiento»: el total del día laborable situado frente a los sitios
    habitados de la Comunidad, en cinco niveles (estimación). La unidad es el «paso»: una
    persona que pasa a menos de 300 metros en esa franja; quien entra y sale de un sitio
    cuenta dos veces.

    Todas las cifras son estimaciones para comparar horas y tipos de cliente entre sí,
    no recuentos reales. Si el punto está fuera de la Comunidad de Madrid, devuelve un
    error."""
    muni, perfil, _, _ = _calcular(lat, lon, "perfil")
    sup = _modulos()["supuestos"]
    nombres = {**sup.TIPOS_CLIENTE, "total": "Total"}
    dias = {"laborable": "laborable", "fin_de_semana": "sabado", "domingo": "domingo"}
    franjas, horas = {}, {}
    for dia, etiqueta in dias.items():
        tabla = perfil["franjas"].loc[dia]
        franjas[etiqueta] = {
            str(franja): {nombres.get(col, col): int(round(float(valor)))
                          for col, valor in fila.items()}
            for franja, fila in tabla.iterrows()}
        total = perfil["horas"].loc[dia]["total"]
        horas[etiqueta] = {f"{int(h):02d}:00": int(round(float(v))) for h, v in total.items()}
    confianza = [
        {"tipo_de_cliente": f.nombre, "horario": f.confianza_horario,
         "cantidad": f.confianza_cantidad, "motivo_horario": f.motivo_horario,
         "motivo_cantidad": f.motivo_cantidad}
        for f in perfil["confianza"].itertuples()]
    return _respuesta(
        {"municipio": muni["nombre"], "radio_m": int(perfil["radio_m"]),
         "nivel_de_movimiento": _movimiento(perfil),
         "unidad": "personas que pasan cerca en la franja (estimación)",
         "nota": "Tres tipos de día con su propio horario de transporte y sus supuestos. "
                 "«domingo» vale también, de forma aproximada, para los festivos.",
         "horas_de_cada_franja": {k: [f"{h:02d}:00" for h in v]
                                  for k, v in sup.FRANJAS.items()},
         "personas_por_franja": franjas, "total_por_hora": horas,
         "confianza_por_tipo_de_cliente": confianza},
        _fuentes(PORTAL_PERFIL, EXTERNAS_PERFIL))


@servidor.tool(title="Informe de la zona")
def informe_de_zona(lat: float, lon: float) -> dict[str, Any]:
    """Contexto de mercado alrededor de un punto de la Comunidad de Madrid, en ocho
    bloques: competencia, mercado potencial, precios, turismo, festivos, sector, accesos
    (cómo se llega en transporte público) y entorno (qué hay a 1 km).

    Úsala cuando la pregunta sea sobre la zona y no sobre qué ofrecer: cuántos bares y
    restaurantes hay ya en 300 metros y si son muchos o pocos para el municipio, cuánto
    gastan los vecinos en restauración, si la zona es de precios económicos, medios o
    altos, cuánto turismo hay, qué festivos vienen, cómo va el sector, qué transporte
    público para a menos de 300 y de 800 metros (redes, líneas y vehículos al día, con un
    nivel de «Muy bien comunicado» a «Sin transporte cerca») y cuántos vecinos y locales
    hay a 1 km, para distinguir un punto aislado de uno en el borde de un barrio. Los
    800 m y el kilómetro son solo contexto: lo demás se calcula a 300 metros. Necesita la
    latitud y la longitud en grados decimales (WGS84).

    Cada bloque trae un resumen, sus datos, sus notas, sus fuentes y su «caracter»: si
    es un dato (tal como lo publica la fuente) o una estimación. Los locales se cuentan
    por tipo; nunca se dan sus nombres. No hay precios en euros.

    Es una orientación, no una garantía. Si el punto está fuera de la Comunidad de
    Madrid, devuelve un error."""
    muni, _, inf, _ = _calcular(lat, lon, "informe")
    return _respuesta(
        {"municipio": muni["nombre"], "radio_m": inf["radio_m"],
         "fecha": inf["fecha_informe"], "bloques": inf["bloques"]},
        _fuentes_informe(inf))


@servidor.tool(title="Buscar una dirección")
def buscar_direccion(texto: str) -> dict[str, Any]:
    """Convierte una dirección de la Comunidad de Madrid en coordenadas (latitud y
    longitud), con el geocodificador de CartoCiudad del Instituto Geográfico Nacional.

    Úsala antes de las otras herramientas cuando el usuario dé una dirección en vez de
    coordenadas. Escribe la calle, el número y el municipio, por ejemplo «Plaza de la
    Constitución 1, Fuenlabrada». Solo busca en la provincia de Madrid.

    Devuelve una lista de candidatos, con los portales exactos primero. Cada uno trae su
    dirección, sus coordenadas, su «precision» (portal, calle, localidad, municipio o
    codigo_postal) y «es_portal_exacto». Solo un portal con número es un punto concreto.
    Si el resultado es una calle entera, una localidad, un municipio o un código postal,
    lleva un «aviso»: sus coordenadas son un punto cualquiera de esa zona y NO debes
    calcular con ellas; pide antes al usuario el número del portal o que confirme el
    sitio exacto. Si hay varios candidatos, pregunta cuál es el suyo antes de seguir.
    Puede proponer números de portal cercanos y no el exacto. No busca por nombre de
    comercio: los resultados que son nombres de establecimientos o de lugares se
    descartan.

    La dirección se envía a CartoCiudad para situarla y no se guarda."""
    texto = (texto or "").strip()
    if not texto:
        raise ToolError("Escribe una dirección, por ejemplo «Calle Mayor 1, Getafe».")
    d = _modulos()["direcciones"]
    try:
        candidatos = d.geocodificar(texto)
    except Exception:
        raise ToolError("No se ha podido consultar CartoCiudad. Prueba más tarde o usa "
                        "directamente las coordenadas del punto.") from None
    resultados = []
    for c in candidatos:
        try:
            xy = d.coordenadas(c)
        except Exception:
            xy = None
        if xy:
            r = {"direccion": c["texto"], "tipo": c["tipo"], "precision": c["precision"],
                 "es_portal_exacto": c["exacto"],
                 "lat": round(xy[0], 6), "lon": round(xy[1], 6)}
            if not c["exacto"]:
                r["aviso"] = f"{c['precision_texto'].capitalize()}. {d.AVISO_NO_EXACTO}"
            resultados.append(r)
    exactos = sum(r["es_portal_exacto"] for r in resultados)
    return {
        "aviso": ("Comprueba que la dirección es la que buscas. Las coordenadas son una "
                  "aproximación: CartoCiudad puede proponer un portal cercano. Lo que se "
                  "calcule con ellas será una orientación con estimaciones, no una "
                  "garantía."),
        "resultados": resultados,
        "portales_exactos": exactos,
        "nota": ("Sin resultados en la provincia de Madrid: prueba a escribir la dirección "
                 "de otra forma." if not resultados else
                 "Ningún resultado es un portal exacto: son calles o zonas enteras. No "
                 "calcules todavía; pide el número del portal o que confirmen el sitio."
                 if not exactos else
                 "Usa lat y lon de un portal exacto con recomendar_local, perfil_por_horas "
                 "o informe_de_zona. Los resultados con «aviso» no son un punto concreto."),
        "privacidad": "La dirección se ha enviado a CartoCiudad para situarla y no se guarda.",
        "fuentes": _fuentes([], [], ["CartoCiudad"]),
        "atribucion": ("Direcciones: CartoCiudad, IGN · CC BY 4.0 "
                       "www.scne.es/productos.html#CartoCiudad. " + ATRIBUCION)}


if __name__ == "__main__":
    servidor.run()   # stdio
