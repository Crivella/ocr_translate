import io

from PIL import Image

from .. import models as m
from .base import import_models
from .ocr import (get_box_model, get_ocr_boxes, get_ocr_model, load_ocr_model,
                  ocr)
from .tsl import get_tsl_model, load_tsl_model, tsl_pipeline

lang_src = 'ja'
lang_dst = 'en'

import logging

logger = logging.getLogger('ocr_tsl')
logger.setLevel(logging.DEBUG)

f = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
h = logging.StreamHandler()
h.setLevel(logging.DEBUG)
h.setFormatter(f)

logger.addHandler(h)

def ocr_tsl_pipeline_lazy(md5) -> list[dict]:
    raise ValueError('Cannot fulfill lazy')

# This is already kinda lazy, but the idea for the lazy version is to
# check if all results are available just with the md5, and if not,
# ask the extension to send the binary to minimize traffic
def ocr_tsl_pipeline_work(img, md5, force=False, options={}) -> list[dict]:
    bbox_model_obj = get_box_model()
    ocr_model_obj = get_ocr_model()
    tsl_model_obj = get_tsl_model()
    
    res = []

    img_obj, _ = m.Image.objects.get_or_create(md5=md5)
    params = {
        'image': img_obj,
        'model': bbox_model_obj,
        'options': {},
    }

    bbox_run = m.OCRBoxRun.objects.filter(**params).first()
    if bbox_run is None or force:
        logger.debug('Running BBox OCR')
        bboxes = get_ocr_boxes(img)
        # Create it here to avoid having a failed entry in DB
        bbox_run = m.OCRBoxRun.objects.create(**params)
        for bbox in bboxes:
            l,b,r,t = bbox
            m.BBox.objects.create(
                l=l,
                b=b,
                r=r,
                t=t,
                image=img_obj,
                from_ocr=bbox_run,
                )
    else:
        logger.debug('Reusing BBox OCR')
    logger.debug(f'BBox OCR result: {len(bbox_run.result.all())} boxes')

    for bbox_obj in bbox_run.result.all():
        logger.debug(str(bbox_obj))
        bbox = bbox_obj.lbrt
        params = {
            'bbox': bbox_obj,
            'model': ocr_model_obj,
            'options': {},
        }
        ocr_run = m.OCRRun.objects.filter(**params).first()
        if ocr_run is None or force:
            logger.debug('Running OCR')
            text = ocr(img, bbox=bbox)
            text_obj, _ = m.Text.objects.get_or_create(
                text=text,
                lang=lang_src,
                )
            ocr_run = m.OCRRun.objects.create(**params)
            ocr_run.result = text_obj
            ocr_run.save()
        else:
            logger.debug('Reusing OCR')
            text_obj = ocr_run.result
            text = ocr_run.result.text

        logger.info(f'{bbox}, {text}')
        params = {
            'options': {},
            'text': text_obj,
            'model': tsl_model_obj,
        }
        tsl_run_obj = m.TranslationRun.objects.filter(**params).first()
        if tsl_run_obj is None or force:
            logger.debug('Running TSL')
            new = tsl_pipeline(text, lang_src, lang_dst)
            text_obj, _ = m.Text.objects.get_or_create(
                text=new,
                # lang=lang_dst,
                )
            tsl_run_obj = m.TranslationRun.objects.create(**params)
            tsl_run_obj.result = text_obj
            tsl_run_obj.save()
        else:
            logger.debug('Reusing TSL')
            new = tsl_run_obj.result.text
        # print(new)
        res.append({
            'ocr': text,
            'tsl': new,
            'box': bbox,
            })
    
    return res

def ocr_tsl_pipeline(bin, md5, force=False, options={}) -> list[dict]:
    bbox_model_obj = get_box_model()
    ocr_model_obj = get_ocr_model()
    tsl_model_obj = get_tsl_model()

    if any([_ is None for _ in [bbox_model_obj, ocr_model_obj, tsl_model_obj]]):
        logger.warning(f'Models not loaded, box:{bbox_model_obj} ocr:{ocr_model_obj} tsl:{tsl_model_obj}')
        return []
    
    if not force:
        try:
            res = ocr_tsl_pipeline_lazy(md5)
        except ValueError:
            img = Image.open(io.BytesIO(bin))
            res = ocr_tsl_pipeline_work(img, md5, options=options)
    else:
        img = Image.open(io.BytesIO(bin))
        res = ocr_tsl_pipeline_work(img, md5, force=force, options=options)

    return res

def init_most_used():
    from django.db.models import Count
    import_models()
    
    ocr = m.OCRModel.objects.annotate(count=Count('runs')).order_by('-count').first()
    tsl = m.TSLModel.objects.annotate(count=Count('runs')).order_by('-count').first()

    if ocr:
        load_ocr_model(ocr.name)
    if tsl:
        load_tsl_model(tsl.name)

import_models()
init_most_used()