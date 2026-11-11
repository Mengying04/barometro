# 2026-11-11 · README y preparación del despliegue (fase 6, parte A)

## Qué se quería

Publicar la aplicación en Streamlit Community Cloud, que despliega desde el
repositorio de GitHub, y escribir un README para el jurado. Para eso, la aplicación
tiene que arrancar desde un clon del repositorio, sin ejecutar descargas.

## Medidas

| Qué | Medida |
|---|---|
| `datos/originales` (no se sube) | 723 MB |
| `datos/procesados` completo | 9,5 MB antes de esta fase |
| Datos que se suben al repositorio | 13,2 MB en 18 ficheros; el mayor, 4,9 MB |
| Memoria en un proceso sin Streamlit | unos 270 MB tras cargar; unos 300 MB tras los tres ejemplos |
| Memoria del servidor de Streamlit | unos 400 MB tras los tres ejemplos y el Informe completo (pico de 411 MB) |

Cabe en el servicio: alrededor de 1 GB de memoria y ficheros de menos de 100 MB.

## Qué ha cambiado

### El informe ya no lee los ficheros originales

`src/informe_local.py` leía en cada consulta siete conjuntos de `datos/originales`
(gasto, IPC, alojamientos, viviendas de uso turístico, festivos y las dos series de
demografía empresarial) y las fichas de las fuentes. Sin esos ficheros, la aplicación
no arrancaba.

- **Nuevo `src/procesar_informe.py`:** copia a `datos/procesados/informe/` solo las
  filas y columnas que el informe usa. No calcula ni cambia valores, y deja los
  nombres de las columnas como en el original.
- **`src/informe_local.py`** lee ahora esas tablas. Sus filtros y sus cálculos son
  los mismos.
- **Sin nombres ni direcciones:** de los alojamientos solo se guarda el tipo, el
  código postal y la localidad; de las viviendas de uso turístico, la localidad.
- **`fuentes.json`** conserva el título, la licencia, la fecha de última modificación
  y la fecha de descarga de cada fuente.

### Qué datos se suben

- Las ocho capas que carga la aplicación, `salidas_paradas_dias.json` (fechas del
  calendario del CRTM) y la carpeta `informe/`. `.gitignore` sigue ignorando el
  resto de `datos/procesados` y todo `datos/originales`.
- **No se han recortado las columnas de las capas:** ya eran pequeñas (8,7 MB entre
  las ocho), y recortarlas tenía más riesgo que beneficio.
- No se suben `farmacias.parquet`, `desfibriladores.parquet` ni
  `centros_educativos.parquet`: la aplicación no los carga.

### Revisión de nombres

Se revisaron todas las columnas de texto de los ficheros que se suben.

- **Un caso encontrado y corregido:** la columna `horario_acceso` de
  `desfibriladores_horario.parquet` es texto libre del registro, y uno de sus 952
  valores distintos nombraba un establecimiento. La columna no se usa al calcular (el horario ya
  está interpretado en otras columnas), así que se ha quitado del fichero y de
  `src/procesar_perfil.py`.
- **Lo que queda son nombres de lugares e instituciones, no de personas ni de
  locales:** paradas de transporte, municipios, universidades (por sus siglas) y
  tipos de centro.
- El censo del Ayuntamiento y OpenStreetMap ya se guardaban sin rótulos ni nombres.

### Licencias

Nuevo `datos/LICENCIAS.md`: qué licencia aplica a cada fichero y la aclaración de que
la licencia MIT es solo para el código.

- **Todas las fuentes permiten redistribuir los datos procesados.** No ha habido que
  dejar ninguna fuera.
- **CRTM:** su licencia se volvió a leer el 2026-11-11. Permite copiar, distribuir,
  modificar y combinar, y pide citar la fuente indicando que los datos están
  explotados, «Powered by CRTM», conservar las fechas, mantenerlos al día y compartir
  los datos con el mismo tipo de licencia.
- **OpenStreetMap:** `hosteleria_osm.parquet` y `campus_universitarios.parquet` se
  publican bajo ODbL.
- **Decisión prudente a revisar:** `desfibriladores_horario.parquet` sale del portal
  de la Comunidad (CC BY 4.0), pero al procesarlo se descartaron las filas cercanas a
  un campus usando posiciones de OpenStreetMap. Por si eso lo convierte en base de
  datos derivada, se ofrece también bajo ODbL.

### Dependencias

- `altair==6.3.0` añadido a `requirements.txt`: la aplicación lo importa y solo
  estaba instalado como dependencia de Streamlit.
- Con las versiones fijadas hay paquetes para Python 3.12, 3.13 y 3.14, y no para
  3.11 ni anteriores. Se comprobó pidiendo a PyPI los paquetes de cada versión.

### Documentos

- **`README.md`**, para el jurado. Las dos tablas de datos se generan con
  `src/tablas_readme.py` a partir de `docs/fuentes.md`; lo único escrito a mano es
  para qué sirve cada conjunto del portal. Lleva un marcador para la dirección de la
  demo.
- **`docs/despliegue.md`:** pasos para publicar, lista de comprobación y
  mantenimiento.
- **`docs/fuentes.md`:** bloque nuevo «Tablas del informe del local».

## Pruebas

- **Mismos resultados.** Antes de tocar nada se guardaron en JSON el perfil, el
  informe y las recomendaciones de los tres ejemplos. Después de cada cambio (tablas
  del informe, columna quitada) el JSON es idéntico byte a byte.
- **Clon limpio.** `git clone` en una carpeta vacía, contenedor `python:3.12-slim`
  (Python 3.12.16), `pip install -r requirements.txt` y la aplicación en marcha, sin
  `datos/originales`:
  - el JSON de los tres ejemplos es idéntico al de antes;
  - con un navegador se pulsaron los tres ejemplos y las cinco pestañas del Informe
    completo, sin errores en pantalla ni de JavaScript.
- **`AppTest`** de las dos vistas con los tres ejemplos, sin excepciones.

## Limitaciones y pendientes

- **No se pudo consultar la documentación de Streamlit Community Cloud** (bloqueada
  desde el entorno de trabajo). Los pasos del servicio y las versiones de Python que
  ofrece están escritos de memoria; hay que confirmarlos al publicar.
- **No se ha desplegado:** falta el `git push` y crear la aplicación, que hace la
  autora.
- **Privacidad del servicio:** puede registrar las visitas por su cuenta. Queda
  pendiente leer sus condiciones.
- **Los datos caducan:** el calendario GTFS de Cercanías cubre unas semanas y la
  licencia del CRTM pide mantener los datos al día.
- El perfil del día depende de la fecha en los festivos próximos: el informe cambia
  solo con el paso de los días, aunque los datos no cambien.
