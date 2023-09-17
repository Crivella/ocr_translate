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
"""Functions and piplines to perform Box OCR on an image."""
import logging

from .. import models as m

dev = 'cpu' #pylint: disable=invalid-name

logger = logging.getLogger('ocr.general')

BOX_MODEL_ID = None
BOX_MODEL_OBJ: m.OCRBoxModel = None

def unload_box_model():
    """Remove the current box model from memory."""
    global BOX_MODEL_OBJ, BOX_MODEL_ID

    logger.info(f'Unloading BOX model: {BOX_MODEL_ID}')
    del BOX_MODEL_OBJ
    BOX_MODEL_OBJ = None
    BOX_MODEL_ID = None

def load_box_model(model_id: str):
    """Load a box model into memory."""
    global BOX_MODEL_OBJ, BOX_MODEL_ID

    if BOX_MODEL_ID == model_id:
        return

    if BOX_MODEL_OBJ is not None:
        BOX_MODEL_OBJ.unload()

    logger.info(f'Loading BOX model: {model_id}')
    model = m.OCRBoxModel.from_entrypoint(model_id)
    model.load()

    BOX_MODEL_OBJ = model
    BOX_MODEL_ID = model_id

    logger.debug(f'OCR model loaded: {model_id}')
    logger.debug(f'OCR model object: {BOX_MODEL_OBJ}')

def get_box_model() -> m.OCRBoxModel:
    """Get the current box model."""
    return BOX_MODEL_OBJ
