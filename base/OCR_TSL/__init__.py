import io

from PIL import Image

from .. import models as m
from .ocr import bbox_model_obj, get_ocr_boxes, ocr, ocr_model_obj
from .tsl import tsl_model_obj, tsl_pipeline

lang_src = 'ja'
lang_dst = 'en'

import logging

logger = logging.getLogger('ocr_tsl')
logger.setLevel(logging.WARNING)

f = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
h = logging.StreamHandler()
h.setLevel(logging.WARNING)
h.setFormatter(f)

logger.addHandler(h)

def ocr_tsl_pipeline_lazy(md5):
    raise ValueError('Cannot fulfill lazy')

# This is already kinda lazy, but the idea for the lazy version is to
# check if all results are available just with the md5, and if not,
# ask the extension to send the binary to minimize traffic
def ocr_tsl_pipeline_work(img, md5):
    res = []

    img_obj, _ = m.Image.objects.get_or_create(md5=md5)
    bbox_run, todo = m.OCRBoxRun.objects.get_or_create(
        options={},
        image=img_obj,
        model=bbox_model_obj
        )
    if todo:
        logger.debug('Running BBox OCR')
        bboxes = get_ocr_boxes(img)
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

    for bbox_obj in bbox_run.result.all():
        logger.debug(bbox_obj)
        bbox = bbox_obj.lbrt
        ocr_run, todo = m.OCRRun.objects.get_or_create(
            options={},
            bbox=bbox_obj,
            model=ocr_model_obj,
            )
        if todo or ocr_run.result is None:
            logger.debug('Running OCR')
            text = ocr(img, bbox=bbox)
            text_obj, _ = m.Text.objects.get_or_create(
                text=text,
                lang=lang_src,
                )
            ocr_run.result = text_obj
            ocr_run.save()
        else:
            logger.debug('Reusing OCR')
            text_obj = ocr_run.result
            text = ocr_run.result.text

        logger.info(bbox, text)
        tsl_run_obj, todo = m.TranslationRun.objects.get_or_create(
            options={},
            text=text_obj,
            model=tsl_model_obj,
            )
        
        if todo or tsl_run_obj.result is None:
            logger.debug('Running TSL')
            new = tsl_pipeline(text, lang_src, lang_dst)
            text_obj, _ = m.Text.objects.get_or_create(
                text=new,
                lang=lang_dst,
                )
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

def ocr_tsl_pipeline(bin, md5):
    try:
        res = ocr_tsl_pipeline_lazy(md5)
    except ValueError:
        img = Image.open(io.BytesIO(bin))
        res = ocr_tsl_pipeline_work(img, md5)

    return res
