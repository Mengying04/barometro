# 2026-11-15 · Propuesta: tipo de local («¿Qué tipo de local?»)

**Estado: propuesta aprobada con cambios e implementada.** Lo implementado está en
[`2026-11-15-tipo-de-local.md`](2026-11-15-tipo-de-local.md). Cambios principales:

- las visitas por vecino se rebajaron a la mitad tras contrastarlas con el gasto en
  restauración de la EPF;
- se añadió el análisis de sensibilidad.

Por eso algunos resultados de este documento, sobre todo los del bar de validación en
laborable, ya no son los de la aplicación. Se conserva tal cual, como registro de la
propuesta. Todas las cifras son estimaciones, y todos los valores nuevos son supuestos.

## Punto de partida: primera validación con un hostelero

Se trata de un bar de barrio de Madrid capital, que en este documento se llama **«bar de
validación 1 (Madrid capital)»**. El bar no ha autorizado publicar su dirección: aquí no
figuran ni la dirección ni las coordenadas, ni su nombre ni el de quien lo lleva.

Según el hostelero:

- abre hacia las 8;
- no da menú del día;
- tiene carta de raciones y desayunos;
- su clientela es gente del barrio;
- tiene más clientes de 13:00 a 16:00 y de 18:00 a 20:00.

La aplicación da la hora punta de un laborable a las 8-9 h y solo coincide con el
hostelero en el fin de semana.

Diagnóstico previo de la autora: la aplicación mide bien la gente que pasa, pero cuándo hay
clientes depende del tipo de local, y hoy la aplicación da una sola respuesta para todos.

## 1. Perfil del bar de validación, sin cambiar nada

Se calculó con `perfil_horario()` tal como está hoy, con el radio de 300 m.

Elementos dentro del radio:

- centros educativos: 5;
- campus universitarios: 0;
- centros sanitarios con público: 16;
- sitios del registro de desfibriladores: 0;
- paradas de transporte (por red): 4;
- población estimada, ponderada por distancia: unas 3.300 personas.

### Laborable (pasos por hora, estimación)

«Clientes posibles» es lo que calcula hoy la aplicación: los pasos multiplicados por la
propensión a pararse de cada tipo (`PROPENSION_CONSUMO`). Universitarios, trabajadores y
deporte y eventos valen 0 todo el día, así que no se muestran.

| Hora | Padres y niños | Pacientes | Viajeros | Vecinos | **Paso total** | Clientes posibles (actual) |
|---|---|---|---|---|---|---|
| 6 | 0 | 0 | 7 | 74 | 80 | 76 |
| 7 | 54 | 0 | 11 | 332 | 397 | 368 |
| 8 | 266 | 0 | 14 | 590 | **870** | **754** |
| 9 | 124 | 13 | 13 | 442 | 592 | 533 |
| 10 | 0 | 32 | 13 | 369 | 414 | 405 |
| 11 | 0 | 32 | 13 | 369 | 414 | 405 |
| 12 | 9 | 32 | 14 | 369 | 424 | 411 |
| 13 | 9 | 26 | 13 | 442 | 490 | 477 |
| 14 | 105 | 6 | 14 | 442 | 568 | 515 |
| 15 | 63 | 0 | 14 | 295 | 372 | 337 |
| 16 | 225 | 19 | 13 | 295 | 553 | 453 |
| 17 | 122 | 32 | 13 | 442 | 609 | 551 |
| 18 | 60 | 32 | 13 | 516 | 621 | 588 |
| 19 | 45 | 26 | 13 | 516 | 600 | 573 |
| 20 | 60 | 6 | 13 | 442 | 522 | 488 |
| 21 | 45 | 0 | 9 | 332 | 386 | 362 |
| 22 | 0 | 0 | 9 | 184 | 193 | 187 |
| 23 | 0 | 0 | 6 | 88 | 94 | 90 |

### Sábado y domingo (paso total por hora, estimación)

Casi todo son vecinos: más del 95 % del paso. Los pacientes suman como mucho 19 por hora
el sábado por la mañana, y los viajeros, de 3 a 9 por hora.

