# 2026-11-12 · Rediseño visual completo de la aplicación

## Qué se pidió

Un rediseño visual completo, pensado primero para el móvil y luego para el portátil:
portada con un buscador grande, sugerencias mientras se escribe, cabecera fija, un
sistema visual propio, el nivel de movimiento como aguja de barómetro, un gráfico por
horas más claro y un Informe completo en una sola columna con índice. **Sin cambiar
cálculos ni textos obligatorios** (aviso de orientación, atribuciones, «Powered by
CRTM», fuentes).

## ¿Da Streamlit para esto?

**Sí, sin cambiar de herramienta**, pero no solo con CSS. Lo que el CSS no permite
(un buscador con sugerencias y el botón dentro, la barra fija con el buscador, el
índice que sigue el desplazamiento, la ubicación del navegador) se ha hecho con **un
componente propio** montado con `st.components.v2`, que Streamlit 1.67 trae de serie:
HTML y JavaScript propios dentro de la página, sin iframe, que hablan con Python. Todo
lo demás es HTML y CSS dentro de `st.markdown`, más los contenedores con clave de
Streamlit para las tarjetas.

Por eso **no se ha usado `streamlit-searchbox`**, que era la sugerencia del encargo:

- va en un iframe: no hereda la letra de la página, su lista de sugerencias no puede
  salir del marco (empuja el contenido en vez de flotar encima) y no admite el botón
  dentro del campo;
- habría sido una dependencia más que fijar y vigilar. Con el componente propio,
  **`requirements.txt` no cambia**.

El comportamiento pedido es el mismo: sugerencias con el servicio `candidates` de
CartoCiudad, espera entre pulsaciones y mínimo de 4 caracteres.

## Qué ha cambiado

### Ficheros

- `app/app.py`: la parte de pantalla, reescrita. Las funciones que leen
  `recomendar()` e `informe_local()` y las frases del Resumen **no se han tocado**.
- `app/estilo.css` (nuevo): el sistema visual. Antes el CSS iba dentro de `app.py`.
- `app/buscador.js` (nuevo): el componente del buscador y de la barra.
- `app/logo.svg` (nuevo): el logotipo, que es también el icono de la página.
- `src/direcciones.py` y `docs/fuentes.md`: solo el texto de privacidad y de uso de
  CartoCiudad. **Ningún otro fichero de `src/` ha cambiado.**
- `.streamlit/config.toml`: se añade el peso 800 de la letra Inter.

### Logotipo

Un SVG propio y sencillo: una taza vista desde arriba (círculo con su asa) cuya
aguja, como la de un barómetro, marca hacia arriba a la derecha, en blanco sobre un
cuadrado teja de esquinas redondeadas. No imita ninguna marca. Se usa en la portada,
en las dos barras y como icono de la pestaña del navegador.

### Portada (sin dirección elegida)

- A pantalla completa, sobre un fondo oscuro café con un degradado suave en teja.
- El logotipo y el nombre muy grandes, la frase de siempre («Te ayuda a decidir qué
  ofrecer en tu bar o restaurante, según la zona.») y **un único buscador** ancho y
  redondeado, con su botón dentro.
- Debajo, discretos: los tres ejemplos, **«Usar mi ubicación»** y el texto de
  privacidad con la atribución de CartoCiudad.
- **Tres cifras, calculadas al arrancar** (no escritas a mano):
  - **15 conjuntos de datos abiertos de la Comunidad de Madrid en uso:** los de la
    tabla del portal de `docs/fuentes.md` que tienen un uso declarado en
    `src/tablas_readme.py` (la misma lista que genera la tabla del README). En
    `docs/fuentes.md` hay 16: las farmacias se descargan y se procesan, pero ningún
    cálculo las usa, y por eso no cuentan;
  - **4.518 zonas analizadas:** las secciones censales de
    `datos/procesados/secciones_censales.parquet`;
  - **179 municipios cubiertos:** los municipios distintos de esas secciones.
- El aviso de orientación sigue en la portada, en una línea discreta bajo las cifras.
- **Barra superior fija y fina:** el logotipo a la izquierda y enlaces a «Cómo
  funciona», «Fuentes y licencias» (dos secciones nuevas más abajo, en la misma
  portada, sobre fondo claro) y al repositorio.
- **Ya no hay mapa en la portada.** Antes se podía tocar el mapa sin haber elegido
  nada; ahora se empieza por el buscador, un ejemplo o la ubicación. En el resultado
  se sigue pudiendo tocar el mapa para mirar otro sitio.

### Buscador en tiempo real

- Mientras se escribe aparecen hasta 6 sugerencias. **Es un solo paso:** al elegir
  una que es un portal con número se calcula directamente. Con el teclado, las
  flechas mueven la selección e Intro (o el botón «Buscar») elige.
- **Para no saturar CartoCiudad:** no se pregunta con menos de 4 caracteres, se
  esperan 350 ms desde la última pulsación y no se repite la última consulta al
  elegir. Mientras solo se escribe se vuelve a ejecutar el buscador, no la página.
