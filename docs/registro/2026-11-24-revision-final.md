# 2026-11-24 · Eslogan nuevo y revisión final antes de congelar el código

Hecho entre el 24 y el 25 de noviembre de 2026, para la final de DATAMAD 2026 (jueves 26).
**No se ha cambiado ningún cálculo, dato ni supuesto.** Solo textos, el aviso del buscador
y el cliente de prueba del servidor MCP.

## Antes: el PDF técnico

El trabajo del PDF que estaba en curso
([`2026-11-24-documento-tecnico.md`](2026-11-24-documento-tecnico.md)) se comprobó
(`comprobar_datos.py` y `probar_cliente.py` bien) y quedó en el commit `03e67b8`.

## Parte 1 · Eslogan nuevo

- **Portada** (`app/app.py`, `app/estilo.css`): el titular pasa a ser **«¿Habrá negocio
  aquí?»**, con **«Mira los datos antes de firmar.»** debajo, en color teja claro (clase
  nueva `.pt-lema`). Sustituye a «Que pase mucha gente no significa que tengas clientes.».
- **Frase de debajo**, sin repetir «antes de firmar»: «Escribe la dirección del local y
  descubre en segundos cuánta gente pasa, cuándo tendrías más clientes, a quién vender, qué
  ofrecer y a qué precios. Gratis y con datos abiertos.».
- **README:** segunda línea bajo el título, antes del párrafo de qué es.
- **Pestaña del navegador:** «BARómetro · ¿Habrá negocio aquí?».
- **PDF:** el subtítulo bajo «BARómetro» era «Qué ofrecer, a quién, a qué hora y a qué
  precio» en el informe y «Comparación de dos locales» en la comparación. Ahora es «¿Habrá
  negocio aquí? Mira los datos antes de firmar.» y «¿Habrá negocio aquí? · Comparación de
  dos locales». Ningún texto obligatorio cambia.
- **La frase antigua** solo queda en
  [`2026-11-24-rediseno-tecnico.md`](2026-11-24-rediseno-tecnico.md), que es historia y no
  se toca.
- La primera versión del lema tenía un margen negativo y pisaba el titular. Se vio en las
  capturas y se corrigió antes del commit.
- **Capturas rehechas:** `portatil-portada`, `movil-portada`, `portatil-sugerencias` y
  `movil-sugerencias` (las que enseñan el titular). También los dos PDF de `docs/ejemplos/`
  y las cuatro `documento-*.png`, porque la cabecera del PDF cambia.
- **PDF de muestra:** su texto, comparado con el de antes, solo cambia en lo esperado:
  - el subtítulo;
  - la fecha y la versión de la ficha;
  - el aviso de festivos, que ahora incluye el 25 de diciembre porque cae dentro de los
    30 días al generarlos un día más tarde.

Commit `bc27482`.

## Parte 2 · Revisión