| Hora | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sábado | 121 | 234 | 390 | **483** | **483** | **449** | 349 | 236 | 235 | 350 | 407 | 437 | 378 | 322 | 235 |
| Domingo | 60 | 144 | 284 | **423** | **506** | **506** | 367 | 201 | 200 | 312 | 396 | 395 | 311 | 201 | 116 |

### Horas punta que salen hoy (las tres primeras)

| Día | De la gente que pasa | De los clientes posibles (actual) |
|---|---|---|
| Laborable | 8, 18, 17 | 8, 18, 19 |
| Sábado | 11, 12, 13 | 12, 11, 13 |
| Domingo | 12, 13, 11 | 12, 13, 11 |

### Diagnóstico: confirmado, con dos correcciones

1. **La punta de las 8 de un laborable no la dan los viajeros.** Con 4 paradas de autobús,
   los viajeros son unos 14 pasos por hora. La punta sale de dos fuentes:
   - los vecinos que salen de casa (590 pasos): el reparto supuesto de los vecinos,
     `REPARTO_VECINOS`, tiene su máximo a las 8;
   - la entrada a los 5 colegios (266 pasos).

   Es «gente que va al trabajo o al colegio», pero sale andando de casa, no del transporte.
2. **Los «clientes posibles» de ahora no pueden mover la hora punta.** La propensión a
   pararse es un número por tipo de cliente, igual a todas las horas. Solo cambia el peso de
   cada tipo, no el momento del día. Por eso las horas punta de paso y de clientes posibles
   casi coinciden.

Además:

- **La punta de la tarde (17-19 h) ya sale en el paso.** Lo que falta es la de 13 a 16 h:
  a las 14 pasan 568 personas, frente a 870 a las 8. A mediodía la gente va al bar a
  propósito y se queda más rato, y eso el paso no lo recoge.
- **El fin de semana coincide** porque el paso de los vecinos y los clientes de un bar de
  barrio caen a la misma hora (el aperitivo de 11 a 14 h).
- Con este testimonio no se puede comprobar si el paso está bien medido. El hostelero
  habla de clientes, que es otra magnitud.

## 2. Propuesta: selector «¿Qué tipo de local?»

Cinco tipos:

| Clave | Nombre |
|---|---|
| `bar_barrio` | Bar de barrio (raciones y desayunos) |
| `cafeteria` | Cafetería de desayunos o café para llevar |
| `menu_dia` | Menú del día |
| `comida_llevar` | Comida para llevar |
| `restaurante_cenas` | Restaurante de cenas |

Para cada tipo habría dos supuestos nuevos en `src/supuestos.py`, todos marcados como
SUPUESTO y con su justificación.

### A. Tasa de parada por paso (tipos de cliente que no son vecinos)

Es la fracción de los pasos de cada tipo de cliente que se convierte en una visita a
locales de ese tipo, en cada tramo de horas (de la hora *a* a la hora *b*, sin incluir *b*).
Las horas que no se citan valen 0.

**Bar de barrio.** Sin menú; desayunos, almuerzo de media mañana, raciones y cañas.

| Tipo de cliente | Tasas | Justificación |
|---|---|---|
| Viajeros | 7–10: 0,01 · 10–13: 0,02 · 13–16: 0,02 · 16–18: 0,02 · 18–21: 0,04 | A las 8 van con prisa y casi no se paran en un bar de raciones; la caña a la vuelta es lo más probable |
| Trabajadores | 7–10: 0,06 · 10–12: 0,15 · 12–16: 0,10 · 17–21: 0,10 | El almuerzo (bocadillo y café) es típico de bar; sin menú, a mediodía solo raciones; caña a la salida |
| Universitarios | 8–10: 0,03 · 10–13: 0,05 · 13–16: 0,05 · 18–21: 0,08 | Buscan precio; cañas al salir |
| Padres y niños | 8–10: 0,05 · 16–18: 0,03 | Café tras dejar a los niños; se cuentan niños y adultos |
| Pacientes | 9–13: 0,05 · 16–19: 0,02 | Desayuno tras un análisis en ayunas |
| Deporte y eventos | 12–15: 0,10 · 18–23: 0,10 | Aperitivo tras el partido; cañas tras el evento |

