"""Supuestos del perfil por horas (src/perfil_horario.py y src/procesar_perfil.py).

TODO LO DE ESTE FICHERO ES UNA ESTIMACIÓN. Son valores típicos elegidos a mano para un
prototipo, no medidas. Cada uno lleva un comentario con su origen o razonamiento; si se
consigue un dato mejor, se cambia aquí y todo lo demás se recalcula solo.

Convenciones:
  - Hora h = de h:00 a h:59 (0 a 23).
  - Un «paso» es una persona que pasa cerca del punto en esa hora. Quien entra y sale de
    un sitio cuenta dos pasos (uno al llegar y otro al irse).
  - Un perfil horario es un diccionario {hora: pasos por persona}; las horas que faltan
    valen 0. La suma de un perfil = pasos por persona y día.
"""

from __future__ import annotations

ES_ESTIMACION = True  # recordatorio para quien importe el módulo: nada de esto es medido

# --------------------------------------------------------------------- área de análisis
# Radio de 300 m: unos 4 minutos andando (a ~4,5 km/h). Es la distancia que se suele
# tomar como «a la vuelta de la esquina» para comercio de proximidad. ESTIMACIÓN.
RADIO_M = 300

# Peso por distancia: 1 en el punto y baja en línea recta hasta PESO_BORDE en el borde
# del radio. Lo que está más cerca aporta más gente que pasa por delante del local.
# El 0,25 es una elección (algo a 300 m cuenta la cuarta parte que algo en la puerta).
PESO_BORDE = 0.25


def peso_distancia(d_m: float, radio: float = RADIO_M) -> float:
    """Peso de algo situado a d_m metros (0 fuera del radio). ESTIMACIÓN."""
    if d_m > radio:
        return 0.0
    return 1.0 - (1.0 - PESO_BORDE) * d_m / radio


# Anillos para repartir la población de cada sección censal según la distancia
# (se calcula la superficie de la sección dentro de cada anillo de 50 m).
ANCHO_ANILLO_M = 50

# ---------------------------------------------------------------- comidas en España
# Horas típicas de las comidas en España (más tarde que en el resto de Europa).
# Fuente: costumbre general; el INE (Encuesta de Empleo del Tiempo 2009-2010) sitúa
# la comida principal hacia las 14-15 h y la cena hacia las 21-22 h. ESTIMACIÓN.
COMIDAS = {
    "desayuno": (7, 10),      # de 7:00 a 9:59 (en casa o de camino al trabajo)
    "media_manana": (10, 12),  # café o almuerzo de media mañana
    "comida": (14, 16),        # de 14:00 a 15:59
    "merienda": (17, 19),
    "cena": (21, 23),          # de 21:00 a 22:59
}

# ------------------------------------------------------------------- franjas del día
# Agrupación de las 24 horas para mostrar el resultado. Cubren todo el día sin solaparse.
FRANJAS = {
    "primera hora de la mañana": [6, 7, 8, 9],
    "media mañana": [10, 11, 12],
    "mediodía": [13, 14, 15],
    "media tarde": [16, 17, 18],
    "tarde-noche": [19, 20, 21, 22],
    "noche": [23, 0, 1, 2, 3, 4, 5],
}

# --------------------------------------------------------------------- tipos de cliente
TIPOS_CLIENTE = {
    "padres_ninos": "Padres y niños",
    "universitarios": "Universitarios",
    "pacientes": "Pacientes",
    "trabajadores": "Trabajadores",
    "deporte_eventos": "Deporte y eventos",
    "viajeros": "Viajeros",
    "vecinos": "Vecinos",
}

# Confianza de cada tipo de cliente, por separado para el HORARIO (a qué horas pasa la
# gente) y para la CANTIDAD (cuánta gente pasa), según la calidad del dato de partida.
# Niveles: alta (dato real y directo), media (dato real con un reparto o un supuesto
# razonable), orientativa (supuesto de orden de magnitud).
CONFIANZA = {
    "viajeros": {
        "horario": ("alta", "horarios reales del transporte público (GTFS del CRTM)"),
        "cantidad": ("media", "viajeros diarios reales de cada red (CRTM) y de las "
                              "estaciones grandes de Cercanías, repartidos por igual entre "
                              "los vehículos; sin datos por estación de Metro ni de autobús"),
    },
    "padres_ninos": {
        "horario": ("media", "horarios típicos de entrada y salida de cada etapa"),
        "cantidad": ("media", "alumnos reales por municipio o distrito repartidos a partes "
                              "iguales entre los centros"),
    },
    "universitarios": {
        "horario": ("media", "horario típico de mañana y tarde de una universidad"),
        "cantidad": ("media", "estudiantes reales por universidad repartidos entre sus "
                              "campus según la superficie (estimación)"),
    },
    "pacientes": {
        "horario": ("media", "horarios típicos de cada tipo de centro sanitario"),
        "cantidad": ("orientativa", "pacientes al día típicos por tipo de centro (supuesto)"),
    },
    "trabajadores": {
        "horario": ("media", "horario de acceso del registro cuando se puede leer; si no, "
                             "horario típico"),
        "cantidad": ("orientativa", "el registro solo dice el tamaño mínimo (más de 250 "
                                    "trabajadores…); plantilla supuesta"),
    },
    "deporte_eventos": {
        "horario": ("media", "horario de acceso del registro cuando se puede leer; si no, "
                             "horario típico"),
        "cantidad": ("orientativa", "usuarios o aforo mínimos del registro y probabilidad "
                                    "de evento supuesta"),
    },
    "vecinos": {
        "horario": ("orientativa", "costumbres generales de salida a la calle"),
        "cantidad": ("media", "población real del INE por sección censal, repartida por "
                              "superficie; pasos por vecino supuestos"),
    },
}

# Fin de semana: para el transporte se usa el horario de un sábado típico (el domingo
# suele tener aún menos servicio). Para lo demás, perfiles de fin de semana genéricos.


def perfil(**horas: float) -> dict[int, float]:
    """perfil(h8=0.5, h14=0.5) → {8: 0.5, 14: 0.5}."""
    return {int(k[1:]): v for k, v in horas.items()}


def escalar(p: dict[int, float], f: float) -> dict[int, float]:
    return {h: v * f for h, v in p.items()}