| # | Qué se revisó | Resultado | Qué se corrigió |
|---|---|---|---|
| 1 | Cifras en README, aplicación, PDF, servidor MCP, `docs/fuentes.md`, `docs/validacion.md` y `datos/LICENCIAS.md` | 15 conjuntos en uso de 16 descargados (falta la farmacia), 4.518 secciones, 179 municipios, 38 comprobaciones, 5 herramientas MCP y Python 3.12–3.14: iguales en todas partes y calculados de los datos (portada: `cifras_portada()`) | **Fecha de los datos:** el README y `datos/LICENCIAS.md` decían 2026-11-12, pero los datos en uso son los de la actualización automática #2, del 2026-11-16. No se cambiaron a mano tras aceptarla (paso 5 de `docs/despliegue.md`). Corregidos, con la versión del CRTM (GTFS hasta el 2026-11-16, EMT, y demanda del 2026-11-16). **`docs/fuentes.md`:** nota de que «Oficinas de farmacia» se descarga y no se usa, también en su generador (`src/descargar_datos.py`) para que no la borre la actualización semanal |
| 2 | Frases obsoletas | No quedan «el domingo no se modela», «Buscar otra», «viajes falsos» ni «de relleno» como cosa descartada. «Hora de relleno» se refiere al campo del GTFS y es correcto. «No se ha probado en Claude Desktop» ya tenía su nota fechada | README: «diez secciones» → **«once secciones»** (se añadió «Metodología y supuestos clave»). `docs/despliegue.md`: «La portada carga y se ve el mapa» (la portada ya no tiene mapa) → titular, buscador, ejemplos y cifras. «No se ha podido ejecutar en GitHub» → ya ha funcionado dos veces (#1 y #2). La prueba de 2026-11-11 «con las cinco pestañas» queda fechada como de entonces. `datos/LICENCIAS.md`: «la pestaña de fuentes» → la sección «Fuentes y licencias» |
| 3 | Enlaces | 31 ficheros (README, `docs/**`, `datos/LICENCIAS.md`): todos los enlaces relativos existen y las anclas del README funcionan. Las capturas del README existen y son las actuales | Ninguno. Hay dos enlaces de [`2026-11-24-contraste-aforos-peatones.md`](2026-11-24-contraste-aforos-peatones.md) que parecen rotos, pero están dentro de la cita del texto propuesto para el README y son correctos desde allí. Se dejan |
| 4 | Pruebas completas | `comprobar_datos.py`: 38 de 38 bien. `probar_cliente.py` con `TZ=CET-1`, `UTC` y `UTC-8`: todo correcto. Huellas de `resumen_ejemplos.py`: iguales a las del commit anterior, calculadas el mismo día (2026-11-25), en un `git worktree` aparte. AppTest: 32 de 32 bien (ver abajo). Chromium a 390, 1.280, 1.440 y 1.920 px, bajando hasta el pie en portada, Resumen, Informe, planes y comparación (20 vistas): sin errores de JavaScript, sin desplazamiento horizontal, sin solapes y sin el índice sobre el pie | En la primera pasada con `UTC`, CartoCiudad falló un momento y `probar_cliente.py` se cayó con una traza larga. Ahora, si una herramienta devuelve error, el cliente enseña su mensaje y dice «con fallos». Repetido después: bien en las tres zonas |
| 5 | Despliegue | Clon limpio en `python:3.12-slim` (3.12.16), sin `datos/originales`: `pip install -r requirements.txt` bien. La aplicación arranca (`/_stcore/health` ok). Portada y tres ejemplos con «Bar de barrio» e Informe completo, sin errores de JavaScript. Huellas iguales. Imagen del `Dockerfile`, construida desde ese clon: huellas iguales, comprobación de salud «healthy», la misma navegación bien, 1,16 GB y unos 340 MB de memoria. `BAROMETRO_MEDIR` solo se activa con la variable a 1, y nada la pone (ni Dockerfile, ni devcontainer, ni flujo) | Medidas nuevas, con fecha, en `docs/despliegue.md` y en el README («Rigor», «Contenedor»). La carpeta `.git` de un clon ocupa ahora unos 324 MB (la guía decía 22 MB), sobre todo por las capturas rehechas en cada ronda. No impide desplegar |
| 6 | Datos válidos el día de la final | La aplicación no lee los calendarios en marcha: usa los vehículos de un día típico por red, calculados al procesar. Calendarios de los GTFS: Metro Ligero hasta el 2027-10-28; interurbanos y urbanos hasta el 2027-11-28; EMT hasta el 2026-12-31; **Cercanías del 2026-10-30 al 2026-11-28** (cubre el jueves 26, el viernes 27 y el sábado 28; el domingo 29 ya no); Metro, caducado el 2026-05-27 (ya conocido y avisado: se usa un día de su vigencia). Con el reloj en el 26-11-2026 (`faketime` y AppTest, y también llamando a las funciones): sin excepciones, «Fecha del informe 2026-11-26» en la web y en el PDF, y aviso de festivos del 7, 8 y 25 de diciembre (y el 26 en Fuenlabrada). Igual el 27 a las 00:30 UTC (ya 27 en Madrid) y el 30 | Nada regenerado. **Aviso:** el GTFS de Cercanías caduca el sábado 28 |
| 7 | Sin conexión a CartoCiudad | Aplicación arrancada con un proxy que no responde, en Chromium a 1.440 y 390 px. El buscador de la portada y el de la barra avisan, también tras Intro. Los tres botones de ejemplo calculan y se ven bien. Sin errores de JavaScript | El aviso decía solo «Ahora no podemos buscar direcciones. Prueba más tarde.». Ahora dice que el buscador de CartoCiudad no responde. En la portada añade «…o, mientras, con un ejemplo o «Usar mi ubicación»». La tabla de `docs/despliegue.md` sigue valiendo |
| 8 | Privacidad y licencias | En los ficheros actuales y en **todo el historial de git** solo hay coordenadas de puntos de prueba públicos (los tres ejemplos, la Puerta del Sol, campo entre Griñón y Cubas, Toledo, Lavapiés, Villaverde Alto, Getafe y Alcalá). Ni la dirección ni las coordenadas del bar de validación. Sin claves ni secretos. Los únicos correos son los de los autores de DejaVu, en su licencia. Sin nombres de personas ni de locales: las columnas prohibidas las vigila `comprobar_datos.py`. Atribuciones (aviso, Powered by CRTM, OpenStreetMap, CartoCiudad, no respaldo) en las 20 vistas de Chromium y en los 8 PDF de AppTest (los ocho `TEXTOS_OBLIGATORIOS`) | Ninguno |
| 9 | Repositorio limpio | Nada de `.DS_Store`, entornos virtuales, `__pycache__`, registros ni temporales en git. El mayor fichero, en el árbol y en todo el historial, es `secciones_censales.parquet` (4,9 MB). `.claude/settings.json` sí se sube a propósito: solo quita la atribución a Claude en los commits | Ninguno. `git status` vacío tras el último commit |
| 10 | Registro, commit y etiqueta | Este documento, commits y etiqueta `v1.0-datamad-final` | El `git push` **no se ha podido hacer** desde el entorno de trabajo, que no tiene credenciales de GitHub (además, `CLAUDE.md` pide que lo haga la autora). Lo hace la autora desde su Mac (ver abajo) |

### AppTest (32 comprobaciones)

- Portada: eslogan nuevo, sin el antiguo, cifras 15, 4.518 y 179, y enlace a Planes.
- Planes, desde la portada: cuatro planes y nada prohibido.
- Para cada ejemplo, sin tipo y con «bar de barrio» (12 vistas):
  - Resumen e Informe, cada uno en laborable, sábado y domingo;
  - titular, o pregunta de clientes con tipo;
  - «Metodología y supuestos clave» en el Informe;
  - con tipo, la unidad de las cifras;
  - PDF del informe con los ocho textos obligatorios y el eslogan (63 KB con tipo);
  - Planes y «Volver al resultado».
- Comparación Vicálvaro–Griñón, sin tipo y con «bar de barrio»:
  - filas, botones y domingo;
  - PDF con los textos obligatorios y el eslogan (47–48 KB);
  - Planes y «Volver a la comparación».

## Limitaciones conocidas, a 2026-11-25

Las del README («Limitaciones conocidas»), que siguen todas en pie:

- **La hora punta de paso en laborable es poco fiable.** El modelo la pone a las 8. Los
  conteos de peatones de Madrid capital la tienen por la tarde. El fin de semana, el modelo
  da menos gente que en laborable, y las aceras, más.
- **Todo lo que es «gente» es una estimación,** y pasar no es entrar.
- **Los clientes por tipo de local son supuestos sin calibrar.** Solo hay un bar de
  validación y no cuenta como validación independiente.
- **Solo se mide el negocio de paso,** no el local al que se va a propósito o en coche.
- **El nivel de movimiento compara estimaciones con estimaciones.** Los pueblos pequeños
  pueden salir con menos paso.
- **«Cómo se llega» es solo transporte público:** líneas y vehículos, no viajeros. Los
  autobuses urbanos de fuera de Madrid son «datos parciales».
- **Metro:**
  - la línea 3 es una estimación;
  - los horarios publicados son de 2025 y su calendario terminó el 2026-05-27;
  - no hay entradas por estación ni viajeros por parada de autobús.
- **Autobuses sin hora en cada parada:** 68 líneas interurbanas y 24 urbanas.
- **Líneas que no salen:** la C9 y 17 líneas de autobús.
- **El contexto a 1 km es solo contexto.**
- **Direcciones:** una calle sin número no se calcula hasta confirmar el punto, y con un
  portal CartoCiudad puede situar uno cercano.
- **Un estudiante que llega en metro cuenta dos veces.**
- **Fuera de Madrid capital, a OpenStreetMap le faltan locales.**
- **En el resultado general, las cenas y las copas casi nunca salen.**
- **El domingo** es un modelo con supuestos propios y vale para los festivos solo de forma
  aproximada.
- **El dato del sector y el índice de precios** mezclan actividades.
- **Horarios de la competencia:** casi no los hay.

Además, de esta revisión:

- **El GTFS de Cercanías caduca el sábado 28 de noviembre de 2026.** La aplicación no
  falla por eso, porque usa un día típico ya calculado (laborable del 2026-11-12). Pero la
  licencia del CRTM pide datos al día, y la actualización del lunes 30 necesitará un GTFS
  nuevo de Renfe.
- **Esquema de la zona del PDF:**
  - alguna marca de local puede tapar en parte el rótulo de un anillo;
  - las paradas son cuadrados, sin el icono de cada modo.
- **Streamlit Community Cloud** puede registrar visitas por su cuenta. Está pendiente que
  la autora lea sus condiciones (`docs/despliegue.md`).
- **La prueba en Claude Desktop** la hizo la autora el 2026-11-24. No se ha repetido desde
  el entorno de trabajo.
- **El historial de git pesa** unos 324 MB en un clon, por las capturas.
- **Capturas sin rehacer:** fuera de la portada y los PDF, las capturas son de la ronda
  del 2026-11-24. No enseñan el titular de la portada.
- **Versión en la ficha técnica:** los PDF de muestra dicen «commit 03e67b8», el commit
  anterior a esta revisión, que es la versión que tenía el código al generarlos.

## Archivos

- `app/app.py`, `app/estilo.css`: el eslogan y el título de la pestaña.
- `app/buscador.js`: el aviso cuando CartoCiudad no responde.
- `src/documento.py`: el subtítulo de la cabecera del PDF.
- `src/descargar_datos.py`, `docs/fuentes.md`: la nota de la farmacia.
- `mcp/probar_cliente.py`: el error de una herramienta, con su mensaje.
- `README.md`: el eslogan, la fecha de los datos, «once secciones» y la prueba de
  despliegue.
- `datos/LICENCIAS.md`: las fechas de los datos y la sección de fuentes.
- `docs/despliegue.md`: frases obsoletas y medidas nuevas.
- `docs/capturas/` (seis) y `docs/ejemplos/` (dos PDF).
