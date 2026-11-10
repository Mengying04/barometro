"""Descarga los conjuntos de datos del Portal de Datos Abiertos de la Comunidad de Madrid.

Para cada conjunto de datos:
  1. Guarda la ficha (package_show) en datos/originales/<id>/ficha.json.
  2. Descarga el fichero completo de cada recurso CSV, JSON, SHP o ZIP desde su
     campo `url` (no se usa datastore_search para descargar: puede cortar los datos).
  3. Si el recurso tiene la API de datos activa, compara las filas del CSV
     descargado con el total de datastore_search y avisa si no coinciden.
  4. Genera docs/fuentes.md con la tabla de fuentes.

Uso:  python src/descargar_datos.py
Solo usa la biblioteca estándar de Python.
"""

from __future__ import annotations

import csv
import io
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

PORTAL = "https://datos.comunidad.madrid"
API = f"{PORTAL}/api/3/action"

CONJUNTOS = [
    "centros_educativos",
    "centros_servicios_establecimientos_sanitarios",
    "desfibriladores_externos_fuera_ambito_sanitario",
    "oficinas_farmacia",
    "alojamientos_turisticos",
    "declaraciones_actividad_viviendas_uso_turistico",
    "secciones_censales",
    "festivos_regionales_locales",
    "gasto_por_subgrupo_gasto_3_digitos_coicop_epf_base_2006",
    "ipc_base_2025",
    "demografia_empresarial_cnae25",
    # Alumnos por municipio (y distrito en Madrid), enseñanza y titularidad: se reparten
    # entre los centros para estimar el peso de cada colegio (src/procesar_perfil.py).
    "spacm_estadisticas_alumnos",
]

FORMATOS = {"CSV", "JSON", "SHP", "ZIP"}

RAIZ = Path(__file__).resolve().parent.parent
DIR_ORIGINALES = RAIZ / "datos" / "originales"
FICHERO_FUENTES = RAIZ / "docs" / "fuentes.md"

USER_AGENT = "BARometro-datamad2026/0.1 (descarga de datos abiertos)"
REINTENTOS = 3
TIMEOUT = 120


class Bloqueado(Exception):
    """El cortafuegos del entorno ha bloqueado la petición."""