# ===================================================================== CENTROS EDUCATIVOS
# Enseñanzas tal como se llaman en «Estadísticas de alumnos» del portal (fichero
# alumnos_regimen_general_por_titularidad_y_financiacion.csv, columna ENSENANZA).
# Qué enseñanzas imparte cada centro se deduce de las palabras de su tipo (TIPO_EXT).
# ESTIMACIÓN: un IES puede no tener FP y un colegio privado puede no tener bachillerato.
ENSENANZAS_POR_PALABRA = [
    # (palabras que deben aparecer en TIPO_EXT, enseñanzas que se le asignan)
    (("CASA DE NIÑOS",), ["E. Infantil Primer Ciclo"]),
    (("CASAS DE NIÑOS",), ["E. Infantil Primer Ciclo"]),
    (("ESCUELA INFANTIL",), ["E. Infantil Primer Ciclo"]),
    (("INFANTIL",), ["E. Infantil Segundo Ciclo"]),
    (("PRIMARIA",), ["E. Primaria"]),
    (("EDUCACION GENERAL BASICA",), ["E. Infantil Segundo Ciclo", "E. Primaria"]),
    (("SECUNDARIA",), ["E.S.O.", "Bachillerato"]),
    (("INSTITUTO DE EDUCACIÓN SECUNDARIA",), ["C.F. Grado Básico", "C.F. Grado Medio",
                                               "C.F. Grado Superior"]),
    (("FORMACIÓN PROFESIONAL",), ["C.F. Grado Básico", "C.F. Grado Medio",
                                  "C.F. Grado Superior", "Cursos Especialización"]),
    (("EDUCACIÓN ESPECIAL",), ["Educación Especial"]),
]

# Titularidad del listado de centros → titularidad de la estadística de alumnos.
TITULARIDAD_ALUMNOS = {
    "PÚBLICO": "C. Públicos",
    "PÚBLICO-TITULARIDAD PRIVADA": "C. Públicos",
    "PRIVADO CONCERTADO": "C. Concertados",
    "PRIVADO": "C. Privados",
}

# Centros que no salen en la estadística de alumnos de régimen general (música,
# idiomas, adultos…): alumnos típicos por centro y perfil. ESTIMACIÓN a ojo a partir del
# tamaño habitual de estos centros. 0 = no recibe alumnos (equipos de orientación,
# oficinas).
PESO_TIPICO_EDUCATIVO = [
    # (palabra en TIPO_EXT, alumnos o usuarios al día, perfil)
    ("EQUIPO DE ORIENTACIÓN", 0, "tarde"),
    ("ESTABLECIMIENTO ADMINISTRATIVO", 0, "tarde"),
    ("CENTRO TERRITORIAL DE INNOVACIÓN", 0, "tarde"),
    ("INSTITUTO SUPERIOR MADRILEÑO", 0, "tarde"),
    ("ZONA CASAS DE NIÑOS", 0, "tarde"),  # es una agrupación administrativa
    ("AULA HOSPITALARIA", 10, "primaria"),
    ("ESCUELA OFICIAL DE IDIOMAS", 800, "tarde"),
    ("EXTENSION ESCUELA OFICIAL DE IDIOMAS", 200, "tarde"),
    ("PERSONAS ADULTAS", 300, "tarde"),
    ("ADULTOS", 300, "tarde"),
    ("MÚSICA", 200, "tarde"),
    ("DANZA", 150, "tarde"),
    ("ARTE", 200, "universidad"),
    ("DISEÑO", 200, "universidad"),
    ("UNIVERSIDAD", 3000, "universidad"),
    ("ENSEÑANZAS DEPORTIVAS", 100, "tarde"),
    ("CENTRO DOCENTE EXTRANJERO", 400, "primaria"),
    ("CENTRO DOCENTE MILITAR", 300, "universidad"),
]
PESO_TIPICO_EDUCATIVO_OTROS = (100, "tarde")  # cualquier otro tipo no previsto

# Desfibrilador de tipo «Centro educativo» que no tiene ningún centro del listado a menos
# de esta distancia: se trata como un centro de estudios que falta (academias, centros
# universitarios que no están en OpenStreetMap…), con horario de tipo universitario.
# Si está a menos de DEA_EDUCATIVO_CAMPUS_M de un campus universitario, no se cuenta
# (sus estudiantes ya salen del campus).
DEA_EDUCATIVO_DISTANCIA_M = 120
DEA_EDUCATIVO_CAMPUS_M = 150
DEA_EDUCATIVO_PESO = 1000      # usuarios al día (centro grande). ESTIMACIÓN.
DEA_EDUCATIVO_PERFIL = "universidad"
DEA_EDUCATIVO_CLIENTE = "universitarios"

# Acompañantes adultos por alumno (padres, abuelos, cuidadores) que van y vienen a la
# puerta. ESTIMACIÓN: casi todos los niños pequeños van acompañados; algunos hermanos
# comparten adulto, por eso menos de 1.
ACOMPANANTES = {
    "E. Infantil Primer Ciclo": 0.9,
    "E. Infantil Segundo Ciclo": 0.8,
    "E. Primaria": 0.6,
    "Educación Especial": 0.5,
    "E.S.O.": 0.1,
}

# Horarios típicos de entrada y salida (pasos por alumno en cada hora; entrada + salida
# ≈ 2). Fuente: horarios habituales de los centros de la Comunidad de Madrid.
# ESTIMACIÓN: cada centro decide su horario y cambia en septiembre y junio.
PERFIL_EDUCATIVO = {
    # Escuela infantil 0-3: entrada escalonada 7:30-9:30, salida 12:30-17:00.
    "E. Infantil Primer Ciclo": perfil(h7=0.3, h8=0.5, h9=0.2,
                                       h12=0.1, h13=0.1, h15=0.2, h16=0.4, h17=0.2),
    # Colegio (infantil 3-6 y primaria): entrada a las 9:00 (se llega de 8:45 a 9:00;
    # «primeros del cole» desde las 7:30); salida a las 14:00 sin comedor, a las 16:00
    # con comedor o jornada partida, y a las 17:00 tras extraescolares.
    "E. Infantil Segundo Ciclo": perfil(h7=0.1, h8=0.6, h9=0.3, h14=0.35, h16=0.55, h17=0.1),
    "E. Primaria": perfil(h7=0.1, h8=0.6, h9=0.3, h14=0.35, h16=0.55, h17=0.1),
    "Educación Especial": perfil(h8=0.4, h9=0.6, h16=0.7, h17=0.3),
    # Instituto (ESO y bachillerato): entrada 8:15-8:30, salida 14:20-15:15.
    "E.S.O.": perfil(h7=0.1, h8=0.9, h14=0.5, h15=0.5),
    "Bachillerato": perfil(h7=0.1, h8=0.9, h14=0.5, h15=0.5),
    # FP: aproximadamente mitad en turno de mañana (8-14:30) y mitad de tarde (15-21:30).
    "C.F. Grado Básico": perfil(h8=1.0, h14=1.0),
    "C.F. Grado Medio": perfil(h8=0.5, h14=0.5, h15=0.5, h21=0.5),
    "C.F. Grado Superior": perfil(h8=0.5, h14=0.5, h15=0.5, h21=0.5),
    "Cursos Especialización": perfil(h15=1.0, h21=1.0),
    # Centros de tarde (idiomas, música, adultos): clases de 17 a 21.
    "tarde": perfil(h16=0.2, h17=0.4, h18=0.4, h19=0.3, h20=0.4, h21=0.3),
    # Universidad y centros grandes sin datos: turno de mañana (8:30-14:30) y de tarde
    # (15-21), con gente entrando y saliendo durante todo el día entre clases.
    "universidad": perfil(h8=0.35, h9=0.25, h10=0.1, h11=0.1, h12=0.1, h13=0.15,
                          h14=0.3, h15=0.25, h16=0.1, h17=0.1, h18=0.1, h19=0.1,
                          h20=0.1, h21=0.2),
    "primaria": perfil(h8=0.6, h9=0.4, h14=0.35, h16=0.55, h17=0.1),
}
# En fin de semana no hay clase. ESTIMACIÓN: se ignoran actividades de sábado.
EDUCATIVO_FIN_DE_SEMANA = 0.0

