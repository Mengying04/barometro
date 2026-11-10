# 2026-11-10 · Perfil por horas

## Qué queríamos

Para cualquier punto de la Comunidad de Madrid, estimar **cuánta gente pasa cerca a
cada hora** (de 0 a 23), en un día laborable y en fin de semana, separada por tipo de
cliente: padres y niños, pacientes, trabajadores, deporte y eventos, viajeros y vecinos.

> **Todo el resultado es una estimación.** Sirve para comparar horas y tipos de cliente
> entre sí («a las 8 pasa mucha más gente que a las 11, y casi toda va al transporte»),
> no como un recuento real de personas.

## Qué se ha hecho

| Paso | Dónde | Resultado |
|---|---|---|
| Supuestos en un solo sitio | `src/supuestos.py` | Radio, pesos, horarios típicos, comidas, franjas y confianza; cada valor comentado y marcado como estimación |
| Alumnos por centro | `src/descargar_datos.py` + `src/procesar_perfil.py` | Nuevo conjunto del portal descargado y repartido entre los colegios → `datos/procesados/centros_educativos_alumnos.parquet` |
| Horario de los desfibriladores | `src/procesar_perfil.py` (`normalizar_horario`) | Texto libre convertido en horas de apertura → `datos/procesados/desfibriladores_horario.parquet` |
| Salidas por parada y hora | `src/procesar_perfil.py` + GTFS del CRTM | Laborable y sábado típicos → `datos/procesados/salidas_paradas.parquet` |
| Función del perfil | `src/perfil_horario.py` | `perfil_horario(lat, lon)` devuelve la tabla por horas, por franjas y la confianza |

Para regenerarlo todo:

```bash
python src/descargar_datos.py          # incluye ahora spacm_estadisticas_alumnos
python src/descargar_externas.py crtm  # incluye ahora el GTFS de Metro
python src/procesar.py
python src/procesar_perfil.py
python src/perfil_horario.py 40.4046 -3.6106
```

## Cómo funciona, explicado de forma sencilla

Dibujamos un **círculo de 300 m** (unos 4 minutos andando) alrededor del punto y
contamos qué hay dentro. Cada cosa aporta gente a ciertas horas, y **lo que está más
cerca pesa más**: algo en la puerta cuenta entero y algo en el borde del círculo cuenta
una cuarta parte (bajando en línea recta entre medias).

La unidad es el **«paso»**: una persona que pasa cerca en esa hora. Quien entra y sale
de un sitio cuenta dos veces (al llegar y al irse).

### Padres y niños (colegios)

- **Dónde están:** listado de centros educativos del portal (ubicación real).
- **Cuántos alumnos tienen:** el portal **no** publica alumnos por centro. Sí publica
  («Estadísticas de alumnos», `spacm_estadisticas_alumnos`) los alumnos de cada
  municipio —por distrito en Madrid capital—, por enseñanza (infantil, primaria, ESO,
  bachillerato, FP…) y por titularidad (pública, concertada, privada), curso 2024/2025.
  Ese total se **reparte a partes iguales** entre los centros del mismo territorio que
  imparten esa enseñanza con esa titularidad. Se asigna así el 99,9 % de los alumnos.
  Es una estimación: un colegio grande y uno pequeño del mismo barrio reciben lo mismo.
- **Centros que no salen en esa estadística** (escuelas de idiomas, música, adultos…):
  un número típico de alumnos por tipo de centro (supuesto).
- **Acompañantes:** en infantil y primaria se suma un adulto por cada niño, algo menos
  porque los hermanos comparten (0,6–0,9 según la etapa).
- **Horario:** entradas y salidas típicas (colegio de 9 a 14 o 16, instituto de 8:30 a
  15, FP de mañana y de tarde, escuela infantil escalonada…). Sin clase en fin de semana.

### Pacientes (centros sanitarios)

- **Dónde:** registro de centros sanitarios del portal.
- **Cuántos:** pacientes al día típicos según el tipo (centro de salud 500, hospital
  general 3.000, clínica dental o consulta 12–15…). Los servicios médicos dentro de
  empresas o residencias no cuentan (no reciben público de la calle).
- **Horario:** centro de salud de 8 a 21 con más gente por la mañana; consultas de 10 a
  14 y de 16 a 20; hospitales con consultas por la mañana y visitas por la tarde.

### Trabajadores, deporte y eventos (registro de desfibriladores)

En la Comunidad de Madrid es obligatorio tener desfibrilador en sitios con mucha gente
(centros de trabajo de más de 250 trabajadores, polideportivos con más de 500 usuarios
al día, recintos de más de 2.000 personas, grandes superficies, hoteles grandes…). El
registro del portal sirve, por tanto, como **mapa de sitios grandes**:

| Tipo en el registro | Tipo de cliente | Personas al día (supuesto) |
|---|---|---|
| Centro de trabajo de más de 250 trabajadores | Trabajadores | 400 |
| Administración pública | Trabajadores | 60 |
| Gran superficie comercial | Trabajadores (plantilla) | 80 |
| Hotel grande / residencia de mayores | Trabajadores (turnos) | 40 / 80 |
| Instalación deportiva de más de 500 usuarios | Deporte y eventos | 500 |
| Recinto de más de 2.000 personas | Deporte y eventos | 2.000 × prob. de evento |
| «Centro educativo» sin colegio del listado al lado | Padres y niños (universidades…) | 1.000 |

Se descartan los 2.202 desfibriladores que están **dentro de autobuses** (su dirección es
la del depósito) y los de tipo «Otros», transporte y aeropuertos. Los del mismo tipo a
menos de 50 m se cuentan como un solo sitio.

**Horario de acceso.** Es texto libre («24H», «DE 5 A 0.30», «L-V 8-20 / S-D 9-15»,
«HORARIO LECTIVO», «según partidos»…). Se ha normalizado así:

| Resultado | Filas | Qué se hace |
|---|---|---|
| Rango de horas leído del texto | 3.235 | Se usa: la llegada y la salida de la plantilla se colocan en la apertura y el cierre; para deporte y comercio se recorta el horario típico a las horas abiertas. Si dice que abre el fin de semana, se usa también. |
| Expresión («oficina», «comercial», «lectivo») | 180 | Se traduce a horas (8-18, 10-21, 8-17) |
| Eventos o partidos | 81 | Horario típico de eventos |
| 24 horas | 3.208 | El aparato está accesible desde la calle; no dice cuándo hay gente → horario típico del tipo |
| Vacío o no interpretable | 4.773 | Horario típico del tipo |
| Autobús | 2.202 | Se descarta |

### Viajeros (transporte público)

- De los **GTFS del Consorcio** (horarios oficiales) se cuenta cuántos vehículos paran en
  cada parada en cada hora, en un **laborable típico** y un **sábado típico** (se elige el
  día mediano de las próximas semanas para no caer en un festivo).
- Redes: Metro, Metro Ligero, Cercanías, EMT, interurbanos y urbanos de otros municipios.
- Cada paso de vehículo se multiplica por un número típico de personas que suben o bajan
  (Metro 40, Cercanías 60, Metro Ligero 10, EMT 5, interurbanos 4, urbanos 3;
  estimación de orden de magnitud a partir de los viajeros anuales de cada red).
- Detalles resueltos por el camino:
  - El GTFS de Metro es de mayo de 2025 (el último publicado) y su calendario terminó el
    27/05/2026: se usa un día de su vigencia y se supone que las frecuencias actuales son
    parecidas. Además, Metro define los trenes como «plantillas» que se repiten cada X
    minutos (`frequencies.txt`), así que hay que expandirlas. EMT también trae ese
    fichero, pero solo como descripción: sus viajes ya están todos listados.
  - Los GTFS de interurbanos y urbanos traen 7.480 viajes «de relleno» con todas las
    paradas a la 01:00:00. Daban un pico falso de madrugada; se han quitado.

### Vecinos

- Población 2024 del INE de cada **sección censal que toca el círculo**, en proporción a
  la superficie de la sección que queda dentro (se calcula por anillos de 50 m para dar
  más peso a lo más cercano). Se supone que la gente vive repartida por igual en su
  sección.
- Cada vecino pasa unas 2 veces al día por su calle en laborable y 1,6 en fin de semana
  (orden de magnitud de la Encuesta Domiciliaria de Movilidad del CRTM), repartidas por
  horas según costumbres generales (salir a trabajar, compras, comida, paseo, cena).

### Franjas y confianza

El resultado se agrupa en franjas: **primera hora de la mañana** (6–9 h), **media
mañana** (10–12), **mediodía** (13–15), **media tarde** (16–18), **tarde-noche**
(19–22) y **noche** (23–5).

| Tipo de cliente | Confianza | Por qué |
|---|---|---|
| Viajeros | **Alta** | Horarios reales del transporte |
| Padres y niños, pacientes, trabajadores, deporte y eventos | **Media** | Ubicación real, horario típico |
| Vecinos | **Orientativa** | Población repartida por superficie y costumbres generales |

## Prueba: entrada del campus de Vicálvaro (URJC), 40.4046, -3.6106

