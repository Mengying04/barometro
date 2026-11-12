# 2026-11-12 · Direcciones sin número, nivel de movimiento y accesos

## Qué se pidió

Tres mejoras a partir de pruebas reales, sin cambiar los cálculos que ya había:

1. No calcular con una dirección que no sea un punto concreto y limpiar la lista de
   resultados del buscador.
2. Decir arriba del todo cuánto movimiento tiene la zona frente al resto de la
   Comunidad.
3. Añadir cómo se llega en transporte público y qué hay a 1 km.

## 1. Direcciones sin número

**Qué pasaba.** Si se escribía una calle sin número, CartoCiudad devolvía la calle
entera y la aplicación calculaba en su punto medio, como si fuera el local. La lista
enseñaba «PASEO PASEO ARTILLEROS, Madrid», todo en mayúsculas.

**Qué se ha hecho** (`src/direcciones.py`, compartido por la aplicación y el servidor
MCP):

- Cada resultado lleva su **precisión**: portal, calle, localidad, municipio o código
  postal. Solo un **portal con número** es un punto exacto. Un «portal» sin número se
  trata como calle.
- **Lista limpia:** sin el tipo de vía repetido, con mayúsculas normales, con el
  artículo en su sitio («MARTIRES FUENLABRADA (DE LOS)» → «Calle de los Martires
  Fuenlabrada») y con el municipio siempre a la vista. Los portales van primero y lo que
  no es un portal dice qué es («· calle entera, sin número»).
- CartoCiudad da los nombres sin tildes («Constitucion»): no se inventan.
- Se acepta además el tipo «Municipio», que antes se descartaba por la mayúscula.

**En la aplicación.** Con un resultado que no es un portal no se calcula nada. Se borra
el punto anterior, se enseña el mapa centrado en ese sitio y se pregunta: «¿Es aquí? Si
no, toca el mapa en el sitio exacto». Se calcula solo al pulsar «Sí, es aquí» o al tocar
el mapa. El texto recuerda que también se puede escribir el número del portal.

**En el servidor MCP.** `buscar_direccion` devuelve en cada resultado `precision` y
`es_portal_exacto`, y un `aviso` en los que no son un punto concreto. Añade
`portales_exactos` y, si no hay ninguno, una nota que pide no calcular todavía. Las
instrucciones del servidor dicen lo mismo.

## 2. Nivel de movimiento de la zona

**Referencia** (`src/movimiento.py`, `datos/procesados/referencia_movimiento.parquet`).
Se calcula el perfil por horas en un punto interior de cada una de las 4.518 secciones
censales de la Comunidad (todas tienen vecinos) y se guarda la gente que pasa en un día
laborable. Tarda 28 segundos y ocupa 156 kB. El fichero guarda el código de la sección,
su población, el punto y la cifra.

| Parte de la referencia | 10 % | 30 % | 50 % | 70 % | 90 % |
|---|---|---|---|---|---|
| Personas que pasan en un laborable (estimación) | 432 | 5.981 | 10.656 | 15.117 | 24.700 |

**Niveles** (cortes en `src/supuestos.py`): «Muy poco paso» por debajo del 10 %, «Poco
paso» hasta el 30 %, «Paso medio» hasta el 70 %, «Mucho paso» hasta el 90 % y
«Muchísimo paso» por encima. Además, con menos de 500 personas al día el nivel es
siempre «Muy poco paso».

**Frase de comparación.** «Pasa menos (o más) gente que en N de cada 10 sitios
habitados de la Comunidad», redondeando hacia abajo para no exagerar. Entre el 40 % y el
60 % dice que pasa más o menos lo mismo que en un sitio medio.

**En la aplicación.** Es lo primero que se ve en el Resumen, antes del titular y de las
tarjetas: el nombre del nivel, la etiqueta «Estimación», una escala de cinco tramos y la
frase. Con «Muy poco paso»:

- el titular pasa a ser «Muy poco paso: por aquí casi no pasa gente andando»;
- aparece el aviso «Aquí casi no pasa gente andando. BARómetro mide el negocio de paso;
  un local al que se va a propósito o en coche no se puede valorar con estos datos.»;
- las cuatro tarjetas y su explicación se atenúan (opacidad al 50 %).

