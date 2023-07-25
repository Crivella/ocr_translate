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
"""Functions and piplines to perform Box OCR on an image."""
import logging
from typing import Hashable, Iterable

import easyocr
import numpy as np
import torch
from PIL import Image

from .. import models as m
from ..queues import box_queue as q
from .base import dev

READER = None

logger = logging.getLogger('ocr.general')

BOX_MODEL_ID = None
BBOX_MODEL_OBJ = None

def unload_box_model():
    """Remove the current box model from memory."""
    global BBOX_MODEL_OBJ, READER, BOX_MODEL_ID

    logger.info(f'Unloading BOX model: {BOX_MODEL_ID}')
    if BOX_MODEL_ID == 'easyocr':
        pass
    READER = None
    BBOX_MODEL_OBJ = None
    BOX_MODEL_ID = None

    if dev == 'cuda':
        torch.cuda.empty_cache()


def load_box_model(model_id: str):
    """Load a box model into memory."""
    global BBOX_MODEL_OBJ, READER, BOX_MODEL_ID

    if BOX_MODEL_ID == model_id:
        return

    logger.info(f'Loading BOX model: {model_id}')
    if model_id == 'easyocr':
        READER = easyocr.Reader([], gpu=(dev == 'cuda'), recognizer=False)
        BBOX_MODEL_OBJ, _ = m.OCRBoxModel.objects.get_or_create(name=model_id)
        BOX_MODEL_ID = model_id
    else:
        raise NotImplementedError

    logger.debug(f'OCR model loaded: {model_id}')
    logger.debug(f'OCR model object: {BBOX_MODEL_OBJ}')

def get_box_model() -> m.OCRBoxModel:
    """Get the current box model."""
    return BBOX_MODEL_OBJ

def intersections(bboxes: Iterable[tuple[int, int, int, int]], margin: int = 5) -> list[set[int]]:
    """Determine the intersections between a list of bounding boxes.

    Args:
        bboxes (Iterable[tuple[int, int, int, int]]): List of bounding boxes in lrbt format.
        margin (int, optional): Number of extra pixels outside of the boxes that define an intersection. Defaults to 5.

    Returns:
        list[set[int]]: List of sets of indexes of the boxes that intersect.
    """
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

def merge_bboxes(bboxes: Iterable[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
    """Merge a list of intersecting bounding boxes. All intersecting boxes are merged into a single box.

    Args:
        bboxes (Iterable[Iterable[int]]): Iterable of bounding boxes in lrbt format.

    Returns:
        list[tuple[int]]: List of merged bounding boxes in lrbt format.
    """
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

def _box_pipeline(image: Image.Image, options: dict = None) -> list[tuple[int, int, int, int]]:
    """Perform box OCR on an image.

    Args:
        image (Image.Image): A Pillow image on which to perform OCR.
        options (dict, optional): A dictionary of options.

    Raises:
        NotImplementedError: The type of model specified is not implemented.

    Returns:
        list[tuple[int, int, int, int]]: A list of bounding boxes in lrbt format.
    """

    if options is None:
        options = {}

    # reader.recognize(image)
    if BOX_MODEL_ID == 'easyocr':
        image = image.convert('RGB')
        results = READER.detect(np.array(image))

        # Axis rectangles
        bboxes = results[0][0]

        # Free (NOT IMPLEMENTED)
        # ...

        bboxes = merge_bboxes(bboxes)
    else:
        raise NotImplementedError

    return bboxes

def box_pipeline(*args, id_: Hashable, block: bool = True, **kwargs):
    """Queue a box OCR pipeline.

    Args:
        id_ (Hashable): A unique identifier for the OCR task.
        block (bool, optional): Whether to block until the task is complete. Defaults to True.

    Returns:
        Union[str, Message]: The text extracted from the image (block=True) or a Message object (block=False).
    """
    msg = q.put(
        id_ = id_,
        msg = {'args': args, 'kwargs': kwargs},
        handler = _box_pipeline,
    )

    if block:
        return msg.response()
    return msg

def box_run(
        img_obj: m.Image, lang: m.Language, image: Image.Image = None,
        force: bool = False, options: m.OptionDict = None
        ) -> list[m.BBox]:
    """High level function to perform box OCR on an image. Will attempt to reuse a previous run if possible.

    Args:
        img_obj (m.Image): An Image object from the database.
        lang (m.Language): A Language object from the database (not every model is gonna use this).
        image (Image.Image, optional): The Pillow image to be used for OCR if a previous result is not found.
            Defaults to None.
        force (bool, optional): If true, re-run the OCR even if a previous result is found. Defaults to False.
        options (m.OptionDict, optional): An OptionDict object from the database. Defaults to None.

    Raises:
        ValueError: ValueError is raised if at any step of the pipeline an image is required but not provided.

    Returns:
        list[m.BBox]: A list of BBox objects containing the resulting bounding boxes.
    """
    options_obj = options or m.OptionDict.objects.get(options={})
    params = {
        'image': img_obj,
        'model': BBOX_MODEL_OBJ,
        'options': options_obj,
        'lang_src': lang,
    }

    bbox_run = m.OCRBoxRun.objects.filter(**params).first()
    if bbox_run is None or force:
        if image is None:
            raise ValueError('Image is required for BBox OCR')
        logger.info('Running BBox OCR')
        opt_dct = options_obj.options
        bboxes = box_pipeline(
            image,
            id_=img_obj.md5,
            options=opt_dct,
            )
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
        logger.info(f'Reusing BBox OCR <{bbox_run.id}>')
    logger.info(f'BBox OCR result: {len(bbox_run.result.all())} boxes')

    return list(bbox_run.result.all())
