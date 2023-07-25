###################################################################################
# ocr_translate - a django app to perform OCR and translation of images.          #
# Copyright (C) 2023-present Davide Grassano                                      #
#                                                                                 #
# This program is free software: you can redistribute it and/or modify            #
# it under the terms of the GNU General Public License as published by            #
# the Free Software Foundation, either version 3 of the License.                  #
#                                                                                 #
# This program is distributed in the hope that it will be useful,                 #
# but WITHOUT ANY WARRANTY; without even the implied warranty of                  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                   #
# GNU General Public License for more details.                                    #
#                                                                                 #
# You should have received a copy of the GNU General Public License               #
# along with this program.  If not, see {http://www.gnu.org/licenses/}.           #
#                                                                                 #
# Home: https://github.com/Crivella/ocr_translate                                 #
###################################################################################
"""Functions and piplines to perform OCR on images using tesseract."""
import logging
import os
from pathlib import Path

import requests
from PIL import Image
from pytesseract import Output, image_to_string

from .base import root

logger = logging.getLogger('ocr.general')

MODEL_URL = 'https://github.com/tesseract-ocr/tessdata_best/raw/main/{}.traineddata'

DATA_DIR = Path(os.getenv('TESSERACT_PREFIX', root / 'tesseract'))

VERTICAL_LANGS = ['jpn', 'chi_tra', 'chi_sim', 'kor']

DOWNLOAD = os.getenv('TESSERACT_ALLOW_DOWNLOAD', 'false').lower() == 'true'
CONFIG = False

def download_model(lang: str):
    """Download a tesseract model for a given language.

    Args:
        lang (str): A language code for tesseract.

    Raises:
        ValueError: If the model could not be downloaded.
    """
    if not DOWNLOAD:
        raise ValueError('Downloading models is not allowed')
    create_config()

    logger.info(f'Downloading tesseract model for language {lang}')
    dst = DATA_DIR / f'{lang}.traineddata'
    if dst.exists():
        return
    res = requests.get(MODEL_URL.format(lang), timeout=5)
    if res.status_code != 200:
        raise ValueError(f'Could not download model for language {lang}')

    with open(DATA_DIR / f'{lang}.traineddata', 'wb') as f:
        f.write(res.content)

    if lang in VERTICAL_LANGS:
        download_model(lang + '_vert')

def create_config():
    """Create a tesseract config file. Run only once"""
    global CONFIG
    if CONFIG:
        return
    CONFIG = True

    logger.info('Creating tesseract tsv config')
    cfg = DATA_DIR / 'configs'
    cfg.mkdir(exist_ok=True, parents=True)

    dst = cfg / 'tsv'
    if dst.exists():
        return
    with dst.open('w') as f:
        f.write('tessedit_create_tsv 1')

# Page segmentation modes:
#   0    Orientation and script detection (OSD) only.
#   1    Automatic page segmentation with OSD.
#   2    Automatic page segmentation, but no OSD, or OCR.
#   3    Fully automatic page segmentation, but no OSD. (Default)
#   4    Assume a single column of text of variable sizes.
#   5    Assume a single uniform block of vertically aligned text.
#   6    Assume a single uniform block of text.
#   7    Treat the image as a single text line.
#   8    Treat the image as a single word.
#   9    Treat the image as a single word in a circle.
#  10    Treat the image as a single character.
#  11    Sparse text. Find as much text as possible in no particular order.
#  12    Sparse text with OSD.
#  13    Raw line. Treat the image as a single text line,
#        bypassing hacks that are Tesseract-specific.
def tesseract_pipeline(img: Image.Image, lang: str, favor_vertical: bool = True) -> str:
    """Run tesseract on an image.

    Args:
        img (Image.Image): An image to run tesseract on.
        lang (str): A language code for tesseract.
        favor_vertical (bool, optional): Wether to favor vertical or horizontal configuration for languages that
            can be written vertically. Defaults to True.

    Returns:
        str: The text extracted from the image.
    """    """"""
    create_config()
    if not (DATA_DIR / f'{lang}.traineddata').exists():
        download_model(lang)
    logger.info(f'Running tesseract for language {lang}')

    psm = 6
    if lang in VERTICAL_LANGS:
        exp = 1 if favor_vertical else -1
        if img.height * 1.5**exp > img.width:
            psm = 5

    # Using image_to_string will atleast preserve spaces
    res = image_to_string(
        img,
        lang=lang,
        config=f'--tessdata-dir {DATA_DIR.as_posix()} --psm {psm}',
        output_type=Output.DICT
        )

    return res['text']
