# 2026-11-14 · Comparar dos locales y descargar el informe

## Qué se pidió

Dos funciones nuevas, **sin cambiar los cálculos que ya había**: comparar dos locales (en
la aplicación y en el servidor MCP) y descargar el informe, o la comparación, como
documento.

## Ficheros

- **Nuevos:**
  - `src/comparar.py`: la comparación de dos locales.
  - `src/documento.py`: el documento en PDF.
  - `src/calle.py`: las frases en lenguaje sencillo, que antes estaban en `app/app.py`.
  - `app/letra/`: la letra DejaVu Sans (normal y negrita) y su licencia.
  - `docs/ejemplos/`: dos PDF de muestra (Vicálvaro, y Vicálvaro frente a Griñón).
- **Cambiados:** `app/app.py`, `app/estilo.css`, `mcp/servidor.py`,
  `mcp/probar_cliente.py`, `src/supuestos.py` (dos valores nuevos al final),
  `requirements.txt` (fpdf2), `README.md` y `docs/capturas/`.
- **Sin tocar:** `perfil_horario.py`, `informe_local.py`, `recomendaciones.py`,
  `movimiento.py` y `datos/`.

### Un movimiento de código que no cambia nada

Las funciones que traducen los resultados a palabras sencillas («Vecinos y
universitarios», «De 8 a 10 y a las 14», el titular, las cifras de Mercado…) estaban en
`app/app.py`, que solo puede usar la aplicación. Ahora las necesitan también la
comparación, el PDF y el servidor MCP, así que **se han movido tal cual** a
`src/calle.py`. No se ha reescrito ninguna: la comprobación de abajo (los textos de los
tres ejemplos, idénticos) lo confirma.

## 1. Comparar dos locales

### En la aplicación

- En el Resumen y en el Informe completo hay un botón **«Comparar con otra dirección»**.
- Lleva a un panel con **el mismo buscador y las mismas reglas**: mínimo de 4 letras,
  sugerencias de CartoCiudad, los tres ejemplos y «Usar mi ubicación». Un portal se
  calcula directamente; una calle sin número se enseña en el mapa con «¿Es aquí?» y no se
  calcula hasta confirmar o tocar el mapa. Un punto fuera de la Comunidad avisa y deja
  elegir otro.
- La vista de comparación enseña, en este orden:
  - las dos direcciones, marcadas A y B;
  - once filas: nivel de movimiento (con las dos agujas), gente en un día de diario,
    gente en sábado, quién pasa, horas punta, qué conviene ofrecer, gama de precios,
    competencia a 300 m, competencia frente a su municipio y cómo se llega;
  - el gráfico por horas con las dos curvas superpuestas (día de diario o sábado);
  - los avisos de cada sitio;
  - un resumen final de dos o tres frases.
- **Portátil:** los dos locales lado a lado. **Móvil:** uno debajo de otro.
- Las dos curvas no se distinguen solo por el color: A va en línea continua con puntos
  redondos y B en discontinua con puntos cuadrados.
- Botones de la vista: «Volver al resumen», «Cambiar la segunda dirección» y «Descargar
  comparación (PDF)». Los botones «Resumen» e «Informe completo» de la barra también
  salen de la comparación.
- **Las dos direcciones solo viven en la sesión.** Al volver al resumen, la segunda se
  conserva (el botón pasa a ser «Ver la comparación»); al buscar otra primera dirección,
  tocar el mapa o volver al inicio, se borra.

### Cómo se decide cuál «sale mejor» (`src/comparar.py`)

| Fila | Sale mejor el que tiene… | Cuándo no decide |
|---|---|---|
| Movimiento, gente en diario y en sábado | más gente de paso | diferencia de menos del 15 % |
| Horas punta | más gente en su mejor hora | diferencia pequeña, o fiabilidad baja en alguno |
| Qué conviene ofrecer | más posibles clientes en su mejor momento | lo mismo |
| Competencia a 300 m | menos locales | menos de 3 locales o del 15 % de diferencia; fuentes distintas; faltan locales en el mapa |
| Competencia frente al municipio | menos saturación | no se puede valorar en alguno; fuentes distintas |
| Cómo se llega | mejor nivel de comunicación | mismo nivel |
| Quién pasa, gama de precios, avisos | **nunca hay mejor** | se dice «no es mejor ni peor» |

