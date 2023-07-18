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
import logging
import os

from PIL import Image

from .. import models as m
# from .base import import_models
from .box import box_run, load_box_model
from .lang import get_lang_dst, get_lang_src, load_lang_dst, load_lang_src
from .ocr import load_ocr_model, ocr_run
from .tsl import load_tsl_model, tsl_run

logger = logging.getLogger('ocr.general')

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
    bbox_obj_list = box_run(img_obj, get_lang_src())
    for bbox_obj in bbox_obj_list:
        text_obj = ocr_run(bbox_obj, get_lang_src())
        text_obj = next(text_obj)
        tsl_obj = tsl_run(text_obj, get_lang_src(), get_lang_dst(), lazy=True)
        tsl_obj = next(tsl_obj)

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
    bbox_obj_list = box_run(img_obj, get_lang_src() ,image=img)

    texts = []
    for bbox_obj in bbox_obj_list:
        logger.debug(str(bbox_obj))

        text_obj = ocr_run(bbox_obj, get_lang_src(), image=img, force=force, block=False)
        next(text_obj)
        texts.append(text_obj)

    texts = [next(_) for _ in texts]
    logger.debug(f'OCR DONE: {texts}')

    trans = []
    for text_obj in texts:
        tsl_obj = tsl_run(text_obj, get_lang_src(), get_lang_dst(), force=force, block=False)
        next(tsl_obj)
        trans.append(tsl_obj)

    trans = [next(_) for _ in trans]
    logger.debug(f'TRANSLATION DONE: {trans}')

    for bbox_obj, text_obj, tsl_obj in zip(bbox_obj_list, texts, trans):
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

    src = m.Language.objects.annotate(count=Count('trans_src')).order_by('-count').first()
    dst = m.Language.objects.annotate(count=Count('trans_dst')).order_by('-count').first()

    if src:
        load_lang_src(src.iso1)
    if dst:
        load_lang_dst(dst.iso1)

    box = m.OCRBoxModel.objects.annotate(count=Count('box_runs')).order_by('-count').first()
    ocr = m.OCRModel.objects.annotate(count=Count('ocr_runs')).order_by('-count').first()
    tsl = m.TSLModel.objects.annotate(count=Count('tsl_runs')).order_by('-count').first()

    if box:
        load_box_model(box.name)
    if ocr:
        load_ocr_model(ocr.name)
    if tsl:
        load_tsl_model(tsl.name)


if os.environ.get('LOAD_ON_START', 'false').lower() == 'true':
    init_most_used()
