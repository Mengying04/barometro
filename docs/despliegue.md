# Despliegue en Streamlit Community Cloud

Streamlit Community Cloud es gratuito y publica la aplicación directamente desde el
repositorio de GitHub. Esta guía explica cómo publicarla, qué se ha comprobado antes y
cómo mantenerla.

> **Aviso sobre esta guía.** Las medidas y pruebas de abajo se hicieron el 2026-11-11.
> Los pasos del servicio (nombres de botones, versiones de Python que ofrece, límites)
> están escritos de memoria: la documentación de Streamlit no se pudo consultar desde el
> entorno de trabajo. Si la pantalla no coincide, manda lo que diga el servicio.

## Lo que ya está comprobado

| Requisito del servicio | Medida | ¿Cabe? |
|---|---|---|
| Ningún fichero de más de 100 MB | El mayor es `secciones_censales.parquet`, de 4,9 MB | Sí |
| Tamaño de los datos | 13,6 MB en 20 ficheros de `datos/procesados/`; la carpeta `.git` del clon ocupa unos 22 MB | Sí |
| Alrededor de 1 GB de memoria | El servidor usa unos **400 MB** después de cargar los datos, calcular los tres ejemplos y abrir el Informe completo (pico de 411 MB) | Sí, con margen |
| Arranque sin descargas | Un clon limpio, sin `datos/originales`, instala y arranca | Sí |

- **Prueba del clon limpio:** `git clone` del repositorio en una carpeta vacía,
  contenedor `python:3.12-slim` (Python 3.12.16), `pip install -r requirements.txt` y
  `streamlit run app/app.py`. Con un navegador se pulsaron los tres ejemplos y las
  cinco pestañas del Informe completo: sin errores en pantalla ni de JavaScript.
- **Mismos resultados:** el perfil, el informe y las recomendaciones de los tres
  ejemplos son idénticos, byte a byte, a los de antes de preparar el despliegue,
  tanto en el entorno de trabajo (Python 3.14) como en el clon (Python 3.12).
- **Memoria en un proceso sin Streamlit:** unos 270 MB tras cargar los datos y unos
  300 MB tras los tres puntos. La carga tarda menos de un segundo.
- **Versión de Python:** con las versiones fijadas en `requirements.txt` hay paquetes
  para Python **3.12, 3.13 y 3.14**. Para 3.11 y anteriores no (numpy 2.5.4 no existe
  para ellas). El devcontainer (`.devcontainer/`, para Codespaces) usa también 3.12.
- **Paquetes del sistema:** no hace falta `packages.txt`; geopandas, pyogrio y pyproj
  traen sus bibliotecas dentro.
- **PDF y fecha (comprobado el 2026-11-14 en la imagen de Docker, Python 3.12.16):**
  fpdf2 2.9.0 es Python puro (con fonttools y Pillow, que ya trae Streamlit) y genera el
  informe sin programas del sistema. `tzdata` da la hora de Madrid aunque el servidor no
  tenga zonas horarias. Las huellas de los tres ejemplos son las mismas que con Python
  3.14. Community Cloud funciona en UTC: la fecha de hoy (festivos, avisos, fecha del
  informe) se calcula en hora de Madrid (`src/fecha.py`).

## Antes de publicar

1. Haz `git push` de la rama `main` a GitHub (`Mengying04/barometro`).
2. Comprueba en GitHub que están `app/app.py`, `requirements.txt`,
   `.streamlit/config.toml` y la carpeta `datos/procesados/` con sus ficheros.

## Publicar

1. Entra en <https://share.streamlit.io> con tu cuenta de GitHub y da permiso para
   leer el repositorio.
2. Pulsa **Create app** (o «New app») y elige desplegar desde GitHub.
3. Rellena:
   - **Repository:** `Mengying04/barometro`
   - **Branch:** `main`
   - **Main file path:** `app/app.py`
   - **App URL:** el nombre que quieras, por ejemplo `barometro-madrid`.
