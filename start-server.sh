#!/usr/bin/env bash
# start-server.sh

echo "Create group and user with specified UID/GID"
groupadd -g ${GID} runner
useradd -u ${UID} -g ${GID} -s /bin/bash runner

source /venv/bin/activate

function migrate {
    echo "Running database migrations."
    LOAD_ON_START=false AUTOCREATE_LANGUAGES=false AUTOCREATE_VALIDATED_MODELS=false python manage.py migrate
    if [ $? -ne 0 ]; then
        echo "Error: Database migration failed."
        exit 1
    fi
}

export EASYOCR_MODULE_PATH="${TRANSFORMERS_CACHE}/.easyocr"
export HF_TRANSORMERS_CACHE="${TRANSFORMERS_CACHE}"

echo "Make sure /models folder is writable is readable and writable"
chown -R runner:runner /models

if [ ${DATABASE_ENGINE} == 'django.db.backends.sqlite3' ]; then
    if [[ ! -e ${DATABASE_NAME} ]]; then
        migrate
    fi
fi
echo "Make sure database is readable and writable"
chown -R runner:runner /data

# If starting from an uninitialized database, run migrations
if [[ ! `python manage.py inspectdb` ]]; then
    migrate
fi
# Create superuser if DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD are set
if [ -n "${DJANGO_SUPERUSER_USERNAME}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD}" ] ; then
    echo "Creating superuser ${DJANGO_SUPERUSER_USERNAME}"
    (LOAD_ON_START=false AUTOCREATE_LANGUAGES=false AUTOCREATE_VALIDATED_MODELS=false python manage.py createsuperuser --no-input --email a@b.c)
fi

echo "Starting Gunicorn with #${NUM_WEB_WORKERS} workers."
su runner -c "source /venv/bin/activate && gunicorn mysite.wsgi --user runner --bind 0.0.0.0:4010 --workers ${NUM_WEB_WORKERS}" &
echo "Starting nginx."
nginx -g "daemon off;"