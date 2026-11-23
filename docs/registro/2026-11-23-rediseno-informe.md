# 2026-11-23 · Rediseño visual: escala tipográfica, cabecera común e Informe como informe

## Qué se pidió

Un rediseño **solo visual** de la aplicación, sin cambiar cálculos, datos ni lo que dicen
las respuestas, y tocando solo `app/` (`app.py`, `estilo.css`, `buscador.js`) y
`.streamlit/config.toml`. Objetivo: que parezca un informe profesional, fácil de leer y de
seguir, con más impacto visual. Además: capturas y PDF de muestra rehechos, el principio del
README revisado y este registro.

Antes de tocar nada se guardaron, fuera del repositorio, capturas de todas las vistas (390,
1.280, 1.440 y 1.920 px) y los textos de 42 vistas volcados con AppTest, para comparar al
final.

## Qué se ha hecho

### 1. Tipografía (todas las vistas)

- Letra base de 16 px (antes 18) e Inter solo con los pesos 400, 600 y 700.
- Una sola escala, definida como variables en `app/estilo.css`, y nada fuera de ella:

  | Tamaño | Uso |
  |---|---|
  | 0,75 rem | Rótulos en mayúsculas (espaciado 0,08em) y etiquetas |
  | 0,875 rem | Notas, pies y fuentes |
  | 1 rem | Texto |
  | 1,25 rem | Títulos de bloque |
  | 1,75 rem | Títulos de sección |
  | 2,5 rem | Título de página |
  | 3 rem | Cifras destacadas |

- Pesos: 400 texto, 600 títulos de bloque y botones, 700 títulos y cifras. Se ha quitado
  el 800.
- Interlineado 1,6 en texto y 1,2 en títulos; espaciado negativo solo desde 1,75 rem;
  números tabulares en toda la página.
- Texto corrido de 72 letras por línea como mucho (34 rem a 16 px; 30 rem en la letra
  pequeña).
- Los gráficos usan 12 y 14 px (dentro de la escala).

### 2. Cabecera común

- En todas las vistas con resultado: logotipo, buscador, cambio Resumen / Informe completo
  y un **botón de menú (tres rayas)** con Cómo funciona, Fuentes y licencias, Planes y
  Repositorio. En el Informe completo, cuando no hay sitio para el índice lateral, el
  mismo menú lleva también las diez secciones.
- Portada: en pantallas anchas los cuatro enlaces siguen a la vista; desde 860 px hacia
  abajo, el menú.
- Planes y «Cómo funciona» sin resultado: la misma cabecera, sin buscador. El botón de
  volver se mantiene.
- «Cómo funciona», desde una vista sin esa sección (Resumen, Informe, comparación…), abre
  una página aparte con los tres pasos de la portada y el botón de volver, en vez de
  borrar el resultado para ir a la portada.

### 3. Informe completo

- **Sin recuadros de apoyo a la derecha.** Lo que había en ellos (aguja, cifra, «de cada
  10», reparto, fiabilidad y descarga) pasa a una **fila de datos clave** al principio de
  cada sección: de 2 a 4 tarjetas pequeñas con la cifra, su etiqueta y la etiqueta de
  fiabilidad o de dato/estimación.
- **Secciones numeradas** («01 Nivel de movimiento» … «10 Fuentes y licencias»), con una
  línea fina encima y el mismo esquema: datos clave, porqué, detalle desplegable a todo el
  ancho y una línea final pequeña y gris «Fuente: … · Dato/Estimación». El índice lateral
  y el menú llevan también los números.
- **Desplegables a todo el ancho;** los de texto largo (todas las recomendaciones, el
  porqué de los avisos, las condiciones de las fuentes) en dos columnas desde 1.100 px.
- **Mercado:** los 8 bloques en una cuadrícula de tarjetas (qué es, cifra, una frase y
  dato/estimación; «Con avisos» si sus notas los traen) y un solo desplegable «Notas,
  métodos y fuentes del mercado», con un subtítulo por bloque (dos bloques por fila desde
  1.100 px).
- **Fuentes y licencias:** una tabla (fuente, licencia, fecha, enlace) con enlaces de texto
  corto («ficha», «aviso legal», «copyright», «portal», «servicio»), nunca la dirección
  entera. En el móvil, una ficha por fuente. Debajo, un desplegable con las versiones de los
  datos, los enlaces y las condiciones completas de las otras fuentes (lo que antes salía
  como lista, también con enlaces cortos) y una caja a todo el ancho con las atribuciones
  obligatorias.
- Las direcciones web sueltas que traían las notas y licencias del mercado (por ejemplo,
  la de OpenStreetMap) también pasan a enlaces cortos.
- **Índice lateral:** sigue fijo, pero al llegar al pie sube con él y nunca se monta encima
  (antes lo tapaba el pie a 1.280 y 1.440 px). Comprobado bajando hasta el final a 1.280,
  1.440 y 1.920 px.
- Cabecera del informe: rótulo «Informe completo», la dirección como título de página y
  «Radio de 300 m · calculado en … s».

**Líneas «Fuente».** Salen de lo que ya usa cada sección, sin inventar nada: el perfil por
horas (CRTM, Portal de Datos Abiertos de la Comunidad de Madrid, INE y OpenStreetMap, como
en `docs/fuentes.md`) y los supuestos de `src/supuestos.py`; en «A qué precio», los
nombres de las fuentes del bloque de precios; en Mercado, la remisión al desplegable, donde
cada bloque cita las suyas. Dato o estimación es el de la recomendación de la sección.

