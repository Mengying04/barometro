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
  para ellas).
- **Paquetes del sistema:** no hace falta `packages.txt`; geopandas, pyogrio y pyproj
  traen sus bibliotecas dentro.

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
- [ ] El buscador encuentra una dirección, por ejemplo «Plaza de la Constitución 1,
      Fuenlabrada».
- [ ] El Informe completo abre sus cinco pestañas y «Fuentes y licencias» muestra
      las fechas.
- [ ] En el pie se ven «Powered by CRTM», OpenStreetMap y CartoCiudad.
- [ ] En el móvil se lee bien.

## Qué necesita de internet

- **El servidor** consulta el geocodificador de CartoCiudad (`www.cartociudad.es`)
  cuando alguien busca una dirección. Si el servicio no dejara salir esa petición, el
  buscador avisaría del fallo; los ejemplos y el clic en el mapa seguirían
  funcionando.
- **El navegador de quien la usa** pide las teselas del mapa a
  `tile.openstreetmap.org`, la biblioteca del mapa a varias CDN y la tipografía a
  Google Fonts. Sin la tipografía se usa la del sistema.

## Mantenimiento

- **Actualizar la aplicación:** cada `git push` a `main` la vuelve a desplegar sola.
- **Actualizar los datos.** La licencia del CRTM pide que la información esté al día,
  y el calendario GTFS de Cercanías solo cubre unas semanas. Para renovarlos:

  ```bash
  python src/descargar_datos.py
  python src/descargar_externas.py
  python src/procesar.py
  python src/procesar_perfil.py
  python src/procesar_informe.py
  python src/movimiento.py --generar
  python src/tablas_readme.py --escribir
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
| «Ahora no podemos buscar direcciones» | CartoCiudad no responde o el servicio bloquea la salida | Usar los ejemplos o el clic en el mapa; volver a probar más tarde |
| El mapa sale en blanco | El navegador no llega a las teselas o a las CDN | Probar con otra red |
| La aplicación se reinicia sola | Se ha quedado sin memoria | Mirar el registro del servicio; no debería pasar con 400 MB |
