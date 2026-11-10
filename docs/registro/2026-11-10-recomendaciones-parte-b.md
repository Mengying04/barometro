# 2026-11-10 · Recomendaciones (parte B): a quién, a qué hora, qué y a qué precio

## Qué se ha hecho

`src/recomendaciones.py` tiene la función `recomendar(lat, lon)`. Combina el perfil por
horas (`perfil_horario()`) y el informe del local (`informe_local()`) y responde a cuatro
preguntas para un bar o restaurante en el punto: **a quién vender, a qué hora, qué vender
y a qué precio**. Añade además riesgos y avisos, y una lista de **qué comprobar en
persona**.

```bash
python src/recomendaciones.py 40.4046 -3.6106          # Markdown
python src/recomendaciones.py 40.4046 -3.6106 --json   # JSON
```

Reglas que cumple cada recomendación:

- lleva su **porqué** (los datos concretos), una **confianza** (alta, media o baja) y su
  **base** (dato o estimación);
- la confianza sale de la de sus datos: es la del dato más débil entre los que pesan al
  menos un 25 % (un tipo de cliente minoritario no la rebaja);
- usa lenguaje de orientación («conviene», «posible hueco», «a comprobar»), nunca de
  garantía;
- nunca nombra locales: los datos procesados no guardan nombres ni rótulos.

Todos los valores nuevos están en `src/supuestos.py`, sección **«RECOMENDACIONES»**, cada
uno con su comentario.

## Cambios en la parte A

### 1. Locales que sirven comidas

En el censo del Ayuntamiento, el «bar restaurante» contaba como bar, así que el recuento
de «restaurantes» a secas se quedaba muy corto (en Vicálvaro salían 0). El bloque de
competencia trae ahora aparte los **locales que sirven comidas**, y los huecos se buscan
siempre con ese recuento, nunca con el de «restaurantes».

| Fuente | Criterio |
|---|---|
| Censo de Madrid | Epígrafes restaurante (561001), autoservicio (561003), **bar restaurante (561004)** y **bar con cocina (561005)**. No entran la cafetería (dudosa: se cuenta aparte), el bar sin cocina ni la comida rápida (que tiene su propio tipo). |
| OpenStreetMap | Todos los `restaurant`, más los `bar`, `pub` y `cafe` con `food=yes` o con un tipo de cocina de comida (no solo café, helado, churros o bebida). La etiqueta `food` casi no se usa (22 locales en toda la Comunidad), así que es una **aproximación**: muchos bares de OSM que dan comidas no lo indican. |

El bloque compara además cada tipo de local con la media del municipio (bares,
restaurantes, cafeterías, comida rápida y locales que sirven comidas).

Para Vicálvaro: 13 locales sirven comidas, frente a 0 «restaurantes» y frente a 24,9 de
media en un punto habitado de Madrid (×0,52).

### 2. Gama ajustada a la clientela

La gama ya no sale solo de la renta de los vecinos. El informe da **las dos gamas**, ambas
marcadas como estimación:

- **por la renta de los vecinos**, como antes;
- **ajustada a la clientela**: media de las gamas de cada tipo de cliente, en una escala
  de 1 (económica) a 3 (alta), ponderada por el peso de cada tipo en el perfil por horas.

| Tipo de cliente | Gama supuesta | Por qué |
|---|---|---|
| Vecinos | la de la zona | su renta es la de la zona (dato del INE) |
| Padres y niños | la de la zona | los colegios escolarizan sobre todo a niños del barrio |
| Pacientes | la de la zona | el centro de salud atiende a su zona básica de salud |
| Universitarios | económica (1) | presupuesto de estudiante: buscan precio |
| Viajeros | económica-media (1,5) | de paso: compra rápida, de poco importe y sensible al precio |
| Trabajadores | media (2) | menú del día a precio de mercado, a veces con ticket de comida |
| Deporte y eventos | media (2) | gasto de ocio de gente de la zona o de fuera |

La semana suma 5 laborables y 1 sábado. **El perfil no modela el domingo** (su «fin de
semana» usa el horario de transporte del sábado), así que el domingo no entra.

### 3. Otros cambios hechos al construir la parte B

- `src/procesar.py` guarda ahora de OpenStreetMap el horario (`opening_hours`, que tienen
  2.275 locales) y la etiqueta `food`. Sirven para comparar con el horario de la
  competencia y para el criterio de «sirve comidas».
- **Propensión a pararse a consumir** (nuevo supuesto). El perfil cuenta gente que
  *pasa*, pero no todos son clientes posibles: a los viajeros se les da 0,3 (van de
  paso), a padres y niños 0,6 (se cuentan niños y adultos, pero paga el adulto) y al
  resto 1. Se usa en «a quién», en los momentos de consumo y en la gama ajustada; el
  perfil por horas no cambia.

## Metodología de las cuatro respuestas

### A quién vender

Para cada franja y día (laborable y sábado), los tipos de cliente que suman al menos un
10 % de la gente que pasa. La recomendación del día se basa en los **clientes posibles**
(gente × propensión a pararse). En el porqué se dan los dos pesos: el de gente que pasa
y el de clientes posibles. **El domingo no se modela**, y así se dice en la salida.

### A qué hora

- Se compara la gente media por hora de cada franja con la de la mejor franja: a partir
  del 50 % conviene abrir; entre el 30 % y el 50 %, valorarlo; por debajo, no compensa.
- Se dan las tres horas punta del perfil.
- **Competencia:** el horario de apertura solo está en OpenStreetMap. Si hay al menos 3
  locales con horario en el radio, se calcula qué parte abre en cada franja (miércoles
  para el laborable y sábado para el sábado). Una franja con movimiento en la que abren
  menos del 40 % es un **posible hueco horario**. Con menos de 3 locales con horario, la
  salida dice que no hay datos suficientes.

### Qué vender

**Momentos de consumo.** La tabla `TABLA_MOMENTOS` de `supuestos.py` relaciona cada tipo
de cliente y franja con sus momentos de consumo. Se basa en los horarios de comida en
España, en los horarios de cada tipo de cliente y en costumbres generales de la
hostelería, y cada relación lleva su comentario en el código:

| Tipo de cliente | Primera hora de la mañana | Media mañana | Mediodía | Media tarde | Tarde-noche | Noche |
|---|---|---|---|---|---|---|
| Padres y niños | Desayuno | — | — | Merienda | — | — |
| Universitarios | Desayuno | Almuerzo de media mañana | Menú del día | Merienda | Cañas y raciones | — |
| Pacientes | Desayuno | Almuerzo de media mañana | — | Merienda | — | — |
| Trabajadores | Desayuno | Almuerzo de media mañana | Menú del día | Cañas y raciones | Cañas y raciones | — |
| Deporte y eventos | — | — | Cañas y raciones | Merienda | Cañas y raciones, Cenas | Copas |
| Viajeros | Desayuno | Almuerzo de media mañana | — | Merienda | Cañas y raciones | — |
| Vecinos | Desayuno | Almuerzo de media mañana | Menú del día, Cañas y raciones | Merienda | Cañas y raciones, Cenas | Copas |

