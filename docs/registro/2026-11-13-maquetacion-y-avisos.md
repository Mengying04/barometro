# 2026-11-13 · Maquetación (rejilla y pie) y avisos concretos del sitio

## Qué se pidió

Tres ajustes de maquetación y de avisos, **sin cambiar cálculos**: anchos coherentes en
toda la aplicación, un pie de página diseñado y que «Ojo con esto» dé avisos propios de
cada sitio, con su cifra.

## Ficheros tocados

- `app/app.py`, `app/estilo.css` y `app/buscador.js`.
- `src/recomendaciones.py` (solo la función `riesgos()` y tres ayudas para redactar) y
  `src/supuestos.py` (tres valores nuevos, en «B4. avisos y riesgos»).
- `mcp/servidor.py`: solo la descripción de la herramienta `recomendar_local`.
- `docs/capturas/`: capturas rehechas y nuevas (lista al final).
- **Ningún fichero de `datos/` ha cambiado.**

## 1. Una sola rejilla

**Qué pasaba.** En el Informe completo los recuadros, los desplegables y las listas medían
unos 1.070 px, pero el texto se cortaba a 42 rem: quedaba un hueco vacío a la derecha.
El Resumen y el Informe tenían anchos distintos (1.120 y 1.400 px), y el índice lateral
no empezaba donde el logotipo de la barra.

**Cómo queda** (`app/estilo.css`, variables al principio del fichero):

- **Un ancho máximo de contenido para todas las vistas: 1.280 px** (`--ancho`), con un
  margen lateral simétrico de 2,5 rem (`--margen`; 1,5 rem entre 641 y 1.100 px y 1 rem
  en el móvil). Antes el margen era de 1,5 rem.
- **La barra superior, el índice, el contenido y el pie comparten los mismos bordes.**
  Medido en el navegador: a 1.440 px, todo empieza en el píxel 80 y acaba en el 1.360; a
  1.920 px, en el 320 y el 1.600; en el móvil, en el 18 y el 372.
- **Informe completo: cada sección es una rejilla de dos columnas.**
  - A la izquierda, la **columna de lectura** (40 rem, unas 80 letras por línea): el
    texto, las listas y los desplegables miden lo mismo.
  - A la derecha, un **recuadro de apoyo** con contenido útil, que acompaña a la lectura
    al bajar por la sección:

    | Sección | Recuadro de apoyo |
    |---|---|
    | Nivel de movimiento | La aguja y las personas que pasan en un día laborable |
    | A quién | «De cada 10 posibles clientes» y la fiabilidad |
    | A qué hora | La mejor hora con sus personas y la fiabilidad |
    | Qué vender | Barras pequeñas por momento del día y la fiabilidad |
    | A qué precio | La subida de precios del año y la fiabilidad |
    | Riesgos y avisos | Los avisos sobre los datos |
    | Qué comprobar en persona | Cuántas comprobaciones son y el botón de descarga |
    | Fuentes y licencias | Las atribuciones |

  - Ocupan todo el ancho, como antes: el gráfico del perfil, las tablas y los ocho
    bloques de Mercado (en dos columnas; dentro de cada bloque, texto y recuadro miden
    lo mismo).
- **Resumen:** «Ojo con esto» y «Antes de decidir, compruébalo tú» van en dos columnas
  iguales (antes eran franjas a todo el ancho con una línea corta dentro). El mapa y el
  gráfico tienen ahora la misma altura.
- **Portada:** «Fuentes y licencias» usa la misma rejilla (lista a la izquierda,
  atribuciones a la derecha).
- **Pantallas más estrechas:** el índice lateral aparece desde 1.280 px (antes, 1.100);
  por debajo se usa el menú «Secciones». Por debajo de 1.000 px las dos columnas pasan a
  una y el recuadro de apoyo queda debajo de su texto.

**No se calcula nada nuevo.** Los recuadros de apoyo enseñan lo que ya daban
`recomendar()`, `informe_local()` y `nivel_movimiento()`; cuatro de ellos son los mismos
que ya salían al abrir una tarjeta del Resumen. Las barras pequeñas de «Qué vender» son
las del Resumen dibujadas en estrecho.

## 2. Pie de página

- Franja a todo el ancho, del color oscuro de la barra, **igual en todas las vistas**
  (portada, Resumen, Informe y «¿Es aquí?»).
