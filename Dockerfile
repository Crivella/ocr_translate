FROM python:3.10.12-slim-bookworm as intermediate

RUN pip install virtualenv
RUN virtualenv /venv/

RUN mkdir -p /src

COPY ocr_translate /src/ocr_translate
COPY pyproject.toml /src/
COPY README.md /src/
COPY LICENSE.txt /src/

RUN mkdir -p /pip_cache
RUN --mount=type=cache,target=/pip_cache /venv/bin/pip install --cache-dir /pip_cache /src/[mysql,postgres]
# RUN --mount=type=cache,target=/pip_cache /venv/bin/pip install --cache-dir /pip_cache django-ocr_translate[mysql,postgres]==0.6.1
RUN --mount=type=cache,target=/pip_cache /venv/bin/pip install gunicorn --cache-dir /pip_cache

FROM python:3.10.12-slim-bookworm

RUN apt-get update && apt-get install \
    nginx \
    tesseract-ocr \
    -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/app
RUN mkdir -p /models
RUN mkdir -p /data

COPY --from=intermediate /venv /venv


RUN mkdir -p /opt/app/main
RUN mkdir -p /opt/app/static
RUN mkdir -p /opt/app/media

COPY start-server.sh /opt/app/
COPY run_server.py /opt/app/
COPY mysite /opt/app/mysite/
COPY staticfiles /opt/app/static/
COPY media /opt/app/media/

RUN chown -R www-data:www-data /opt/app
RUN chmod +x /opt/app/start-server.sh

COPY nginx.default /etc/nginx/sites-available/default

RUN ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log

ENV \
    UID=1000 \
    GID=1000 \
    LOAD_ON_START="false" \
    AUTOCREATE_LANGUAGES="false" \
    DEVICE="cpu" \
    OCT_GUNICORN_NUM_WORKERS="1" \
    NUM_MAIN_WORKERS="4" \
    NUM_BOX_WORKERS="1" \
    NUM_OCR_WORKERS="1" \
    NUM_TSL_WORKERS="1" \
    DJANGO_DEBUG="true" \
    DJANGO_LOG_LEVEL="INFO" \
    DJANGO_SUPERUSER_USERNAME="" \
    DJANGO_SUPERUSER_PASSWORD="" \
    DATABASE_ENGINE="django.db.backends.sqlite3" \
    DATABASE_NAME="/db_data/db.sqlite3" \
    DATABASE_HOST="" \
    DATABASE_PORT="" \
    DATABASE_USER="" \
    DATABASE_PASSWORD=""

VOLUME /plugin_data
VOLUME /models
VOLUME /db_data

WORKDIR /opt/app

EXPOSE 4000

STOPSIGNAL SIGTERM

CMD ["/opt/app/start-server.sh"]
