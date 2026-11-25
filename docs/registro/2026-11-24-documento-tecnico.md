# 2026-11-24 · El PDF, al día con la web y con aspecto de informe técnico

## Qué se pidió

Poner el documento descargable (`src/documento.py`) al día con la web tras la segunda ronda
de diseño y darle aspecto de informe técnico, **sin cambiar cálculos ni respuestas**. Además:

- marcar «Oficinas de farmacia», que se descarga pero no se usa, también en la tabla de
  fuentes de la aplicación;
- corregir en el README cómo se abre la configuración de Claude Desktop y anotar que el
  servidor MCP se ha probado allí.

## Qué se ha hecho

### 1. Estilo del PDF (como la web)

- **Secciones numeradas** (01, 02…). Cada una lleva una línea fina encima, el número en teja
  y el título.
- **Bordes finos y radios pequeños** (0,25 mm y 1,2 mm, los 1 px y 6 a 8 px de la web) en
  lugar de las cajas amarillas redondeadas. Los avisos llevan un rótulo («Aviso», «Sin
  novedad», «Resultado general», «Contraste con conteos reales»).
- **Rótulos pequeños en mayúsculas,** con algo de espacio entre letras, como `.rotulo`.
- **Etiquetas de fiabilidad rectangulares,** con los colores de `.conf-alta`, `.conf-media` y
  `.conf-baja`.
- **Números tabulares.** DejaVu Sans ya tiene todas las cifras del mismo ancho. Las tablas
  alinean los números a la derecha (valor del nivel de movimiento, valores del mercado,
  locales por tipo, fechas de las fuentes).
- **Cabecera** fina en las páginas 2 y siguientes, y **pie** con las atribuciones y «página
  / total».
- Sigue la letra **DejaVu Sans**.

### 2. Primera página

- Logotipo, «BARómetro», subtítulo y, a la derecha, «Informe técnico · Datos abiertos de la
  Comunidad de Madrid».
- Título (la dirección) y una **«Ficha técnica»** en tabla con las mismas filas que el
  Informe completo: punto analizado (con coordenadas), municipio, radio, tipo de local,
  fecha de los datos, fecha del informe, método y versión.
- El aviso de orientación y, debajo, **01 Resumen**: el titular y las cuatro respuestas en
  una cuadrícula de dos por dos.

En la comparación, la ficha lleva «Local A» y «Local B» en lugar del punto y el municipio, y
el radio «en cada uno».

### 3. Esquema de la zona

- Los locales se dibujan con **los mismos SVG que el mapa de la web** (taza, cuchillo y
  tenedor, jarra y hamburguesa, en blanco sobre un círculo del color de cada tipo). fpdf2
  los dibuja como vectores.
- Para no copiarlos, `DIBUJO_TIPO` y `marca_tipo()` pasan de `app/app.py` a `src/calle.py`,
  junto a `COLOR_TIPO`. La web los importa de ahí.
- La leyenda es una tabla pequeña con los mismos dibujos, la cuenta por tipo a la derecha y
  el total. Debajo, el punto analizado y las paradas.
- El esquema tiene las distancias de los anillos (100, 200 y 300 m) y «norte arriba».
- Sigue **sin mapa de fondo ni nombres**.

### 4. Contenido nuevo

- **Nota del contraste con conteos reales** en «A qué hora», con el mismo texto que la web.
- **«Metodología y supuestos clave»** antes de Fuentes, con la misma tabla y la misma
  fórmula que la web.
- Para que la web y el PDF digan exactamente lo mismo, estos textos pasan a un módulo
  nuevo, [`src/metodologia.py`](../../src/metodologia.py), que comparten las dos:
  - las filas de la ficha técnica y la versión del código;
  - las filas de la metodología, leídas de `src/supuestos.py` sin cambiar nada;
  - la fórmula del mercado potencial;
  - la nota del contraste (`AVISO_AFOROS`);
  - la línea de fuente de los gráficos por horas.

  En el PDF, la «e» elevada de la fórmula se escribe «ᵉ».
- Los **gráficos por horas** llevan títulos de eje («Personas por hora (≈)» o «Visitas
  posibles por hora (≈)», y «Hora del día»), una rejilla clara, marcas cada 3 horas y,
  debajo, la línea «Fuente: … Elaboración propia · Estimación». Igual en las curvas de la
  comparación.
- El **mercado** va en una tabla (indicador, valor, detalle y si es dato o estimación).

### 5. «Cómo se llega», una sola vez

Antes salía en «La zona» y otra vez en «Mercado». Ahora solo está en «La zona»: la tabla del
mercado se salta el bloque `accesos`.

### 6. Fuentes y licencias

- **Una tabla compacta:** fuente, licencia, fecha de los datos y fecha de descarga.
  - Las licencias van con su nombre corto («CC BY 4.0», «Open Database License (ODbL) 1.0»…).
  - La versión de los datos, en pocas palabras. El CRTM, con muchos ficheros, pone «Varios
    ficheros, del 2025-05-30 al 2026-11-16».
  - Sin direcciones web enteras ni citas literales largas.
- **Condiciones de uso, en una línea cada una:** CRTM, INE, CartoCiudad y teselas de
  OpenStreetMap. El texto completo sigue en `docs/fuentes.md`.
