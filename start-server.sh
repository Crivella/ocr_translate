#!/usr/bin/env bash
# start-server.sh

echo "Create group and user with specified UID/GID"
USER=runner
if [ ! -z ${OCT_GUNICORN_USER} ]; then
    USER=${OCT_GUNICORN_USER}
fi
groupadd -g ${GID} ${USER}
useradd -u ${UID} -g ${GID} -s /bin/bash runner

mkdir -p /plugin_data
mkdir -p /models
mkdir -p /db_data

chown -R ${USER}:${USER} /plugin_data
chown -R ${USER}:${USER} /models
chown -R ${USER}:${USER} /db_data

echo "Starting nginx."
nginx

su ${USER}

export OCT_DJANGO_PORT=4010
export OCT_BASE_DIR="/plugin_data"
export TRANSFORMERS_CACHE="/models/huggingface"
export TRANSFORMERS_OFFLINE="0"
export EASYOCR_MODULE_PATH="/models/easyocr"
export TESSERACT_PREFIX="/models/tesseract"
export TESSERACT_ALLOW_DOWNLOAD="true"
export PADDLEOCR_PREFIX="/models/paddleocr"

source /venv/bin/activate
python run_server.py
