# 2026-11-26 · Sección «Estado del proyecto» en el README

Se añade al principio del README, debajo del título, una sección corta «Estado del
proyecto» (11 líneas con el título). No cambia ningún código, dato, cálculo ni supuesto.

## Contenido

- Presentado a DATAMAD 2026, el datatón de datos abiertos de la Comunidad de Madrid
  (26 de noviembre de 2026). No se dice «finalista».
- Qué funciona: 15 conjuntos de la Comunidad y otras fuentes integrados, actualización
  semanal con 38 comprobaciones, reproducible con Docker, servidor MCP.
- Qué no funciona bien, con enlace a `docs/validacion.md`: en día laborable no coincide con
  los aforos de peatones; fuera de Madrid capital OpenStreetMap recoge menos de la mitad de
  los locales; en polígonos industriales no ve a los trabajadores de empresas pequeñas; los
  tipos de local no están calibrados.
- Desarrollo cerrado.

## Respaldo de cada frase en el repositorio

| Frase | Dónde está |
|---|---|
| 15 conjuntos en uso | README («15 descargados, 15 en uso»), `docs/fuentes.md` |
| 38 comprobaciones | README, `src/comprobar_datos.py` |
| Docker, servidor MCP | README («O con Docker»), `docs/despliegue.md`, `mcp/` |
| Laborable frente a aforos | `docs/validacion.md`, «Contraste con aforos de peatones» |
| Tipos de local sin calibrar | `docs/validacion.md` («Lo que esto no es: una calibración»), README, «Limitaciones conocidas» |
| OpenStreetMap, menos de la mitad de los locales fuera de Madrid capital | **Sin cifra en el repositorio.** El README solo dice que «le faltan locales». La cifra la da la autora |
| Polígonos industriales y trabajadores de empresas pequeñas | **No está escrito en el repositorio.** La da la autora |

`docs/validacion.md` no cambia: las dos últimas limitaciones quedan enlazadas a un
documento que todavía no las recoge.
