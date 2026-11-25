# 2026-11-25 · Fuera «Oficinas de farmacia»

Se quita del proyecto el conjunto «Oficinas de farmacia» (`oficinas_farmacia`) del Portal de
Datos Abiertos de la Comunidad de Madrid. Se descargaba y se procesaba, pero no entraba en
ningún cálculo. No cambia ningún otro cálculo, dato ni texto.

## Cambios

- **Descarga** (`src/descargar_datos.py`): fuera de `CONJUNTOS` y fuera la nota que lo
  explicaba en `docs/fuentes.md`. La actualización semanal de los lunes ya no lo descarga.
  Tampoco lo echa en falta: ningún script ni el flujo esperaba ese conjunto.
- **Procesado** (`src/procesar.py`): fuera la capa `farmacias`. Las notas de coordenadas ya
  no la nombran. El censo de locales sigue citado como contrastado.
- **`docs/fuentes.md`**: fuera la fila del portal, la nota y la fila de la capa en «Datos
  procesados». El texto queda igual que si lo escribieran los scripts.
- **`src/fuentes.py`, `app/app.py`**: solo los comentarios. El grupo «Descargada, no se usa
  en los cálculos» de la web y del PDF (`src/documento.py`) ya solo salía si había alguna
  fuente en ese caso. Ahora no hay ninguna y no sale. `src/documento.py` no cambia.
- **README**: el párrafo del PDF ya no habla de la farmacia. Los 15 conjuntos descargados
  son los 15 en uso. Las tablas generadas (`src/tablas_readme.py`) no cambian.
- **`datos/LICENCIAS.md`**: no nombraba la farmacia. No cambia.
- **No se borra** `datos/originales/oficinas_farmacia/` ni `datos/procesados/farmacias.parquet`.
  Están fuera de git.
- El comentario de `src/supuestos.py` que menciona «farmacias» habla de la categoría «Otros»
  de los locales, no de este conjunto. Se deja.

## Comprobaciones

| Prueba | Resultado |
|---|---|
| `python src/comprobar_datos.py` | 38 comprobaciones, 0 con fallo |
| `python mcp/probar_cliente.py` | Todo correcto |
| Huellas de `src/resumen_ejemplos.py` | Iguales a las de `v1.0-datamad-final`, calculadas el mismo día (2026-11-25), en un `git worktree` aparte |
| AppTest: Informe completo de Vicálvaro y comparación Vicálvaro–Griñón, sin tipo y con «bar de barrio» | Sin excepciones. Tabla de fuentes de la web con 15 filas del portal y solo los rótulos «Portal…» y «Otras fuentes». Sin «farmacia» en la web. Los cuatro PDF (informe y comparación) llevan los ocho `TEXTOS_OBLIGATORIOS` y «15 conjuntos en uso». Su tabla tiene 15 filas del portal, sin «farmacia» ni el rótulo de no usadas |
| AppTest: portada | Tabla de fuentes con 15 filas del portal, sin «farmacia» |
| `actionlint` 1.7.12 sobre `.github/workflows/actualizar-datos.yml` | Sin errores |
| Chromium sin interfaz (Playwright, fuera del proyecto) | Sin errores de JavaScript |

## PDF y capturas

- **PDF de muestra** de `docs/ejemplos/`: rehechos con «Bar de barrio». Su texto solo
  cambia en las filas de la farmacia y en el commit de la ficha técnica.
- **Capturas rehechas** con Chromium sin interfaz: las 14 que enseñan la tabla de fuentes.
  Son `portatil-portada-fuentes` y `movil-portada-fuentes`, y las 12 `*-informe-entera`
  (Vicálvaro, Fuenlabrada, Griñón y el punto sin colegios, a 1.440, 1.920 y 390 px).
  Las `documento-*.png` no enseñan la tabla de fuentes y no se tocan.

## Etiqueta

`v1.0.1-datamad-final`.