# ================================================================== UNIVERSIDADES
# Estudiantes: Grado + máster presenciales por universidad del último curso publicado
# en el portal de la Comunidad (conjuntos 1925489 y 1925502). No hay datos por campus.
# Ubicación: recintos `amenity=university` de OpenStreetMap.
#
# Asignación de cada elemento de OSM a una universidad: por palabras de su nombre y su
# operador (UNIVERSIDADES_PALABRAS); si no las tiene, por estar dentro del recinto de una
# universidad ya asignada. Los elementos de una misma universidad a menos de
# CAMPUS_UNION_M se unen en un solo campus (facultades sueltas de un mismo campus).
CAMPUS_UNION_M = 300

# Reparto de los estudiantes de una universidad entre sus campus. ESTIMACIÓN: en
# proporción a la raíz cuadrada de la superficie del campus (en hectáreas, con un
# mínimo de 1 ha para edificios sueltos o puntos). La raíz cuadrada amortigua el tamaño:
# los campus grandes tienen mucho espacio verde, deportivo o de aparcamiento, así que sus
# alumnos no crecen en proporción a la superficie. Ejemplo: un campus de 36 ha recibe
# 6 partes y uno de 391 ha, unas 20 (no 11 veces más).
CAMPUS_SUPERFICIE_MINIMA_HA = 1.0

# Elementos de OSM con amenity=university que no son centros de estudio (residencias,
# museos, oficinas, un instituto de secundaria mal etiquetado…). No se cuentan.
CAMPUS_EXCLUIR = ("COLEGIO MAYOR", "COLEGIO MENOR", " HALL", "MUSEO", "OFFICES",
                  "INSTITUTO DE EDUCACION SECUNDARIA", "RESIDENCIA")

# Centros universitarios o de estudios superiores de OSM que no son de ninguna de las
# universidades de la estadística (UNED, escuelas de negocios, universidades extranjeras,
# centros adscritos…): estudiantes al día típicos. ESTIMACIÓN.
CAMPUS_SIN_DATOS_ESTUDIANTES = 300

# Fracción de los matriculados que va al campus un día lectivo cualquiera (clases que no
# son diarias, prácticas, ausencias). ESTIMACIÓN.
UNIVERSIDAD_ASISTENCIA = 0.7

# Horario: el perfil «universidad» de PERFIL_EDUCATIVO (turno de mañana y de tarde). En
# fin de semana no hay clase (EDUCATIVO_FIN_DE_SEMANA).

# Los estudiantes se suponen repartidos por igual en la superficie del campus; se
# calcula como con los vecinos (superficie dentro de cada anillo de 50 m). Los puntos se
# tratan como un círculo de CAMPUS_SUPERFICIE_MINIMA_HA.

# ===================================================================== CENTROS SANITARIOS
# Pacientes y acompañantes al día por tipo de centro (columna centro_tipo del registro
# de centros sanitarios del portal). ESTIMACIÓN de orden de magnitud: un centro de salud
# de Madrid atiende a una población de 20.000-30.000 personas y ve a varios cientos de
# pacientes al día; una consulta privada, de 10 a 20.
PACIENTES_DIA = {
    "Centro de salud": 500,
    "Consultorio de atención primaria": 80,
    "Hospital general": 3000,         # consultas externas, urgencias y visitas
    "Hospital especializado": 800,
    "Hospital de media y larga estancia": 300,
    "Hospital de salud mental y tratamiento de toxicomanías": 200,
    "Otros centros con internamiento": 100,
    "Centro de cirugía mayor ambulatoria": 80,
    "Centro de diálisis": 60,
    "Centro de diagnóstico": 80,
    "Centro de salud mental": 100,
    "Centro Polivalente": 40,
    "Otros centros especializados": 30,
    "Centro de reconocimiento": 30,      # reconocimientos de carné de conducir, etc.
    "Centro de reproducción humana asistida": 30,
    "Centro de interrupción voluntaria del embarazo": 20,
    "Centro de transfusión": 50,
    "Clínica dental": 15,
    "Consulta médica": 15,
    "Consulta de otros profesionales sanitarios": 12,  # fisioterapia, psicología, podología…
    "Otros proveedores de asistencia sanitaria sin internamiento": 15,
    # Sin público de la calle: servicios médicos de empresas, colegios, residencias;
    # unidades móviles; bancos de tejidos.
    "Servicio sanitario integrado en una organización no sanitaria": 0,
    "Centro móvil de asistencia sanitaria": 0,
    "Banco de tejidos": 0,
}
PACIENTES_DIA_OTROS = 15

# Qué horario se aplica a cada tipo (si no está en la lista, «consulta»).
HORARIO_SANITARIO = {
    "Centro de salud": "centro_salud",
    "Consultorio de atención primaria": "consultorio",
    "Hospital general": "hospital",
    "Hospital especializado": "hospital",
    "Hospital de media y larga estancia": "hospital",
    "Hospital de salud mental y tratamiento de toxicomanías": "hospital",
    "Otros centros con internamiento": "hospital",
    "Centro de diálisis": "dialisis",
}

