# 2026-11-10 · Informe del local (parte A): contexto de mercado

## Qué se ha hecho

`src/informe_local.py` tiene la función `informe_local(lat, lon)`, que devuelve seis
bloques de contexto alrededor de un punto (mismo radio de 300 m que el perfil por
horas). **Cada bloque indica sus fuentes con su licencia y fecha, y si su resultado es
un dato** (tal como lo publica la fuente) **o una estimación** (calculada con supuestos).
Los supuestos nuevos están en `src/supuestos.py`, en la sección «INFORME DEL LOCAL».

```bash
python src/informe_local.py 40.4046 -3.6106          # Markdown
python src/informe_local.py 40.4046 -3.6106 --json   # JSON (para la app)
```

Todavía no incluye recomendaciones de qué vender: eso será la parte B.

## Metodología, bloque a bloque

### 1. Competencia en el radio (dato + estimación)

- **Madrid capital:** censo de locales del Ayuntamiento, que es el registro oficial de
  locales abiertos. Cada local se clasifica por su epígrafe: el «bar restaurante»
  cuenta como bar y la heladería o salón de té como cafetería (supuesto). Un local con
  varios epígrafes cuenta una vez, con el tipo más específico.
- **Resto de municipios:** OpenStreetMap (`restaurant`, `bar` y `pub`, `cafe` y
  `fast_food`). El informe dice siempre qué fuente ha usado.
- **Tipos de cocina:** solo existen en OpenStreetMap, y el informe avisa de cuántos
  locales la indican. En toda la Comunidad la indica el 37 %, y alrededor de los puntos
  de prueba muchos menos.
- **Comparación con el municipio:** se calcula la media de locales a menos de 300 m de
  donde vive la gente del municipio (media de sus secciones censales, desde un punto
  interior, ponderada por población). Así se compara con un sitio habitado típico y no
  con toda la superficie del término municipal, que incluye campo y polígonos.
  *Estimación de referencia.*
- **Cobertura de OSM (añadido):** al probarlo se vio que en OSM faltan muchos locales
  fuera de Madrid. El informe compara los locales por habitante que tiene OSM en el
  municipio con los del censo oficial de Madrid capital, y avisa cuando OSM tiene menos
  del 60 %:
  - Madrid capital (censo): 5,0 locales por 1.000 habitantes;
  - Fuenlabrada (OSM): 1,9;
  - Griñón (OSM): 1,05.

  En esos municipios los números absolutos se quedan cortos. La comparación con la
  media del municipio sigue sirviendo, porque las dos cifras salen de la misma fuente.

### 2. Mercado potencial (estimación, en rango)

**gasto = población del radio × gasto medio por persona en restauración ×
(renta de la zona ÷ renta media de la Comunidad) ^ elasticidad**

- **Gasto medio por persona en restauración** en la Comunidad de Madrid, 2025:
  **1.239,81 €** (dato; Encuesta de Presupuestos Familiares en el portal).
- **Población del radio:** secciones censales del INE (2024), en proporción a la
  superficie que queda dentro del círculo.
- **Renta:** renta neta media por persona del INE (2024). La de la zona es la media de
  sus secciones ponderada por población; la de la Comunidad es de **19.129 €**.
- **Supuesto del ajuste:** quien tiene más renta gasta más en comer fuera, más o menos
  en proporción a su renta. Se usa una elasticidad de **0,8 a 1,2**: 1 significaría
  exactamente proporcional, 0,8 que sube algo menos y 1,2 que sube algo más. Se añade un
  ±10 % por la población (dato de 2024 repartido por superficie). Por eso el resultado
  es un **rango redondeado a dos cifras**.
- Es lo que gastan los vecinos en cualquier sitio, no lo que facturaría un local.

### 3. Gama de precios (estimación) y evolución de precios (dato)

- **Gama:** económica si la renta de la zona es menor que 0,85 veces la media de la
  Comunidad, alta si es mayor que 1,15 y media entre medias (supuesto). Se basa en los
  residentes; si la mayoría de los clientes no son vecinos, hay que tomarla con cautela.
- **IPC de la Comunidad de Madrid** (portal, base 2025), tasa interanual de
  **septiembre de 2026**:

  | Grupo | Últimos 12 meses |
  |---|---|
  | Restaurantes y servicios de alojamiento | **+5,7 %** |
  | Alimentos y bebidas no alcohólicas | **+3,2 %** |
  | Bebidas alcohólicas | +0,6 % |
  | Índice general | +5,3 % |
  | Hoteles (dentro del primer grupo) | +18,0 % |

  El portal **no publica una subclase solo de restaurantes**: el grupo incluye hoteles,
  que han subido un 18 %. La subida propia de bares y restaurantes es probablemente
  menor que el +5,7 % del grupo. Aun así, los precios de comer fuera han subido más que
  los de la materia prima (alimentos +3,2 %).

### 4. Turismo (dato, con aproximación)

