"""BARómetro: comparación de dos locales.

    from comparar import comparar
    c = comparar(a, b)

`a` y `b` son los resultados de dos puntos: {"nombre", "perfil", "informe", "rec", "mov"}
(perfil_horario(), informe_local(), recomendar() y nivel_movimiento()). No calcula nada
nuevo: pone lado a lado lo que ya dicen esas funciones y, en cada aspecto, dice cuál sale
mejor, sin exagerar:

  - si la diferencia es pequeña (supuestos.COMPARAR_DIFERENCIA_PEQUENA), «diferencia
    pequeña, no decide»;
  - si la fiabilidad de alguno de los dos es baja, tampoco decide;
  - en lo que no es mejor ni peor (qué gente pasa, la gama de precios), lo dice.

El resumen final son dos o tres frases y no declara un ganador: es una ORIENTACIÓN, no una
garantía. Lo usan la aplicación web, el documento descargable y el servidor MCP. No nombra
ningún local ni guarda nada.
"""

from __future__ import annotations

import supuestos as S
from calle import (CLIENTE_CALLE, FIABILIDAD, MOMENTO_CALLE, PRECIO_CALLE, bloque_inf,
                   clientes_principales, dec, grupos_horas, hora_de_grupo, horas_calle,
                   lista_y, mayus, miles, ofertas, rec_dia, redondo, unas)

AVISO = ("Es una orientación con datos abiertos y estimaciones, no una garantía. No dice "
         "qué local es mejor: dice en qué se diferencian. Compruébalo en persona en los dos "
         "sitios.")
NIVELES = ["baja", "media", "alta"]
NO_DECIDE = "Diferencia pequeña, no decide."
DIAS = {"laborable": "Día de diario", "fin_de_semana": "Sábado", "domingo": "Domingo"}
MODOS_CORTO = {"Autobús urbano": "autobús", "Autobús interurbano": "autobús"}


def _conf(*rs: dict | None) -> str:
    """La fiabilidad de una fila es la más baja de las dos."""
    v = [r.get("confianza", "baja") for r in rs if r]
    return min(v, key=NIVELES.index) if v else "baja"


def _fila(clave: str, aspecto: str, a: dict, b: dict, mejor: str | None, veredicto: str,
          fiabilidad: str | None = None, corto: str = "") -> dict:
    return {"clave": clave, "aspecto": aspecto, "a": a, "b": b, "mejor": mejor,
            "veredicto": veredicto, "fiabilidad": fiabilidad,
            "fiabilidad_texto": FIABILIDAD[fiabilidad][1] if fiabilidad else "",
            "corto": corto}


def _lado(titulo: str, detalle: str = "", valor: float | None = None) -> dict:
    return {"titulo": titulo, "detalle": detalle, "valor": valor}


def _mayor(va: float, vb: float, na: str, nb: str, que: str, conf: str,
           minimo: float = 0.0, plural: bool = False) -> tuple[str | None, str]:
    """Quién tiene la cifra mayor y cómo decirlo. `que` completa «… en X»."""
    tope = max(va, vb)
    if tope <= 0 or abs(va - vb) / tope < S.COMPARAR_DIFERENCIA_PEQUENA \
            or abs(va - vb) < minimo:
        return None, NO_DECIDE
    lado, nombre = ("a", na) if va > vb else ("b", nb)
    veces = tope / max(min(va, vb), 1e-9)
    cuanto = (("muchos más" if veces >= 3 else "bastantes más" if veces >= 1.5
               else "algunos más") if plural else
              ("mucha más" if veces >= 3 else "bastante más" if veces >= 1.5 else "algo más"))
    if conf == "baja":
        return None, (f"{nombre} tiene {cuanto} {que}, pero la fiabilidad es baja: no "
                      "decide.")
    return lado, f"{mayus(cuanto)} {que} en {nombre}."


def _gente(res: dict, dia: str) -> float:
    return float(res["perfil"]["horas"].loc[dia]["total"].sum())