**Qué hay en 300 m:** 2 escuelas infantiles, 16 centros sanitarios con público (entre
ellos un centro de salud a ~195 m y muchas clínicas dentales y consultas), 3 sitios del
registro de desfibriladores (2 de administración pública con horario de tipo
universitario, L-V 8:30–21:30, y uno de «centro educativo»), 14 paradas de transporte
(Metro Vicálvaro de la línea 9 a ~150 m, varias paradas de EMT —cuatro con «Campus
Universitario» en el nombre— e interurbanos) y unos 2.350 vecinos (ponderados por distancia).

### Las tres horas con más movimiento (laborable)

| Hora | Personas que pasan (estimación) | Tipo principal | Reparto |
|---|---|---|---|
| **8:00–8:59** | ~1.780 | Viajeros | Viajeros 63 %, vecinos 23 %, padres y niños 11 % |
| **9:00–9:59** | ~1.590 | Viajeros | Viajeros 67 %, vecinos 20 %, padres y niños 7 % |
| **14:00–14:59** | ~1.430 | Viajeros | Viajeros 68 %, vecinos 22 %, padres y niños 6 % |

En **fin de semana** las horas fuertes son de **11:00 a 13:59** (~1.000 personas por
hora: dos tercios viajeros y un tercio vecinos).

### Por franjas (laborable, personas en toda la franja, estimación)

| Franja | Padres y niños | Pacientes | Trabajadores | Deporte y eventos | Viajeros | Vecinos | Total |
|---|---|---|---|---|---|---|---|
| Primera hora (6–9) | 354 | 111 | 40 | 0 | 3.658 | 1.014 | **5.178** |
| Media mañana (10–12) | 103 | 258 | 10 | 0 | 2.853 | 780 | 4.004 |
| Mediodía (13–15) | 252 | 124 | 53 | 0 | 2.882 | 832 | 4.144 |
| Media tarde (16–18) | 195 | 145 | 0 | 0 | 2.856 | 884 | 4.080 |
| Tarde-noche (19–22) | 112 | 50 | 51 | 0 | 3.387 | 1.040 | 4.641 |
| Noche (23–5) | 0 | 0 | 0 | 0 | 1.239 | 134 | 1.373 |

### Cómo leerlo

- Es un punto **de paso hacia el transporte**: el Metro y los autobuses explican dos
  tercios del movimiento a cualquier hora. La primera hora de la mañana es claramente la
  mejor franja (desayuno y café para llevar).
- Fuera de las 8–9 h el día es bastante **plano** (entre 1.300 y 1.430 personas por hora
  de 10 a 19 h), con un ligero repunte a la hora de comer (13–14 h) por la salida de las
  escuelas infantiles y la vuelta a casa de los vecinos.
- Los pacientes se concentran a media mañana (centro de salud) y los padres y niños a
  las 8–9 y a las 14–16 h.
- No hay deporte ni eventos dentro del radio: los dos polideportivos más cercanos están
  a ~430 y ~470 m.

### Limitaciones importantes de esta prueba

1. **La universidad casi no aparece.** El listado de centros educativos del portal es
   solo de enseñanzas *no universitarias* y no hay ningún conjunto abierto con la
   ubicación y los alumnos de los campus. Los estudiantes de la URJC solo se ven
   indirectamente (como viajeros del Metro y del autobús) y a través de los
   desfibriladores, que en este campus parecen estar registrados como «administración
   pública» (60 personas cada uno) y no como centro educativo. **Lo más probable es que
   el movimiento real a las 8–9 h y a las 14–15 h sea bastante mayor** de lo estimado.
   Si se consigue el número de estudiantes del campus (memoria de la universidad), se
   puede añadir como un sitio más.
2. **Los viajeros siguen la oferta, no la demanda.** Se cuenta cuántos trenes y
   autobuses pasan, multiplicado por un número fijo de personas por vehículo. En hora
   punta los vehículos van más llenos, así que el pico real de las 8–9 h será más
   marcado que el estimado.
3. Los recintos del registro de desfibriladores dicen el **tamaño mínimo** («más de
   2.000 personas»), no el real: un estadio grande queda muy por debajo.
4. Los horarios de Metro son de 2025.

## Próximos pasos posibles

- Añadir las universidades (ubicación de los campus y alumnos) desde una fuente abierta.
- Ajustar los viajeros por hora con datos de demanda (entradas por estación del CRTM o
  de Metro, si se publican).
- Usar el domingo además del sábado para el fin de semana.
- Cruzar las franjas con las horas de comida (`supuestos.COMIDAS`) para pasar de «gente
  que pasa» a «momentos de consumo» (desayuno, menú del día, merienda, cena).
