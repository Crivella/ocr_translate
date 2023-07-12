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

def load_box_model(model_id):
    global bbox_model_obj, reader, box_model_id

    if box_model_id == model_id:
        return

    if model_id == 'easyocr':
        logger.info('Loading easyocr')
        reader = easyocr.Reader(['ja'], gpu=(dev == "cuda"))
        bbox_model_obj, _ = m.OCRBoxModel.objects.get_or_create(name='easyocr')
        box_model_id = model_id
        return

    raise NotImplementedError

def get_box_model():
    return bbox_model_obj

def bbox_to_lbrt(bbox):
    l = bbox[0][0]
    b = bbox[0][1]
    r = bbox[2][0]
    t = bbox[2][1]

    return l,b,r,t

def intersections(bboxes, margin=5):
    res = []

    for i,bb1 in enumerate(bboxes):
        b1 = bb1[0][1]-margin
        t1 = bb1[2][1]+margin
        l1 = bb1[0][0]-margin
        r1 = bb1[2][0]+margin
        for j,bb2 in enumerate(bboxes):
            if i == j:
                continue
            b2 = bb2[0][1]
            t2 = bb2[2][1]
            l2 = bb2[0][0]
            r2 = bb2[2][0]

            # if b1 < t2 and t1 > b2 and l1 < r2 and r1 > l2:

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
        data = bboxes[app].reshape(-1,2)
        l = data[:,0].min()
        r = data[:,0].max()
        b = data[:,1].min()
        t = data[:,1].max()
        
        res.append([
            [l,b],
            [r,b],
            [r,t],
            [l,t]
        ])

        torm = torm.union(app)

    for i in lst:
        if i in torm:
            continue
        res.append(bboxes[i])
    
    return res

def _box_pipeline(image):
    # reader.recognize(image)
    image = image.convert('RGB')
    results = reader.readtext(np.array(image))
    bboxes = [_[0] for _ in results]

    app = []
    for bbox in bboxes:
        if bbox[0][1] == bbox[1][1] and bbox[1][0] == bbox[2][0]:
            app.append(bbox)
    bboxes = merge_bboxes(app)

    bboxes = merge_bboxes(bboxes)

    return [bbox_to_lbrt(_) for _ in bboxes]

def box_pipeline(image, md5):
    msg = q.put(
        id = md5,
        msg = {'args': (image,)},
        handler = _box_pipeline,
    )

    return msg.response()

def box_run(img_obj: m.Image, image: Union[Image.Image, None] = None, force: bool = False, options: dict = {}) -> list[m.BBox]:
    params = {
        'image': img_obj,
        'model': bbox_model_obj,
        'options': options,
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

