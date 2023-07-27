#!/usr/bin/env bash

export DJANGO_SETTINGS_MODULE=mysite.settings

pyinstaller \
    --onefile \
    --icon icon.ico \
    --add-data "ocr_translate/ocr_tsl/languages.json:ocr_translate/ocr_tsl" \
    --add-data "ocr_translate/ocr_tsl/models.json:ocr_translate/ocr_tsl" \
    --add-data "ocr_translate/migrations:ocr_translate" \
    --collect-all torch \
    --collect-all torchvision \
    --collect-all transformers \
    --collect-all unidic_lite \
    --collect-all sacremoses \
    --collect-all sentencepiece \
    --recursive-copy-metadata torch \
    --recursive-copy-metadata torchvision \
    --recursive-copy-metadata transformers \
    --recursive-copy-metadata unidic_lite \
    --recursive-copy-metadata sacremoses \
    --recursive-copy-metadata sentencepiece \
    run_server.py
