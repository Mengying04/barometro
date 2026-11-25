# 2026-11-24 · Contraste de la «gente que pasa» con aforos reales de peatones

## Qué se pidió

Contrastar la gente que pasa del modelo (`perfil_horario()`, sin tipo de local) con
conteos reales de peatones, **sin cambiar ningún cálculo ni supuesto**. Lo que mejoraría el
modelo va aparte, como propuesta, sin aplicar.

Todo el análisis se reproduce con [`src/contraste_aforos.py`](../../src/contraste_aforos.py)
(`python src/contraste_aforos.py`; con `--fuentes` anota las fuentes en
`docs/fuentes.md`). No toca la aplicación ni el servidor MCP.

## 1. La fuente

**«Aforos de peatones y bicicletas»**, Ayuntamiento de Madrid, en datos.madrid.es
(`300321-0-aforos-peatones-bicicletas`). Se descarga por la API oficial del portal (CKAN,
`package_show`).

| Qué se comprobó | Resultado |
|---|---|
| Licencia y condiciones | **CC BY 4.0**. Hay que citar «Fuente: Ayuntamiento de Madrid», igual que el censo de locales que ya usa el proyecto. Permite reutilizar, también con fines comerciales |
| Último periodo con datos | Ficha modificada el 2026-07-24, con cobertura del **2019-09-01 al 2024-06-30**. La ficha dice que se actualiza cada trimestre, pero no hay nada posterior a junio de 2024. El último trimestre publicado es provisional |
| Ubicación de cada estación | **Sí**: latitud y longitud en cada fila. Vienen mal formateadas, con puntos de miles («40.417.386» por 40,417386); el script las corrige |
| Qué mide | Peatones por estación y hora. La ficha dice «mediciones en determinadas calles en puntos concretos con periodicidad diaria cada hora». La columna `observaciones_direccion` dice en muchas estaciones si cuenta **una acera** (pares o impares) o una **calle peatonal**; en las estaciones nuevas no lo dice. El PDF de estructura no dice si la hora es el principio o el final del intervalo (ver «Limitaciones») |
| Cambio de método | Entre **agosto de 2021 y septiembre de 2022** se cambiaron los detectores. La ficha **no recomienda comparar** datos de antes y después |

Hay también un error en la estructura publicada: dice que `peatones` es el «número de
bicicletas registradas»; por el nombre de la columna y por el fichero, son peatones. El CSV
de 2023 trae los textos en UTF-8 mal leído («MartÃ­n»); el script lo corrige.

Para quitar los festivos se usa el **«Calendario laboral»** del Ayuntamiento
(`300082-0-calendario_laboral`, CC BY 4.0), que trae los festivos de la ciudad de 2013 a
2027. Así no se escribe ninguna fecha a mano.

Las dos fuentes están anotadas en `docs/fuentes.md`, en un bloque propio
(`contraste`), fuera de los que lee la aplicación. La tabla de fuentes de la aplicación no
cambia (sigue con 16 conjuntos del portal, 6 fuentes externas y 2 servicios).

## 2. Los datos

**Año: 2023.** Es el último año completo, y es todo posterior al cambio de detectores
(septiembre de 2022). De 2024 solo hay hasta junio, y el último trimestre es provisional.
No se mezclan años.

- **30 estaciones** en 29 puntos: las dos de Gran Vía (una por acera) tienen coordenadas
  distintas, y las dos de Fuencarral comparten las mismas coordenadas publicadas, así que el
  modelo da lo mismo para las dos. 18 tienen todo 2023. **Nueve empezaron
  entre septiembre y octubre de 2023**, así que solo tienen días de otoño (entre 22 y 41
  laborables válidos). Dos (PEA01 y PEA20) empiezan en julio y una (PEA15) se corta en
  octubre.
- **Tipos de día:** laborable = martes, miércoles y jueves no festivos (calendario
  oficial); sábados no festivos; domingos.
- **Media por hora:** la media de los días válidos de cada tipo, en cada estación. Se exigen
  8 días válidos como mínimo; las 30 los tienen.
- **Días quitados** (cada día de cada estación se mira por separado):
  - **huecos:** falta alguna de las 24 horas, o está vacía o repetida;
  - **ceros sospechosos:** un cero entre las 8 y las 21 en una hora en la que esa estación
    suele contar 20 peatones o más;
  - **corte de datos:** el día cuenta menos del 20 % de lo habitual en esa estación y tipo
    de día.

  Se quita el 11 % de los días-estación (tabla abajo). Casi todo son ceros sospechosos:
  horas sueltas a cero en pleno día, propias de un detector parado.

