from pathlib import Path
from typing import Union

from PIL import Image
from transformers import (BertJapaneseTokenizer, VisionEncoderDecoderModel,
                          ViTImageProcessor)

from .. import models as m
from .base import dev, load_model

obj_model_id = None
ocr_model = None
ocr_tokenizer = None
ocr_image_processor = None

import logging

logger = logging.getLogger('ocr_tsl')

ocr_model_obj = None
bbox_model_obj = None

def load_ocr_model(model_id):
    global ocr_model_obj, ocr_model, ocr_tokenizer, ocr_image_processor, obj_model_id

    if obj_model_id == model_id:
        return

    # mid = root / model_id
    logger.debug(f'Loading OCR model: {model_id}')
    res = load_model(model_id, request=['ved_model', 'tokenizer', 'image_processor'])
    ocr_model = res['ved_model']
    ocr_tokenizer = res['tokenizer']
    ocr_image_processor = res['image_processor']
    # ocr_model = VisionEncoderDecoderModel.from_pretrained(model_id).to(dev)
    # ocr_tokenizer = BertJapaneseTokenizer.from_pretrained(model_id)
    # ocr_image_processor = ViTImageProcessor.from_pretrained(model_id)

    ocr_model_obj, _ = m.OCRModel.objects.get_or_create(name=model_id)
    obj_model_id = model_id

    logger.debug(f'OCR model loaded: {model_id}')
    logger.debug(f'OCR model object: {ocr_model_obj}')

def get_ocr_model():
    return ocr_model_obj

def ocr(img: Image.Image, bbox: tuple[int, int, int, int] = None, *args, **kwargs) -> str:
    if isinstance(img, (str, Path)):
        img = Image.open(img)
    if isinstance(img, Image.Image):
        img = img.convert("RGB")
    else:
        raise TypeError(f"img should be PIL Image or path to file, but got {type(img)}")
    
    if bbox:
        img = img.crop(bbox)
    
    pixel_values = ocr_image_processor(img, return_tensors="pt").pixel_values
    if dev == 'cuda':
        pixel_values = pixel_values.cuda()
    generated_ids = ocr_model.generate(pixel_values, *args, **kwargs)
    generated_text = ocr_tokenizer.batch_decode(generated_ids, skip_special_tokens=True)

    return generated_text[0].replace(' ', '')

def ocr_run(bbox_obj: m.BBox, image: Union[Image.Image, None] = None, force: bool = False, options: dict = {}) -> m.Text:
        global ocr_model_obj
        params = {
            'bbox': bbox_obj,
            'model': ocr_model_obj,
            'options': options,
        }
        ocr_run = m.OCRRun.objects.filter(**params).first()
        if ocr_run is None or force:
            if image is None:
                raise ValueError('Image is required for OCR')
            logger.debug('Running OCR')
            text = ocr(image, bbox=bbox_obj.lbrt)
            text_obj, _ = m.Text.objects.get_or_create(
                text=text,
                # lang=lang_src,
                )
            ocr_run = m.OCRRun.objects.create(**params)
            ocr_run.result = text_obj
            ocr_run.save()
        else:
            logger.debug('Reusing OCR')
            text_obj = ocr_run.result
            # text = ocr_run.result.text

        return text_obj
