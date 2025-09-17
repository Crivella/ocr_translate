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
import os
from importlib import resources
from importlib.metadata import entry_points
from typing import Callable

from django.db.models import Count
from django.db.utils import OperationalError

from .. import models as m
from ..plugin_manager import PluginManager
from .box import load_box_model
from .lang import load_lang_dst, load_lang_src
from .ocr import load_ocr_model
from .tsl import load_tsl_model

logger = logging.getLogger('ocr.general')

def run_on_env(env_name: str, func_map: dict[str, Callable]):
    """Run a function if the environment variable is set."""
    if env_name in os.environ:
        value = os.environ.get(env_name).lower()
        for key, func in func_map.items():
            if isinstance(key, str):
                key = key.lower()
                if key.lower() == value:
                    break
            elif isinstance(key, tuple):
                if any(k.lower() == value for k in key):
                    break
            else:
                raise ValueError(f'Invalid use of `run_on_env`: key `{key}` is not a string or tuple')
        else:
            logger.warning('Unknown value for environment variable `{env_name}`: {value}... Doing nothing')
            func = None

        if func is None:
            return

        try:
            func()
            logger.info(f'Ran `{func.__name__}` based on environment variable `{env_name}`')
        except OperationalError:
            msg = f'Ignoring environment variable `{env_name}` as the database is not ready/migrated.'
            logger.warning(msg)

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
    lang = ep_dict.pop('lang', [])
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
    lang = ep_dict.pop('lang', [])
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
    #pylint: disable=import-outside-toplevel,cyclic-import
    from ..entrypoint_manager import ep_manager
    logger.info('Ensuring that all plugins are loaded')
    pmng = PluginManager()
    known = set(_['name'] for _ in pmng.plugins_data)
    installed = set(pmng.plugins)
    for plugin in known & installed:
        with ep_manager():
            pmng.install_plugin(plugin)

def deactivate_missing_models():
    """Deactivate models that are in the database but whose entrypoint is no longer available."""
    for cls, group in [
        (m.OCRBoxModel, 'ocr_translate.box_data'),
        (m.OCRModel, 'ocr_translate.ocr_data'),
        (m.TSLModel, 'ocr_translate.tsl_data'),
        ]:
        q = cls.objects.filter(active=True)
        names_db = set(q.values_list('name', flat=True))
        names_ep = set(_['name'] for _ in load_ept_data(group))
        removed = names_db - names_ep
        for name in removed:
            model = cls.objects.get(name=name)
            model.active = False
            model.save()
            logger.info(f'Deactivated box model `{name}` as its entrypoint is no longer available')

def auto_create_box():
    """Create OCRBoxModel objects from entrypoints."""
    for box in load_ept_data('ocr_translate.box_data'):
        model = add_box_model(box)
        model.active = True
        model.save()

def auto_create_ocr():
    """Create OCRModel objects from entrypoints."""
    for ocr in load_ept_data('ocr_translate.ocr_data'):
        model = add_ocr_model(ocr)
        model.active = True
        model.save()

def auto_create_tsl():
    """Create TSLModel objects from entrypoints."""
    for tsl in load_ept_data('ocr_translate.tsl_data'):
        model = add_tsl_model(tsl)
        model.active = True
        model.save()

def auto_create_models():
    """Create OCR and TSL models from json file. Also create default OptionDict"""
    logger.info('Creating default models')
    auto_create_box()
    auto_create_ocr()
    auto_create_tsl()

    m.OptionDict.objects.get_or_create(options={})

def deprecate_los_true():
    """Deprecate the environment variable `LOAD_ON_START=true`."""
    logger.warning('The environment variable `LOAD_ON_START=true` is deprecated (defaults to `most`).')
    logger.warning('Use `LOAD_ON_START=most` or `LOAD_ON_START=last` instead.')
    init_most_used()

TRUE_VALUES = ('true', 't', '1')
FALSE_VALUES = ('false', 'f', '0')
RUN_ON_ENV_INIT = {
    'AUTOCREATE_LANGUAGES': {
        TRUE_VALUES: auto_create_languages,
        FALSE_VALUES: None,
    },
    # Re-added to give a way to install plugin independently and still add the models from the entrypoints
    'AUTOCREATE_MODELS': {
        TRUE_VALUES: auto_create_models,
        FALSE_VALUES: None,
    },
    'LOAD_ON_START': {
        'most': init_most_used,
        'last': init_last_used,
        TRUE_VALUES: deprecate_los_true,
        FALSE_VALUES: None
    }
}

def env_var_init():
    """Run initializations based on environment variables."""
    for env, func_map in RUN_ON_ENV_INIT.items():
        run_on_env(env, func_map)