- Contenido, en columnas: el logotipo con el nombre y una frase; **Atribuciones**
  («Powered by CRTM» con enlace, © colaboradores de OpenStreetMap con enlace y
  CartoCiudad con su mención CC BY 4.0 y su enlace); **Datos** (fecha de descarga,
  «Fuentes y licencias» y el repositorio); y debajo, el aviso de orientación y la nota
  de que ninguna entidad respalda el proyecto. En el móvil, todo apilado.
- **«Fuentes y licencias» lleva siempre a esa sección:** en la portada y en el Informe,
  baja hasta ella; desde el Resumen, abre el Informe completo y baja; con una dirección
  sin confirmar, vuelve a la portada y baja. Lo atiende `app/buscador.js`. Desaparece el
  botón suelto que había debajo del pie.

## 3. Avisos concretos del sitio

Los avisos se generan en `riesgos()` (`src/recomendaciones.py`) y son los mismos en
«Ojo con esto», en «Riesgos y avisos» del Informe y en la respuesta del servidor MCP.

**Las reglas que deciden cuándo hay aviso no cambian, salvo la de festivos.** Tampoco las
cifras. Cambian la redacción, el orden y el máximo.

| Aviso | Regla | Ejemplo de cómo se dice ahora |
|---|---|---|
| Colegios | Sin cambios (15 % o más de la gente de un laborable) | «Aquí 1 de cada 2 personas que pasan en un día de diario son familias del colegio: en vacaciones escolares (Navidad, Semana Santa, julio y agosto) lo notarás.» |
| Universidad | Sin cambios (15 % o más) | «Aquí 1 de cada 5 personas que pasan en un día de diario son universitarios: en vacaciones de la universidad (…) lo notarás.» |
| Competencia alta | Sin cambios (más de 1,5 veces la media) | «Ya hay 25 bares y restaurantes a menos de 300 m: 2,1 veces lo normal en Fuenlabrada.» |
| Festivos | **Cambia:** solo los de los próximos 30 días | «Vienen festivos: el lunes 7 de diciembre (Día de la Constitución Española) y el martes 8 de diciembre (Inmaculada Concepción). Esos días…» |
| Faltan locales en el mapa | Sin cambios | «Seguramente hay más de 2 bares y restaurantes cerca: el mapa colaborativo que usamos recoge en Griñón 1,1 locales por cada 1.000 vecinos, y el censo oficial de Madrid capital, 5.» |
| Competencia sin valorar | Sin cambios | «En Griñón hay tan pocos bares (menos de 1 de media en un círculo como este) que no podemos decir si 2 bares y restaurantes a menos de 300 m son mucha o poca competencia.» |

- **Festivos.** Antes salía «Festivos próximos» siempre que hubiera alguno publicado en
  los 12 meses siguientes, es decir, casi siempre. Ahora solo si hay uno en los próximos
  30 días (`RIESGO_FESTIVO_DIAS`), y se dice cuál y qué día. Una fiesta local se nombra
  como tal: «el sábado 26 de diciembre (fiesta local en Fuenlabrada)». El resto de
  festivos sigue en el bloque «Festivos» de Mercado.
- **«1 de cada N».** La proporción se dice con la fracción sencilla más cercana (el 46 %
  es «1 de cada 2»; el 19 %, «1 de cada 5»). **Es solo una forma de decirlo:** el
  porcentaje exacto sigue en el «Por qué» del Informe y en el servidor MCP.
- **Orden y máximo.** Como mucho tres (`MAX_RIESGOS`), en este orden
  (`ORDEN_RIESGOS`): colegios o universidad, competencia alta, festivos, faltan locales
  en el mapa y competencia sin valorar. Primero lo que cambia el negocio, después lo
  que tiene fecha y al final los límites de los datos.
- **Sin avisos:** una sola frase, «No vemos nada especial que vigilar en esta zona».
- Cada aviso lleva un campo nuevo, `clave`, y conserva `texto`, `porque`, `confianza` y
  `base`. La aplicación elige el icono por la clave, no por cómo empieza el texto.

### Decisiones mías que conviene revisar

- **Los festivos nacionales cuentan como aviso.** Pediste «local o regional». El conjunto
  del portal mezcla regionales y nacionales en la misma lista («regional o nacional») y
  no los distingue, así que el 7 y el 8 de diciembre salen. Si solo quieres los locales,
  es un cambio de una línea.
- **Con cuatro avisos, el cuarto no se enseña.** En Griñón se cumplen cuatro reglas y
  deja de verse «competencia sin valorar» (antes, con el orden antiguo, se quedaba fuera
  el de festivos). El máximo de tres se aplica también al Informe completo y al
  servidor MCP, como pediste; si en el Informe prefieres verlos todos, se cambia en
  `MAX_RIESGOS` o se separa por vista.
