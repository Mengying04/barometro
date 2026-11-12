# 2026-11-12 · Día típico del transporte: línea 3, viajes sin hora y líneas de la Sierra

## Qué se pidió

En el laborable típico, la línea 3 de Metro, la C9 de Cercanías y algunas líneas de
autobús no tenían servicio y no aportaban viajeros. Había que averiguar por qué, elegir
la solución más fiel a la realidad, regenerar, comparar los tres ejemplos, probar un
punto junto a la línea 3 y documentarlo.

## Qué se ha encontrado

No era un solo problema, sino cuatro distintos. Solo uno se arreglaba cambiando de día.

| Red | Qué pasaba | Causa |
|---|---|---|
| Metro, línea 3 | Ningún viaje, ningún día | El GTFS de Metro (versión 27/05/2025) trae los 18 andenes de la línea, de Villaverde Alto a Moncloa, pero cero viajes y cero horas de paso. No hay obras que lo expliquen: es un hueco del fichero. Es el único GTFS publicado; hoy se ha comprobado que el CRTM no lo ha modificado desde el 30/05/2025. |
| Cercanías, C9 | Viajes solo 5 días del mes (30 y 31 de octubre; 16, 17 y 18 de noviembre) | La línea Cercedilla-Cotos está cerrada por obras de renovación desde mayo de 2024. Que no salga es lo correcto. |
| Interurbanos: 19 líneas de la Sierra (610, 611, 612, 613, 680 a 688, 690, 691, 696, N602…) y 2 urbanas | Solo «circulan» los martes | Defecto de calendario del GTFS: sus servicios de miércoles, jueves y viernes valen para un único día (28, 29 y 30 de octubre), mientras que el de los martes vale todo el año. El día elegido era un jueves. |
| Interurbanos: 30 líneas (480 a 499, 350 a 355, 665 a 667, nocturnas N802, N804, N808…) y 11 urbanas (Pinto, Valdemoro, Arganda, San Lorenzo de El Escorial, Tres Cantos, Arroyomolinos) | Se descartaban todos sus viajes | El código los tomaba por «viajes de relleno» porque todas sus paradas llevan la misma hora. **Son viajes reales**, con su calendario y su hora de salida; solo les falta la hora en cada parada. La salida está en las horas de paso o, cuando estas llevan el relleno 01:00:00 o 01:00:01, dentro del identificador del viaje. También afectaba a 36 líneas interurbanas que mezclan viajes de los dos tipos (la 492 tenía 324 de sus 325 viajes así). |

Otras líneas sin servicio, que están bien como están:

- **EMT:** 172SF (variante de sábados y festivos) y SE721, SE730 y SE766 (servicios
  especiales sin ningún viaje en el fichero).
- **Sin ningún viaje en el fichero:** 12 interurbanas (635, 720 a 728, N702 y N908) y
  5 urbanas. No hay nada que recuperar.
- **Solo de fin de semana:** 196, 414, 692, 819, FS1, FS2 y 199A.

## Opciones y decisión

Se explicaron las opciones a la autora antes de cambiar nada. Eligió las tres
recomendadas.

**Línea 3 de Metro.**

- *Elegida: reconstruirla.* Con sus andenes del propio GTFS y la frecuencia media de
  líneas parecidas. Es una estimación y se marca.
- Buscar un GTFS antiguo archivado con la frecuencia real de entonces. Necesitaba abrir
  el acceso a archive.org y una fuente nueva, y podía no existir copia.
- Dejarla fuera con un aviso. Los locales junto a la línea seguirían sin sus viajeros.

**Autobuses.**

- *Elegida: recuperar los viajes sin hora por parada y elegir en cada red el día en que
  circulan más líneas.*
- Día típico propio de cada línea. Más complejo, con resultado casi igual, y trataría
  como diaria una línea que de verdad solo sale algunos días.
- Solo cambiar el día. Arreglaba las 21 líneas de la Sierra, pero no las 41 líneas ni
  el 15 % de viajes sin hora por parada.

**C9.** *Elegida: dejarla fuera*, de forma explícita y explicada, en lugar de incluirla
con el horario de un día suelto.

## Qué se ha hecho

Todo en `src/procesar_perfil.py`, con los supuestos en `src/supuestos.py` (sección
«Transporte público»).

### 1. Viajes sin hora en cada parada