En el Informe completo se da la cifra, la posición en la referencia y la mediana.

**En el servidor MCP.** `recomendar_local` y `perfil_por_horas` añaden
`nivel_de_movimiento`, con el aviso cuando toca.

## 3. Cómo se llega y qué hay un poco más lejos

**Líneas por parada** (`python src/procesar_perfil.py lineas` →
`datos/procesados/lineas_paradas.parquet`, 232 kB). Por cada parada, línea y sentido,
los vehículos que paran en el mismo laborable típico que ya usaba el perfil.

- Para contar los mismos viajes, la carga del GTFS se sacó a una función común
  (`cargar_red`) que usan el paso antiguo y el nuevo. Es el mismo código, movido.
- **Comprobación:** en las 14.401 paradas, la suma por líneas coincide con el
  `total_lab` de `salidas_paradas.parquet`. Ese fichero no se ha regenerado (misma huella
  antes y después).

**Bloque «Cómo se llega»** (`accesos`, en `informe_local()`): redes que paran a menos de
300 m y de 800 m (Metro, Cercanías, Metro Ligero, autobús urbano y autobús interurbano),
con sus líneas, los vehículos al día y la distancia a la parada más cercana.

- Vehículos al día: de cada línea y sentido se toma la parada del radio con más
  vehículos, para no contar el mismo autobús en tres paradas seguidas.
- Nivel: «Muy bien comunicado» con Metro, Cercanías o Metro Ligero a menos de 300 m o
  600 autobuses al día; «Bien comunicado» con uno de esos modos a menos de 800 m o 200
  autobuses al día; «Poco transporte» si hay algo menos; «Sin transporte cerca» si no
  hay ninguna parada a 800 m.

**Bloque «Qué hay un poco más lejos»** (`entorno`): vecinos y locales de hostelería a
1 km (unos 12 minutos andando), comparados con los de 300 m. Clasifica el punto en
«aislado», «en el borde de una zona habitada» o «dentro». Es solo contexto: el perfil y
las recomendaciones siguen usando 300 m.

**En la aplicación.** El Resumen tiene una sección nueva, «Cómo se llega y qué hay un
poco más lejos», con dos frases. El Informe completo enseña los dos bloques en la
pestaña Mercado y explica en una frase por qué se usan 300 metros: es lo que se anda en
unos 4 minutos, la distancia a la que alguien se desvía para tomar algo de paso.

## Supuestos nuevos

Todos en `src/supuestos.py`, sección «Nivel de movimiento, accesos y entorno», con su
comentario: cortes de los cinco niveles, suelo de 500 personas, texto del aviso, radio de
800 m, redes que forman cada modo, umbrales de 600 y 200 autobuses, radio de 1 km y
umbrales del tipo de entorno (1.000 vecinos a 1 km; la mitad del reparto uniforme o 300
vecinos a 300 m).

## Pruebas

### Los tres ejemplos conservan sus resultados

Antes de tocar nada se guardaron el perfil (horas, franjas y elementos), el informe y
las recomendaciones de los tres puntos. Después de los cambios:

- perfil y recomendaciones: **idénticos** en los tres;
- los seis bloques anteriores del informe: **idénticos** en los tres;
- lo único nuevo son los bloques `accesos` y `entorno`, al final.

### Qué sale en cada caso

| Punto | Movimiento | Personas al día | Cómo se llega | A 1 km |
|---|---|---|---|---|
| Campus de Vicálvaro | Mucho paso (más que 8 de cada 10) | ≈23.000 | Muy bien comunicado: Metro a 120 m | ≈46.000 vecinos, 124 locales; dentro |
| Centro de Fuenlabrada | Muchísimo paso (más que 9 de cada 10) | ≈46.000 | Muy bien comunicado: Cercanías a 60 m y Metro a 130 m | ≈78.000 vecinos, 212 locales; dentro |
| Plaza Mayor de Griñón | Poco paso (menos que 8 de cada 10) | ≈3.100 | Poco transporte: 4 líneas interurbanas, 139 autobuses | ≈4.000 vecinos, 8 locales; dentro |
| M-404, km 18 (Griñón) | Muy poco paso (menos que 9 de cada 10) | ≈200 | Poco transporte | ≈2.100 vecinos, 2 locales; borde |
| Campo entre Griñón y Cubas (40,2000, −3,8900) | Muy poco paso (menos que 9 de cada 10) | ≈100 | Poco transporte: autobús a 690 m | ≈950 vecinos, 0 locales; aislado |

