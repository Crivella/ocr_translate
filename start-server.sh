#!/usr/bin/env bash
# start-server.sh
export EASYOCR_MODULE_PATH="${TRANSFORMERS_CACHE}/.easyocr"
source /venv/bin/activate
chown -R www-data:www-data /data
if [ ${DATABASE_ENGINE} == 'sqlite3' ]; then
    echo "Make sure database is readable and writable by www-data"
    chown www-data:www-data ${DATABASE_NAME}
fi

# If starting from an uninitialized database, run migrations
if [[ ! `python manage.py inspectdb` ]]; then
    echo "Running database migrations."
    python manage.py migrate
    if [ $? -ne 0 ]; then
        echo "Error: Database migration failed."
        exit 1
    fi
fi
# Create superuser if DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD are set
if [ -n "${DJANGO_SUPERUSER_USERNAME}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD}" ] ; then
    echo "Creating superuser ${DJANGO_SUPERUSER_USERNAME}"
    (LOAD_ON_START="false"; python manage.py createsuperuser --no-input --email a@b.c)
fi

echo "Starting Gunicorn with #${NUM_WEB_WORKERS} workers."
(gunicorn ocr_translate.wsgi --user www-data --bind 0.0.0.0:4010 --workers ${NUM_WEB_WORKERS}) &
echo "Starting nginx."
nginx -g "daemon off;"