# 2026-11-10 · Perfil por horas: universidades y revisión de los viajeros

Continúa [el perfil por horas](2026-11-10-perfil-horario.md). Dos correcciones:
añadir los campus universitarios y revisar si los viajeros estaban sobrestimados.

> Todo sigue siendo una **estimación** («personas que pasan cerca por hora»), útil para
> comparar horas y tipos de cliente, no como recuento real.

## 1. Universidades

### Qué datos hay

- **Alumnos:** el portal de la Comunidad **sí** tiene alumnos por universidad, así que no
  ha hecho falta la estadística del Ministerio:
  - [1925489](https://datos.comunidad.madrid/dataset/1925489): estudiantes de Grado
    presenciales por universidad;
  - [1925502](https://datos.comunidad.madrid/dataset/1925502): estudiantes de máster
    presenciales por universidad.

  Se usa el último año publicado (curso 2025-26, provisional): **331.029 estudiantes**
  en 18 universidades presenciales. No hay datos por campus ni por facultad: el conjunto
  «por centro» (1925484) solo distingue centros propios y adscritos.
- **Ubicación:** recintos `amenity=university` de **OpenStreetMap** (164 elementos), con
  su contorno completo.

### Cómo se ha hecho

1. Cada elemento de OSM se asigna a una universidad por su nombre u operador («Rey Juan
   Carlos», «URJC», «Complutense», «UCM»…). Si no los tiene, se asigna a la universidad
   del recinto en el que está (por ejemplo, una facultad dentro de la Ciudad
   Universitaria). 78 elementos se asignan por nombre y 25 por recinto.
2. Se quitan 13 que no son centros de estudio: colegios mayores, residencias, un museo,
   unas oficinas y un instituto de secundaria mal etiquetado.
3. Los elementos de una misma universidad a menos de 300 m se unen en **un campus**.
4. Los estudiantes de cada universidad se reparten entre sus campus **en proporción a la
   raíz cuadrada de la superficie**, con un mínimo de 1 ha para los edificios sueltos.
   La raíz amortigua el tamaño: un campus enorme tiene mucho verde, deporte y
   aparcamiento, y no tiene alumnos en proporción a su superficie. *Estimación.*
5. Los centros universitarios que no son de ninguna universidad de la estadística
   (UNED, escuelas de negocios, universidades extranjeras…) cuentan como 300
   estudiantes al día. *Supuesto.*
6. En el perfil, los estudiantes se suponen **repartidos por igual en la superficie del
   campus** (como los vecinos en su sección censal), con el peso por distancia. Va al
   campus el **70 %** de los matriculados un día lectivo, con el horario típico de una
   universidad: turno de mañana y de tarde, con picos a las 8–9, 14–15 y 21 h. En fin
   de semana, nada. *Supuestos.*

Resultado: 98 campus, con 323.345 de los 331.029 estudiantes colocados. CUNEF y UDIT no
tienen recinto en OSM y quedan fuera.

### Nuevo tipo de cliente: «Universitarios»

Los estudiantes van en un tipo propio, **Universitarios**, y no en «Padres y niños».
Para un bar no es el mismo cliente (ni el mismo producto ni el mismo precio). Los
desfibriladores de «centro educativo» que no tienen ningún colegio cerca pasan también a
este tipo, y se descartan los que están junto a un campus (172), porque sus estudiantes
ya se cuentan en el campus.

## 2. Viajeros

### ¿Hay entradas por estación en abierto?

| Qué | ¿Hay datos abiertos? | Uso |
|---|---|---|
| Entradas por estación de **Metro** | **No.** El portal solo tiene ratios de toda la red («Ratios del Metro de Madrid») y el catálogo de datos.crtm.es no tiene nada por estación | — |
| Viajeros por parada de **autobús** | **No** | — |
| Viajeros **diarios por red** (Metro, EMT, concesiones por carretera, Cercanías) | **Sí**: Excel «Evolución demanda diaria» del Observatorio de la Demanda del CRTM, hasta el 25/10/2026 | Calibrar las personas por vehículo de cada red |
| Viajeros subidos y bajados por **estación de Cercanías** | **Sí**, para las 27 estaciones principales (portal, [1923861](https://datos.comunidad.madrid/dataset/1923861), año 2024) | Ajustar esas estaciones |

### Calibración de las personas por vehículo

Antes, las personas que suben o bajan por cada tren o autobús eran un supuesto de orden
de magnitud. Ahora se calculan con la demanda real de un laborable típico (mediana de
martes a jueves del 30/08 al 25/10/2026, sin festivos):

**personas por paso = 2 × viajeros del día ÷ trenes o autobuses que paran en todo el día**

(el 2 es porque cada viaje sube en una parada y baja en otra)

| Red | Antes (supuesto) | Ahora, laborable | Ahora, sábado |
|---|---|---|---|
| Metro | 40 | **44,3** | 37,4 |
| Cercanías | 60 | **72,8** (y ajuste por estación en 19) | 56,5 |
| EMT | 5 | **3,6** | 3,2 |
| Interurbanos y urbanos | 4 y 3 | **2,6** | 1,8 |
| Metro Ligero | 10 | 10 (sin datos de demanda) | 10 |

Así que **los autobuses sí estaban sobrestimados** (entre un 13 % y un 35 %), mientras
que en Metro y Cercanías el supuesto se quedaba corto. En las 19 estaciones de Cercanías
con dato propio se multiplica el valor de la red por la proporción entre esa estación y
la media; por ejemplo, Sol ×3,5 y Vicálvaro ×1,45. Getafe y Entrevías no se pudieron
emparejar por el nombre.

Limitación: dentro de una misma red, todas las paradas reciben la misma gente por
vehículo, porque no hay datos por estación de Metro ni de autobús.

### Nuevo supuesto: las paradas lejanas pesan menos

Como no hay entradas por estación de Metro ni de autobús, además de calibrar se ha
**reducido el peso de las paradas lejanas**. Quien sale del metro o baja del autobús
puede ir en cualquier dirección: por la puerta de la parada pasan todos, pero a 250 m
solo los que van justo hacia el local. Por eso las paradas pierden peso con la
distancia más deprisa que el resto de cosas:

| Distancia | Peso de los demás sitios (sin cambios) | Peso de una parada (antes) | Peso de una parada (ahora) |
|---|---|---|---|
| 0–50 m | 1–0,88 | 1–0,88 | **1** |
| 125 m | 0,69 | 0,69 | **0,5** |
| 200 m | 0,5 | 0,5 | **0,25** |
| 300 m | 0,25 | 0,25 | **0,1** |

Regla: peso 1 hasta 50 m y, a partir de ahí, la mitad cada 75 m. Las calles concentran
el paso, así que cae menos deprisa que si la gente se repartiera por igual en todas las
direcciones. *Estimación* (`supuestos.peso_parada`).

Además, en Metro y Metro Ligero la distancia se mide **al acceso más cercano** de la
estación (por donde sale la gente a la calle) y no al andén. En Vicálvaro, el acceso
está a 119 m y el andén a 154 m.

### Confianza separada en horario y cantidad

| Tipo de cliente | Horario | Cantidad |
|---|---|---|
| Viajeros | **alta** (horarios reales) | **media** (demanda real por red, repartida por igual) |
| Padres y niños | media | media (alumnos reales repartidos entre centros) |
| Universitarios | media | media (estudiantes reales repartidos entre campus) |
| Pacientes | media | orientativa (pacientes al día supuestos) |
| Trabajadores | media | orientativa (el registro solo da el tamaño mínimo) |
| Deporte y eventos | media | orientativa (usuarios o aforo mínimos) |
| Vecinos | orientativa | media (población real del INE) |

## 3. Prueba en el campus de Vicálvaro (URJC), 40.4046, -3.6106: antes y después

**Qué ha cambiado en el entorno:** ahora aparece el campus de Vicálvaro de la URJC
(7,3 ha, unos **5.430 estudiantes estimados** de los 44.600 de la universidad). Dentro
del radio y ponderados por distancia cuentan como ~2.730.

### Las tres horas con más movimiento (laborable)

| Hora | Antes | Después | Reparto después |
|---|---|---|---|
| **8:00–8:59** | 1.776 (viajeros 63 %) | **2.084** | Viajeros 41 %, universitarios 32 %, vecinos 20 % |
| **9:00–9:59** | 1.587 (viajeros 67 %) | **1.747** | Viajeros 47 %, universitarios 27 %, vecinos 18 % |
| **14:00–14:59** | 1.425 (viajeros 68 %) | **1.685** | Viajeros 44 %, universitarios 34 %, vecinos 19 % |

Las horas punta siguen siendo las mismas, pero **el pico es más marcado** y el cliente
cambia: antes eran casi solo viajeros, y ahora **un tercio son universitarios**. Entre
medias (10–12 h y 16–20 h) hay algo menos gente que antes (1.220–1.340 por hora frente
a 1.270–1.390), porque los viajeros bajan.

En **fin de semana** las horas fuertes siguen siendo de 11 a 14 h, pero con menos gente
(~790 por hora frente a ~1.025): ahí solo bajan los viajeros, porque no hay clase.

### Por franjas (laborable, personas en toda la franja)

| Franja | Total antes | Total después | Viajeros antes → después | Universitarios después |
|---|---|---|---|---|
| Primera hora (6–9) | 5.178 | **5.272** | 3.658 → 2.774 | 1.145 |
| Media mañana (10–12) | 4.004 | 3.842 | 2.853 → 2.201 | 573 |
| Mediodía (13–15) | 4.144 | **4.607** | 2.882 → 2.203 | 1.336 |
| Media tarde (16–18) | 4.080 | 3.891 | 2.856 → 2.176 | 573 |
| Tarde-noche (19–22) | 4.641 | 4.525 | 3.387 → 2.620 | 764 |
| Noche (23–5) | 1.373 | 1.159 | 1.239 → 1.024 | 0 |

**El mediodía pasa a ser la segunda franja**, casi igual que la primera hora: es la
salida del turno de mañana y la entrada del de tarde. Para un bar al lado del campus,
eso apunta a desayuno y café a primera hora y **menú del día o comida rápida a las
14 h**.

### De dónde sale cada cambio en los viajeros (primera hora, laborable)

| Paso | Viajeros 6–9 h | Cambio |
|---|---|---|
| Antes | 3.658 | — |
| + calibración con la demanda real (y accesos de Metro) | 3.722 | +2 %: Metro sube (44 en vez de 40, y su acceso está más cerca) y los autobuses bajan |
| + menos peso para las paradas lejanas | **2.774** | −25 % |

En este punto, la calibración por sí sola apenas cambia el total, porque se compensan
el Metro y los autobuses. Lo que más reduce los viajeros es el nuevo peso de las paradas
lejanas. El Metro de Vicálvaro sigue siendo la fuente principal: unas 17.600 personas
entran o salen al día y, a 119 m, pesa 0,53.

Los padres y niños bajan a primera hora (de 354 a 186) porque un desfibrilador de
«centro educativo» a 288 m, que antes se contaba como un centro sin datos de 1.000
usuarios, ahora queda dentro del campus y ya no se cuenta aparte.

## Limitaciones que quedan

- **Doble recuento parcial:** un estudiante que llega en metro cuenta como viajero y
  como universitario. No se corrige porque no hay datos de cómo llega cada uno; el total
  de las horas punta puede estar algo inflado.
- El reparto entre campus es una estimación: si la URJC publica sus alumnos por campus,
  se puede sustituir.
- Dentro de un campus muy grande (la Ciudad Universitaria tiene 391 ha) los estudiantes
  se reparten por toda la superficie, así que un punto concreto recibe poca gente. Es
  razonable de media, pero no distingue la puerta de una facultad de un descampado.
- Las personas por vehículo son las mismas en todas las paradas de una red (salvo las 19
  estaciones de Cercanías con dato propio).
- Metro sigue con horarios de 2025.

## Ficheros

- `src/supuestos.py`: universidades (reparto por raíz de la superficie, asistencia,
  centros sin datos), personas por vehículo (calibración y respaldo), `peso_parada` y
  la confianza doble.
- `src/procesar_perfil.py`: nuevo paso `universidades` →
  `datos/procesados/campus_universitarios.parquet`. El paso `gtfs` añade accesos y
  calibración (`pp_lab`, `pp_sab`, `origen_pp`). El paso `dea` excluye lo que ya es campus.
- `src/perfil_horario.py`: tipo «Universitarios», nuevo peso de paradas y confianza en
  dos columnas (`confianza_horario`, `confianza_cantidad`).
- Descargas nuevas: `src/descargar_datos.py` (1925489, 1925502, 1923861) y
  `src/descargar_externas.py` (`osm_uni`, y la demanda diaria dentro de `crtm`).
  Están anotadas en `docs/fuentes.md` con su licencia: CC BY 4.0 las del portal, ODbL
  la de OSM y la licencia del CRTM la de la demanda.
- Ninguna dirección estuvo bloqueada por el cortafuegos. Overpass rechaza peticiones con
  el agente de `curl` (error 406), pero funciona con el cliente de los scripts.
- `requirements.txt`: se añade `openpyxl` para leer el Excel del CRTM.
