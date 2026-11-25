# 2026-11-25 · Datos del 25 de noviembre y dos ideas de futuro

La actualización automática de los datos del 2026-11-25 (#3) se generó con el código de
antes de quitar «Oficinas de farmacia». La autora la aceptó y resolvió a mano dos conflictos
en `docs/fuentes.md`. Esta ronda deja todo coherente con los datos nuevos y añade dos ideas
a «Siguientes pasos». No cambia ningún cálculo ni supuesto: desde `c44d70f` solo cambian
datos y documentación.

## «Oficinas de farmacia», otra vez fuera

- Habían vuelto dos filas a `docs/fuentes.md`: la del portal y la capa `farmacias` en
  «Datos procesados». Quitadas.
- No aparecía en el README, en `datos/LICENCIAS.md` ni en
  `datos/procesados/informe/fuentes.json`.
- Fuera de `docs/registro/`, «farmac» solo queda en un comentario de `src/supuestos.py`. Ese
  comentario habla de la categoría «Otros» de los locales, no de este conjunto.
- Con el código actual, la próxima actualización semanal ya no lo descarga.
- Quedan 15 conjuntos descargados y 15 en uso.

## `docs/fuentes.md` y fechas

- **Sin marcas de conflicto.**
- **Cifras de «Datos procesados»:** coinciden con los ficheros en git.
  - `secciones_censales`: 4.518;
  - `centros_educativos`: 3.851;
  - `centros_sanitarios`: 15.739;
  - `hosteleria_osm`: 15.690;
  - `hosteleria_madrid_capital`: 17.150.
  - Desfibriladores: 13.664 filas de origen, igual que las del CSV del portal.
- **Tablas del README:** iguales a las que genera `src/tablas_readme.py`.
- **Fecha de descarga:** pasa del 2026-11-16 al 2026-11-25 en el README («Datos») y en
  `datos/LICENCIAS.md`. El flujo no la cambia solo. En LICENCIAS, los ficheros del censo,
  los datos de OSM, los GTFS del CRTM (publicados hasta el 2026-11-24) y su demanda
  (2026-11-18) llevan las fechas de `docs/fuentes.md`.

## Comprobaciones

| Prueba | Resultado |
|---|---|
| `python src/comprobar_datos.py` | 38 comprobaciones, 0 con fallo |
| `python mcp/probar_cliente.py` | Todo correcto |
| AppTest: Informe y comparación, con y sin tipo, y sus PDF | 34 de 34 bien. Ocho textos obligatorios, 15 filas del portal y ninguna «farmacia» |
| Chromium sin interfaz, al rehacer las capturas | Sin errores de JavaScript |

## Los tres ejemplos: datos del 16 de noviembre frente a los del 25

Las dos versiones se calcularon el mismo día (2026-11-25): los datos del 16 desde `c44d70f`,
en un `git worktree` aparte, y los del 25 desde el repositorio. Las diferencias vienen solo
de los datos nuevos.

| Punto | Movimiento | Pasan en un laborable (≈) | Clientes principales (laborable) | Locales en el radio | Precios | Transporte |
|---|---|---|---|---|---|---|
| Campus de Vicálvaro | Mucho paso (igual) | 22.670 → **22.747** | vecinos 34 %, universitarios 32 %, viajeros 27 % (igual) | 27 (igual) | económica (igual) | Muy bien comunicado (igual) |
| Centro de Fuenlabrada | Muchísimo paso (igual) | 46.152 → **45.257** | viajeros 71 → **70 %**, vecinos 26 % | 25 (igual) | económica (igual) | Muy bien comunicado (igual) |
| Plaza Mayor de Griñón | Poco paso (igual) | 3.066 → **3.079** | vecinos 41 %, familias con niños 35 %, pacientes 23 → **24 %** | 2 (igual) | media (igual) | Poco transporte (igual) |

Huellas de `src/resumen_ejemplos.py`:

- **Vicálvaro:** `4f72caef99b6` → `e675fc22bd1a`.
- **Fuenlabrada:** `22f81d1d7023` → `a5d2bcc287cf`.
- **Griñón:** `3ffb73fdff1e` → `a71556c65459`.

**No cambian:**

- los niveles de movimiento;
- los titulares;
- las cuatro respuestas del Resumen de los tres ejemplos;
- la tabla de los tres puntos del README.

**Lo que cambia en pantalla** (texto de todas las vistas, comparado entre las dos versiones):

- **Vicálvaro:**
  - Pasos de viajeros, ~12.372 → ~12.448.
  - Con «Bar de barrio», de cada 10 clientes posibles en un laborable: «3 viajeros ·
    3 vecinos · 3 universitarios · 1 de otro tipo» pasa a «4 viajeros · 3 vecinos ·
    3 universitarios».
  - Autobús urbano a 300 m, 1.199 → 1.221 vehículos al día. A 800 m, 1.692 → 1.714.
  - Alojamientos turísticos inscritos en el municipio de Madrid, 6.007 → 5.945.
  - Gente en domingo en la comparación, ≈9.600 → ≈9.700.
  - Varias visitas posibles por franja cambian en unas pocas unidades.
- **Fuenlabrada:**
  - Gente que pasa, ≈46.000 → ≈45.000.
  - Cercanías C5 a 60 m, 293 → 253 vehículos al día. El día típico de Cercanías pasa del
    jueves 2026-11-12 al jueves 2026-12-17 (`salidas_paradas_dias.json`). También cambian
    los días típicos de las demás redes, salvo Metro.
  - Con «Bar de barrio»:
    - La hora con más clientes de un laborable pasa de las 18 a las 19. La respuesta
      del Resumen sigue siendo «De 18 a 21», y la lista de comprobaciones dice ahora «a
      las 19».
    - La franja fuerte de los viajeros pasa de «media tarde» a «tarde-noche».
    - Reparto de un laborable:
      - cañas con raciones, 46 → 47 %;
      - meriendas, 24 → 22 %;
      - almuerzos, 16 → 18 %;
      - desayunos, 14 → 13 %.
  - Índice de precios del sábado, 1,33 → 1,34, y del domingo, 1,32 → 1,33. La gama no
    cambia.
- **Griñón:**
  - Pasos de pacientes, ~568 → ~582.
  - Con «Bar de barrio», desayunos 41 → 40 % y almuerzos 18 → 19 %.
  - El sábado, con «Bar de barrio», la hora con más clientes pasa de las 13 a las 12. Las
    tres horas con más clientes siguen siendo las mismas: 12, 13 y 14.
- **Punto sin colegios** (calle de Serrano):
  - La hora punta de paso pasa de «De 8 a 10 y a las 18» a «A las 8 y de 18 a 20».
  - Locales a 1 km, 965 → 966.
- **En todas las vistas:** la fecha de descarga (pie, ficha técnica y tabla de fuentes)
  pasa al 2026-11-25.

## PDF y capturas

- **PDF de muestra** de `docs/ejemplos/`: rehechos con «Bar de barrio». Su texto solo
  cambia en las cifras de arriba, en las fechas y en el commit de la ficha técnica.
- **Capturas rehechas:** solo las 39 que enseñan alguna cifra o fecha que cambia.
  - Las 28 `*-entera`:
    - Resumen e Informe de los cuatro puntos, a 1.440, 1.920 y 390 px;
    - comparación y planes, a 1.440 y 390 px.
    - Todas llevan la fecha de descarga en el pie. Las del Informe y la comparación
      llevan además cifras que cambian.
  - Arriba del Informe en portátil, por la ficha técnica con «Fecha de los datos»:
    - `portatil-vicalvaro-informe`, `portatil-fuenlabrada-informe` y
      `portatil-grinon-informe`;
    - `portatil-informe-botones` y `portatil-informe-planes`.
  - `portatil-informe-indice`: la tarjeta de turismo de «Mercado», 6.007 → 5.945.
  - `portatil-comparar-elegir`, `portatil-pie` y `movil-pie`: fecha en el pie.
  - `portatil-portada-fuentes` y `movil-portada-fuentes`: fechas de la tabla de fuentes.
- **No se tocan las demás.** No enseñan ninguna cifra que cambie:
  - las de la parte de arriba del Resumen, cuyas respuestas son iguales;
  - las del Informe en el móvil, donde la ficha técnica queda fuera de la pantalla;
  - la tarjeta abierta, cuya explicación queda fuera de la pantalla.
  - Los gráficos por horas de algunas de ellas cambian un poco, sin que cambie ningún
    número visible.

## Siguientes pasos (README)

Dos ideas nuevas, sin fechas:

- **Más idiomas** (inglés y chino, entre otros), para hosteleros que no tienen el español
  como primera lengua.
- **Una versión para otros negocios de barrio** (peluquería, panadería, tienda de
  alimentación…). La gente que pasa se calcula igual; lo que cambia es qué parte se para en
  cada tipo de negocio y a qué hora.

## Etiqueta

`v1.0.2-datamad-final`.