# Horarios típicos (pasos por paciente: llegada + salida ≈ 2).
# Centro de salud del SERMAS: abierto de lunes a viernes de 8:00 a 21:00; más demanda por
# la mañana (9-13) que por la tarde. Los sábados por la mañana solo abren algunos.
# Consultorio local (pueblos pequeños): solo por la mañana.
# Hospital: consultas externas por la mañana, visitas a planta por la tarde (habituales
# de 12 a 21) y cambios de turno del personal a las 8, 15 y 22.
# Consultas y clínicas privadas: de 10 a 14 y de 16 a 20.
# Diálisis: turnos de mañana, tarde y noche de unas 4 horas.
# Todo ESTIMACIÓN.
PERFIL_SANITARIO = {
    "laborable": {
        "centro_salud": perfil(h8=0.15, h9=0.25, h10=0.25, h11=0.25, h12=0.25, h13=0.2,
                               h14=0.12, h15=0.08, h16=0.1, h17=0.12, h18=0.12, h19=0.08,
                               h20=0.03),
        "consultorio": perfil(h8=0.2, h9=0.4, h10=0.4, h11=0.4, h12=0.4, h13=0.2),
        "hospital": perfil(h7=0.1, h8=0.2, h9=0.18, h10=0.16, h11=0.15, h12=0.14,
                           h13=0.13, h14=0.12, h15=0.13, h16=0.1, h17=0.12, h18=0.12,
                           h19=0.12, h20=0.1, h21=0.08, h22=0.05, h23=0.02, h0=0.01,
                           h1=0.01, h2=0.01, h3=0.01, h4=0.01, h5=0.01, h6=0.02),
        "dialisis": perfil(h7=0.4, h11=0.3, h12=0.3, h15=0.3, h16=0.3, h20=0.4),
        "consulta": perfil(h9=0.1, h10=0.25, h11=0.25, h12=0.25, h13=0.2, h14=0.05,
                           h16=0.15, h17=0.25, h18=0.25, h19=0.2, h20=0.05),
    },
    "fin_de_semana": {
        "centro_salud": {},
        "consultorio": {},
        "hospital": perfil(h8=0.05, h9=0.08, h10=0.1, h11=0.12, h12=0.14, h13=0.12,
                           h14=0.08, h15=0.08, h16=0.12, h17=0.14, h18=0.14, h19=0.12,
                           h20=0.1, h21=0.06, h22=0.04, h23=0.02),
        "dialisis": perfil(h7=0.4, h11=0.3, h12=0.3, h15=0.3, h16=0.3, h20=0.4),
        # Solo algunas abren el sábado por la mañana: un 30 % de la actividad.
        "consulta": perfil(h10=0.1, h11=0.15, h12=0.15, h13=0.1),
    },
}
# Factor de fin de semana del total de pacientes del hospital (menos consultas).
HOSPITAL_FIN_DE_SEMANA = 0.5

# ================================================== DESFIBRILADORES: trabajo, deporte...
# El registro de desfibriladores (DEA) del portal es obligatorio en sitios con mucha
# gente (Decreto 78/2017 de la Comunidad de Madrid: centros de trabajo de más de 250
# trabajadores, instalaciones deportivas de más de 500 usuarios diarios, recintos de
# 2.000 personas, grandes superficies, hoteles grandes, transporte…). Por eso sirve para
# ubicar centros de trabajo grandes, polideportivos y recintos. Su tipo dice el tamaño
# mínimo; se toma un valor algo por encima del mínimo. ESTIMACIÓN.
DEA_TIPOS = {
    # tipo_establecimiento: (tipo de cliente, personas al día, horario típico)
    "Centro de trabajo con más de 250 trabajadores": ("trabajadores", 400, "oficina"),
    "Establecimiento dependiente de una Administración Pública":
        ("trabajadores", 60, "administracion"),
    "Grandes establecimientos comerciales con una superficie superior a 2500 m2":
        ("trabajadores", 80, "comercio"),           # solo la plantilla, no los compradores
    "Establecimiento hotelero con más de 100 plazas": ("trabajadores", 40, "turnos"),
    "Centros residenciales de mayores con 200 plazas": ("trabajadores", 80, "turnos"),
    "Instalación, centro o complejo deportivo con más de 500 usuarios diarios":
        ("deporte_eventos", 500, "deporte"),
    "Establecimiento público con aforo igual o superior a 2000 personas":
        ("deporte_eventos", 2000, "eventos"),
    # No se usan:
    #  - «Centro educativo»: los colegios ya vienen del listado de centros educativos
    #    (salvo los que faltan, ver DEA_EDUCATIVO_*).
    #  - «Instalaciones de transporte» y «Aeropuertos»: los viajeros salen del GTFS.
    #  - «Otros»: no se sabe qué es (farmacias, gimnasios pequeños, comercios…).
}

# Desfibriladores del mismo tipo a menos de esta distancia se cuentan como un solo sitio
# (un edificio grande suele tener varios). ESTIMACIÓN.
DEA_FUSION_M = 50

# Recintos de eventos: probabilidad de que haya un evento un día cualquiera y fracción
# del aforo que acude. ESTIMACIÓN: en un recinto grande hay eventos algunos días a la
# semana, sobre todo en fin de semana.
EVENTOS_PROB = {"laborable": 0.1, "fin_de_semana": 0.3}
EVENTOS_OCUPACION = 0.6

# Horarios típicos de cada tipo (pasos por persona y día).
PERFIL_DEA = {
    "laborable": {
        # Oficina o fábrica: entrada 7-9, salida a comer (un tercio sale), salida 17-19.
        "oficina": perfil(h7=0.2, h8=0.5, h9=0.3, h14=0.3, h15=0.3, h17=0.3, h18=0.4,
                          h19=0.3),
        # Administración: jornada de mañana de 8 a 15, con atención al público.
        "administracion": perfil(h7=0.2, h8=0.6, h9=0.2, h11=0.1, h12=0.1, h14=0.4,
                                 h15=0.6),
        # Comercio: turnos de mañana (9:30-16) y de tarde (15:30-22).
        "comercio": perfil(h9=0.5, h15=0.5, h16=0.5, h21=0.2, h22=0.3),
        # Turnos de 8 horas: 7-15, 15-23, 23-7 (hoteles, residencias).
        "turnos": perfil(h6=0.2, h7=0.3, h14=0.2, h15=0.5, h22=0.3, h23=0.5),
        # Polideportivo: antes del trabajo, a mediodía y sobre todo por la tarde.
        "deporte": perfil(h7=0.08, h8=0.08, h9=0.08, h10=0.08, h11=0.08, h12=0.08,
                          h13=0.1, h14=0.08, h15=0.06, h16=0.1, h17=0.2, h18=0.26,
                          h19=0.26, h20=0.24, h21=0.16, h22=0.06),
        # Evento entre semana: entrada 18-20, salida 21-23.
        "eventos": perfil(h18=0.3, h19=0.5, h20=0.2, h21=0.3, h22=0.5, h23=0.2),
    },
    "fin_de_semana": {
        "oficina": escalar(perfil(h8=0.5, h9=0.5, h14=0.5, h15=0.5), 0.15),
        "administracion": {},
        "comercio": perfil(h9=0.5, h15=0.5, h16=0.5, h21=0.2, h22=0.3),
        "turnos": perfil(h6=0.2, h7=0.3, h14=0.2, h15=0.5, h22=0.3, h23=0.5),
        "deporte": perfil(h8=0.1, h9=0.2, h10=0.26, h11=0.26, h12=0.24, h13=0.16,
                          h14=0.06, h16=0.08, h17=0.14, h18=0.16, h19=0.12, h20=0.06),
        # Fin de semana: partidos y eventos a mediodía o por la tarde-noche.
        "eventos": perfil(h11=0.15, h12=0.25, h14=0.25, h15=0.15, h17=0.15, h18=0.3,
                          h19=0.15, h20=0.15, h21=0.3, h22=0.15),
    },
}

