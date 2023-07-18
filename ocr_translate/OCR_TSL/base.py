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
import json
import logging
import os
from pathlib import Path

from transformers import (AutoImageProcessor, AutoModel, AutoModelForSeq2SeqLM,
                          AutoTokenizer, VisionEncoderDecoderModel)

from .. import models as m

logger = logging.getLogger('ocr.general')

root = Path(os.environ.get('TRANSFORMERS_CACHE', '.'))
logger.debug(f'Cache dir: {root}')
dev = os.environ.get('DEVICE', 'cpu')

def load(loader, model_id: str):
    res = None
    try:
        mid = root / model_id
        logger.debug(f'Attempt loading from store: "{loader}" "{mid}"')
        res = loader.from_pretrained(mid)
    except Exception:
        # Needed to catch some weird exception from transformers
        # eg: huggingface_hub.utils._validators.HFValidationError: Repo id must use alphanumeric chars or '-', '_', '.', '--' and '..' are forbidden, '-' and '.' cannot start or end the name, max length is 96: ...
        logger.debug(f'Attempt loading from cache: "{loader}" "{model_id}" "{root}"')
        res = loader.from_pretrained(model_id, cache_dir=root)
    return res

mapping = {
    'tokenizer': AutoTokenizer,
    'ved_model': VisionEncoderDecoderModel,
    'model': AutoModel,
    'image_processor': AutoImageProcessor,
    'seq2seq': AutoModelForSeq2SeqLM
}

accept_device = ['ved_model', 'seq2seq', 'model']

def load_hugginface_model(model_id: str, request: list[str]):
    res = {}
    for r in request:
        if r not in mapping:
            raise ValueError(f'Unknown request: {r}')
        v = load(mapping[r], model_id)
        if v is None:
            raise ValueError(f'Could not load model: {model_id}')
        
        if r in accept_device:
            v = v.to(dev)

        res[r] = v

    return res

if os.environ.get('AUTOCREATE_LANGUAGES', 'false').lower() == 'true':
    cwd = Path(__file__).parent
    with open(cwd / 'languages.json', encoding='utf-8') as f:
        langs = json.load(f)

    for lang in langs:
        logger.debug(f'Creating language: {lang}')
        name = lang.pop('name')
        iso1 = lang.pop('iso1')
        iso2t = lang.pop('iso2t')
        iso2b = lang.pop('iso2b')
        iso3 = lang.pop('iso3')
        l, _ = m.Language.objects.get_or_create(name=name, iso1=iso1, iso2t=iso2t, iso2b=iso2b, iso3=iso3)
        for k,v in lang.items():
            setattr(l, k, v)
        l.save()

if os.environ.get('AUTOCREATE_VALIDATED_MODELS', 'false').lower() == 'true':
    cwd = Path(__file__).parent
    with open(cwd / 'models.json') as f:
        models = json.load(f)

    for box in models['box']:
        logger.debug(f'Creating box model: {box}')
        lang = box.pop('lang')
        lcode = box.pop('lang_code')
        model, _ = m.OCRBoxModel.objects.get_or_create(**box)
        model.language_format = lcode
        for l in lang:
            model.languages.add(m.Language.objects.get(iso1=l))
        model.save()

    for ocr in models['ocr']:
        logger.debug(f'Creating ocr model: {ocr}')
        lang = ocr.pop('lang')
        lcode = ocr.pop('lang_code')
        model, _ = m.OCRModel.objects.get_or_create(**ocr)
        model.language_format = lcode
        for l in lang:
            model.languages.add(m.Language.objects.get(iso1=l))
        model.save()

    for tsl in models['tsl']:
        logger.debug(f'Creating tsl model: {tsl}')
        src = tsl.pop('lang_src')
        dst = tsl.pop('lang_dst')
        lcode = tsl.pop('lang_code', None)
        model, _ = m.TSLModel.objects.get_or_create(**tsl)
        model.language_format = lcode
        for l in src:
            logger.debug(f'Adding src language: {l}')
            kw = {lcode: l}
            model.src_languages.add(*m.Language.objects.filter(**kw))

        for l in dst:
            logger.debug(f'Adding dst language: {l}')
            kw = {lcode: l}
            model.dst_languages.add(*m.Language.objects.filter(**kw))
        model.save()

    base_option, _ = m.OptionDict.objects.get_or_create(options={})