Cómo se usa:

- La gente de cada celda (por la propensión a pararse) se reparte a partes iguales entre
  sus momentos, para no contarla dos veces.
- El **menú del día solo existe en laborable**: en sábado, ese público pasa a «cañas y
  raciones» (aperitivo).
- Se recomiendan los momentos con al menos la mitad de clientes posibles que el más
  fuerte del día.
- La confianza es como mucho media, porque la tabla es un supuesto.

**Huecos de competencia.** Se compara con la media del municipio cada tipo de local:
locales que sirven comidas, bares, cafeterías y comida rápida (nunca «restaurantes» a
secas).

- Por debajo de ×0,75 hay un **posible hueco**; por encima de ×1,5, **oferta abundante**.
- Solo se compara si la media del municipio es de al menos 1 local.
- Se añade la densidad total del radio como contexto, porque si toda la zona tiene pocos
  locales, todos los tipos «faltan».
- Si hay hueco de comidas y público para menú del día o cenas, se señala como la
  combinación que más apunta a una oportunidad (a comprobar).

**Cocinas.** Solo se usan si en el radio hay al menos 5 locales de OSM y más de la mitad
indica su cocina. En los tres puntos de prueba no se cumple, y la salida dice que no hay
datos suficientes.

### A qué precio

- Se dan la **gama ajustada** y la gama por la renta de los vecinos. La confianza es baja,
  salvo que los vecinos sean más de la mitad de la clientela.
- **Índice de precios** (septiembre de 2026): restaurantes y alojamiento +5,7 % frente a
  alimentos +3,2 %. Va con el aviso de que el grupo incluye hoteles (+18 %).
- **No se dan precios en euros**, porque no hay datos abiertos de cartas. Se recomienda
  comprobar en persona los precios de 3 a 5 locales del radio.

### Riesgos y avisos

- **Competencia alta:** más de ×1,5 la media del municipio. Si la media es menor de 1
  local, se dice que no se puede valorar.
- **Cobertura baja de OpenStreetMap.**
- **Festivos próximos**, y las fiestas locales de 2026 como orientación (los de 2027 aún
  no están publicados).
- **Periodos sin clase:** se avisa si universitarios o padres y niños son al menos el 15 %
  de un laborable.
- **Calendario escolar:** se buscó en el portal de la Comunidad («calendario escolar»,
  «calendario lectivo», «vacaciones escolares», «calendario» y títulos con «escolar») y
  **no hay ningún conjunto con el calendario escolar**. El periodo lectivo es un
  **supuesto** en `supuestos.py` (`PERIODO_LECTIVO`), con el calendario típico de la
  Comunidad, y la salida lo dice. No se ha usado ninguna otra fuente.

### Qué comprobar en persona

De 5 a 8 comprobaciones concretas, elegidas según el punto:

- contar durante 15 minutos la gente que pasa en la hora punta (la salida da la cifra
  estimada para comparar);
- anotar los precios de 3 a 5 locales;
- comprobar los horarios reales de la competencia;
- según el punto: ver hacia dónde sale la gente del transporte; consultar el calendario
  del campus y si dentro hay cafetería; observar la salida de los colegios; contar los
  locales reales donde OSM tiene pocos; confirmar los huecos detectados;
- preguntar a un hostelero de la zona.

## Comprobación a mano y correcciones

Se revisaron las tres salidas contra los números del perfil y del informe. Lo que no
tenía sentido se corrigió:

| Lo que salía | Por qué no tenía sentido | Corrección |
|---|---|---|
| Vicálvaro: el **menú del día no aparecía** en laborable, aunque a mediodía hay ~1.340 universitarios y el primer momento era «cañas y raciones» | Los viajeros (56 % del paso) contaban igual que quien se sienta a comer, y las celdas con dos momentos se contaban dos veces | Propensión a pararse (viajeros 0,3) y reparto de las celdas entre sus momentos. Ahora: desayuno > cañas > merienda > almuerzo > menú del día |
| Confianza «baja» en momentos y horarios por aportes mínimos (35 pacientes o 53 trabajadores) | Un aporte del 1-2 % no debe marcar la confianza | Solo cuentan los tipos con al menos un 25 % del momento o la franja |
| Griñón: «**competencia alta**, 2 locales, ×3,20» | La media del municipio en OSM es de 0,6 locales; la proporción no dice nada | Si la media es menor de 1 local: «no se puede valorar» |
| Griñón: «sin huecos claros» | No se había podido comparar ningún tipo | Se dice que no se pueden buscar huecos y por qué |
| Sábado: «vecinos a mediodía» repetido en cañas y raciones; aportes de «~1 persona» | La sustitución del menú duplicaba la línea | Aportes agrupados y filtrados (mínimo 5 personas) |
| Griñón: padres y niños como primer cliente (47 %) | Se contaba a los niños como clientes que pagan | Propensión 0,6 para padres y niños: queda en un 35 %, detrás de los vecinos |
| Festivos: «el público de laborable desaparece» | Exagerado: esos días cambia el público | «Cambia el público; el día se parece más a un sábado» |

También se comprobó que las cifras grandes tienen origen en los datos. En Fuenlabrada los
viajeros suman unos 41.000 pasos en un laborable porque la estación de Cercanías está a
59 m de la plaza y el portal le da 9,3 millones de viajeros al año; es coherente con el
método.

## Resultados de los tres puntos (resumen)

| | Vicálvaro (campus URJC) | Fuenlabrada (Pl. de la Constitución) | Griñón (Plaza Mayor) |
|---|---|---|---|
| **A quién** (laborable, clientes posibles) | vecinos 33 %, universitarios 31 %, viajeros 28 % | viajeros 71 %, vecinos 26 % | vecinos 41 %, padres y niños 35 %, pacientes 23 % |
| **A quién** (sábado) | vecinos 60 %, viajeros 39 % | viajeros 64 %, vecinos 34 % | vecinos 92 % |
| **A qué hora** (laborable) | abrir de 6 a 22 h; punta 8, 9 y 14 h | abrir de 6 a 22 h; punta 7, 8 y 9 h | abrir de 6 a 18 h (no compensa la tarde-noche); punta 8, 16 y 14 h |
| **A qué hora** (sábado) | todo el día; punta 11-13 h | todo el día; punta 11-13 h | de 10 a 22 h; punta 11-13 h |
| Horario de la competencia | posible hueco en tarde-noche (solo 3 locales con horario: confianza baja) | sin hueco claro (5 locales con horario) | sin datos (0 locales con horario) |
| **Qué vender** (laborable) | desayuno, cañas y raciones, merienda, almuerzo, menú del día | desayuno, cañas y raciones, merienda, almuerzo | desayuno, merienda, almuerzo |
| **Qué vender** (sábado) | cañas y raciones, almuerzo, merienda | cañas y raciones, almuerzo, merienda | cañas y raciones, almuerzo, merienda |
| Huecos | **menos locales que sirven comidas (×0,52)**, bares (×0,73) y cafeterías (×0,57); abundante comida rápida (×3,66). Hueco de comidas + público de menú: oportunidad a comprobar | todo abundante (×1,6 a ×2,6), confianza baja por la cobertura de OSM | no se pueden buscar (media del municipio < 1 local en OSM) |
| **A qué precio** | económica (vecinos: económica) | económica (vecinos: económica) | media (vecinos: media) |
| Riesgos | festivos; periodos sin clase (universitarios 19 % del laborable) | competencia alta (×2,07); cobertura baja de OSM; festivos (incluido el local del 26/12) | cobertura muy baja de OSM; festivos; periodos sin clase (padres y niños 46 % del laborable) |