def _quien(res: dict, dia: str) -> list[str]:
    return [CLIENTE_CALLE[t] for t, _ in clientes_principales(res["rec"], dia)]


def _punta(res: dict) -> tuple[str, float, int | None]:
    rec = res["rec"]
    g = grupos_horas(rec, "laborable")
    if not g:
        return "Sin horas punta", 0.0, None
    h = hora_de_grupo(rec, "laborable", g[0])
    total = {int(x["hora"][:2]): x["total"]
             for x in rec["a_que_hora"]["detalle"]["laborable"]["horas_punta"]}
    return mayus(horas_calle(g)), float(total[h]), h


def _oferta(res: dict) -> tuple[str, float, str]:
    rec = res["rec"]
    of = ofertas(rec)
    mo = rec["que_vender"]["momentos"]["laborable"]
    if not of:
        return "Sin datos", 0.0, ""
    return mayus(lista_y([MOMENTO_CALLE[m] for m in of])), float(mo.get(of[0], 0)), of[0]


def _modos(acc: dict) -> str:
    """Modos a menos de ACCESOS_RADIO_LEJOS_M, en pocas palabras: «metro (9), autobús»."""
    out, bus = [], 0
    for modo, v in acc["lejos"].items():
        if modo in MODOS_CORTO:
            bus += v["lineas"]
        else:
            n = v["nombres_lineas"]
            out.append(f"{modo} ({', '.join(n[:4])}{'…' if len(n) > 4 else ''})")
    if bus:
        out.append(f"autobús ({bus} {'línea' if bus == 1 else 'líneas'})")
    return lista_y(out) if out else "ninguna parada a 10 minutos andando"


def _locales(n: int) -> str:
    return "1 bar o restaurante" if n == 1 else f"{miles(n)} bares y restaurantes"