Las estaciones se nombran por su código (PEA01-1 = `PERM_PEA01_PM01`) y por su número de
distrito de Madrid (calculado con las secciones censales del proyecto), **sin nombres de
calle**: varias calles llevan nombres de personas.

## 3. El modelo

En la posición publicada de cada estación se calcula `perfil_horario(lat, lon)`, tal cual
y sin tipo de local: la columna `total` (gente que pasa en 300 m) para laborable, sábado
(`fin_de_semana`) y domingo. Ningún supuesto se ha cambiado.

## 4. Resultados

### Días quitados (2023)

| Tipo de día | Días-estación | Huecos | Ceros sospechosos | Corte de datos | Válidos |
|---|---|---|---|---|---|
| laborable | 3235 | 94 | 258 | 15 | 2868 |
| sabado | 1136 | 37 | 114 | 1 | 984 |
| domingo | 1159 | 59 | 105 | 3 | 992 |

### a) Forma del día (correlación hora a hora y hora punta)

| Estación | Distrito | Punto | Días lab. | r lab. | r lab. 7–22 h | Punta conteo / modelo (lab.) | r sáb. | Punta sáb. | r dom. | Punta dom. |
|---|---|---|---|---|---|---|---|---|---|---|
| PEA01-1 | 01 | calle peatonal | 67 | 0,72 | -0,16 | 13 / 8 h ✗ | 0,84 | 13 / 19 h ✗ | 0,87 | 14 / 12 h ✗ |
| PEA02-1 | 01 | calle peatonal | 122 | 0,67 | 0,03 | 20 / 8 h ✗ | 0,79 | 19 / 12 h ✗ | 0,76 | 19 / 12 h ✗ |
| PEA03-1 | 01 | acera pares | 109 | 0,67 | -0,29 | 20 / 8 h ✗ | 0,81 | 20 / 19 h ✓ | 0,75 | 20 / 12 h ✗ |
| PEA04-1 | 01 | acera pares | 148 | 0,60 | -0,37 | 20 / 8 h ✗ | 0,79 | 21 / 19 h ✗ | 0,76 | 20 / 12 h ✗ |
| PEA06-1 | 01 | acera impares | 146 | 0,71 | -0,23 | 19 / 8 h ✗ | 0,93 | 20 / 19 h ✓ | 0,93 | 12 / 12 h ✓ |
| PEA07-1 | 01 | acera impares | 148 | 0,70 | -0,41 | 14 / 8 h ✗ | 0,81 | 15 / 18 h ✗ | 0,79 | 15 / 12 h ✗ |
| PEA08-1 | 01 | acera pares | 144 | 0,66 | -0,14 | 19 / 8 h ✗ | 0,79 | 19 / 19 h ✓ | 0,78 | 19 / 13 h ✗ |
| PEA08-2 | 01 | acera impares | 145 | 0,67 | -0,17 | 19 / 8 h ✗ | 0,82 | 20 / 19 h ✓ | 0,81 | 17 / 13 h ✗ |
| PEA09-1 | 04 | acera pares | 98 | 0,67 | 0,00 | 19 / 8 h ✗ | 0,77 | 21 / 18 h ✗ | 0,64 | 14 / 19 h ✗ |
| PEA10-1 | 01 | acera pares | 140 | 0,87 | 0,30 | 14 / 8 h ✗ | 0,83 | 18 / 19 h ✓ | 0,77 | 19 / 12 h ✗ |
| PEA11-1 | 01 | calle peatonal | 135 | 0,70 | -0,20 | 19 / 8 h ✗ | 0,72 | 15 / 19 h ✗ | 0,74 | 15 / 12 h ✗ |
| PEA12-1 | 10 | calle peatonal | 140 | 0,71 | -0,03 | 20 / 8 h ✗ | 0,96 | 13 / 12 h ✓ | 0,98 | 13 / 12 h ✓ |
| PEA13-1 | 09 | sin dato | 121 | 0,72 | -0,22 | 19 / 8 h ✗ | 0,72 | 20 / 18 h ✗ | 0,65 | 20 / 12 h ✗ |
| PEA14-1 | 07 | acera pares | 129 | 0,77 | -0,08 | 19 / 8 h ✗ | 0,87 | 19 / 12 h ✗ | 0,78 | 20 / 12 h ✗ |
| PEA15-1 | 01 | acera impares | 119 | 0,71 | -0,18 | 19 / 8 h ✗ | 0,93 | 12 / 12 h ✓ | 0,96 | 12 / 12 h ✓ |
| PEA16-1 | 01 | acera impares | 85 | 0,67 | -0,18 | 19 / 8 h ✗ | 0,88 | 19 / 18 h ✓ | 0,89 | 17 / 12 h ✗ |
| PEA17-1 | 01 | acera pares | 107 | 0,69 | -0,12 | 18 / 8 h ✗ | 0,95 | 18 / 12 h ✗ | 0,97 | 11 / 12 h ✓ |
| PEA18-1 | 01 | acera pares | 142 | 0,76 | 0,00 | 12 / 8 h ✗ | 0,82 | 19 / 18 h ✓ | 0,76 | 13 / 19 h ✗ |
| PEA19-1 | 01 | acera pares | 141 | 0,67 | 0,05 | 13 / 8 h ✗ | 0,82 | 14 / 12 h ✗ | 0,87 | 14 / 12 h ✗ |
| PEA20-1 | 04 | sin dato | 59 | 0,69 | 0,03 | 19 / 8 h ✗ | 0,83 | 20 / 19 h ✓ | 0,83 | 18 / 13 h ✗ |
| PEA21-1 | 08 | sin dato | 38 | 0,64 | 0,09 | 11 / 8 h ✗ | 0,79 | 12 / 11 h ✓ | 0,86 | 12 / 12 h ✓ |
| PEA21-2 | 08 | sin dato | 31 | 0,66 | 0,16 | 12 / 8 h ✗ | 0,76 | 11 / 11 h ✓ | 0,76 | 12 / 12 h ✓ |
| PEA22-1 | 09 | sin dato | 41 | 0,82 | 0,44 | 10 / 8 h ✗ | 0,87 | 12 / 12 h ✓ | 0,84 | 12 / 12 h ✓ |
| PEA23-1 | 10 | sin dato | 25 | 0,81 | 0,12 | 13 / 8 h ✗ | 0,94 | 12 / 11 h ✓ | 0,89 | 13 / 12 h ✓ |
| PEA24-1 | 11 | sin dato | 22 | 0,80 | 0,40 | 18 / 8 h ✗ | 0,93 | 13 / 12 h ✓ | 0,94 | 11 / 12 h ✓ |
| PEA25-1 | 12 | sin dato | 34 | 0,86 | 0,42 | 18 / 8 h ✗ | 0,83 | 18 / 11 h ✗ | 0,83 | 13 / 13 h ✓ |
| PEA26-1 | 13 | sin dato | 35 | 0,87 | 0,39 | 18 / 8 h ✗ | 0,91 | 18 / 19 h ✓ | 0,91 | 18 / 12 h ✗ |
| PEA27-1 | 15 | sin dato | 125 | 0,60 | -0,22 | 20 / 8 h ✗ | 0,85 | 20 / 12 h ✗ | 0,80 | 20 / 13 h ✗ |
| PEA28-1 | 20 | sin dato | 37 | 0,77 | 0,31 | 11 / 8 h ✗ | 0,69 | 11 / 11 h ✓ | 0,67 | 11 / 12 h ✓ |
| PEA29-1 | 21 | sin dato | 35 | 0,86 | 0,44 | 18 / 8 h ✗ | 0,90 | 18 / 12 h ✗ | 0,85 | 16 / 12 h ✗ |

