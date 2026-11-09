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

<!-- inicio:procesados -->
## Datos procesados

Generados con `src/procesar.py` en `datos/procesados/<capa>.parquet` (GeoParquet, geometría en EPSG:25830 y columnas `lat`/`lon` en EPSG:4326).

- Sistema de coordenadas de origen: las X/Y del portal (centros educativos, sanitarios, farmacias, desfibriladores) y del censo de locales están en ETRS89 / UTM 30N (EPSG:25830). Comprobado el 2026-11-09: los desfibriladores traen también lon/lat y coinciden a 0 m; con ED50 (EPSG:23030) habría ~234 m de desfase. Los demás se contrastaron por distancia al vecino más cercano (desfibriladores, OSM, farmacias del censo).
- Recorte a la Comunidad de Madrid con la unión de las secciones censales; cada punto lleva `cdgseccion` (10 dígitos, como el INE) y `cod_municipio`.
- No se conservan nombres de titulares ni de establecimientos, NIF, teléfonos, faxes ni correos.

| Capa | Origen | Final | Descartes |
|---|---|---|---|
| secciones_censales | 4.417 polígonos | 4.417 | — |
| centros_educativos | 7.757 filas | 3.851 | situación BAJA: 3552; situación INACTIVO: 193; situación ANULACIÓN: 76; situación EN TRÁMITE: 28; situación AUTORIZADO PENDIENTE FUNCIONAMIENTO: 2; sin coordenadas: 55 |
| centros_sanitarios | 15.906 centros | 15.737 | sin coordenadas: 169 |
| desfibriladores | 13.680 filas | 13.679 | fila duplicada exacta: 1 |
| farmacias | 2.957 filas | 2.953 | sin coordenadas: 4 |
| hosteleria_osm | 15.665 elementos | 15.665 | — |
| hosteleria_madrid_capital | 21.596 locales | 19.157 | local cerrado: 1790; local baja reunificación: 350; local baja: 162; local uso vivienda: 48; sin coordenadas: 89 |

**secciones_censales**

- 1 polígono(s) inválido(s) reparado(s)
- Emparejamiento: «28» + CDGSECCION sin guiones = código de 10 dígitos del INE. 4368 de 4417 polígonos con datos 2024; 49 sin datos (1.1 %).
- 150 códigos INE 2024 con datos no tienen polígono (secciones creadas después de 2019) en 60 distritos; sus datos no se usan.
- 111 polígonos marcados como posible división desde 2019 (estimación).
- Población 2024 total en polígonos: 6.704.745; en todos los códigos INE: 6.995.318

**centros_sanitarios**

- 46155 filas (una por servicio) agrupadas en 15906 centros por `centro_nro_registro`; `servicios` separa los servicios con « | ».
- 0 centros con tipo o coordenadas distintos entre sus filas (se toma el primero).
- No se conserva la dirección postal ni el NIF; el original no trae nombre del centro.

**desfibriladores**

- `horario_acceso` se deja tal cual viene (texto libre, sin normalizar).
- No se conserva `direccion_ubicacion` (texto libre que a veces nombra empresas o personas) ni la dirección postal.

**hosteleria_osm**

- `tipo` = etiqueta amenity (restaurant, bar, cafe, fast_food, pub). `cocina` = etiqueta cuisine tal cual (puede llevar varios valores separados por «;»).
- Vías y relaciones (edificios) se representan por su punto central.
- No se conserva el nombre del local ni etiquetas de contacto.

**hosteleria_madrid_capital**

- Hostelería y restauración = división CNAE 56 (servicios de comidas y bebidas): `categoria` distingue restauración (561), catering y comedores colectivos (562) y bares (563). No incluye alojamiento (55) ni discotecas (93).
- Coordenadas: local 17236, edificio (estimación) 1419, agrupación 502, sin coordenadas 89.
- `tiene_terraza`: terraza en situación «Abierta» en el fichero de terrazas. 404 id_local del fichero de terrazas no están entre los locales de hostelería abiertos.
- No se conserva el rótulo (puede ser un nombre de persona).

**Estimaciones** (supuestos explícitos):

- `secciones_censales.posible_division_desde_2019`: se marca una sección de 2019 cuando su distrito tiene códigos INE de 2024 sin polígono (secciones nuevas) y su población cae más de un 25 % entre 2021 y 2024. Supuesto: esa caída se debe a que parte de la sección pasó a otra nueva, así que sus datos de 2024 solo cubren una parte del polígono.
- `hosteleria_madrid_capital.origen_coordenadas = "edificio (estimación)"`: el local no tiene coordenadas propias y se le asigna la media de los demás locales del mismo edificio (mismo `id_ndp_edificio`, es decir, el mismo número de portal).

<!-- fin:procesados -->
