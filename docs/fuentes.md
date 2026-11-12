# Fuentes de datos

<!-- inicio:portal -->
## Portal de Datos Abiertos de la Comunidad de Madrid

Conjuntos descargados del [Portal de Datos Abiertos de la Comunidad de Madrid](https://datos.comunidad.madrid) con `src/descargar_datos.py`.

Fecha de descarga: 2026-11-10.

Los ficheros se guardan en `datos/originales/<id>/` y no se suben a GitHub; se regeneran ejecutando el script.

| Título | Ficha | Licencia | Última modificación | Formatos | Filas (CSV) |
|---|---|---|---|---|---|
| Centros educativos de la comunidad de Madrid | [centros_educativos](https://datos.comunidad.madrid/dataset/centros_educativos) | Creative Commons Attribution | 2026-05-05 | CSV, JSON | 7.757 |
| Centros, servicios y establecimientos sanitarios | [centros_servicios_establecimientos_sanitarios](https://datos.comunidad.madrid/dataset/centros_servicios_establecimientos_sanitarios) | Creative Commons Attribution | 2026-11-10 | CSV, JSON | 46.155 |
| Desfibriladores externos fuera del ámbito sanitario | [desfibriladores_externos_fuera_ambito_sanitario](https://datos.comunidad.madrid/dataset/desfibriladores_externos_fuera_ambito_sanitario) | Creative Commons Attribution | 2026-11-10 | CSV, JSON | 13.680 |
| Oficinas de farmacia | [oficinas_farmacia](https://datos.comunidad.madrid/dataset/oficinas_farmacia) | Creative Commons Attribution | 2026-11-09 | CSV, JSON | 2.957 |
| Alojamientos turísticos de la Comunidad de Madrid | [alojamientos_turisticos](https://datos.comunidad.madrid/dataset/alojamientos_turisticos) | Creative Commons Attribution | 2026-11-09 | CSV, JSON | 8.335 |
| Declaraciones responsables de actividad de viviendas de uso turístico de la Comunidad de Madrid presentadas | [declaraciones_actividad_viviendas_uso_turistico](https://datos.comunidad.madrid/dataset/declaraciones_actividad_viviendas_uso_turistico) | Creative Commons Attribution | 2026-10-14 | CSV, JSON, ZIP | 1.164 |
| Secciones censales | [secciones_censales](https://datos.comunidad.madrid/dataset/secciones_censales) | Creative Commons Attribution | 2025-02-07 | CSV, JSON, SHP | 4.417 |
| Festivos regionales y locales año en curso | [festivos_regionales_locales](https://datos.comunidad.madrid/dataset/festivos_regionales_locales) | Creative Commons Attribution | 2026-01-13 | CSV, JSON | 338 + 12 |
| Gasto medio de los hogares por subgrupo de gasto (3 dígitos COICOP/EPF) (Base 2006) | [gasto_por_subgrupo_gasto_3_digitos_coicop_epf_base_2006](https://datos.comunidad.madrid/dataset/gasto_por_subgrupo_gasto_3_digitos_coicop_epf_base_2006) | Creative Commons Attribution | 2026-11-05 | CSV, JSON | 1.680 |
| Índice de Precios de Consumo (IPC), por grupo. Base 2025. Comunidad de Madrid y España | [ipc_base_2025](https://datos.comunidad.madrid/dataset/ipc_base_2025) | Creative Commons Attribution | 2026-11-05 | CSV, JSON | 160.709 |
| Demografía empresarial de la Comunidad de Madrid. Unidades empresariales y puestos de trabajo asociados a las unidades empresariales, por rama de actividad (CNAE-2025) | [demografia_empresarial_cnae25](https://datos.comunidad.madrid/dataset/demografia_empresarial_cnae25) | Creative Commons Attribution | 2026-11-05 | CSV, JSON | 573 |
| Demografía empresarial de la Comunidad de Madrid. Unidades empresariales y puestos de trabajo asociados a las unidades empresariales, por rama de actividad (CNAE-2009) | [demografia_empresarial_cnae09](https://datos.comunidad.madrid/dataset/demografia_empresarial_cnae09) | Creative Commons Attribution | 2026-11-05 | CSV, JSON | 37.345 |
| Estadísticas de alumnos de centros educativos de la Comunidad de Madrid | [spacm_estadisticas_alumnos](https://datos.comunidad.madrid/dataset/spacm_estadisticas_alumnos) | Creative Commons Attribution | 2026-07-22 | CSV, JSON | 11.479 + 19.664 + 22.693 + 12.031 + 8.963 + 1.781 + 3.154 + 5.311 + 17.885 + 5.311 + 31.679 + 991 + 7.611 + 6.054 + 5.700 + 399 + 10.705 + 16.567 + 4.631 + 9.377 |
| Estudiantes matriculados en estudios de Grado presenciales por universidad | [1925489](https://datos.comunidad.madrid/dataset/1925489) | Creative Commons Attribution | 2026-11-06 | CSV, JSON | 198 |
| Estudiantes matriculados en estudios de máster presenciales por universidad | [1925502](https://datos.comunidad.madrid/dataset/1925502) | Creative Commons Attribution | 2026-11-05 | CSV, JSON | 220 |
| Viajeros subidos y bajados en trenes de cercanias por estaciones | [1923861](https://datos.comunidad.madrid/dataset/1923861) | Creative Commons Attribution | 2026-11-05 | CSV, JSON | 540 |

Cuando un conjunto tiene varios CSV, la columna de filas los muestra en el orden de la ficha separados por «+».

Los recuentos corresponden a la fecha de descarga. Varios conjuntos se reemplazan completos de forma periódica (según el campo «Frecuencia de actualización de datos» de la ficha: alojamientos_turisticos cada semana, los lunes hacia las 06:11; centros_servicios_establecimientos_sanitarios cada día hacia las 06:06), y el CSV y el datastore se actualizan a la vez. Por eso un recuento consultado otro día puede no coincidir: es una versión distinta de los datos, no un corte de la descarga.

### Discrepancias entre el CSV y la API de datos (datastore_search)

- festivos_regionales_locales/festivos_regionales.csv: CSV 12 filas ≠ datastore 24

<!-- fin:portal -->

<!-- inicio:externas -->
## Fuentes externas

Descargadas con `src/descargar_externas.py` en `datos/originales/<carpeta>/`.

### INE. Atlas de distribución de renta de los hogares (ADRH), provincia de Madrid, por municipio, distrito y sección censal

- **Carpeta:** `datos/originales/ine_adrh/`
- **Enlace:** https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177088&idp=1254735976608
- **Licencia:** Reutilización libre citando la fuente: «Fuente: Instituto Nacional de Estadística (INE)» ([aviso legal](https://www.ine.es/aviso_legal))
- **Fecha de descarga:** 2026-11-09
- **Versión de los datos:** Años 2015–2024 (último disponible: **2024**); tablas actualizadas el 2026-10-15
- **Ficheros:**
  - 31097.csv (Indicadores de renta media y mediana): 300.660 filas
  - 31105.csv (Indicadores demográficos): 350.770 filas
- Se descarga la serie completa; el análisis usará el último año. La población está en la tabla 31105, indicador «Población».
- Los valores usan coma decimal y punto de miles; «..» o vacío = dato no disponible (secreto estadístico).

### INE. Cartografía digitalizada de secciones censales, seccionado a 1 de enero de 2025 (toda España)

- **Carpeta:** `datos/originales/ine_seccionado/`
- **Enlace:** https://www.ine.es/ss/Satellite?L=es_ES&c=Page&cid=1259952026632&p=1259952026632&pagename=ProductosYServicios%2FPYSLayout (fichero https://www.ine.es/prodyser/cartografia/seccionado_2025.zip)
- **Licencia:** Reutilización libre citando la fuente: «Fuente: Instituto Nacional de Estadística (INE)» ([aviso legal](https://www.ine.es/aviso_legal))
- **Fecha de descarga:** 2026-11-09
- **Versión de los datos:** Seccionado a 1 de enero de 2025
- **Ficheros:**
  - seccionado_2025.zip: shapefile `España_Seccionado2025_ETRS89H30/SECC_CE_20250101.shp` (ETRS89 / UTM 30N, EPSG:25830); capa.txt: ruta del .shp dentro del ZIP
- Se usa el seccionado de 2025 y no el de 2024 porque es el que corresponde a los datos del Atlas de renta de 2024: casan todas las secciones de Madrid con datos.
- Uso: polígonos de las secciones para la renta y la población del INE (capa `secciones_censales` procesada). Los límites de la Comunidad y de los municipios se toman de las secciones del portal de la Comunidad.

### Censo de locales, sus actividades y terrazas de hostelería y restauración

- **Carpeta:** `datos/originales/madrid_censo_locales/`
- **Enlace:** https://datos.madrid.es/dataset/200085-0-censo-locales
- **Licencia:** Creative Commons Attribution 4.0 International (CC BY 4.0). Citar: «Fuente: Ayuntamiento de Madrid»
- **Fecha de descarga:** 2026-11-09
- **Versión de los datos:** Actualización diaria; ficheros del 2026-11-09
- **Ficheros:**
  - locales.csv (Locales; original `200085-0-censo-locales_2_20261109_063056.csv`): 203.794 filas
  - actividades.csv (Actividades; original `200085-0-censo-locales_4_20261109_063752.csv`): 225.892 filas
  - terrazas.csv (Terrazas; original `200085-0-censo-locales_5_20261109_064136.csv`): 6.614 filas
  - estructura_ds_ficherocla.pdf (Censo de Locales y Actividades. Contenido y estructura del fichero)
  - estructura_ds_ficherocla_terrazas.pdf (Terrazas de hostelería y restauración. Contenido y estructura del fichero)
- No se descargan las copias JSON/XML (mismo contenido) ni el fichero «Locales con información de licencia».

### OpenStreetMap: bares, pubs, cafeterías, restaurantes y comida rápida de la Comunidad de Madrid (API Overpass)

- **Carpeta:** `datos/originales/osm_hosteleria/`
- **Enlace:** https://www.openstreetmap.org/copyright
- **Licencia:** Open Database License (ODbL) 1.0. Citar: «© colaboradores de OpenStreetMap» con enlace a https://www.openstreetmap.org/copyright
- **Fecha de descarga:** 2026-11-09
- **Versión de los datos:** Datos OSM a 2026-11-09T18:22:32Z
- **Ficheros:**
  - osm_hosteleria.json: 15.665 elementos (restaurant 7.675, bar 2.343, cafe 2.225, fast_food 1.792, pub 1.630); 5.753 con etiqueta `cuisine`
  - consulta.overpassql: consulta usada
- Se incluye `amenity=pub` porque en España muchos bares están etiquetados así; se puede filtrar después.
- Nodos con `lat`/`lon`; vías y relaciones con su punto central (`center`).
- Una base de datos derivada que se publique debe mantener la licencia ODbL.

### OpenStreetMap: recintos universitarios (amenity=university) de la Comunidad de Madrid (API Overpass)

- **Carpeta:** `datos/originales/osm_universidades/`
- **Enlace:** https://www.openstreetmap.org/copyright
- **Licencia:** Open Database License (ODbL) 1.0. Citar: «© colaboradores de OpenStreetMap» con enlace a https://www.openstreetmap.org/copyright
- **Fecha de descarga:** 2026-11-10
- **Versión de los datos:** Datos OSM a 2026-11-10T10:36:21Z
- **Ficheros:**
  - osm_universidades.json: 164 elementos (node 42, relation 12, way 110), con geometría completa (`out geom`)
  - consulta.overpassql: consulta usada
- Se usan para ubicar los campus y repartir entre ellos los estudiantes de cada universidad (src/procesar_perfil.py). Unos elementos son campus enteros y otros, facultades o edificios sueltos; no se conserva más que el nombre del centro, el operador y la geometría.
- Una base de datos derivada que se publique debe mantener la licencia ODbL.

### Consorcio Regional de Transportes de Madrid (CRTM): estaciones y paradas de Metro, Metro Ligero, Cercanías y autobuses interurbanos y urbanos, y demanda diaria de viajeros por modo

- **Carpeta:** `datos/originales/crtm_paradas/`
- **Enlace:** Portal de datos abiertos del CRTM, https://datos.crtm.es/ — Metro: ficha «Datos abiertos: Elementos de la Red de Metro» (capa https://services5.arcgis.com/UxADft6QPcvFyDU1/arcgis/rest/services/M4_Red/FeatureServer/0); resto: fichas GTFS https://datos.crtm.es/datasets/crtm::gtfs-red-de-metro, https://datos.crtm.es/datasets/crtm::gtfs-red-de-metro-ligero, https://datos.crtm.es/datasets/crtm::gtfs-red-de-cercanías, https://datos.crtm.es/datasets/crtm::gtfs-red-de-autobuses-interurbanos, https://datos.crtm.es/datasets/crtm::gtfs-red-de-emt, https://datos.crtm.es/datasets/crtm::gtfs-red-de-autobuses-urbanos; demanda: https://datos.crtm.es/datasets/crtm::crtm-evolucion-demanda-diaria (ficheros servidos desde https://www.arcgis.com/sharing/rest/content/items/<id>/data)
- **Licencia:** [Licencia de datos abiertos y estáticos del CRTM](https://www.crtm.es/licencia-de-uso): uso comercial y no comercial. Obligaciones: mostrar **«Powered by CRTM»** con enlace a [crtm.es](http://www.crtm.es/) en webs y apps; **garantizar que la información mostrada esté siempre actualizada** (volver a ejecutar este script); citar al CRTM como fuente indicando si son datos en bruto o explotados; conservar los metadatos de fecha de actualización; no sugerir que el CRTM patrocina o apoya el producto
- **Fecha de descarga:** 2026-11-10
- **Versión de los datos:** metro_estaciones: capa editada el 2026-06-05; gtfs_metro.zip: publicado el 2025-05-30, feed_version 20250527; gtfs_metro_ligero.zip: publicado el 2026-11-05, feed_version 20261028; gtfs_cercanias.zip: publicado el 2026-11-05; gtfs_interurbanos.zip: publicado el 2026-11-05, feed_version 20261027; gtfs_emt.zip: publicado el 2026-11-05; gtfs_urbanos.zip: publicado el 2026-11-05, feed_version 20261027; crtm_demanda_diaria.xlsx: publicado el 2026-10-28
- **Ficheros:**
  - metro_estaciones.geojson (Metro: estaciones (capa de red)): 293 estaciones
  - gtfs_metro.zip (Metro (solo para frecuencias; publicado en mayo de 2025); original `google_transit_M4.zip`): 1.050 registros en stops.txt (location_type 0: 290, location_type 1: 240, location_type 2: 520), 13 líneas, calendario 20250527–20260527
  - gtfs_metro_ligero.zip (Metro Ligero / Tranvía; original `google_transit_M10.zip`): 96 registros en stops.txt (location_type 0: 57, location_type 1: 14, location_type 2: 25), 4 líneas, calendario 20261028–20271028
  - gtfs_cercanias.zip (Cercanías (producido por Renfe); original `google_transit_M5.zip`): 95 registros en stops.txt (location_type 0: 95), 38 líneas, calendario 20261030–20261128
  - gtfs_interurbanos.zip (Autobuses interurbanos; original `google_transit_M89.zip`): 8.408 registros en stops.txt (location_type 0: 8.399, location_type 1: 9), 354 líneas, calendario 20261027–20271128
  - gtfs_emt.zip (Autobuses urbanos de Madrid (EMT); original `google_transit_M6.zip`): 4.935 registros en stops.txt (location_type 0: 4.935), 238 líneas, calendario 20261030–20261231
  - gtfs_urbanos.zip (Autobuses urbanos de otros municipios (el CRTM avisa: «datos parciales»); original `google_transit_M9.zip`): 8.408 registros en stops.txt (location_type 0: 8.399, location_type 1: 9), 117 líneas, calendario 20261027–20271128
  - crtm_demanda_diaria.xlsx (Evolución de la demanda diaria y mensual por modo (Observatorio de la Demanda del Transporte Público); original `CRTM_Evolucion_demanda_diaria.xlsx`): hojas «diaria» y «mensual» con viajeros de Metro de Madrid, EMT, concesiones por carretera y Renfe Cercanías (datos provisionales)
  - metadatos_capas.json, metadatos_gtfs.json: metadatos originales (fechas de actualización, que la licencia obliga a conservar)
- Las estaciones de Metro se toman de la capa de red porque su GTFS publicado (30/05/2025) es anterior a la capa (junio de 2026). Coordenadas de la capa en WGS84 (EPSG:4326). El GTFS de Metro se descarga igualmente, solo para calcular cuántos trenes pasan por hora (src/procesar_perfil.py): los horarios de 2025 se toman como aproximación de los actuales.
- Los GTFS se guardan completos, sin descomprimir. Las paradas están en `stops.txt` (`stop_lat`/`stop_lon`, WGS84). `location_type`: 0 = parada o andén, 1 = estación, 2 = acceso; vacío equivale a 0.
- gtfs_interurbanos.zip y gtfs_urbanos.zip comparten el mismo `stops.txt` (paradas de las dos redes juntas); lo que cambia son las líneas y los horarios. Para saber qué paradas usa cada red hay que cruzar `stop_times.txt` y `trips.txt`.
- El calendario del GTFS de Cercanías solo cubre unas semanas: hay que volver a descargarlo con frecuencia.
- La demanda diaria sirve para calibrar cuántas personas suben o bajan por cada tren o autobús que para (src/procesar_perfil.py). Es por modo, no por estación.

<!-- fin:externas -->

<!-- inicio:procesados -->
## Datos procesados

Generados con `src/procesar.py` en `datos/procesados/<capa>.parquet` (GeoParquet, geometría en EPSG:25830 y columnas `lat`/`lon` en EPSG:4326).

- Sistema de coordenadas de origen: las X/Y del portal (centros educativos, sanitarios, farmacias, desfibriladores) y del censo de locales están en ETRS89 / UTM 30N (EPSG:25830). Comprobado el 2026-11-09: los desfibriladores traen también lon/lat y coinciden a 0 m; con ED50 (EPSG:23030) habría ~234 m de desfase. Los demás se contrastaron por distancia al vecino más cercano (desfibriladores, OSM, farmacias del censo).
- Dos cartografías de secciones censales, cada una con un uso:
  - **Secciones del portal de la Comunidad** (`secciones_censales/558.zip`, seccionado 2019): límite de la Comunidad para recortar todas las capas y límites municipales (`cod_municipio` de cada punto).
  - **Cartografía del INE** (`ine_seccionado/`, seccionado a 1 de enero de 2025): polígonos de la capa `secciones_censales` con la renta y la población del Atlas de renta de 2024, y `cdgseccion` de cada punto (sección del INE en la que cae, para cruzarlo con la renta).
- No se conservan nombres de titulares ni de establecimientos, NIF, teléfonos, faxes ni correos.

| Capa | Origen | Final | Descartes |
|---|---|---|---|
| secciones_censales | 4.518 polígonos | 4.518 | — |
| centros_educativos | 7.757 filas | 3.851 | situación BAJA: 3552; situación INACTIVO: 193; situación ANULACIÓN: 76; situación EN TRÁMITE: 28; situación AUTORIZADO PENDIENTE FUNCIONAMIENTO: 2; sin coordenadas: 55 |
| centros_sanitarios | 15.906 centros | 15.737 | sin coordenadas: 169 |
| desfibriladores | 13.680 filas | 13.679 | fila duplicada exacta: 1 |
| farmacias | 2.957 filas | 2.953 | sin coordenadas: 4 |
| hosteleria_osm | 15.665 elementos | 15.665 | — |
| hosteleria_madrid_capital | 21.596 locales | 17.143 | local cerrado: 1790; local baja reunificación: 350; local baja: 162; local uso vivienda: 48; solo catering o comedor colectivo (CNAE 562): 2036; sin coordenadas: 67 |

**secciones_censales**

- Polígonos: cartografía del INE, seccionado a 1 de enero de 2025 (4518 secciones de la provincia de Madrid); 0 inválidos reparados.
- Emparejamiento: `CUSEC` de la cartografía = código de 10 dígitos del Atlas de renta («2807912062 Madrid sección 12062»). 4518 de 4518 polígonos con datos 2024; 0 sin datos (0.0 %). 0 secciones INE con datos sin polígono.
- Población 2024 en polígonos: 6.995.318; total de las secciones INE con dato: 6.995.318.
- Recorte al límite de la Comunidad del portal: se pierde un 0.050 % del área (diferencias de borde entre cartografías).
- 0 secciones cuyo punto interior cae en otro municipio según el portal.

**centros_sanitarios**

- 46155 filas (una por servicio) agrupadas en 15906 centros por `centro_nro_registro`; `servicios` separa los servicios con « | ».
- 0 centros con tipo o coordenadas distintos entre sus filas (se toma el primero).
- No se conserva la dirección postal ni el NIF; el original no trae nombre del centro.

**desfibriladores**

- 3 puntos tienen una sección del INE de otro municipio que el del portal (diferencias de borde entre las dos cartografías).
- `horario_acceso` se deja tal cual viene (texto libre, sin normalizar).
- No se conserva `direccion_ubicacion` (texto libre que a veces nombra empresas o personas) ni la dirección postal.

**hosteleria_osm**

- 1 puntos dentro de la Comunidad no caen en ningún polígono del INE (diferencias de borde); quedan sin `cdgseccion`.
- 1 puntos tienen una sección del INE de otro municipio que el del portal (diferencias de borde entre las dos cartografías).
- `tipo` = etiqueta amenity (restaurant, bar, cafe, fast_food, pub). `cocina` = etiqueta cuisine tal cual (puede llevar varios valores separados por «;»).
- Vías y relaciones (edificios) se representan por su punto central.
- `horario_osm` = etiqueta opening_hours tal cual (la tienen pocos locales); `comida_osm` = etiqueta food (casi nunca está).
- No se conserva el nombre del local ni etiquetas de contacto.

**hosteleria_madrid_capital**

- Hostelería y restauración = división CNAE 56 (servicios de comidas y bebidas) sin catering ni comedores colectivos (562), que no compiten con un bar abierto al público. `categoria` distingue restauración (561) y bares (563). No incluye alojamiento (55) ni discotecas (93).
- 142 locales con catering o comedor colectivo y además otra actividad de hostelería se conservan, sin el epígrafe 562.
- Coordenadas: local 16007, edificio (estimación) 641, agrupación 495, sin coordenadas 67.
- `tiene_terraza`: terraza en situación «Abierta» en el fichero de terrazas. 412 id_local del fichero de terrazas no están entre los locales de hostelería abiertos.
- No se conserva el rótulo (puede ser un nombre de persona).

**Estimaciones** (supuestos explícitos):

- `hosteleria_madrid_capital.origen_coordenadas = "edificio (estimación)"`: el local no tiene coordenadas propias y se le asigna la media de los demás locales del mismo edificio (mismo `id_ndp_edificio`, es decir, el mismo número de portal).

<!-- fin:procesados -->

<!-- inicio:perfil -->
## Datos para el perfil por horas

Generados con `src/procesar_perfil.py` en `datos/procesados/` (GeoParquet, EPSG:25830, con `lat`/`lon`). Supuestos en `src/supuestos.py`.

**centros_educativos_alumnos** (3.851 centros → 3.851)

- Fuente de los alumnos: «Estadísticas de alumnos» del portal (spacm_estadisticas_alumnos), curso 2024/2025, alumnos de régimen general por municipio (distrito en Madrid capital), enseñanza y titularidad.
- No hay un conjunto con alumnos por centro: cada total se reparte a partes iguales entre los centros del territorio que imparten esa enseñanza (según su tipo) y tienen esa titularidad (pública, concertada o privada). **Estimación**: un colegio grande y uno pequeño reciben lo mismo.
- Alumnos asignados: 1.256.640 de 1.258.015 (99.9 %); 20.481 repartidos sin respetar la titularidad (no había centros de esa titularidad con esa enseñanza en el territorio).
- 3202 centros con alumnos de la estadística; 539 con peso típico por tipo (idiomas, música, adultos…); 110 sin alumnos (equipos de orientación, oficinas).
- 11 centros de Madrid capital sin distrito reconocible.

**campus_universitarios** (164 elementos OSM → 98)

- Descartados por no es un centro de estudios (residencia, museo, oficinas, instituto…): 13
- Ubicación: elementos `amenity=university` de OpenStreetMap (polígonos; los puntos se tratan como un círculo de 1 ha).
- Asignación a universidad: 78 por su nombre u operador, 25 por estar dentro del recinto de una universidad; el resto son «otros» centros de estudios superiores con 300 estudiantes al día (**supuesto**).
- Estudiantes: Grado + máster presenciales por universidad, año 2026 de las tablas 1925489 y 1925502 del portal (datos provisionales): 323.345 de 331.029 colocados en algún campus.
- Reparto entre campus de la misma universidad (unidos si están a menos de 300 m): proporcional a la raíz cuadrada de la superficie (**estimación**, ver src/supuestos.py).
- Campus por universidad: CEU 2 (11.361); Comillas 3 (13.067); ESIC 2 (2.762); Nebrija 5 (14.218); UAH 3 (19.695); UAM 3 (26.296); UAX 1 (16.197); UC3M 3 (20.537); UCJC 3 (14.244); UCM 8 (57.745); UEM 2 (24.988); UFV 1 (14.947); UNIE 1 (4.760); UPM 5 (35.377); URJC 6 (44.622); Villanueva 2 (2.529).
- Universidades de la estadística sin ningún campus en OSM (sus estudiantes no se colocan): CUNEF, UDIT.

**desfibriladores_horario** (13.679 filas → 3.258)

- Descartados por en un vehículo (autobús): 2202
- Descartados por «Centro educativo» junto a un campus universitario (a menos de 150 m): 172
- Descartados por tipo sin uso en el perfil (Otros, transporte, aeropuertos, colegio ya listado): 6725
- Descartados por fusionados con otro del mismo sitio: 1322
- Interpretación de `horario_acceso` (todas las filas): vacio 4407, rango 3235, 24h 3208, vehiculo 2202, no_interpretable 366, expresion 180, eventos 81. rango = horas leídas del texto; expresion = «horario de oficina», «comercial», «lectivo»…; 24h y vacío usan el horario típico del tipo de establecimiento.
- 344 desfibriladores de «Centro educativo» sin ningún centro del listado a menos de 120 m ni campus universitario a menos de 150 m (academias, centros de estudios que no están en ninguna lista): se cuentan como «universitarios» con 1000 usuarios al día y horario universitario (**supuesto**), fusionando los que están a menos de 150 m.
- Los del mismo tipo a menos de 50 m se fusionan en un solo sitio (`n_dea` = cuántos había).
- `cliente`, `personas_dia` y `perfil` salen de src/supuestos.py (**estimación**).
- No se guarda el texto libre de `horario_acceso` (ya está interpretado en `horario_tipo` y en las horas de apertura y cierre, y alguna vez nombra el establecimiento).

**salidas_paradas** (15.207 paradas → 15.207)

- Pasos de vehículos (cada vez que un tren o autobús para en la parada) por hora, en un laborable típico (`lab_00`…`lab_23`) y un sábado típico (`sab_00`…`sab_23`). Las horas de más de 24:00 del GTFS se pasan a la madrugada (25:30 → 1).
- Día típico de cada red: entre los martes, miércoles y jueves (y entre los sábados) de las 4 primeras semanas de vigencia a partir de hoy, sin los días con menos del 80 % de los viajes del día mediano (festivos), el día en que circulan más líneas y, entre los empatados, el de número de viajes mediano. Antes se tomaba solo el de viajes mediano, y en interurbanos y urbanos caía en un día en que el GTFS deja sin servicio 21 líneas de la Sierra (su calendario de miércoles y jueves solo vale para un día suelto; el resto del año solo figuran los martes).
- Viajes sin hora en cada parada (interurbanos y urbanos): son viajes reales, con su calendario y su hora de salida, en los que todas las paradas llevan la misma hora (la de salida o, si viene la hora de relleno 01:00:00, la que figura en el identificador del viaje). Antes se descartaban y sus líneas (480-499, 350-355, 665-667, urbanos de Pinto, Valdemoro, Arganda o Tres Cantos…) salían sin servicio. Ahora se cuentan: el número de vehículos es un **dato** y la hora en cada parada, una **estimación** (salida + orden de la parada × tiempo mediano entre paradas de los viajes con horario de la red).
- `origen_pasos` dice si los pasos de la parada salen de los horarios del GTFS o de una línea reconstruida (estimación).
- Metro: GTFS de mayo de 2025 (el más reciente publicado, comprobado el 2026-11-12: el fichero del CRTM no se ha modificado desde el 30/05/2025; su calendario terminó el 27/05/2026), así que se usa un día dentro de su vigencia. **Estimación**: se supone que las frecuencias actuales son parecidas.
- Cercanías, línea C9 (Cercedilla-Cotos): excluida. Está cerrada por obras de renovación desde mayo de 2024 (aviso de cierre: https://www.timeout.es/madrid/es/noticias/la-linea-de-cercanias-que-lleva-a-la-sierra-de-guadarrama-cierra-en-mayo-042924; consultado el 2026-11-12) y el GTFS solo le pone viajes 5 días sueltos del mes. Revisar cuando reabra (`GTFS_LINEAS_EXCLUIDAS` en src/supuestos.py).
- Interurbanos y urbanos comparten `stops.txt`: cada red cuenta solo sus vehículos.
- Geometría: la parada; en Metro y Metro Ligero, el conjunto de accesos de la estación (`location_type` 2 del GTFS), para medir la distancia a la salida más cercana a la calle.
- metro: laborable 2026-05-13, sábado 2026-05-09 (viajes-plantilla de frequencies.txt expandidos); ese laborable circulan 12 de las 13 líneas del fichero; 271 con la posición de sus accesos; 290 paradas con servicio; 122.515 pasos en laborable
- metro_ligero: laborable 2026-11-25, sábado 2026-11-21; ese laborable circulan 4 de las 4 líneas del fichero; 13 con la posición de sus accesos; 57 paradas con servicio; 12.507 pasos en laborable
- cercanias: laborable 2026-11-12, sábado 2026-11-21; ese laborable circulan 11 de las 12 líneas del fichero; línea C9 excluida (sin servicio habitual: cerrada por obras); 93 paradas con servicio; 20.201 pasos en laborable
- emt: laborable 2026-11-25, sábado 2026-11-21; ese laborable circulan 234 de las 238 líneas del fichero; 4935 paradas con servicio; 982.548 pasos en laborable
- interurbanos: laborable 2026-11-24, sábado 2026-11-21; ese laborable circulan 335 de las 354 líneas del fichero; 5759 viajes de 68 líneas sin hora en cada parada, contados con la hora estimada (salida + 117 s por parada); 56 repetidos y 11 sin hora de salida, descartados; 6768 paradas con servicio; 880.577 pasos en laborable
- urbanos: laborable 2026-11-24, sábado 2026-11-21; ese laborable circulan 110 de las 117 líneas del fichero; 1600 viajes de 24 líneas sin hora en cada parada, contados con la hora estimada (salida + 90 s por parada); 54 repetidos y 0 sin hora de salida, descartados; 3064 paradas con servicio; 240.476 pasos en laborable
- metro: **línea 3 reconstruida (estimación)**. El GTFS trae sus andenes pero ningún viaje. En cada andén (18 propios y 1 de otra línea en la misma estación: EL CASAR) se ponen, hora a hora, los trenes de la estación mediana de las líneas 1, 2, 4, 5 (media de las cuatro): 461 trenes al día en laborable y 370 en sábado, sumando los dos sentidos.
- Calibración con la demanda diaria del CRTM (2026-08-30 a 2026-10-25; mediana de martes a jueves y de sábados, sin festivos): personas por paso = 2 × viajeros del día / pasos de vehículos del día en el GTFS. **Estimación**: igual en todas las paradas de la red.
- Laborable: Conc. por carretera 1.140.012 viajeros / 1.121.053 pasos → 2.0 personas por paso; EMT 1.768.702 viajeros / 982.548 pasos → 3.6 personas por paso; Metro de Madrid 2.520.976 viajeros / 122.515 pasos → 41.2 personas por paso; Renfe Cercanías 735.479 viajeros / 20.201 pasos → 72.8 personas por paso
- Sábado: Conc. por carretera 562.112 viajeros / 828.493 pasos → 1.4 personas por paso; EMT 1.037.032 viajeros / 656.740 pasos → 3.2 personas por paso; Metro de Madrid 1.744.264 viajeros / 100.230 pasos → 34.8 personas por paso; Renfe Cercanías 441.096 viajeros / 15.615 pasos → 56.5 personas por paso
- Cercanías: 19 estaciones con viajeros subidos y bajados propios (portal, conjunto 1923861, año 2024); su valor es el de la red multiplicado por la proporción entre la estación y la media de la red: SOL ×3.49, VILLAVERDE BAJO ×1.15, VICALVARO ×1.45, CHAMARTIN ×1.44, VILLAVERDE ALTO ×1.40, ALUCHE ×1.46, MOSTOLES ×1.52, VALLECAS ×1.75, ATOCHA ×4.59, NUEVOS MINISTERIOS ×2.53, MENDEZ ALVARO ×1.78, RECOLETOS ×0.96, FUENLABRADA ×1.75, PARLA ×2.68, EMBAJADORES ×1.49, PRINCIPE PIO ×1.99, ALCALA DE HENARES ×1.71, LEGANES ×1.48, CANTOBLANCO ×1.89. Sin emparejar (sin dato o nombre ambiguo): GETAFE, ENTREVIAS.

**lineas_paradas** (36.484 pares parada-línea-sentido → 36.484)

- Por cada parada, línea y sentido: vehículos que paran en el laborable típico (`vehiculos_lab`), con los mismos días y los mismos viajes que `salidas_paradas` (se comprueba que cada parada suma lo mismo que su `total_lab`). Sin geometría: se cruza con `salidas_paradas` por `red` y `stop_id`.
- `linea` es el nombre corto de la línea (`route_short_name`); `id_linea` la distingue de otras con el mismo nombre (urbanos de distintos municipios). En Cercanías, que no trae sentido, cada `route_id` hace de sentido.
- `estimada` vale verdadero en las líneas reconstruidas (línea 3 de Metro): sus vehículos son una **estimación** (ver `salidas_paradas`).
- Las líneas que «no salen» no tienen viajes ese laborable: no tienen ninguno en el fichero, solo circulan en fin de semana o festivo, o están excluidas por obras (C9 de Cercanías).
- metro: 13 líneas con servicio el 2026-05-13 (la 3, reconstruida: **estimación**)
- metro_ligero: 4 líneas con servicio el 2026-11-25
- cercanias: 11 líneas con servicio el 2026-11-12; no salen: C9
- emt: 234 líneas con servicio el 2026-11-25; no salen: 172SF, SE721, SE730, SE766 (sin ningún viaje en el fichero: SE721, SE730, SE766)
- interurbanos: 335 líneas con servicio el 2026-11-24; no salen: 196, 199A, 414, 635, 692, 720, 721, 722, 723, 724, 725, 726, 727, 728, 819, FS1, FS2, N702, N908 (sin ningún viaje en el fichero: 635, 720, 721, 722, 723, 724, 725, 726, 727, 728, N702, N908)
- urbanos: 110 líneas con servicio el 2026-11-24; no salen: 3A, I1, SE (sin ningún viaje en el fichero: 3A, I1, SE)

<!-- fin:perfil -->

<!-- inicio:informe -->
## Tablas del informe del local

Generadas con `src/procesar_informe.py` en `datos/procesados/informe/` (CSV con «;»). Son las filas y columnas de siete conjuntos del portal que usa `src/informe_local.py`, sin calcular ni cambiar valores, para que la aplicación funcione sin los ficheros originales.

| Fichero | Conjunto del portal | Filas | Qué se conserva |
|---|---|---|---|
| gasto_restauracion.csv | gasto_por_subgrupo_gasto_3_digitos_coicop_epf_base_2006 | 10 | Gasto medio por persona en restauración, por año |
| ipc.csv | ipc_base_2025 | 26.355 | Tasas interanuales de la Comunidad de Madrid, por grupo y mes |
| alojamientos_turisticos.csv | alojamientos_turisticos | 8.335 | Tipo de alojamiento, código postal y localidad |
| viviendas_uso_turistico.csv | declaraciones_actividad_viviendas_uso_turistico | 1.164 | Localidad |
| festivos_locales.csv | festivos_regionales_locales | 338 | Municipio, entidad y fecha |
| festivos_regionales.csv | festivos_regionales_locales | 12 | Fecha y festividad |
| demografia_cnae09.csv | demografia_empresarial_cnae09 | 6.432 | Serie de unidades empresariales por rama |
| demografia_cnae25.csv | demografia_empresarial_cnae25 | 192 | Serie de unidades empresariales por rama |

- No se copian la denominación de los alojamientos ni las direcciones.
- `fuentes.json` guarda de cada fuente el título, la licencia, la fecha de última modificación y la fecha de descarga, sin alterarlas.
- Las licencias de todos los ficheros publicados en el repositorio están en `datos/LICENCIAS.md`.

<!-- fin:informe -->

<!-- inicio:aplicacion -->
## Servicios que usa la aplicación web (app/app.py)

No se descargan: la aplicación los consulta en el momento.

### CartoCiudad: geocodificador de direcciones (Instituto Geográfico Nacional)

- **Enlace:** https://www.cartociudad.es/web/portal/directorio-de-servicios/geoprocesamiento (servicio REST Geocoder: `https://www.cartociudad.es/geocoder/api/geocoder/candidates` y `.../find`)
- **Licencia:** CC BY 4.0. Según las preguntas frecuentes oficiales (https://www.cartociudad.es/web/portal/faq, consultadas el 2026-11-10): «Se permite el uso libre y gratuito de los datos para cualquier propósito legítimo, incluido el comercial y la publicación», y «el acceso y uso de los servicios web de CartoCiudad son gratuitos en cualquier caso, siempre que se mencionen la autoría y propiedad del siguiente modo: «CC BY 4.0 www.scne.es/productos.html#CartoCiudad»». El aviso legal (https://www.cartociudad.es/web/portal/aviso-legal) pide un uso lícito y citar el origen. La aplicación muestra esa mención junto al buscador.
- **Fecha de descarga:** no se descarga (consulta en el momento); condiciones revisadas el 2026-11-10
- **Versión de los datos:** la vigente en el servicio en el momento de la consulta
- Uso: convertir la dirección que escribe el usuario en coordenadas (`candidates` y, para calles sin coordenadas, `find`), solo en la provincia de Madrid (`provincia_filter=Madrid`).
- Privacidad: la dirección se envía a CartoCiudad para geolocalizarla; la aplicación no la guarda. No se muestran resultados de tipo «topónimo» ni «punto de interés» (pueden ser nombres de comercios o de personas).

### OpenStreetMap: teselas del mapa base

- **Enlace:** https://www.openstreetmap.org/copyright (teselas `https://tile.openstreetmap.org/{z}/{x}/{y}.png`)
- **Licencia:** datos con Open Database License (ODbL) 1.0; atribución obligatoria «© colaboradores de OpenStreetMap» con enlace a https://www.openstreetmap.org/copyright, que el mapa muestra en su esquina. Política de uso de las teselas (https://operations.osmfoundation.org/policies/tiles/, consultada el 2026-11-10): se cumple usando la URL HTTPS `https://tile.openstreetmap.org/{z}/{x}/{y}.png`, mostrando la atribución visible en el mapa, sin descarga masiva ni precarga, y dejando que sea el navegador de quien usa la aplicación quien pida las teselas (con su User-Agent, su Referer y su caché). Disponibilidad sin garantía («best-effort»); para un uso intensivo habría que usar otro proveedor. Se añade el enlace recomendado para informar de errores del mapa (https://www.openstreetmap.org/fixthemap).
- **Fecha de descarga:** no se descarga (el navegador las pide al ver el mapa)
- **Versión de los datos:** la vigente en el servidor de teselas

<!-- fin:aplicacion -->