def comparar(a: dict, b: dict) -> dict:
    """Comparación de dos locales, fila a fila, con un resumen de dos o tres frases."""
    na, nb = a["nombre"], b["nombre"]
    filas = []

    # ---- nivel de movimiento
    ma, mb = a["mov"], b["mov"]
    pa, pb = float(ma["pasos_laborable"]), float(mb["pasos_laborable"])
    mejor, ver = _mayor(pa, pb, na, nb, "gente de paso", "media")
    if mejor and ma["nivel"] == mb["nivel"]:
        ver = f"El mismo nivel; {ver[0].lower()}{ver[1:]}"
    filas.append(_fila(
        "movimiento", "Nivel de movimiento",
        _lado(ma["nombre"], f"Nivel {ma['nivel']} de 5: {ma['frase']}.", ma["nivel"]),
        _lado(mb["nombre"], f"Nivel {mb['nivel']} de 5: {mb['frase']}.", mb["nivel"]),
        mejor, ver, "media", "movimiento"))

    # ---- gente en un día de diario, en sábado y en domingo
    for dia, nombre_dia, corto in (("laborable", "un día de diario", ""),
                                   ("fin_de_semana", "un sábado", "gente en sábado"),
                                   ("domingo", "un domingo", "gente en domingo")):
        ga, gb = _gente(a, dia), _gente(b, dia)
        mejor, ver = _mayor(ga, gb, na, nb, f"gente en {nombre_dia}", "media")
        filas.append(_fila(
            f"gente_{dia}", f"Gente que pasa en {nombre_dia}",
            _lado(f"≈{redondo(ga)} personas", "Estimación: pasan a menos de "
                  f"{S.RADIO_M} m a lo largo del día.", ga),
            _lado(f"≈{redondo(gb)} personas", "Estimación: pasan a menos de "
                  f"{S.RADIO_M} m a lo largo del día.", gb),
            mejor, ver, "media", corto))

    # ---- quién pasa
    qa, qb = _quien(a, "laborable"), _quien(b, "laborable")
    sa, sb = _quien(a, "fin_de_semana"), _quien(b, "fin_de_semana")
    da_, db_ = _quien(a, "domingo"), _quien(b, "domingo")

    def finde(s: list[str], d: list[str]) -> str:
        return " ".join(x for x in (f"Los sábados, sobre todo {s[0]}." if s else "",
                                    f"Los domingos, sobre todo {d[0]}." if d else "") if x)
    ra = rec_dia(a["rec"]["a_quien"]["recomendaciones"], "laborable")
    rb = rec_dia(b["rec"]["a_quien"]["recomendaciones"], "laborable")
    filas.append(_fila(
        "quien", "Quién pasa",
        _lado(mayus(lista_y(qa)) if qa else "Poca gente", finde(sa, da_)),
        _lado(mayus(lista_y(qb)) if qb else "Poca gente", finde(sb, db_)),
        None, ("Pasa el mismo tipo de gente en los dos." if set(qa) == set(qb) else
               "Públicos distintos: no es mejor ni peor, depende de lo que quieras "
               "ofrecer."),
        _conf(ra[0] if ra else None, rb[0] if rb else None), "público"))

    # ---- horas punta
    (ta, va, ha), (tb, vb, hb) = _punta(a), _punta(b)
    ra = rec_dia(a["rec"]["a_que_hora"]["recomendaciones"], "laborable")
    rb = rec_dia(b["rec"]["a_que_hora"]["recomendaciones"], "laborable")
    conf = _conf(ra[0] if ra else None, rb[0] if rb else None)
    mejor, ver = _mayor(va, vb, na, nb, "gente en su mejor hora", conf)
    filas.append(_fila(
        "horas", "Horas punta (día de diario)",
        _lado(ta, f"Unas {unas(va)} personas a las {ha}, su mejor hora." if ha is not None
              else "", va),
        _lado(tb, f"Unas {unas(vb)} personas a las {hb}, su mejor hora." if hb is not None
              else "", vb),
        mejor, ver, conf, "gente en la mejor hora"))

    # ---- qué conviene ofrecer
    (oa, ca, moa), (ob, cb, mob) = _oferta(a), _oferta(b)
    ra = rec_dia(a["rec"]["que_vender"]["recomendaciones"], "laborable")
    rb = rec_dia(b["rec"]["que_vender"]["recomendaciones"], "laborable")
    conf = _conf(ra[0] if ra else None, rb[0] if rb else None)
    mejor, ver = _mayor(ca, cb, na, nb, "posibles clientes en su mejor momento", conf,
                       plural=True)
    if oa != ob and mejor is None and ver == NO_DECIDE:
        ver = "Encajan cosas distintas; en posibles clientes, diferencia pequeña: no decide."
    filas.append(_fila(
        "ofrecer", "Qué conviene ofrecer",
        _lado(oa, f"Unos {unas(ca)} posibles clientes para {MOMENTO_CALLE[moa]} en un día "
              "de diario." if moa else "", ca),
        _lado(ob, f"Unos {unas(cb)} posibles clientes para {MOMENTO_CALLE[mob]} en un día "
              "de diario." if mob else "", cb),
        mejor, ver, conf, "posibles clientes"))

    # ---- gama de precios
    da, db = bloque_inf(a["informe"], "precios")["datos"], bloque_inf(b["informe"], "precios")["datos"]
    ga, gb = da["gama_ajustada"]["gama"]["semana"], db["gama_ajustada"]["gama"]["semana"]
    conf = _conf(a["rec"]["a_que_precio"]["recomendaciones"][0],
                 b["rec"]["a_que_precio"]["recomendaciones"][0])
    filas.append(_fila(
        "precios", "Gama de precios",
        _lado(f"Precios {PRECIO_CALLE.get(ga, ga)}",
              f"Renta de los vecinos: ×{dec(bloque_inf(a['informe'], 'mercado')['datos']['renta_relativa'], 2)} la media de la Comunidad."),
        _lado(f"Precios {PRECIO_CALLE.get(gb, gb)}",
              f"Renta de los vecinos: ×{dec(bloque_inf(b['informe'], 'mercado')['datos']['renta_relativa'], 2)} la media de la Comunidad."),
        None, ("La misma gama en los dos." if ga == gb else
               "No es mejor ni peor: es el nivel de precios que encaja con quien pasa.")
        + (" Fiabilidad baja: mira antes los precios de cada zona." if conf == "baja" else ""),
        conf, "precios"))

    # ---- competencia en 300 m
    ka, kb = bloque_inf(a["informe"], "competencia")["datos"], bloque_inf(b["informe"], "competencia")["datos"]
    dudas = []
    if ka["fuente_usada"] != kb["fuente_usada"]:
        dudas.append("los locales se cuentan con fuentes distintas "
                     f"({ka['fuente_usada']} y {kb['fuente_usada']})")
    for k, n in ((ka, na), (kb, nb)):
        cob = k.get("cobertura_osm")
        if cob and cob["relacion"] < S.COBERTURA_OSM_AVISO:
            dudas.append(f"en {n} seguramente faltan locales en el mapa")
    menos = ("a", na) if ka["total"] < kb["total"] else ("b", nb)
    if abs(ka["total"] - kb["total"]) < S.COMPARAR_LOCALES_MINIMOS or \
            abs(ka["total"] - kb["total"]) / max(ka["total"], kb["total"], 1) \
            < S.COMPARAR_DIFERENCIA_PEQUENA:
        mejor, ver = None, NO_DECIDE
    elif dudas:
        mejor, ver = None, (f"Menos locales contados en {menos[1]}, pero "
                            f"{lista_y(dudas)}: no decide.")
    else:
        mejor, ver = menos[0], (f"Menos competencia directa en {menos[1]}. Ojo: pocos "
                                "locales también puede querer decir poca clientela.")

    def tipos(k: dict) -> str:
        t = k.get("comparacion_por_tipo", {})
        uno = {"bar": "bar", "restaurante": "restaurante", "cafeteria": "cafetería"}
        return ", ".join(f"{t[c]['radio']} "
                         + ("de comida rápida" if c == "comida_rapida" else
                            uno[c] if t[c]["radio"] == 1 else n.lower())
                         for c, n in S.TIPOS_COMPETENCIA.items()
                         if c in t and t[c]["radio"]) or "ninguno"
    filas.append(_fila(
        "competencia", f"Competencia a menos de {S.RADIO_M} m",
        _lado(_locales(ka["total"]), f"{mayus(tipos(ka))}. Fuente: {ka['fuente_usada']}.",
              ka["total"]),
        _lado(_locales(kb["total"]), f"{mayus(tipos(kb))}. Fuente: {kb['fuente_usada']}.",
              kb["total"]),
        mejor, ver, "baja" if dudas else "media", "competencia directa"))

    # ---- competencia frente al municipio
    def frente(k: dict, res: dict) -> tuple[str, str, float | None]:
        muni = res["informe"]["municipio"]["nombre"]
        rel = k["relacion_con_media"]
        if k["media_municipio"] < S.HUECO_MEDIA_MINIMA or rel is None:
            return ("No se puede valorar", f"En {muni} hay menos de 1 local de media en un "
                    "círculo como este: la comparación no dice nada.", None)
        return (f"×{dec(rel)} la media", f"Frente a un círculo igual en un punto medio de "
                f"{muni} ({dec(k['media_municipio'])} locales).", float(rel))
    (fa, fda, rva), (fb, fdb, rvb) = frente(ka, a), frente(kb, b)
    if rva is None or rvb is None:
        mejor, ver = None, "En uno de los dos no se puede valorar: no decide."
    elif abs(rva - rvb) / max(rva, rvb, 1e-9) < S.COMPARAR_DIFERENCIA_PEQUENA:
        mejor, ver = None, NO_DECIDE
    else:
        menos = ("a", na) if rva < rvb else ("b", nb)
        if dudas:
            mejor, ver = None, (f"Menos saturado para su municipio en {menos[1]}, pero "
                                f"{lista_y(dudas)}: no decide.")
        else:
            mejor, ver = menos[0], f"Menos saturado para su municipio en {menos[1]}."
    filas.append(_fila("competencia_municipio", "Competencia frente a su municipio",
                       _lado(fa, fda, rva), _lado(fb, fdb, rvb), mejor, ver,
                       "baja" if dudas or rva is None or rvb is None else "media",
                       "saturación frente al municipio"))

    # ---- cómo se llega
    aa, ab = bloque_inf(a["informe"], "accesos")["datos"], bloque_inf(b["informe"], "accesos")["datos"]
    ia, ib = S.ACCESOS_NIVELES.index(aa["nivel"]), S.ACCESOS_NIVELES.index(ab["nivel"])
    mejor = None if ia == ib else ("a" if ia > ib else "b")
    filas.append(_fila(
        "accesos", "Cómo se llega",
        _lado(aa["nivel"], mayus(_modos(aa)) + ".", ia),
        _lado(ab["nivel"], mayus(_modos(ab)) + ".", ib),
        mejor, ("Igual de comunicados." if mejor is None else
                f"Mejor comunicado {na if mejor == 'a' else nb}."), "alta", "transporte"))

    # ---- avisos
    def avisos(res: dict) -> dict:
        r = res["rec"]["riesgos"]
        return {"titulo": ("Nada especial que vigilar" if r[0].get("clave") == "ninguno" else
                           f"{len(r)} {'aviso' if len(r) == 1 else 'avisos'}"),
                "detalle": "", "valor": None, "lista": [x["texto"] for x in r]}
    filas.append(_fila("avisos", "Ojo con esto", avisos(a), avisos(b), None,
                       "Los avisos no se suman ni se comparan: lee los de cada sitio.",
                       None, "avisos"))

    # ---- resumen: dos o tres frases, sin ganador
    gana = {l: [f["corto"] for f in filas if f["mejor"] == l and f["corto"]]
            for l in ("a", "b")}
    resumen = []
    for lado, nombre in (("a", na), ("b", nb)):
        if gana[lado]:
            resumen.append(f"Con estos datos, {nombre} sale mejor en "
                           f"{lista_y(gana[lado])}.")
    if not resumen:
        resumen.append("Con estos datos, ninguno de los dos sale claramente mejor en lo "
                       "que se puede comparar: las diferencias son pequeñas o poco fiables.")
    elif not gana["a"] or not gana["b"]:
        otro = nb if gana["a"] else na
        resumen.append(f"{otro} no sale mejor en ninguno de esos aspectos, pero eso no lo "
                       "descarta: puede encajar con otro tipo de local.")
    poco = [n for n, m in ((na, ma), (nb, mb)) if m["muy_poco_paso"]]
    if poco:
        final = (f"En {lista_y(poco)} pasa muy poca gente andando y ahí estas respuestas "
                 "valen poco; es")
    elif set(qa) == set(qb) or not qa or not qb:
        final = "Es"
    else:
        final = (f"Pasan públicos distintos ({lista_y(qa)} frente a {lista_y(qb)}), y esto "
                 "es")
    resumen.append(final + " una orientación, no una garantía: compruébalo en persona en "
                           "los dos sitios antes de decidir.")

    def horas(res: dict) -> dict:
        return {dia: [round(float(v)) for v in res["perfil"]["horas"].loc[dia]["total"]]
                for dia in DIAS}
    return {"aviso": AVISO, "locales": {"a": na, "b": nb}, "filas": filas,
            "resumen": resumen, "personas_por_hora": {"a": horas(a), "b": horas(b)},
            "nota": ("«Sale mejor» solo se dice cuando la diferencia pasa del "
                     f"{100 * S.COMPARAR_DIFERENCIA_PEQUENA:.0f} % y la fiabilidad no es "
                     "baja. El domingo sirve también, de forma aproximada, para los "
                     "festivos.")}