- **Corregido «descargado el no se descarga»:** CartoCiudad y las teselas ponen «No se
  descarga» en la columna de descarga.
- Las atribuciones llevan dominios cortos («crtm.es», «openstreetmap.org/copyright»), con
  enlace en el PDF. La mención de CartoCiudad («CC BY 4.0 www.scne.es/…») se deja tal cual,
  porque es la forma que pide su licencia.
- Se mantiene la frase «Portal de Datos Abiertos de la Comunidad de Madrid
  (datos.comunidad.madrid), descargado el …», que es uno de los textos obligatorios.

### 7. «Oficinas de farmacia»

- Se descarga y se procesa, pero **no entra en ningún cálculo**. No tiene uso en
  `src/tablas_readme.py` (`USO`), que es lo mismo que cuenta la cifra «15 conjuntos» de la
  portada.
- `src/fuentes.py` añade a cada conjunto del portal el campo «En uso».
- En el PDF y en la tabla de fuentes de la aplicación, los 15 en uso van primero y la
  farmacia va aparte, bajo **«Descargada, no se usa en los cálculos»**. No se borra de
  `docs/fuentes.md`, porque sí se descarga.

### 8. Comparación

El mismo estilo: ficha técnica, secciones numeradas, marcas «A» y «B» rectangulares, líneas
finas entre aspectos, gráficos con ejes y fuente, y la misma tabla de fuentes.

### 9. README y servidor MCP

- **Sección del PDF:** qué lleva ahora, el aspecto técnico, la farmacia y el tamaño (unos
  60 KB).
- **Sección del servidor MCP:** la ruta correcta en Claude Desktop (en el Mac, menú «Claude»
  de la barra de menús → Ajustes → Desarrollador → Editar configuración). Se dice que se ha
  probado en Claude Desktop el 24 de noviembre de 2026, según lo indicó la autora; esa
  prueba no se repitió desde este entorno.
- En [`2026-11-12-servidor-mcp.md`](2026-11-12-servidor-mcp.md) se añade una nota con la
  fecha bajo «No se ha probado en Claude Desktop», sin borrar el texto original.

## Pruebas

| Prueba | Resultado |
|---|---|
| Huellas de `src/resumen_ejemplos.py`, antes y después, el mismo día | Iguales en los tres puntos |
| Textos de la web (AppTest: Resumen, Informe completo y comparación de Vicálvaro y Griñón, sin tipo y con «bar de barrio»), antes y después | Iguales, salvo la tabla de fuentes del Informe: las mismas 27 filas, con la farmacia al final y la fila «Descargada, no se usa en los cálculos» |
| AppTest de la ronda anterior (portada, planes, tres ejemplos con los tres días, comparación y las dos descargas) | 17 de 17 bien |
| Los ocho `TEXTOS_OBLIGATORIOS` en los PDF (tres informes con y sin tipo, y la comparación; texto sacado con `pdftotext`) | Están todos |
| `python mcp/probar_cliente.py` | Todo correcto |
| `pyflakes` en los ficheros tocados | Sin avisos |
| Revisión visual, página a página, a 70 y 80 ppp | Sin solapes. Se corrigió una etiqueta de hora que pisaba el título del eje y unos textos que salían justificados |

Medido en el entorno de trabajo, cada informe ocupa unos 60 KB (7 páginas con tipo de local,
6 sin él), tarda menos de un segundo y usa unos 12 MB de memoria. La comparación ocupa unos
47 KB (5 páginas).

## Capturas y PDF

- Rehechos los dos PDF de muestra de `docs/ejemplos/`, con «Bar de barrio» elegido, a partir
  del mismo resultado que usa el botón de la aplicación (sacado con AppTest).
- Rehechas las cuatro capturas `docs/capturas/documento-*.png`, a 80 ppp como las
  anteriores.
- La ficha técnica de las muestras dice «commit f4a305d»: es la versión del código en el
  momento de generarlas, antes de este cambio. La web hace lo mismo.

## Limitaciones

- En el esquema de la zona, alguna marca de local puede tapar en parte el rótulo de un
  anillo («200 m»).
- Las paradas siguen siendo cuadrados blancos, no los iconos por modo (M, C, ML, autobús)
  del mapa de la web.
- Las condiciones de uso de una línea son un resumen. El texto completo, con enlaces y
  fechas de revisión, está en `docs/fuentes.md`.

## Archivos

- `src/documento.py`: rehecho el estilo y la maquetación; contenido nuevo (ficha,
  metodología, nota del contraste) y tabla de fuentes.
- `src/metodologia.py` (nuevo): ficha técnica, metodología, fórmula, nota del contraste y
  fuente del perfil, compartidos por la web y el PDF.
- `src/calle.py`: `DIBUJO_TIPO` y `marca_tipo()`, traídos de `app/app.py`.
- `src/fuentes.py`: campo «En uso» de cada conjunto del portal.
- `app/app.py`: usa `src/metodologia.py` y `src/calle.py` (mismos textos), y la tabla de
  fuentes separa la farmacia.
- `README.md`, `docs/registro/2026-11-12-servidor-mcp.md`, `docs/ejemplos/` y
  `docs/capturas/documento-*.png`.
