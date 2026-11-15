"""BARómetro: clientes posibles según el tipo de local («¿Cuándo tendrías más clientes?»).

    from perfil_horario import perfil_horario
    from tipo_local import clientes_local, sensibilidad
    perfil = perfil_horario(40.4046, -3.6106)
    c = clientes_local(perfil, "bar_barrio")
    c["horas"]      # 72 filas (3 días × 24 horas) × tipos de cliente + «total»
    c["franjas"]    # lo mismo por franjas del día
    s = sensibilidad(perfil, "bar_barrio")   # ¿cambia la hora con más clientes?

Desde la terminal:  python src/tipo_local.py 40.4046 -3.6106 bar_barrio

El perfil por horas (src/perfil_horario.py) cuenta gente que PASA y no cambia. Aquí se
calcula, para un tipo de local, cuántas visitas podría haber cada hora:
  - de cada tipo de cliente que pasa: pasos × tasa de parada de ese tipo de local y hora;
  - de los vecinos, que van a propósito aunque no pasen por delante: población del radio ×
    visitas por vecino y día × reparto por horas.
Son VISITAS POSIBLES PARA TODOS LOS LOCALES DE ESE TIPO A MENOS DE 300 m, no las de un solo
local. Todo es ESTIMACIÓN con supuestos (src/supuestos.py, sección «TIPO DE LOCAL»).
"""

from __future__ import annotations

import sys

import pandas as pd

import supuestos as S
from perfil_horario import DIAS, TIPOS, vec

UNIDAD = f"visitas posibles para todos los locales de ese tipo en {S.RADIO_M} m"
NOMBRES_ESCENARIO = {("tasas", 0.5): "la gente que pasa se para la mitad",
                     ("tasas", 2.0): "la gente que pasa se para el doble",
                     ("visitas", 0.5): "los vecinos van la mitad",
                     ("visitas", 2.0): "los vecinos van el doble"}


def comprobar_tipo(tipo: str | None) -> str | None:
    if tipo is not None and tipo not in S.TIPOS_LOCAL:
        raise ValueError(f"Tipo de local desconocido: {tipo!r}. Valen: "
                         + ", ".join(S.TIPOS_LOCAL))
    return tipo


def clientes_local(perfil: dict, tipo: str, f_tasas: float = 1.0,
                   f_visitas: float = 1.0) -> dict:
    """Visitas posibles por hora y tipo de cliente para un tipo de local (ESTIMACIÓN).
    f_tasas y f_visitas multiplican los supuestos (para el análisis de sensibilidad)."""
    comprobar_tipo(tipo)
    pob = float(perfil["poblacion_radio"])
    filas = []
    for d in DIAS:
        h = perfil["horas"].loc[d]
        rep = vec(S.REPARTO_VISITAS_VECINO[tipo][d])
        rep = rep / rep.sum()
        vecinos = pob * S.VISITAS_VECINO[tipo][d] * f_visitas * rep
        for hh in range(24):
            fila = {"dia": d, "hora": hh}
            for t in TIPOS:
                fila[t] = (vecinos[hh] if t == "vecinos" else
                           float(h.loc[hh, t]) * S.TASA_PARADA[tipo][t].get(hh, 0.0) * f_tasas)
            filas.append(fila)
    horas = pd.DataFrame(filas).set_index(["dia", "hora"])
    horas["total"] = horas[TIPOS].sum(axis=1)
    franja_de = {h: f for f, hs in S.FRANJAS.items() for h in hs}
    fr = horas.reset_index()
    fr["franja"] = pd.Categorical(fr["hora"].map(franja_de), categories=list(S.FRANJAS),
                                  ordered=True)
    franjas = fr.groupby(["dia", "franja"], observed=False)[TIPOS + ["total"]].sum()
    return {"tipo": tipo, "nombre": S.TIPOS_LOCAL[tipo], "horas": horas, "franjas": franjas,
            "unidad": UNIDAD, "es_estimacion": True}


def _resumen_dia(c: dict, d: str) -> dict:
    tot = c["horas"].loc[d]["total"]
    if tot.max() <= 0:
        return {"horas": [], "mejor": None, "franja": None}
    franja_de = {h: f for f, hs in S.FRANJAS.items() for h in hs}
    mejor = int(tot.idxmax())
    return {"horas": sorted(int(h) for h in tot.nlargest(3).index), "mejor": mejor,
            "franja": franja_de[mejor]}