- **Registro de alojamientos turísticos** (hoteles, hostales, pensiones, apartamentos,
  viviendas de uso turístico inscritas…), que trae código postal y localidad.
- **Declaraciones responsables de viviendas de uso turístico**, que solo traen
  localidad.
- **Aproximación:** no se convierten direcciones en coordenadas. Se cuentan los
  alojamientos del mismo código postal y del mismo municipio, no los del radio. El
  código postal del punto se estima con el más repetido entre los 5 centros sanitarios
  más cercanos, porque no hay límites de códigos postales en abierto.
- No se muestran los nombres de los establecimientos.

### 5. Festivos (dato + orientación)

- Festivos regionales y locales del portal.
- **Limitación:** el portal solo publica el año en curso (2026), y los de 2027 aún no
  están; el datastore tampoco los tiene. El informe da los festivos que quedan hasta el
  31/12/2026 (dato) y, como orientación, cuándo fueron en 2026 las fiestas locales que
  caerían antes de noviembre de 2027 (estimación, porque muchas cambian de fecha).

### 6. Salud del sector (dato, de toda la Comunidad)

- Demografía empresarial del portal: serie trimestral CNAE-2009 (2009–2025, que se ha
  añadido a las descargas) y CNAE-2025 (2026).
- **Limitación importante:** el portal **no separa la hostelería**. La agrupa con el
  comercio y el transporte en «Servicios de distribución y hostelería». Se buscaron
  alternativas en el portal (afiliados por municipio y rama, demografía por actividad,
  comparativas) y todas usan la misma agrupación.
- **Detalle corregido al probarlo:** en el primer trimestre de 2026 el total de esa rama
  cae de 70.139 a 66.865 empresas (−4,7 %). No son cierres: 2.815 empresas pasan a otras
  ramas por el cambio a la clasificación CNAE-2025 («saldo interno»). Para 2026 se
  compara el **saldo externo** (altas − bajas ± traslados) con los mismos trimestres del
  año anterior.
- Resultado: la rama **se mantiene**:
  - +0,3 % en 2025 (el total de la economía, +0,8 %) y +0,8 % frente a 2019;
  - en el primer semestre de 2026, saldo de **+109 empresas**, frente a −345 en el mismo
    semestre de 2025.

## Puntos de prueba

| Punto | Coordenadas | De dónde salen |
|---|---|---|
| Campus de Vicálvaro (URJC) | 40.4046, -3.6106 | Indicadas en la petición |
| Fuenlabrada, Plaza de la Constitución | **40.283366, -3.800132** | OpenStreetMap, vía peatonal «Plaza de la Constitución» (way 73267558), centro geométrico |
| Griñón, plaza central | **40.212861, -3.852623** | OpenStreetMap: **no hay ninguna «Plaza de la Constitución» en Griñón** (ni como vía ni en ninguna dirección). Se ha usado la **Plaza Mayor** (way 839255766), la plaza central junto al Ayuntamiento (Plaza Mayor, 1). Si la plaza que se quería es otra, basta con cambiar las coordenadas. |

## Resultados resumidos

| | Vicálvaro (campus) | Fuenlabrada (centro) | Griñón (centro) |
|---|---|---|---|
| Fuente de la competencia | Censo del Ayuntamiento | OpenStreetMap | OpenStreetMap |
| Locales en 300 m (bares / restaurantes / cafeterías / comida rápida) | **27** (18 / 0 / 4 / 5) | **25** (10 / 5 / 8 / 2) | **2** (1 / 0 / 1 / 0) |
| Frente a la media del municipio | ×0,69 (menos que un punto típico de Madrid) | ×2,07 (el doble) | ×3,20 |
| Cobertura de OSM | — | baja (1,9 por 1.000 hab.) | muy baja (1,05 por 1.000 hab.) |
| Vecinos en el radio | ~5.000 | ~4.760 | ~1.020 |
| Renta por persona (×media) | 14.250 € (×0,74) | 14.226 € (×0,74) | 16.486 € (×0,86) |
| Mercado potencial de los vecinos (estimación) | **3,9–5,4 M€/año** | **3,7–5,1 M€/año** | **0,95–1,2 M€/año** |
| Gama de precios (estimación) | **Económica** | **Económica** | **Media** (justo en el límite) |
| Código postal (aprox.) y alojamientos | 28032: 10 (8 viviendas turísticas) | 28943: 2 (municipio: 17) | 28971: 3 (municipio: 3) |
| Viviendas turísticas declaradas en el municipio | 1.113 (Madrid) | 0 | 0 |
| Festivos locales que quedan en 2026 | ninguno | 26/12 (sábado) | ninguno |
| Fiestas locales de 2026 (orientación para 2027) | 15/05, 09/11 | 14/09, 26/12 | 17/06, 14/08 |

Lectura rápida (sin recomendaciones, que serán la parte B):

