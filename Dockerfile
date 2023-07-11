FROM python:3.10.12-slim-bookworm

# libpq-dev gcc needed for psycopg2 or psycopg (required for postgresql engine)
RUN apt-get update && apt-get install \
    nginx \
    gcc \
    libpq-dev \
    -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/app
RUN mkdir -p /opt/app/pip_cache
RUN mkdir -p /models
RUN mkdir -p /data

COPY requirements.txt /opt/app/
COPY requirements-torch.txt /opt/app/
# !!! Usefull for local development but should be removed for production !!!
COPY .pip_cache2 /pip_cache/

RUN mkdir -p /pip_cache
# torch should be before requirements.txt otherwise tranformers will intall it on its own
# and torch>=2.x defaults to cuda and install all the nvidia stuff
RUN pip install -r /opt/app/requirements-torch.txt --cache-dir /pip_cache
RUN pip install -r /opt/app/requirements.txt --cache-dir /pip_cache
RUN pip install gunicorn --cache-dir /pip_cache

RUN rm -rf /pip_cache
RUN apt remove gcc -y
RUN apt autoremove -y

RUN mkdir -p /opt/app/main
RUN mkdir -p /opt/app/static
RUN mkdir -p /opt/app/media

COPY start-server.sh /opt/app/
COPY manage.py /opt/app/
COPY base /opt/app/base/
COPY ocr_translate /opt/app/ocr_translate/
COPY staticfiles /opt/app/static/
COPY media /opt/app/media/

RUN chown -R www-data:www-data /opt/app
RUN chmod +x /opt/app/start-server.sh

COPY nginx.default /etc/nginx/sites-available/default

RUN ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log


ENV \
    LOAD_ON_START="true" \
    AUTOCREATE_LANGUAGES="true" \
    AUTOCREATE_VALIDATED_MODELS="true" \
    TRANSFORMERS_CACHE="/models" \
    TRANSFORMERS_OFFLINE="0" \
    DEVICE="cpu" \
    NUM_WEB_WORKERS="1" \
    NUM_MAIN_WORKERS="4" \
    NUM_BOX_WORKERS="1" \
    NUM_OCR_WORKERS="1" \
    NUM_TSL_WORKERS="1" \
    DJANGO_SUPERUSER_USERNAME="admin" \
    DJANGO_SUPERUSER_PASSWORD="password" \
    DATABASE_ENGINE="django.db.backends.sqlite3" \
    DATABASE_NAME="/data/db.sqlite3" \
    DATABASE_HOST="" \
    DATABASE_PORT="" \
    DATABASE_USER="" \
    DATABASE_PASSWORD=""

VOLUME [ "/models" ]
VOLUME [ "/data" ]

WORKDIR /opt/app

EXPOSE 4000

STOPSIGNAL SIGTERM

CMD ["/opt/app/start-server.sh"]
