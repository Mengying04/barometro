# 2026-11-10 · Aplicación web (fase 4, parte A)

## Qué hace

`app/app.py` es una aplicación de Streamlit que, para un punto de la Comunidad de Madrid,
muestra el perfil por horas, el informe del local y las recomendaciones. **No repite
cálculos**: solo llama a `perfil_horario()`, `informe_local()` y `recomendar()`.

- Para no calcular dos veces, `recomendar()` acepta ahora el perfil y el informe ya
  calculados (`perfil=`, `inf=`). Es el único cambio en `src/`.
- Usa además dos consultas que ya existían en `informe_local`: el municipio del punto
  (`municipio()`) y los locales del radio que se dibujan en el mapa (`locales()` y
  `en_radio()`), con la misma fuente que el informe.

### Cómo se elige el punto

- **Buscador de direcciones** con el geocodificador de CartoCiudad (IGN):
  - solo en la provincia de Madrid;
  - nunca muestra resultados de tipo «topónimo» o «punto de interés», porque son nombres
    de comercios y pueden incluir nombres de personas. Se comprobó que aparecen, por
    ejemplo, ópticas con nombre propio;
  - las calles sin coordenadas se resuelven con una segunda petición (`find`).
- **Clic en el mapa.**
- **Tres ejemplos:** campus de Vicálvaro (40.4046, -3.6106), centro de Fuenlabrada
  (40.283366, -3.800132) y Plaza Mayor de Griñón (40.212861, -3.852623), con las
  coordenadas del registro de la parte A.
- **Fuera de la Comunidad:** si el punto no cae en ninguna sección censal, la app avisa
  y no calcula. Se probó con un punto de Toledo.

### Pantalla

1. **Cabecera:** el nombre, una frase de qué hace y el aviso fijo: «Orientación a partir
   de datos abiertos y supuestos explícitos, no garantías. Toda cifra de personas es una
   estimación.».
2. **Mapa:**
   - folium con streamlit-folium y teselas de OpenStreetMap, con su atribución visible;
   - el punto, el círculo de 300 m y los locales del radio como puntos de color por tipo
     (bar, restaurante, cafetería, comida rápida), sin nombres, ventanas ni datos al
     pasar el ratón;
   - **zoom máximo 16:** a partir de 17, las teselas de OSM rotulan los nombres de los
     bares y comercios.
3. **Resumen:** cuatro tarjetas (a quién, a qué hora, qué vender, a qué precio), además
   de riesgos y avisos.
   - Cada recomendación lleva su confianza, si es dato o estimación, y un «Por qué»
     desplegable.
   - «A qué hora» y «Qué vender» van en pestañas (laborable, sábado y huecos y cocinas)
     para que no sean demasiado largas.
4. **Perfil por horas:** barras apiladas por tipo de cliente (altair) con selector de
   laborable o sábado, la tabla por franjas y la confianza de cada tipo de cliente. El
   domingo no se modela, y se indica.
5. **Mercado:** los seis bloques del informe. Los avisos importantes (cobertura de OSM,
   índice de precios con hoteles, festivos de 2027 sin publicar, hostelería mezclada con
   comercio) van resaltados.
6. **Qué comprobar en persona:** lista numerada, también en un bloque con botón de
   copiar y como descarga en `.txt`. La descarga se genera en memoria.
7. **Fuentes y licencias:**
   - **leídas de `docs/fuentes.md`**, no escritas a mano: la tabla del portal con enlace,
     licencia y fecha, y las fuentes externas y los servicios de la aplicación con
     enlace, licencia, versión y fecha;
   - «**Powered by CRTM**» con enlace a https://www.crtm.es, indicando que los datos del
     Consorcio se usan procesados;
   - «© colaboradores de OpenStreetMap» con enlace a la licencia ODbL y a la página para
     informar de errores del mapa;
   - una nota de que el proyecto no está respaldado por ninguna de las entidades que
     publican los datos.

## Cómo se arranca

Desde la raíz del repositorio, con el entorno virtual activado:

```bash
python -m pip install -r requirements.txt   # streamlit 1.67.0, folium 0.20.0, streamlit-folium 0.27.4
streamlit run app/app.py --server.address 0.0.0.0 --server.port 8501
```

Hacen falta los datos procesados (`src/procesar.py` y `src/procesar_perfil.py`). La
configuración está en `.streamlit/config.toml`:

- `gatherUsageStats = false`;
- `headless = true`;
- registro solo de avisos y errores.

En el sandbox, para verla desde el Mac hay que publicar el puerto en el host:
`sbx ports <sandbox> --publish 8501:8501`.

## Privacidad

- Las direcciones y los puntos solo viven en la memoria de la sesión
  (`st.session_state`): no se escriben en ficheros, en registros ni en la URL.
- No se guardan en caché por punto: la caché solo guarda los datos abiertos
  (`st.cache_resource`) y la lectura de `docs/fuentes.md` (`st.cache_data`).
