# Fuentes de datos

<!-- inicio:portal -->
## Portal de Datos Abiertos de la Comunidad de Madrid

Conjuntos descargados del [Portal de Datos Abiertos de la Comunidad de Madrid](https://datos.comunidad.madrid) con `src/descargar_datos.py`.

Fecha de descarga: 2026-11-09.

Los ficheros se guardan en `datos/originales/<id>/` y no se suben a GitHub; se regeneran ejecutando el script.

| Título | Ficha | Licencia | Última modificación | Formatos | Filas (CSV) |
|---|---|---|---|---|---|
| Centros educativos de la comunidad de Madrid | [centros_educativos](https://datos.comunidad.madrid/dataset/centros_educativos) | Creative Commons Attribution | 2026-05-05 | CSV, JSON | 7.757 |
| Centros, servicios y establecimientos sanitarios | [centros_servicios_establecimientos_sanitarios](https://datos.comunidad.madrid/dataset/centros_servicios_establecimientos_sanitarios) | Creative Commons Attribution | 2026-11-09 | CSV, JSON | 46.155 |
| Desfibriladores externos fuera del ámbito sanitario | [desfibriladores_externos_fuera_ambito_sanitario](https://datos.comunidad.madrid/dataset/desfibriladores_externos_fuera_ambito_sanitario) | Creative Commons Attribution | 2026-11-09 | CSV, JSON | 13.680 |
| Oficinas de farmacia | [oficinas_farmacia](https://datos.comunidad.madrid/dataset/oficinas_farmacia) | Creative Commons Attribution | 2026-11-09 | CSV, JSON | 2.957 |
| Alojamientos turísticos de la Comunidad de Madrid | [alojamientos_turisticos](https://datos.comunidad.madrid/dataset/alojamientos_turisticos) | Creative Commons Attribution | 2026-11-09 | CSV, JSON | 8.335 |
| Declaraciones responsables de actividad de viviendas de uso turístico de la Comunidad de Madrid presentadas | [declaraciones_actividad_viviendas_uso_turistico](https://datos.comunidad.madrid/dataset/declaraciones_actividad_viviendas_uso_turistico) | Creative Commons Attribution | 2026-10-14 | CSV, JSON, ZIP | 1.164 |
| Secciones censales | [secciones_censales](https://datos.comunidad.madrid/dataset/secciones_censales) | Creative Commons Attribution | 2025-02-07 | CSV, JSON, SHP | 4.417 |
| Festivos regionales y locales año en curso | [festivos_regionales_locales](https://datos.comunidad.madrid/dataset/festivos_regionales_locales) | Creative Commons Attribution | 2026-01-13 | CSV, JSON | 338 + 12 |
| Gasto medio de los hogares por subgrupo de gasto (3 dígitos COICOP/EPF) (Base 2006) | [gasto_por_subgrupo_gasto_3_digitos_coicop_epf_base_2006](https://datos.comunidad.madrid/dataset/gasto_por_subgrupo_gasto_3_digitos_coicop_epf_base_2006) | Creative Commons Attribution | 2026-11-05 | CSV, JSON | 1.680 |
| Índice de Precios de Consumo (IPC), por grupo. Base 2025. Comunidad de Madrid y España | [ipc_base_2025](https://datos.comunidad.madrid/dataset/ipc_base_2025) | Creative Commons Attribution | 2026-11-05 | CSV, JSON | 160.709 |
| Demografía empresarial de la Comunidad de Madrid. Unidades empresariales y puestos de trabajo asociados a las unidades empresariales, por rama de actividad (CNAE-2025) | [demografia_empresarial_cnae25](https://datos.comunidad.madrid/dataset/demografia_empresarial_cnae25) | Creative Commons Attribution | 2026-11-05 | CSV, JSON | 573 |

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

### Consorcio Regional de Transportes de Madrid (CRTM): estaciones y paradas de Metro, Metro Ligero, Cercanías y autobuses interurbanos y urbanos

- **Carpeta:** `datos/originales/crtm_paradas/`
- **Enlace:** Portal de datos abiertos del CRTM, https://datos.crtm.es/ — Metro: ficha «Datos abiertos: Elementos de la Red de Metro» (capa https://services5.arcgis.com/UxADft6QPcvFyDU1/arcgis/rest/services/M4_Red/FeatureServer/0); resto: fichas GTFS https://datos.crtm.es/datasets/crtm::gtfs-red-de-metro-ligero, https://datos.crtm.es/datasets/crtm::gtfs-red-de-cercanías, https://datos.crtm.es/datasets/crtm::gtfs-red-de-autobuses-interurbanos, https://datos.crtm.es/datasets/crtm::gtfs-red-de-emt, https://datos.crtm.es/datasets/crtm::gtfs-red-de-autobuses-urbanos (ficheros servidos desde https://www.arcgis.com/sharing/rest/content/items/<id>/data)
- **Licencia:** [Licencia de datos abiertos y estáticos del CRTM](https://www.crtm.es/licencia-de-uso): uso comercial y no comercial. Obligaciones: mostrar **«Powered by CRTM»** con enlace a [crtm.es](http://www.crtm.es/) en webs y apps; **garantizar que la información mostrada esté siempre actualizada** (volver a ejecutar este script); citar al CRTM como fuente indicando si son datos en bruto o explotados; conservar los metadatos de fecha de actualización; no sugerir que el CRTM patrocina o apoya el producto
- **Fecha de descarga:** 2026-11-09
- **Versión de los datos:** metro_estaciones: capa editada el 2026-06-05; gtfs_metro_ligero.zip: publicado el 2026-11-05, feed_version 20261028; gtfs_cercanias.zip: publicado el 2026-11-05; gtfs_interurbanos.zip: publicado el 2026-11-05, feed_version 20261027; gtfs_emt.zip: publicado el 2026-11-05; gtfs_urbanos.zip: publicado el 2026-11-05, feed_version 20261027
- **Ficheros:**
  - metro_estaciones.geojson (Metro: estaciones (capa de red)): 293 estaciones
  - gtfs_metro_ligero.zip (Metro Ligero / Tranvía; original `google_transit_M10.zip`): 96 registros en stops.txt (location_type 0: 57, location_type 1: 14, location_type 2: 25), 4 líneas, calendario 20261028–20271028
  - gtfs_cercanias.zip (Cercanías (producido por Renfe); original `google_transit_M5.zip`): 95 registros en stops.txt (location_type 0: 95), 38 líneas, calendario 20261030–20261128
  - gtfs_interurbanos.zip (Autobuses interurbanos; original `google_transit_M89.zip`): 8.408 registros en stops.txt (location_type 0: 8.399, location_type 1: 9), 354 líneas, calendario 20261027–20271128
  - gtfs_emt.zip (Autobuses urbanos de Madrid (EMT); original `google_transit_M6.zip`): 4.935 registros en stops.txt (location_type 0: 4.935), 238 líneas, calendario 20261030–20261231
  - gtfs_urbanos.zip (Autobuses urbanos de otros municipios (el CRTM avisa: «datos parciales»); original `google_transit_M9.zip`): 8.408 registros en stops.txt (location_type 0: 8.399, location_type 1: 9), 117 líneas, calendario 20261027–20271128
  - metadatos_capas.json, metadatos_gtfs.json: metadatos originales (fechas de actualización, que la licencia obliga a conservar)
- Metro se toma de la capa de red porque su GTFS publicado (30/05/2025) es anterior a la capa (junio de 2026). Coordenadas de la capa en WGS84 (EPSG:4326).
- Los GTFS se guardan completos, sin descomprimir. Las paradas están en `stops.txt` (`stop_lat`/`stop_lon`, WGS84). `location_type`: 0 = parada o andén, 1 = estación, 2 = acceso; vacío equivale a 0.
- gtfs_interurbanos.zip y gtfs_urbanos.zip comparten el mismo `stops.txt` (paradas de las dos redes juntas); lo que cambia son las líneas y los horarios. Para saber qué paradas usa cada red hay que cruzar `stop_times.txt` y `trips.txt`.
- El calendario del GTFS de Cercanías solo cubre unas semanas: hay que volver a descargarlo con frecuencia.

<!-- fin:externas -->