**Sin fila de datos clave:** «Perfil por horas» (son los gráficos) y «Fuentes y licencias»
(es la tabla). Añadir cifras ahí habría sido añadir contenido.

### 4. Resumen

Solo la escala tipográfica: mismas cuatro tarjetas, misma explicación abierta y mismo
contenido. Revisado bajando hasta el pie en los cuatro anchos: nada se solapa.

### 5. Página de planes

- Título grande centrado, una frase, el aviso de DATAMAD 2026 en una línea (en el móvil
  ocupa dos) y dos pestañas: «Para hosteleros» (Gratis e Informe) y «Para profesionales e
  instituciones» (Profesional e Institucional).
- Tarjetas con icono, nombre, una frase, la forma de pago en grande («Gratis», «Pago
  único», «Suscripción», «Licencia anual») con «Precio por definir» en pequeño y de 3 a 4
  líneas con marca de verificación de 7 palabras como mucho. «Por hacer» como etiqueta.
- Plan Informe destacado con un borde y la etiqueta «Para traspasos y alquileres».
- Gratis: botón «Probar ahora», que lleva al buscador (con resultado, al de la cabecera;
  sin él, al de la portada) y deja el cursor dentro. Los demás: solo el enlace «Me
  interesa» al repositorio, sin aspecto de botón.
- Animación al entrar: título, frase, aviso, pestañas y tarjetas suben con un fundido,
  escalonados 80 ms; todo termina antes de 0,9 s. Sin animación con `prefers-reduced-motion`.
- Debajo, en pequeño, la compatibilidad con las licencias. Se ha añadido que, con el
  logotipo de un cliente, las fuentes y atribuciones se mantienen siempre (antes estaba en
  la tarjeta Profesional).
- Sigue sin haber precios, campos, formularios, botones de compra, registro ni recogida de
  datos.

### 6. Sin perder nada

Siguen: el aviso de orientación, Powered by CRTM, © colaboradores de OpenStreetMap, la
mención de CartoCiudad (que es la mención literal que pide CartoCiudad, por eso es la
única dirección web que se ve), la nota de no respaldo, el zoom máximo 16 y la privacidad
de las direcciones. El gris de las notas (`--tenue`) pasa de #8a7f73 (3,75:1) a #6f655a
(5,5:1) para llegar al contraste 4,5:1.

## Pruebas

| Prueba | Resultado |
|---|---|
| Huellas de `src/resumen_ejemplos.py` antes y después | Iguales en los tres puntos |
| AppTest: portada, planes, tres ejemplos (Resumen e Informe, tres días), comparación con domingo, los dos PDF y los textos obligatorios | 17 de 17 bien |
| AppTest: tres puntos × cinco tipos de local y general (cuatro tarjetas, gráfico de clientes, Informe en los tres días; sin cifras de clientes en el Resumen) | Todo correcto |
| AppTest: «Cómo funciona» y planes con y sin resultado y con una dirección sin confirmar | Sin excepciones, botón de volver correcto |
| Chromium a 390, 1.280, 1.440 y 1.920 px: portada, Resumen, Informe, planes y comparación, bajando hasta el pie | Sin errores de JavaScript, sin desplazamiento horizontal, sin textos solapados, el índice nunca sobre el pie |
| Chromium, en cada vista: tamaños de letra, pesos, contraste y direcciones web visibles | Todo dentro de la escala; pesos 400, 600 y 700; ningún texto por debajo de 4,5:1; ninguna dirección web (salvo la mención de CartoCiudad) |
| Letras por línea en el texto corrido | 70 como mucho |
| Navegación en Chromium (1.440 y 390 px): menú de la portada y de la cabecera, Fuentes desde el Resumen, secciones desde el menú, Cómo funciona, pestañas de planes, Probar ahora | Todo funciona |

**Comparación de textos** (las 42 vistas volcadas con AppTest, palabra a palabra):

- Resumen (con y sin tipo de local y con cada tarjeta abierta), comparación, elegir la
  segunda dirección y dirección sin confirmar: **no se pierde ninguna palabra**; solo se
  añade «Cómo funciona» en el pie.
- Informe completo: solo desaparecen trozos de direcciones web (ahora enlaces cortos), la
  cabecera de la antigua tabla del portal y los rótulos viejos («Detalle, notas y fuentes»,
  «Por qué» de cada aviso). Se añaden los números de sección, los rótulos («Respuesta»,
  «Fiabilidad», «Gente que pasa», «Descarga»…), las líneas de fuente y la cabecera del
  informe. Ninguna respuesta cambia.
- Planes: texto más corto, como se pidió.

Durante las pruebas apareció un «None» suelto en planes: la «magia» de Streamlit pintaba el
valor de una expresión (`vista_planes() if … else vista_como()`). Se cambió por un `if`.

## Capturas y PDF

Rehechas **las 89** de `docs/capturas/` con Chromium sin interfaz (Playwright, fuera del
proyecto), con los mismos nombres, y los dos PDF de muestra de `docs/ejemplos/` (y sus
imágenes `documento-*.png`). En los tres ejemplos y en la comparación está elegido «Bar de
barrio» en «¿Qué tipo de local?». Sin fallos, sin avisos y sin errores de JavaScript.

## Archivos

- `app/app.py`, `app/estilo.css`, `app/buscador.js`, `.streamlit/config.toml`.
- `README.md`: una frase de qué diferencia a BARómetro al principio, el Informe por
  secciones y la nueva página de planes.
- `docs/capturas/` y `docs/ejemplos/`: rehechos.