**Cafetería de desayunos o café para llevar**

| Tipo de cliente | Tasas | Justificación |
|---|---|---|
| Viajeros | 6–10: 0,05 · 10–13: 0,03 · 13–16: 0,01 · 16–19: 0,03 · 19–21: 0,01 | El café para llevar es justo la compra de quien va al transporte |
| Trabajadores | 7–10: 0,15 · 10–12: 0,15 · 13–16: 0,05 · 16–19: 0,05 | Desayuno y pausa de media mañana; café después de comer |
| Universitarios | 8–10: 0,10 · 10–13: 0,08 · 13–16: 0,05 · 16–19: 0,06 | Café antes de clase y entre clases |
| Padres y niños | 8–10: 0,08 · 16–18: 0,06 | Café tras dejar a los niños; merienda |
| Pacientes | 8–13: 0,08 · 16–19: 0,03 | Desayuno tras un análisis en ayunas |
| Deporte y eventos | 9–13: 0,03 · 16–19: 0,03 | Poco: no es su momento |

**Menú del día**

| Tipo de cliente | Tasas | Justificación |
|---|---|---|
| Viajeros | 7–10: 0,005 · 13–16: 0,01 | Comen en su destino |
| Trabajadores | 7–10: 0,03 · 10–12: 0,05 · 13–16: 0,40 · 17–20: 0,03 | Los pasos de las 14-16 h son sobre todo de quien sale a comer (`SALEN_A_COMER`): es su cliente principal |
| Universitarios | 13–16: 0,15 | Menú barato al cambiar de turno |
| Padres y niños | 0 | A mediodía recogen a los niños y comen en casa |
| Pacientes | 9–12: 0,02 · 13–16: 0,03 | Poco |
| Deporte y eventos | 13–16: 0,05 | Comida tras el partido |

**Comida para llevar**

| Tipo de cliente | Tasas | Justificación |
|---|---|---|
| Viajeros | 13–16: 0,02 · 19–22: 0,03 | Cena para casa al volver |
| Trabajadores | 13–16: 0,10 · 18–21: 0,03 | Comida rápida en la pausa |
| Universitarios | 13–16: 0,08 · 19–22: 0,05 | Comida barata |
| Padres y niños | 13–15: 0,01 · 16–18: 0,01 | Casi nada |
| Pacientes | 13–16: 0,02 | Poco |
| Deporte y eventos | 13–15: 0,05 · 19–23: 0,08 | Comida o cena tras el evento |

**Restaurante de cenas**

| Tipo de cliente | Tasas | Justificación |
|---|---|---|
| Viajeros | 20–23: 0,005 | Casi nada: van a casa |
| Trabajadores | 13–16: 0,05 · 20–23: 0,02 | Alguna comida de trabajo |
| Universitarios | 20–23: 0,02 | Poco: por precio |
| Padres y niños | 0 | — |
| Pacientes | 0 | — |
| Deporte y eventos | 20–24: 0,10 | Cena tras el evento |

### B. Vecinos que van a propósito

Los vecinos dejan de contarse por los pasos. Se cuentan así:

> clientes vecinos = población del radio × visitas por vecino y día × reparto por horas
> (propio de cada tipo de local y de cada tipo de día)

Así entra la gente del barrio que va al local aunque no pase por delante, y no se cuenta
dos veces a quien pasa por delante y entra.

