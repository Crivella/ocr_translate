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
"""Functions and piplines to perform translation on text."""
import logging

from .. import models as m

logger = logging.getLogger('ocr.general')

TSL_MODEL_ID = None
TSL_MODEL_OBJ: m.TSLModel = None

def unload_tsl_model():
    """Remove the current TSL model from memory."""
    global TSL_MODEL_OBJ, TSL_MODEL_ID

    logger.info(f'Unloading TSL model: {TSL_MODEL_ID}')
    del TSL_MODEL_OBJ
    TSL_MODEL_OBJ = None
    TSL_MODEL_ID = None

def load_tsl_model(model_id):
    """Load a TSL model into memory."""
    global TSL_MODEL_OBJ, TSL_MODEL_ID

    if TSL_MODEL_ID == model_id:
        return

    if TSL_MODEL_OBJ is not None:
        TSL_MODEL_OBJ.unload()

    logger.info(f'Loading TSL model: {model_id}')
    model = m.TSLModel.from_entrypoint(model_id)
    model.load()

    TSL_MODEL_OBJ = model
    TSL_MODEL_ID = model_id

def get_tsl_model() -> m.TSLModel:
    """Get the current TSL model."""
    return TSL_MODEL_OBJ