- **Vicálvaro:** menos competencia que un sitio típico de Madrid, sin restaurantes en
  300 m (el censo cuenta 18 bares, muchos de ellos bar-restaurante) y renta baja. La
  clientela principal no son los vecinos sino viajeros y universitarios (ver el perfil
  por horas), así que la gama «económica» sale de los residentes y puede no reflejar a
  los estudiantes.
- **Fuenlabrada:** el centro concentra el doble de locales que un punto típico del
  municipio, con renta baja y casi sin turismo.
- **Griñón:** la cifra de competencia es poco fiable porque OSM tiene muy pocos locales
  del pueblo. El mercado de los vecinos es pequeño (~1 M€/año) y la renta está en el
  límite entre la gama económica y la media.

## Fuentes nuevas o usadas por primera vez

Todas están anotadas en `docs/fuentes.md`, con su licencia y fecha de descarga:

- Gasto medio por subgrupo (EPF, COICOP 3 dígitos);
- IPC base 2025;
- alojamientos turísticos;
- declaraciones de viviendas de uso turístico;
- festivos regionales y locales;
- demografía empresarial CNAE-2009 (descarga nueva) y CNAE-2025.

Todas son del portal de la Comunidad, con licencia CC BY 4.0. La competencia usa además
el censo de locales del Ayuntamiento de Madrid (CC BY 4.0) y OpenStreetMap (ODbL).

## Anexo: informes completos generados por `src/informe_local.py`

### Punto 40.4046, -3.6106 · Madrid (28079) · radio 300 m

#### Competencia en el radio · *dato + estimación*

27 locales de hostelería en 300 m (Censo de locales del Ayuntamiento de Madrid): bares 18, restaurantes 0, cafeterías 4, comida rápida 5; 0,7 veces la media del municipio (media: 38,9).

| Tipo | Locales |
|---|---|
| Bares | 18 |
| Restaurantes | 0 |
| Cafeterías | 4 |
| Comida rápida | 5 |
| **Total** | **27** |

Densidad: 96 locales/km² frente a 138 de media en el municipio (×0,69).

Cocinas en OSM: chicken (2), pizza (1), burger (1).

- Fuente de los recuentos: **Censo de locales del Ayuntamiento de Madrid** (registro oficial de locales abiertos).
- Media del municipio = locales a menos de 300 m de donde vive la gente del municipio (media de sus secciones censales ponderada por población). **Estimación** de referencia.
- Tipos de cocina: solo de OpenStreetMap y **no todos los locales la indican** (4 de 10 en el radio).
- Clasificación del censo por epígrafe (src/supuestos.py): el «bar restaurante» cuenta como bar.