| Tipo de local | Visitas por vecino y día (laborable / sábado / domingo) | Reparto por horas (supuesto) |
|---|---|---|
| Bar de barrio | 0,15 / 0,20 / 0,20 | Laborable: desayuno moderado (7-12 h), máximos de 13 a 16 (raciones, aperitivo) y de 18 a 21 (cañas). Sábado y domingo: aperitivo de 12 a 15 y tarde de 18 a 21 |
| Cafetería | 0,12 / 0,12 / 0,10 | Laborable: máximo de 8 a 10, media mañana y merienda de 17 a 19; cierra hacia las 21. Fin de semana: de 10 a 12 y merienda |
| Menú del día | 0,05 / 0,04 / 0,04 | Casi todo de 13 a 16, con el máximo a las 14 |
| Comida para llevar | 0,04 / 0,07 / 0,07 | De 13 a 15 y de 20 a 23 |
| Restaurante de cenas | 0,02 / 0,06 / 0,04 | Laborable y sábado: sobre todo de 21 a 23. Domingo: comida de 14 a 16 |

Pesos por hora del prototipo. Se normalizan para que cada día sume 1, y las horas que no
se citan valen 0.

- **Bar de barrio**
  - Laborable: 7: 3 · 8: 6 · 9: 7 · 10: 7 · 11: 6 · 12: 6 · 13: 9 · 14: 10 · 15: 8 ·
    16: 4 · 17: 5 · 18: 8 · 19: 9 · 20: 7 · 21: 4 · 22: 2.
  - Sábado: 8: 2 · 9: 5 · 10: 7 · 11: 8 · 12: 10 · 13: 12 · 14: 11 · 15: 7 · 16: 4 ·
    17: 5 · 18: 7 · 19: 8 · 20: 7 · 21: 5 · 22: 2.
  - Domingo: 8: 2 · 9: 4 · 10: 6 · 11: 9 · 12: 13 · 13: 15 · 14: 12 · 15: 6 · 16: 3 ·
    17: 5 · 18: 7 · 19: 7 · 20: 6 · 21: 3 · 22: 2.
- **Cafetería**
  - Laborable: 7: 8 · 8: 13 · 9: 13 · 10: 11 · 11: 9 · 12: 6 · 13: 4 · 14: 3 · 15: 4 ·
    16: 6 · 17: 8 · 18: 8 · 19: 5 · 20: 2.
  - Sábado: 8: 4 · 9: 9 · 10: 13 · 11: 13 · 12: 10 · 13: 6 · 14: 3 · 15: 4 · 16: 7 ·
    17: 10 · 18: 10 · 19: 7 · 20: 4.
  - Domingo: como el sábado, con 8: 3, 9: 8, 10: 13, 11: 14 y 12: 11.
- **Menú del día**
  - Laborable: 8: 4 · 9: 5 · 10: 4 · 11: 3 · 12: 3 · 13: 12 · 14: 30 · 15: 22 · 16: 4 ·
    17: 3 · 18: 4 · 19: 4 · 20: 2.
  - Sábado: 10: 4 · 11: 5 · 12: 7 · 13: 14 · 14: 28 · 15: 22 · 16: 5 · 19: 5 · 20: 6 ·
    21: 4.
  - Domingo: 10: 3 · 11: 5 · 12: 8 · 13: 16 · 14: 30 · 15: 24 · 16: 6 · 20: 4 · 21: 4.
- **Comida para llevar**
  - Laborable: 12: 4 · 13: 12 · 14: 16 · 15: 8 · 19: 6 · 20: 16 · 21: 24 · 22: 12 · 23: 2.
  - Sábado: igual, con 14: 14 y 22: 14.
  - Domingo: 12: 5 · 13: 15 · 14: 18 · 15: 9 · 19: 6 · 20: 16 · 21: 20 · 22: 9 · 23: 2.
- **Restaurante de cenas**
  - Laborable: 13: 6 · 14: 12 · 15: 7 · 20: 10 · 21: 35 · 22: 25 · 23: 5.
  - Sábado: 13: 6 · 14: 15 · 15: 12 · 16: 3 · 20: 8 · 21: 25 · 22: 25 · 23: 6.
  - Domingo: 13: 10 · 14: 28 · 15: 22 · 16: 5 · 20: 8 · 21: 18 · 22: 9.

### C. Qué ofrece cada tipo de local en cada franja

