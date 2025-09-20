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

from .. import entrypoint_manager as epm
from .. import models as m
from ..plugin_manager import PluginManager

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
        m.Language.load_model_src(src.iso1)
    if dst and dst.count > 0:
        m.Language.load_model_dst(dst.iso1)

    box = m.OCRBoxModel.objects.annotate(count=Count('box_runs')).order_by('-count').first()
    ocr = m.OCRModel.objects.annotate(count=Count('ocr_runs')).order_by('-count').first()
    tsl = m.TSLModel.objects.annotate(count=Count('tsl_runs')).order_by('-count').first()

    if box and box.count > 0:
        m.OCRBoxModel.load_model(box.name)
    if ocr and ocr.count > 0:
        m.OCRModel.load_model(ocr.name)
    if tsl and tsl.count > 0:
        m.TSLModel.load_model(tsl.name)

def init_last_used():
    """Initialize the server with the most used languages and models."""
    logger.info('Initializing server with the last used languages and models')
    src = m.Language.get_last_loaded_src()
    dst = m.Language.get_last_loaded_dst()

    box = m.OCRBoxModel.get_last_loaded()
    ocr = m.OCRModel.get_last_loaded()
    tsl = m.TSLModel.get_last_loaded()

    if src:
        m.Language.load_model_src(src.iso1)
    else:
        logger.warning('No last source language found')
    if dst:
        m.Language.load_model_dst(dst.iso1)
    else:
        logger.warning('No last destination language found')
    if box:
        m.OCRBoxModel.load_model(box.name)
    else:
        logger.warning('No last box model found')
    if ocr:
        m.OCRModel.load_model(ocr.name)
    else:
        logger.warning('No last OCR model found')
    if tsl:
        m.TSLModel.load_model(tsl.name)
    else:
        logger.warning('No last TSL model found')

def auto_create_languages():
    """Create Language objects from json file."""
    lang_file = resources.files('ocr_translate.ocr_tsl').joinpath('languages.json')
    with lang_file.open(encoding='utf-8') as f:
        langs = json.load(f)

    for lang in langs:
        m.Language.from_dct(lang)

    m.OptionDict.objects.get_or_create(options={})

def load_ept_data(namespace):
    """Load all entrypoints from a namespace into a list"""
    return[_.load() for _ in entry_points(group=namespace)]

def ensure_plugins():
    """Ensure that all plugins are installed on initialization.
    This is used to make sure that running the server with a new DEVICE will have the correct dependencies installed."""
    #pylint: disable=import-outside-toplevel,cyclic-import
    from ..entrypoint_manager import ep_manager
    logger.info('Ensuring that all plugins are loaded')
    pmng = PluginManager()
    known = set(_['name'] for _ in pmng.plugins_data)
    installed = set(pmng.managed_plugins)
    for plugin in known & installed:
        with ep_manager():
            pmng.install_plugin(plugin)

def sync_models_epts():
    """Deactivate models that are in the database but whose entrypoint is no longer available."""
    for group, cls in epm.GROUPS.items():
        ept_data = load_ept_data(group)
        names_ep = set(_['name'] for _ in ept_data)

        # Deactivate models that do not have an entrypoint anymore
        q = cls.objects
        names_db_on = set(q.filter(active=True).values_list('name', flat=True))
        removed = names_db_on - names_ep
        for name in removed:
            model = cls.objects.get(name=name)
            model.deactivate()
            logger.info(f'Deactivated {cls.__name__:>12s} `{name}` as its entrypoint is no longer available')

        for model_data in ept_data:
            cls.from_dct(model_data)

def deprecate_los_true():
    """Deprecate the environment variable `LOAD_ON_START=true`."""
    logger.warning('The environment variable `LOAD_ON_START=true` is deprecated (defaults to `most`).')
    logger.warning('Use `LOAD_ON_START=most` or `LOAD_ON_START=last` instead.')
    init_most_used()

TRUE_VALUES = ('true', 't', '1')
FALSE_VALUES = ('false', 'f', '0')
RUN_ON_ENV_INIT = {
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