`cargar_red()` ya no los descarta. Para cada viaje de 3 o más paradas con todas a la
misma hora:

- la salida es la hora de sus paradas o, si es el relleno 01:00:00 o 01:00:01
  (`GTFS_HORAS_RELLENO`), la que figura en el identificador del viaje;
- la hora de cada parada se **estima**: salida + número de orden de la parada × el
  tiempo mediano entre paradas de los viajes con horario de la misma red (117 segundos
  en interurbanos y 90 en urbanos);
- se descartan los repetidos (misma línea, sentido, servicio y salida que un viaje con
  horario) y los que no tienen hora de salida en ningún sitio.

| Red | Viajes recuperados | Líneas | Repetidos | Sin hora de salida |
|---|---|---|---|---|
| Interurbanos | 5.759 | 68 | 56 | 11 |
| Urbanos | 1.600 | 24 | 54 | 0 |

El número de vehículos al día es un dato. La hora en cada parada es una estimación.

### 2. Elección del día

`elegir_dias()`: entre los martes, miércoles y jueves (y entre los sábados) de las 4
primeras semanas de vigencia, se quitan los días con menos del 80 % de los viajes del
día mediano (`GTFS_DIA_MINIMO_VIAJES`; festivos) y se toma el día en que circulan más
líneas. Entre los empatados, el de número de viajes mediano, como antes.

| Red | Laborable antes | Laborable ahora | Líneas con servicio |
|---|---|---|---|
| Metro | 2026-05-13 | 2026-05-13 | 12 de 13, más la 3 reconstruida |
| Metro Ligero | 2026-11-19 | 2026-11-25 | 4 de 4 |
| Cercanías | 2026-11-12 | 2026-11-12 | 11 de 12 (sin la C9) |
| EMT | 2026-11-19 | 2026-11-25 | 234 de 238 |
| Interurbanos | 2026-11-26 (jueves) | 2026-11-24 (martes) | 335 de 354 (antes 287) |
| Urbanos | 2026-11-26 (jueves) | 2026-11-24 (martes) | 110 de 117 (antes 97) |

En Metro Ligero y EMT cambia la fecha, pero no el servicio: todos los laborables de la
muestra son iguales y la muestra empieza hoy, dos días después de la vez anterior. El
sábado es el mismo en todas las redes (2026-11-21; 2026-05-09 en Metro).

### 3. Línea 3 de Metro (estimación)

`lineas_reconstruidas()`, con la configuración en `GTFS_LINEAS_RECONSTRUIDAS`:

- **Dónde:** los 18 andenes sin viajes del GTFS (se comprueba que son exactamente los de
  la línea 3; si el CRTM publica un fichero con viajes, el programa se para y pide quitar
  la reconstrucción) y El Casar, a donde la línea llega desde abril de 2025 y que en el
  GTFS solo tiene el andén de la línea 12.
- **Cuántos trenes:** en cada hora, la media de las líneas 1, 2, 4 y 5 (de cada una, su
  estación mediana). Son las líneas del centro de longitud y frecuencia parecidas.
  Resultado: **461 trenes al día en laborable y 370 en sábado** por estación, sumando
  los dos sentidos (las cuatro líneas modelo tienen 446, 482, 502 y 410).
- **Cómo se marca:** columna nueva `origen_pasos` en `salidas_paradas.parquet` y columna
  `estimada` en `lineas_paradas.parquet`. El informe añade `lineas_estimadas` en «Cómo
  se llega» y una frase que dice que los vehículos de la línea 3 son una estimación. La
  aplicación lo repite bajo la tabla de transporte. El perfil cuenta en «elementos» las
  paradas con trenes estimados.

### 4. C9 fuera

`GTFS_LINEAS_EXCLUIDAS = {"cercanias": ("C9",)}`. Sin esto, la regla de «más líneas»
habría elegido uno de los días sueltos en que el GTFS le pone trenes.

## Efecto en los datos

| | Antes | Ahora |
|---|---|---|
| Paradas con servicio | 14.401 | 15.207 |
| Pasos de Metro en laborable | 113.756 | 122.515 |
| Pasos de interurbanos en laborable | 691.865 | 880.577 |
| Pasos de urbanos en laborable | 200.362 | 240.476 |
| Pares parada-línea-sentido | — | 36.484 |

Los viajeros de cada red son los mismos (demanda del CRTM) y se reparten entre más
pasos de vehículos, así que bajan las personas por vehículo:

