# 2026-11-12 · Servidor MCP (fase 4, parte B)

## Punto de partida

La carpeta `mcp/` existía desde el 9 de noviembre, pero estaba vacía y git no la seguía.

## Qué se ha hecho

- **`mcp/servidor.py`:** servidor MCP en Python, en local por stdio, con el SDK oficial
  (`mcp==2.3.0`). En la versión 2 del SDK, la clase `FastMCP` pasó a llamarse
  `MCPServer`; es la misma interfaz. Si se prefiere `FastMCP` con ese nombre, habría
  que fijar `mcp<2`.
- **Cuatro herramientas,** con descripciones en español, que solo llaman a las
  funciones de `src/`:
  - `recomendar_local(lat, lon)` → `recomendar()`;
  - `perfil_por_horas(lat, lon)` → `perfil_horario()`;
  - `informe_de_zona(lat, lon)` → `informe_local()`;
  - `buscar_direccion(texto)` → `geocodificar()` y `coordenadas()`.
- **Código compartido con la aplicación,** para no repetirlo: el buscador de
  CartoCiudad pasa a `src/direcciones.py` y el lector de `docs/fuentes.md` a
  `src/fuentes.py`. `app/app.py` los importa; su comportamiento no cambia.
- **Cada respuesta incluye** el aviso de orientación con estimaciones, las fuentes con
  licencia y fechas (leídas de `docs/fuentes.md` y de los bloques del informe) y
  «Powered by CRTM».
- **Privacidad:** no se escriben ficheros ni registros con los puntos o direcciones, no
  hay caché por punto y el nivel de registro es solo de avisos. No se devuelven
  nombres de locales; el buscador descarta topónimos y puntos de interés.
- **Fuera de la Comunidad de Madrid:** error claro, sin calcular nada.
- **`requirements.txt`:** `mcp==2.3.0`. La aplicación web no lo necesita.
- **README:** sección corta con la conexión a Claude Code y Claude Desktop.

## Pruebas

`mcp/probar_cliente.py` arranca el servidor por stdio con el cliente del SDK y llama
a cada herramienta con los tres puntos de ejemplo. Resultado: todo correcto.

- Están las cuatro herramientas.
- En los tres puntos, `recomendar_local` e `informe_de_zona` devuelven lo mismo que
  `recomendar()` e `informe_local()` llamadas directamente, y los totales por franja
  de `perfil_por_horas` coinciden con `perfil_horario()`.
- Todas las respuestas llevan aviso, fuentes con licencia y fecha y «Powered by CRTM»
  (entre 12 y 21 fuentes según la herramienta).
- `buscar_direccion` encuentra las tres direcciones probadas y no devuelve nombres de
  comercios. Para «Paseo de los Artilleros 38» propone el 35: CartoCiudad da portales
  cercanos.
- Un punto de Toledo da error en las tres herramientas, con el mensaje «Ese punto
  está fuera de la Comunidad de Madrid…».
- La salida de errores del servidor queda vacía: no aparecen puntos ni direcciones.
- La aplicación web da los mismos textos que antes de mover el buscador.

### Prueba dentro de Claude Code

Con `claude -p`, el servidor cargado desde un fichero de configuración
(`--mcp-config`) y la pregunta de ejemplo del README («Quiero abrir un bar en la
Plaza de la Constitución 1 de Fuenlabrada. ¿Qué me conviene ofrecer y a qué horas?»):

- el servidor aparece como conectado, con sus cuatro herramientas;
- el asistente llamó primero a `buscar_direccion` y, con las coordenadas que devolvió,
  a `recomendar_local`, `perfil_por_horas` e `informe_de_zona`, sin errores;
- la respuesta empezó diciendo que es una orientación con estimaciones y no una
  garantía, avisó de que el buscador puede situar un portal cercano, no nombró
  locales ni dio precios en euros, y terminó con las fuentes y «Powered by CRTM».

### Instalación

Con `mcp==2.3.0` añadido, sigue habiendo paquetes de todas las dependencias para
Python 3.12 y 3.13 (comprobado pidiéndolos a PyPI), y `pip check` no encuentra
conflictos.

## Limitaciones

- **No se ha probado en Claude Desktop,** solo en Claude Code y con el cliente de
  prueba del SDK. La configuración es la misma (un comando y un argumento).
- Las respuestas son largas (13 a 35 kB de texto por llamada).
- `mcp` queda en `requirements.txt`, así que Streamlit Community Cloud también lo
  instalará, aunque la aplicación no lo use. No se ha vuelto a desplegar con él.
