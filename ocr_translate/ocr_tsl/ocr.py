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
from typing import Generator, Hashable, Union

import torch
from PIL import Image

from .. import models as m
from ..messaging import Message
from ..queues import ocr_queue as q
from .base import dev, load_hugginface_model
from .tesseract import tesseract_pipeline

logger = logging.getLogger('ocr.general')

OBJ_MODEL_ID: str = None
OCR_MODEL = None
OCR_TOKENIZER = None
OCR_IMAGE_PROCESSOR = None

OCR_MODEL_OBJ: m.OCRModel = None

NO_SPACE_LANGUAGES = [
    'ja', 'zh', 'lo', 'my'
]

def unload_ocr_model():
    """Remove the current OCR model from memory."""
    global OCR_MODEL_OBJ, OCR_MODEL, OCR_TOKENIZER, OCR_IMAGE_PROCESSOR, OBJ_MODEL_ID

    logger.info(f'Unloading OCR model: {OBJ_MODEL_ID}')
    OCR_MODEL = None
    OCR_TOKENIZER = None
    OCR_IMAGE_PROCESSOR = None
    OCR_MODEL_OBJ = None
    OBJ_MODEL_ID = None

    if dev == 'cuda':
        torch.cuda.empty_cache()

def load_ocr_model(model_id: str):
    """Load an OCR model into memory."""
    global OCR_MODEL_OBJ, OCR_MODEL, OCR_TOKENIZER, OCR_IMAGE_PROCESSOR, OBJ_MODEL_ID

    if OBJ_MODEL_ID == model_id:
        return

    # mid = root / model_id
    logger.info(f'Loading OCR model: {model_id}')
    if model_id == 'tesseract':
        pass
    else:
        res = load_hugginface_model(model_id, request=['ved_model', 'tokenizer', 'image_processor'])
        OCR_MODEL = res['ved_model']
        OCR_TOKENIZER = res['tokenizer']
        OCR_IMAGE_PROCESSOR = res['image_processor']

    OCR_MODEL_OBJ, _ = m.OCRModel.objects.get_or_create(name=model_id)
    OBJ_MODEL_ID = model_id

    logger.debug(f'OCR model loaded: {model_id}')
    logger.debug(f'OCR model object: {OCR_MODEL_OBJ}')

def get_ocr_model() -> m.OCRModel:
    """Return the current OCR model."""
    return OCR_MODEL_OBJ

def _ocr(img: Image.Image, lang: str = None, bbox: tuple[int, int, int, int] = None, options: dict = None) -> str:
    """Perform OCR on an image.

    Args:
        img (Image.Image):  A Pillow image on which to perform OCR.
        lang (str, optional): The language to use for OCR. (Not every model will use this)
        bbox (tuple[int, int, int, int], optional): The bounding box of the text on the image in lbrt format.
        options (dict, optional): A dictionary of options to pass to the OCR model.

    Raises:
        TypeError: If img is not a Pillow image.

    Returns:
        str: The text extracted from the image.
    """
    if options is None:
        options = {}
    if not isinstance(img, Image.Image):
        raise TypeError(f'img should be PIL Image, but got {type(img)}')
    img = img.convert('RGB')

    if bbox:
        img = img.crop(bbox)

    if OBJ_MODEL_ID == 'tesseract':
        generated_text = tesseract_pipeline(img, lang)
    else:
        pixel_values = OCR_IMAGE_PROCESSOR(img, return_tensors='pt').pixel_values
        if dev == 'cuda':
            pixel_values = pixel_values.cuda()
        generated_ids = OCR_MODEL.generate(pixel_values)
        generated_text = OCR_TOKENIZER.batch_decode(generated_ids, skip_special_tokens=True)[0]

    return generated_text

def ocr(*args, id_: Hashable, block: bool = True, **kwargs) -> Union[str, Message]:
    """Queue a text OCR pipeline.

    Args:
        id_ (Hashable): A unique identifier for the OCR task.
        block (bool, optional): Whether to block until the task is complete. Defaults to True.

    Returns:
        Union[str, Message]: The text extracted from the image (block=True) or a Message object (block=False).
    """
    msg = q.put(
        id_ = id_,
        msg = {'args': args, 'kwargs': kwargs},
        handler = _ocr,
    )

    if block:
        return msg.response()
    return msg

def ocr_run(
        bbox_obj: m.BBox, lang: m.Language,  image: Image.Image = None, options: m.OptionDict = None,
        force: bool = False, block: bool = True,
        ) -> Generator[Union[Message, m.Text], None, None]:
    """High level function to perform OCR on an image.

    Args:
        bbox_obj (m.BBox): The BBox object from the database.
        lang (m.Language): The Language object from the database.
        image (Image.Image, optional): The image on which to perform OCR. Needed if no previous OCR run exists, or
            force is True.
        options (m.OptionDict, optional): The OptionDict object from the database containing the options for the OCR.
        force (bool, optional): Whether to force the OCR to run again even if a previous run exists. Defaults to False.
        block (bool, optional): Whether to block until the task is complete. Defaults to True.

    Raises:
        ValueError: ValueError is raised if at any step of the pipeline an image is required but not provided.

    Yields:
        Generator[Union[Message, m.Text], None, None]:
            If block is True, yields a Message object for the OCR run first and the resulting Text object second.
            If block is False, yields the resulting Text object.
    """
    options_obj = options
    if options_obj is None:
        options_obj = m.OptionDict.objects.get(options={})
    params = {
        'bbox': bbox_obj,
        'model': OCR_MODEL_OBJ,
        'lang_src': lang,
        'options': options_obj,
    }
    ocr_run_obj = m.OCRRun.objects.filter(**params).first()
    if ocr_run_obj is None or force:
        if image is None:
            raise ValueError('Image is required for OCR')
        logger.info('Running OCR')

        id_ = (bbox_obj.id, OCR_MODEL_OBJ.id, lang.id)
        mlang = getattr(lang, OCR_MODEL_OBJ.language_format or 'iso1')
        opt_dct = options_obj.options
        text = ocr(
            image,
            lang=mlang,
            bbox=bbox_obj.lbrt,
            options=opt_dct,
            id_=id_,
            block=block,
            )
        if not block:
            yield text
            text = text.response()
        if lang.iso1 in NO_SPACE_LANGUAGES:
            text = text.replace(' ', '')
        text_obj, _ = m.Text.objects.get_or_create(
            text=text,
            )
        params['result'] = text_obj
        ocr_run_obj = m.OCRRun.objects.create(**params)
    else:
        if not block:
            # Both branches should have the same number of yields
            yield None
        logger.info(f'Reusing OCR <{ocr_run_obj.id}>')
        text_obj = ocr_run_obj.result
        # text = ocr_run.result.text

    yield text_obj
