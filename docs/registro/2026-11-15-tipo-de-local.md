# 2026-11-15 · Tipo de local: «¿Cuándo tendrías más clientes?»

## Punto de partida

La primera validación con un hostelero (un bar de barrio de Madrid capital, «bar de
validación 1») mostró que la aplicación daba una sola respuesta para todos los locales.
Medía la gente que pasa, pero cuándo hay clientes depende del tipo de local.

El diagnóstico, la propuesta y sus tablas están en
[`2026-11-15-propuesta-tipo-de-local.md`](2026-11-15-propuesta-tipo-de-local.md). La autora
aprobó la propuesta con siete cambios, y este registro cuenta qué se ha hecho con cada uno.

**Privacidad del bar.** No figuran su dirección, sus coordenadas ni ningún nombre:

- en ningún fichero del repositorio;
- en los scripts de comprobación: las coordenadas se pasaron por variables de entorno.

Para situar el punto se consultó la dirección a CartoCiudad, igual que hace la
aplicación, sin guardarla. Se ha buscado en todo el repositorio y no aparece.

## Qué se ha hecho

### El selector y lo que cambia

En la aplicación hay un selector **«¿Qué tipo de local?»**, siempre visible encima de las
respuestas (Resumen, Informe completo y comparación), con cinco tipos:

- bar de barrio (raciones y desayunos);
- cafetería de desayunos o café para llevar;
- menú del día;
- comida para llevar;
- restaurante de cenas.

El tipo se guarda en la sesión y se mantiene al cambiar de dirección. Cambiar de tipo no
recalcula el perfil: solo las recomendaciones, que se guardan por tipo.

**Con un tipo elegido:**

- **«¿Cuándo pasa más gente?»** sigue igual (la gente que pasa).
- **«¿Cuándo tendrías más clientes?»** sale de los clientes posibles de ese tipo de
  local. En la tarjeta del Resumen es la pregunta principal, y debajo se recuerda cuándo
  pasa más gente.
- **A quién, a qué hora (franjas para abrir, horas con más clientes, huecos horarios) y qué
  ofrecer** usan los clientes de ese tipo de local.
- **La comparación** añade la fila «Cuándo tendrías más clientes». En «Qué conviene
  ofrecer» compara los clientes posibles de todo el día.
- **El PDF** dice el tipo de local y añade «Clientes posibles por horas».
- **El servidor MCP** acepta `tipo_local` en `recomendar_local` y `comparar_locales`.
- **La gama de precios y los riesgos** no cambian (punto 5).

**Sin tipo elegido** el resultado es el de antes. La aplicación pide el tipo y avisa:
«Resultado general. Para cualquier bar o restaurante: cuenta la gente que pasa. Elige el
tipo de local para saber cuándo tendrías más clientes». El mismo aviso va en el porqué de
«a qué hora», en el PDF y en el servidor MCP (`general: true` y `aviso_general`).

### Cómo se calculan los clientes (`src/tipo_local.py`)

El perfil por horas no cambia: sigue contando gente que pasa. Para un tipo de local:

- **Gente que pasa** (todos los tipos de cliente menos los vecinos): pasos de cada hora ×
  **tasa de parada** de ese tipo de local, tipo de cliente y hora (`TASA_PARADA`).
- **Vecinos que van a propósito**, aunque no pasen por delante: población del radio ×
  **visitas por vecino y día** (`VISITAS_VECINO`) × **reparto por horas**
  (`REPARTO_VISITAS_VECINO`). No se usan sus pasos, para no contar dos veces a quien pasa y
  entra.
- **Qué ofrecer:** los clientes de cada franja se reparten entre los momentos que encajan
  a la vez con el cliente (`TABLA_MOMENTOS`) y con lo que vende el local en esa franja
  (`MOMENTOS_LOCAL`).
  - Hay dos momentos nuevos, solo para los tipos de local: «comida para llevar» y «comida a
    la carta».
  - En sábado y domingo, en un local de menú del día el menú pasa a «comida a la carta».

Los valores son los de la propuesta, con un cambio: las visitas por vecino, que se
rebajaron (punto 1). Todos están en `src/supuestos.py`, sección «TIPO DE LOCAL», marcados
como SUPUESTO y con su porqué. **No se ha ajustado ningún valor para que encaje el bar de
validación.**

Las cifras son **«visitas posibles para todos los locales de ese tipo en 300 m»**, no las
de un local, y así se dicen siempre.