- Comprobado: después de buscar «Plaza de la Constitución 1, Fuenlabrada», el registro
  del servidor no contiene la dirección.
- La dirección sí se envía a CartoCiudad para geolocalizarla, y la app lo dice en la
  ayuda del buscador.
- Las estadísticas de uso de Streamlit están desactivadas.

## Licencias de los servicios nuevos (anotadas en `docs/fuentes.md`, bloque «aplicacion»)

- **CartoCiudad (IGN).** Según sus preguntas frecuentes oficiales, el uso de los datos
  es libre y gratuito para cualquier propósito legítimo, incluido el comercial. El
  acceso a los servicios web es gratuito siempre que se mencione la autoría así: «CC BY
  4.0 www.scne.es/productos.html#CartoCiudad». La app muestra esa mención bajo el
  buscador. **Permite este uso.**
- **Teselas de OpenStreetMap.** Política de uso consultada el 2026-11-10. Se cumple:
  - URL HTTPS correcta;
  - atribución visible;
  - las teselas las pide el navegador del usuario, con su User-Agent, su Referer y su
    caché;
  - sin descarga masiva.

  La disponibilidad no está garantizada; para un uso intensivo habría que usar otro
  proveedor.

## Pruebas

- **`streamlit.testing.v1.AppTest`:** arranque, los tres ejemplos, una dirección escrita
  y un punto fuera de la Comunidad. Sin excepciones, con el aviso correcto para el punto
  de fuera.
- **Navegador real** (Chromium sin interfaz, con Playwright instalado fuera del
  proyecto): los tres ejemplos y la dirección «Plaza de la Constitución 1, Fuenlabrada»
  (CartoCiudad la sitúa en Fuenlabrada). Además:
  - el mapa se dibuja (430 px de alto, 10 teselas cargadas; 32 trazos en Vicálvaro: los
    27 locales, el círculo y el punto);
  - sin errores de JavaScript;
  - el aviso, «Powered by», la atribución de OSM, la de CartoCiudad, la nota de no
    respaldo, las comprobaciones y las fuentes aparecen en la página.
- **Nombres de locales:** los datos procesados no guardan nombres (solo tipo y
  posición). El mapa no tiene ventanas ni rótulos, el geocodificador descarta topónimos
  y puntos de interés, y el zoom no pasa de 16. A ese zoom, la captura del mapa base solo
  muestra calles, instituciones (universidad, colegio) e iconos, sin nombres de bares ni
  restaurantes.
- **Móvil (390 px):** las columnas se apilan y todo se lee. La tabla de fuentes del
  portal es una tabla de datos con desplazamiento horizontal.
- **Terminal del servidor:** sin errores. Solo el mensaje informativo de Streamlit «Did
  not auto detect external IP».

## Tiempos medidos

Servidor recién arrancado, en el sandbox:

| Paso | Tiempo |
|---|---|
| Primera carga de la página (incluye cargar todos los datos procesados en memoria) | 1,3-1,4 s |
| Primer punto (Vicálvaro): de pulsar el botón a ver la página completa | 1,2 s (cálculo: 0,4 s) |
| Segundo punto (Fuenlabrada) | 0,4 s (cálculo: 0,2 s) |
| Tercer punto (Griñón) | 0,4 s (cálculo: 0,2 s) |
| Dirección escrita (dos consultas a CartoCiudad más el cálculo) | unos 1 s (1,2 s en AppTest) |

Fuera de Streamlit, en un proceso limpio: carga de datos 0,3 s, primer punto 0,18 s y
siguientes unos 0,05 s. La caché funciona: un segundo punto tarda menos de medio
segundo. El primer arranque tras reiniciar la máquina puede ser algo más lento, porque
los ficheros aún no están en la caché del sistema.

## Limitaciones

- **El mapa necesita internet en el navegador:** folium carga Leaflet y sus estilos
  desde CDN (cdn.jsdelivr.net, cdnjs.cloudflare.com, code.jquery.com,
  netdna.bootstrapcdn.com) y las teselas desde tile.openstreetmap.org. Sin ese acceso,
  el mapa sale en blanco; el resto de la página funciona. En el sandbox hubo que
  aprobarlos en el cortafuegos para probarlo.
- **Geocodificador:** depende de que CartoCiudad esté disponible. Busca por parecido
  fonético, así que a veces propone números de portal cercanos y no el exacto: por
  ejemplo, pidiendo «Paseo de los Artilleros 38» ofrece del 27 al 35. Si falla, se puede
  hacer clic en el mapa.
- **El zoom máximo de 16** impide acercarse más, a cambio de no mostrar nombres de
  locales.
- **Domingo** no modelado (igual que en el perfil).
- **Sin control de acceso ni límites de uso:** es un prototipo para una sola persona o
  una demostración, no un servicio público.
- La licencia del CRTM pide que la información mostrada esté **siempre actualizada**: hay
  que volver a ejecutar las descargas y el procesado de forma periódica. La app muestra
  las fechas de los datos.
