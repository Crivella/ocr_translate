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
from importlib import resources
from importlib.metadata import entry_points

from django.db.models import Count

from .. import models as m
from ..plugin_manager import PluginManager
from .box import load_box_model
from .lang import load_lang_dst, load_lang_src
from .ocr import load_ocr_model
from .tsl import load_tsl_model

logger = logging.getLogger('ocr.general')

def init_most_used():
    """Initialize the server with the most used languages and models."""
    logger.info('Initializing server with most used languages and models')
    src = m.Language.objects.annotate(count=Count('trans_src')).order_by('-count').first()
    dst = m.Language.objects.annotate(count=Count('trans_dst')).order_by('-count').first()

    if src and src.count > 0:
        load_lang_src(src.iso1)
    if dst and dst.count > 0:
        load_lang_dst(dst.iso1)

    box = m.OCRBoxModel.objects.annotate(count=Count('box_runs')).order_by('-count').first()
    ocr = m.OCRModel.objects.annotate(count=Count('ocr_runs')).order_by('-count').first()
    tsl = m.TSLModel.objects.annotate(count=Count('tsl_runs')).order_by('-count').first()

    if box and box.count > 0:
        load_box_model(box.name)
    if ocr and ocr.count > 0:
        load_ocr_model(ocr.name)
    if tsl and tsl.count > 0:
        load_tsl_model(tsl.name)

def init_last_used():
    """Initialize the server with the most used languages and models."""
    logger.info('Initializing server with the last used languages and models')
    src = m.Language.get_last_loaded_src()
    dst = m.Language.get_last_loaded_dst()

    box = m.OCRBoxModel.get_last_loaded()
    ocr = m.OCRModel.get_last_loaded()
    tsl = m.TSLModel.get_last_loaded()

    if src:
        load_lang_src(src.iso1)
    else:
        logger.warning('No last source language found')
    if dst:
        load_lang_dst(dst.iso1)
    else:
        logger.warning('No last destination language found')
    if box:
        load_box_model(box.name)
    else:
        logger.warning('No last box model found')
    if ocr:
        load_ocr_model(ocr.name)
    else:
        logger.warning('No last OCR model found')
    if tsl:
        load_tsl_model(tsl.name)
    else:
        logger.warning('No last TSL model found')

def auto_create_languages():
    """Create Language objects from json file."""
    lang_file = resources.files('ocr_translate.ocr_tsl').joinpath('languages.json')
    with lang_file.open(encoding='utf-8') as f:
        langs = json.load(f)

    for lang in langs:
        logger.debug(f'Creating language: {lang}')
        name = lang.pop('name')
        iso1 = lang.pop('iso1')
        iso2t = lang.pop('iso2t')
        iso2b = lang.pop('iso2b')
        iso3 = lang.pop('iso3')
        def_opt = lang.pop('default_options', {})
        opt_obj, _ = m.OptionDict.objects.get_or_create(options=def_opt)
        l, _ = m.Language.objects.get_or_create(name=name, iso1=iso1, iso2t=iso2t, iso2b=iso2b, iso3=iso3)
        l.default_options = opt_obj
        # for k,v in lang.items():
        #     setattr(l, k, v)
        l.save()

    m.OptionDict.objects.get_or_create(options={})

def load_ept_data(namespace):
    """Load all entrypoints from a namespace into a list"""
    return[_.load() for _ in entry_points(group=namespace)]

# Pop and set after so that running this after a migration should modify the existing model (with less
# attributes) instead of creating a new one
def add_box_model(ep_dict: dict) -> m.OCRBoxModel:
    """Create OCRBoxModel object from dict."""
    ep_dict = ep_dict.copy()
    logger.debug(f'Creating box model: {ep_dict}')
    lang = ep_dict.pop('lang')
    lcode = ep_dict.pop('lang_code')
    entrypoint = ep_dict.pop('entrypoint')
    iso1_map = ep_dict.pop('iso1_map', {})
    def_opt = ep_dict.pop('default_options', {})
    opt_obj, _ = m.OptionDict.objects.get_or_create(options=def_opt)
    model, _ = m.OCRBoxModel.objects.get_or_create(**ep_dict)
    model.default_options = opt_obj
    model.entrypoint = entrypoint
    model.language_format = lcode
    model.iso1_map = iso1_map
    model.languages.clear()
    for l in lang:
        model.languages.add(m.Language.objects.get(iso1=l))
    model.save()
    return model

def add_ocr_model(ep_dict: dict) -> m.OCRModel:
    """Create OCRModel object from dict."""
    ep_dict = ep_dict.copy()
    logger.debug(f'Creating ocr model: {ep_dict}')
    lang = ep_dict.pop('lang')
    lcode = ep_dict.pop('lang_code')
    ocr_mode = ep_dict.pop('ocr_mode', m.OCRModel.MERGED)
    entrypoint = ep_dict.pop('entrypoint')
    iso1_map = ep_dict.pop('iso1_map', {})
    def_opt = ep_dict.pop('default_options', {})
    opt_obj, _ = m.OptionDict.objects.get_or_create(options=def_opt)
    model, _ = m.OCRModel.objects.get_or_create(**ep_dict)
    model.default_options = opt_obj
    model.language_format = lcode
    model.ocr_mode = ocr_mode
    model.iso1_map = iso1_map
    model.entrypoint = entrypoint
    model.languages.clear()
    for l in lang:
        model.languages.add(m.Language.objects.get(iso1=l))
    model.save()
    return model

def add_tsl_model(ep_dict: dict) -> m.TSLModel:
    """Create TSLModel object from dict."""
    ep_dict = ep_dict.copy()
    logger.debug(f'Creating tsl model: {ep_dict}')
    src = ep_dict.pop('lang_src', [])
    dst = ep_dict.pop('lang_dst', [])
    lcode = ep_dict.pop('lang_code', None)
    entrypoint = ep_dict.pop('entrypoint', None)
    iso1_map = ep_dict.pop('iso1_map', {})
    def_opt = ep_dict.pop('default_options', {})
    opt_obj, _ = m.OptionDict.objects.get_or_create(options=def_opt)
    model, _ = m.TSLModel.objects.get_or_create(**ep_dict)
    model.default_options = opt_obj
    model.language_format = lcode
    model.iso1_map = iso1_map
    model.entrypoint = entrypoint
    model.src_languages.clear()
    for l in src:
        logger.debug(f'Adding src language: {l}')
        kwargs = {lcode: l}
        model.src_languages.add(*m.Language.objects.filter(**kwargs))

    model.dst_languages.clear()
    for l in dst:
        logger.debug(f'Adding dst language: {l}')
        kwargs = {lcode: l}
        model.dst_languages.add(*m.Language.objects.filter(**kwargs))
    model.save()
    return model

def ensure_plugins():
    """Ensure that all plugins are installed on initialization.
    This is used to make sure that running the server with a new DEVICE will have the correct dependencies installed."""
    logger.info('Ensuring that all plugins are loaded')
    pmng = PluginManager()
    known = set(_['name'] for _ in pmng.plugins_data)
    installed = set(pmng.plugins)
    for plugin in known:
        if plugin in installed:
            pmng.install_plugin(plugin)
