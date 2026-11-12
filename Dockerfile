# BARómetro: imagen para arrancar la aplicación de Streamlit con los datos procesados que
# trae el repositorio. No descarga datos, no necesita secretos y no se ejecuta como root.
#
#   docker build -t barometro .
#   docker run --rm -p 8501:8501 barometro        # y abrir http://localhost:8501

# Imagen oficial de Python, fijada a una versión concreta (la misma 3.12 del despliegue).
FROM python:3.12.16-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Usuario sin privilegios, con su carpeta (Streamlit guarda ahí su configuración).
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin barometro
WORKDIR /app

# Primero las dependencias: esta capa solo se rehace si cambia requirements.txt.
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

# Solo lo que la aplicación necesita para funcionar (ver también .dockerignore).
COPY .streamlit/config.toml .streamlit/config.toml
COPY app app
COPY src src
COPY datos/LICENCIAS.md datos/LICENCIAS.md
COPY datos/procesados datos/procesados
COPY docs/fuentes.md docs/fuentes.md
COPY LICENSE README.md ./

# Lectura para todos: en algunas carpetas de trabajo hay ficheros que solo puede leer su
# dueña, y el usuario sin privilegios no podría abrirlos.
RUN chmod -R a+rX /app

USER barometro
EXPOSE 8501

# La aplicación responde en /_stcore/health cuando está lista.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=4)"]

CMD ["streamlit", "run", "app/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