Los textos completos están en el anexo.

## Limitaciones

- **Todo lo que es gente es estimación** (perfil por horas), y el paso de «gente que
  pasa» a «cliente posible» es un supuesto (propensión a pararse).
- La tabla de momentos de consumo es cualitativa: dice qué momento encaja con cada
  cliente y franja, no cuánto gasta cada uno.
- **Las cenas y las copas casi nunca salen recomendadas.** Por la noche pasa poca gente
  cerca y la cena depende más de que la gente vaya a propósito (el local como destino)
  que de que pase por delante, y eso el modelo no lo capta. No significa que no haya
  mercado de cenas.
- **El domingo no se modela** y el perfil de fin de semana es el del sábado.
- **Calendario escolar** supuesto: no hay conjunto abierto en el portal.
- **Horarios de la competencia:** solo en OSM y con muestras muy pequeñas (0 a 5 locales
  con horario por punto). El censo de Madrid no tiene horarios.
- **Cocinas:** sin datos suficientes en ninguno de los tres puntos.
- **Fuera de Madrid capital**, la competencia sale de OSM, al que le faltan muchos
  locales (cobertura de 0,2 a 0,4 frente al censo). Huecos y saturaciones allí tienen
  confianza baja.
- **Precios:** no hay cartas en abierto, así que no se dan euros. El índice de precios
  mezcla restaurantes y hoteles.

## Fuentes

No hay fuentes nuevas. Se usan las de la parte A y del perfil por horas, ya anotadas en
`docs/fuentes.md`. El bloque de datos procesados de `docs/fuentes.md` recoge los dos
campos nuevos de OpenStreetMap (horario y comida).

## Anexo: salidas completas de `src/recomendaciones.py`

### Recomendaciones · 40.4046, -3.6106 · Madrid · radio 300 m

> Orientaciones a partir de datos abiertos y supuestos explícitos, no garantías. Toda cifra de personas es una estimación.

#### A quién vender

- **En laborable, orientar la oferta sobre todo a vecinos (33 %), universitarios (31 %), viajeros (28 %).** *(confianza media; estimación)*
  - Vecinos: 20 % de la gente que pasa cerca en el día (~4.684 pasos) y 33 % de los clientes posibles (propensión a pararse 1,0); su franja fuerte es «tarde-noche».
  - Universitarios: 19 % de la gente que pasa cerca en el día (~4.391 pasos) y 31 % de los clientes posibles (propensión a pararse 1,0); su franja fuerte es «mediodía».
  - Viajeros: 56 % de la gente que pasa cerca en el día (~12.998 pasos) y 28 % de los clientes posibles (propensión a pararse 0,3); su franja fuerte es «primera hora de la mañana».
- **En sábado, orientar la oferta sobre todo a vecinos (60 %), viajeros (39 %).** *(confianza media; estimación)*
  - Vecinos: 31 % de la gente que pasa cerca en el día (~3.753 pasos) y 60 % de los clientes posibles (propensión a pararse 1,0); su franja fuerte es «tarde-noche».
  - Viajeros: 68 % de la gente que pasa cerca en el día (~8.162 pasos) y 39 % de los clientes posibles (propensión a pararse 0,3); su franja fuerte es «tarde-noche».

Clientes principales por franja (peso ≥ 10 %, estimación):

| Franja | Laborable | Sábado |
|---|---|---|
| primera hora de la mañana | Viajeros 53 %, Universitarios 22 %, Vecinos 19 % (~5.272) | Viajeros 83 %, Vecinos 16 % (~1.756) |
| media mañana | Viajeros 57 %, Vecinos 20 %, Universitarios 15 % (~3.842) | Viajeros 57 %, Vecinos 41 % (~2.222) |
| mediodía | Viajeros 48 %, Universitarios 29 %, Vecinos 18 % (~4.607) | Viajeros 66 %, Vecinos 34 % (~2.102) |
| media tarde | Viajeros 56 %, Vecinos 23 %, Universitarios 15 % (~3.891) | Viajeros 67 %, Vecinos 33 % (~2.063) |
| tarde-noche | Viajeros 58 %, Vecinos 23 %, Universitarios 17 % (~4.525) | Viajeros 65 %, Vecinos 34 % (~2.749) |
| noche | Viajeros 88 %, Vecinos 12 % (~1.159) | Viajeros 80 %, Vecinos 20 % (~1.110) |

*El perfil no modela el domingo aparte: el «fin de semana» usa el horario de transporte del sábado y costumbres genéricas de fin de semana. Aquí se presenta como «sábado».*

#### A qué hora

- **En laborable, conviene abrir en: primera hora de la mañana, media mañana, mediodía, media tarde, tarde-noche. Horas punta: 08:00-08:59, 09:00-09:59, 14:00-14:59.** *(confianza media; estimación)*
  - «primera hora de la mañana»: ~1.318 personas por hora (86 % de la mejor franja)
  - «media mañana»: ~1.281 personas por hora (83 % de la mejor franja)
  - «mediodía»: ~1.536 personas por hora (100 % de la mejor franja)
  - «media tarde»: ~1.297 personas por hora (84 % de la mejor franja)
  - «tarde-noche»: ~1.131 personas por hora (74 % de la mejor franja)
  - «noche»: ~166 personas por hora (11 % de la mejor franja)
  - Horas punta: 08:00-08:59 (~2.084; Viajeros 41 %, Universitarios 32 %, Vecinos 20 %); 09:00-09:59 (~1.747; Viajeros 47 %, Universitarios 27 %, Vecinos 18 %); 14:00-14:59 (~1.685; Viajeros 44 %, Universitarios 34 %, Vecinos 19 %)
- **Posible hueco horario en laborable: tarde-noche (hay movimiento y abren pocos locales).** *(confianza baja; dato + estimación)*
  - «primera hora de la mañana»: abre el 100 % de los 3 locales con horario en OpenStreetMap
  - «media mañana»: abre el 100 % de los 3 locales con horario en OpenStreetMap
  - «mediodía»: abre el 100 % de los 3 locales con horario en OpenStreetMap
  - «media tarde»: abre el 67 % de los 3 locales con horario en OpenStreetMap
  - «tarde-noche»: abre el 0 % de los 3 locales con horario en OpenStreetMap
  - «noche»: abre el 0 % de los 3 locales con horario en OpenStreetMap
  - Solo 3 de 10 locales de OSM del radio tienen horario: muestra pequeña.