## Los siete cambios pedidos

### 1. Contraste de las visitas con el gasto en restauración (EPF)

**Dato:** gasto medio por persona de los hogares en restauración en la Comunidad de
Madrid. Encuesta de Presupuestos Familiares, portal de la Comunidad; ya se usaba en el
bloque «Mercado». Último año publicado, 2025: **1.239,81 €** por persona y año.

**Precio medio por visita y persona** (SUPUESTO, euros de 2026, `PRECIO_VISITA`):

| Tipo de local | Precio | Por qué |
|---|---|---|
| Bar de barrio | 5 € | Café con tostada o caña con tapa (3-4 €), a veces una ración compartida |
| Cafetería o café para llevar | 3,5 € | Café y bollería, o café para llevar |
| Menú del día | 14 € | Lo habitual en Madrid está entre 12 y 16 € |
| Comida para llevar | 10 € | Un plato o un menú para llevar |
| Restaurante de cenas | 30 € | Cena a la carta |

Los precios solo sirven para este contraste y nunca se enseñan. La EPF es de 2025 y los
precios, de 2026: con la subida de la restauración, el contraste exagera algo la parte del
gasto, es decir, va del lado prudente.

**Criterio de coherencia.**

- Las visitas de los vecinos a los cinco tipos juntos no pueden superar el gasto.
- Además, para ser coherentes, no pueden pasar de la **mitad** (`PARTE_GASTO_CERCA_DE_CASA`,
  SUPUESTO). El resto se gasta cerca del trabajo o del centro de estudios, en el ocio fuera
  del barrio y en viajes y vacaciones. No hay dato abierto de dónde se gasta.

**Resultado.**

| | Visitas por vecino (laborable / sábado / domingo) | Visitas al año | € por persona y año |
|---|---|---|---|
| **Propuesta inicial** (todos los tipos) | bar 0,15/0,20/0,20 · cafetería 0,12/0,12/0,10 · menú 0,05/0,04/0,04 · llevar 0,04/0,07/0,07 · cenas 0,02/0,06/0,04 | ≈150 | **≈1.180 € (95 % del gasto)** |
| Bar de barrio | 0,08 / 0,10 / 0,10 | 31 | 156 € |
| Cafetería | 0,06 / 0,06 / 0,05 | 21 | 75 € |
| Menú del día | 0,025 / 0,02 / 0,02 | 9 | 120 € |
| Comida para llevar | 0,02 / 0,035 / 0,035 | 9 | 89 € |
| Restaurante de cenas | 0,01 / 0,03 / 0,02 | 5 | 156 € |
| **Ajustado** (todos los tipos) | | 75 | **≈597 € (48 % del gasto)** |

La propuesta inicial no superaba el gasto, pero **no era coherente**: dejaba casi nada para
lo que se gasta lejos de casa. Se dividieron todas las visitas por 2, más o menos, y se
redondearon. La forma del día de cada tipo de local no cambia; sí el peso de los vecinos
frente a la gente que pasa.

`src/comprobar_datos.py` lo comprueba ahora en cada ejecución (comprobación nueva número
38). Si alguien sube las visitas por encima del límite, falla.

**Efecto en el bar de validación.** Con las visitas rebajadas pesan más los padres que
toman café tras dejar a los niños, y en laborable la mañana vuelve a quedar primera por
poco. Ver «Bar de validación 1» abajo.

### 2. Análisis de sensibilidad

Para cada tipo de local y día se repite el cálculo en cuatro casos:

- las tasas de parada por 0,5;
- las tasas de parada por 2;
- las visitas de los vecinos por 0,5;
- las visitas de los vecinos por 2.

Multiplicar las dos a la vez por lo mismo no cambia ninguna hora, porque solo cuenta la
proporción entre ellas. Por eso «tasas × 0,5» da lo mismo que «visitas × 2», y «tasas × 2»,
lo mismo que «visitas × 0,5».

**Cuándo se considera que «cambia con poco».** Tienen que darse tres cosas en alguno de
los cuatro casos:

- la hora con más clientes cae en otra franja del día;
- está a más de una hora de la de antes;
- cambian al menos dos de las tres horas que se enseñan.

Entonces la fiabilidad del horario de clientes es **baja**, y la aplicación lo dice:

- en la tarjeta: «Cambia con poco: compruébalo»;
- en la explicación: «Ojo: … es poco fiable: cuenta tú los clientes»;
- en el porqué, con los casos que la cambian;
- en el PDF: «(cambia con poco)»;
- en el servidor MCP: `sensibilidad.estable`.