**Resumen de la forma del día:**

- Laborable: 30 estaciones; r mediana 0,70 (de 0,60 a 0,87); r ≥ 0,7 en 16; solo de 7 a 22 h, r mediana -0,01; hora punta a ±1 h en 0 de 30.
- Sábado: 30 estaciones; r mediana 0,83 (de 0,69 a 0,96); r ≥ 0,7 en 29; solo de 7 a 22 h, r mediana 0,79; hora punta a ±1 h en 17 de 30.
- Domingo: 30 estaciones; r mediana 0,82 (de 0,64 a 0,98); r ≥ 0,7 en 27; solo de 7 a 22 h, r mediana 0,79; hora punta a ±1 h en 11 de 30.

### b) Orden entre estaciones (total del laborable)

Spearman entre el total del conteo y el del modelo: **0,39** (30 estaciones). Mismo tercio (alto, medio, bajo): **13 de 30**.

| Estación | Peatones/día (conteo) | Gente que pasa/día (modelo, 300 m) | Tercio conteo | Tercio modelo |
|---|---|---|---|---|
| PEA08-2 | 69.039 | 53.369 | alto | alto |
| PEA08-1 | 55.161 | 53.162 | alto | alto |
| PEA02-1 | 36.796 | 25.857 | alto | medio |
| PEA01-1 | 27.866 | 33.584 | alto | medio |
| PEA24-1 | 20.817 | 20.795 | alto | bajo |
| PEA16-1 | 20.812 | 23.955 | alto | medio |
| PEA07-1 | 15.623 | 46.254 | alto | alto |
| PEA14-1 | 15.476 | 65.453 | alto | alto |
| PEA18-1 | 14.768 | 36.861 | alto | medio |
| PEA19-1 | 14.694 | 6.419 | alto | bajo |
| PEA25-1 | 13.461 | 17.257 | medio | bajo |
| PEA13-1 | 13.268 | 60.273 | medio | alto |
| PEA15-1 | 11.768 | 29.451 | medio | medio |
| PEA04-1 | 11.034 | 31.875 | medio | medio |
| PEA26-1 | 10.505 | 40.129 | medio | alto |
| PEA06-1 | 8.834 | 32.325 | medio | medio |
| PEA11-1 | 8.276 | 18.719 | medio | bajo |
| PEA10-1 | 8.007 | 54.012 | medio | alto |
| PEA03-1 | 7.584 | 71.026 | medio | alto |
| PEA20-1 | 7.039 | 56.974 | medio | alto |
| PEA09-1 | 6.986 | 27.521 | bajo | medio |
| PEA28-1 | 5.724 | 13.060 | bajo | bajo |
| PEA17-1 | 5.324 | 43.174 | bajo | alto |
| PEA27-1 | 4.966 | 34.503 | bajo | medio |
| PEA22-1 | 4.380 | 5.267 | bajo | bajo |
| PEA23-1 | 2.731 | 28.207 | bajo | medio |
| PEA12-1 | 2.554 | 13.532 | bajo | bajo |
| PEA21-1 | 1.611 | 10.079 | bajo | bajo |
| PEA29-1 | 687 | 4.999 | bajo | bajo |
| PEA21-2 | 579 | 10.079 | bajo | bajo |

