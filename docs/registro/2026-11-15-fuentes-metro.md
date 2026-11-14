# Fuentes de horarios de Metro de Madrid más recientes que el GTFS del CRTM (versión 20250527)

Consulta hecha el 2026-11-14 (hora de Madrid) en los dominios que ya están permitidos: nap.transportes.gob.es, datos.metromadrid.es, www.metromadrid.es y datos.gob.es. **No se ha cambiado nada del proyecto**: este registro es lo único nuevo y no tiene commit.

## Respuesta corta

**No existe una fuente oficial y abierta de horarios de Metro de Madrid más reciente que el GTFS del CRTM versión 20250527.** Todas las fichas oficiales que hay en esos portales (NAP, datos.gob.es y, a través de este, datos.comunidad.madrid) llevan al **mismo fichero** que ya usamos: el ítem `5c7f2951962540d69ffe8f640d94c246` del CRTM (`google_transit_M4.zip`), que no se ha modificado desde el 30/05/2025. La única información más reciente es la tabla de «intervalo medio entre trenes» de la web de Metro de Madrid, y no es abierta: su aviso legal prohíbe usarla sin autorización escrita. Por eso no hay que cambiar nada. La línea 3 sigue reconstruida (estimación) como hasta ahora.

## Qué se ha mirado y qué se ha encontrado

### 1. Punto de Acceso Nacional (NAP), nap.transportes.gob.es

