"""BARómetro: cliente MCP de prueba para mcp/servidor.py.

Arranca el servidor por stdio, como haría Claude Desktop, y llama a cada herramienta con
los tres puntos de ejemplo, con una calle sin número y con un punto aislado de campo.
Comprueba que cada respuesta trae el aviso, las fuentes con
licencia y fecha y «Powered by CRTM», que el resultado es el mismo que da la función de
src/ llamada directamente, y que un punto de fuera de la Comunidad da un error claro.

Uso:  python mcp/probar_cliente.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from mcp import Client, StdioServerParameters  # noqa: E402

EJEMPLOS = {"Campus de Vicálvaro": (40.4046, -3.6106),
            "Centro de Fuenlabrada": (40.283366, -3.800132),
            "Plaza Mayor de Griñón": (40.212861, -3.852623)}
DIRECCIONES = ["Paseo de los Artilleros 38, Madrid", "Plaza de la Constitución 1, Fuenlabrada",
               "Plaza Mayor 1, Griñón"]
SIN_NUMERO = "Paseo de los Artilleros, Madrid"     # una calle entera
CAMPO = (40.2000, -3.8900)   # punto aislado de campo, entre Griñón y Cubas de la Sagra
FUERA = (39.8628, -4.0273)   # Toledo
fallos: list[str] = []


def comprobar(cond: bool, texto: str) -> None:
    if not cond:
        fallos.append(texto)
        print("   ✗", texto)


def datos(resultado) -> dict:
    """El contenido estructurado de la respuesta, o el JSON del texto."""
    d = getattr(resultado, "structured_content", None)
    if d is None:
        d = getattr(resultado, "structuredContent", None)
    if d is None:
        d = json.loads(resultado.content[0].text)
    return d.get("result", d) if set(d) == {"result"} else d


def es_error(resultado) -> bool:
    return bool(getattr(resultado, "is_error", getattr(resultado, "isError", False)))


def comunes(nombre: str, d: dict) -> None:
    comprobar("orientación" in d.get("aviso", "").lower()
              and "estimaci" in d.get("aviso", "").lower(), f"{nombre}: falta el aviso")
    comprobar("Powered by CRTM" in d.get("atribucion", ""), f"{nombre}: falta Powered by CRTM")
    fuentes = d.get("fuentes", [])
    comprobar(len(fuentes) > 0, f"{nombre}: sin fuentes")
    for f in fuentes:
        comprobar(all(f.get(k) for k in ("nombre", "licencia", "descargado")),
                  f"{nombre}: fuente sin licencia o fecha ({f.get('nombre')})")


async def main() -> int:
    import informe_local as I
    import perfil_horario as P
    from movimiento import nivel_movimiento
    from recomendaciones import recomendar

    servidor = StdioServerParameters(command=sys.executable,
                                     args=[str(RAIZ / "mcp" / "servidor.py")])
    async with Client(servidor) as cliente:
        herramientas = (await cliente.list_tools()).tools
        print("Herramientas:", [h.name for h in herramientas])
        comprobar({h.name for h in herramientas} == {"recomendar_local", "perfil_por_horas",
                                                     "informe_de_zona", "buscar_direccion"},
                  "no están las cuatro herramientas")
        for h in herramientas:
            comprobar(len(h.description or "") > 200, f"{h.name}: descripción corta")

        for nombre, (lat, lon) in EJEMPLOS.items():
            print(f"\n== {nombre}")
            perfil = P.perfil_horario(lat, lon)
            inf = I.informe_local(lat, lon, perfil=perfil)
            rec = recomendar(lat, lon, perfil=perfil, inf=inf)
            args = {"lat": lat, "lon": lon}

            r = datos(await cliente.call_tool("recomendar_local", args))
            comunes("recomendar_local", r)
            for k in ("a_quien", "a_que_hora", "que_vender", "a_que_precio", "riesgos",
                      "comprobar_en_persona"):
                comprobar(json.dumps(r[k], sort_keys=True, default=str)
                          == json.dumps(rec[k], sort_keys=True, default=str),
                          f"recomendar_local: «{k}» no coincide con recomendar()")
            mov = nivel_movimiento(perfil)
            comprobar(r["nivel_de_movimiento"] == json.loads(json.dumps(mov)),
                      "recomendar_local: el nivel de movimiento no coincide")
            una = r["a_quien"]["recomendaciones"][0]
            comprobar(all(k in una for k in ("texto", "porque", "confianza", "base")),
                      "recomendar_local: falta porqué, confianza o base")
            print(f"   recomendar_local: {una['texto']} [{una['confianza']}, {una['base']}] · "
                  f"{len(r['riesgos'])} riesgos · {len(r['comprobar_en_persona'])} "
                  f"comprobaciones · {len(r['fuentes'])} fuentes · {mov['nombre']}")

            p = datos(await cliente.call_tool("perfil_por_horas", args))
            comunes("perfil_por_horas", p)
            comprobar(p["nivel_de_movimiento"]["nombre"] == mov["nombre"],
                      "perfil_por_horas: el nivel de movimiento no coincide")
            for dia, etiqueta in (("laborable", "laborable"), ("fin_de_semana", "sabado")):
                esperado = perfil["franjas"].loc[dia]["total"]
                for franja, total in esperado.items():
                    comprobar(p["personas_por_franja"][etiqueta][str(franja)]["Total"]
                              == int(round(float(total))),
                              f"perfil_por_horas: total de {franja} ({etiqueta}) no coincide")
            lab = p["personas_por_franja"]["laborable"]
            mejor = max(lab, key=lambda f: lab[f]["Total"])
            print(f"   perfil_por_horas: franja con más gente en laborable: {mejor} "
                  f"(~{lab[mejor]['Total']}) · {len(p['fuentes'])} fuentes")

            z = datos(await cliente.call_tool("informe_de_zona", args))
            comunes("informe_de_zona", z)
            comprobar(json.dumps(z["bloques"], sort_keys=True, default=str)
                      == json.dumps(inf["bloques"], sort_keys=True, default=str),
                      "informe_de_zona: los bloques no coinciden con informe_local()")
            comprobar([b["clave"] for b in z["bloques"]] == [
                "competencia", "mercado", "precios", "turismo", "festivos", "sector",
                "accesos", "entorno"], "informe_de_zona: no están los ocho bloques")
            print(f"   informe_de_zona: {z['municipio']} · {len(z['bloques'])} bloques · "
                  f"{z['bloques'][0]['resumen'][:70]}…")
            print(f"   accesos: {z['bloques'][6]['datos']['nivel']} · entorno: "
                  f"{z['bloques'][7]['datos']['tipo']}")

        print("\n== buscar_direccion")
        for texto in DIRECCIONES:
            b = datos(await cliente.call_tool("buscar_direccion", {"texto": texto}))
            comunes("buscar_direccion", b)
            comprobar("no se guarda" in b.get("privacidad", ""), "buscar_direccion: privacidad")
            comprobar(all(x["tipo"] not in ("toponimo", "poi") for x in b["resultados"]),
                      "buscar_direccion: hay nombres de lugares o comercios")
            primero = b["resultados"][0] if b["resultados"] else None
            print(f"   {len(b['resultados'])} resultados; el primero:",
                  f"{primero['direccion']} ({primero['lat']}, {primero['lon']})"
                  if primero else "ninguno")
            comprobar(primero is not None, f"buscar_direccion: sin resultados para «{texto}»")
            comprobar(primero and primero["es_portal_exacto"] and "aviso" not in primero,
                      f"buscar_direccion: «{texto}» no da un portal exacto el primero")
            exactos = [x["es_portal_exacto"] for x in b["resultados"]]
            comprobar(exactos == sorted(exactos, reverse=True),
                      "buscar_direccion: los portales no van primero")

        print("\n== calle sin número")
        b = datos(await cliente.call_tool("buscar_direccion", {"texto": SIN_NUMERO}))
        comunes("buscar_direccion", b)
        for x in b["resultados"]:
            print(f"   {x['direccion']} · {x['precision']} · exacto={x['es_portal_exacto']} · "
                  f"{x.get('aviso', '')[:60]}")
        comprobar(b["resultados"] and b["portales_exactos"] == 0
                  and all(x["precision"] == "calle" and "aviso" in x for x in b["resultados"]),
                  "calle sin número: no avisa de que es una calle entera")
        comprobar("No calcules" in b["nota"], "calle sin número: la nota no pide el número")
        comprobar(all("PASEO PASEO" not in x["direccion"].upper()
                      and x["direccion"] != x["direccion"].upper()
                      and "Madrid" in x["direccion"] for x in b["resultados"]),
                  "calle sin número: la dirección no está limpia")

        print("\n== punto aislado de campo")
        r = datos(await cliente.call_tool("recomendar_local",
                                          {"lat": CAMPO[0], "lon": CAMPO[1]}))
        m = r["nivel_de_movimiento"]
        print(f"   {m['nombre']} (~{m['pasos_laborable']} personas al día): {m['frase']}")
        comprobar(m["muy_poco_paso"] and m["nombre"] == "Muy poco paso"
                  and "casi no pasa gente andando" in (m["aviso"] or ""),
                  "campo: no sale «Muy poco paso» con su aviso")
        z = datos(await cliente.call_tool("informe_de_zona",
                                          {"lat": CAMPO[0], "lon": CAMPO[1]}))
        acc, ent = z["bloques"][6]["datos"], z["bloques"][7]["datos"]
        print(f"   accesos: {acc['nivel']} · entorno: {ent['tipo']} "
              f"(~{ent['vecinos']} vecinos a 1 km)")
        comprobar(ent["tipo"] == "aislado", "campo: el entorno no sale aislado")

        print("\n== punto fuera de la Comunidad de Madrid")
        for h in ("recomendar_local", "perfil_por_horas", "informe_de_zona"):
            r = await cliente.call_tool(h, {"lat": FUERA[0], "lon": FUERA[1]})
            texto = r.content[0].text if r.content else ""
            comprobar(es_error(r) and "fuera de la Comunidad de Madrid" in texto,
                      f"{h}: no da un error claro fuera de la Comunidad")
            print(f"   {h}: error={es_error(r)} · {texto[:90]}")

    print("\nRESULTADO:", "todo correcto" if not fallos else f"{len(fallos)} fallos")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
