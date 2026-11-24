# Validación con hosteleros

Aquí se anota cada vez que un hostelero cuenta cómo funciona su local y se compara con lo
que dice BARómetro. Se recoge lo siguiente:

- qué dijo;
- qué decía la aplicación antes del cambio que provocó;
- qué dice después;
- si coincide.

Por privacidad, no se escriben direcciones, coordenadas ni nombres, ni del local ni de
quien lo lleva. Cada bar se llama solo por un número y por el tipo de zona.

**Lo que esto no es:** una calibración. Con un solo bar no se pueden ajustar los
supuestos. Si un valor se escribe conociendo lo que dijo un hostelero, ese bar deja de
servir para comprobarlo, y se dice en la conclusión.

## Resultados

| Fecha | Zona y tipo de local | Lo que dice el hostelero | Lo que decía la aplicación antes | Lo que dice después (tipo «bar de barrio») | Conclusión |
|---|---|---|---|---|---|
| 2026-11-15 | **Bar de validación 1 (Madrid capital).** Zona residencial con colegios cerca y solo autobús: casi todo el paso son vecinos. Bar de barrio que abre hacia las 8, sin menú del día, con carta de raciones y desayunos; lo frecuenta gente del barrio | Laborable: más clientes de 13:00 a 16:00 y de 18:00 a 20:00 | «¿Cuándo hay más gente?»: a las 8 y de 17 a 19 (gente que pasa, una sola respuesta para todos los locales). Fin de semana: de 11 a 14 | «¿Cuándo tendrías más clientes?», laborable: **de 8 a 10 y a las 14, poco fiable (cambia con poco)**. Con los vecinos pesando el doble, o la gente que pasa la mitad, sale de 13 a 15 y a las 19. Sábado y domingo: de 12 a 15. «Qué ofrecer»: cañas y raciones, 43 %; desayuno, 20 %; merienda, 19 %; almuerzo, 18 % | **Coincide parcialmente.** Coinciden las 14 h y el fin de semana. La punta de la mañana sigue saliendo primera en laborable, aunque la aplicación avisa de que esa hora es poco fiable. **Advertencia:** los supuestos se escribieron conociendo su testimonio, así que **no cuenta como validación independiente** |

## Notas sobre el bar de validación 1

**Diagnóstico.** La aplicación da bien la gente que pasa por delante, pero cuándo hay
clientes depende del tipo de local, y daba una sola respuesta para todos.

- La punta de las 8 no venía del transporte: los viajeros son unos 14 por hora. Venía de
  los vecinos que salen de casa y de la entrada a los colegios.
- La «propensión a pararse» de antes vale lo mismo a todas las horas, así que no podía
  mover la hora punta.

De ahí salió el selector «¿Qué tipo de local?».

**Por qué no coincide del todo.**

- La primera propuesta de supuestos daba en laborable las 13, 14 y 19 h, justo los tramos
  del hostelero.
- Al contrastar las visitas de los vecinos con el gasto medio por persona en restauración
  (Encuesta de Presupuestos Familiares), esa propuesta suponía el 95 % del gasto solo en los
  300 m alrededor de casa. Eso no es coherente, y se rebajaron las visitas a la mitad.
- Con eso, en esta zona pesan más los padres que toman café tras dejar a los niños, y la
  mañana vuelve a quedar primera por poco: 29 visitas posibles a las 8 frente a 27 a las 14.
- No se ha retocado nada para que el bar encaje.

**Qué haría falta.** Más bares, de distintos tipos y zonas, contados en persona (clientes
por hora durante una semana) y no solo por testimonio. Eso sí permitiría calibrar.

Todo el detalle, con las tablas de antes y después:

- [`registro/2026-11-15-propuesta-tipo-de-local.md`](registro/2026-11-15-propuesta-tipo-de-local.md)
  (diagnóstico y propuesta);
- [`registro/2026-11-15-tipo-de-local.md`](registro/2026-11-15-tipo-de-local.md) (lo que se
  implementó).

## Contraste con aforos de peatones (Madrid capital, 2023)

Además de los hosteleros, la gente que pasa del modelo se ha contrastado con los conteos
por hora de las 30 estaciones permanentes de peatones del Ayuntamiento de Madrid
([`src/contraste_aforos.py`](../src/contraste_aforos.py); detalle en
[`registro/2026-11-24-contraste-aforos-peatones.md`](registro/2026-11-24-contraste-aforos-peatones.md)).
Sin cambiar ningún supuesto:

- **Laborable: no coincide la forma del día.** El modelo pone la punta a las 8 en todas
  las estaciones; las aceras la tienen por la tarde o a mediodía. Durante el día (7 a 22 h)
  la correlación es nula. Es lo mismo que se vio con el bar de validación 1.
- **Fin de semana: la forma coincide** (correlación de 0,8 de mediana), **pero el modelo da
  la mitad de gente que en laborable, y las aceras, más.**
- **Orden entre zonas: regular** (Spearman 0,39). El modelo acierta los extremos, pero pone
  arriba varios puntos que en la acera cuentan poco.

Las cifras absolutas no se comparan: la estación cuenta una acera y el modelo, un círculo
de 300 m. Solo hay estaciones en Madrid capital, la mitad en el distrito Centro.

**Qué significa para la aplicación.**

- **La hora punta de paso en laborable es poco fiable,** sobre todo en calles comerciales y
  de paseo, donde las aceras se llenan por la tarde.
- **El contraste no cubre zonas como los tres ejemplos.** La mitad de las estaciones están
  en el distrito Centro, y ninguna en una zona como el campus de Vicálvaro, el centro de
  Fuenlabrada o la plaza mayor de Griñón.
- **«¿Cuándo tendrías más clientes?» no depende solo del paso:** suma a los vecinos que van
  a propósito. En Vicálvaro y Fuenlabrada, con «bar de barrio», sale por la tarde. Aun así,
  hereda este sesgo de la mañana.

