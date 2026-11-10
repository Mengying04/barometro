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
    "pacientes": "Pacientes",
    "trabajadores": "Trabajadores",
    "deporte_eventos": "Deporte y eventos",
    "viajeros": "Viajeros",
    "vecinos": "Vecinos",
}

# Confianza de cada tipo según la calidad del dato de partida.
CONFIANZA = {
    "viajeros": ("alta", "horarios reales del transporte público (GTFS del CRTM)"),
    "padres_ninos": ("media", "ubicación real de los centros; alumnos repartidos desde "
                              "totales por municipio y horario típico"),
    "pacientes": ("media", "ubicación real de los centros sanitarios y horario típico"),
    "trabajadores": ("media", "ubicación real de centros de trabajo grandes (registro de "
                              "desfibriladores) y horario típico"),
    "deporte_eventos": ("media", "ubicación real de instalaciones y recintos (registro de "
                                 "desfibriladores) y horario típico"),
    "vecinos": ("orientativa", "población por sección censal repartida por superficie y "
                               "costumbres generales de salida a la calle"),
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
# de esta distancia: se trata como un centro que falta (universidades, academias…).
DEA_EDUCATIVO_DISTANCIA_M = 120
DEA_EDUCATIVO_PESO = 1000      # usuarios al día (campus o centro grande). ESTIMACIÓN.
DEA_EDUCATIVO_PERFIL = "universidad"

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
# Personas que suben o bajan en una parada por cada vehículo que pasa (media del día).
# ESTIMACIÓN de orden de magnitud: viajeros anuales de cada red (memorias del CRTM y de
# los operadores, del orden de 600-700 millones en Metro, 400-450 millones en EMT, unos
# 200 millones en interurbanos y en Cercanías) divididos entre el número de paradas y
# los pasos de vehículos por parada y día. Ejemplo para Metro: ~700 M / 365 / ~300
# estaciones ≈ 6.000 entradas al día por estación; con ~300 trenes al día y las salidas
# del mismo orden que las entradas, ~40 personas por tren y estación.
VIAJEROS_POR_PASO = {
    "metro": 40,
    "cercanias": 60,      # menos trenes que Metro, más viajeros por tren
    "metro_ligero": 10,
    "emt": 5,
    "interurbanos": 4,
    "urbanos": 3,
}

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