Los clientes de cada franja se reparten entre los momentos de consumo que encajan a la vez
con el cliente (`TABLA_MOMENTOS`) y con el local. Si no encaja ninguno, se usan los del
local en esa franja. Habría dos momentos nuevos: **«comida para llevar»** y **«comida a la
carta»**.

| Franja | Bar de barrio | Cafetería | Menú del día | Comida para llevar | Restaurante de cenas |
|---|---|---|---|---|---|
| Primera hora | desayuno | desayuno | desayuno | — | — |
| Media mañana | almuerzo | almuerzo | almuerzo | — | — |
| Mediodía | cañas y raciones | comida para llevar | menú del día (sábado y domingo: cañas y raciones) | comida para llevar | comida a la carta |
| Media tarde | merienda, cañas y raciones | merienda | merienda | — | — |
| Tarde-noche | cañas y raciones | merienda | cañas y raciones | comida para llevar | cenas |
| Noche | copas | — | — | — | — |

Solo se ha probado el bar de barrio. Las columnas de los otros cuatro tipos son la
propuesta y todavía no se han calculado.

### Lo que esta propuesta no hace

- **No calibra con este bar.** Un solo bar no basta para calibrar. Los valores salen de
  costumbres generales (horas de las comidas en España, `COMIDAS`, y horarios de cada tipo
  de cliente), pero **se escribieron sabiendo lo que dijo el hostelero**. Por eso este bar
  no cuenta como una validación independiente, y no se ha ajustado ningún valor para que
  encaje mejor.
- **Las cifras de clientes son de toda la zona.** Son visitas posibles al conjunto de
  locales de ese tipo en 300 m, no a un solo local; habría que repartirlas entre los que
  haya.
- **El modelo cuenta visitas que llegan, no lo lleno que está el local.** Puede que «más
  clientes» quiera decir más ocupación, y a mediodía la gente se queda más rato.
- **Los restaurantes de cenas atraen gente de más de 300 m,** y los pedidos a domicilio no
  son visitas: la parte de destino queda corta en esos tipos.

## 3. Cómo cambiaría la aplicación (propuesta)

- **`perfil_horario()` no cambia** (sigue midiendo la gente que pasa). Una función nueva
  calcula, a partir del perfil, los clientes de cada tipo de local por hora y franja.
- **`recomendar(..., tipo_local=None)`.** Con un tipo elegido, «a qué hora» (franjas para
  abrir y horas punta), «a quién» y «qué ofrecer» se calculan con los clientes de ese tipo.
  El detalle guarda las dos horas punta: la de paso y la de clientes.
- **Aplicación web, PDF y comparación:** el selector «¿Qué tipo de local?» y dos preguntas
  separadas:
  - «¿Cuándo pasa más gente?» (paso, como ahora);
  - «¿Cuándo tendrías más clientes?» (para ese tipo de local).
- **Servidor MCP:** un parámetro opcional `tipo_local` en las herramientas que recomiendan
  y comparan.
- **Sin tipo elegido:** se usa el cálculo de hoy (paso × propensión) y se avisa de que el
  resultado es general.
- **Comprobar en persona:** se añadiría contar los clientes dentro del local en la hora
  punta de clientes.
- **Pendiente de decidir:** la gama de precios. La propuesta es dejarla como está (paso ×
  propensión), porque no estaba en el encargo. Otra opción es que use los clientes del tipo
  elegido.

## 4. Resultados del prototipo con «bar de barrio»

Se calcularon con un prototipo aparte, fuera del repositorio, que aplica los supuestos de
arriba al perfil de hoy.

### Horas punta (las tres primeras, ordenadas por hora)

| Punto | Laborable: antes → después | Sábado: antes → después | Domingo: antes → después |
|---|---|---|---|
| Campus de Vicálvaro | 8, 9, 14 → **14, 18, 19** | 11, 12, 13 → 12, 13, 14 | 11, 12, 13 → 12, 13, 14 |
| Centro de Fuenlabrada | 7, 8, 9 → **18, 19, 20** | 11, 12, 13 → 18, 19, 20 | 11, 12, 13 → 12, 13, 14 |
| Plaza Mayor de Griñón | 8, 14, 16 → 8, 9, 16 | 11, 12, 13 → 12, 13, 14 | 11, 12, 13 → 12, 13, 14 |
| Bar de validación 1 | 8, 17, 18 → **13, 14, 19** | 11, 12, 13 → 12, 13, 14 | 11, 12, 13 → 12, 13, 14 |

