import logging
import os

from PIL import Image

from .. import models as m
# from .base import import_models
from .box import box_run, load_box_model
from .lang import lang_dst, lang_src
from .ocr import load_ocr_model, ocr_run
from .tsl import load_tsl_model, tsl_run

logger = logging.getLogger('ocr_tsl')
logger.setLevel(logging.DEBUG)

f = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
h = logging.StreamHandler()
h.setLevel(logging.DEBUG)
h.setFormatter(f)

logger.addHandler(h)

def ocr_tsl_pipeline_lazy(md5: str, options: dict = {}) -> list[dict]:
    """
    Try to lazily generate reponse from md5.
    Should raise a ValueError if the operation is not possible (fails at any step).
    """
    logger.debug(f'LAZY: START {md5}')
    res = []
    try:
        img_obj= m.Image.objects.get(md5=md5)
    except m.Image.DoesNotExist:
        raise ValueError(f'Image with md5 {md5} does not exist')
    bbox_obj_list = box_run(img_obj)
    for bbox_obj in bbox_obj_list:
        text_obj = ocr_run(bbox_obj, lang_src)
        tsl_obj = tsl_run(text_obj, lang_src, lang_dst)

        text = text_obj.text
        new = tsl_obj.text

        res.append({
            'ocr': text,
            'tsl': new,
            'box': bbox_obj.lbrt,
            })
        
    logger.debug(f'LAZY: DONE')
    return res

# This is already kinda lazy, but the idea for the lazy version is to
# check if all results are available just with the md5, and if not,
# ask the extension to send the binary to minimize traffic
def ocr_tsl_pipeline_work(img: Image.Image, md5: str, force: bool = False, options: dict = {}) -> list[dict]:
    """
    Generate response from md5 and binary.
    Will attempt to behave lazily at every step unless force is True.
    """
    logger.debug(f'WORK: START {md5}')
    res = []

    img_obj, _ = m.Image.objects.get_or_create(md5=md5)
    bbox_obj_list = box_run(img_obj, image=img)

    for bbox_obj in bbox_obj_list:
        logger.debug(str(bbox_obj))

        text_obj = ocr_run(bbox_obj, lang_src, image=img, force=force)
        tsl_obj = tsl_run(text_obj, lang_src, lang_dst, force=force)

        text = text_obj.text
        new = tsl_obj.text

        res.append({
            'ocr': text,
            'tsl': new,
            'box': bbox_obj.lbrt,
            })
    
    logger.debug(f'WORK: DONE')
    return res

def init_most_used():
    from django.db.models import Count

    box = m.OCRBoxModel.objects.annotate(count=Count('runs')).order_by('-count').first()
    ocr = m.OCRModel.objects.annotate(count=Count('runs')).order_by('-count').first()
    tsl = m.TSLModel.objects.annotate(count=Count('runs')).order_by('-count').first()

    if box:
        load_box_model(box.name)
    if ocr:
        load_ocr_model(ocr.name)
    if tsl:
        load_tsl_model(tsl.name)

if os.environ.get('LOAD_ON_START', 'false').lower() == 'true':
    init_most_used()