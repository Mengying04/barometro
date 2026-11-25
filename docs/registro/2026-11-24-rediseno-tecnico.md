# 2026-11-24 · Segunda ronda de diseño: aspecto técnico y portada con más impacto

## Qué se pidió

Una segunda ronda de diseño, **sin cambiar cálculos, datos ni respuestas**, tocando solo
`app/` y `.streamlit/config.toml`:

- un aspecto más técnico y profesional, que no parezca infantil;
- una portada con más impacto;
- un Informe completo con ficha técnica y metodología.

Antes de tocar nada se guardaron, fuera del repositorio:

- capturas de la portada, el Resumen y el Informe a 390, 1.280, 1.440 y 1.920 px;
- los textos de 42 vistas, volcados con AppTest.

## Qué se ha hecho

### 1. Estilo general (todas las vistas)

- **Radios de 6 a 8 px.** Solo el cambio Resumen / Informe sigue en píldora. El buscador,
  los botones, los ejemplos, las pestañas de planes y los botones del selector de tipo de
  local pasan a 6 px. El radio base de Streamlit pasa de 0,6 rem a 6 px
  (`.streamlit/config.toml`).
- **Bordes de 1 px en lugar de sombras.** Afecta al veredicto, las tarjetas del Resumen, las
  cajas del mapa y del gráfico, los datos clave, la comparación, los planes y los pasos.
  - Al pasar el ratón, una tarjeta ya no sube: cambia el color del borde.
  - El borde ancho que marca la explicación abierta, el plan destacado y el resumen de la
    comparación se mantiene.
- **Etiquetas rectangulares** (3 px de radio): fiabilidad, «Plan …», «Por hacer» y las líneas
  de transporte.
- **Menos iconos decorativos en los títulos del Informe.** Quedan los números de sección. Se
  quitan el icono del título «¿Qué tipo de local?» (solo dentro del Informe) y el de la
  línea «Radio de … · calculado en …».
- Los dibujos de los locales del mapa no cambian.

### 2. Cabecera

- **Más alta:** de 56 a 68 px en pantallas anchas, y de 52 a 56 px en el móvil.
- **Logotipo** de 30 a 37 px; el buscador, de 40 a 44 px de alto y hasta 40 rem de ancho.
- **Nada queda tapado al bajar:** el contenido empieza más abajo y se ajustan el margen de
  las anclas (las secciones a las que se salta desde el índice) y la posición del índice
  lateral. Comprobado bajando hasta el pie en los cuatro anchos.

### 3. Portada

- **Rótulo** «Datos abiertos de la Comunidad de Madrid», pequeño y en mayúsculas.
- **«BARómetro» a 8 rem** en portátil, con el logotipo proporcional (0,82 del alto de la
  letra). En pantallas estrechas mide el 14 % del ancho, para que nunca pase del borde (unos
  55 px a 390 px).
  - Es el único tamaño fuera de la escala de la primera ronda: se añade como `--f-portada`,
    solo para esto.
- **Titular** «Que pase mucha gente no significa que tengas clientes.» (2,5 rem; 1,75 en el
  móvil) y la **frase** pedida. El lema anterior («Te ayuda a decidir…») sigue en el pie.
- **El buscador**, como antes.
- **Tres ventajas** en fila, cada una con un icono de línea (reloj, dos columnas y
  gráfico): «Cuándo tendrías clientes, según tu tipo de local» · «Compara dos locales lado a
  lado» · «Dato y estimación, siempre separados». En el móvil, una debajo de otra.
- **Cuatro cifras:** 15 conjuntos, 4.518 zonas, 179 municipios y «Cada semana · datos
  actualizados».
  - «Cada semana» es el flujo de GitHub Actions `actualizar-datos.yml`.
  - Las tres cifras numéricas suben contando al entrar (0,8 s). El HTML ya trae la cifra
    final: sin JavaScript, o si el sistema pide reducir el movimiento, se ven quietas
    desde el principio. Comprobado en Chromium en los dos casos.
  - En pantallas de menos de 1.100 px van en dos filas de dos.
- **El aviso de orientación** sigue visible bajo las cifras.

### 4. Informe completo

- **Ficha técnica** al principio, después del selector de tipo de local, en una tabla de
  dos columnas:
  - punto analizado (con sus coordenadas);
  - municipio y radio de análisis;
  - tipo de local (o «Sin elegir (resultado general)»);
  - fecha de los datos (la descarga del portal) y fecha del informe (hoy, en hora de Madrid);
  - método: «Modelo por horas con supuestos explícitos»;
  - versión: el commit corto, leído de `.git` sin ejecutar git. Si no hay `.git`, como en la
    imagen de Docker, pone la fecha de los datos.

  En el móvil, cada dato va debajo de su nombre.
- **Datos clave sobrios:** rótulo en mayúsculas, cifra en tinta oscura con números
  tabulares, y unidad donde faltaba («≈23.000 personas/día»). Debajo, separado por una
  línea fina, «Dato», «Estimación» o «Estimación · confianza media», en texto.
  - La confianza mantiene su color (verde, ocre o rojo oscuro).
  - En el mercado, «· con avisos» cuando el bloque los tiene.
  - La tarjeta de fiabilidad conserva los puntos y su texto («Orientativo»…).