- **El 15 % es una elección mía** (`COMPARAR_DIFERENCIA_PEQUENA` en
  `src/supuestos.py`, con su explicación): las cifras de personas son estimaciones y no
  distinguen diferencias más pequeñas. Conviene revisarla.
- **«Menos competencia» no se da por bueno sin más:** el veredicto añade que pocos
  locales también puede querer decir poca clientela.
- La intensidad se dice sin exagerar: «algo más», «bastante más» (desde 1,5 veces) o
  «mucha más» (desde 3 veces).
- **El resumen no declara un ganador.** Dice en qué sale mejor cada uno; si uno no sale
  mejor en nada, añade que eso no lo descarta; y acaba recordando que es una
  orientación. Si en alguno hay muy poco paso, lo dice.

### Vicálvaro frente a Griñón

- Sale mejor Vicálvaro en movimiento, gente en diario y en sábado, posibles clientes y
  transporte.
- **No deciden:** las horas punta (fiabilidad baja en Griñón), la competencia a 300 m
  (27 locales del censo municipal frente a 2 de OpenStreetMap, donde seguramente
  faltan) y la competencia frente al municipio (en Griñón no se puede valorar).
- Ni mejor ni peor: el público (vecinos y universitarios frente a vecinos y familias
  con niños) y los precios (económicos frente a medios).

### En el servidor MCP

Herramienta nueva `comparar_locales(lat1, lon1, lat2, lon2)`: devuelve las mismas filas
y el mismo resumen que la aplicación (llama a `comparar()`), la gente por horas de los
dos sitios, las fuentes de ambos y las atribuciones. La descripción pide al asistente
que no declare un ganador y que repita los veredictos que no deciden. Si un punto está
fuera de la Comunidad, el error dice cuál de los dos.

## 2. Descargar el informe

- Botón **«Descargar informe (PDF)»** en el Resumen y en el Informe completo, y
  **«Descargar comparación (PDF)»** en la comparación.
- **Informe (5 páginas):** logotipo, dirección, municipio y fecha; aviso de orientación;
  resumen (titular y las cuatro respuestas cortas); nivel de movimiento; las cuatro
  respuestas con su porqué y su fiabilidad; gente por horas (día de diario y sábado);
  la zona; los ocho bloques de mercado; avisos; comprobaciones en persona; fuentes y
  atribuciones.
- **Comparación (4 páginas):** las dos direcciones, el resumen, las once filas con su
  veredicto, las dos curvas por horas, fuentes y atribuciones.
- **Textos obligatorios**, al final de los dos documentos y en el pie de cada página: el
  aviso de orientación, las fuentes con licencia y fecha (leídas de `docs/fuentes.md`),
  «Powered by CRTM», © colaboradores de OpenStreetMap, CartoCiudad con su CC BY 4.0 y la
  nota de no respaldo.
- **La zona es un esquema, no un mapa:** el círculo de 300 m, los locales con la forma y
  el color de su tipo y las paradas, sin fondo ni rótulos. Así el servidor no descarga
  teselas de OpenStreetMap (su política de uso no lo quiere) y no puede aparecer el
  nombre de ningún local.
- **Se genera en memoria al pulsar el botón** (no antes) y no se escribe en disco. El
  nombre del fichero no lleva la dirección: `barometro_informe.pdf` y
  `barometro_comparacion.pdf`.

### Por qué PDF y no HTML

Elegido **PDF con fpdf2 2.9.0**:

- **Ligera y fiable:** es Python puro (3,5 MB). No necesita un navegador, wkhtmltopdf ni
  bibliotecas del sistema, que es lo que suele fallar en Streamlit Community Cloud. Sus
  dos dependencias son Pillow (ya instalada por Streamlit) y fonttools (30 MB en disco).
- **Medido en el entorno de trabajo,** con los datos de la aplicación ya cargados:

  | Medida | Valor |
  |---|---|
  | Tamaño de cada PDF | 42 a 49 KB |
  | Tiempo por documento | 0,12 a 0,15 s (0,5 s el primero, midiendo memoria) |
  | Memoria al importar fpdf2 | +29 MB, una vez por proceso |
  | Pico de memoria mientras se genera | unos 12 MB |

  El proceso de la aplicación ocupa unos 295 MB antes y unos 350 MB después de cinco
  documentos; el límite de Community Cloud ronda 1 GB.