Las cifras no se comparan entre sí como acierto: la estación cuenta un punto de una calle (a menudo una sola acera) y el modelo, toda la gente que pasa en un círculo de 300 m.

### c) Fin de semana (cociente frente al laborable)

| Estación | Sáb./lab. conteo | Sáb./lab. modelo | Dom./lab. conteo | Dom./lab. modelo |
|---|---|---|---|---|
| PEA01-1 | 1,06 | 0,73 | 1,04 | 0,57 |
| PEA02-1 | 1,23 | 0,65 | 1,11 | 0,53 |
| PEA03-1 | 1,28 | 0,65 | 1,16 | 0,49 |
| PEA04-1 | 1,20 | 0,69 | 1,17 | 0,55 |
| PEA06-1 | 1,18 | 0,63 | 1,11 | 0,50 |
| PEA07-1 | 1,23 | 0,70 | 1,25 | 0,54 |
| PEA08-1 | 1,64 | 0,68 | 1,24 | 0,52 |
| PEA08-2 | 1,41 | 0,68 | 1,24 | 0,53 |
| PEA09-1 | 1,23 | 0,67 | 1,21 | 0,48 |
| PEA10-1 | 0,89 | 0,58 | 0,82 | 0,44 |
| PEA11-1 | 1,35 | 0,72 | 1,38 | 0,57 |
| PEA12-1 | 1,49 | 0,66 | 1,65 | 0,54 |
| PEA13-1 | 1,01 | 0,61 | 0,98 | 0,47 |
| PEA14-1 | 0,87 | 0,57 | 0,77 | 0,44 |
| PEA15-1 | 1,47 | 0,65 | 1,47 | 0,52 |
| PEA16-1 | 1,29 | 0,64 | 1,29 | 0,48 |
| PEA17-1 | 0,99 | 0,53 | 0,89 | 0,42 |
| PEA18-1 | 1,39 | 0,66 | 1,22 | 0,49 |
| PEA19-1 | 1,53 | 0,70 | 1,40 | 0,58 |
| PEA20-1 | 1,64 | 0,66 | 1,20 | 0,50 |
| PEA21-1 | 0,89 | 0,59 | 0,67 | 0,50 |
| PEA21-2 | 0,89 | 0,59 | 0,66 | 0,50 |
| PEA22-1 | 1,00 | 0,65 | 0,68 | 0,54 |
| PEA23-1 | 1,11 | 0,66 | 0,95 | 0,54 |
| PEA24-1 | 1,10 | 0,69 | 0,80 | 0,59 |
| PEA25-1 | 1,00 | 0,69 | 0,84 | 0,59 |
| PEA26-1 | 1,03 | 0,67 | 0,82 | 0,52 |
| PEA27-1 | 0,92 | 0,66 | 0,86 | 0,54 |
| PEA28-1 | 0,99 | 0,64 | 0,68 | 0,55 |
| PEA29-1 | 1,13 | 0,71 | 0,86 | 0,60 |