4. Abre **Advanced settings** y elige **Python 3.12** (o 3.13). No uses 3.11 ni
   anteriores: la instalación fallaría. No hace falta escribir ningún secreto.
5. Pulsa **Deploy**. La primera vez tarda unos minutos, porque instala las
   dependencias.
6. Cuando arranque, copia la dirección y ponla en el `README.md`, en la línea
   «Demo». Hecho el 2026-11-12: <https://barometro-madrid.streamlit.app/>.

La versión de Python se elige al crear la aplicación. Si te equivocas, lo más sencillo
es borrarla y crearla de nuevo.

## Comprobar que funciona

- [ ] La portada carga y se ve el mapa.
- [ ] Los tres ejemplos dan su titular: «Buena zona para desayunos y menú del día»,
      «Zona de desayunos, con mucha competencia cerca» y «Aquí encajan sobre todo
      desayunos y meriendas».
- [ ] Al pulsar una tarjeta se abre su explicación a todo el ancho.
- [ ] El buscador de la portada sugiere direcciones al escribir, por ejemplo «Plaza
      de la Constitución 1, Fuenlabrada», y al elegir una se ve el resultado.
- [ ] Al bajar, la barra superior sigue visible, con la dirección. Al pulsar sobre ella se
      puede escribir otra: salen las sugerencias por encima del contenido y se busca al
      elegir una, con Intro o con el botón.
- [ ] El Informe completo muestra todas sus secciones, el índice salta entre ellas y
      «Fuentes y licencias» muestra las fechas.
- [ ] En el pie se ven «Powered by CRTM», OpenStreetMap y CartoCiudad.
- [ ] En el móvil se lee bien.

## Qué necesita de internet

- **El servidor** consulta el geocodificador de CartoCiudad (`www.cartociudad.es`)
  mientras alguien escribe una dirección. Si el servicio no dejara salir esa petición,
  el buscador avisaría del fallo; los ejemplos y «Usar mi ubicación» seguirían
  funcionando.
- **El navegador de quien la usa** pide las teselas del mapa a
  `tile.openstreetmap.org`, la biblioteca del mapa a varias CDN y la tipografía a
  Google Fonts. Sin la tipografía se usa la del sistema.

## Mantenimiento

- **Actualizar la aplicación:** cada `git push` a `main` la vuelve a desplegar sola.
- **Actualizar los datos.** La licencia del CRTM pide que la información esté al día,
  y el calendario GTFS de Cercanías solo cubre unas semanas. Lo hace cada semana un
  flujo de GitHub Actions (ver «Actualización automática de los datos», más abajo).
  Para renovarlos a mano:

  ```bash
  python src/descargar_datos.py
  python src/descargar_externas.py
  python src/procesar.py
  python src/procesar_perfil.py
  python src/procesar_informe.py
  python src/movimiento.py --generar
  python src/tablas_readme.py --escribir
  python src/comprobar_datos.py
  python src/resumen_ejemplos.py
  ```

  Después revisa `docs/fuentes.md` y `datos/LICENCIAS.md` (fechas), comprueba los tres
  ejemplos y sube los ficheros de `datos/procesados/` que están permitidos en
  `.gitignore`. Los resultados cambiarán con los datos nuevos: es lo esperado.
- **Reposo:** el servicio gratuito duerme las aplicaciones que pasan un tiempo sin
  visitas y las despierta con un botón. Antes de la presentación conviene abrirla un
  rato antes.
- **Un solo proceso para todos:** los datos se cargan una vez y se comparten entre
  visitantes; cada visitante solo añade el resultado de su punto. No está pensada
  para muchas visitas a la vez.

## Con Docker

El `Dockerfile` de la raíz arranca la misma aplicación en cualquier máquina con Docker,
con los datos procesados del repositorio y sin descargas:

```bash
docker build -t barometro .
docker run --rm -p 8501:8501 barometro
```

- Imagen oficial `python:3.12.16-slim-bookworm`, usuario sin privilegios (`barometro`),
  sin secretos. Ocupa 1,1 GB y el servidor usa unos 320 MB de memoria.