# Desfibriladores con horario «HORARIO AUTOBUS URBANO» o parecido: están dentro de
# autobuses; su dirección es la del depósito, no un sitio con gente. Se descartan.
DEA_PALABRAS_VEHICULO = ("AUTOBUS", "AUTOBÚS", "VEHICULO", "VEHÍCULO", "AMBULANCIA")

# Interpretación de expresiones habituales del campo horario_acceso.
# ESTIMACIÓN: «horario de oficina» = 8-18, «comercial» = 10-21, «lectivo» = 8-17.
HORARIO_EXPRESIONES = {
    "oficina": (8, 18),
    "laboral": (8, 18),
    "comercial": (10, 21),
    "lectivo": (8, 17),
    "escolar": (8, 17),
}

# Cuando se conoce el horario (apertura y cierre) de un centro de trabajo o de una
# administración, el perfil se construye a partir de él. ESTIMACIÓN:
#  - llegada: el 70 % en la hora de apertura (llegan unos minutos antes) y el 30 % en la
#    siguiente;
#  - salida: el 40 % en la media hora anterior al cierre y el 60 % a la hora del cierre;
#  - si la jornada abarca la hora de comer (14-16) y dura 8 horas o más, un 30 % sale a
#    comer fuera (dos pasos: ida y vuelta);
#  - si el edificio abre más de 12 horas, se supone que hay dos turnos con la mitad de la
#    plantilla cada uno;
#  - en fin de semana, si el texto dice que abre, trabaja la mitad de la plantilla.
JORNADA_LLEGADA = (0.7, 0.3)
JORNADA_SALIDA = (0.4, 0.6)
SALEN_A_COMER = 0.3
JORNADA_MAX_UN_TURNO_H = 12
PLANTILLA_FIN_DE_SEMANA = 0.5

# Un horario de acceso de 24 horas casi siempre quiere decir que el aparato está en un
# sitio accesible desde la calle, no que el edificio tenga gente toda la noche. En ese
# caso se usa el horario típico del tipo de establecimiento. ESTIMACIÓN.

# =================================================================== TRANSPORTE PÚBLICO
# Personas que suben o bajan en una parada por cada vehículo que pasa.
#
# CALIBRACIÓN (src/procesar_perfil.py): con la demanda diaria real de cada red publicada
# por el CRTM (Observatorio de la Demanda; Metro, EMT, concesiones por carretera y
# Cercanías) se calcula, para un laborable y un sábado típicos:
#     personas por paso = 2 × viajeros del día / pasos de vehículos del día en el GTFS
# El 2 es porque cada viaje sube en una parada y baja en otra. Supuestos: todas las
# paradas de una red reciben la misma gente por vehículo (no hay datos por estación de
# Metro ni de autobús); los transbordos dentro de Metro no salen a la calle y no cuentan;
# «concesiones por carretera» engloba interurbanos y urbanos de otros municipios.
# En las estaciones de Cercanías con dato propio (viajeros subidos y bajados por
# estación, portal de la Comunidad) se usa el de la estación.
#
# Valores de respaldo (los de la versión anterior), solo para las redes sin demanda
# publicada (Metro Ligero) o si falta el fichero de demanda. ESTIMACIÓN de orden de
# magnitud a partir de los viajeros anuales de cada red.
VIAJEROS_POR_PASO = {
    "metro": 40,
    "cercanias": 60,
    "metro_ligero": 10,
    "emt": 5,
    "interurbanos": 4,
    "urbanos": 3,
}
# Columna del Excel de demanda que corresponde a cada red del GTFS.
DEMANDA_COLUMNA = {
    "metro": "Metro de Madrid",
    "emt": "EMT",
    "interurbanos": "Conc. por carretera",
    "urbanos": "Conc. por carretera",
    "cercanias": "Renfe Cercanías",
}
# Días de la demanda que se usan: las últimas DEMANDA_SEMANAS semanas publicadas; el
# laborable típico es la mediana de martes a jueves y el sábado, la de los sábados.
# Se descartan los días con menos del 80 % de la mediana (festivos, huelgas).
DEMANDA_SEMANAS = 8
DEMANDA_DESCARTE = 0.8

# Peso de una parada según la distancia. Quien sale del metro o baja del autobús va en
# cualquier dirección: a la puerta de la parada pasan todos, pero a 250 m solo los que
# van justo hacia el local. Por eso las paradas pesan menos con la distancia que el resto
# de cosas (que usan peso_distancia). ESTIMACIÓN: peso 1 hasta 50 m y a partir de ahí se
# reduce a la mitad cada 75 m (0,5 a 125 m; 0,25 a 200 m; 0,1 a 300 m). Las calles
# concentran el paso, así que se cae menos deprisa que si la gente se repartiera por
# igual en todas direcciones.
PARADA_DISTANCIA_PLENA_M = 50
PARADA_SEMIDISTANCIA_M = 75


def peso_parada(d_m: float, radio: float = RADIO_M) -> float:
    """Peso de una parada a d_m metros (0 fuera del radio). ESTIMACIÓN."""
    if d_m > radio:
        return 0.0
    return 0.5 ** (max(0.0, d_m - PARADA_DISTANCIA_PLENA_M) / PARADA_SEMIDISTANCIA_M)


# Metro y Metro Ligero: la distancia se mide al acceso más cercano de la estación (por
# donde sale la gente a la calle), no al andén. Accesos del GTFS (location_type 2).

# Para elegir un día típico de cada GTFS se miran los martes, miércoles y jueves (y los
# sábados) de las primeras semanas de vigencia y se toma el de número de viajes mediano,
# para no caer en un festivo ni en un día especial.
GTFS_SEMANAS_MUESTRA = 4

