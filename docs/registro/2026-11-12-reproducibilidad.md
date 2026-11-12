# 2026-11-12 · Reproducibilidad: Dockerfile y actualización semanal de los datos

## Qué se pidió

Dos mejoras de reproducibilidad, **sin cambiar cálculos ni la aplicación:**

1. un `Dockerfile` sencillo que arranque la aplicación con los datos procesados del
   repositorio;
2. un flujo semanal de GitHub Actions que descargue, procese, compruebe la calidad y
   abra una propuesta de cambios (*pull request*) con los datos nuevos.

## Ficheros

| Fichero | Qué es |
|---|---|
| `Dockerfile`, `.dockerignore` | Nuevos |
| `.github/workflows/actualizar-datos.yml` | Nuevo: el flujo semanal |
| `src/comprobar_datos.py` | Nuevo: comprobación de calidad |
| `src/resumen_ejemplos.py` | Nuevo: los tres ejemplos, con su huella |
| `src/descargar_externas.py` | **Corregido** un fallo real de descarga (ver abajo) |
| `README.md`, `docs/despliegue.md`, `datos/LICENCIAS.md` | Documentación |

**No han cambiado** `app/`, los datos de `datos/procesados/` ni ningún cálculo
(`perfil_horario.py`, `informe_local.py`, `recomendaciones.py`, `movimiento.py`,
`supuestos.py`, `procesar*.py`). Las huellas de los tres ejemplos son las mismas al
empezar y al terminar.

## 1. Dockerfile

- **Imagen:** `python:3.12.16-slim-bookworm`, la oficial, fijada a una versión
  concreta. Es la misma 3.12 con la que se probó el despliegue.
- Instala `requirements.txt` y arranca Streamlit en el puerto 8501. **No descarga
  datos.** Copia solo lo que hace falta: `app/`, `src/`, `.streamlit/config.toml`,
  `datos/procesados/`, `datos/LICENCIAS.md`, `docs/fuentes.md`, `README.md` y `LICENSE`.
- **Usuario sin privilegios** (`barometro`, uid 10001). **Sin secretos:** no hay
  ninguno en el proyecto.
- Comprobación de salud: la dirección `/_stcore/health` de Streamlit.
- **`.dockerignore`** deja fuera `datos/originales`, los entornos virtuales, `.git`,
  los datos procesados que el repositorio no publica (la misma lista que `.gitignore`)
  y lo que la aplicación no usa: capturas, registro, servidor MCP.

### Comprobado

- **Se construye,** desde un clon limpio del repositorio y desde la carpeta de
  trabajo: 34 segundos la primera vez. Ocupa 1,1 GB.
- **Los tres ejemplos dan los mismos resultados dentro del contenedor,** de dos formas:
  - `src/resumen_ejemplos.py --huellas` da las mismas tres huellas (SHA-256 de todo el
    resultado: perfil, informe, recomendaciones y nivel de movimiento) en el entorno de
    trabajo (Python 3.14) y en el contenedor (Python 3.12);
  - con un navegador contra la aplicación del contenedor, todo lo que enseña en los
    tres ejemplos (Resumen e Informe, móvil y portátil) es idéntico a lo que enseña la
    aplicación local.
- Dentro corre como `barometro`, no hay `.git` ni `datos/originales`, y solo están los
  12 ficheros y carpetas de datos publicados. El servidor usa unos 320 MB.
- **Un fallo encontrado y corregido:** al construir desde la carpeta de trabajo, la
  aplicación no arrancaba, porque algunos ficheros solo los puede leer su dueña (por
  ejemplo, `src/procesar.py`) y el usuario sin privilegios no podía abrirlos. Desde un
  clon limpio no pasaba. El `Dockerfile` da ahora permiso de lectura a lo copiado.

**No probado:** construir la imagen en un Mac (se ha construido en Linux, arquitectura
ARM de 64 bits). La imagen oficial existe para las dos arquitecturas.

## 2. Actualización automática de los datos

### El flujo

`.github/workflows/actualizar-datos.yml`, los lunes a las 04:17 UTC y a mano. Dos
trabajos:

1. **«Descargar, procesar y comprobar»**, solo con permiso de lectura:
   resumen de los tres ejemplos antes → descarga del portal → descarga de las fuentes
   externas → procesado → referencia de movimiento y tablas del README → comprobación
   de calidad → resumen después → paquete con los ficheros que cambian.
2. **«Abrir la propuesta de cambios»**, solo si lo anterior ha ido bien y hay datos
   nuevos: sube la rama `datos/actualizacion-automatica` y abre la propuesta contra
   `main` (o actualiza la que siga abierta).

