import base64
import hashlib
import json

from django.http import HttpRequest, JsonResponse
from django.middleware import csrf
from django.views.decorators.csrf import csrf_exempt

from . import models as m
from .OCR_TSL import ocr_tsl_pipeline


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
            b64 = data.get('contents')
            md5 = data.get('md5')
            url = data.get('url')
            if b64 is None:
                return JsonResponse({'error': 'no contents'}, status=400)

            bin = base64.b64decode(b64)
            # Doing md5 on the base64 to have consistency with the JS generate one
            # Can't find a way to run ms5 on the binary (the blob does not work)
            if md5 != hashlib.md5(b64.encode('utf-8')).hexdigest():
                return JsonResponse({'error': 'md5 mismatch'}, status=400)

            print('md5', md5)
            print('url', url)

            res = ocr_tsl_pipeline(bin, md5)

        return JsonResponse({
            'test': 'POST',
            'result': res,
            })
    return JsonResponse({'error': f'{request.method} not allowed'}, status=405)