Si no cambia, la fiabilidad es la del horario de paso de los tipos de cliente que pesan,
como mucho media, porque todo son supuestos.

Al ajustar el criterio se descartaron dos versiones más simples:

- «otra franja» a secas marcaba como inestable pasar de las 9 a las 10, que solo cruza el
  borde entre dos franjas;
- también marcaba casos en los que las tres horas que se enseñan eran las mismas.

**Dónde cambian las horas con más clientes.** Tres horas con más clientes en cada caso.
«**» marca un cambio que cuenta como «cambia con poco». Se muestran todas las filas del
bar de barrio y, de los demás tipos, solo las que cambian en algo.

| Punto | Tipo de local | Día | Supuestos tal cual | Tasas × 0,5 | Tasas × 2 | Visitas × 0,5 | Visitas × 2 | ¿Estable? |
|---|---|---|---|---|---|---|---|---|
| Vicálvaro | Bar de barrio | laborable | 14, 18, 19 | 14, 18, 19 | 14, 18, 19 | 14, 18, 19 | 14, 18, 19 | sí |
| Vicálvaro | Bar de barrio | sábado | 13, 19, 20 | 12, 13, 14 | 18, 19, 20 | 18, 19, 20 | 12, 13, 14 | sí |
| Vicálvaro | Bar de barrio | domingo | 12, 13, 14 | 12, 13, 14 | 13, 18, 20 | 13, 18, 20 | 12, 13, 14 | sí |
| Fuenlabrada | Bar de barrio | laborable | 18, 19, 20 | igual | igual | igual | igual | sí |
| Fuenlabrada | Bar de barrio | sábado | 18, 19, 20 | igual | igual | igual | igual | sí |
| Fuenlabrada | Bar de barrio | domingo | 18, 19, 20 | 12, 13, 14 ** | 18, 19, 20 | 18, 19, 20 | 12, 13, 14 ** | **no** |
| Fuenlabrada | Comida para llevar | domingo | 19, 20, 21 | 14, 20, 21 | igual | igual | 14, 20, 21 | sí |
| Fuenlabrada | Restaurante de cenas | sábado | 20, 21, 22 | 14, 21, 22 | igual | igual | 14, 21, 22 | sí |
| Fuenlabrada | Restaurante de cenas | domingo | 14, 15, 21 | igual | 20, 21, 22 | 20, 21, 22 | igual | sí |
| Griñón | Bar de barrio | laborable | 8, 9, 16 | igual | igual | igual | igual | sí |
| Griñón | Bar de barrio | sábado | 12, 13, 14 | igual | 11, 12, 13 | 11, 12, 13 | igual | sí |
| Griñón | Bar de barrio | domingo | 12, 13, 14 | igual | igual | igual | igual | sí |
| Griñón | Comida para llevar | laborable | 14, 16, 21 | 13, 14, 21 | 13, 14, 16 | 13, 14, 16 | 13, 14, 21 | sí |
| Griñón | Comida para llevar | sábado | 14, 20, 21 | igual | 13, 20, 21 | 13, 20, 21 | igual | sí |
| Bar de validación 1 | Bar de barrio | laborable | 8, 9, 14 | 13, 14, 19 ** | igual | igual | 13, 14, 19 ** | **no** |
| Bar de validación 1 | Bar de barrio | sábado y domingo | 12, 13, 14 | igual | igual | igual | igual | sí |
| Bar de validación 1 | Cafetería | laborable | 8, 9, 16 | 8, 9, 10 | igual | igual | 8, 9, 10 | sí |

En los cuatro puntos, los 3 tipos de día y los 5 tipos de local (60 casos), las tres horas
cambian en algún caso en 11, y solo **2 cambian con poco**:

- el bar de barrio en Fuenlabrada en domingo: de la tarde (18-20 h) al mediodía si pesan
  más los vecinos;
- el bar de barrio del bar de validación en laborable: de la mañana (8-9 h) al mediodía y la
  tarde.

Menú del día no cambia nunca, y la cafetería solo en un caso sin importancia.

### 3. «Qué ofrecer»: reparto en porcentaje

Con un tipo de local elegido, «qué ofrecer» da **todos** los momentos que vende ese
local, cada uno con su parte de los clientes posibles del día, y no solo los que llegan a
la mitad del más fuerte. Está en `que_vender.reparto` y en el porqué de cada momento. En el
Informe completo se ve en «Reparto de los clientes posibles en un día de diario».