| Red | Laborable antes | Laborable ahora | Sábado antes | Sábado ahora |
|---|---|---|---|---|
| Metro | 44,3 | 41,2 (−7 %) | 37,4 | 34,8 |
| Interurbanos y urbanos | 2,6 | 2,0 (−20 %) | 1,8 | 1,4 |
| EMT | 3,6 | 3,6 | 3,2 | 3,2 |
| Cercanías | 72,8 | 72,8 | 56,5 | 56,5 |

La bajada en autobuses es mayor de la que se anunció al plantear las opciones (en torno
al 13 %): además de los viajes sin hora se suman las líneas de la Sierra.

### Referencia de movimiento

Regenerada (`python src/movimiento.py --generar`, 29 segundos, 4.518 secciones).

| Parte de la referencia | 10 % | 30 % | 50 % | 70 % | 90 % |
|---|---|---|---|---|---|
| Antes | 433 | 5.982 | 10.656 | 15.118 | 24.701 |
| Ahora | 430 | 6.001 | 10.675 | 15.263 | 24.899 |

Bajan 2.263 secciones (casi todas un poco: solo 9 más de un 10 %), suben 576 (107 más de
un 20 %: las que tienen cerca la línea 3 o las líneas de autobús recuperadas) y 1.679
quedan igual.

## Los tres ejemplos, antes y después

En los tres, lo único que cambia en el perfil son los viajeros; los demás tipos de
cliente quedan idénticos hora a hora. El nivel de movimiento, el nivel de accesos, las
franjas recomendadas, qué vender y a qué precio son los mismos.

| Punto | Personas en laborable | Viajeros en laborable | Posición en la referencia | Por qué |
|---|---|---|---|---|
| Campus de Vicálvaro | 23.296 → 22.592 (−3 %) | 12.998 → 12.293 (−5 %) | 0,883 → 0,874 (Mucho paso) | Sus viajeros vienen sobre todo del Metro (línea 9 a 120 m). La estación tiene los mismos trenes, pero cada tren reparte un 7 % menos de gente porque la demanda de la red se reparte ahora también entre los trenes de la línea 3. Los autobuses de la EMT no cambian. |
| Centro de Fuenlabrada | 46.100 → 45.852 (−0,5 %) | 40.986 → 40.737 (−0,6 %) | 0,986 → 0,983 (Muchísimo paso) | Dos efectos que casi se anulan. Baja el Metro (línea 12, −7 % por tren) y bajan un 20 % las personas por autobús; pero aparecen 5 líneas interurbanas que antes no salían (491, 492, 496, 497 y N804): de 5 líneas y 303 autobuses a 10 líneas y 1.049, con una parada a 160 m en vez de a 260 m. Cercanías no cambia (dato propio de la estación). |
| Plaza Mayor de Griñón | 3.082 → 3.066 (−0,5 %) | 74 → 59 (−20 %) | 0,189 → 0,190 (Poco paso) | Tiene las mismas 4 líneas interurbanas y los mismos 139 autobuses. Solo cambia la gente por autobús, que baja un 20 % al repartirse la demanda entre los autobuses recuperados en el resto de la red. Los viajeros pesan muy poco aquí. |

Otras diferencias, todas consecuencia de lo anterior:

- **Gama de precios ajustada a la clientela.** Cambia el reparto por tipo de cliente en
  milésimas (Vicálvaro: viajeros de 0,287 a 0,276; el valor de laborable, de 1,15 a
  1,14). La gama recomendada no cambia en ninguno.
- **Fuenlabrada, sábado.** Las dos primeras horas punta, que estaban empatadas a 1.706
  personas, cambian de orden (ahora 12:00 con 1.694 y 11:00 con 1.693). Son las mismas
  tres horas.
- **Bloque «Cómo se llega».** Cambian las fechas de los días usados y las notas. En
  Fuenlabrada, además, las líneas y autobuses interurbanos ya dichos.
- **Mediana de la referencia:** de 10.656 a 10.675 en los tres.

## Punto junto a una estación de la línea 3

