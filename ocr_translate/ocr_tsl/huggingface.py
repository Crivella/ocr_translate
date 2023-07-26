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
"""Base utility functions to load models and project-wise environment variables."""
import logging
import os
from pathlib import Path

from transformers import (AutoImageProcessor, AutoModel, AutoModelForSeq2SeqLM,
                          AutoTokenizer, VisionEncoderDecoderModel)

logger = logging.getLogger('ocr.general')

root = Path(os.environ.get('TRANSFORMERS_CACHE', '.'))
logger.debug(f'Cache dir: {root}')
dev = os.environ.get('DEVICE', 'cpu')

def load(loader, model_id: str):
    """Use the specified loader to load a transformers specific Class."""
    res = None
    try:
        mid = root / model_id
        logger.debug(f'Attempt loading from store: "{loader}" "{mid}"')
        res = loader.from_pretrained(mid)
    except Exception:
        # Needed to catch some weird exception from transformers
        # eg: huggingface_hub.utils._validators.HFValidationError: Repo id must use alphanumeric chars or
        # '-', '_', '.', '--' and '..' are forbidden, '-' and '.' cannot start or end the name, max length is 96: ...
        logger.debug(f'Attempt loading from cache: "{loader}" "{model_id}" "{root}"')
        res = loader.from_pretrained(model_id, cache_dir=root)
    return res

mapping = {
    'tokenizer': AutoTokenizer,
    'ved_model': VisionEncoderDecoderModel,
    'model': AutoModel,
    'image_processor': AutoImageProcessor,
    'seq2seq': AutoModelForSeq2SeqLM
}

accept_device = ['ved_model', 'seq2seq', 'model']

def load_hugginface_model(model_id: str, request: list[str]) -> list:
    """Load the requested HuggingFace's Classes for the model into the memory of the globally specified device.

    Args:
        model_id (str): The HuggingFace model id to load, or a path to a local model.
        request (list[str]): A list of HuggingFace's Classes to load.

    Raises:
        ValueError: If the model_id is not found or if the requested Class is not supported.

    Returns:
        _type_: A list of the requested Classes.
    """    """"""
    res = {}
    for r in request:
        if r not in mapping:
            raise ValueError(f'Unknown request: {r}')
        cls = load(mapping[r], model_id)
        if cls is None:
            raise ValueError(f'Could not load model: {model_id}')

        if r in accept_device:
            cls = cls.to(dev)

        res[r] = cls

    return res
