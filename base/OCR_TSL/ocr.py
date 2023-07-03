from pathlib import Path

import easyocr
import numpy as np
from PIL import Image
from transformers import (BertJapaneseTokenizer, VisionEncoderDecoderModel,
                          ViTImageProcessor)

from .base import dev, root

ocr_model_id = "kha-white/manga-ocr-base"

reader = easyocr.Reader(['ja'], gpu=True)

mid = root / 'OCR' / ocr_model_id
ocr_model = VisionEncoderDecoderModel.from_pretrained(
    mid
    ).to(dev)
ocr_tokenizer = BertJapaneseTokenizer.from_pretrained(mid)
ocr_image_processor = ViTImageProcessor.from_pretrained(mid)

from ..models import OCRBoxModel, OCRModel

# bbox_model = 1
# ocr_model = 1
bbox_model_obj, _ = OCRBoxModel.objects.get_or_create(name='easyocr')
ocr_model_obj, _ = OCRModel.objects.get_or_create(name=ocr_model_id)

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

        for i in app:
            lst.remove(i)

    for i in lst:
        res.append(bboxes[i])
    
    return res

def get_ocr_boxes(image):
    # reader.recognize(image)
    results = reader.readtext(np.array(image))
    bboxes = [_[0] for _ in results]

    app = []
    for bbox in bboxes:
        if bbox[0][1] == bbox[1][1] and bbox[1][0] == bbox[2][0]:
            app.append(bbox)
    bboxes = merge_bboxes(app)

    bboxes = merge_bboxes(bboxes)

    return [bbox_to_lbrt(_) for _ in bboxes]



def ocr(img: Image, bbox: tuple[int, int, int, int] = None, *args, **kwargs):
    if isinstance(img, (str, Path)):
        img = Image.open(img)
    if isinstance(img, Image.Image):
        img = img.convert("RGB")
    else:
        raise TypeError(f"img should be PIL Image or path to file, but got {type(img)}")
    
    if bbox:
        img = img.crop(bbox)
    
    pixel_values = ocr_image_processor(img, return_tensors="pt").pixel_values
    if dev == 'cuda':
        pixel_values = pixel_values.cuda()
    generated_ids = ocr_model.generate(pixel_values, *args, **kwargs)
    generated_text = ocr_tokenizer.batch_decode(generated_ids, skip_special_tokens=True)

    return generated_text[0].replace(' ', '')

# def ocr_pipeline(image):
#     bboxes = get_ocr_boxes(image)

#     res = []
#     for bbox in bboxes:
#         bbox = bbox_to_lbrt(bbox)
#         app = image.crop(bbox)

#         text = ocr(app)
#         res.append((bbox, text))
    
#     return res