- `.dockerignore` deja fuera `datos/originales`, los entornos virtuales, `.git` y lo que
  la aplicación no usa (capturas, registro, servidor MCP).
- Streamlit Community Cloud no usa este fichero: sirve para probar en local o para
  publicar en otro servicio que admita contenedores.

## Actualización automática de los datos

El flujo `.github/workflows/actualizar-datos.yml` se ejecuta **los lunes a las 04:17
UTC** y también se puede lanzar a mano. Hace esto, en orden:

1. descarga las fuentes, una detrás de otra, con reintentos y esperas;
2. las procesa y regenera la referencia de movimiento y las tablas del README;
3. pasa la comprobación de calidad (`src/comprobar_datos.py`); **si falla, se detiene**;
4. si hay datos nuevos, los sube a la rama `datos/actualizacion-automatica` y abre una
   **propuesta de cambios** (*pull request*) contra `main`.

Nunca escribe en `main`. No usa secretos: solo el permiso temporal que GitHub da a cada
ejecución. El trabajo que descarga y procesa solo puede leer el repositorio; el que
abre la propuesta solo puede escribir una rama y una propuesta.

> **No se ha podido ejecutar en GitHub desde el entorno de trabajo.** Lo comprobado y
> lo que falta está en `docs/registro/2026-11-12-reproducibilidad.md`. La primera
> ejecución hay que lanzarla a mano y mirarla.

### Una sola vez: dar permiso para abrir propuestas

En GitHub, en el repositorio: **Settings → Actions → General → Workflow permissions**,
marcar **«Allow GitHub Actions to create and approve pull requests»** y guardar. Sin
eso, el último paso falla con un error de permisos (la rama se sube, pero la propuesta
no se abre). No hace falta cambiar nada más ni crear ningún secreto.

Recomendable, aunque no imprescindible: proteger `main` (**Settings → Branches** o
**Rules**) para que solo se pueda cambiar con una propuesta aceptada.

### Lanzarlo a mano

Pestaña **Actions → «Actualizar datos» → Run workflow → Run workflow**. Tarda unos
minutos. Al terminar, el resumen de la ejecución enseña los tres ejemplos antes y
después y el informe de calidad.

### Revisar y aceptar la propuesta

1. Abre la pestaña **Pull requests** y entra en «Actualización automática de los datos».
2. Lee el texto de la propuesta:
   - **Los tres ejemplos, antes y después.** Lo normal es que el nivel de movimiento y
     los clientes principales no cambien, o cambien poco. Si un punto cambia de nivel o
     pierde la mitad de la gente, no aceptes sin entender por qué.
   - **Comprobación de calidad:** todas las filas deben llevar ✅.
   - **Ficheros que cambian:** solo `datos/procesados/…`, `docs/fuentes.md` y `README.md`.
3. En **Files changed**, mira `docs/fuentes.md`: fechas nuevas y ningún aviso raro (por
   ejemplo, un fichero con muchas menos filas).
4. Si quieres verla funcionando antes de aceptar:

   ```bash
   git fetch origin
   git switch datos/actualizacion-automatica
   streamlit run app/app.py
   ```

5. En esa misma rama, pon la fecha nueva en `datos/LICENCIAS.md` y en la frase de
   «Datos» del README (se escriben a mano) y, si han cambiado, los resultados de la
   tabla de los tres puntos. Se puede hacer desde GitHub con el lápiz de cada fichero.
6. Pulsa **Squash and merge** y borra la rama cuando GitHub lo ofrezca. Streamlit
   Community Cloud vuelve a desplegar sola con los datos nuevos.

**Si esa semana no quieres los cambios,** cierra la propuesta sin aceptarla. La semana
siguiente el flujo rehace la rama desde `main` con los datos de ese día y abre otra. Si
la propuesta anterior sigue abierta, la actualiza en vez de abrir una nueva.

### Si el flujo falla

GitHub avisa por correo. En **Actions**, la ejecución fallida dice en qué paso:

| Paso | Causa probable | Qué hacer |
|---|---|---|
| Descargar… | Una fuente no responde (pasa: el 2026-11-12 OpenStreetMap devolvió un error 502 y al rato funcionó) | Volver a lanzarlo más tarde con **Re-run jobs** |
| Descargar… , siempre en la misma fuente | La fuente ha cambiado de dirección o de formato (pasó con una fecha del INE) | Hay que corregir `src/descargar_externas.py` o `src/descargar_datos.py` |
| Procesar | Una fuente ha cambiado de columnas | Corregir el script de procesado |
| Comprobación de calidad | Un dato fuera de lo esperado: el informe dice cuál | Mirar el dato. Si es un error de la fuente, esperar a la semana siguiente. Si es correcto (por ejemplo, un censo nuevo), cambiar la referencia en `src/comprobar_datos.py` |
| Subir la rama y abrir la propuesta | Falta el permiso de «Una sola vez» | Marcar la casilla y relanzar |

Mientras falle, **la aplicación sigue funcionando con los datos anteriores**: nada
cambia sin una propuesta aceptada.

### Límites de GitHub Actions: ¿cabe?

Medido el 2026-11-12 en el entorno de trabajo, con todas las fuentes:

| | Medida | Límite de GitHub (ejecutor estándar) | ¿Cabe? |
|---|---|---|---|
| Tiempo | Unos 3 minutos de descarga y 1 de procesado | 6 horas por trabajo; el flujo se corta a los 60 minutos | Sí |
| Disco | 720 MB de datos originales, más las dependencias | Unos 14 GB libres | Sí |
| Memoria | Pico de 1,3 GB (en `procesar_perfil.py`) | 16 GB en repositorios públicos | Sí |
| Lo que sale de la máquina | Un paquete de 2 MB con los ficheros que cambian | — | Sí |

Los límites de GitHub están escritos de memoria. En un repositorio público, los minutos
de Actions no se cobran. El tiempo en GitHub será algo mayor (hay que instalar las
dependencias, alrededor de un minuto) y depende de la red de cada fuente.

### Cosas que conviene saber

- GitHub **desactiva los flujos programados si el repositorio pasa 60 días sin
  actividad**, y avisa por correo. Se reactivan desde la pestaña Actions.
- La hora programada es aproximada: GitHub puede retrasarla.
- El commit de la propuesta lo firma `github-actions[bot]`. Al aceptar con «Squash and
  merge», el commit que entra en `main` es tuyo.
- `procesar_perfil.py` elige el laborable, el sábado y el domingo típicos según la
  fecha: los viajeros pueden cambiar algo de una semana a otra aunque los horarios sean
  los mismos.

## Privacidad en el servicio

- La aplicación no guarda direcciones ni puntos, y tiene desactivadas las
  estadísticas de uso de Streamlit (`gatherUsageStats = false`).
- **Pendiente de comprobar por la autora:** Streamlit Community Cloud es un servicio
  de un tercero y puede registrar por su cuenta las visitas a las aplicaciones que
  aloja. Conviene leer sus condiciones antes de la presentación y, si hace falta,
  decirlo en la aplicación.
- Un repositorio público deja a la vista el código y los datos procesados. Ninguno
  contiene nombres de personas ni de locales, y sus licencias permiten publicarlos
  (ver `datos/LICENCIAS.md`).

## Si algo falla

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| Error al instalar `numpy` o `pandas` | Versión de Python anterior a 3.12 | Crear la aplicación de nuevo con Python 3.12 |
| `FileNotFoundError` en `datos/procesados/…` | Falta un fichero de datos en GitHub | Comprobar `.gitignore` y que el fichero se ha subido |
| «Ahora no podemos buscar direcciones» | CartoCiudad no responde o el servicio bloquea la salida | Usar los ejemplos o «Usar mi ubicación»; volver a probar más tarde |
| El mapa sale en blanco | El navegador no llega a las teselas o a las CDN | Probar con otra red |
| La aplicación se reinicia sola | Se ha quedado sin memoria | Mirar el registro del servicio; no debería pasar con 400 MB |
