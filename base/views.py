import base64
import hashlib
import json

from django.http import HttpRequest, JsonResponse
from django.middleware import csrf
from django.views.decorators.csrf import csrf_exempt

from . import models as m
from .OCR_TSL import (get_ocr_model, get_tsl_model, load_bbox_model,
                      load_ocr_model, load_tsl_model, ocr_tsl_pipeline)


def handshake(request: HttpRequest) -> JsonResponse:
    # import_models()
    print(str(get_ocr_model()), str(get_tsl_model()))
    return JsonResponse({
        'OCRModels': [str(_) for _ in m.OCRModel.objects.all()] or ["1","2","3"],
        'TSLModels': [str(_) for _ in m.TSLModel.objects.all()] or ["4","5","6"],
        'ocr_selected': str(get_ocr_model()),
        'tsl_selected': str(get_tsl_model()), 
        })

@csrf_exempt
def load_models(request: HttpRequest) -> JsonResponse:
    if request.method == 'POST':
        data = {}
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            return JsonResponse({'error': 'invalid content type'}, status=400)
        print('LOAD', data)
        
        ocr_model_id = data.get('ocr_model_id')
        tsl_model_id = data.get('tsl_model_id')
        if ocr_model_id is None:
            return JsonResponse({'error': 'no ocr_model_id'}, status=400)
        if tsl_model_id is None:
            return JsonResponse({'error': 'no tsl_model_id'}, status=400)

        try:
            load_bbox_model('easyocr')
            load_ocr_model(ocr_model_id)
            load_tsl_model(tsl_model_id)
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
        data = {}
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            return JsonResponse({'error': 'invalid content type'}, status=400)
        
        b64 = data.get('contents')
        md5 = data.get('md5')
        frc = data.get('force', False)
        opt = data.get('options', {})
        if b64 is None:
            return JsonResponse({'error': 'no contents'}, status=400)
        # return JsonResponse({}, status=500)

        bin = base64.b64decode(b64)
        # Doing md5 on the base64 to have consistency with the JS generate one
        # Can't find a way to run ms5 on the binary (the blob does not work)
        if md5 != hashlib.md5(b64.encode('utf-8')).hexdigest():
            return JsonResponse({'error': 'md5 mismatch'}, status=400)

        print('md5', md5)

        res = ocr_tsl_pipeline(bin, md5, force=frc, options=opt)
        
        # res = [
        #         {'ocr': '123', 'tsl': '456', 'box': (0,0,100,100)},
        #         {'ocr': 'abc', 'tsl': 'def', 'box': (50,50,150,150)},
        #     ]

        return JsonResponse({
            'test': 'POST',
            'result': res,
            })
    return JsonResponse({'error': f'{request.method} not allowed'}, status=405)