- **Una página HTML para imprimir** no añadía dependencias, pero obligaba al hostelero a
  usar «Imprimir → Guardar como PDF» y el resultado dependía de su navegador. Queda como
  alternativa si fpdf2 diera problemas en el despliegue.
- **Coste:** hay que llevar la letra en el repositorio (1,4 MB, `app/letra/`). Las
  letras que trae el formato PDF no tienen «≈», «×» ni «→». DejaVu Sans tiene licencia
  libre, incluida al lado.

## Comprobaciones

Con Chromium sin interfaz (Playwright, fuera del proyecto) contra la aplicación en
marcha, en portátil (1.440 × 900) y móvil (390 × 844).

- **Los resultados de los tres ejemplos no cambian.**
  - Las huellas de `src/resumen_ejemplos.py` son las de ayer: `f14a23b7b732`
    (Vicálvaro), `fef42c68a5ee` (Fuenlabrada) y `6f0c2d0d4eec` (Griñón).
  - Comparados todos los textos del Resumen y del Informe completo con los de ayer, en
    1.440, 1.920 y 390 px: **lo único nuevo son los dos botones** («Comparar con otra
    dirección» y «Descargar informe (PDF)»). Nada ha desaparecido ni cambiado.
- **Documentos.** Descargados desde el navegador con el botón, en portátil y en móvil,
  el informe de Vicálvaro y la comparación Vicálvaro–Griñón. Generados además con los
  tres ejemplos desde Python. En todos se ha extraído el texto y **están los ocho textos
  obligatorios** (`TEXTOS_OBLIGATORIOS` en `src/documento.py`). Revisadas las páginas una
  a una.
- **Comparación Vicálvaro–Griñón** en portátil y móvil: sin desplazamiento horizontal ni
  errores de JavaScript; volver al resumen conserva la comparación; las vistas de la
  barra salen de ella.
- **Segunda dirección:**
  - «Paseo de los Artilleros, Madrid» (sin número) pide «¿Es aquí?» y no calcula hasta
    confirmar;
  - una ubicación en Toledo avisa de que está fuera de la Comunidad y deja elegir otra;
  - «Cancelar» vuelve al resumen.
- **Un local comparado consigo mismo** da «diferencia pequeña, no decide» en todas las
  filas numéricas y un resumen que dice que ninguno sale mejor.
- **Servidor MCP** (`mcp/probar_cliente.py`, ampliado): están las cinco herramientas y
  `comparar_locales` devuelve las mismas filas y el mismo resumen que `comparar()`.
  **La prueba sigue dando los 3 fallos de antes** en `informe_de_zona` («los bloques no
  coinciden con informe_local()»), que no son de este trabajo y siguen sin mirar.

**No se ha probado** en la demo pública (Streamlit Community Cloud), ni la memoria allí,
ni en un móvil de verdad. Las medidas son del entorno de trabajo, con Python 3.14; el
despliegue usa 3.12.

## Capturas

En `docs/capturas/`:

- **Nuevas:** `*-resumen-botones`, `*-informe-botones`, `*-comparar-elegir`,
  `*-comparacion`, `*-comparacion-entera` (portátil y móvil),
  `portatil-comparar-confirmar` y las dos primeras páginas de cada PDF
  (`documento-informe-1/2`, `documento-comparacion-1/2`).
- **Rehechas** (ahora con los dos botones): las de los tres ejemplos (`-resumen`,
  `-informe` y sus `-entera`, en portátil, 1.920 px y móvil).
- Siguen sin rehacer las mismas de ayer (`*-barra-*`, `*-sugerencias`…) y las del punto
  sin colegios.

## Limitaciones

- **La comparación hereda las de cada dato.** Entre Madrid capital (censo municipal) y
  cualquier otro municipio (OpenStreetMap), la competencia nunca decide.
- «Sale mejor» compara cifras, no negocios: más gente de paso no es más ventas.
- El resumen se monta con frases fijas; con nombres de dirección largos queda pesado.
- El esquema de la zona del PDF sitúa los locales con una proyección sencilla, suficiente
  para 300 m; no es un plano.
- El PDF no lleva el detalle desplegable de cada pregunta ni las tablas del Informe
  completo: lleva la recomendación principal de cada una con su porqué.
- En el PDF de la comparación, las horas punta de las curvas no van rotuladas.
- Si la sesión caduca, la comparación se pierde, como el resto del resultado.