- **En sábado, conviene abrir en: primera hora de la mañana, media mañana, mediodía, media tarde, tarde-noche. Horas punta: 11:00-11:59, 12:00-12:59, 13:00-13:59.** *(confianza baja; estimación)*
  - «primera hora de la mañana»: ~439 personas por hora (59 % de la mejor franja)
  - «media mañana»: ~741 personas por hora (100 % de la mejor franja)
  - «mediodía»: ~701 personas por hora (95 % de la mejor franja)
  - «media tarde»: ~688 personas por hora (93 % de la mejor franja)
  - «tarde-noche»: ~687 personas por hora (93 % de la mejor franja)
  - «noche»: ~159 personas por hora (21 % de la mejor franja)
  - Horas punta: 11:00-11:59 (~793; Viajeros 58 %, Vecinos 41 %); 12:00-12:59 (~772; Viajeros 56 %, Vecinos 42 %); 13:00-13:59 (~771; Viajeros 60 %, Vecinos 39 %)
- **No hay datos suficientes para comparar con el horario de la competencia en sábado.** *(confianza baja; dato)*
  - Solo 0 de 10 locales de OpenStreetMap del radio indican su horario (mínimo 3); el censo de Madrid no tiene horarios.

#### Qué vender

Momentos de consumo:

- **Laborable: desayuno (~3.254 clientes posibles; 25 % del total de momentos del día).** *(confianza media; estimación)*
  - Universitarios en «primera hora de la mañana»: ~1.145 clientes posibles
  - Vecinos en «primera hora de la mañana»: ~1.014 clientes posibles
  - Viajeros en «primera hora de la mañana»: ~832 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).
- **Laborable: cañas y raciones (~2.537 clientes posibles; 20 % del total de momentos del día).** *(confianza media; estimación)*
  - Viajeros en «tarde-noche»: ~786 clientes posibles
  - Universitarios en «tarde-noche»: ~764 clientes posibles
  - Vecinos en «tarde-noche»: ~520 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).
- **Laborable: merienda (~2.322 clientes posibles; 18 % del total de momentos del día).** *(confianza media; estimación)*
  - Vecinos en «media tarde»: ~884 clientes posibles
  - Viajeros en «media tarde»: ~653 clientes posibles
  - Universitarios en «media tarde»: ~573 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).
- **Laborable: almuerzo de media mañana (~2.281 clientes posibles; 18 % del total de momentos del día).** *(confianza media; estimación)*
  - Vecinos en «media mañana»: ~780 clientes posibles
  - Viajeros en «media mañana»: ~660 clientes posibles
  - Universitarios en «media mañana»: ~573 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).
- **Laborable: menú del día (~1.805 clientes posibles; 14 % del total de momentos del día).** *(confianza media; estimación)*
  - Universitarios en «mediodía»: ~1.336 clientes posibles
  - Vecinos en «mediodía»: ~416 clientes posibles
  - Trabajadores en «mediodía»: ~53 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).
- **Sábado: cañas y raciones (~1.741 clientes posibles; 31 % del total de momentos del día).** *(confianza media; estimación)*
  - Vecinos en «mediodía»: ~705 clientes posibles
  - Viajeros en «tarde-noche»: ~536 clientes posibles
  - Vecinos en «tarde-noche»: ~473 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).
- **Sábado: almuerzo de media mañana (~1.328 clientes posibles; 24 % del total de momentos del día).** *(confianza media; estimación)*
  - Vecinos en «media mañana»: ~906 clientes posibles
  - Viajeros en «media mañana»: ~382 clientes posibles
  - Pacientes en «media mañana»: ~35 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).
- **Sábado: merienda (~1.098 clientes posibles; 20 % del total de momentos del día).** *(confianza media; estimación)*
  - Vecinos en «media tarde»: ~685 clientes posibles
  - Viajeros en «media tarde»: ~413 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).
- **La oferta de comidas del radio está por debajo de lo habitual y hay público para menú del día: es la combinación que más apunta a una oportunidad (a comprobar).** *(confianza media; dato + estimación)*
  - 13 locales que sirven comidas en 300 m frente a 24,9 de media en un punto habitado del municipio (×0,52); fuente: Censo de locales del Ayuntamiento de Madrid.
  - Ver los momentos recomendados arriba.

Huecos de competencia (con «locales que sirven comidas», no «restaurantes» a secas):

- **Posible hueco: hay menos locales que sirven comidas que en un punto típico del municipio.** *(confianza media; dato + estimación)*
  - 13 locales que sirven comidas en 300 m frente a 24,9 de media en un punto habitado del municipio (×0,52); fuente: Censo de locales del Ayuntamiento de Madrid.
  - En conjunto el radio tiene 27 locales, ×0,69 la media del municipio: parte de la diferencia se explica por eso.
- **Posible hueco: hay menos bares que en un punto típico del municipio.** *(confianza media; dato + estimación)*
  - 18 bares en 300 m frente a 24,7 de media en un punto habitado del municipio (×0,73); fuente: Censo de locales del Ayuntamiento de Madrid.
  - En conjunto el radio tiene 27 locales, ×0,69 la media del municipio: parte de la diferencia se explica por eso.
- **Posible hueco: hay menos cafeterías que en un punto típico del municipio.** *(confianza media; dato + estimación)*
  - 4 cafeterías en 300 m frente a 7,0 de media en un punto habitado del municipio (×0,57); fuente: Censo de locales del Ayuntamiento de Madrid.
  - En conjunto el radio tiene 27 locales, ×0,69 la media del municipio: parte de la diferencia se explica por eso.
- **Oferta abundante de locales de comida rápida: competir en ese formato puede ser más difícil.** *(confianza media; dato + estimación)*
  - 5 locales de comida rápida en 300 m frente a 1,4 de media en un punto habitado del municipio (×3,66); fuente: Censo de locales del Ayuntamiento de Madrid.
  - En conjunto el radio tiene 27 locales, ×0,69 la media del municipio: parte de la diferencia se explica por eso.

Tipos de cocina:

- **No hay datos suficientes sobre tipos de cocina en el radio.** *(confianza baja; dato)*
  - Solo 4 de 10 locales de OpenStreetMap indican su cocina (hacen falta al menos 5 locales y más del 50 %).

#### A qué precio

- **Gama orientativa: económica (ajustada a la clientela); por la renta de los vecinos sería económica.** *(confianza baja; estimación)*
  - Renta de los vecinos: ×0,74 la media de la Comunidad → gama económica.
  - Peso de cada cliente en la semana (gente × propensión a pararse): vecinos 36 %, universitarios 29 %, viajeros 29 %.
  - Laborable: económica (1,15); sábado: económica (1,20); escala de 1 (económica) a 3 (alta).
  - Las gamas de universitarios, viajeros, trabajadores y deporte son supuestos (src/supuestos.py, GAMA_CLIENTE).
- **Precios del sector: en los últimos 12 meses (hasta septiembre de 2026) restaurantes y alojamiento +5,7 % frente a alimentos +3,2 %: el sector ha subido precios por encima de la materia prima. Puede servir de referencia al revisar la carta, no como regla.** *(confianza media; dato)*
  - IPC de la Comunidad de Madrid (portal): restaurantes y servicios de alojamiento +5,7 %, alimentos y bebidas no alcohólicas +3,2 %, bebidas alcohólicas +0,6 %, índice general +5,3 %.
  - **Aviso:** el grupo incluye hoteles, que han subido +18,0 %; la subida propia de bares y restaurantes probablemente sea menor.