- **Las reglas de siempre:** las peticiones salen del servidor con `geocodificar()`,
  así que siguen sin aparecer nombres de comercios ni de lugares (se descartan
  «topónimo» y «punto de interés») y solo hay direcciones de Madrid. Si se elige una
  calle sin número, un municipio o un código postal, la sugerencia lo avisa
  («confirmarás el sitio en el mapa») y se pide la confirmación «¿Es aquí?» antes de
  calcular nada.
- **«Usar mi ubicación»** pide la posición al navegador. Solo llega si el usuario
  pulsa el botón y da permiso; si lo niega, se le dice que escriba la dirección. El
  navegador solo ofrece la ubicación en páginas seguras (https, como la demo, o
  `localhost`).
- **Fuera de la Comunidad:** el aviso «Ese punto está fuera de la Comunidad de
  Madrid. Elige otro.» sale ahora bajo el buscador de la portada.

### Condiciones de uso de CartoCiudad

Revisadas de nuevo el 2026-11-12 (preguntas frecuentes y aviso legal):

- el acceso y uso de los servicios web es gratuito «en cualquier caso», mencionando
  la autoría como «CC BY 4.0 www.scne.es/productos.html#CartoCiudad», que la
  aplicación muestra bajo el buscador y en el pie;
- no fijan un límite de peticiones ni prohíben el autocompletado, y `candidates` es
  el método del servicio para proponer candidatos a partir de un texto incompleto.

Conclusión: **el uso está permitido.** No hay garantía de disponibilidad ni un límite
publicado, así que la espera y el mínimo de letras son una cortesía, no una condición
escrita. Anotado en `docs/fuentes.md`.

### Privacidad

- Texto nuevo bajo el buscador: «Lo que escribes se envía a CartoCiudad para sugerir
  direcciones; no se guarda. Tu ubicación solo se usa si pulsas el botón y la
  aceptas; tampoco se guarda.»
- Lo escrito, la dirección elegida y la ubicación solo viven en la memoria de la
  sesión. De las sugerencias solo se recuerda la última consulta, y se borra al
  elegir un punto.
- La dirección elegida se enseña ahora en la barra y en el resultado (antes ponía «El
  punto que has elegido»). Es una ubicación, no un nombre de local.
- Comprobado: después de las pruebas, el registro del servidor no contiene ninguna de
  las direcciones escritas.

### Resultado: barra fija

- Al elegir una dirección, la portada se sustituye por el resultado, sobre fondo
  claro. La barra oscura queda siempre visible al bajar, con el logotipo (que vuelve
  a la portada), **la dirección analizada**, el botón **«Buscar otra»** (abre el
  buscador con sugerencias dentro de la propia barra) y el cambio entre «Resumen» e
  «Informe completo».
- En el móvil, el cambio de vista baja a una segunda fila fina, también fija.
- Al cambiar de vista se vuelve arriba.

### Sistema visual

- **Paleta:** un color principal oscuro (café, `#1d1410`) para la portada y la
  barra; **el teja de siempre (`#9c3d1b`) como acento**, y es el color de las
  respuestas; ocre solo para los avisos; fondo crema y tarjetas blancas.
- **Escala tipográfica marcada** (Inter): cifras y veredictos de 2,3 a 3,3 rem con
  peso 800, títulos de 1,2 a 1,75 rem, texto secundario más pequeño y más suave, y
  rótulos pequeños en versalitas.
- **Tarjetas** blancas con sombra suave y esquinas redondeadas.
- **Iconos propios de un mismo estilo** (línea de 2 px, sin relleno), en lugar de los
  emojis de antes: uno por pregunta, por sección y por tipo de aviso.
- **Color con significado:** teja para la respuesta; ocre con icono para los avisos y
  los riesgos; verde solo cuando no hay nada especial; las etiquetas de confianza
  siguen en verde, ámbar y rojo.
- **Carga:** mientras se calcula se ve la aguja oscilando con «Mirando la zona…»;
  mientras se buscan direcciones, tres puntos animados.

### Nivel de movimiento: la aguja

- Es la imagen del resultado: un barómetro de cinco tramos, de claro a oscuro en un
  solo tono, con una aguja que gira hasta su sitio al cargar. Al lado, el nombre del
  nivel en grande, la etiqueta «Estimación» y la frase de comparación; debajo, el
  titular.
- **Solo dibuja el nivel (1 a 5) que da `nivel_movimiento()`:** la aguja apunta al
  centro de su tramo. No se ha inventado una posición más fina.

### Gráfico por horas

- **Resumen:** una barra por hora con el total de gente, **las horas punta en teja**
  y el resto en un teja suave, con la hora escrita encima de las dos mejores.
  Etiquetas cada tres horas («6 h», «9 h»…) en horizontal, para que se lean en el
  móvil, y leyenda de dos entradas. Al pasar el ratón se ve la hora, la gente y quién
  pasa sobre todo.
