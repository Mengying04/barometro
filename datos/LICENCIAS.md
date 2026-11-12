# Licencias de los datos de este repositorio

**La licencia MIT del fichero `LICENSE` se aplica solo al código** (`src/`, `app/` y la
documentación escrita para el proyecto). **No se aplica a los datos de esta carpeta.**
Cada fichero de `datos/procesados/` deriva de una o varias fuentes públicas y conserva la
licencia de su fuente, como se detalla abajo.

Aquí solo están los datos procesados que la aplicación necesita para funcionar. Los
ficheros originales no se redistribuyen: se descargan de cada fuente con
`src/descargar_datos.py` y `src/descargar_externas.py`. El detalle de cada fuente
(enlace, versión, fecha de descarga y cómo se procesó) está en
[`docs/fuentes.md`](../docs/fuentes.md).

Ningún fichero contiene nombres de personas, nombres de bares o restaurantes, rótulos,
direcciones postales, NIF, teléfonos ni correos.

## Licencias y citas

| Fuente | Licencia | Cita |
|---|---|---|
| Portal de Datos Abiertos de la Comunidad de Madrid | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/legalcode.es) | «Fuente: Comunidad de Madrid, Portal de Datos Abiertos (datos.comunidad.madrid)» |
| Ayuntamiento de Madrid, censo de locales | CC BY 4.0 | «Fuente: Ayuntamiento de Madrid» |
| Instituto Nacional de Estadística (INE) | Reutilización libre citando la fuente ([aviso legal](https://www.ine.es/aviso_legal)) | «Fuente: Instituto Nacional de Estadística (INE)». Elaboración propia con datos del INE; el INE no ha participado en ella. |
| OpenStreetMap | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) | «© colaboradores de OpenStreetMap», con enlace a <https://www.openstreetmap.org/copyright> |
| Consorcio Regional de Transportes de Madrid (CRTM) | [Licencia de datos abiertos y estáticos del CRTM](https://www.crtm.es/licencia-de-uso) | «Fuente: CRTM. Datos explotados (procesados), no en bruto». En webs y aplicaciones, «Powered by CRTM» con enlace a <https://www.crtm.es> |

CartoCiudad (IGN, CC BY 4.0) solo se consulta desde la aplicación para situar una
dirección: no hay datos de CartoCiudad en este repositorio.

## Qué licencia aplica a cada fichero

Todos están en `datos/procesados/`. En todos se ha cambiado algo respecto al original:
se han elegido filas y columnas, y en las capas geográficas se han añadido el municipio
y la sección censal de cada punto.

| Fichero | Deriva de | Licencia del fichero |
|---|---|---|
| `hosteleria_osm.parquet` | OpenStreetMap (bares, restaurantes, cafeterías y comida rápida); municipio y sección censal de la Comunidad de Madrid y del INE | **ODbL 1.0** (base de datos derivada de OpenStreetMap) |
| `campus_universitarios.parquet` | OpenStreetMap (recintos universitarios); estudiantes por universidad del portal de la Comunidad de Madrid | **ODbL 1.0** (base de datos derivada de OpenStreetMap); los estudiantes, además, citando a la Comunidad de Madrid |
| `desfibriladores_horario.parquet` | Portal de la Comunidad de Madrid (desfibriladores externos). Para descartar los que están junto a un campus se usó la posición de los campus de OpenStreetMap | **CC BY 4.0** (Comunidad de Madrid). Por prudencia, al haber usado OpenStreetMap como filtro, se ofrece también bajo **ODbL 1.0** con las dos citas |
| `hosteleria_madrid_capital.parquet` | Censo de locales del Ayuntamiento de Madrid | **CC BY 4.0** (Ayuntamiento de Madrid) |
| `centros_educativos_alumnos.parquet` | Portal de la Comunidad de Madrid (centros educativos y estadísticas de alumnos) | **CC BY 4.0** (Comunidad de Madrid) |
| `centros_sanitarios.parquet` | Portal de la Comunidad de Madrid (centros, servicios y establecimientos sanitarios) | **CC BY 4.0** (Comunidad de Madrid) |
| `secciones_censales.parquet` | INE (cartografía de secciones censales de 2025 y Atlas de distribución de renta de los hogares, 2024); límites municipales del portal de la Comunidad de Madrid | Reutilización citando al **INE**; los límites, **CC BY 4.0** (Comunidad de Madrid) |
| `salidas_paradas.parquet` | CRTM (paradas, horarios GTFS y demanda diaria); viajeros de Cercanías por estación del portal de la Comunidad de Madrid | **Licencia del CRTM**, con las mismas condiciones; los viajeros por estación, **CC BY 4.0** (Comunidad de Madrid) |
| `salidas_paradas_dias.json` | CRTM: días del calendario GTFS usados como laborable y sábado típicos | **Licencia del CRTM** |
| `lineas_paradas.parquet` | CRTM (horarios GTFS): por parada, línea y sentido, vehículos que paran en el laborable típico | **Licencia del CRTM**, con las mismas condiciones |
| `referencia_movimiento.parquet` | Elaboración propia: gente que pasa en un laborable (estimación del perfil por horas) en un punto interior de cada sección censal. Se calcula con todos los ficheros anteriores del perfil | Las de sus fuentes a la vez: **CC BY 4.0** (Comunidad de Madrid), **INE**, **ODbL 1.0** (campus de OpenStreetMap) y **licencia del CRTM**, con todas las citas |
| `informe/gasto_restauracion.csv` | Portal de la Comunidad de Madrid (gasto medio de los hogares) | **CC BY 4.0** (Comunidad de Madrid) |
| `informe/ipc.csv` | Portal de la Comunidad de Madrid (IPC por grupo, base 2025) | **CC BY 4.0** (Comunidad de Madrid) |
| `informe/alojamientos_turisticos.csv` | Portal de la Comunidad de Madrid (alojamientos turísticos): solo tipo, código postal y localidad | **CC BY 4.0** (Comunidad de Madrid) |
| `informe/viviendas_uso_turistico.csv` | Portal de la Comunidad de Madrid (declaraciones responsables): solo la localidad | **CC BY 4.0** (Comunidad de Madrid) |
| `informe/festivos_locales.csv`, `informe/festivos_regionales.csv` | Portal de la Comunidad de Madrid (festivos regionales y locales) | **CC BY 4.0** (Comunidad de Madrid) |
| `informe/demografia_cnae09.csv`, `informe/demografia_cnae25.csv` | Portal de la Comunidad de Madrid (demografía empresarial) | **CC BY 4.0** (Comunidad de Madrid) |
| `informe/fuentes.json` | Fichas de las fuentes: título, licencia, fecha de última modificación y fecha de descarga | Metadatos; se conservan sin alterar |

## Condiciones del CRTM

La [licencia del CRTM](https://www.crtm.es/licencia-de-uso), consultada el 2026-11-11,
permite copiar, distribuir, modificar y combinar sus datos estáticos, también con fines
comerciales. Pide lo siguiente, y así se cumple:

- **Citar al CRTM e indicar si los datos son en bruto o explotados.** Son datos
  **explotados**: `salidas_paradas.parquet` no contiene horarios, sino el número de
  vehículos que paran en cada parada por hora y una estimación de personas por
  vehículo, calculada con la demanda diaria de cada red. `lineas_paradas.parquet`
  tampoco: solo cuántos vehículos de cada línea paran en cada parada en un día.
- **«Powered by CRTM» con enlace** en webs y aplicaciones: está en el pie de la
  aplicación y en la pestaña de fuentes.
- **Conservar las fechas de actualización:** están en `informe/fuentes.json` (entrada
  `crtm_paradas`), en `salidas_paradas_dias.json` y en `docs/fuentes.md`.
- **Mantener la información actualizada:** un flujo semanal de GitHub Actions
  (`.github/workflows/actualizar-datos.yml`) vuelve a descargar y procesar los datos y
  propone los cambios, que la autora revisa y acepta. Los de este repositorio se
  descargaron el 2026-11-10.
- **No sugerir que el CRTM patrocina o apoya el proyecto:** no lo hace.
- **Compartir los datos con el mismo tipo de licencia:** quien reutilice
  `salidas_paradas.parquet`, `lineas_paradas.parquet` o `referencia_movimiento.parquet`
  debe respetar estas mismas condiciones.

## Fechas de los datos

| Fuente | Versión de los datos | Descargado el |
|---|---|---|
| Portal de la Comunidad de Madrid | Última modificación de cada conjunto en `informe/fuentes.json` y en `docs/fuentes.md` | 2026-11-10 |
| Ayuntamiento de Madrid, censo de locales | Ficheros del 2026-11-09 | 2026-11-09 |
| INE, Atlas de renta | Año 2024; tablas actualizadas el 2026-10-15 | 2026-11-09 |
| INE, cartografía de secciones | Seccionado a 1 de enero de 2025 | 2026-11-09 |
| OpenStreetMap, hostelería | Datos a 2026-11-09 | 2026-11-09 |
| OpenStreetMap, universidades | Datos a 2026-11-10 | 2026-11-10 |
| CRTM | GTFS publicados entre el 2025-05-30 (Metro) y el 2026-11-05; demanda publicada el 2026-10-28 | 2026-11-10 |

Este proyecto no está respaldado ni patrocinado por ninguna de las entidades que
publican los datos.