Fuentes: [Censo de locales, sus actividades y terrazas de hostelería y restauración](https://datos.madrid.es/dataset/200085-0-censo-locales) (Creative Commons Attribution 4.0 International (CC BY 4.0). Citar: «Fuente: Ayuntamiento de Madrid»; descargado el 2026-11-09); [OpenStreetMap: bares, pubs, cafeterías, restaurantes y comida rápida de la Comunidad de Madrid (API Overpass)](https://www.openstreetmap.org/copyright) (Open Database License (ODbL) 1.0. Citar: «© colaboradores de OpenStreetMap» con enlace a https://www.openstreetmap.org/copyright; descargado el 2026-11-09)

#### Mercado potencial: gasto en restauración de los vecinos · *estimación*

Entre 3.900.000 € y 5.400.000 € al año (estimación) gastan en bares y restaurantes los ~5.016 vecinos del radio.

- Gasto medio por persona en restauración en la Comunidad de Madrid (2025): 1.239,81 € (**dato**).
- Renta neta media por persona de la zona: 14.250 € frente a 19.129 € de media en la Comunidad (×0,74) (**dato** del INE, 2024; la de la zona es la media de sus secciones censales ponderada por población).
- Ajuste por renta (**supuesto**): gasto = población × gasto medio × (renta relativa) ^ elasticidad, con una elasticidad de 0,8 a 1,2 (el gasto en comer fuera crece más o menos en proporción a la renta), y un ±10 % por la población. Por eso se da un rango.
- Es lo que gastan los vecinos en cualquier sitio, no lo que facturaría un local: parte lo gastan lejos de casa y, a la vez, el local recibe gente que no vive aquí (ver el perfil por horas).

Fuentes: [Gasto medio de los hogares por subgrupo de gasto (3 dígitos COICOP/EPF) (Base 2006)](https://datos.comunidad.madrid/dataset/gasto_por_subgrupo_gasto_3_digitos_coicop_epf_base_2006) (Creative Commons Attribution; Encuesta de Presupuestos Familiares 2025; descargado el 2026-11-10); [INE. Atlas de distribución de renta de los hogares (ADRH), provincia de Madrid, por municipio, distrito y sección censal](https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177088&idp=1254735976608) (Reutilización libre citando la fuente: «Fuente: Instituto Nacional de Estadística (INE)» (aviso legal); renta y población 2024; descargado el 2026-11-09)

#### Gama de precios y evolución de precios · *dato + estimación*

Gama **económica** (renta de la zona ×0,74 la media de la Comunidad). En los últimos 12 meses (hasta septiembre de 2026) restaurantes y alojamiento +5,7 % frente a alimentos +3,2 %.

- Gama (**estimación**): económica si la renta de la zona es menor que 0,85 veces la media de la Comunidad, alta si es mayor que 1,15, media entre medias. Se basa en la renta de los residentes: si la mayoría de los clientes no son vecinos (perfil por horas), tómese con cautela.
- IPC de la Comunidad de Madrid, tasa interanual de septiembre de 2026 (**dato**): restaurantes y servicios de alojamiento +5,7 %, alimentos y bebidas no alcohólicas +3,2 %, bebidas alcohólicas +0,6 %, índice general +5,3 %.
- El portal no publica una subclase solo de restaurantes: el grupo incluye hoteles, que han subido +18,0 %. La subida de bares y restaurantes por sí sola probablemente sea menor que la del grupo.

Fuentes: [INE. Atlas de distribución de renta de los hogares (ADRH), provincia de Madrid, por municipio, distrito y sección censal](https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177088&idp=1254735976608) (Reutilización libre citando la fuente: «Fuente: Instituto Nacional de Estadística (INE)» (aviso legal); renta 2024; descargado el 2026-11-09); [Índice de Precios de Consumo (IPC), por grupo. Base 2025. Comunidad de Madrid y España](https://datos.comunidad.madrid/dataset/ipc_base_2025) (Creative Commons Attribution; septiembre de 2026; descargado el 2026-11-10)

#### Turismo: alojamientos del código postal y del municipio · *dato + estimación*

Código postal 28032 (aproximado): 10 alojamientos turísticos inscritos. Municipio: 6043 inscritos y 1113 viviendas de uso turístico con declaración responsable.

- Código postal 28032: Vivienda de uso turístico 8, Hotel-apart. 1, Casa huespedes 1
- Municipio: Vivienda de uso turístico 4479, Casa huespedes 380, Hotel 341, Hostal 315, Apart-turistico 224, Pension 198, Hosterias 77, Hotel-apart. 28, Camping 1

- **Aproximación**: no se convierten las direcciones en coordenadas. Se cuentan los alojamientos del mismo código postal y del mismo municipio, no los del radio.
- El código postal del punto es el más repetido entre los 5 centros sanitarios más cercanos (no hay límites de códigos postales en abierto): **estimación**.
- Registro de alojamientos (hoteles, hostales, apartamentos y viviendas de uso turístico inscritas) y declaraciones responsables de viviendas de uso turístico (conjunto aparte, solo con municipio): son **datos**; puede haber viviendas en los dos.
- No se muestran los nombres de los establecimientos.

Fuentes: [Alojamientos turísticos de la Comunidad de Madrid](https://datos.comunidad.madrid/dataset/alojamientos_turisticos) (Creative Commons Attribution; descargado el 2026-11-10); [Declaraciones responsables de actividad de viviendas de uso turístico de la Comunidad de Madrid presentadas](https://datos.comunidad.madrid/dataset/declaraciones_actividad_viviendas_uso_turistico) (Creative Commons Attribution; descargado el 2026-11-10)

#### Festivos de los próximos 12 meses · *dato + estimación*

3 festivos publicados hasta el 31/12/2026 (0 locales); los de 2027 aún no están publicados.

- 2026-12-07 (lunes): Día de la Constitución Española (regional o nacional)
- 2026-12-08 (martes): Inmaculada Concepción (regional o nacional)
- 2026-12-25 (viernes): Natividad del Señor (regional o nacional)
- Orientación para el año siguiente (fiestas locales de 2026): 2026-05-15 (Madrid), 2026-11-09 (Madrid)

- Festivos regionales y locales publicados en el portal (**dato**).
- El portal solo publica los festivos de 2026: los de 2027 aún no están. Como orientación se indica cuándo fueron en 2026 los que caerían antes del 10/11/2027 (**estimación**: muchas fiestas cambian de fecha cada año).

Fuentes: [Festivos regionales y locales año en curso](https://datos.comunidad.madrid/dataset/festivos_regionales_locales) (Creative Commons Attribution; año 2026; descargado el 2026-11-10)

#### Salud del sector (Comunidad de Madrid) · *dato*

Las empresas de distribución y hostelería de la Comunidad se mantienen: +0,3 % en el último año hasta el 4º trimestre de 2025 (+0,8 % frente a 2019). En 2026 (T1, T2) el saldo de altas y bajas es de +109 empresas, frente a -345 en los mismos trimestres de 2025.

- **Limitación importante**: el portal agrupa la hostelería con el comercio y el transporte en «Servicios de distribución y hostelería». No hay datos abiertos de empresas solo de hostelería; tampoco los afiliados a la Seguridad Social por municipio la separan.
- Último año (serie CNAE-2009): 13.420 altas y 13.203 bajas; el total de la economía madrileña varió +0,8 %.
- En 2026 cambia la clasificación (CNAE-2025) y 2.815 empresas pasan de esta rama a otras («saldo interno»): no son cierres. Por eso para 2026 se compara el saldo externo (altas − bajas ± traslados de sede) con los mismos trimestres del año anterior, y no el total.
- Es un dato de toda la Comunidad, no de la zona.

Fuentes: [Demografía empresarial de la Comunidad de Madrid. Unidades empresariales y puestos de trabajo asociados a las unidades empresariales, por rama de actividad (CNAE-2009)](https://datos.comunidad.madrid/dataset/demografia_empresarial_cnae09) (Creative Commons Attribution; 2009–2025; descargado el 2026-11-10); [Demografía empresarial de la Comunidad de Madrid. Unidades empresariales y puestos de trabajo asociados a las unidades empresariales, por rama de actividad (CNAE-2025)](https://datos.comunidad.madrid/dataset/demografia_empresarial_cnae25) (Creative Commons Attribution; 2026, trimestres T1, T2; descargado el 2026-11-10)


### Punto 40.283366, -3.800132 · Fuenlabrada (28058) · radio 300 m

#### Competencia en el radio · *dato + estimación*

25 locales de hostelería en 300 m (OpenStreetMap): bares 10, restaurantes 5, cafeterías 8, comida rápida 2; 2,1 veces la media del municipio (media: 12,1).

| Tipo | Locales |
|---|---|
| Bares | 10 |
| Restaurantes | 5 |
| Cafeterías | 8 |
| Comida rápida | 2 |
| **Total** | **25** |

Densidad: 88 locales/km² frente a 43 de media en el municipio (×2,07).

Cocinas en OSM: burger (1).

- Fuente de los recuentos: **OpenStreetMap** (mapa colaborativo: puede faltar algún local, sobre todo en municipios pequeños; no hay un censo oficial abierto fuera de Madrid capital).
- Media del municipio = locales a menos de 300 m de donde vive la gente del municipio (media de sus secciones censales ponderada por población). **Estimación** de referencia.
- Tipos de cocina: solo de OpenStreetMap y **no todos los locales la indican** (1 de 25 en el radio).
- Cobertura de OpenStreetMap: en Fuenlabrada registra 1,89 locales por 1.000 habitantes, frente a 5,02 del censo oficial en Madrid capital. **Probablemente faltan locales en OSM**: los números absolutos se quedan cortos, aunque la comparación con la media del municipio (que también sale de OSM) sigue siendo útil.

Fuentes: [OpenStreetMap: bares, pubs, cafeterías, restaurantes y comida rápida de la Comunidad de Madrid (API Overpass)](https://www.openstreetmap.org/copyright) (Open Database License (ODbL) 1.0. Citar: «© colaboradores de OpenStreetMap» con enlace a https://www.openstreetmap.org/copyright; descargado el 2026-11-09)

#### Mercado potencial: gasto en restauración de los vecinos · *estimación*

Entre 3.700.000 € y 5.100.000 € al año (estimación) gastan en bares y restaurantes los ~4.759 vecinos del radio.

- Gasto medio por persona en restauración en la Comunidad de Madrid (2025): 1.239,81 € (**dato**).
- Renta neta media por persona de la zona: 14.226 € frente a 19.129 € de media en la Comunidad (×0,74) (**dato** del INE, 2024; la de la zona es la media de sus secciones censales ponderada por población).
- Ajuste por renta (**supuesto**): gasto = población × gasto medio × (renta relativa) ^ elasticidad, con una elasticidad de 0,8 a 1,2 (el gasto en comer fuera crece más o menos en proporción a la renta), y un ±10 % por la población. Por eso se da un rango.
- Es lo que gastan los vecinos en cualquier sitio, no lo que facturaría un local: parte lo gastan lejos de casa y, a la vez, el local recibe gente que no vive aquí (ver el perfil por horas).

Fuentes: [Gasto medio de los hogares por subgrupo de gasto (3 dígitos COICOP/EPF) (Base 2006)](https://datos.comunidad.madrid/dataset/gasto_por_subgrupo_gasto_3_digitos_coicop_epf_base_2006) (Creative Commons Attribution; Encuesta de Presupuestos Familiares 2025; descargado el 2026-11-10); [INE. Atlas de distribución de renta de los hogares (ADRH), provincia de Madrid, por municipio, distrito y sección censal](https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177088&idp=1254735976608) (Reutilización libre citando la fuente: «Fuente: Instituto Nacional de Estadística (INE)» (aviso legal); renta y población 2024; descargado el 2026-11-09)

#### Gama de precios y evolución de precios · *dato + estimación*

Gama **económica** (renta de la zona ×0,74 la media de la Comunidad). En los últimos 12 meses (hasta septiembre de 2026) restaurantes y alojamiento +5,7 % frente a alimentos +3,2 %.

- Gama (**estimación**): económica si la renta de la zona es menor que 0,85 veces la media de la Comunidad, alta si es mayor que 1,15, media entre medias. Se basa en la renta de los residentes: si la mayoría de los clientes no son vecinos (perfil por horas), tómese con cautela.
- IPC de la Comunidad de Madrid, tasa interanual de septiembre de 2026 (**dato**): restaurantes y servicios de alojamiento +5,7 %, alimentos y bebidas no alcohólicas +3,2 %, bebidas alcohólicas +0,6 %, índice general +5,3 %.
- El portal no publica una subclase solo de restaurantes: el grupo incluye hoteles, que han subido +18,0 %. La subida de bares y restaurantes por sí sola probablemente sea menor que la del grupo.

Fuentes: [INE. Atlas de distribución de renta de los hogares (ADRH), provincia de Madrid, por municipio, distrito y sección censal](https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177088&idp=1254735976608) (Reutilización libre citando la fuente: «Fuente: Instituto Nacional de Estadística (INE)» (aviso legal); renta 2024; descargado el 2026-11-09); [Índice de Precios de Consumo (IPC), por grupo. Base 2025. Comunidad de Madrid y España](https://datos.comunidad.madrid/dataset/ipc_base_2025) (Creative Commons Attribution; septiembre de 2026; descargado el 2026-11-10)

#### Turismo: alojamientos del código postal y del municipio · *dato + estimación*

Código postal 28943 (aproximado): 2 alojamientos turísticos inscritos. Municipio: 17 inscritos y 0 viviendas de uso turístico con declaración responsable.

- Código postal 28943: Hotel 1, Vivienda de uso turístico 1
- Municipio: Hotel 9, Vivienda de uso turístico 5, Hostal 2, Casa huespedes 1

- **Aproximación**: no se convierten las direcciones en coordenadas. Se cuentan los alojamientos del mismo código postal y del mismo municipio, no los del radio.
- El código postal del punto es el más repetido entre los 5 centros sanitarios más cercanos (no hay límites de códigos postales en abierto): **estimación**.
- Registro de alojamientos (hoteles, hostales, apartamentos y viviendas de uso turístico inscritas) y declaraciones responsables de viviendas de uso turístico (conjunto aparte, solo con municipio): son **datos**; puede haber viviendas en los dos.
- No se muestran los nombres de los establecimientos.

Fuentes: [Alojamientos turísticos de la Comunidad de Madrid](https://datos.comunidad.madrid/dataset/alojamientos_turisticos) (Creative Commons Attribution; descargado el 2026-11-10); [Declaraciones responsables de actividad de viviendas de uso turístico de la Comunidad de Madrid presentadas](https://datos.comunidad.madrid/dataset/declaraciones_actividad_viviendas_uso_turistico) (Creative Commons Attribution; descargado el 2026-11-10)

#### Festivos de los próximos 12 meses · *dato + estimación*

4 festivos publicados hasta el 31/12/2026 (1 local); los de 2027 aún no están publicados.

- 2026-12-07 (lunes): Día de la Constitución Española (regional o nacional)
- 2026-12-08 (martes): Inmaculada Concepción (regional o nacional)
- 2026-12-25 (viernes): Natividad del Señor (regional o nacional)
- 2026-12-26 (sábado): Fuenlabrada (local)
- Orientación para el año siguiente (fiestas locales de 2026): 2026-09-14 (Fuenlabrada)

- Festivos regionales y locales publicados en el portal (**dato**).
- El portal solo publica los festivos de 2026: los de 2027 aún no están. Como orientación se indica cuándo fueron en 2026 los que caerían antes del 10/11/2027 (**estimación**: muchas fiestas cambian de fecha cada año).

Fuentes: [Festivos regionales y locales año en curso](https://datos.comunidad.madrid/dataset/festivos_regionales_locales) (Creative Commons Attribution; año 2026; descargado el 2026-11-10)

#### Salud del sector (Comunidad de Madrid) · *dato*

Las empresas de distribución y hostelería de la Comunidad se mantienen: +0,3 % en el último año hasta el 4º trimestre de 2025 (+0,8 % frente a 2019). En 2026 (T1, T2) el saldo de altas y bajas es de +109 empresas, frente a -345 en los mismos trimestres de 2025.

- **Limitación importante**: el portal agrupa la hostelería con el comercio y el transporte en «Servicios de distribución y hostelería». No hay datos abiertos de empresas solo de hostelería; tampoco los afiliados a la Seguridad Social por municipio la separan.
- Último año (serie CNAE-2009): 13.420 altas y 13.203 bajas; el total de la economía madrileña varió +0,8 %.
- En 2026 cambia la clasificación (CNAE-2025) y 2.815 empresas pasan de esta rama a otras («saldo interno»): no son cierres. Por eso para 2026 se compara el saldo externo (altas − bajas ± traslados de sede) con los mismos trimestres del año anterior, y no el total.
- Es un dato de toda la Comunidad, no de la zona.

Fuentes: [Demografía empresarial de la Comunidad de Madrid. Unidades empresariales y puestos de trabajo asociados a las unidades empresariales, por rama de actividad (CNAE-2009)](https://datos.comunidad.madrid/dataset/demografia_empresarial_cnae09) (Creative Commons Attribution; 2009–2025; descargado el 2026-11-10); [Demografía empresarial de la Comunidad de Madrid. Unidades empresariales y puestos de trabajo asociados a las unidades empresariales, por rama de actividad (CNAE-2025)](https://datos.comunidad.madrid/dataset/demografia_empresarial_cnae25) (Creative Commons Attribution; 2026, trimestres T1, T2; descargado el 2026-11-10)


### Punto 40.212861, -3.852623 · Griñón (28066) · radio 300 m

#### Competencia en el radio · *dato + estimación*

2 locales de hostelería en 300 m (OpenStreetMap): bares 1, restaurantes 0, cafeterías 1, comida rápida 0; 3,2 veces la media del municipio (media: 0,6).

| Tipo | Locales |
|---|---|
| Bares | 1 |
| Restaurantes | 0 |
| Cafeterías | 1 |
| Comida rápida | 0 |
| **Total** | **2** |

Densidad: 7 locales/km² frente a 2 de media en el municipio (×3,20).

- Fuente de los recuentos: **OpenStreetMap** (mapa colaborativo: puede faltar algún local, sobre todo en municipios pequeños; no hay un censo oficial abierto fuera de Madrid capital).
- Media del municipio = locales a menos de 300 m de donde vive la gente del municipio (media de sus secciones censales ponderada por población). **Estimación** de referencia.
- Tipos de cocina: solo de OpenStreetMap y **no todos los locales la indican** (0 de 2 en el radio).
- Cobertura de OpenStreetMap: en Griñón registra 1,05 locales por 1.000 habitantes, frente a 5,02 del censo oficial en Madrid capital. **Probablemente faltan locales en OSM**: los números absolutos se quedan cortos, aunque la comparación con la media del municipio (que también sale de OSM) sigue siendo útil.

Fuentes: [OpenStreetMap: bares, pubs, cafeterías, restaurantes y comida rápida de la Comunidad de Madrid (API Overpass)](https://www.openstreetmap.org/copyright) (Open Database License (ODbL) 1.0. Citar: «© colaboradores de OpenStreetMap» con enlace a https://www.openstreetmap.org/copyright; descargado el 2026-11-09)

#### Mercado potencial: gasto en restauración de los vecinos · *estimación*

Entre 950.000 € y 1.200.000 € al año (estimación) gastan en bares y restaurantes los ~1.022 vecinos del radio.

- Gasto medio por persona en restauración en la Comunidad de Madrid (2025): 1.239,81 € (**dato**).
- Renta neta media por persona de la zona: 16.486 € frente a 19.129 € de media en la Comunidad (×0,86) (**dato** del INE, 2024; la de la zona es la media de sus secciones censales ponderada por población).
- Ajuste por renta (**supuesto**): gasto = población × gasto medio × (renta relativa) ^ elasticidad, con una elasticidad de 0,8 a 1,2 (el gasto en comer fuera crece más o menos en proporción a la renta), y un ±10 % por la población. Por eso se da un rango.
- Es lo que gastan los vecinos en cualquier sitio, no lo que facturaría un local: parte lo gastan lejos de casa y, a la vez, el local recibe gente que no vive aquí (ver el perfil por horas).

Fuentes: [Gasto medio de los hogares por subgrupo de gasto (3 dígitos COICOP/EPF) (Base 2006)](https://datos.comunidad.madrid/dataset/gasto_por_subgrupo_gasto_3_digitos_coicop_epf_base_2006) (Creative Commons Attribution; Encuesta de Presupuestos Familiares 2025; descargado el 2026-11-10); [INE. Atlas de distribución de renta de los hogares (ADRH), provincia de Madrid, por municipio, distrito y sección censal](https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177088&idp=1254735976608) (Reutilización libre citando la fuente: «Fuente: Instituto Nacional de Estadística (INE)» (aviso legal); renta y población 2024; descargado el 2026-11-09)

#### Gama de precios y evolución de precios · *dato + estimación*

Gama **media** (renta de la zona ×0,86 la media de la Comunidad). En los últimos 12 meses (hasta septiembre de 2026) restaurantes y alojamiento +5,7 % frente a alimentos +3,2 %.

- Gama (**estimación**): económica si la renta de la zona es menor que 0,85 veces la media de la Comunidad, alta si es mayor que 1,15, media entre medias. Se basa en la renta de los residentes: si la mayoría de los clientes no son vecinos (perfil por horas), tómese con cautela.
- IPC de la Comunidad de Madrid, tasa interanual de septiembre de 2026 (**dato**): restaurantes y servicios de alojamiento +5,7 %, alimentos y bebidas no alcohólicas +3,2 %, bebidas alcohólicas +0,6 %, índice general +5,3 %.
- El portal no publica una subclase solo de restaurantes: el grupo incluye hoteles, que han subido +18,0 %. La subida de bares y restaurantes por sí sola probablemente sea menor que la del grupo.

Fuentes: [INE. Atlas de distribución de renta de los hogares (ADRH), provincia de Madrid, por municipio, distrito y sección censal](https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177088&idp=1254735976608) (Reutilización libre citando la fuente: «Fuente: Instituto Nacional de Estadística (INE)» (aviso legal); renta 2024; descargado el 2026-11-09); [Índice de Precios de Consumo (IPC), por grupo. Base 2025. Comunidad de Madrid y España](https://datos.comunidad.madrid/dataset/ipc_base_2025) (Creative Commons Attribution; septiembre de 2026; descargado el 2026-11-10)

#### Turismo: alojamientos del código postal y del municipio · *dato + estimación*

Código postal 28971 (aproximado): 3 alojamientos turísticos inscritos. Municipio: 3 inscritos y 0 viviendas de uso turístico con declaración responsable.

- Código postal 28971: Hotel 1, Pension 1, Vivienda de uso turístico 1
- Municipio: Hotel 1, Pension 1, Vivienda de uso turístico 1

- **Aproximación**: no se convierten las direcciones en coordenadas. Se cuentan los alojamientos del mismo código postal y del mismo municipio, no los del radio.
- El código postal del punto es el más repetido entre los 5 centros sanitarios más cercanos (no hay límites de códigos postales en abierto): **estimación**.
- Registro de alojamientos (hoteles, hostales, apartamentos y viviendas de uso turístico inscritas) y declaraciones responsables de viviendas de uso turístico (conjunto aparte, solo con municipio): son **datos**; puede haber viviendas en los dos.
- No se muestran los nombres de los establecimientos.

Fuentes: [Alojamientos turísticos de la Comunidad de Madrid](https://datos.comunidad.madrid/dataset/alojamientos_turisticos) (Creative Commons Attribution; descargado el 2026-11-10); [Declaraciones responsables de actividad de viviendas de uso turístico de la Comunidad de Madrid presentadas](https://datos.comunidad.madrid/dataset/declaraciones_actividad_viviendas_uso_turistico) (Creative Commons Attribution; descargado el 2026-11-10)

#### Festivos de los próximos 12 meses · *dato + estimación*

3 festivos publicados hasta el 31/12/2026 (0 locales); los de 2027 aún no están publicados.

- 2026-12-07 (lunes): Día de la Constitución Española (regional o nacional)
- 2026-12-08 (martes): Inmaculada Concepción (regional o nacional)
- 2026-12-25 (viernes): Natividad del Señor (regional o nacional)
- Orientación para el año siguiente (fiestas locales de 2026): 2026-06-17 (Griñón), 2026-08-14 (Griñón)

- Festivos regionales y locales publicados en el portal (**dato**).
- El portal solo publica los festivos de 2026: los de 2027 aún no están. Como orientación se indica cuándo fueron en 2026 los que caerían antes del 10/11/2027 (**estimación**: muchas fiestas cambian de fecha cada año).

Fuentes: [Festivos regionales y locales año en curso](https://datos.comunidad.madrid/dataset/festivos_regionales_locales) (Creative Commons Attribution; año 2026; descargado el 2026-11-10)

#### Salud del sector (Comunidad de Madrid) · *dato*

Las empresas de distribución y hostelería de la Comunidad se mantienen: +0,3 % en el último año hasta el 4º trimestre de 2025 (+0,8 % frente a 2019). En 2026 (T1, T2) el saldo de altas y bajas es de +109 empresas, frente a -345 en los mismos trimestres de 2025.

- **Limitación importante**: el portal agrupa la hostelería con el comercio y el transporte en «Servicios de distribución y hostelería». No hay datos abiertos de empresas solo de hostelería; tampoco los afiliados a la Seguridad Social por municipio la separan.
- Último año (serie CNAE-2009): 13.420 altas y 13.203 bajas; el total de la economía madrileña varió +0,8 %.
- En 2026 cambia la clasificación (CNAE-2025) y 2.815 empresas pasan de esta rama a otras («saldo interno»): no son cierres. Por eso para 2026 se compara el saldo externo (altas − bajas ± traslados de sede) con los mismos trimestres del año anterior, y no el total.
- Es un dato de toda la Comunidad, no de la zona.

Fuentes: [Demografía empresarial de la Comunidad de Madrid. Unidades empresariales y puestos de trabajo asociados a las unidades empresariales, por rama de actividad (CNAE-2009)](https://datos.comunidad.madrid/dataset/demografia_empresarial_cnae09) (Creative Commons Attribution; 2009–2025; descargado el 2026-11-10); [Demografía empresarial de la Comunidad de Madrid. Unidades empresariales y puestos de trabajo asociados a las unidades empresariales, por rama de actividad (CNAE-2025)](https://datos.comunidad.madrid/dataset/demografia_empresarial_cnae25) (Creative Commons Attribution; 2026, trimestres T1, T2; descargado el 2026-11-10)