# ============================================================================= VECINOS
# Pasos por residente y día cerca de casa. La Encuesta Domiciliaria de Movilidad del
# CRTM (2018) da del orden de 2,5-3 desplazamientos por persona en un día laborable; en
# torno a la mitad empiezan o acaban en casa y cada uno supone pasar por la calle de
# casa; a eso se suman paseos y recados cortos. ESTIMACIÓN: 2 pasos en laborable y 1,6
# en fin de semana (menos desplazamientos al trabajo).
PASOS_VECINO = {"laborable": 2.0, "fin_de_semana": 1.6}

# Reparto por horas de esos pasos (se normaliza para que sume 1). ESTIMACIÓN basada en
# las horas habituales de salida al trabajo y al colegio, compras de mañana, vuelta a
# comer, tarde de recados y paseo, y salir a cenar o de copas el fin de semana.
REPARTO_VECINOS = {
    "laborable": perfil(h0=0.5, h1=0.3, h2=0.2, h3=0.1, h4=0.1, h5=0.2, h6=1.0, h7=4.5,
                        h8=8.0, h9=6.0, h10=5.0, h11=5.0, h12=5.0, h13=6.0, h14=6.0,
                        h15=4.0, h16=4.0, h17=6.0, h18=7.0, h19=7.0, h20=6.0, h21=4.5,
                        h22=2.5, h23=1.2),
    "fin_de_semana": perfil(h0=1.2, h1=0.8, h2=0.5, h3=0.3, h4=0.2, h5=0.1, h6=0.3, h7=0.8,
                            h8=2.0, h9=4.0, h10=6.5, h11=8.0, h12=8.0, h13=7.5, h14=6.0,
                            h15=4.0, h16=4.0, h17=6.0, h18=7.0, h19=7.5, h20=6.5, h21=5.5,
                            h22=4.0, h23=2.5),
}
# La población de cada sección se supone repartida de forma uniforme por su superficie.


# #########################################################################################
# INFORME DEL LOCAL (src/informe_local.py). Mismo radio que el perfil por horas (RADIO_M).
# #########################################################################################

# ----------------------------------------------------------------------- 1. competencia
# Tipos de local que se cuentan. En Madrid capital se usa el censo de locales del
# Ayuntamiento (epígrafes de la división CNAE 56); en el resto, OpenStreetMap.
TIPOS_COMPETENCIA = {
    "bar": "Bares",
    "restaurante": "Restaurantes",
    "cafeteria": "Cafeterías",
    "comida_rapida": "Comida rápida",
}
# Epígrafe del censo de Madrid → tipo. ESTIMACIÓN en dos casos dudosos: el «bar
# restaurante» se cuenta como bar (es el bar español con menú, no un restaurante a la
# carta) y la chocolatería, salón de té o heladería como cafetería.
EPIGRAFE_COMPETENCIA = {
    "561001": "restaurante",    # restaurante
    "561003": "restaurante",    # autoservicio de restauración
    "561002": "comida_rapida",  # restaurantes de comida rápida
    "561008": "comida_rapida",  # establecimiento de restauración móvil
    "561006": "cafeteria",      # cafetería
    "561007": "cafeteria",      # chocolatería, salón de té y heladería
    "563006": "cafeteria",      # ciber-café
    "561004": "bar",            # bar restaurante
    "561005": "bar",            # bar con cocina
    "563005": "bar",            # bar sin cocina
    "563001": "bar",            # bodega con consumo
    "563002": "bar",            # bar especial sin actuaciones
    "563003": "bar",            # bar especial con actuaciones
    "563004": "bar",            # taberna
    "563007": "bar",            # café espectáculo
}
# Un local con varios epígrafes cuenta una sola vez, con el tipo más específico.
PRIORIDAD_COMPETENCIA = ["comida_rapida", "restaurante", "cafeteria", "bar"]
# Etiqueta amenity de OpenStreetMap → tipo («pub» se cuenta como bar: en España casi
# todos los bares de copas y muchos bares de barrio están etiquetados así).
AMENITY_COMPETENCIA = {"restaurant": "restaurante", "bar": "bar", "pub": "bar",
                       "cafe": "cafeteria", "fast_food": "comida_rapida"}
# Densidad «media del municipio»: número medio de locales a menos de RADIO_M de donde
# vive la gente del municipio (media de las secciones censales ponderada por población).
# Así se compara con un punto típico habitado y no con la superficie total del término
# municipal, que incluye campo y polígonos. ESTIMACIÓN de referencia.
# Aviso de cobertura de OpenStreetMap: si en el municipio OSM tiene menos de este
# porcentaje de los locales por habitante que el censo oficial de Madrid capital, se
# avisa de que probablemente faltan locales. ESTIMACIÓN: los pueblos tienen algo menos
# de bares por habitante que la capital, por eso no se pide el 100 %.
COBERTURA_OSM_AVISO = 0.6
# Cuántos tipos de cocina se muestran como máximo.
COCINAS_MAX = 10

# --------------------------------------------------------------- 2. mercado potencial
# Gasto en restauración de los residentes del radio (gasten donde gasten):
#     población × gasto medio por persona en restauración (Comunidad de Madrid)
#     × (renta de la zona / renta media de la Comunidad) ^ elasticidad
# La elasticidad dice cuánto sube el gasto en restauración si sube la renta: 1 =
# proporcional. En las encuestas de presupuestos familiares el gasto en comer y beber
# fuera crece aproximadamente en proporción a la renta del hogar (algo más en unos años,
# algo menos en otros). ESTIMACIÓN: se usa un rango de 0,8 a 1,2.
ELASTICIDAD_RESTAURACION = (0.8, 1.2)
# Margen adicional por la población (dato de 2024, repartida por igual en la superficie
# de cada sección). ESTIMACIÓN: ±10 %.
MARGEN_POBLACION = 0.10

# ------------------------------------------------------------------ 3. gama de precios
# Gama según la renta neta media por persona de la zona frente a la media de la
# Comunidad. ESTIMACIÓN: ±15 % alrededor de la media es «media».
GAMA_UMBRALES = (0.85, 1.15)   # por debajo: económica; por encima: alta
# Grupos del IPC (portal, Comunidad de Madrid) que se comparan. El portal no publica una
# subclase solo de restaurantes: el grupo «Restaurantes y servicios de alojamiento»
# incluye hoteles, así que se muestra también «Hoteles» para ver su efecto.
IPC_GRUPOS = {
    "restaurantes_alojamiento": "Restaurantes y servicios de alojamiento",
    "hoteles": "Hoteles",
    "alimentos": "Alimentos y bebidas no alcohólicas",
    "bebidas_alcoholicas": "Bebidas alcohólicas",
    "general": "Índice general",
}