- Sábado/laborable: mediana 1,16 en el conteo y 0,66 en el modelo; el modelo da un cociente menor que el conteo en 30 de 30 estaciones.

- Domingo/laborable: mediana 1,07 en el conteo y 0,53 en el modelo; el modelo da un cociente menor que el conteo en 30 de 30 estaciones.


### Lectura

**a) Forma del día.**

- **Laborable: no coincide.** La correlación de 24 horas parece buena (mediana 0,70), pero
  se debe sobre todo a que de noche hay poca gente en los dos. **Solo de 7 a 22 h, la
  mediana es −0,01**: durante el día no hay relación.
- **La hora punta del laborable no coincide en ninguna estación (0 de 30).** El modelo pone
  la punta a las **8 en las 30**. Las aceras la tienen por la tarde (de 18 a 20 h, 20
  estaciones) o entre media mañana y mediodía (de 10 a 14 h, 10 estaciones).
- **Perfil medio del laborable** (porcentaje del día en cada hora, media de las 30
  estaciones):

  | Hora | 7 | 8 | 9 | 12 | 14 | 17 | 18 | 19 | 20 |
  |---|---|---|---|---|---|---|---|---|---|
  | Conteo | 2,1 % | 3,1 % | 4,2 % | 6,9 % | 6,2 % | 7,0 % | 8,0 % | 8,1 % | 7,2 % |
  | Modelo | 5,2 % | **9,0 %** | 7,0 % | 5,1 % | 6,9 % | 6,1 % | 6,5 % | 6,5 % | 5,6 % |

  El modelo concentra a las 8 casi el triple que el conteo. Esa punta del modelo son, en la
  media de las estaciones, viajeros (51 %), vecinos (25 %) y padres con niños (14 %): la
  gente que sale del transporte y entra a trabajar o a los colegios. El conteo, en cambio,
  sube durante el día y es máximo por la tarde.
- **Sábado y domingo: coinciden bastante mejor.** La r de 24 horas tiene una mediana de 0,83
  y 0,82; solo de 7 a 22 h, de 0,79 los dos días. La hora punta coincide (±1 h) en 17 de 30
  sábados y en 11 de 30 domingos.

**b) Orden entre estaciones.** Spearman de **0,39** (30 estaciones); el mismo tercio en **13
de 30**. El modelo acierta los extremos (las dos de Gran Vía, arriba; las de barrio de la
periferia, abajo), pero pone arriba varios puntos que en la acera cuentan poco, como PEA03,
PEA10, PEA17 y PEA20. Los cuatro tienen accesos de Metro (y PEA17, también Cercanías) en el
círculo de 300 m, y el modelo cuenta a todos sus viajeros, aunque no pasen por esa acera.
Es una **hipótesis, no algo demostrado**: las dos estaciones de Gran Vía también tienen
Metro en el círculo, y ahí la acera sí cuenta mucho.

**c) Fin de semana.** **El modelo da menos gente el fin de semana que el conteo en las 30
estaciones.** Sábado/laborable: mediana de 1,16 en el conteo y 0,66 en el modelo.
Domingo/laborable: 1,07 frente a 0,53. En el centro, el sábado pasa más gente que en
laborable (hasta 1,6 veces en Gran Vía); en los barrios, más o menos igual. El modelo, en
cambio, baja siempre a la mitad o dos tercios.