«Antes» son las horas punta de paso. Coinciden con las de clientes posibles de hoy, salvo
en el bar de validación en laborable (8, 18, 19).

### Clientes posibles por hora con «bar de barrio» (estimación, toda la zona)

En laborable:

| Hora | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Vicálvaro | 18 | 54 | 54 | 54 | 48 | 48 | 59 | **80** | 68 | 31 | 34 | **72** | **74** | 67 | 14 | 7 |
| Fuenlabrada | 43 | 56 | 53 | 62 | 58 | 57 | 72 | 82 | 85 | 56 | 62 | **121** | **119** | **112** | 13 | 7 |
| Griñón | 2 | **28** | **17** | 9 | 8 | 8 | 7 | 8 | 6 | **14** | 7 | 7 | 7 | 5 | 3 | 2 |
| Bar de validación 1 | 15 | 43 | 42 | 36 | 31 | 31 | **45** | **50** | 40 | 27 | 29 | 41 | **45** | 35 | 20 | 10 |

Sábado y domingo en el bar de validación:

| Hora | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Sábado | 13 | 33 | 47 | 54 | **68** | **80** | **73** | 47 | 27 | 33 | 47 | 54 | 47 | 33 | 13 |
| Domingo | 13 | 27 | 40 | 60 | **86** | **100** | **80** | 40 | 20 | 33 | 47 | 47 | 40 | 20 | 13 |

Total del día y de dónde salen los clientes (bar de barrio):

| Punto | Laborable | Sábado | Domingo |
|---|---|---|---|
| Vicálvaro | 782 (vecinos 45 %, viajeros 27 %, universitarios 22 %) | 606 (vecinos 77 %, viajeros 22 %) | 582 (vecinos 81 %, viajeros 19 %) |
| Fuenlabrada | 1.057 (viajeros 65 %, vecinos 32 %) | 871 (vecinos 52 %, viajeros 47 %) | 786 (vecinos 58 %, viajeros 42 %) |
| Griñón | 137 (vecinos 56 %, padres y niños 32 %, pacientes 12 %) | 104 (vecinos 97 %) | 102 (vecinos 100 %) |
| Bar de validación 1 | 539 (vecinos 92 %, padres y niños 6 %) | 669 (vecinos 99 %) | 666 (vecinos 100 %) |

### Qué ofrecer (momentos que se recomiendan: al menos la mitad que el más fuerte del día)

Las cifras son clientes posibles.

| Punto | Día | Antes | Después (bar de barrio) |
|---|---|---|---|
| Vicálvaro | Laborable | desayuno 3.210, cañas y raciones 2.494, merienda 2.288, almuerzo 2.246, menú del día 1.805 | cañas y raciones 370 |
| | Sábado | cañas y raciones 1.711, almuerzo 1.308, merienda 1.075 | cañas y raciones 307 |
| | Domingo | cañas y raciones 1.546, almuerzo 1.151, merienda 950 | cañas y raciones 292, almuerzo 152 |
| Fuenlabrada | Laborable | desayuno 4.426, cañas y raciones 3.334, merienda 2.918, almuerzo 2.467 | cañas y raciones 490 |
| | Sábado | cañas y raciones 2.758, almuerzo 2.150, merienda 1.888 | cañas y raciones 430 |
| | Domingo | cañas y raciones 2.374, almuerzo 1.795, merienda 1.587 | cañas y raciones 387 |
| Griñón | Laborable | desayuno 724, merienda 564, almuerzo 384 | desayuno 47, cañas y raciones 37, merienda 27, almuerzo 25 |
| | Sábado | cañas y raciones 256, almuerzo 251, merienda 149 | cañas y raciones 53, almuerzo 28 |
| | Domingo | cañas y raciones 239, almuerzo 183, merienda 137 | cañas y raciones 52, almuerzo 28 |
| Bar de validación 1 | Laborable | desayuno 1.731, merienda 1.592, cañas y raciones 1.340, almuerzo 1.215 | cañas y raciones 244 (después: desayuno, almuerzo y merienda, unos 100 cada uno) |
| | Sábado | cañas y raciones 1.678, almuerzo 1.341, merienda 975 | cañas y raciones 347 |
| | Domingo | cañas y raciones 1.562, almuerzo 1.200, merienda 895 | cañas y raciones 340, almuerzo 186 |