### Calle sin número

«paseo de los artilleros»: un resultado, «Paseo Artilleros, Madrid · calle entera, sin
número». Al elegirlo no hay punto ni resultado: aparece la pregunta con el mapa. Al
confirmar, se calcula. Probado también con «Fuenlabrada» (localidad y municipio: mapa
más alejado y la misma pregunta) y con «Plaza de la Constitución 1, Fuenlabrada»
(portal: se calcula directamente).

### Punto aislado de campo

Probado de dos formas: con el punto 40,2000, −3,8900 y, desde el buscador, con «carretera
M-404 118 griñón», cuyo primer resultado es el kilómetro 18. En los dos sale «Muy poco
paso», el titular y el aviso, y las tarjetas atenuadas. Al elegir después un ejemplo
normal, las tarjetas vuelven a verse enteras.

### Cómo se ha probado

- **`AppTest`:** los tres ejemplos en las dos vistas, la calle sin número, el municipio,
  el portal y el punto de campo. Sin excepciones.
- **Navegador automático** (Chromium con Playwright, 1440 × 900 y 390 × 844): los mismos
  casos, sin errores de JavaScript. Capturas nuevas en `docs/capturas/`:
  `portatil-vicalvaro-resumen-inicio.png` (sustituida), `portatil-calle-sin-numero.png`,
  `portatil-muy-poco-paso.png` y `portatil-grinon-accesos-entorno.png`.
- **`python mcp/probar_cliente.py`:** todo correcto. Ahora comprueba también los ocho
  bloques, el nivel de movimiento, la calle sin número y el punto de campo.
- **Tiempo de cálculo:** un punto tarda entre 50 y 60 ms con los datos ya cargados; el
  bloque de accesos, entre 5 y 10 ms.

## Lo que ha salido al mirar los datos

- **La línea 3 de Metro no tiene servicio** en el día que se usa del GTFS de Metro (13
  de mayo de 2026, GTFS de 2025). No aparece en «Cómo se llega» y, como ya pasaba, sus
  trenes no aportan viajeros al perfil. Lo mismo con la C9 de Cercanías y con algunas
  líneas de autobús (lista en `docs/fuentes.md`). No se ha corregido: habría que cambiar
  el día o los datos, y eso cambia los resultados.
- **El 10 % más bajo de la referencia son sitios casi vacíos.** En las secciones grandes
  de campo (el 12 % mide más de 1 km²) el punto interior cae lejos de las casas y el
  modelo reparte a los vecinos por igual. Por eso «Muy poco paso» equivale en la práctica
  a menos de unas 430 personas al día.
- **En `docs/fuentes.md` faltaba una nota en el código.** La nota de que no se guarda el
  texto libre del horario de los desfibriladores estaba en el documento, pero no en
  `procesar_perfil.py`, y se perdía al regenerarlo. Se ha añadido al código.

## Limitaciones

- El nivel de movimiento compara estimaciones con estimaciones y hereda todos los
  supuestos del perfil. Hay que regenerar la referencia si cambian los datos o los
  supuestos del perfil.
- Solo se mide el negocio de paso. El aviso lo dice, pero la aplicación no sabe valorar
  un local de destino.
- «Cómo se llega» cuenta líneas y vehículos, no viajeros, y no sabe nada del coche.
- Los umbrales de los niveles (10/30/70/90 %, 600 y 200 autobuses, 1.000 y 300 vecinos)
  son elecciones razonadas, no medidas.
- Fuera de Madrid capital, los locales a 1 km salen de OpenStreetMap, al que le faltan.
- El punto de una calle sin número es su centro según CartoCiudad; confirmar sin mirar
  el mapa da un resultado de otro sitio de la calle.
- Las demás capturas de `docs/capturas/` son anteriores a estos cambios.
- No se ha desplegado ni medido en Streamlit Community Cloud. El repositorio lleva dos
  ficheros de datos más (13,6 MB en 20 ficheros).
