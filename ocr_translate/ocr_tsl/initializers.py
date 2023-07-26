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
"""Initialize the server based on environment variables."""
import json
import logging
from pathlib import Path

from django.db.models import Count

from .. import models as m
from .box import load_box_model
from .lang import load_lang_dst, load_lang_src
from .ocr import load_ocr_model
from .tsl import load_tsl_model

logger = logging.getLogger('ocr.general')

def init_most_used():
    """Initialize the server with the most used languages and models."""
    src = m.Language.objects.annotate(count=Count('trans_src')).order_by('-count').first()
    dst = m.Language.objects.annotate(count=Count('trans_dst')).order_by('-count').first()

    if src:
        load_lang_src(src.iso1)
    if dst:
        load_lang_dst(dst.iso1)

    box = m.OCRBoxModel.objects.annotate(count=Count('box_runs')).order_by('-count').first()
    ocr = m.OCRModel.objects.annotate(count=Count('ocr_runs')).order_by('-count').first()
    tsl = m.TSLModel.objects.annotate(count=Count('tsl_runs')).order_by('-count').first()

    if box:
        load_box_model(box.name)
    if ocr:
        load_ocr_model(ocr.name)
    if tsl:
        load_tsl_model(tsl.name)

def auto_create_languages():
    """Create Language objects from json file."""
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

def auto_create_models():
    """Create OCR and TSL models from json file. Also create default OptionDict"""
    cwd = Path(__file__).parent
    with open(cwd / 'models.json', encoding='utf-8') as f:
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
            kwargs = {lcode: l}
            model.src_languages.add(*m.Language.objects.filter(**kwargs))

        for l in dst:
            logger.debug(f'Adding dst language: {l}')
            kwargs = {lcode: l}
            model.dst_languages.add(*m.Language.objects.filter(**kwargs))
        model.save()

    m.OptionDict.objects.get_or_create(options={})