| Punto | Personas en laborable | Viajeros | Movimiento | Cómo se llega |
|---|---|---|---|---|
| Lavapiés (40,4087, −3,7010), a 20 m de la estación | 20.186 → 39.159 | 423 → 19.395 | Mucho paso (0,836) → Muchísimo paso (0,974) | Bien comunicado → Muy bien comunicado: Metro a 20 m (línea 3, 461 trenes, estimación) |
| Villaverde Alto (40,3411, −3,7125) | 59.563 → 78.509 | 53.443 → 72.390 | Muchísimo paso (0,994 → 0,998) | Muy bien comunicado en los dos casos; ahora aparece el Metro a 20 m además de Cercanías |

En Lavapiés:

- los viajeros pasan de casi nada a ser la mitad del paso en las horas punta (a las
  9:00, 49 % viajeros y 45 % vecinos);
- las horas punta de laborable pasan de 8, 18 y 19 a 8, 19 y 9;
- la primera hora de la mañana del sábado pasa de «no compensa» a «valorar»;
- la gama ajustada baja de 2,00 a 1,89, porque los viajeros gastan menos;
- en el informe sale la frase «Los vehículos de la línea 3 de Metro son una
  **estimación**…» y, en «elementos» del perfil, una parada con trenes estimados.

Una sola estación a 20 m aporta unas 19.000 personas al día (461 trenes × 41,2 personas
por tren × peso de la distancia). Es lo que hace el modelo con cualquier estación de
Metro pegada al punto, pero aquí los trenes son estimados: hay que leerlo con cautela.

También se probó un punto de Leganés servido por las líneas 480 a 499: de 3 líneas y 116
autobuses a 6 líneas y 1.150; el paso sube de 11.731 a 12.434 y sigue en «Paso medio».

## Pruebas

- **Mismos datos al regenerar:** `python src/procesar_perfil.py gtfs lineas` dos veces
  da ficheros con la misma huella.
- **Suma por líneas:** en las 15.207 paradas, los vehículos por línea suman el
  `total_lab` de la parada, incluidas la línea 3 y El Casar.
- **`AppTest`:** los tres ejemplos, Lavapiés y Villaverde Alto en las dos vistas, sin
  excepciones. El aviso de estimación de la línea 3 sale en el Informe completo de los
  dos puntos de la línea y en ninguno de los tres ejemplos.
- **`python mcp/probar_cliente.py`:** todo correcto.
- **No se ha probado** en navegador ni se han rehecho las capturas de `docs/capturas/`.

## Ficheros cambiados

- `src/procesar_perfil.py`, `src/supuestos.py`: lo descrito arriba.
- `src/informe_local.py`: `lineas_estimadas`, frase de estimación y nota del día usado
  en el bloque «Cómo se llega».
- `src/perfil_horario.py`: cuenta las paradas con trenes estimados.
- `app/app.py`: aviso bajo la tabla de transporte del Informe completo.
- `datos/procesados/`: `salidas_paradas.parquet` (columna nueva `origen_pasos`),
  `salidas_paradas_dias.json`, `lineas_paradas.parquet` (columna nueva `estimada`) y
  `referencia_movimiento.parquet`.
- `docs/fuentes.md` (bloque generado del perfil por horas) y `README.md` (limitaciones y
  comprobaciones).

## Limitaciones

- **La frecuencia de la línea 3 es inventada con criterio, no medida.** Si la real es
  distinta, los viajeros de sus 19 estaciones lo serán en la misma proporción. Además,
  añadirla baja un 7 % las personas por tren en el resto del Metro; ese ajuste es
  correcto en dirección, pero su tamaño depende de la misma estimación.
- **La hora por parada de los viajes recuperados es aproximada.** En una línea larga, el
  error al final del recorrido puede ser de una hora. El total diario no cambia.
- **El calendario de las líneas de la Sierra sigue mal en el GTFS.** Se evita eligiendo
  un martes. Si el CRTM lo corrige, la regla elige sola cualquier otro día.
- **El día depende de la fecha en que se ejecuta**, como antes: la muestra son las 4
  semanas siguientes a hoy.
- **La C9 hay que revisarla a mano** cuando reabra (`GTFS_LINEAS_EXCLUIDAS`).
- **Siguen sin salir** 12 líneas interurbanas y 5 urbanas sin ningún viaje en el
  fichero, entre ellas las 720 a 728 de Colmenar Viejo.
- **Todas las paradas de una red reciben la misma gente por vehículo**, como antes. Los
  autobuses recuperados de líneas poco usadas bajan la media de las muy usadas.
- El registro `2026-11-12-movimiento-y-accesos.md` conserva las cifras de antes de este
  cambio.
