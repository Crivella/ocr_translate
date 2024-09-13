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
"""Full OCR + translation pipelines."""
import logging

from PIL import Image

from .. import models as m
from .box import get_box_model
from .lang import get_lang_dst, get_lang_src
from .ocr import get_ocr_model
from .tsl import get_tsl_model

logger = logging.getLogger('ocr.general')

def ocr_tsl_pipeline_lazy(
        md5: str,
        options_box: m.OptionDict,
        options_ocr: m.OptionDict,
        options_tsl: m.OptionDict,
        ) -> list[dict]:
    """
    Try to lazily generate reponse from md5.
    Should raise a ValueError if the operation is not possible (fails at any step).
    """
    box_model = get_box_model()
    ocr_model = get_ocr_model()
    tsl_model = get_tsl_model()

    favor_manual = options_tsl.options.get('favor_manual', True)
    logger.debug(f'LAZY: START {md5}')
    res = []
    try:
        img_obj= m.Image.objects.get(md5=md5)
    except m.Image.DoesNotExist as exc:
        raise ValueError(f'Image with md5 {md5} does not exist') from exc
    _, bbox_obj_list = box_model.box_detection(img_obj, get_lang_src(), options=options_box)

    for bbox_obj in bbox_obj_list:
        text_obj = ocr_model.ocr(bbox_obj, get_lang_src(), options=options_ocr)
        text_obj = next(text_obj)

        tsl_obj = tsl_model.translate(
            text_obj, get_lang_src(), get_lang_dst(),
            options=options_tsl, favor_manual=favor_manual,
            lazy=True
            )
        tsl_obj = next(tsl_obj)

        text = text_obj.text
        new = tsl_obj.text

        res.append({
            'ocr': text,
            'tsl': new,
            'box': bbox_obj.lbrt,
            })

    logger.debug('LAZY: DONE')
    return res

# This is already kinda lazy, but the idea for the lazy version is to
# check if all results are available just with the md5, and if not,
# ask the extension to send the binary to minimize traffic
def ocr_tsl_pipeline_work(  # pylint: disable=too-many-locals
        img: Image.Image, md5: str,
        options_box: m.OptionDict,
        options_ocr: m.OptionDict,
        options_tsl: m.OptionDict,
        force: bool = False,
        ) -> list[dict]:
    """
    Generate response from md5 and binary.
    Will attempt to behave lazily at every step unless force is True.
    """
    box_model = get_box_model()
    ocr_model = get_ocr_model()
    tsl_model = get_tsl_model()
    lang_src = get_lang_src()
    lang_dst = get_lang_dst()

    favor_manual = options_tsl.options.get('favor_manual', True)
    logger.debug(f'WORK: START {md5}')

    img_obj, _ = m.Image.objects.get_or_create(md5=md5)
    bbox_obj_list_single, bbox_obj_list_merged = box_model.box_detection(
        img_obj, lang_src ,image=img, options=options_box
        )

    bbox_obj_list = bbox_obj_list_merged
    if ocr_model.ocr_mode == ocr_model.SINGLE:
        bbox_obj_list = bbox_obj_list_single

    texts = []
    for bbox_obj in bbox_obj_list:
        logger.debug(str(bbox_obj))

        text_obj = ocr_model.ocr(bbox_obj, lang_src, image=img, force=force, block=False, options=options_ocr)
        next(text_obj)
        texts.append(text_obj)

    texts = [next(_) for _ in texts]
    # If OCR is running in single element mode, must merge the results and pretend runs on the merged
    # bounding boxes were done with the merged text as outputs
    if ocr_model.ocr_mode == ocr_model.SINGLE:
        logger.debug(f'OCR DONE (single): {texts}')
        str_list = [_.text for _ in texts]

        merged_text = ocr_model.merge_single_result(
            lang_src.iso1,
            str_list,
            bbox_obj_list_single,
            bbox_obj_list_merged
            )
        texts = []
        for text, bbox_obj in zip(merged_text, bbox_obj_list_merged):
            text_obj, _ = m.Text.objects.get_or_create(text=text)
            params = {
                'bbox': bbox_obj,
                'model': ocr_model,
                'lang_src': lang_src,
                'options': options_ocr,
                'result_merged': text_obj
            }
            merged_run = m.OCRRun.objects.create(**params)

            # Pretend the current texts are the merged ones
            texts.append(merged_run.result_merged)

            logger.debug(f'OCR DONE (mock_merged): {text}')


    logger.debug(f'OCR DONE: {texts}')

    trans = []
    for text_obj in texts:
        tsl_obj = tsl_model.translate(
            text_obj, lang_src, lang_dst, options=options_tsl,
            force=force, block=False, favor_manual=favor_manual
            )
        next(tsl_obj)
        trans.append(tsl_obj)

    trans = [next(_) for _ in trans]
    logger.debug(f'TRANSLATION DONE: {trans}')

    res = []
    for bbox_obj, text_obj, tsl_obj in zip(bbox_obj_list_merged, texts, trans):
        text = text_obj.text
        new = tsl_obj.text

        res.append({
            'ocr': text,
            'tsl': new,
            'box': bbox_obj.lbrt,
            })

    logger.debug('WORK: DONE')
    return res