- **No se dan precios en euros: no hay datos abiertos de cartas. Conviene comprobar en persona los precios de 3 a 5 locales del radio (café, caña, menú del día, ración) antes de fijar los propios.** *(confianza alta; dato)*
  - Ninguna fuente abierta del proyecto publica precios de cartas.

#### Riesgos y avisos

- **Festivos próximos: esos días cambia el público; baja el de laborable (trabajadores, estudiantes) y el día se parece más a un sábado.** *(confianza alta; dato)*
  - 2026-12-07 (lunes): Día de la Constitución Española
  - 2026-12-08 (martes): Inmaculada Concepción
  - 2026-12-25 (viernes): Natividad del Señor
  - Fiestas locales del año en curso (orientación para el siguiente, aún sin publicar): 2026-05-15, 2026-11-09
- **Periodos sin clase: universitarios son el 19 % de la gente de un laborable; sin clase ese público desaparece.** *(confianza media; estimación)*
  - Periodo lectivo típico (universidad): de mediados de septiembre a mayo, con exámenes hasta finales de junio o principios de julio; sin clase en Navidad, en Semana Santa ni en julio y agosto (el campus queda casi vacío en agosto).
  - El portal de la Comunidad no publica el calendario escolar: el periodo lectivo es un supuesto (src/supuestos.py).

#### Qué comprobar en persona

1. Contar durante 15 minutos la gente que pasa por delante del local en la hora punta de un laborable (08:00-08:59) y comparar con la estimación (~521 personas en 15 minutos); repetirlo en una hora floja.
2. Anotar en 3 a 5 locales del radio el precio del café, la caña, el menú del día y una ración, y si tienen menú del día.
3. Comprobar a qué hora abren y cierran de verdad los bares y restaurantes del radio (los datos abiertos casi no traen horarios).
4. Ver por qué acera sale la gente del metro o de las paradas de autobús y si pasa por delante del local o va hacia otro lado.
5. Consultar el calendario académico y los horarios de clase del campus, y si dentro hay cafetería o comedor (competencia que no está en el censo).
6. Preguntar a un hostelero de la zona qué días y meses flojean (agosto, fiestas locales, puentes) y cuánto pesa la terraza en su negocio.
7. Confirmar los posibles huecos (locales que sirven comidas, bares, cafeterías) recorriendo el radio y preguntando si hubo locales de ese tipo que cerraron y por qué.


### Recomendaciones · 40.283366, -3.800132 · Fuenlabrada · radio 300 m

> Orientaciones a partir de datos abiertos y supuestos explícitos, no garantías. Toda cifra de personas es una estimación.

#### A quién vender

- **En laborable, orientar la oferta sobre todo a viajeros (71 %), vecinos (26 %).** *(confianza media; estimación)*
  - Viajeros: 89 % de la gente que pasa cerca en el día (~40.986 pasos) y 71 % de los clientes posibles (propensión a pararse 0,3); su franja fuerte es «primera hora de la mañana».
  - Vecinos: 10 % de la gente que pasa cerca en el día (~4.532 pasos) y 26 % de los clientes posibles (propensión a pararse 1,0); su franja fuerte es «tarde-noche».
- **En sábado, orientar la oferta sobre todo a viajeros (64 %), vecinos (34 %).** *(confianza media; estimación)*
  - Viajeros: 86 % de la gente que pasa cerca en el día (~22.916 pasos) y 64 % de los clientes posibles (propensión a pararse 0,3); su franja fuerte es «tarde-noche».
  - Vecinos: 14 % de la gente que pasa cerca en el día (~3.627 pasos) y 34 % de los clientes posibles (propensión a pararse 1,0); su franja fuerte es «tarde-noche».

Clientes principales por franja (peso ≥ 10 %, estimación):

| Franja | Laborable | Sábado |
|---|---|---|
| primera hora de la mañana | Viajeros 91 % (~12.199) | Viajeros 92 % (~3.827) |
| media mañana | Viajeros 86 %, Vecinos 12 % (~6.245) | Viajeros 82 %, Vecinos 17 % (~5.053) |
| mediodía | Viajeros 88 %, Vecinos 10 % (~7.742) | Viajeros 85 %, Vecinos 14 % (~4.854) |
| media tarde | Viajeros 87 %, Vecinos 11 % (~7.622) | Viajeros 86 %, Vecinos 14 % (~4.823) |
| tarde-noche | Viajeros 88 %, Vecinos 11 % (~9.000) | Viajeros 84 %, Vecinos 15 % (~6.087) |
| noche | Viajeros 96 % (~3.292) | Viajeros 90 %, Vecinos 10 % (~2.084) |

*El perfil no modela el domingo aparte: el «fin de semana» usa el horario de transporte del sábado y costumbres genéricas de fin de semana. Aquí se presenta como «sábado».*

#### A qué hora

- **En laborable, conviene abrir en: primera hora de la mañana, media mañana, mediodía, media tarde, tarde-noche. Horas punta: 08:00-08:59, 07:00-07:59, 09:00-09:59.** *(confianza alta; estimación)*
  - «primera hora de la mañana»: ~3.050 personas por hora (100 % de la mejor franja)
  - «media mañana»: ~2.082 personas por hora (68 % de la mejor franja)
  - «mediodía»: ~2.581 personas por hora (85 % de la mejor franja)
  - «media tarde»: ~2.541 personas por hora (83 % de la mejor franja)
  - «tarde-noche»: ~2.250 personas por hora (74 % de la mejor franja)
  - «noche»: ~470 personas por hora (15 % de la mejor franja)
  - Horas punta: 08:00-08:59 (~3.667; Viajeros 87 %, Vecinos 11 %); 07:00-07:59 (~3.450; Viajeros 93 %, Vecinos 7 %); 09:00-09:59 (~3.000; Viajeros 88 %, Vecinos 10 %)
- **En laborable la competencia con horario conocido cubre las franjas con movimiento: no se ve un hueco horario claro.** *(confianza baja; dato + estimación)*
  - «primera hora de la mañana»: abre el 60 % de los 5 locales con horario en OpenStreetMap
  - «media mañana»: abre el 60 % de los 5 locales con horario en OpenStreetMap
  - «mediodía»: abre el 60 % de los 5 locales con horario en OpenStreetMap
  - «media tarde»: abre el 60 % de los 5 locales con horario en OpenStreetMap
  - «tarde-noche»: abre el 80 % de los 5 locales con horario en OpenStreetMap
  - «noche»: abre el 80 % de los 5 locales con horario en OpenStreetMap
  - Solo 5 de 25 locales de OSM del radio tienen horario: muestra pequeña.