def _peticion(url: str, datos: bytes | None = None, timeout: int = TIMEOUT):
    req = urllib.request.Request(url, data=datos, headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(req, timeout=timeout)


def _abrir(url: str, datos: bytes | None = None, timeout: int = TIMEOUT):
    """Abre una URL (GET, o POST si se pasan `datos`) con reintentos.

    Lanza Bloqueado si el cortafuegos responde 403."""
    ultimo_error: Exception | None = None
    for intento in range(1, REINTENTOS + 1):
        try:
            return _peticion(url, datos, timeout)
        except urllib.error.HTTPError as e:
            cuerpo = e.read(2000).decode("utf-8", "replace")
            if e.code == 403 and (
                "Approval required" in cuerpo
                or "Blocked by" in cuerpo
                or "network policy" in cuerpo
                or "org policy" in cuerpo
            ):
                raise Bloqueado(urllib.parse.urlsplit(url).hostname) from e
            ultimo_error = e
            if 400 <= e.code < 500 and e.code != 429:
                break
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            ultimo_error = e
        time.sleep(2 * intento)
    raise RuntimeError(f"{url}: {ultimo_error}")


def api(accion: str, **params) -> dict:
    url = f"{API}/{accion}?{urllib.parse.urlencode(params)}"
    with _abrir(url) as r:
        datos = json.load(r)
    if not datos.get("success"):
        raise RuntimeError(f"{accion} {params}: {datos.get('error')}")
    return datos["result"]


def descargar(url: str, destino: Path, datos: bytes | None = None,
              timeout: int = TIMEOUT) -> int:
    """Descarga en streaming a un fichero temporal y lo renombra al terminar."""
    tmp = destino.with_suffix(destino.suffix + ".part")
    with _abrir(url, datos, timeout) as r, open(tmp, "wb") as f:
        total = 0
        while bloque := r.read(1 << 20):
            f.write(bloque)
            total += len(bloque)
    tmp.replace(destino)
    return total


def contar_filas_csv(ruta: Path) -> int:
    """Cuenta registros (sin cabecera) respetando campos entrecomillados con saltos de línea."""
    crudo = ruta.read_bytes()
    for codificacion in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            texto = crudo.decode(codificacion)
            break
        except UnicodeDecodeError:
            continue
    cabecera = texto.split("\n", 1)[0]
    separador = max([";", ",", "\t", "|"], key=cabecera.count)
    lector = csv.reader(io.StringIO(texto, newline=""), delimiter=separador)
    filas = sum(1 for fila in lector if any(c.strip() for c in fila))
    return max(filas - 1, 0)


def total_datastore(resource_id: str) -> int | None:
    try:
        return api("datastore_search", resource_id=resource_id, limit=0)["total"]
    except Exception:
        return None


def nombre_fichero(recurso: dict, usados: set[str]) -> str:
    nombre = Path(urllib.parse.urlsplit(recurso["url"]).path).name or recurso["id"]
    nombre = urllib.parse.unquote(nombre)
    if nombre in usados:
        nombre = f"{recurso['id'][:8]}_{nombre}"
    usados.add(nombre)
    return nombre


def procesar(conjunto: str, informe: dict) -> dict:
    fila = {"id": conjunto, "titulo": conjunto, "licencia": "?", "modificado": "?",
            "formatos": [], "filas": [], "estado": "ok"}
    carpeta = DIR_ORIGINALES / conjunto
    carpeta.mkdir(parents=True, exist_ok=True)

    try:
        ficha = api("package_show", id=conjunto)
    except Bloqueado as e:
        informe["bloqueadas"].add(str(e))
        informe["fallos"].append(f"{conjunto}: ficha bloqueada por el cortafuegos ({e})")
        fila["estado"] = "bloqueado"
        return fila
    except Exception as e:
        informe["fallos"].append(f"{conjunto}: no se pudo leer la ficha: {e}")
        fila["estado"] = "error"
        return fila

    (carpeta / "ficha.json").write_text(
        json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")
    fila.update(titulo=ficha.get("title") or conjunto,
                licencia=ficha.get("license_title") or ficha.get("license_id") or "?",
                modificado=(ficha.get("metadata_modified") or "?")[:10])

    usados: set[str] = set()
    for recurso in ficha.get("resources", []):
        formato = (recurso.get("format") or "").strip().upper()
        if formato not in FORMATOS:
            continue
        nombre = nombre_fichero(recurso, usados)
        destino = carpeta / nombre
        print(f"  · {formato:4} {nombre} ...", end=" ", flush=True)
        try:
            tam = descargar(recurso["url"], destino)
        except Bloqueado as e:
            print("BLOQUEADO")
            informe["bloqueadas"].add(str(e))
            informe["fallos"].append(f"{conjunto}/{nombre}: bloqueado ({e})")
            continue
        except Exception as e:
            print("ERROR")
            informe["fallos"].append(f"{conjunto}/{nombre}: {e}")
            continue

        if formato not in fila["formatos"]:
            fila["formatos"].append(formato)
        informe["descargados"].append(f"{conjunto}/{nombre} ({tam / 1e6:.1f} MB)")
        msg = f"{tam / 1e6:.1f} MB"

        declarado = recurso.get("size")
        if declarado and abs(declarado - tam) > max(1024, 0.01 * declarado):
            informe["avisos"].append(
                f"{conjunto}/{nombre}: tamaño descargado {tam} B ≠ declarado en la ficha {declarado} B")

        if formato == "CSV":
            n = contar_filas_csv(destino)
            fila["filas"].append(f"{n:,}".replace(",", "."))
            msg += f", {n} filas"
            if recurso.get("datastore_active"):
                total = total_datastore(recurso["id"])
                if total is None:
                    informe["avisos"].append(
                        f"{conjunto}/{nombre}: no se pudo consultar datastore_search")
                elif total != n:
                    informe["cortados"].append(
                        f"{conjunto}/{nombre}: CSV {n} filas ≠ datastore {total}")
                    msg += f" ⚠ datastore dice {total}"
                else:
                    msg += " (= datastore)"
        print(msg)
    return fila


def actualizar_bloque(clave: str, lineas: list[str]) -> None:
    """Reescribe en docs/fuentes.md solo el bloque delimitado por los comentarios
    <!-- inicio:clave --> y <!-- fin:clave -->; si no existe, lo añade al final.

    Así cada script de descarga mantiene su propia sección sin borrar las demás."""
    inicio, fin = f"<!-- inicio:{clave} -->", f"<!-- fin:{clave} -->"
    bloque = "\n".join([inicio, *lineas, fin])
    texto = (FICHERO_FUENTES.read_text(encoding="utf-8") if FICHERO_FUENTES.exists()
             else "# Fuentes de datos\n")
    if inicio in texto and fin in texto:
        antes, resto = texto.split(inicio, 1)
        despues = resto.split(fin, 1)[1]
        texto = antes + bloque + despues
    else:
        texto = texto.rstrip("\n") + "\n\n" + bloque + "\n"
    FICHERO_FUENTES.parent.mkdir(parents=True, exist_ok=True)
    FICHERO_FUENTES.write_text(texto, encoding="utf-8")


def escribir_fuentes(filas: list[dict], informe: dict) -> None:
    hoy = date.today().isoformat()
    lineas = [
        "## Portal de Datos Abiertos de la Comunidad de Madrid",
        "",
        "Conjuntos descargados del [Portal de Datos Abiertos de la Comunidad de Madrid]"
        f"({PORTAL}) con `src/descargar_datos.py`.",
        "",
        f"Fecha de descarga: {hoy}.",
        "",
        "Los ficheros se guardan en `datos/originales/<id>/` y no se suben a GitHub; "
        "se regeneran ejecutando el script.",
        "",
        "| Título | Ficha | Licencia | Última modificación | Formatos | Filas (CSV) |",
        "|---|---|---|---|---|---|",
    ]
    for f in filas:
        enlace = f"[{f['id']}]({PORTAL}/dataset/{f['id']})"
        formatos = ", ".join(f["formatos"]) or "—"
        n = " + ".join(str(x) for x in f["filas"]) or "—"
        titulo = f["titulo"].replace("|", "\\|")
        if f["estado"] != "ok":
            titulo += f" (**{f['estado']}**)"
        lineas.append(f"| {titulo} | {enlace} | {f['licencia']} | {f['modificado']} "
                      f"| {formatos} | {n} |")
    lineas += [
        "",
        "Cuando un conjunto tiene varios CSV, la columna de filas los muestra en el orden "
        "de la ficha separados por «+».",
        "",
        "Los recuentos corresponden a la fecha de descarga. Varios conjuntos se reemplazan "
        "completos de forma periódica (según el campo «Frecuencia de actualización de datos» "
        "de la ficha: alojamientos_turisticos cada semana, los lunes hacia las 06:11; "
        "centros_servicios_establecimientos_sanitarios cada día hacia las 06:06), y el CSV "
        "y el datastore se actualizan a la vez. Por eso un recuento consultado otro día "
        "puede no coincidir: es una versión distinta de los datos, no un corte de la "
        "descarga.",
        "",
    ]
    if informe["cortados"]:
        lineas += ["### Discrepancias entre el CSV y la API de datos (datastore_search)", ""]
        lineas += [f"- {x}" for x in informe["cortados"]]
        lineas.append("")
    actualizar_bloque("portal", lineas)


def main() -> int:
    informe = {"descargados": [], "fallos": [], "avisos": [], "cortados": [],
               "bloqueadas": set()}
    filas = []
    for conjunto in CONJUNTOS:
        print(f"\n{conjunto}")
        filas.append(procesar(conjunto, informe))
    escribir_fuentes(filas, informe)

    print("\n================ RESUMEN ================")
    print(f"Ficheros descargados: {len(informe['descargados'])}")
    for clave, titulo in [("fallos", "Fallos"), ("cortados", "Posibles cortes (CSV ≠ datastore)"),
                          ("avisos", "Avisos")]:
        print(f"{titulo}: {len(informe[clave])}")
        for x in informe[clave]:
            print(f"  - {x}")
    print(f"Direcciones bloqueadas: {', '.join(sorted(informe['bloqueadas'])) or 'ninguna'}")
    print(f"Tabla de fuentes: {FICHERO_FUENTES.relative_to(RAIZ)}")
    return 1 if informe["fallos"] else 0


if __name__ == "__main__":
    sys.exit(main())
