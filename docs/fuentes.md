# Fuentes de datos

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

## Discrepancias entre el CSV y la API de datos (datastore_search)

- festivos_regionales_locales/festivos_regionales.csv: CSV 12 filas ≠ datastore 24