- **El orden pone festivos por delante de los dos avisos sobre los datos.** Antes iban al
  final.

## Comprobaciones

Con Chromium sin interfaz (Playwright, fuera del proyecto), contra la aplicación en
marcha, en portátil (1.440 × 900 y 1.920 × 1.080) y móvil (390 × 844). Puntos: los tres
ejemplos y uno sin colegios ni universidad cerca (calle de Serrano, Madrid; 40,4300,
−3,6870; peso de colegios y de universidad, 0 %).

- **Los resultados de los tres ejemplos no cambian.**
  - La huella de todo el resultado, quitando los avisos, es idéntica antes y después en
    los tres puntos (`ac4624aef735`, `4ee0950dd409` y `675ae58b36c3`). La huella
    completa de `src/resumen_ejemplos.py` sí cambia, porque incluye el texto de los
    avisos.
  - En pantalla, comparando todos los textos de antes y de después en los tres tamaños:
    iguales el titular, el nivel de movimiento, las cuatro tarjetas, «Cómo se llega»,
    las comprobaciones, las respuestas del Informe, las etiquetas, las ocho cifras de
    Mercado y todos los párrafos y listas. **Lo único distinto:** los avisos, el pie, la
    fiabilidad repetida en los recuadros de apoyo y el desplegable «Copiar o descargar
    la lista», que ahora es «Copiar la lista» con el botón de descarga al lado.
- **Rejilla:** sin desplazamiento horizontal en ninguna vista ni tamaño (tampoco a
  1.280, 1.100, 1.000, 820 y 700 px, probados en el Informe de Vicálvaro). Revisadas
  las capturas sección por sección. Sin errores de JavaScript.
- **Pie:** sin hueco por debajo; el enlace «Fuentes y licencias» probado desde la
  portada y desde el Resumen en los tres tamaños.
- **Avisos:**
  - punto sin colegios ni universidad: solo sale el aviso de festivos, sin ninguno de
    vacaciones;
  - **el caso sin ningún aviso no se da hoy en ningún punto,** porque el 7 y el 8 de
    diciembre caen dentro de los 30 días. Se ha probado llamando a `riesgos()` con la
    fecha cambiada al 1 de septiembre de 2026: devuelve la frase en positivo. **No se ha
    visto en pantalla;**
  - con la fecha cambiada al 10 de diciembre, Fuenlabrada dice «el sábado 26 de
    diciembre (fiesta local en Fuenlabrada)».
- **Servidor MCP** (`mcp/probar_cliente.py`): los avisos de `recomendar_local`
  coinciden con los de `recomendar()`. **La prueba da 3 fallos, los mismos que antes de
  estos cambios** («informe_de_zona: los bloques no coinciden con informe_local()», uno
  por ejemplo). No son de este trabajo y no se han tocado; están pendientes de mirar.

**No se ha probado** en la demo pública ni en un móvil de verdad.

## Capturas

En `docs/capturas/`:

- **Rehechas:** `portatil-*` y `movil-*` de los tres ejemplos (`-resumen`, `-informe` y
  sus `-entera`), `*-portada`, `*-portada-fuentes` y `*-vicalvaro-tarjeta-abierta`.
- **Nuevas:** `portatil-1920-*-entera` (los cuatro puntos a 1.920 px),
  `*-sin-colegios-*-entera` (el punto sin colegios ni universidad) y `*-pie`.
- **Sin rehacer** (enseñan todavía los márgenes y el pie antiguos): `*-barra-*`,
  `*-cabecera-fija`, `*-calle-sin-numero`, `*-fuera-de-madrid`, `*-muy-poco-paso`,
  `*-sugerencias`, `*-informe-indice`, `movil-informe-menu` y
  `portatil-direccion-elegida`.

## Limitaciones

- **La barra y el pie se alinean con el ancho de la ventana; el contenido, con el de la
  zona que se desplaza.** En un navegador con barra de desplazamiento siempre visible
  (Windows) puede haber unos píxeles de diferencia. En las pruebas, sin esa barra,
  coinciden.
- El recuadro de apoyo que acompaña a la lectura y la rejilla siguen apoyándose en
  nombres internos de Streamlit: al actualizarlo hay que volver a probar.
- A 1.280 px justos la columna de lectura baja a unos 630 px (unas 70 letras).
- Los avisos dependen de la fecha del día: el de festivos aparece y desaparece solo.
