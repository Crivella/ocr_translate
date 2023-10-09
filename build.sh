#!/usr/bin/env bash

export DJANGO_SETTINGS_MODULE=mysite.settings

pyinstaller \
    --onedir \
    --name run_server-gpu \
    --icon icon.ico \
    --add-data "ocr_translate/ocr_tsl/languages.json:ocr_translate/ocr_tsl" \
    --add-data "ocr_translate/dictionaries/*:ocr_translate/dictionaries" \
    --collect-all torch \
    --collect-all torchvision \
    --collect-all transformers \
    --collect-all unidic_lite \
    --collect-all sacremoses \
    --collect-all sentencepiece \
    --collect-all ocr_translate-hugging_face \
    --collect-all ocr_translate-easyocr \
    --collect-all ocr_translate-tesseract \
    --recursive-copy-metadata torch \
    --recursive-copy-metadata torchvision \
    --recursive-copy-metadata transformers \
    --recursive-copy-metadata unidic_lite \
    --recursive-copy-metadata sacremoses \
    --recursive-copy-metadata sentencepiece \
    --recursive-copy-metadat ocr_translate-hugging_face \
    --recursive-copy-metadat ocr_translate-easyocr \
    --recursive-copy-metadat ocr_translate-tesseract run_server.py