Bar de barrio, día de diario:

| Punto | Reparto |
|---|---|
| Vicálvaro | cañas con raciones 47 %, almuerzos 19 %, meriendas 18 %, desayunos 16 % |
| Fuenlabrada | cañas con raciones 46 %, meriendas 24 %, almuerzos 16 %, desayunos 14 % |
| Griñón | desayunos 41 %, meriendas 21 %, cañas con raciones 20 %, almuerzos 18 % |
| Bar de validación 1 | cañas con raciones 43 %, desayunos 20 %, meriendas 19 %, almuerzos 18 % |

Sin tipo, «qué ofrecer» sigue como antes.

### 4. El Resumen, sin cifras de clientes

En el Resumen solo hay horas y comparaciones:

- «¿Cuándo tendrías más clientes? A las 14 y de 18 a 20» y, en el apoyo, «Pasa más gente
  de 8 a 10 y a las 14»;
- frases del tipo «Más clientes a mediodía que a primera hora, aunque a primera hora pasa
  más gente». Cada franja se compara por su mejor hora, para que diga lo mismo que las
  horas punta. Si la diferencia es de menos del 15 %, dice «parecidos».

Cambios concretos:

- **Gráfico del Resumen.** Hay un selector «Gente que pasa / Tus clientes». La vista de
  clientes no tiene eje de cifras: cada barra es su parte de la mejor hora.
- **Barras de «qué ofrecer» en el Resumen.** Ya no llevan cifras, tampoco en el resultado
  general («Lo que más te pedirían en un día de diario, de más a menos»).
- **Cifras de personas que pasan.** Se mantienen, porque no son clientes.
- **«De cada 10 posibles clientes».** Se mantiene: es una proporción entre tipos de
  cliente, no una cifra de clientes.
- **Las cifras de clientes** están en el Informe completo, siempre como «visitas posibles
  para todos los locales de ese tipo en 300 m (estimación)»:
  - la hora con más clientes, con su cifra;
  - el gráfico por horas y tipo de cliente;
  - el reparto de «qué ofrecer»;
  - la sensibilidad de cada día.

La prueba recorre las cuatro tarjetas abiertas en los tres ejemplos, con y sin tipo, y no
encuentra ninguna cifra de clientes en el Resumen.

### 5. Gama de precios

No cambia (paso × propensión a pararse, como antes).

### 6. Sin tipo elegido

Lo que hace la aplicación:

- el selector está siempre arriba y, sin tipo, pide elegirlo («Elígelo para saber cuándo
  tendrías más clientes y qué te pedirían») con el aviso de resultado general;
- la tarjeta de la hora pregunta «¿Cuándo pasa más gente?» y la explicación termina con
  «Es la gente que pasa, no los clientes: elige el tipo de local…»;
- el PDF dice «Tipo de local: sin elegir (resultado general)» y lleva el aviso.

### 7. `docs/validacion.md`

El bar de validación 1 queda registrado como **«coincide parcialmente»**, con la
advertencia de que los valores se escribieron conociendo su testimonio y de que no cuenta
como validación independiente. Está enlazado desde la sección «Rigor» del README.

## Resultados: antes y después

### Tres ejemplos y bar de validación, con «bar de barrio»

| Punto | Antes: cuándo pasa más gente (laborable) | Después: cuándo tendría más clientes un bar de barrio (laborable) | Sábado (paso → clientes) | Domingo (paso → clientes) | Fiabilidad del horario de clientes (lab. / sáb. / dom.) |
|---|---|---|---|---|---|
| Campus de Vicálvaro | 8, 9 y 14 h | **14 y 18-19 h** | 11-13 → 13, 19, 20 h | 11-13 → 12-14 h | media / media / media |
| Centro de Fuenlabrada | 7, 8 y 9 h | **18-20 h** | 11-13 → 18-20 h | 11-13 → 18-20 h | media / media / **baja** |
| Plaza Mayor de Griñón | 8, 14 y 16 h | 8, 9 y 16 h | 11-13 → 12-14 h | 11-13 → 12-14 h | media / media / media |
| Bar de validación 1 | 8, 17 y 18 h | 8, 9 y 14 h | 11-13 → 12-14 h | 11-13 → 12-14 h | **baja** / media / media |

Público principal de un bar de barrio en laborable:

- Vicálvaro: viajeros 35 %, vecinos 30 %, universitarios 28 %;
- Fuenlabrada: viajeros 76 %, vecinos 20 %;
- Griñón: padres y niños 43 %, vecinos 40 %, pacientes 16 %.

En Fuenlabrada el resultado depende mucho de la tasa de los viajeros (la caña a la vuelta).

### Los cinco tipos (tres horas con más clientes en laborable)

| Punto | Bar de barrio | Cafetería | Menú del día | Comida para llevar | Restaurante de cenas |
|---|---|---|---|---|---|
| Vicálvaro | 14, 18, 19 | 8, 9, 10 | 13, 14, 15 | 14, 15, 21 | 20, 21, 22 |
| Fuenlabrada | 18, 19, 20 | 7, 8, 9 | 13, 14, 15 | 19, 20, 21 | 20, 21, 22 |
| Griñón | 8, 9, 16 | 8, 9, 16 | 13, 14, 15 | 14, 16, 21 | 14, 21, 22 |
| Bar de validación 1 | 8, 9, 14 | 8, 9, 16 | 13, 14, 15 | 14, 20, 21 | 14, 21, 22 |

### Bar de validación 1

**Clientes posibles para un bar de barrio** (visitas posibles para todos los bares de
barrio en 300 m, estimación):

| Hora | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Laborable | 8 | **29** | **25** | 20 | 18 | 18 | 24 | **27** | 21 | 18 | 18 | 22 | 24 | 19 | 11 | 5 |
| Sábado | 0 | 7 | 17 | 24 | 28 | 34 | **40** | **37** | 23 | 13 | 17 | 24 | 27 | 24 | 17 | 7 |
| Domingo | 0 | 7 | 13 | 20 | 30 | **43** | **50** | **40** | 20 | 10 | 17 | 24 | 23 | 20 | 10 | 7 |

En laborable, el 87 % son vecinos que van a propósito y el 10 %, padres y niños.

**Frente al hostelero** (más clientes de 13 a 16 y de 18 a 20 h en laborable):

- **Coincide parcialmente.**
- Coinciden las 14 h y el fin de semana.
- La mañana (8-9 h) queda primera por poco: 29 frente a 27.
- La aplicación marca esa hora como poco fiable, porque con los vecinos pesando el doble
  sale de 13 a 15 y a las 19, justo lo que dice el hostelero.
- Con un solo bar no se puede decidir cuál de los dos pesos es el bueno, y no se ha tocado
  ningún valor para que encaje.
- La primera propuesta sí encajaba, pero no pasaba el contraste con el gasto (punto 1).

## Comprobaciones

| Comprobación | Resultado |
|---|---|
| `python src/comprobar_datos.py` | 38 comprobaciones, 0 fallos. La nueva: visitas de los vecinos, 597 € por persona y año, 48 % de 1.240 € (2025), límite 50 % |
| `python mcp/probar_cliente.py` | «todo correcto». Nuevas comprobaciones: `recomendar_local` con `tipo_local` igual que `recomendar()`, horas de clientes, sensibilidad y reparto; sin tipo, `general` y aviso; `comparar_locales` con tipo y 13 filas (fila de clientes); tipo desconocido, error claro |
| Resultado general sin tipo frente al último commit (tres ejemplos) | Igual: perfil, informe, a quién, qué vender, precio, riesgos y comprobaciones. Solo se añaden el aviso de resultado general en el porqué de «a qué hora» y dos claves nuevas (`por_franja_de` y `confianza_paso`) |
| `python src/resumen_ejemplos.py` | Mismas cifras de la tabla. Las huellas cambian por las claves nuevas: Vicálvaro `f0d5622a86df` → `cb5f7e0c357e`, Fuenlabrada `a97f2c92fc16` → `f172481d9d9a`, Griñón `e50b524e6024` → `1590295e4d46` |
| AppTest (fuera del proyecto): tres ejemplos × sin tipo y cinco tipos | 18 casos sin excepciones: Resumen con las cuatro tarjetas abiertas; gráfico de clientes; Informe completo en laborable, sábado y domingo. Selector siempre visible; aviso de resultado general sin tipo; «¿Cuándo tendrías más clientes?» y «Pasa más gente» con tipo; ninguna cifra de clientes en el Resumen; unidad y reparto en el Informe |
| AppTest: elegir el tipo con el selector | Pulsar «Bar de barrio» cambia las respuestas. El tipo se mantiene al cambiar de dirección |
| AppTest: comparación Vicálvaro-Griñón, sin tipo y con bar de barrio | Sin excepciones en los tres días. Fila de clientes solo con tipo. Cambiar el tipo desde la comparación funciona |
| PDF del informe (Vicálvaro y Griñón, sin tipo y con tipo) y de la comparación | Los ocho textos obligatorios. Sin tipo, el aviso de resultado general; con tipo, «Clientes posibles por horas» |
| Chromium (portátil 1.440 px y móvil 390 px), Vicálvaro sin tipo y con bar de barrio | Sin errores de JavaScript ni desplazamiento horizontal. Revisadas a ojo: el selector, la tarjeta y la explicación de la hora, y el gráfico «Tus clientes». Se corrigió una minúscula tras punto en el aviso |
| Privacidad | En el repositorio no aparecen ni la dirección ni las coordenadas del bar |

