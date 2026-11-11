# 2026-11-11 · Rediseño de la aplicación web (fase 4, parte A2)

## Por qué

En la primera versión, todo estaba al mismo nivel: siete secciones numeradas, una detrás
de otra, con párrafos largos desde el principio. A primera vista, la página no decía
qué conclusión sacar ni animaba a leer. El rediseño reorganiza **la misma información**
de la conclusión al detalle, en tres niveles. **No cambia ningún cálculo**: `src/` no se
ha tocado, y la aplicación sigue llamando solo a `perfil_horario()`, `informe_local()` y
`recomendar()`.

## Qué ha cambiado

### Nivel 1: visible sin bajar en un portátil

- **Cabecera compacta:**
  - en una línea, el nombre y una frase de qué hace;
  - en una sola fila, el buscador, el botón «Buscar» y los tres ejemplos. El ejemplo
    elegido queda resaltado. Al pulsar Intro en el buscador también se busca;
  - el aviso «Orientación… no garantías. Toda cifra de personas es una estimación.» va
    en una línea discreta con borde ocre, siempre visible.
- **Lugar:** una línea con el ejemplo o «Punto elegido», el municipio, el radio y el
  tiempo de cálculo.
- **Titular de una frase**, generado a partir de las recomendaciones:
  - **clientes:** los tipos con al menos el 25 % de los clientes posibles en
    laborable (dos como mucho);
  - **horas punta del laborable:** se juntan las horas seguidas y se nombra la más
    concurrida de cada tramo (dos tramos como mucho);
  - **competencia,** según lo que digan las recomendaciones, en este orden: falta de
    locales que sirven comidas, otro hueco, «competencia alta» o, si no, el número de
    locales. Si la fuente es OpenStreetMap con cobertura baja, se dice «al menos».
  - Sin lenguaje de garantía. Ejemplos:
    - Vicálvaro: «Zona de vecinos y universitarios, con hora punta hacia las 8 y las 14
      y pocos locales que sirven comidas.»;
    - Fuenlabrada: «Zona de viajeros y vecinos, con hora punta hacia las 8 y mucha
      competencia (al menos 25 locales en 300 m).»;
    - Griñón: «Zona de vecinos y familias con niños, con hora punta hacia las 8 y las 16
      y al menos 2 locales de hostelería en 300 m.».
- **Cuatro tarjetas en fila** (a quién, a qué hora, qué vender, a qué precio). Cada una
  lleva icono, respuesta en letra grande, una línea de apoyo, la etiqueta de confianza
  (verde alta, ámbar media, roja baja) y la de dato o estimación. El «Por qué»
  desplegable contiene **todas** las recomendaciones de esa pregunta con sus motivos.
  - **A quién:** los tipos principales, con el punto de su color, y «≈33 % y ≈31 % de
    los clientes posibles en laborable · sábado: …».
  - **A qué hora:** los tramos punta del laborable («8–10 h · 14 h»), el sábado y, si
    lo hay, el posible hueco horario.
  - **Qué vender:** el momento con más clientes posibles en laborable. Si recomendar()
    señala la oportunidad de comidas, la línea de apoyo la menciona («a comprobar»).
  - **A qué precio:** la gama ajustada a la clientela, la subida del IPC del sector y
    el aviso de que no hay precios en euros.

### Nivel 2: mapa y perfil por horas, lado a lado (apilados en móvil)

- El mapa a la izquierda y el gráfico a la derecha, con el selector Laborable o Sábado
  encima del gráfico.
- **Horas punta marcadas** en el gráfico con la palabra «punta» sobre la barra. Son las
  mismas horas que da recomendar().
- **Leyendas** propias en HTML bajo cada elemento:
  - en el mapa, los tipos de local, el radio y la fuente;
  - en el gráfico, los tipos de cliente presentes ese día.
- El eje del gráfico usa el punto de miles («1.500») y su título lleva «≈».
- Sin punto elegido, se ve solo el mapa, a todo el ancho, para hacer clic.

### Nivel 3: pestañas

1. **Detalle de las recomendaciones:**
   - todas las recomendaciones con etiquetas y «Por qué», como antes;
   - la tabla de clientes por franja;
   - la tabla del perfil por franjas del día elegido (redondeada solo para mostrarla);
   - la confianza de cada tipo de cliente;
   - la nota de que el domingo no se modela.
2. **Mercado:** los seis bloques del informe en una cuadrícula de tres columnas. Cada
   uno empieza con su cifra clave (`st.metric`) y una frase:
   - **competencia:** locales en 300 m;
   - **mercado:** gasto anual de los vecinos, con «≈»;
   - **precios:** la gama;
   - **turismo:** alojamientos del código postal;
   - **festivos:** el próximo festivo;
   - **sector:** la variación anual.

   El resumen, las tablas, todas las notas (los avisos en amarillo) y las fuentes van
   en el desplegable «Detalle, notas y fuentes». Ese desplegable lleva ⚠️ en el título
   si contiene un aviso importante.