**Cifras absolutas.** **No se comparan como acierto.** La estación cuenta un punto de una
calle, a menudo una sola acera, y el modelo, toda la gente que pasa en un círculo de 300 m.
Que el modelo dé más gente que la estación es lo esperable; la tabla b) se usa solo para el
orden.

## 5. Limitaciones

- **Solo Madrid capital** y sobre todo el distrito Centro: 15 de las 30 estaciones están en
  el distrito 01. No dice nada de los municipios de fuera, ni de zonas universitarias,
  hospitalarias o de colegios (Vicálvaro, Fuenlabrada o Griñón).
- **Años distintos:** conteos de 2023 y modelo con el transporte de noviembre de 2026 y
  población de 2024.
- **Punto frente a círculo:** una acera frente a 300 m a la redonda. La forma del día y el
  fin de semana se pueden comparar; las cifras, no.
- **Estaciones nuevas, solo otoño:** las nueve que empezaron en septiembre u octubre de 2023
  no tienen verano ni primavera.
- **Convención de la hora:** el portal no dice si «8:00» son los peatones de 8:00 a 8:59 o de
  7:00 a 7:59. Se ha tomado lo primero. Con lo segundo, la r de 24 horas del laborable sube
  de 0,70 a 0,78, pero la punta del conteo seguiría siendo por la tarde: la conclusión no
  cambia.
- **Datos de un detector:** los conteos también tienen errores. Se han quitado los días con
  huecos o ceros sospechosos, pero no se puede saber si un detector cuenta de menos.

## 6. Propuestas (sin aplicar)

Nada de esto se ha cambiado. Son ideas para decidir más adelante, y en todos los casos
habría que **reservar parte de las estaciones** para comprobar después, o el contraste
dejaría de ser independiente.

1. **Pasear, comprar y ocio.** El modelo no tiene a la gente que va andando a comprar, de
   paseo o a tomar algo, que es la que llena las aceras por la tarde y el fin de semana. Se
   podría añadir un tipo de cliente «paseo y compras», con su horario y más peso el fin de
   semana, a partir del comercio de la zona (por ejemplo, el censo de locales del
   Ayuntamiento, que ya se usa).
2. **Viajeros que no pasan por todas las aceras.** Hoy todos los viajeros de una estación
   del círculo cuentan como gente que pasa. Se podría repartir según la distancia a la
   parada, como ya se hace con la población.
3. **Punta de las 8 en laborable.** Las aceras no la tienen. La mañana del modelo pesa
   demasiado: los viajeros de entrada y los padres con niños se concentran en una sola
   hora. Coincide con lo que se vio con el bar de validación 1 (`docs/validacion.md`).
4. **Fin de semana.** Los cocientes sábado/laborable y domingo/laborable de estas estaciones
   (1,16 y 1,07 de mediana) son una referencia real para revisar el peso del fin de semana,
   al menos en Madrid capital.

## 7. Textos propuestos (sin aplicar)

**Para `docs/validacion.md`**, una sección nueva después de «Notas sobre el bar de
validación 1»:

> ## Contraste con aforos de peatones (Madrid capital, 2023)
>
> Además de los hosteleros, la gente que pasa del modelo se ha contrastado con los conteos
> por hora de las 30 estaciones permanentes de peatones del Ayuntamiento de Madrid
> (`src/contraste_aforos.py`; detalle en
> `docs/registro/2026-11-24-contraste-aforos-peatones.md`). Sin cambiar ningún supuesto:
>
> - **Laborable: no coincide la forma del día.** El modelo pone la punta a las 8 en todas
>   las estaciones; las aceras la tienen por la tarde o a mediodía. Durante el día (7 a 22 h)
>   la correlación es nula. Es lo mismo que se vio con el bar de validación 1.
> - **Fin de semana: la forma coincide** (correlación de 0,8 de mediana), **pero el modelo da
>   la mitad de gente que en laborable, y las aceras, más.**
> - **Orden entre zonas: regular** (Spearman 0,39). El modelo acierta los extremos, pero pone
>   arriba varios puntos que en la acera cuentan poco.
>
> Las cifras absolutas no se comparan: la estación cuenta una acera y el modelo, un círculo
> de 300 m. Solo hay estaciones en Madrid capital, la mitad en el distrito Centro.

