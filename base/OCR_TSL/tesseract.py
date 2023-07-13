import logging
import os
from pathlib import Path

import requests
from PIL import Image
from pytesseract import Output, image_to_data

from .base import root

logger = logging.getLogger('ocr.general')

model_url = 'https://github.com/tesseract-ocr/tessdata_best/raw/main/{}.traineddata'

data_dir = Path(os.getenv('TESSERACT_PREFIX', root / 'tesseract'))
data_dir.mkdir(exist_ok=True)

vertical_langs = ['jpn', 'chi_tra', 'chi_sim', 'kor']

download = os.getenv('TESSERACT_ALLOW_DOWNLOAD', 'false').lower() == 'true'

def download_model(lang: str):
    if not download:
        raise ValueError('Downloading models is not allowed')
    
    logger.info(f'Downloading tesseract model for language {lang}')
    dst = data_dir / f'{lang}.traineddata'
    if dst.exists():
        return
    res = requests.get(model_url.format(lang))
    if res.status_code != 200:
        raise ValueError(f'Could not download model for language {lang}')
    
    with open(data_dir / f'{lang}.traineddata', 'wb') as f:
        f.write(res.content)

    if lang in vertical_langs:
        download_model(lang + '_vert')

def create_config():
    logger.info('Creating tesseract tsv config')
    cfg = data_dir / 'configs'
    cfg.mkdir(exist_ok=True)

    dst = cfg / 'tsv'
    if dst.exists():
        return
    with dst.open('w') as f:
        f.write('tessedit_create_tsv 1')



def tesseract_pipeline(img: Image.Image, lang: str, conf_thr: int = 15, favor_vertical: bool = True) -> str:
    create_config()
    if not (data_dir / f'{lang}.traineddata').exists():
        download_model(lang)
    logger.info(f'Running tesseract for language {lang}')

    psm = 6
    if lang in vertical_langs:
        e = 1 if favor_vertical else -1
        if img.height * 1.5**e > img.width:
            psm = 5

    res = image_to_data(
        img, 
        lang=lang, 
        config=f'--tessdata-dir {data_dir.as_posix()} --psm {psm}', 
        output_type=Output.DICT
        )
    
    return ''.join([t for t,c in zip(res['text'], res['conf']) if int(c) > conf_thr])