Las pruebas con AppTest, el PDF y Chromium están fuera del proyecto, como en los registros
anteriores.

**No se han rehecho las capturas de `docs/capturas/` ni los PDF de muestra de
`docs/ejemplos/`.** Siguen mostrando la versión anterior, sin el selector.

## Ficheros

- **Nuevo, `src/tipo_local.py`:** clientes por tipo de local, sensibilidad y contraste con
  el gasto. Se puede ejecutar desde la terminal.
- **`src/supuestos.py`:** sección «TIPO DE LOCAL» con tipos, tasas de parada, visitas y
  reparto de los vecinos, precios por visita, límite del gasto, momentos por tipo de local
  y criterio de sensibilidad.
- **`src/perfil_horario.py`:** devuelve también `poblacion_radio`, la población sin
  redondear.
- **`src/recomendaciones.py`:** `recomendar(..., tipo_local=None)`; a quién, a qué hora y
  qué vender con los clientes del tipo; detalle con las dos horas punta, la sensibilidad y
  `clientes_por_hora`.
- **`src/calle.py`:** las dos preguntas de la hora, la comparación entre franjas sin
  cifras, las frases con tipo de local y la comprobación en persona de contar clientes.
- **`src/comparar.py`:** fila «Cuándo tendrías más clientes»; «Qué conviene ofrecer» con
  los clientes del día; la fila de paso se llama ahora «Cuándo pasa más gente (día de
  diario)» y usa la fiabilidad de las horas de paso.
- **`src/documento.py`:** tipo de local en la cabecera, aviso de resultado general y
  gráficos de clientes.
- **`app/app.py` y `app/estilo.css`:** selector, tarjetas, gráfico «Tus clientes», Resumen
  sin cifras de clientes, cifras y sensibilidad en el Informe completo, y selector en la
  comparación.
- **`mcp/servidor.py` y `mcp/probar_cliente.py`:** parámetro `tipo_local` y sus pruebas.
- **`src/comprobar_datos.py`:** comprobación 38 (contraste con el gasto).
- **`src/tablas_readme.py` y `README.md`:** el uso de la EPF, la validación en «Rigor», la
  pregunta nueva, las limitaciones, el servidor MCP y la línea del bar de barrio en la
  tabla de ejemplos.
- **Documentos nuevos:**
  - `docs/validacion.md`;
  - `docs/registro/2026-11-15-propuesta-tipo-de-local.md` (la propuesta, con una nota de
    que se aprobó con cambios);
  - este registro.

## Fuentes

No hay fuentes nuevas. La Encuesta de Presupuestos Familiares ya estaba en
`docs/fuentes.md` y ahora se usa también para el contraste de las visitas. El testimonio
del hostelero es una comunicación personal y no se publica nada que identifique el local.

## Limitaciones

- **Los clientes por tipo de local son supuestos sin calibrar:** tasas de parada,
  visitas, repartos por hora, precios por visita y la mitad del gasto cerca de casa. Un
  solo bar no basta, y además sus valores se escribieron conociendo su testimonio.
- **Son visitas que llegan, no ocupación.** A mediodía la gente se queda más rato, y eso
  no se ve.
- **Las cifras son para todos los locales de ese tipo en 300 m.** No se reparten entre
  los locales que hay.
- **Los restaurantes de cenas y la comida para llevar** atraen gente de más de 300 m, y los
  pedidos a domicilio no son visitas: el modelo se queda corto en esos tipos.
- **La sensibilidad solo mueve el peso de la gente que pasa frente al de los vecinos.** No
  mueve la forma de cada reparto por horas.
- **Sigue sin medirse la gente que pasa contra un recuento real.**