- **En sábado, conviene abrir en: primera hora de la mañana, media mañana, mediodía, media tarde, tarde-noche. Horas punta: 11:00-11:59, 12:00-12:59, 13:00-13:59.** *(confianza alta; estimación)*
  - «primera hora de la mañana»: ~957 personas por hora (57 % de la mejor franja)
  - «media mañana»: ~1.684 personas por hora (100 % de la mejor franja)
  - «mediodía»: ~1.618 personas por hora (96 % de la mejor franja)
  - «media tarde»: ~1.608 personas por hora (95 % de la mejor franja)
  - «tarde-noche»: ~1.522 personas por hora (90 % de la mejor franja)
  - «noche»: ~298 personas por hora (18 % de la mejor franja)
  - Horas punta: 11:00-11:59 (~1.706; Viajeros 81 %, Vecinos 18 %); 12:00-12:59 (~1.706; Viajeros 81 %, Vecinos 18 %); 13:00-13:59 (~1.680; Viajeros 82 %, Vecinos 17 %)
- **En sábado la competencia con horario conocido cubre las franjas con movimiento: no se ve un hueco horario claro.** *(confianza baja; dato + estimación)*
  - «primera hora de la mañana»: abre el 50 % de los 4 locales con horario en OpenStreetMap
  - «media mañana»: abre el 50 % de los 4 locales con horario en OpenStreetMap
  - «mediodía»: abre el 50 % de los 4 locales con horario en OpenStreetMap
  - «media tarde»: abre el 50 % de los 4 locales con horario en OpenStreetMap
  - «tarde-noche»: abre el 100 % de los 4 locales con horario en OpenStreetMap
  - «noche»: abre el 100 % de los 4 locales con horario en OpenStreetMap
  - Solo 4 de 25 locales de OSM del radio tienen horario: muestra pequeña.

#### Qué vender

Momentos de consumo:

- **Laborable: desayuno (~4.445 clientes posibles; 31 % del total de momentos del día).** *(confianza media; estimación)*
  - Viajeros en «primera hora de la mañana»: ~3.322 clientes posibles
  - Vecinos en «primera hora de la mañana»: ~980 clientes posibles
  - Trabajadores en «primera hora de la mañana»: ~131 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).
- **Laborable: cañas y raciones (~3.348 clientes posibles; 23 % del total de momentos del día).** *(confianza media; estimación)*
  - Viajeros en «tarde-noche»: ~2.380 clientes posibles
  - Vecinos en «tarde-noche»: ~503 clientes posibles
  - Vecinos en «mediodía»: ~402 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).
- **Laborable: merienda (~2.928 clientes posibles; 20 % del total de momentos del día).** *(confianza media; estimación)*
  - Viajeros en «media tarde»: ~1.997 clientes posibles
  - Vecinos en «media tarde»: ~855 clientes posibles
  - Pacientes en «media tarde»: ~76 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).
- **Laborable: almuerzo de media mañana (~2.478 clientes posibles; 17 % del total de momentos del día).** *(confianza media; estimación)*
  - Viajeros en «media mañana»: ~1.615 clientes posibles
  - Vecinos en «media mañana»: ~756 clientes posibles
  - Pacientes en «media mañana»: ~87 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).
- **Sábado: cañas y raciones (~2.774 clientes posibles; 31 % del total de momentos del día).** *(confianza media; estimación)*
  - Viajeros en «tarde-noche»: ~1.543 clientes posibles
  - Vecinos en «mediodía»: ~681 clientes posibles
  - Vecinos en «tarde-noche»: ~458 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).
- **Sábado: almuerzo de media mañana (~2.162 clientes posibles; 24 % del total de momentos del día).** *(confianza media; estimación)*
  - Viajeros en «media mañana»: ~1.239 clientes posibles
  - Vecinos en «media mañana»: ~875 clientes posibles
  - Pacientes en «media mañana»: ~48 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).
- **Sábado: merienda (~1.900 clientes posibles; 21 % del total de momentos del día).** *(confianza media; estimación)*
  - Viajeros en «media tarde»: ~1.239 clientes posibles
  - Vecinos en «media tarde»: ~661 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).

Huecos de competencia (con «locales que sirven comidas», no «restaurantes» a secas):

- **Oferta abundante de locales que sirven comidas: competir en ese formato puede ser más difícil.** *(confianza baja; dato + estimación)*
  - 5 locales que sirven comidas en 300 m frente a 1,9 de media en un punto habitado del municipio (×2,57); fuente: OpenStreetMap.
  - En conjunto el radio tiene 25 locales, ×2,07 la media del municipio: parte de la diferencia se explica por eso.
  - OpenStreetMap tiene pocos locales en este municipio (cobertura ×0,38 frente al censo de Madrid): la comparación es orientativa.
- **Oferta abundante de bares: competir en ese formato puede ser más difícil.** *(confianza baja; dato + estimación)*
  - 10 bares en 300 m frente a 5,9 de media en un punto habitado del municipio (×1,71); fuente: OpenStreetMap.
  - En conjunto el radio tiene 25 locales, ×2,07 la media del municipio: parte de la diferencia se explica por eso.
  - OpenStreetMap tiene pocos locales en este municipio (cobertura ×0,38 frente al censo de Madrid): la comparación es orientativa.
- **Oferta abundante de cafeterías: competir en ese formato puede ser más difícil.** *(confianza baja; dato + estimación)*
  - 8 cafeterías en 300 m frente a 3,1 de media en un punto habitado del municipio (×2,56); fuente: OpenStreetMap.
  - En conjunto el radio tiene 25 locales, ×2,07 la media del municipio: parte de la diferencia se explica por eso.
  - OpenStreetMap tiene pocos locales en este municipio (cobertura ×0,38 frente al censo de Madrid): la comparación es orientativa.
- **Oferta abundante de locales de comida rápida: competir en ese formato puede ser más difícil.** *(confianza baja; dato + estimación)*
  - 2 locales de comida rápida en 300 m frente a 1,2 de media en un punto habitado del municipio (×1,62); fuente: OpenStreetMap.
  - En conjunto el radio tiene 25 locales, ×2,07 la media del municipio: parte de la diferencia se explica por eso.
  - OpenStreetMap tiene pocos locales en este municipio (cobertura ×0,38 frente al censo de Madrid): la comparación es orientativa.

Tipos de cocina:

- **No hay datos suficientes sobre tipos de cocina en el radio.** *(confianza baja; dato)*
  - Solo 1 de 25 locales de OpenStreetMap indican su cocina (hacen falta al menos 5 locales y más del 50 %).

#### A qué precio

- **Gama orientativa: económica (ajustada a la clientela); por la renta de los vecinos sería económica.** *(confianza baja; estimación)*
  - Renta de los vecinos: ×0,74 la media de la Comunidad → gama económica.
  - Peso de cada cliente en la semana (gente × propensión a pararse): viajeros 70 %, vecinos 27 %.
  - Laborable: económica (1,37); sábado: económica (1,33); escala de 1 (económica) a 3 (alta).
  - Las gamas de universitarios, viajeros, trabajadores y deporte son supuestos (src/supuestos.py, GAMA_CLIENTE).
