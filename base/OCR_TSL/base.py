# import json
import json
import os
from pathlib import Path

from transformers import (AutoImageProcessor, AutoModel, AutoModelForSeq2SeqLM,
                          AutoTokenizer, VisionEncoderDecoderModel)

from .. import models as m

# from .. import models as m

# This should be set from env variables in the container
root = Path(os.environ.get('TRANSFORMERS_CACHE', '.'))
# print(f'Cache dir: {cache_dir}')
# root = Path("C:\models")
# root = Path("/home/crivella/app/AI")
dev = os.environ.get('DEVICE', 'cpu')

def load(loader, model_id: str):
    res = None
    try:
        mid = root / model_id
        # raise OSError
        print(f'Attempt loading from store: "{loader}" "{mid}"')
        res = loader.from_pretrained(mid)
    except Exception:
        # Needed to catch some weird exception from transformers
        # eg: huggingface_hub.utils._validators.HFValidationError: Repo id must use alphanumeric chars or '-', '_', '.', '--' and '..' are forbidden, '-' and '.' cannot start or end the name, max length is 96: ...
        print(f'Attempt loading from cache: "{loader}" "{model_id}" "{root}"')
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

if os.environ.get('AUTOCREATE_LANGUAGES', 'false').lower() == 'true':
    cwd = Path(__file__).parent
    with open(cwd / 'languages.json') as f:
        langs = json.load(f)

    for lang in langs:
        m.Language.objects.get_or_create(**lang)

if os.environ.get('AUTOCREATE_VALIDATED_MODELS', 'false').lower() == 'true':
    cwd = Path(__file__).parent
    with open(cwd / 'models.json') as f:
        models = json.load(f)

    for box in models['box']:
        model, _ = m.OCRBoxModel.objects.get_or_create(**box)

    for ocr in models['ocr']:
        lang = ocr.pop('lang')
        model, _ = m.OCRModel.objects.get_or_create(**ocr)
        for l in lang:
            model.languages.add(m.Language.objects.get(iso1=l))

    for tsl in models['tsl']:
        src = tsl.pop('lang_src')
        dst = tsl.pop('lang_dst')
        model, _ = m.TSLModel.objects.get_or_create(**tsl)
        for l in src:
            model.src_languages.add(m.Language.objects.get(iso1=l))

        for l in dst:
            model.dst_languages.add(m.Language.objects.get(iso1=l))
