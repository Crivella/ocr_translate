from pathlib import Path
from typing import Union

from PIL import Image
from transformers import (BertJapaneseTokenizer, VisionEncoderDecoderModel,
                          ViTImageProcessor)

from .. import models as m
from ..queues import ocr_queue as q
from .base import dev, load_hugginface_model
from .tesseract import tesseract_pipeline

obj_model_id: str = None
ocr_model = None
ocr_tokenizer = None
ocr_image_processor = None

import logging

logger = logging.getLogger('ocr.general')

ocr_model_obj: m.OCRModel = None

def unload_ocr_model():
    global ocr_model_obj, ocr_model, ocr_tokenizer, ocr_image_processor, obj_model_id

    logger.info(f'Unloading OCR model: {obj_model_id}')
    ocr_model = None
    ocr_tokenizer = None
    ocr_image_processor = None
    ocr_model_obj = None
    obj_model_id = None

    if dev == 'cuda':
        import torch
        torch.cuda.empty_cache()

def load_ocr_model(model_id: str):
    global ocr_model_obj, ocr_model, ocr_tokenizer, ocr_image_processor, obj_model_id

    if obj_model_id == model_id:
        return

    # mid = root / model_id
    logger.info(f'Loading OCR model: {model_id}')
    if model_id == 'tesseract':
        pass
    else:
        res = load_hugginface_model(model_id, request=['ved_model', 'tokenizer', 'image_processor'])
        ocr_model = res['ved_model']
        ocr_tokenizer = res['tokenizer']
        ocr_image_processor = res['image_processor']

    ocr_model_obj, _ = m.OCRModel.objects.get_or_create(name=model_id)
    obj_model_id = model_id

    logger.debug(f'OCR model loaded: {model_id}')
    logger.debug(f'OCR model object: {ocr_model_obj}')

def get_ocr_model() -> m.OCRModel:
    return ocr_model_obj

def _ocr(img: Image.Image, lang: str = None, bbox: tuple[int, int, int, int] = None, *args, **kwargs) -> str:
    if not isinstance(img, Image.Image):
        raise TypeError(f"img should be PIL Image, but got {type(img)}")
    img = img.convert("RGB")
    
    if bbox:
        img = img.crop(bbox)

    if obj_model_id == 'tesseract':
        generated_text = tesseract_pipeline(img, lang)
    else:
        pixel_values = ocr_image_processor(img, return_tensors="pt").pixel_values
        if dev == 'cuda':
            pixel_values = pixel_values.cuda()
        generated_ids = ocr_model.generate(pixel_values, *args, **kwargs)
        generated_text = ocr_tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]


    # This might be specific only to kha-white model? (Having space between each char)
    # Also besides oriental languages + more? other do need spaces
    # Need to work on this it this has to be more general
    res = generated_text.replace(' ', '')

    return res

def ocr(*args, id, **kwargs) -> str:
    msg = q.put(
        id = id,
        msg = {'args': args, 'kwargs': kwargs},
        handler = _ocr,
    )

    return msg.response()

def ocr_run(bbox_obj: m.BBox, lang: m.Language,  image: Union[Image.Image, None] = None, force: bool = False, options: dict = {}) -> m.Text:
        global ocr_model_obj
        params = {
            'bbox': bbox_obj,
            'model': ocr_model_obj,
            'lang_src': lang,
            'options': options,
        }
        ocr_run = m.OCRRun.objects.filter(**params).first()
        if ocr_run is None or force:
            if image is None:
                raise ValueError('Image is required for OCR')
            logger.info('Running OCR')

            id = (bbox_obj.id, ocr_model_obj.id, lang.id)
            mlang = getattr(lang, ocr_model_obj.language_format or 'iso1')
            text = ocr(image, lang=mlang, bbox=bbox_obj.lbrt, id=id)
            text_obj, _ = m.Text.objects.get_or_create(
                text=text,
                )
            params['result'] = text_obj
            ocr_run = m.OCRRun.objects.create(**params)
        else:
            logger.info('Reusing OCR')
            text_obj = ocr_run.result
            # text = ocr_run.result.text

        return text_obj
