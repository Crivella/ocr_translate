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
"""Functions and piplines to perform OCR on an image."""
import logging

from .. import models as m

logger = logging.getLogger('ocr.general')

OBJ_MODEL_ID: str = None
OCR_MODEL_OBJ: m.OCRModel = None

def unload_ocr_model():
    """Remove the current OCR model from memory."""
    global OCR_MODEL_OBJ, OBJ_MODEL_ID

    logger.info(f'Unloading OCR model: {OBJ_MODEL_ID}')
    del OCR_MODEL_OBJ
    OCR_MODEL_OBJ = None
    OBJ_MODEL_ID = None

def load_ocr_model(model_id: str):
    """Load an OCR model into memory."""
    global OCR_MODEL_OBJ, OBJ_MODEL_ID

    if OBJ_MODEL_ID == model_id:
        return

    if OCR_MODEL_OBJ is not None:
        OCR_MODEL_OBJ.unload()

    logger.info(f'Loading OCR model: {model_id}')
    model = m.OCRModel.from_entrypoint(model_id)
    model.load()

    OCR_MODEL_OBJ = model
    OBJ_MODEL_ID = model_id

    logger.debug(f'OCR model loaded: {model_id}')
    logger.debug(f'OCR model object: {OCR_MODEL_OBJ}')

def get_ocr_model() -> m.OCRModel:
    """Return the current OCR model."""
    return OCR_MODEL_OBJ