def sensibilidad(perfil: dict, tipo: str) -> dict:
    """Para cada día: las tres horas con más clientes y la franja de la mejor, con los
    supuestos tal cual y con las tasas de parada o las visitas de los vecinos por 0,5 y
    por 2. «estable» es False si en algún caso la mejor hora cae en otra franja del día, a
    más de una hora de la de antes, y cambian al menos dos de las tres horas."""
    base = clientes_local(perfil, tipo)
    casos = {}
    for que in ("tasas", "visitas"):
        for f in S.SENSIBILIDAD_FACTORES:
            kw = {"f_tasas": f} if que == "tasas" else {"f_visitas": f}
            casos[(que, f)] = clientes_local(perfil, tipo, **kw)
    out = {}
    for d in DIAS:
        b = _resumen_dia(base, d)
        esc = []
        for (que, f), c in casos.items():
            r = _resumen_dia(c, d)
            # Cambia de verdad si la mejor hora cae en otra franja, a más de una hora de la de
            # antes, y además cambian al menos dos de las tres horas que se enseñan. (Pasar de
            # las 9 a las 10 cruza el borde de una franja, pero no es otro momento del día; y
            # si las tres horas son las mismas, lo que se enseña no cambia.)
            salta = (r["mejor"] is not None and b["mejor"] is not None
                     and r["franja"] != b["franja"] and abs(r["mejor"] - b["mejor"]) > 1
                     and len(set(r["horas"]) - set(b["horas"])) >= 2)
            esc.append({"supuesto": que, "factor": f, "descripcion": NOMBRES_ESCENARIO[(que, f)],
                        **r, "cambia_franja": salta,
                        "cambian_horas": r["horas"] != b["horas"]})
        out[d] = {**b, "escenarios": esc,
                  "estable": not any(e["cambia_franja"] for e in esc)}
    return out


def gasto_visitas() -> dict:
    """Contraste de las visitas de los vecinos con el gasto medio por persona en
    restauración (Encuesta de Presupuestos Familiares, portal de la Comunidad): euros por
    persona y año que suponen las visitas de todos los tipos de local juntos, con
    PRECIO_VISITA. Tiene que quedar por debajo del gasto y, para ser coherente, por debajo
    de PARTE_GASTO_CERCA_DE_CASA del gasto."""
    from informe_local import gasto_restauracion
    gasto, anyo = gasto_restauracion()
    por_tipo = {}
    for t in S.TIPOS_LOCAL:
        semana = sum(S.DIAS_SEMANA[d] * S.VISITAS_VECINO[t][d] for d in DIAS)
        por_tipo[t] = {"visitas_semana": semana, "visitas_anyo": semana * 365 / 7,
                       "euros_anyo": semana * 365 / 7 * S.PRECIO_VISITA[t]}
    total = sum(v["euros_anyo"] for v in por_tipo.values())
    return {"gasto_persona": gasto, "anyo": anyo, "por_tipo": por_tipo, "total_euros": total,
            "parte": total / gasto, "limite": S.PARTE_GASTO_CERCA_DE_CASA,
            "no_supera": total <= gasto,
            "coherente": total <= S.PARTE_GASTO_CERCA_DE_CASA * gasto}


def main(argv: list[str]) -> int:
    from perfil_horario import NOMBRE_DIA, perfil_horario
    lat, lon = float(argv[0]), float(argv[1])
    tipos = [argv[2]] if len(argv) > 2 else list(S.TIPOS_LOCAL)
    p = perfil_horario(lat, lon)
    pd.set_option("display.width", 200)
    for t in tipos:
        c = clientes_local(p, t)
        s = sensibilidad(p, t)
        print(f"\n### {S.TIPOS_LOCAL[t]} · {UNIDAD}")
        for d in DIAS:
            tot = c["horas"].loc[d]["total"]
            print(f"  {NOMBRE_DIA[d]:9s} {tot.sum():6.0f} al día · más clientes: "
                  f"{s[d]['horas']} ({s[d]['franja']}) · "
                  f"{'estable' if s[d]['estable'] else 'CAMBIA con los supuestos'}")
    g = gasto_visitas()
    print(f"\nVisitas de los vecinos: ≈{g['total_euros']:.0f} € por persona y año, "
          f"{100 * g['parte']:.0f} % del gasto en restauración ({g['gasto_persona']:.2f} €, "
          f"EPF {g['anyo']}); límite {100 * g['limite']:.0f} %.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
