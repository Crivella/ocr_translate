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
"""OCRtranslate plugin to allow loading of tesseract models."""

import logging
import os
from pathlib import Path

import requests
from PIL import Image
from pytesseract import Output, image_to_string

from ocr_translate import models as m

logger = logging.getLogger('plugin')

MODEL_URL = 'https://github.com/tesseract-ocr/tessdata_best/raw/main/{}.traineddata'

# root = Path(os.environ.get('TRANSFORMERS_CACHE', '.'))
# DATA_DIR = Path(os.getenv('TESSERACT_PREFIX', root / 'tesseract'))

# DOWNLOAD = os.getenv('TESSERACT_ALLOW_DOWNLOAD', 'false').lower() == 'true'

class TesseractOCRModel(m.OCRModel):
    """OCRtranslate plugin to allow usage of Tesseract models."""
    VERTICAL_LANGS = ['jpn', 'chi_tra', 'chi_sim', 'kor']
    config = False

    class Meta:
        proxy = True

    def __init__(self, *args, **kwargs):
        """Initialize the model."""
        super().__init__(*args, **kwargs)

        root = Path(os.environ.get('TRANSFORMERS_CACHE', '.'))
        self.data_dir = Path(os.getenv('TESSERACT_PREFIX', root / 'tesseract'))
        self.download = os.getenv('TESSERACT_ALLOW_DOWNLOAD', 'false').lower() == 'true'

    def download_model(self, lang: str):
        """Download a tesseract model for a given language.

        Args:
            lang (str): A language code for tesseract.

        Raises:
            ValueError: If the model could not be downloaded.
        """
        if not self.download:
            raise ValueError('TESSERACT_ALLOW_DOWNLOAD is false. Downloading models is not allowed')
        self.create_config()

        logger.info(f'Downloading tesseract model for language {lang}')
        dst = self.data_dir / f'{lang}.traineddata'
        if dst.exists():
            return
        res = requests.get(MODEL_URL.format(lang), timeout=5)
        if res.status_code != 200:
            raise ValueError(f'Could not download model for language {lang}')

        with open(self.data_dir / f'{lang}.traineddata', 'wb') as f:
            f.write(res.content)

        if lang in self.VERTICAL_LANGS:
            self.download_model(lang + '_vert')

    def load(self):
        """Mock load, not needed for tesseract. Every call done via CLI."""

    def unload(self) -> None:
        """Mock unload, not needed for tesseract. Every call done via CLI."""

    def create_config(self):
        """Create a tesseract config file. Run only once"""
        if self.config:
            return
        self.config = True

        logger.info('Creating tesseract tsv config')
        cfg = self.data_dir / 'configs'
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
    def _ocr(
            self,
            img: Image.Image, lang: str = None, options: dict = None
            ) -> str:
        """Run tesseract on an image.

        Args:
            img (Image.Image): An image to run tesseract on.
            lang (str): A language code for tesseract.
            favor_vertical (bool, optional): Wether to favor vertical or horizontal configuration for languages that
                can be written vertically. Defaults to True.

        Returns:
            str: The text extracted from the image.
        """
        if options is None:
            options = {}

        self.create_config()
        if not (self.data_dir / f'{lang}.traineddata').exists():
            self.download_model(lang)
        logger.info(f'Running tesseract for language {lang}')

        favor_vertical = options.get('favor_vertical', True)

        psm = 6
        if lang in self.VERTICAL_LANGS:
            exp = 1 if favor_vertical else -1
            if img.height * 1.5**exp > img.width:
                psm = 5

        # Using image_to_string will atleast preserve spaces
        res = image_to_string(
            img,
            lang=lang,
            config=f'--tessdata-dir {self.data_dir.as_posix()} --psm {psm}',
            output_type=Output.DICT
            )

        return res['text']