- **Cambio de contenido, a propósito:** el gráfico del Resumen ya no reparte cada
  barra por tipo de cliente. Quién pasa está en la tarjeta «¿Quién pasa por aquí?» y,
  por horas y con los siete tipos, en el Informe completo.
- **Informe:** el gráfico apilado por tipo de cliente se mantiene, con los mismos
  colores de cliente y la misma marca «punta», y con etiquetas cada dos horas.

### Informe completo

- **Una sola columna**, sin pestañas: diez secciones, una detrás de otra.
- Las cuatro preguntas («A quién», «A qué hora», «Qué vender», «A qué precio») y el
  nivel de movimiento tienen **la misma estructura**: la respuesta en grande, la
  fiabilidad (confianza y dato o estimación), el porqué (la recomendación principal
  con sus motivos) y un detalle desplegable con todas las recomendaciones.
- Después: perfil por horas, mercado (ocho bloques, cada uno con su cifra en grande),
  riesgos y avisos, qué comprobar en persona, y fuentes y licencias.
- **Índice:** fijo a la izquierda en el portátil y en un menú «Secciones» en el
  móvil. Marca la sección en la que se está.
- «Fuentes y licencias», en el pie, lleva directamente a esa sección.

## Comprobaciones

Con Chromium sin interfaz (Playwright, instalado fuera del proyecto), en móvil
(390 × 844) y en portátil (1440 × 900), contra la aplicación en marcha:

- **Los tres ejemplos dan lo mismo que antes.** Se guardó lo que enseñaba la versión
  anterior y se comparó con la nueva en los dos tamaños:
  - iguales el titular, el nivel de movimiento y su frase, las cuatro respuestas, sus
    líneas de apoyo y su fiabilidad, cómo se llega, los avisos y las comprobaciones;
  - iguales las ocho cifras de mercado;
  - todos los textos de `recomendar()` e `informe_local()` (recomendaciones, motivos,
    riesgos, comprobaciones y resúmenes de los bloques: 111, 112 y 86 textos) están
    en el Informe completo.
- **Textos obligatorios** presentes: el aviso de orientación, «Powered by CRTM»,
  «© colaboradores de OpenStreetMap», la mención de CartoCiudad y la nota de no
  respaldo.
- **Ningún nombre de local:** los datos procesados siguen sin tenerlos, el mapa no
  tiene ventanas y su zoom máximo sigue en 16, y las sugerencias pasan por el mismo
  filtro de siempre.
- **Buscador:** con 3 letras no pide nada; con la dirección de prueba salen las
  sugerencias y al elegir se calcula; una calle sin número pide confirmación y no
  calcula hasta el «Sí, es aquí».
- **Ubicación:** con permiso, calcula y la barra dice «Tu ubicación»; sin permiso,
  avisa; con una posición de Toledo, avisa de que está fuera de la Comunidad.
- **Barra fija** al bajar, índice (lleva a la sección y la marca) y enlaces de la
  portada: funcionan. Sin desplazamiento horizontal en el móvil. Sin errores de
  JavaScript.

**No se ha probado** en Streamlit Community Cloud ni en un móvil de verdad: solo en
el entorno de trabajo, con el navegador a tamaño de móvil.

## Capturas

Se han sustituido todas las de `docs/capturas/` (móvil y portátil):

- `*-portada.png`, `*-sugerencias.png` y `*-portada-fuentes.png`;
- `*-{vicalvaro,fuenlabrada,grinon}-resumen.png` (lo que se ve sin bajar) y
  `-resumen-entera.png`;
- `*-{…}-informe.png` e `-informe-entera.png`;
- `*-vicalvaro-tarjeta-abierta.png`, `*-cabecera-fija.png`, `*-informe-indice.png`,
  `movil-informe-menu.png`;
- `*-buscar-otra.png`, `*-calle-sin-numero.png`, `*-muy-poco-paso.png`,
  `*-fuera-de-madrid.png` y `portatil-direccion-elegida.png`.

El README enseña ahora `portatil-portada.png` y `portatil-vicalvaro-resumen.png`.

## Limitaciones

- **`st.components.v2` es una parte reciente de Streamlit.** La aplicación depende de
  la versión fijada (1.67.0); al actualizar Streamlit hay que volver a probar el
  buscador y la barra.
- **Las sugerencias dependen de CartoCiudad.** Busca por parecido, así que a veces
  propone portales cercanos y no el exacto. Si no responde, el buscador lo dice.
- **Cada consulta de sugerencias va del navegador al servidor y de ahí a
  CartoCiudad:** con una conexión lenta tardan en aparecer.
- **El CSS se apoya en nombres internos de Streamlit** (`stMain`, `stColumn`…): un
  cambio de versión puede descolocar algo.
- **Las cuatro tarjetas del Resumen** siguen en fila en el portátil y apiladas en el
  móvil. La regla de «una sola columna» se ha aplicado al Informe completo, que es
  donde se pedía.
- **«Cómo funciona»** es un texto nuevo de tres pasos, escrito a partir del README.
