import base64
import hashlib
import io
import json
import os
import time

from django.http import HttpRequest, JsonResponse
from django.middleware import csrf
from django.views.decorators.csrf import csrf_exempt
from PIL import Image, ImageDraw, ImageFont

from . import models as m
from .OCR_TSL import (bbox_model_obj, get_ocr_boxes, ocr, ocr_model_obj,
                      tsl_model_obj, tsl_pipeline)

# print(os.path.abspath(os.getcwd()))
font = ImageFont.truetype("MangaMaster BB Bold.ttf", 28)

@csrf_exempt
def test(request: HttpRequest) -> JsonResponse:
    if request.method == 'GET':
        csrf.get_token(request)
        return JsonResponse({
            'test': 'GET',
            'objs': list(m.OCRmodel.objects.all()),
            })
    if request.method == 'POST':
        data = {}
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            # print([data])
            # print(data)
            c = data.get('contents')
            if c is None:
                return JsonResponse({'error': 'no contents'}, status=400)

            bin = base64.b64decode(c)
            # md5 = hashlib.md5(bin).hexdigest()
            md5 = hashlib.md5(c.encode('utf-8')).hexdigest()
            print(md5)
            img = Image.open(io.BytesIO(bin))
            # i.show()
            # time.sleep(5)

            img_obj, _ = m.Image.objects.get_or_create(
                md5=md5,
                )

            bbox_run, todo = m.OCRBoxRun.objects.get_or_create(
                options={},
                image=img_obj,
                model=bbox_model_obj
                )
            
            if todo:
                print('Running BBox OCR')
                bboxes = get_ocr_boxes(img)
                for bbox in bboxes:
                    l,b,r,t = bbox
                    new = m.BBox.objects.create(
                        l=l,
                        b=b,
                        r=r,
                        t=t,
                        image=img_obj,
                        from_ocr=bbox_run,
                        )
            else:
                print('Reusing BBox OCR')
                # bboxes = [_.lbrt for _ in bbox_run.result.all()]
            # app = ocr_pipeline(img)
            # print(app)

            draw = ImageDraw.Draw(img)
            for bbox_obj in bbox_run.result.all():
                print(bbox_obj)
                bbox = bbox_obj.lbrt
                ocr_run, todo = m.OCRRun.objects.get_or_create(
                    options={},
                    bbox=bbox_obj,
                    model=ocr_model_obj,
                    )
                if todo or ocr_run.result is None:
                    print('Running OCR')
                    text = ocr(img, bbox=bbox)
                    text_obj, _ = m.Text.objects.get_or_create(
                        text=text,
                        lang='ja',
                        )
                    ocr_run.result = text_obj
                    ocr_run.save()
                else:
                    print('Reusing OCR')
                    text_obj = ocr_run.result
                    text = ocr_run.result.text

                print(bbox, text)
                # print(text)
                tsl_run_obj, todo = m.TranslationRun.objects.get_or_create(
                    options={},
                    text=text_obj,
                    model=tsl_model_obj,
                    )
                
                if todo or tsl_run_obj.result is None:
                    print('Running TSL')
                    new = tsl_pipeline(text, 'ja', 'en')
                    text_obj, _ = m.Text.objects.get_or_create(
                        text=new,
                        lang='en',
                        )
                    tsl_run_obj.result = text_obj
                    tsl_run_obj.save()
                else:
                    print('Reusing TSL')
                    new = tsl_run_obj.result.text
                # print(new)
                l,b,r,t = bbox
                draw.rectangle(bbox, outline='red')
                draw.text((l,b), new, font=font, fill='red')

            img.show()

                


        return JsonResponse({
            'test': 'POST',
            'result': [
                {'ocr': '123', 'tsl': '456', 'box': (0,0,100,100)},
                {'ocr': 'abc', 'tsl': 'def', 'box': (50,50,150,150)},
            ]
            })
    return JsonResponse({'error': f'{request.method} not allowed'}, status=405)