- **Precios del sector: en los últimos 12 meses (hasta septiembre de 2026) restaurantes y alojamiento +5,7 % frente a alimentos +3,2 %: el sector ha subido precios por encima de la materia prima. Puede servir de referencia al revisar la carta, no como regla.** *(confianza media; dato)*
  - IPC de la Comunidad de Madrid (portal): restaurantes y servicios de alojamiento +5,7 %, alimentos y bebidas no alcohólicas +3,2 %, bebidas alcohólicas +0,6 %, índice general +5,3 %.
  - **Aviso:** el grupo incluye hoteles, que han subido +18,0 %; la subida propia de bares y restaurantes probablemente sea menor.
- **No se dan precios en euros: no hay datos abiertos de cartas. Conviene comprobar en persona los precios de 3 a 5 locales del radio (café, caña, menú del día, ración) antes de fijar los propios.** *(confianza alta; dato)*
  - Ninguna fuente abierta del proyecto publica precios de cartas.

#### Riesgos y avisos

- **Competencia alta: 25 locales en el radio, ×2,07 la media del municipio.** *(confianza baja; dato + estimación)*
  - Fuente: OpenStreetMap.
- **Cobertura baja de OpenStreetMap: probablemente hay más locales de los que se cuentan, así que la competencia real es mayor.** *(confianza media; dato)*
  - OSM registra 1,89 locales por 1.000 habitantes en el municipio, frente a 5,02 del censo oficial de Madrid capital.
- **Festivos próximos: esos días cambia el público; baja el de laborable (trabajadores, estudiantes) y el día se parece más a un sábado.** *(confianza alta; dato)*
  - 2026-12-07 (lunes): Día de la Constitución Española
  - 2026-12-08 (martes): Inmaculada Concepción
  - 2026-12-25 (viernes): Natividad del Señor
  - 2026-12-26 (sábado): fiesta local (Fuenlabrada)
  - Fiestas locales del año en curso (orientación para el siguiente, aún sin publicar): 2026-09-14, 2026-12-26

#### Qué comprobar en persona

1. Contar durante 15 minutos la gente que pasa por delante del local en la hora punta de un laborable (08:00-08:59) y comparar con la estimación (~917 personas en 15 minutos); repetirlo en una hora floja.
2. Anotar en 3 a 5 locales del radio el precio del café, la caña, el menú del día y una ración, y si tienen menú del día.
3. Comprobar a qué hora abren y cierran de verdad los bares y restaurantes del radio (los datos abiertos casi no traen horarios).
4. Ver por qué acera sale la gente del metro o de las paradas de autobús y si pasa por delante del local o va hacia otro lado.
5. Recorrer el radio y contar los bares, cafeterías y restaurantes reales: OpenStreetMap solo tiene 25.
6. Preguntar a un hostelero de la zona qué días y meses flojean (agosto, fiestas locales, puentes) y cuánto pesa la terraza en su negocio.


### Recomendaciones · 40.212861, -3.852623 · Griñón · radio 300 m

> Orientaciones a partir de datos abiertos y supuestos explícitos, no garantías. Toda cifra de personas es una estimación.

#### A quién vender

- **En laborable, orientar la oferta sobre todo a vecinos (41 %), padres y niños (35 %), pacientes (23 %).** *(confianza media; estimación)*
  - Vecinos: 33 % de la gente que pasa cerca en el día (~1.016 pasos) y 41 % de los clientes posibles (propensión a pararse 1,0); su franja fuerte es «tarde-noche».
  - Padres y niños: 46 % de la gente que pasa cerca en el día (~1.422 pasos) y 35 % de los clientes posibles (propensión a pararse 0,6); su franja fuerte es «primera hora de la mañana».
  - Pacientes: 18 % de la gente que pasa cerca en el día (~568 pasos) y 23 % de los clientes posibles (propensión a pararse 1,0); su franja fuerte es «media mañana».
- **En sábado, orientar la oferta sobre todo a vecinos (92 %).** *(confianza media; estimación)*
  - Vecinos: 90 % de la gente que pasa cerca en el día (~813 pasos) y 92 % de los clientes posibles (propensión a pararse 1,0); su franja fuerte es «tarde-noche».

Clientes principales por franja (peso ≥ 10 %, estimación):

| Franja | Laborable | Sábado |
|---|---|---|
| primera hora de la mañana | Padres y niños 70 %, Vecinos 22 % (~1.023) | Vecinos 91 % (~68) |
| media mañana | Pacientes 54 %, Vecinos 42 % (~397) | Vecinos 78 %, Pacientes 21 % (~252) |
| mediodía | Padres y niños 53 %, Vecinos 30 %, Pacientes 15 % (~609) | Vecinos 89 % (~170) |
| media tarde | Padres y niños 53 %, Vecinos 26 %, Pacientes 19 % (~729) | Vecinos 97 % (~152) |
| tarde-noche | Vecinos 78 %, Pacientes 17 % (~291) | Vecinos 98 % (~210) |
| noche | Vecinos 88 %, Viajeros 12 % (~33) | Vecinos 96 % (~51) |

*El perfil no modela el domingo aparte: el «fin de semana» usa el horario de transporte del sábado y costumbres genéricas de fin de semana. Aquí se presenta como «sábado».*

#### A qué hora

- **En laborable, conviene abrir en: primera hora de la mañana, media mañana, mediodía, media tarde. Horas punta: 08:00-08:59, 16:00-16:59, 14:00-14:59.** *(confianza baja; estimación)*
  - «primera hora de la mañana»: ~256 personas por hora (100 % de la mejor franja)
  - «media mañana»: ~132 personas por hora (52 % de la mejor franja)
  - «mediodía»: ~203 personas por hora (79 % de la mejor franja)
  - «media tarde»: ~243 personas por hora (95 % de la mejor franja)
  - «tarde-noche»: ~73 personas por hora (28 % de la mejor franja)
  - «noche»: ~5 personas por hora (2 % de la mejor franja)
  - Horas punta: 08:00-08:59 (~580; Padres y niños 79 %, Vecinos 16 %); 16:00-16:59 (~413; Padres y niños 79 %, Vecinos 11 %, Pacientes 8 %); 14:00-14:59 (~362; Padres y niños 73 %, Vecinos 19 %, Pacientes 7 %)
- **No hay datos suficientes para comparar con el horario de la competencia en laborable.** *(confianza baja; dato)*
  - Solo 0 de 2 locales de OpenStreetMap del radio indican su horario (mínimo 3); el censo de Madrid no tiene horarios.
- **En sábado, conviene abrir en: media mañana, mediodía, media tarde, tarde-noche. Horas punta: 11:00-11:59, 12:00-12:59, 13:00-13:59.** *(confianza baja; estimación)*
  - «primera hora de la mañana»: ~17 personas por hora (20 % de la mejor franja)
  - «media mañana»: ~84 personas por hora (100 % de la mejor franja)
  - «mediodía»: ~57 personas por hora (67 % de la mejor franja)
  - «media tarde»: ~51 personas por hora (60 % de la mejor franja)
  - «tarde-noche»: ~52 personas por hora (62 % de la mejor franja)
  - «noche»: ~7 personas por hora (9 % de la mejor franja)
  - Horas punta: 11:00-11:59 (~91; Vecinos 77 %, Pacientes 22 %); 12:00-12:59 (~90; Vecinos 78 %, Pacientes 22 %); 13:00-13:59 (~80; Vecinos 81 %, Pacientes 16 %)
