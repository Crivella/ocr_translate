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
import base64
import hashlib
import io
import json
import logging

import numpy as np
from django.db.models import Count
from django.http import HttpRequest, JsonResponse
from django.middleware import csrf
from django.views.decorators.csrf import csrf_exempt
from PIL import Image

from . import models as m
from .OCR_TSL import ocr_tsl_pipeline_lazy, ocr_tsl_pipeline_work
from .OCR_TSL.box import get_box_model, load_box_model, unload_box_model
from .OCR_TSL.lang import (get_lang_dst, get_lang_src, load_lang_dst,
                           load_lang_src)
from .OCR_TSL.ocr import get_ocr_model, load_ocr_model, unload_ocr_model
from .OCR_TSL.tsl import (get_tsl_model, load_tsl_model, tsl_run,
                          unload_tsl_model)
from .queues import main_queue as q

logger = logging.getLogger('ocr.general')


def post_data_converter(request: HttpRequest) -> dict:
    if request.content_type == 'application/json':
        return json.loads(request.body)
    else:
        raise ValueError('invalid content type')


def handshake(request: HttpRequest) -> JsonResponse:
    # import_models()
    if not request.method == 'GET':
        return JsonResponse({'error': f'{request.method} not allowed'}, status=405)
    
    csrf.get_token(request)
    
    logger.debug(f'Handshake: {str(get_ocr_model())}, {str(get_tsl_model())}')
    lang_src = get_lang_src()
    lang_dst = get_lang_dst()

    languages = m.Language.objects.annotate(count=Count('trans_src')+Count('trans_dst')).order_by('-count')
    box_models = m.OCRBoxModel.objects.annotate(count=Count('box_runs')).order_by('-count')
    ocr_models = m.OCRModel.objects.annotate(count=Count('ocr_runs')).order_by('-count')
    tsl_models = m.TSLModel.objects.annotate(count=Count('tsl_runs')).order_by('-count')

    if not lang_src is None:
        box_models = box_models.filter(languages=lang_src)
        ocr_models = ocr_models.filter(languages=lang_src)
        if not lang_dst is None:
            tsl_models = tsl_models.filter(
                src_languages=lang_src,
                dst_languages=lang_dst,
                )
            
    box_model = get_box_model() or ''
    ocr_model = get_ocr_model() or ''
    tsl_model = get_tsl_model() or ''

    lang_src = lang_src or ''
    lang_dst = lang_dst or ''

    return JsonResponse({
        'Languages': [str(_) for _ in languages],
        'BOXModels': [str(_) for _ in box_models],
        'OCRModels': [str(_) for _ in ocr_models],
        'TSLModels': [str(_) for _ in tsl_models],

        'box_selected': str(box_model), 
        'ocr_selected': str(ocr_model),
        'tsl_selected': str(tsl_model), 
        'lang_src': str(lang_src),
        'lang_dst': str(lang_dst),
        })

@csrf_exempt
def load_models(request: HttpRequest) -> JsonResponse:
    if request.method == 'POST':
        try:
            data = post_data_converter(request)
        except ValueError as e:
            return JsonResponse({'error': 'invalid content type'}, status=400)

        logger.info('LOAD MODELS', data)
        logger.debug(data)
        
        box_model_id = data.get('box_model_id', None)
        ocr_model_id = data.get('ocr_model_id', None)
        tsl_model_id = data.get('tsl_model_id', None)

        try:
            if not box_model_id is None and not box_model_id == '':
                load_box_model(box_model_id)
            if not ocr_model_id is None and not ocr_model_id == '':
                load_ocr_model(ocr_model_id)
            if not tsl_model_id is None and not tsl_model_id == '':
                load_tsl_model(tsl_model_id)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        return JsonResponse({})
    return JsonResponse({'error': f'{request.method} not allowed'}, status=405)