- **Gráficos del perfil por horas:**
  - títulos de eje: «Hora del día» y «Personas por hora (≈)» o «Visitas posibles por hora
    (≈)»;
  - rejilla horizontal clara y marcas en el eje de horas;
  - fondo transparente dentro de su caja;
  - debajo, «Fuente: perfil por horas con datos del CRTM, del Portal de Datos Abiertos de
    la Comunidad de Madrid, del INE y de OpenStreetMap. Elaboración propia.» (en el de
    clientes, también los supuestos del tipo de local).

  Los gráficos del Resumen y de la comparación no cambian.
- **Tablas:** las de Streamlit ya alinean los números a la derecha. Las tablas propias
  (ficha, metodología y fuentes) son de texto.
- **Sección nueva «10 Metodología y supuestos clave»**, antes de Fuentes (que pasa a ser la
  11). Es una tabla de parámetro, valor y de dónde sale, **leída de las constantes de
  `src/supuestos.py` tal cual, sin cambiar ninguna**:

  | Parámetro | Constante |
  |---|---|
  | Radio de análisis | `RADIO_M` |
  | Peso por distancia | `PESO_BORDE` |
  | Propensión a pararse a consumir | `PROPENSION_CONSUMO` |
  | Tasa de parada de la gente que pasa (tipo elegido: la mínima y la máxima) | `TASA_PARADA` |
  | Visitas de los vecinos que van a propósito (tipo elegido) | `VISITAS_VECINO` |
  | Límite de esas visitas (50 % del gasto) | `PARTE_GASTO_CERCA_DE_CASA` |
  | Sensibilidad del horario de clientes | `SENSIBILIDAD_FACTORES` |
  | Cortes del nivel de movimiento | `MOVIMIENTO_NIVELES`, `MOVIMIENTO_MINIMO_PASOS` |

  Sin tipo de local, las dos filas del tipo dicen «Solo con un tipo de local elegido».
  Debajo va la **fórmula del mercado potencial**, con la elasticidad y el margen leídos de
  `ELASTICIDAD_RESTAURACION` y `MARGEN_POBLACION`. Al final, enlaces a `src/supuestos.py` y
  al README para el resto, y la línea de la fuente.

### 5. Resumen

Solo el punto 1 (radios, bordes y etiquetas). El contenido y el lenguaje no cambian.

## Pruebas

| Prueba | Resultado |
|---|---|
| Huellas de `src/resumen_ejemplos.py` con la fecha de referencia (2026-11-23) | Iguales en los tres puntos |
| AppTest: portada, planes, tres ejemplos (Resumen e Informe, tres días), comparación y los dos PDF | 17 de 17 bien |
| AppTest: tres puntos × cinco tipos de local y general (tarjetas, gráfico de clientes, Informe en los tres días) | Todo correcto |
| AppTest: ficha técnica y metodología sin tipo, con «bar de barrio» y con «restaurante de cenas» | Sin excepciones; valores leídos de `src/supuestos.py` |
| Chromium a 390, 1.280, 1.440 y 1.920 px (portada, Resumen, Informe, planes y comparación, bajando hasta el pie) | Sin errores de JavaScript, desplazamiento horizontal, solapes ni índice sobre el pie |
| Contraste y direcciones web visibles | Ningún texto por debajo de 4,5:1; ninguna dirección web (salvo la mención obligatoria de CartoCiudad) |
| Escala tipográfica | Todo dentro de la escala salvo «BARómetro» de la portada (`--f-portada`, pedido) |
| Cifras de la portada | Suben contando hasta la cifra final; con «reducir movimiento», quietas |
| Textos obligatorios | Aviso de orientación, Powered by CRTM, OpenStreetMap, CartoCiudad, nota de no respaldo y privacidad, en su sitio |

**Comparación de textos** (las 42 vistas, palabra a palabra, contra la referencia):

- **Resumen** (con y sin tipo, con cada tarjeta abierta), comparación, planes y dirección sin
  confirmar: no se pierde ninguna palabra.
- **Informe completo:** solo cambian «Con avisos» y «Confianza», que pasan a minúscula en el
  pie de las tarjetas. Se añaden la ficha técnica, la metodología, los títulos de eje, las
  fuentes de los gráficos y la unidad «personas/día».
- **Portada:** el lema anterior se sustituye por el titular y la frase pedidos (sigue en el
  pie); se añaden el rótulo, las ventajas y la cuarta cifra.

## Capturas y PDF

Rehechas **las 89** de `docs/capturas/` (mismos nombres; «Bar de barrio» elegido en los tres
ejemplos y en la comparación) y los dos PDF de muestra de `docs/ejemplos/`. Los PDF no
cambian de diseño: los genera `src/documento.py`, que no se toca. Todo sin fallos ni errores
de JavaScript.

Durante la revisión salió un último detalle: en el móvil, la ficha técnica mostraba líneas
dobles, porque las filas heredaban el borde de las tablas de Streamlit. Se quitaron, se
rehicieron las capturas del Informe y se repitió la revisión del Informe en los cuatro
anchos, sin problemas.

## Archivos

- `app/app.py`: ficha técnica, metodología, pie de las tarjetas, ejes y fuente de los
  gráficos del Informe, portada nueva y versión del código.
- `app/estilo.css`: bloque «segunda ronda» al final (y las líneas de la ficha en el móvil).
- `app/buscador.js`: cifras que suben contando.
- `.streamlit/config.toml`: radio base de 6 px.
- `docs/capturas/` y `docs/ejemplos/`: rehechos.
