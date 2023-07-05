from pathlib import Path

import numpy as np
from PIL import Image
from transformers import (BertJapaneseTokenizer, VisionEncoderDecoderModel,
                          ViTImageProcessor)

from .base import dev, root

obj_model_id = None
ocr_model = None
ocr_tokenizer = None
ocr_image_processor = None

import logging

from ..models import OCRModel

logger = logging.getLogger('ocr_tsl')

ocr_model_obj = None
bbox_model_obj = None

def load_ocr_model(model_id):
    global ocr_model_obj, ocr_model, ocr_tokenizer, ocr_image_processor, obj_model_id

    if obj_model_id == model_id:
        return

    mid = root / model_id
    logger.debug(f'Loading OCR model: {mid}')
    ocr_model = VisionEncoderDecoderModel.from_pretrained(mid).to(dev)
    ocr_tokenizer = BertJapaneseTokenizer.from_pretrained(mid)
    ocr_image_processor = ViTImageProcessor.from_pretrained(mid)

    ocr_model_obj, _ = OCRModel.objects.get_or_create(name=model_id)
    obj_model_id = model_id

    logger.debug(f'OCR model loaded: {model_id}')
    logger.debug(f'OCR model object: {ocr_model_obj}')

def get_ocr_model():
    return ocr_model_obj

def ocr(img: Image, bbox: tuple[int, int, int, int] = None, *args, **kwargs):
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