# --------------------------------------------------------------------------- 4. turismo
# El código postal del punto se aproxima con el código postal más repetido entre los
# centros sanitarios más cercanos (su dirección lo trae). No hay límites de códigos
# postales en abierto. ESTIMACIÓN.
CP_VECINOS = 5          # centros sanitarios que se miran
CP_DISTANCIA_MAX_M = 1000

# -------------------------------------------------------------------------- 5. festivos
# Si el portal aún no publica los festivos del año siguiente, se muestran los del año en
# curso como orientación de cuándo suelen caer (ESTIMACIÓN: muchas fiestas locales
# cambian de fecha cada año).
FESTIVOS_MESES = 12


# #########################################################################################
# RECOMENDACIONES (src/recomendaciones.py) y correcciones de la parte A que las alimentan.
# Todo ESTIMACIÓN; cada valor lleva su justificación.
# #########################################################################################

# ------------------------------------------------- A1. locales que sirven comidas
# En el censo de Madrid el «bar restaurante» cuenta como bar, así que «restaurantes» a
# secas infravalora mucho la oferta de comidas. «Locales que sirven comidas» = locales
# con alguno de estos epígrafes. Se incluyen el bar restaurante y el bar con cocina (en
# la normativa de Madrid tienen cocina y sirven comidas). No se incluyen la cafetería
# (sirve platos combinados, pero su negocio principal es el café: dudosa, se cuenta
# aparte), el bar sin cocina ni la comida rápida (se cuenta en su propio tipo).
EPIGRAFES_SIRVEN_COMIDAS = {
    "561001",  # restaurante
    "561003",  # autoservicio de restauración
    "561004",  # bar restaurante
    "561005",  # bar con cocina
}
# OpenStreetMap, criterio más parecido posible: todos los `restaurant`, y los `bar`,
# `pub` y `cafe` que dicen servir comida, bien con `food=yes` (etiqueta casi nunca
# usada) o bien con un tipo de cocina (`cuisine`) que no sea solo de café, dulce o
# bebida. Aproximación: muchos bares de OSM que sirven comida no lo indican.
OSM_SIRVE_COMIDAS_AMENITY = {"restaurant"}
OSM_COCINAS_NO_COMIDA = {"coffee_shop", "coffee", "tea", "ice_cream", "cake", "churro",
                         "juice", "bubble_tea", "donut", "crepe", "dessert", "cocktail",
                         "wine", "beer", "chocolate", "frozen_yogurt", "pastry"}

# ----------------------------------------------------- A2. gama ajustada a la clientela
# Escala numérica de las gamas para poder hacer medias ponderadas.
GAMA_NUM = {"económica": 1.0, "media": 2.0, "alta": 3.0}
# Media ponderada → gama: por debajo de 1,67 económica, por encima de 2,33 alta (los
# tercios del intervalo 1-3).
GAMA_CORTES = (1.67, 2.33)
# Gama supuesta de cada tipo de cliente. «zona» = la gama de la renta de los vecinos.
GAMA_CLIENTE = {
    "vecinos": "zona",          # su renta es la de la zona (dato del INE)
    "padres_ninos": "zona",     # los colegios escolarizan sobre todo a niños del barrio
    "pacientes": "zona",        # el centro de salud atiende a su zona básica de salud;
                                # en consultas y hospitales el origen es más variado
    "universitarios": 1.0,      # presupuesto de estudiante: buscan precio (menú barato,
                                # café y bocadillo); su renta familiar no es la que gastan
    "viajeros": 1.5,            # de paso: compra rápida y de poco importe, muy sensible
                                # al precio y al tiempo; renta muy variada
    "trabajadores": 2.0,        # menú del día a precio de mercado; parte paga con
                                # tarjeta o ticket de comida de la empresa
    "deporte_eventos": 2.0,     # gente de toda la zona o de fuera; gasto de ocio medio
}
# La gama ajustada de la semana suma 5 laborables y 1 sábado. El perfil por horas no
# modela el domingo aparte (su «fin de semana» usa el horario de transporte del sábado),
# así que el domingo no entra en la media.
DIAS_SEMANA = {"laborable": 5, "fin_de_semana": 1}

# ------------------------------------------------------- propensión a pararse a consumir
# Qué parte de la gente que pasa de cada tipo puede pararse a consumir, frente a un vecino.
# El perfil cuenta gente que PASA; no todos son clientes posibles. ESTIMACIÓN:
#  - viajeros 0,3: van de paso hacia el transporte o el destino; la mayoría no se para
#    (sobre todo en hora punta), solo el café para llevar o la caña de vuelta;
#  - padres y niños 0,6: el perfil cuenta a niños y adultos, pero quien decide y paga es
#    el adulto (unos 0,6-0,9 adultos por niño en infantil y primaria; los de secundaria
#    van solos y gastan poco);
#  - el resto 1: vecinos, estudiantes, trabajadores, pacientes y público de eventos están
#    en la zona un rato y tienen huecos para consumir.
# Se usa para ponderar a quién orientar la oferta, los momentos de consumo y la gama
# ajustada (no cambia el perfil por horas, que sigue contando gente que pasa).
PROPENSION_CONSUMO = {
    "viajeros": 0.3,
    "vecinos": 1.0,
    "universitarios": 1.0,
    "trabajadores": 1.0,
    "padres_ninos": 0.6,
    "pacientes": 1.0,
    "deporte_eventos": 1.0,
}
# La confianza horaria de una franja la marcan los tipos de cliente que pesan al menos
# esto en ella (un tipo minoritario con horario poco fiable no la rebaja).
PESO_CONFIANZA_FRANJA = 0.25

# ------------------------------------------------------------------------- B1. a quién
# Tipos de cliente que se muestran en cada franja: los que suman al menos este peso.
PESO_MINIMO_CLIENTE = 0.10

# ----------------------------------------------------------------------- B2. a qué hora
# Se compara la gente por hora de cada franja (media de sus horas) con la de la mejor
# franja del día: ≥ 50 % «abrir», 30-50 % «valorar», < 30 % «no compensa». Los cortes son
# una elección razonable para un prototipo (un bar pequeño suele cubrir costes si la
# franja tiene al menos la mitad del movimiento de la mejor).
APERTURA_ABRIR = 0.5
APERTURA_VALORAR = 0.3
# Para comparar con los horarios de la competencia (etiqueta opening_hours de OSM) hace
# falta un mínimo de locales con horario en el radio.
HORARIOS_MINIMO_LOCALES = 3
# Día de la semana que representa al laborable y al sábado en opening_hours.
DIA_OSM = {"laborable": "We", "fin_de_semana": "Sa"}
# Una franja es un posible hueco horario si tiene movimiento suficiente («abrir») y abre
# en ella menos de este porcentaje de los locales con horario conocido.
HUECO_HORARIO = 0.4

