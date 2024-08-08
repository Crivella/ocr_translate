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

echo "Make sure /models folder is readable and writable"
chown -R runner:runner /models

# Make sure DB is migrated to the latest version
migrate
echo "Make sure database is readable and writable"
chown -R runner:runner /data
# Create superuser if DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD are set
if [ -n "${DJANGO_SUPERUSER_USERNAME}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD}" ] ; then
    echo "Creating superuser ${DJANGO_SUPERUSER_USERNAME}"
    LOAD_ON_START=false \
    AUTOCREATE_LANGUAGES=false \
    AUTOCREATE_VALIDATED_MODELS=false \
    OCT_DISABLE_PLUGINS=true \
    python manage.py createsuperuser --no-input --email a@b.c
fi

if [ "${AUTOCREATE_LANGUAGES}" == "true" ] || [ "${AUTOCREATE_VALIDATED_MODELS}" == "true" ]; then
    echo "Creating languages"
    python manage.py shell -c 'import ocr_translate.ocr_tsl'
fi
export AUTOCREATE_LANGUAGES="false"
export AUTOCREATE_VALIDATED_MODELS="false"

echo "Starting Gunicorn with #${NUM_WEB_WORKERS} workers."
su runner -c "source /venv/bin/activate && gunicorn mysite.wsgi --user runner --bind 0.0.0.0:4010 --timeout 1200 --workers ${NUM_WEB_WORKERS}" &
echo "Starting nginx."
nginx -g "daemon off;"