Las cifras de antes y de después no se comparan entre sí:

- antes son pasos × propensión, una escala relativa;
- después son visitas posibles estimadas.

Con un tipo de local elegido, «qué ofrecer» pasa a ser un orden dentro de lo que ese local
vende. Para un bar de barrio sale lo esperable: cañas y raciones primero.

### Franjas en las que conviene abrir

Cada letra es una franja, de primera hora a noche:

- A = abrir;
- v = valorar;
- − = no compensa.

| Punto | Laborable: antes → después | Sábado: antes → después | Domingo: antes → después |
|---|---|---|---|
| Vicálvaro | AAAAA− → vAAAA− | AAAAA− → −AAAA− | vAAAA− → −AAAv− |
| Fuenlabrada | AAAAA− → vAAAA− | AAAAA− → −AAAA− | AAAAA− → −AAAA− |
| Griñón | AAAA−− → AAAAv− | −AAAA− → −AAAA− | −AAAA− → −AAvv− |
| Bar de validación 1 | AAAAA− → AAAAA− | −AAAA− → −AAAA− | −AAAA− → −AAvv− |

### Observaciones

- **Vicálvaro:** la punta pasa de la entrada a clase y del transporte (8-9 h) a la comida y
  a la tarde (14 h y 18-19 h).
- **Fuenlabrada:** el resultado depende casi solo de la tasa de los viajeros, que son el
  65 % de los clientes del laborable. La caña de vuelta (0,04 de 18 a 21 h), frente a
  0,01 por la mañana, decide la hora punta. Es el punto más sensible a los supuestos.
- **Griñón:** sigue mandando la entrada al colegio (8-9 h) porque viven pocos vecinos en el
  radio y los padres y niños pesan mucho.

## ¿Coincide el bar de validación con el hostelero?

**En parte, y por poco.**

- En laborable salen las 13, 14 y 19 h, dentro de los tramos del hostelero (de 13 a 16 y
  de 18 a 20).
- La diferencia con la mañana es mínima: unos 45 a 50 clientes a las 13, 14 y 19 h,
  frente a 43 a las 8 y 42 a las 9. Un cambio pequeño en cualquier supuesto podría
  devolver la punta a las 8.
- El fin de semana sigue coincidiendo (12 a 14 h, junto al 11 a 13 h de antes).

Conclusión propuesta para `docs/validacion.md`: «coincide parcialmente; un solo bar no
basta para calibrar; hacen falta más bares de distintos tipos y zonas».

## Pendiente de confirmar antes de implementar

1. Si valen los cinco tipos y los valores de las tablas, o qué se cambia.
2. Si la gama de precios sigue como está o pasa a usar los clientes del tipo elegido.
3. Si las cifras de clientes se muestran como «visitas posibles para todos los locales de
   ese tipo en 300 m».

Después de la confirmación se haría lo siguiente:

- la implementación;
- `docs/validacion.md`, enlazado desde la sección de rigor del README;
- el registro `docs/registro/2026-11-15-tipo-de-local.md`;
- el commit, sin push.

## Fuentes

No hay fuentes nuevas. Se usa el perfil por horas de hoy (fuentes en `docs/fuentes.md`).
El testimonio del hostelero es una comunicación personal: no se publica ni su local, ni su
dirección, ni su nombre.
