# BARómetro

Responde siempre en español.

## Proyecto
Prototipo para el datathon DATAMAD 2026 de la Comunidad de Madrid: a partir de la dirección de un local, analiza qué vender, a quién, a qué hora y a qué precio en un bar o restaurante, usando datos abiertos.

## Reglas obligatorias
- El centro del análisis son los datos del Portal de Datos Abiertos de la Comunidad de Madrid (datos.comunidad.madrid).
- Cada fuente usada se anota en docs/fuentes.md con enlace, licencia y fecha.
- Nunca usar datos de Google Maps, Idealista ni otras webs que prohíban su extracción.
- Nunca mostrar nombres de personas que aparezcan en los registros; solo ubicaciones.
- Toda estimación se marca como estimación y se explican sus supuestos.

## Técnico
- Python. Dentro de este entorno usa un entorno virtual llamado .venv-linux (añádelo a .gitignore).
- Datos descargados en datos/originales; datos limpios en datos/procesados.
- No hagas git push; lo hace la autora desde su Mac.

## Git
- En los mensajes de commit no se añade la línea `Co-Authored-By` de Claude ni ninguna otra atribución a Claude.
- La autora de los commits es Mengying Xia Ruan.
