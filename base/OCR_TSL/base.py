# import json
import os
from pathlib import Path

from transformers import (AutoImageProcessor, AutoModel, AutoModelForSeq2SeqLM,
                          AutoTokenizer, VisionEncoderDecoderModel)

# from .. import models as m

# This should be set from env variables in the container
root = Path(os.environ.get('TRANSFORMERS_CACHE'))
# print(f'Cache dir: {cache_dir}')
# root = Path("C:\models")
# root = Path("/home/crivella/app/AI")
dev = os.environ.get('DEVICE', 'cpu')

def load(loader, model_id: str):
    res = None
    try:
        mid = root / model_id
        # raise OSError
        res = loader.from_pretrained(mid)
    except OSError:
        res = loader.from_pretrained(model_id, cache_dir=root)
    return res

mapping = {
    'tokenizer': AutoTokenizer,
    'ved_model': VisionEncoderDecoderModel,
    'model': AutoModel,
    'image_processor': AutoImageProcessor,
    'seq2seq': AutoModelForSeq2SeqLM
}

def load_model(model_id: str, request: list[str]):
    res = {}
    for r in request:
        if r not in mapping:
            raise ValueError(f'Unknown request: {r}')
        v = load(mapping[r], model_id)
        if v is None:
            raise ValueError(f'Could not load model: {model_id}')
        
        if r in ['ved_model', 'seq2seq', 'model']:
            v = v.to(dev)

        res[r] = v

    return res



# def import_models():
#     with open(root / "config.json") as f:
#         config = json.load(f)

#     for name in config["ocr_models"]:
#         m.OCRModel.objects.get_or_create(name=name)
#     for name in config["tsl_models"]:
#         m.TSLModel.objects.get_or_create(name=name)

    