@csrf_exempt
def set_lang(request: HttpRequest) -> JsonResponse:
    if request.method == 'POST':
        try:
            data = post_data_converter(request)
        except ValueError as e:
            return JsonResponse({'error': 'invalid content type'}, status=400)
        logger.info('SET LANG', data)
        
        lang_src = data.get('lang_src', None)
        lang_dst = data.get('lang_dst', None)
        if lang_src is None:
            return JsonResponse({'error': 'no lang_src'}, status=400)
        if lang_dst is None:
            return JsonResponse({'error': 'no lang_dst'}, status=400)

        old_src = get_lang_src()
        old_dst = get_lang_dst()
        try:
            load_lang_src(lang_src)
            load_lang_dst(lang_dst)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        new_src = get_lang_src()
        new_dst = get_lang_dst()

        c1 = old_src != new_src
        c2 = old_dst != new_dst
        if c1 or c2:
            tsl_model = get_tsl_model()
            if not tsl_model is None and (new_src not in tsl_model.src_languages.all() or new_dst not in tsl_model.dst_languages.all()):
                unload_tsl_model()
        if c1:
            box_model = get_box_model()
            ocr_model = get_ocr_model()
            if not box_model is None and (new_src not in box_model.languages.all()):
                unload_box_model()
            if not ocr_model is None and (new_src not in ocr_model.languages.all()):
                unload_ocr_model()
        if c2:
            pass
        
        return JsonResponse({})
    return JsonResponse({'error': f'{request.method} not allowed'}, status=405)

@csrf_exempt
def run_tsl(request: HttpRequest) -> JsonResponse:
    if request.method != 'POST':
        return JsonResponse({'error': f'{request.method} not allowed'}, status=405)
    
    try:
        data = post_data_converter(request)
    except ValueError as e:
        return JsonResponse({'error': 'invalid content type'}, status=400)
    
    text = data.get('text', None)
    if text is None:
        return JsonResponse({'error': 'no text'}, status=400)
    
    src_obj, _ = m.Text.objects.get_or_create(text=text)
    dst_obj = tsl_run(src_obj, get_lang_src(), get_lang_dst())
    dst_obj = next(dst_obj)

    return JsonResponse({
        'text': dst_obj.text,
        })

@csrf_exempt
def run_ocrtsl(request: HttpRequest) -> JsonResponse:
    if request.method == 'POST':
        try:
            data = post_data_converter(request)
        except ValueError as e:
            return JsonResponse({'error': 'invalid content type'}, status=400)
        
        b64 = data.get('contents', None)
        md5 = data.get('md5')
        frc = data.get('force', False)
        opt = data.get('options', {})

        if b64 is None:
            logger.info('No contents, trying to lazyload')
            if frc:
                return JsonResponse({'error': 'Cannot force ocr without contents'}, status=400)
            try:
                res = ocr_tsl_pipeline_lazy(md5, options=opt)
            except ValueError:
                return JsonResponse({'error': 'Failed to lazyload ocr'}, status=406)
        else:
            bin = base64.b64decode(b64)
            # Doing md5 on the base64 to have consistency with the JS generate one
            # Can't find a way to run md5 on the binary in JS (the blob does not work)
            if md5 != hashlib.md5(b64.encode('utf-8')).hexdigest():
                return JsonResponse({'error': 'md5 mismatch'}, status=400)
            logger.debug(f'md5 {md5} <- {len(bin)} bytes')

            img = Image.open(io.BytesIO(bin))
            # Needed to make sure the image is loaded synchronously before going forward
            # Enforce thread safety. Maybe there is a way to do it without numpy?
            np.array(img)

            # Check if same request is already in queue. If yes attach listener to it
            lang_src = get_lang_src()
            lang_dst = get_lang_dst()
            box_model = get_box_model()
            ocr_model = get_ocr_model()
            tsl_model = get_tsl_model()
            msg = q.put(
                id = (md5, lang_src.id, lang_dst.id, box_model.id, ocr_model.id, tsl_model.id),
                msg = {
                    'args': (img, md5),
                    'kwargs': {'force': frc, 'options': opt},
                },
                handler = ocr_tsl_pipeline_work,
            )

            res = msg.response()


        return JsonResponse({
            'test': 'POST',
            'result': res,
            })
    return JsonResponse({'error': f'{request.method} not allowed'}, status=405)

@csrf_exempt
def get_translations(request: HttpRequest) -> JsonResponse:
    if request.method != 'GET':
        return JsonResponse({'error': f'{request.method} not allowed'}, status=405)

    text = request.GET.get('text', None)

    if text is None:
        return JsonResponse({'error': 'no text'}, status=400)
    
    text_obj = m.Text.objects.filter(text=text).first()
    if text_obj is None:
        return JsonResponse({'error': 'text not found'}, status=404)
    
    translations = text_obj.to_trans.filter(
        lang_src=get_lang_src(),
        lang_dst=get_lang_dst(),
        )
    return JsonResponse({
        'translations': [{
            'model': str(_.model),
            'text': _.result.text,
            } for _ in translations],
        })