- Ficha «Metro de Madrid», https://nap.transportes.gob.es/ConjuntoDato/Detail/933
- **Publica:** CRTM (Consorcio Regional de Transportes de Madrid), como responsable de la publicación y de los datos. El NAP (Ministerio de Transportes y Movilidad Sostenible) solo la aloja.
- **Fecha:** «Actualizado el 30/5/2025». Fecha de los metadatos: 30/05/2025 17:25. El listado general dice «Actualizado el 5/8/2026», pero la ficha y el fichero son de mayo de 2025: lo que se tocó en agosto fue el registro del catálogo, no los datos.
- **Vigencia:** «Válido desde 01/01/2025 hasta 27/05/2026» (rango de fechas que muestra la ficha: 31/12/2024–26/5/2026). **Caducado.**
- **Contenido:** 1.050 paradas, 13 rutas y 120 viajes, «validado correctamente». Son exactamente las mismas cifras que nuestro `datos/originales/crtm_paradas/gtfs_metro.zip`: 1.050 registros en stops.txt, 13 líneas y 120 viajes-plantilla en trips.txt (feed_version 20250527, calendario 20250527–20260527). Tamaño: 1,43 MB, que coincide con los 1.503.773 bytes del ítem del CRTM. **Conclusión: es el mismo fichero.**
- **Licencia:** «Licence and Free of charge», con enlace a la [Licencia de datos abiertos del MITRAMS](https://nap.transportes.gob.es/licencia-datos). Permite la reutilización comercial y no comercial: copia, difusión, modificación, extracción y combinación. Los datos siguen siendo del CRTM y su propia licencia (https://www.crtm.es/licencia-de-uso) tiene más obligaciones: «Powered by CRTM», mantener los datos actualizados, citar la fuente, etc.
- **Condición de uso práctica:** para descargarlo del NAP hay que iniciar sesión (registro gratuito). No lo he descargado porque no hace falta: metadatos, cifras y tamaño coinciden con el ítem del CRTM.
- En el NAP también aparecen las fichas del CRTM de Metro Ligero (5/11/2026), Cercanías, EMT e interurbanos, que coinciden con las que ya usamos. No hay ninguna ficha de Metro publicada por Metro de Madrid, S.A.

### 2. datos.gob.es

- Busqué por título («metro», «Metro de Madrid», «horarios», «Oferta planificada», «Topología de la Red») y por palabra clave («GTFS», «metro», «Metro de Madrid», «transporte público») usando la API del catálogo.
- **«Oferta planificada de la Red de Metro»**, https://datos.gob.es/catalogo/a13002908-oferta-planificada-de-la-red-de-metro1. La publica la Comunidad de Madrid (organismo A13002908) y es la federación de https://datos.comunidad.madrid/catalogo/dataset/red_de_metro_oferta_planificada_horarios_topologia. Descripción: «Horarios y topología en formato GTFS». Su única distribución enlaza a https://crtm.maps.arcgis.com/home/item.html?id=5c7f2951962540d69ffe8f640d94c246, **el mismo ítem del CRTM que ya descargamos**. Hoy su API dice: «GTFS Red de Metro», `modified` 2025-05-30, licencia https://www.crtm.es/licencia-de-uso. La ficha avisa de que «la fecha de última actualización de los datos no se refresca automáticamente».
- «Horarios de metro» del Ayuntamiento de Alcobendas (L01280066): un extracto en Excel de las paradas de Metro de Alcobendas, modificado el 02/05/2024. Es más antiguo y parcial. Descartado.
- «Metro de Madrid. Infraestructura, oferta y empleo», «Ratios del Metro de Madrid» y «Cuenta de pérdidas y ganancias» (Comunidad de Madrid, 05/11/2026): son estadísticas anuales, no horarios.
- No hay ningún otro GTFS de Metro de Madrid en el catálogo.

### 3. datos.metromadrid.es

- **No existe como servicio.** El nombre no tiene dirección: el DNS responde NOERROR con 0 respuestas, y el proxy devuelve 502 porque no hay a dónde conectar. No es un bloqueo del cortafuegos. Ninguna página de www.metromadrid.es enlaza a ese dominio.

### 4. www.metromadrid.es (web oficial de Metro de Madrid, S.A.)

- No publica ningún GTFS ni ninguna sección de datos abiertos. `/es/datos-abiertos` da 404. El portal de transparencia (`/es/transparencia/proyectos-y-datos`) tiene hojas Excel de demanda, reclamaciones y obras, pero ningún horario.
- **Página de la línea 3** (https://www.metromadrid.es/es/linea/linea-3, consultada el 2026-11-14): «El Casar – Moncloa, Línea 3, Circulación normal». Confirma que hoy la línea 3 funciona y que llega a El Casar, con correspondencia L3/L12. Trae una tabla de **«Intervalo medio entre trenes»** por franjas de media hora y cuatro tipos de día (lunes a jueves, viernes, sábados, domingos y festivos). Por ejemplo, de lunes a jueves es de 2–3 min entre las 7:30 y las 9:30 y de 4–5 min a mediodía. También enlaza dos PDF de horarios de trenes por sentido (5,2 y 5,5 MB).
- **Licencia: no es abierta.** El aviso legal (https://www.metromadrid.es/es/aviso-legal) dice que los contenidos son propiedad de Metro de Madrid, S.A., y que «la utilización de la información contenida en la página web sin autorización expresa y por escrito de Metro de Madrid, S.A.» puede dar lugar a acciones legales. Por la regla del proyecto («nunca usar datos de webs que prohíban su extracción») **no se puede usar** sin pedir ese permiso por escrito.

## Lo que pedías, para la fuente más reciente disponible

Como no hay ninguna más reciente, la «más reciente» es la misma que ya usamos:

| Pregunta | Respuesta |
|---|---|
| Quién la publica | Consorcio Regional de Transportes de Madrid (CRTM). Se redistribuye sin cambios en el NAP (ficha 933) y en datos.gob.es / datos.comunidad.madrid («Oferta planificada de la Red de Metro») |
| Fecha | Fichero generado el 27/05/2025 (feed_version 20250527) y publicado el 30/05/2025. Sin cambios a 14/11/2026 |
| Vigencia | calendar.txt del 27/05/2025 al 27/05/2026 (el NAP indica 01/01/2025–27/05/2026). **Caducado desde el 27/05/2026** |
| Licencia y condiciones | CRTM: uso comercial y no comercial, con «Powered by CRTM» y enlace, datos siempre actualizados, cita de la fuente (en bruto o explotados), conservar los metadatos de fecha y no sugerir patrocinio. Copia del NAP: licencia de datos abiertos del MITRAMS (reutilización libre y gratuita), descarga con inicio de sesión |
| ¿Línea 3 con viajes? | **No.** La ruta `4__3___` existe pero tiene 0 viajes en trips.txt (los 120 viajes son de las otras 12 líneas) |
| ¿El Casar en la línea 3? | **No.** El Casar solo aparece con el andén de la línea 12. La línea 3 tiene sus 18 andenes propios, sin El Casar, aunque la web oficial confirma que llega allí |

La única fuente oficial más reciente, la tabla de intervalos de la web de Metro, sí cubre la línea 3 hasta El Casar. Pero no es abierta, es una web (no un GTFS) y da intervalos por línea, no horarios por parada.

## Qué supondría cambiar

**Hoy: nada que cambiar.** No hay alternativa abierta. El tratamiento actual sigue siendo el correcto: el día típico dentro de la vigencia (mayo de 2026), con la nota de estimación sobre las frecuencias actuales, y la línea 3 reconstruida con la media de las líneas 1, 2, 4 y 5, también marcada como estimación. En docs/fuentes.md solo se podría actualizar la fecha de comprobación (ahora dice 2026-11-12). No lo he tocado.

**Si el CRTM publica un GTFS nuevo** (lo más probable, y en el mismo ítem):
1. Volver a ejecutar `src/descargar_externas.py`. La URL no cambia porque el ítem `5c7f2951…` es el mismo.
2. Si la línea 3 ya trae viajes, `src/procesar_perfil.py` se para a propósito («la línea 3 ya no está sin viajes en el GTFS; quitar de supuestos.GTFS_LINEAS_RECONSTRUIDAS»). Habría que quitar la entrada de `src/supuestos.py` (con `estaciones_extra: ("EL CASAR",)`) y los textos de «línea 3 reconstruida (estimación)» en docs/fuentes.md, la aplicación y el PDF, que dejarían de aplicarse.
3. Con un calendario vigente, el día típico de Metro pasaría a ser uno de noviembre o diciembre de 2026, como el resto de redes. Se podrían quitar el aviso de «GTFS de mayo de 2025» y la estimación «se supone que las frecuencias actuales son parecidas», además de la nota de descargar_externas.py y fuentes.md que dice que el GTFS se baja «solo para frecuencias». Las estaciones podrían seguir saliendo de la capa de red.
4. Cambiaría el total de pasos de Metro (hoy 122.515 en laborable, con la línea 3 estimada). Por tanto cambiarían la calibración de personas por paso (hoy 41,2 en laborable, 34,8 en sábado y 28,4 en domingo) y las cifras de las zonas con Metro. Habría que regenerar los procesados, las capturas y el PDF de muestra.

**Si se quisiera usar la tabla de intervalos de la web de Metro:** antes habría que pedir a Metro de Madrid, S.A. una autorización expresa y por escrito, por las reglas del proyecto y por su aviso legal. Aun con permiso, habría que convertir los intervalos (rangos de minutos por media hora y por tipo de día) en trenes por hora. Sería otra estimación, aunque basada en datos oficiales y actuales de la propia línea 3. El viernes no encaja en «laborable típico», que usa de martes a jueves.

**Vías para conseguir algo mejor sin incumplir las reglas** (no he hecho ninguna):
- Avisar al CRTM (https://crtm.es/atencion-al-cliente/) de que el GTFS de Metro está caducado y no tiene la línea 3.
- Presentar una solicitud de acceso a información pública a Metro de Madrid (en su portal de transparencia: `/es/transparencia/solicitud-de-acceso-a-informacion-publica`) para pedir los horarios u ofertas por línea en formato reutilizable.

## Nota al margen (no son horarios)

El portal de transparencia de Metro publica hojas actualizadas: `Ref._PA052_Entradas_estac_2026_10.xlsx` (entradas por estación, octubre de 2026), `PA016_Utilizaciones_por_estaciones_202602.xlsx` y `Ref._PA049_Demanda_Diaria_2026_10.xlsx`. Hoy `src/supuestos.py` dice que no hay «datos por estación de Metro», así que podrían servir para calibrar la demanda por estación. **No he comprobado su licencia ni sus condiciones de reutilización.** Están bajo el mismo aviso legal de la web, así que habría que aclararlo antes de plantearse usarlas.