**Para la sección «Rigor: qué se ha comprobado» del README**, un punto nuevo:

> - **Conteos reales de peatones.** La gente que pasa se ha contrastado con las 30
>   estaciones permanentes de peatones del Ayuntamiento de Madrid (2023), sin ajustar nada.
>   El fin de semana, la forma del día coincide. En laborable, no: el modelo pone la punta
>   a las 8 y las aceras la tienen por la tarde. Además, el modelo da menos gente el fin de
>   semana que en laborable, y las aceras, más. Ver
>   [`docs/validacion.md`](docs/validacion.md) y
>   [`src/contraste_aforos.py`](src/contraste_aforos.py).

## 8. Comprobaciones

| Prueba | Resultado |
|---|---|
| `src/comprobar_datos.py` | 38 de 38 bien |
| `mcp/probar_cliente.py` | Todo correcto |
| Huellas de `src/resumen_ejemplos.py` | Iguales a las de referencia con la misma fecha (2026-11-23). Con la fecha de hoy cambian, como cada día: los festivos «próximos» se cuentan desde hoy. Ningún cálculo ha cambiado |
| Tabla de fuentes de la aplicación (`src/fuentes.py`) | Igual: 16 conjuntos del portal, 6 externas y 2 servicios; el bloque nuevo no se lee |

## Archivos

- `src/contraste_aforos.py` (nuevo).
- `docs/fuentes.md`: bloque `contraste` con las dos fuentes.
- Este registro.

## 9. Lo que se ha aplicado (decisión de la autora)

La autora aprobó los textos propuestos, con estos añadidos. **Ningún cálculo, supuesto ni
confianza cambia.**

- **`docs/validacion.md`:** sección nueva «Contraste con aforos de peatones (Madrid capital,
  2023)», con el texto propuesto y un párrafo final, «Qué significa para la aplicación»:
  - la hora punta de paso en laborable es poco fiable, sobre todo en calles comerciales y
    de paseo;
  - la mitad de las estaciones están en el distrito Centro, y ninguna en una zona como los
    tres ejemplos;
  - «¿Cuándo tendrías más clientes?» suma a los vecinos que van a propósito (en Vicálvaro y
    Fuenlabrada, con «bar de barrio», sale por la tarde), pero hereda el sesgo de la mañana.
- **README:**
  - en «Rigor», el punto «Conteos reales de peatones»;
  - en «Limitaciones conocidas», la línea del laborable y del fin de semana;
  - en «Siguientes pasos», añadir a la gente que va de paseo y de compras y repartir a los
    viajeros según la distancia a la parada, ajustando con la mitad de las estaciones y
    comprobando con la otra mitad.
- **Informe completo, sección «A qué hora»:** una nota de aviso, debajo del porqué y antes
  del detalle: «Contraste con conteos reales (Madrid capital, 2023): en día laborable, las
  aceras tienen más gente por la tarde de lo que dice este modelo; la hora punta de la
  mañana puede estar sobrevalorada. Compruébalo contando en persona.» Sale siempre en esa
  sección, con tipo de local y sin él, y nunca en el Resumen. Es un texto fijo
  (`AVISO_AFOROS` en `app/app.py`) y no cambia ninguna cifra ni ninguna confianza.
- **`src/contraste_aforos.py`:** la fecha de descarga que anota en `docs/fuentes.md` usa
  ahora `fecha.hoy()` (hora de Madrid), como el resto del proyecto.

**Comprobaciones:**

| Prueba | Resultado |
|---|---|
| `src/comprobar_datos.py` | 38 de 38 bien |
| `mcp/probar_cliente.py` | Todo correcto |
| Huellas de `src/resumen_ejemplos.py`, con la fecha de referencia (2026-11-23) | Iguales en los tres puntos |
| AppTest: portada, planes, tres ejemplos (Resumen e Informe, tres días), comparación y PDF | 17 de 17 bien |
| AppTest de la nota: tres ejemplos, sin tipo y con «bar de barrio» | Sale una vez en el Informe completo y ninguna en el Resumen, sin excepciones |
| Chromium (1.440 y 390 px) | La nota se ve bajo el porqué de «A qué hora», sin errores de JavaScript |

Rehechas las 25 capturas del Informe de `docs/capturas/` (sin fallos ni errores de
JavaScript).
