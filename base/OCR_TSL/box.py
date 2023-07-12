from typing import Union

import easyocr
import numpy as np
from PIL import Image

from .base import dev, load_model

reader = None

import logging

from .. import models as m
from ..queues import box_queue as q

logger = logging.getLogger('ocr.general')

box_model_id = None
bbox_model_obj = None

def unload_box_model():
    global bbox_model_obj, reader, box_model_id

    logger.info(f'Unloading BOX model: {box_model_id}')
    if box_model_id == 'easyocr':
        pass
    reader = None
    bbox_model_obj = None
    box_model_id = None

    if dev == 'cuda':
        import torch
        torch.cuda.empty_cache()


def load_box_model(model_id: str):
    global bbox_model_obj, reader, box_model_id

    if box_model_id == model_id:
        return

    logger.info(f'Loading BOX model: {model_id}')
    if model_id == 'easyocr':
        reader = easyocr.Reader([], gpu=(dev == "cuda"), recognizer=False)
        bbox_model_obj, _ = m.OCRBoxModel.objects.get_or_create(name=model_id)
        box_model_id = model_id
    else:
        raise NotImplementedError
    
    logger.debug(f'OCR model loaded: {model_id}')
    logger.debug(f'OCR model object: {bbox_model_obj}')

def get_box_model() -> m.OCRBoxModel:
    return bbox_model_obj

def intersections(bboxes, margin=5):
    res = []

    for i,(l1,r1,b1,t1) in enumerate(bboxes):
        l1 -= margin
        r1 += margin
        b1 -= margin
        t1 += margin

        for j,(l2,r2,b2,t2) in enumerate(bboxes):
            if i == j:
                continue

            if l1 >= r2 or r1 <= l2 or b1 >= t2 or t1 <= b2:
                continue

            for ptr in res:
                if i in ptr or j in ptr:
                    break
            else:
                ptr = set()
                res.append(ptr)

            ptr.add(i)
            ptr.add(j)

    return res

def merge_bboxes(bboxes):
    res = []
    bboxes = np.array(bboxes)
    inters = intersections(bboxes)

    lst = list(range(len(bboxes)))

    torm = set()
    for app in inters:
        app = list(app)
        data = bboxes[app].reshape(-1,4)
        l = data[:,0].min()
        r = data[:,1].max()
        b = data[:,2].min()
        t = data[:,3].max()
        
        res.append([l,b,r,t])

        torm = torm.union(app)

    for i in lst:
        if i in torm:
            continue
        l,r,b,t = bboxes[i]
        res.append([l,b,r,t])
    
    return res

def _box_pipeline(image):
    # reader.recognize(image)
    if box_model_id == 'easyocr':
        image = image.convert('RGB')
        results = reader.detect(np.array(image))

        # Axis rectangles
        bboxes = results[0][0]

        # Free (NOT IMPLEMENTED)
        # ...

        bboxes = merge_bboxes(bboxes)
    else:
        raise NotImplementedError

    return bboxes

def box_pipeline(image, md5):
    msg = q.put(
        id = md5,
        msg = {'args': (image,)},
        handler = _box_pipeline,
    )

    return msg.response()

def box_run(img_obj: m.Image, lang: m.Language, image: Union[Image.Image, None] = None, force: bool = False, options: dict = {}) -> list[m.BBox]:
    params = {
        'image': img_obj,
        'model': bbox_model_obj,
        'options': options,
        'lang_src': lang,
    }

    bbox_run = m.OCRBoxRun.objects.filter(**params).first()
    if bbox_run is None or force:
        if image is None:
            raise ValueError('Image is required for BBox OCR')
        logger.info('Running BBox OCR')
        bboxes = box_pipeline(image, img_obj.md5)
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
        logger.info('Reusing BBox OCR')
    logger.info(f'BBox OCR result: {len(bbox_run.result.all())} boxes')

    return list(bbox_run.result.all())

