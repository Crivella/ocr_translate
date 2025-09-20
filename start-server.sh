#!/usr/bin/env bash
# start-server.sh

echo "Create group and user with specified UID=${UID} GID=${GID}"
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

export TRANSFORMERS_CACHE=${TRANSFORMERS_CACHE:-"/models/huggingface"}
export TRANSFORMERS_OFFLINE=${TRANSFORMERS_OFFLINE:-"0"}
export EASYOCR_MODULE_PATH=${EASYOCR_MODULE_PATH:-"/models/easyocr"}
export TESSERACT_PREFIX=${TESSERACT_PREFIX:-"/models/tesseract"}
export TESSERACT_ALLOW_DOWNLOAD=${TESSERACT_ALLOW_DOWNLOAD:-"true"}
export PADDLEOCR_PREFIX=${PADDLEOCR_PREFIX:-"/models/paddleocr"}
export OCT_DJANGO_PORT=4010
export OCT_BASE_DIR="/plugin_data"
export HF_HOME=${TRANSFORMERS_CACHE}

export COLUMNS=${COLUMNS:-160}

source /venv/bin/activate
su ${USER} /bin/bash -c "python run_server.py"