- **No hay datos suficientes para comparar con el horario de la competencia en sábado.** *(confianza baja; dato)*
  - Solo 0 de 2 locales de OpenStreetMap del radio indican su horario (mínimo 3); el censo de Madrid no tiene horarios.

#### Qué vender

Momentos de consumo:

- **Laborable: desayuno (~726 clientes posibles; 34 % del total de momentos del día).** *(confianza media; estimación)*
  - Padres y niños en «primera hora de la mañana»: ~427 clientes posibles
  - Vecinos en «primera hora de la mañana»: ~220 clientes posibles
  - Pacientes en «primera hora de la mañana»: ~74 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).
- **Laborable: merienda (~565 clientes posibles; 27 % del total de momentos del día).** *(confianza media; estimación)*
  - Padres y niños en «media tarde»: ~233 clientes posibles
  - Vecinos en «media tarde»: ~192 clientes posibles
  - Pacientes en «media tarde»: ~137 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).
- **Laborable: almuerzo de media mañana (~385 clientes posibles; 18 % del total de momentos del día).** *(confianza baja; estimación)*
  - Pacientes en «media mañana»: ~213 clientes posibles
  - Vecinos en «media mañana»: ~168 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).
- **Sábado: cañas y raciones (~256 clientes posibles; 29 % del total de momentos del día).** *(confianza media; estimación)*
  - Vecinos en «mediodía»: ~152 clientes posibles
  - Vecinos en «tarde-noche»: ~102 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).
- **Sábado: almuerzo de media mañana (~251 clientes posibles; 29 % del total de momentos del día).** *(confianza media; estimación)*
  - Vecinos en «media mañana»: ~197 clientes posibles
  - Pacientes en «media mañana»: ~53 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).
- **Sábado: merienda (~149 clientes posibles; 17 % del total de momentos del día).** *(confianza media; estimación)*
  - Vecinos en «media tarde»: ~148 clientes posibles
  - Clientes posibles = gente que pasa × propensión a pararse (viajeros 0,3; padres y niños 0,6), repartida entre los momentos de su franja según la tabla TABLA_MOMENTOS de src/supuestos.py (supuesto).

Huecos de competencia (con «locales que sirven comidas», no «restaurantes» a secas):

- **No se pueden buscar huecos de competencia: en un punto típico del municipio hay menos de un local de cada tipo en 300 m según OpenStreetMap.** *(confianza baja; dato + estimación)*
  - 2 locales en el radio frente a 0,6 de media.
  - Con la cobertura baja de OpenStreetMap en el municipio, faltan datos para comparar: hay que contar los locales en persona.

Tipos de cocina:

- **No hay datos suficientes sobre tipos de cocina en el radio.** *(confianza baja; dato)*
  - Solo 0 de 2 locales de OpenStreetMap indican su cocina (hacen falta al menos 5 locales y más del 50 %).

#### A qué precio

- **Gama orientativa: media (ajustada a la clientela); por la renta de los vecinos sería media.** *(confianza baja; estimación)*
  - Renta de los vecinos: ×0,86 la media de la Comunidad → gama media.
  - Peso de cada cliente en la semana (gente × propensión a pararse): vecinos 45 %, padres y niños 32 %, pacientes 22 %.
  - Laborable: media (2,00); sábado: media (2,00); escala de 1 (económica) a 3 (alta).
  - Las gamas de universitarios, viajeros, trabajadores y deporte son supuestos (src/supuestos.py, GAMA_CLIENTE).
- **Precios del sector: en los últimos 12 meses (hasta septiembre de 2026) restaurantes y alojamiento +5,7 % frente a alimentos +3,2 %: el sector ha subido precios por encima de la materia prima. Puede servir de referencia al revisar la carta, no como regla.** *(confianza media; dato)*
  - IPC de la Comunidad de Madrid (portal): restaurantes y servicios de alojamiento +5,7 %, alimentos y bebidas no alcohólicas +3,2 %, bebidas alcohólicas +0,6 %, índice general +5,3 %.
  - **Aviso:** el grupo incluye hoteles, que han subido +18,0 %; la subida propia de bares y restaurantes probablemente sea menor.
- **No se dan precios en euros: no hay datos abiertos de cartas. Conviene comprobar en persona los precios de 3 a 5 locales del radio (café, caña, menú del día, ración) antes de fijar los propios.** *(confianza alta; dato)*
  - Ninguna fuente abierta del proyecto publica precios de cartas.

#### Riesgos y avisos

- **No se puede valorar si la competencia es alta o baja: la media del municipio es de menos de un local en 300 m.** *(confianza baja; dato + estimación)*
  - 2 locales en el radio frente a 0,6 de media (OpenStreetMap); con tan pocos locales la comparación no dice nada.
- **Cobertura baja de OpenStreetMap: probablemente hay más locales de los que se cuentan, así que la competencia real es mayor.** *(confianza media; dato)*
  - OSM registra 1,05 locales por 1.000 habitantes en el municipio, frente a 5,02 del censo oficial de Madrid capital.
- **Festivos próximos: esos días cambia el público; baja el de laborable (trabajadores, estudiantes) y el día se parece más a un sábado.** *(confianza alta; dato)*
  - 2026-12-07 (lunes): Día de la Constitución Española
  - 2026-12-08 (martes): Inmaculada Concepción
  - 2026-12-25 (viernes): Natividad del Señor
  - Fiestas locales del año en curso (orientación para el siguiente, aún sin publicar): 2026-06-17, 2026-08-14
- **Periodos sin clase: padres y niños son el 46 % de la gente de un laborable; sin clase ese público desaparece.** *(confianza media; estimación)*
  - Periodo lectivo típico (colegios): de principios de septiembre a la segunda quincena de junio; sin clase en Navidad (del 22-23 de diciembre al 7-8 de enero), en Semana Santa (unos 10 días) ni en julio y agosto.
  - El portal de la Comunidad no publica el calendario escolar: el periodo lectivo es un supuesto (src/supuestos.py).

#### Qué comprobar en persona

1. Contar durante 15 minutos la gente que pasa por delante del local en la hora punta de un laborable (08:00-08:59) y comparar con la estimación (~145 personas en 15 minutos); repetirlo en una hora floja.
2. Anotar en 3 a 5 locales del radio el precio del café, la caña, el menú del día y una ración, y si tienen menú del día.
3. Comprobar a qué hora abren y cierran de verdad los bares y restaurantes del radio (los datos abiertos casi no traen horarios).
4. Observar la salida de los colegios (14:00 y 16:00-17:00) y si las familias se quedan a merendar por la zona.
5. Recorrer el radio y contar los bares, cafeterías y restaurantes reales: OpenStreetMap solo tiene 2.
6. Preguntar a un hostelero de la zona qué días y meses flojean (agosto, fiestas locales, puentes) y cuánto pesa la terraza en su negocio.