Decisiones:

- **Nunca sube a la rama principal.** Solo escribe en su rama, y el paso se niega a
  seguir si esa rama fuera la principal.
- **Permisos mínimos y ningún secreto.** Por defecto, solo lectura. El trabajo que
  ejecuta código sobre datos descargados no puede escribir nada; el que abre la
  propuesta solo tiene `contents: write` y `pull-requests: write`. Se usa el permiso
  temporal de cada ejecución (`GITHUB_TOKEN`), que GitHub crea solo: no hay que
  configurar nada secreto.
- **Acciones fijadas por su identificador de versión** (no por una etiqueta que pueda
  cambiar): `checkout` 7.0.1, `setup-python` 7.1.0, `upload-artifact` 7.0.2 y
  `download-artifact` 8.0.2. Los identificadores se leyeron de los repositorios
  oficiales el 2026-11-12.
- **Respeto a los servidores:** una descarga detrás de otra, nunca en paralelo (los
  scripts ya eran así); 20 segundos de pausa entre fuentes; cada fuente externa, hasta
  3 intentos con 1 y 3 minutos de espera; el portal, 2 intentos con 2 minutos (además
  de los 3 reintentos por fichero que ya hacía `descargar_datos.py`); de madrugada.
- **Solo propone si cambia algún dato de verdad.** `informe/fuentes.json` lleva la
  fecha de descarga y cambia siempre; por sí solo no abre propuesta.
- **El texto de la propuesta** trae los tres ejemplos antes y después, el informe de
  calidad, los ficheros que cambian y una lista de lo que hay que mirar a mano.
- El commit de la rama lo firma `github-actions[bot]`: es un commit automático y no
  lleva ninguna atribución a Claude. Al aceptar con «Squash and merge», el commit de
  `main` es de la autora.

### La comprobación de calidad: `src/comprobar_datos.py`

Se puede ejecutar a mano (`python src/comprobar_datos.py`) y devuelve un error si algo
falla. Hace 37 comprobaciones sobre los ficheros publicados:

| Qué mira | Cuándo se detiene |
|---|---|
| **Filas de cada capa** (18 ficheros) | Fuera de un mínimo y un máximo por fichero, o si el fichero falta o no se puede leer. Márgenes anchos donde la fuente crece sola (IPC, demografía de 2026) y estrechos donde no debería cambiar (secciones censales) |
| **Columnas prohibidas** | Una columna con «nombre», «teléfono», «correo», «dirección», «NIF», «titular», «rótulo»… Se permiten tres que son nombres de municipios o de universidades |
| **Correos y teléfonos dentro de los textos** | Un correo o un teléfono español en cualquier columna de texto (las de códigos no se miran para teléfonos) |
| **Población** | El total se aparta más de un 3 % de 6.995.318; hay secciones repetidas, sin población o negativas; no son 179 municipios; o la referencia de movimiento no suma lo mismo que las secciones |
| **Transporte** | Alguna de las seis redes sin paradas suficientes (menos de la mitad de las de hoy), sin líneas, sin pasos en laborable o en sábado, o sin día típico |
| **Posición** | Algún punto fuera de la Comunidad de Madrid (con margen; las paradas, con más) |

Probado:

- **Con los datos del repositorio:** 37 de 37 bien.
- **Con los datos recién descargados** (la medición de abajo): 37 de 37 bien.
- **Con datos estropeados a propósito,** en una copia: una capa cortada a 5.000 filas,
  un fichero borrado, columnas `nombre` y `contacto_tel`, un correo y un teléfono
  dentro de un texto, 400 secciones sin población, Cercanías sin servicio y Metro
  Ligero sin paradas. **Detecta los nueve fallos y devuelve error.**
- Al escribirlo salieron tres falsas alarmas, corregidas: «titularidad» no es
  «titular»; los CSV del informe usan punto y coma; y seis paradas de autobús
  interurbano están de verdad fuera de la Comunidad (llegan a Toledo y Cuenca).

Lo que **no** hace: no compara con la semana anterior ni juzga si un cambio pequeño es
correcto. Para eso está la tabla de los tres ejemplos y la revisión de la autora.

### `src/resumen_ejemplos.py`

Calcula los tres puntos de prueba y enseña una tabla (nivel, gente en un laborable,
clientes principales, locales, precios, transporte) y una huella de todo el resultado.
Sirve para comparar entornos (Docker) y para la propuesta semanal. Las coordenadas son
las de `EJEMPLOS` en `app/app.py`, copiadas (la aplicación no se ha tocado).

### Medición: ¿cabe en GitHub Actions?

Descarga y procesado completos, en un clon limpio fuera del repositorio:

| Paso | Tiempo |
|---|---|
| `descargar_datos.py` (portal, 74 ficheros) | 48 s |
| `descargar_externas.py` (seis fuentes) | unos 140 s |
| `procesar.py` | 9 s |
| `procesar_perfil.py` | 15 s |
| `procesar_informe.py` | 1 s |
| `movimiento.py --generar` | 29 s |
| `tablas_readme.py --escribir` | menos de 1 s |
| **Total** | **unos 4 minutos** |

- Datos originales: **720 MB.** Datos procesados: 14 MB. Pico de memoria: **1,3 GB.**
- **Cabe con mucho margen:** un trabajo de GitHub puede durar 6 horas y el ejecutor
  estándar tiene unos 14 GB de disco y 16 GB de memoria en repositorios públicos (cifras
  de memoria; no se han podido leer en la documentación desde aquí). El flujo se corta
  solo a los 60 minutos, por si algo se queda colgado.
- En GitHub tardará algo más: instalar las dependencias (alrededor de un minuto) y las
  pausas entre fuentes (2 minutos).
- La segunda descarga del día dio **los mismos tres ejemplos** (nivel, gente, clientes)
  con 9 ficheros cambiados: locales, centros y fechas.

### Dos fallos reales que destapó la medición

1. **El INE cambió el formato de una fecha.** El servicio que describe las tablas
   devolvía la última modificación en milisegundos el día 9 y hoy la devuelve como
   texto («Thu Oct 15 09:00:00 CEST 2026»). `descargar_externas.py` fallaba y dejaba
   la descarga del INE a medias, con lo que el procesado no podía seguir.
   **Corregido:** `_fecha_ms()` acepta las dos formas. Es un script de descarga, no un
   cálculo; la fecha que escribe es la misma (2026-10-15).
2. **OpenStreetMap (Overpass) devolvió un error 502** y funcionó al reintentar al cabo
   de un rato. Los reintentos de dentro del script (2, 4 y 6 segundos) no bastaron: por
   eso el flujo reintenta cada fuente con esperas de minutos.

Sin la corrección del INE, el flujo habría fallado todas las semanas.

## Qué se ha probado del flujo y qué no

**Probado aquí:**

- el fichero es YAML válido y pasa `actionlint` (que también revisa los trozos de
  shell con `shellcheck`); con dos errores puestos a propósito, los detecta;
- los pasos de descarga, procesado, calidad y resumen son las mismas órdenes que se
  ejecutaron en la medición;
- los reintentos, con una fuente que falla dos veces (sigue) y otra que falla siempre
  (se detiene con error);
- los pasos «ver si hay datos nuevos», «texto de la propuesta» y «empaquetar», con los
  datos recién descargados;
- el paso que sube la rama, contra un repositorio remoto de prueba en local: crea la
  rama con 9 ficheros, `main` queda intacta, la segunda vez rehace la rama, y se niega
  a seguir si la rama fuera la principal.

**No se ha podido probar desde este entorno:**

- **ejecutar el flujo en GitHub.** No se ha lanzado nunca. Puede fallar por algo que
  aquí no se ve: los nombres de los parámetros de las acciones (se han leído de sus
  ficheros, no ejecutado), la red del ejecutor hacia cada fuente o el tiempo real;
- **abrir la propuesta con `gh`:** en la prueba se sustituyó por un programa que solo
  apunta lo que se le pide. Con el permiso por defecto, GitHub no deja a los flujos
  abrir propuestas: hay que marcar una casilla una vez (`docs/despliegue.md`);
- **la ejecución programada:** solo funciona cuando el fichero esté en `main` en
  GitHub;
- si los servidores de las fuentes aceptan peticiones desde las máquinas de GitHub.
  Overpass y el INE a veces limitan a los centros de datos.

**Primera vez, a mano:** subir los cambios, marcar la casilla de permisos, lanzar el
flujo desde la pestaña Actions y mirar la ejecución entera.

## Limitaciones

- **`datos/LICENCIAS.md` y una frase del README llevan fechas escritas a mano.** El
  flujo no las toca: lo recuerda en la propuesta.
- **La tabla de los tres puntos del README** tampoco se regenera sola.
- Los márgenes de la comprobación de calidad son fijos. Si una fuente cambia de verdad
  (un censo nuevo), el flujo se detendrá hasta que alguien revise la referencia. Es a
  propósito.
- GitHub desactiva los flujos programados tras 60 días sin actividad en el repositorio.
- El `.devcontainer` del repositorio usa Python 3.11, con el que las dependencias
  fijadas no se instalan. No se ha tocado: no era parte del encargo.
