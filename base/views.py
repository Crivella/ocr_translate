import base64
import hashlib
import io
import json
import queue
import time

import numpy as np
from django.http import HttpRequest, JsonResponse
from django.middleware import csrf
from django.views.decorators.csrf import csrf_exempt
from PIL import Image

from . import models as m
from .OCR_TSL import ocr_tsl_pipeline_lazy, ocr_tsl_pipeline_work
from .OCR_TSL.box import get_box_model, load_box_model
from .OCR_TSL.lang import (get_lang_dst, get_lang_src, load_lang_dst,
                           load_lang_src)
from .OCR_TSL.ocr import get_ocr_model, load_ocr_model
from .OCR_TSL.tsl import get_tsl_model, load_tsl_model
from .queues import main_queue as q


def post_data_converter(request: HttpRequest) -> dict:
    if request.content_type == 'application/json':
        return json.loads(request.body)
    else:
        raise ValueError('invalid content type')


def handshake(request: HttpRequest) -> JsonResponse:
    # import_models()
    if not request.method == 'GET':
        return JsonResponse({'error': f'{request.method} not allowed'}, status=405)
    
    # print(str(get_ocr_model()), str(get_tsl_model()))
    lang_src = get_lang_src()
    lang_dst = get_lang_dst()

    languages = m.Language.objects.all()
    box_models = m.OCRBoxModel.objects.all()
    ocr_models = m.OCRModel.objects.all()
    tsl_models = m.TSLModel.objects.all()

    if not lang_src is None:
        ocr_models = ocr_models.filter(languages=lang_src)
        if not lang_dst is None:
            tsl_models = tsl_models.filter(
                src_languages=lang_src,
                dst_languages=lang_dst,
                )

    return JsonResponse({
        'Languages': [str(_) for _ in languages],
        'BOXModels': [str(_) for _ in box_models],
        'OCRModels': [str(_) for _ in ocr_models],
        'TSLModels': [str(_) for _ in tsl_models],

        'box_selected': str(get_box_model()), 
        'ocr_selected': str(get_ocr_model()),
        'tsl_selected': str(get_tsl_model()), 
        'lang_src': str(get_lang_src()),
        'lang_dst': str(get_lang_dst()),
        })

@csrf_exempt
def load_models(request: HttpRequest) -> JsonResponse:
    if request.method == 'POST':
        try:
            data = post_data_converter(request)
        except ValueError as e:
            return JsonResponse({'error': 'invalid content type'}, status=400)

        print('LOAD', data)
        
        ocr_model_id = data.get('ocr_model_id', None)
        tsl_model_id = data.get('tsl_model_id', None)
        if ocr_model_id is None:
            return JsonResponse({'error': 'no ocr_model_id'}, status=400)
        if tsl_model_id is None:
            return JsonResponse({'error': 'no tsl_model_id'}, status=400)

        try:
            load_box_model('easyocr')
            load_ocr_model(ocr_model_id)
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
        print('SET LANG', data)
        
        lang_src = data.get('lang_src', None)
        lang_dst = data.get('lang_dst', None)
        if lang_src is None:
            return JsonResponse({'error': 'no lang_src'}, status=400)
        if lang_dst is None:
            return JsonResponse({'error': 'no lang_dst'}, status=400)

        try:
            load_lang_src(lang_src)
            load_lang_dst(lang_dst)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        return JsonResponse({})
    return JsonResponse({'error': f'{request.method} not allowed'}, status=405)

@csrf_exempt
def test(request: HttpRequest) -> JsonResponse:
    if request.method == 'GET':
        csrf.get_token(request)
        return JsonResponse({
            'test': 'GET',
            'objs': list(m.OCRModel.objects.all()),
            })
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
            print('md5', md5, ' <- ', len(bin))

            img = Image.open(io.BytesIO(bin))
            # Needed to make sure the image is loaded synchronously before going forward
            # Enforce thread safety. Maybe there is a way to do it without numpy?
            np.array(img)

            # Check if same request is already in queue. If yes attach listener to it
            msg = q.put(
                id = md5,
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
    if request.method != 'POST':
        return JsonResponse({'error': f'{request.method} not allowed'}, status=405)
    
    try:
        data = post_data_converter(request)
    except ValueError as e:
        return JsonResponse({'error': 'invalid content type'}, status=400)
    
    text = data.get('text', None)

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