# ---------------------------------------------------------------------- B3. qué vender
MOMENTOS = {
    "desayuno": "Desayuno",
    "almuerzo": "Almuerzo de media mañana",
    "menu_del_dia": "Menú del día",
    "merienda": "Merienda",
    "canas_raciones": "Cañas y raciones",
    "cenas": "Cenas",
    "copas": "Copas",
}
# Tabla tipo de cliente × franja → momentos de consumo. Origen: horarios de comidas en
# España (COMIDAS, arriba), horarios de cada tipo de cliente (perfil por horas) y
# costumbres generales de la hostelería española. ESTIMACIÓN cualitativa.
F1, F2, F3, F4, F5, F6 = list(FRANJAS)   # primera hora … noche
TABLA_MOMENTOS = {
    # Vecinos: café de camino al trabajo o al colegio; media mañana de jubilados, gente que
    # teletrabaja y recados; menú del día entre semana; merienda y paseo; cañas y cena; copas.
    ("vecinos", F1): ["desayuno"],
    ("vecinos", F2): ["almuerzo"],
    ("vecinos", F3): ["menu_del_dia", "canas_raciones"],
    ("vecinos", F4): ["merienda"],
    ("vecinos", F5): ["canas_raciones", "cenas"],
    ("vecinos", F6): ["copas"],
    # Trabajadores: desayuno antes de entrar, la pausa del almuerzo (bocadillo y café hacia
    # las 10:30-11:30), menú del día a la hora de comer y la caña a la salida.
    ("trabajadores", F1): ["desayuno"],
    ("trabajadores", F2): ["almuerzo"],
    ("trabajadores", F3): ["menu_del_dia"],
    ("trabajadores", F4): ["canas_raciones"],
    ("trabajadores", F5): ["canas_raciones"],
    # Universitarios: café antes de clase, descanso entre clases, menú barato al cambio de
    # turno, merienda por la tarde y cañas al salir del turno de tarde.
    ("universitarios", F1): ["desayuno"],
    ("universitarios", F2): ["almuerzo"],
    ("universitarios", F3): ["menu_del_dia"],
    ("universitarios", F4): ["merienda"],
    ("universitarios", F5): ["canas_raciones"],
    # Viajeros: café y bollería para llevar al ir al trabajo, algo rápido a media mañana o
    # media tarde y una caña a la vuelta. A mediodía y de noche pasan de largo (se come en
    # el destino; los búhos van a casa): sin momento.
    ("viajeros", F1): ["desayuno"],
    ("viajeros", F2): ["almuerzo"],
    ("viajeros", F4): ["merienda"],
    ("viajeros", F5): ["canas_raciones"],
    # Padres y niños: los padres desayunan tras dejar a los niños; a la salida de la tarde
    # se merienda. A mediodía recogen a los niños y comen en casa: sin momento.
    ("padres_ninos", F1): ["desayuno"],
    ("padres_ninos", F4): ["merienda"],
    # Pacientes: muchos análisis son en ayunas, así que desayunan al salir; luego café
    # mientras esperan o acompañan.
    ("pacientes", F1): ["desayuno"],
    ("pacientes", F2): ["almuerzo"],
    ("pacientes", F4): ["merienda"],
    # Deporte y eventos: aperitivo tras el partido de mañana, merienda, cañas, cena y copas
    # después de un evento.
    ("deporte_eventos", F3): ["canas_raciones"],
    ("deporte_eventos", F4): ["merienda"],
    ("deporte_eventos", F5): ["canas_raciones", "cenas"],
    ("deporte_eventos", F6): ["copas"],
}
# Si una celda tiene varios momentos, su gente se reparte a partes iguales entre ellos
# (para no contarla dos veces).
# Momentos que solo existen ciertos días: el menú del día es de lunes a viernes; en
# sábado ese público hace el aperitivo (cañas y raciones).
MOMENTO_SOLO_LABORABLE = {"menu_del_dia": "canas_raciones"}
# Se recomiendan los momentos con al menos este porcentaje de la gente del momento más
# fuerte del día.
MOMENTO_RECOMENDAR = 0.5
# En el «porqué» de un momento no se citan aportes de menos de estas personas.
APORTE_MINIMO = 5

# Huecos de competencia: un tipo de local «falta» si en el radio hay menos de este
# porcentaje de la media del municipio, y «sobra» (saturación) si hay más de
# SATURACION veces la media. Solo se compara si la media del municipio es de al menos
# HUECO_MEDIA_MINIMA locales (con menos, la comparación no dice nada).
HUECO_FALTA = 0.75
HUECO_SATURACION = 1.5
HUECO_MEDIA_MINIMA = 1.0
# Cocinas: solo se usan si en el radio hay al menos COCINAS_MINIMO_LOCALES locales en OSM
# y más de COCINAS_MINIMA_FRACCION de ellos indica su cocina.
COCINAS_MINIMO_LOCALES = 5
COCINAS_MINIMA_FRACCION = 0.5

# ----------------------------------------------------------------- B4. avisos y riesgos
# Competencia alta: más de esta proporción frente a la media del municipio.
RIESGO_COMPETENCIA = 1.5
# Peso de estudiantes (universitarios + padres y niños) en un laborable a partir del
# cual se avisa de los periodos sin clase.
RIESGO_ESTUDIANTES = 0.15
# Calendario escolar: el portal de la Comunidad no publica un conjunto con el calendario
# escolar (búsqueda del 2026-11-10: «calendario escolar», «calendario lectivo»,
# «vacaciones escolares», sin resultados). Se usa el periodo lectivo típico de la
# Comunidad de Madrid. ESTIMACIÓN: las fechas exactas cambian cada curso.
PERIODO_LECTIVO = {
    "padres_ninos": "de principios de septiembre a la segunda quincena de junio; sin clase "
                    "en Navidad (del 22-23 de diciembre al 7-8 de enero), en Semana Santa "
                    "(unos 10 días) ni en julio y agosto",
    "universitarios": "de mediados de septiembre a mayo, con exámenes hasta finales de "
                      "junio o principios de julio; sin clase en Navidad, en Semana Santa "
                      "ni en julio y agosto (el campus queda casi vacío en agosto)",
}
# Confianza de una recomendación a partir de la de sus datos («orientativa» → baja).
CONFIANZA_A_RECOMENDACION = {"alta": "alta", "media": "media", "orientativa": "baja"}
# Cuántas comprobaciones en persona se proponen como máximo y como mínimo.
COMPROBACIONES = (5, 8)