3. **Riesgos y avisos:**
   - los riesgos de recomendar() como lista corta, con icono, etiquetas y «Por qué».
     Van ordenados por impacto en el negocio: periodos sin clase, competencia alta,
     cobertura de OSM, competencia sin valorar, festivos;
   - debajo, «Avisos sobre los datos» en una línea cada uno: cobertura de OSM, IPC con
     hoteles, festivos sin publicar, sector mezclado con comercio, domingo no modelado
     y que toda cifra es una estimación.
4. **Qué comprobar en persona:** la lista numerada. El bloque para copiar y la
   descarga `.txt` quedan en un desplegable.
5. **Fuentes y licencias:** igual que antes, leídas de `docs/fuentes.md`, con la
   atribución de CartoCiudad añadida. Sin punto elegido, esta sección está en un
   desplegable bajo el mapa.

### Pie de página

En una línea: Powered by CRTM (con enlace), © colaboradores de OpenStreetMap (ODbL),
CartoCiudad (IGN, CC BY 4.0, con su enlace), la fecha de descarga de los datos del
portal, la nota de no respaldo y «orientación, no garantías».

### Estilo

- **Tema propio** en `.streamlit/config.toml`:
  - color principal ladrillo `#9c3d1b` y acento ocre `#c98a2b`, este solo en la
    interfaz y nunca en los datos;
  - fondo blanco cálido `#fbfaf7`, texto `#1f1b16` (contraste alto), bordes suaves y
    radio de 0,6 rem;
  - tipografía Inter (Google Fonts). Sin conexión, se usa la sin serifa del sistema.
- **CSS mínimo** en `app/app.py`: cabecera, titular, tarjetas, etiquetas, leyendas y
  pie.
- **Un solo juego de colores** para toda la aplicación:
  - **tipos de cliente:** se usa la paleta categórica de referencia de la guía de
    visualización, en orden fijo. Está validada para daltonismo en pares contiguos y
    ese orden es también el de apilado del gráfico: vecinos azul, viajeros naranja,
    universitarios aguamarina, padres y niños amarillo, pacientes rosa, trabajadores
    verde, deporte violeta. Los mismos colores aparecen en las tarjetas, el gráfico,
    la leyenda y `chartCategoricalColors`;
  - **tipos de local en el mapa:** tonos oscuros distintos de los de cliente (bar
    rojo, restaurante azul marino, cafetería marrón, comida rápida gris), con borde
    blanco.
- **Números:** «≈» en las estimaciones de las tarjetas y del mercado, porcentajes sin
  decimales, millones con una decimal y menos de un millón en miles («≈950 mil € –
  1,2 M€»).

## Lo que se mantiene

- Toda la información de la versión anterior sigue en la página, como mucho a un clic.
- **Privacidad:**
  - sin nombres de locales: los datos no los tienen, el mapa no tiene ventanas y el
    zoom máximo sigue en 16;
  - el geocodificador sigue descartando topónimos y puntos de interés;
  - las direcciones solo viven en la sesión. La advertencia de que se envían a
    CartoCiudad aparece ahora junto a los resultados de la búsqueda.

## Pruebas

- **`streamlit.testing.v1.AppTest`:** arranque, los tres ejemplos (con laborable y
  sábado), la dirección «Plaza de la Constitución 1, Fuenlabrada» y un punto de
  Toledo. Sin excepciones; el punto de Toledo da el aviso de fuera de la Comunidad.
- **Capturas con Chromium sin interfaz** (Playwright instalado fuera del proyecto),
  en `docs/capturas/`:
  - `portatil-*-nivel1.png` (1440 × 900) y `movil-*-nivel1.png` (390 × 844): lo que
    se ve sin bajar;
  - `*-completa.png`: la página entera;
  - `portatil-*-mercado.png` y `portatil-*-riesgos.png`: esas pestañas.
- **Nivel 1 en portátil:** en los tres ejemplos, las tarjetas terminan a 547 px de
  900. La cabecera, el aviso, el titular y las cuatro tarjetas (con su «Por qué»)
  caben sin bajar, y aún asoma el principio del mapa y del gráfico.
- **Prueba de los cinco segundos:** sin bajar se leen el titular y cuatro respuestas
  de una a tres palabras («Vecinos y universitarios», «8–10 h · 14 h», «Desayuno»,
  «Gama económica»), cada una con su confianza.
- **Móvil:** todo se apila en una columna y el documento mide 390 px de ancho, sin
  desplazamiento horizontal. Sin bajar se ven la cabecera, el aviso, el titular y el
  principio de la primera tarjeta; las tarjetas terminan hacia los 1.550 px.
- **Navegador:** sin errores de JavaScript en las seis cargas.

## Limitaciones

- **El titular es una plantilla**, no texto libre: si recomendar() cambia la redacción
  de los riesgos o de la oportunidad de comidas, hay que revisar `frase_competencia()`
  y la tarjeta «Qué vender».
- **Inter se carga desde Google Fonts:** el navegador del usuario hace esa petición,
  igual que con las teselas del mapa. Sin acceso, se usa la fuente del sistema.
- **En móvil, el nivel 1 no cabe en una pantalla:** los botones de ejemplo se apilan.
  Se ha priorizado que el titular quede visible.
