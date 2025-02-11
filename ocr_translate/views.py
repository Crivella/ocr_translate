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
"""Django views for the ocr_translate app."""
# pylint: disable=too-many-return-statements
import base64
import hashlib
import io
import logging
import traceback
from typing import Union

import numpy as np
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.middleware import csrf
from django.views.decorators.csrf import csrf_exempt
from PIL import Image

from . import __version__array__
from . import models as m
from .entrypoint_manager import ep_manager
from .ocr_tsl.box import get_box_model, load_box_model, unload_box_model
from .ocr_tsl.cached_lists import (get_all_lang_dst, get_all_lang_src,
                                   get_allowed_box_models,
                                   get_allowed_ocr_models,
                                   get_allowed_tsl_models)
from .ocr_tsl.full import ocr_tsl_pipeline_lazy, ocr_tsl_pipeline_work
from .ocr_tsl.lang import (get_lang_dst, get_lang_src, load_lang_dst,
                           load_lang_src)
from .ocr_tsl.ocr import get_ocr_model, load_ocr_model, unload_ocr_model
from .ocr_tsl.tsl import get_tsl_model, load_tsl_model, unload_tsl_model
from .plugin_manager import PluginManager
from .queues import main_queue as q
from .request_decorators import (get_backend_langs, get_backend_models,
                                 get_data_deserializer, method_or_405,
                                 post_data_deserializer, use_lock,
                                 wait_for_lock)
from .tries import load_trie_src

logger = logging.getLogger('ocr.general')

PMNG = PluginManager()


@method_or_405(['GET'])
def handshake(request: HttpRequest) -> JsonResponse:
    """Handshake with the client."""
    csrf.get_token(request)

    logger.debug(f'Handshake: {str(get_ocr_model())}, {str(get_tsl_model())}')
    lang_src = get_lang_src()
    lang_dst = get_lang_dst()

    languages = get_all_lang_src()
    languages_src = get_all_lang_src()
    languages_dst = get_all_lang_dst()

    box_models = get_allowed_box_models()
    ocr_models = get_allowed_ocr_models()
    tsl_models = get_allowed_tsl_models()

    box_model = get_box_model() or ''
    ocr_model = get_ocr_model() or ''
    tsl_model = get_tsl_model() or ''

    lang_src = getattr(lang_src, 'iso1', None) or ''
    lang_dst = getattr(lang_dst, 'iso1', None) or ''

    res = JsonResponse({
        'version': __version__array__,
        'Languages': [_.iso1 for _ in languages_src],
        'Languages_src': [_.iso1 for _ in languages_src],
        'Languages_dst': [_.iso1 for _ in languages_dst],
        'Languages_hr': [_.name for _ in languages],
        'BOXModels': [str(_) for _ in box_models],
        'OCRModels': [str(_) for _ in ocr_models],
        'TSLModels': [str(_) for _ in tsl_models],

        'box_selected': str(box_model),
        'ocr_selected': str(ocr_model),
        'tsl_selected': str(tsl_model),
        'lang_src': lang_src,
        'lang_dst': lang_dst,
        })

    # res['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
    # res['Access-Control-Allow-Credentials'] = 'true'

    return res

@csrf_exempt
@method_or_405(['POST'])
@post_data_deserializer(['box_model_id', 'ocr_model_id', 'tsl_model_id'], required=False)
@wait_for_lock('plugin')
@use_lock('block_plugin_changes', blocking=False)
def set_models(request: HttpRequest, box_model_id, ocr_model_id, tsl_model_id) -> JsonResponse:
    """Handle a POST request to load models.
    Expected data:
    {
        'box_model_id': 'id',
        'ocr_model_id': 'id',
        'tsl_model_id': 'id',
    }
    """
    logger.info(f'LOAD MODELS: {box_model_id}, {ocr_model_id}, {tsl_model_id}')

    try:
        if not box_model_id is None and not box_model_id == '':
            load_box_model(box_model_id)
        if not ocr_model_id is None and not ocr_model_id == '':
            load_ocr_model(ocr_model_id)
        if not tsl_model_id is None and not tsl_model_id == '':
            load_tsl_model(tsl_model_id)
    except Exception as exc:
        logger.error(f'Failed to load models: {exc}')
        return JsonResponse({'error': str(exc)}, status=400)

    return JsonResponse({})

@csrf_exempt
@method_or_405(['POST'])
@post_data_deserializer(['lang_src', 'lang_dst'], required=True)
def set_lang(request: HttpRequest, lang_src, lang_dst) -> JsonResponse:
    """Handle a POST request to set languages.
    Expected data:
    {
        'lang_src': 'id',
        'lang_dst': 'id',
    }
    """
    logger.info(f'SET LANG: {lang_src}, {lang_dst}')

    old_src = get_lang_src()
    old_dst = get_lang_dst()
    try:
        load_lang_src(lang_src)
        load_lang_dst(lang_dst)
        load_trie_src(lang_src)
        # load_trie_dst(lang_dst)
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    new_src = get_lang_src()
    new_dst = get_lang_dst()

    check1 = old_src != new_src
    check2 = old_dst != new_dst
    if check1 or check2:
        tsl_model = get_tsl_model()
        if (
            not tsl_model is None and
            (
                new_src not in tsl_model.src_languages.all() or
                new_dst not in tsl_model.dst_languages.all()
            )):
            unload_tsl_model()
    if check1:
        box_model = get_box_model()
        ocr_model = get_ocr_model()
        if not box_model is None and (new_src not in box_model.languages.all()):
            unload_box_model()
        if not ocr_model is None and (new_src not in ocr_model.languages.all()):
            unload_ocr_model()
    # if check2:
    #     pass

    return JsonResponse({})

@csrf_exempt
@method_or_405(['POST'])
@post_data_deserializer(['text'], required=True)
@get_backend_langs(strict=True)
@get_backend_models(strict=True)
@wait_for_lock('plugin')
@use_lock('block_plugin_changes', blocking=False)
def run_tsl(request: HttpRequest, text, tsl_model: m.TSLModel, **kwargs) -> JsonResponse:
    """Handle a POST request to run translation.
    Expected data:
    {
        'text': 'text',
    }
    """
    src_obj, _ = m.Text.objects.get_or_create(text=text)
    dst_obj = tsl_model.translate(src_obj, get_lang_src(), get_lang_dst())
    dst_obj = next(dst_obj)

    return JsonResponse({
        'text': dst_obj.text,
        })

@method_or_405(['GET'])
@get_backend_langs(strict=True)
@get_backend_models(strict=True)
@get_data_deserializer(['text'], required=True)
@wait_for_lock('plugin')
@use_lock('block_plugin_changes', blocking=False)
def run_tsl_get_xunityautotrans(
    request: HttpRequest, tsl_model: m.TSLModel, text: str,
    lang_src: m.Language, lang_dst: m.Language, **kwargs
    ) -> JsonResponse:
    """Handle a GET request to run translation.
    Expected parameters:
    {
        'text': 'text',
    }
    """
    src_obj, _ = m.Text.objects.get_or_create(text=text)
    dst_obj = tsl_model.translate(src_obj, lang_src, lang_dst)
    dst_obj = next(dst_obj)

    return HttpResponse(dst_obj.text)

@csrf_exempt
@method_or_405(['POST'])
@get_backend_langs(strict=True)
@get_backend_models(strict=True)
@post_data_deserializer(['contents', 'md5', 'force', 'options'], required=False)
@wait_for_lock('plugin')
@use_lock('block_plugin_changes', blocking=False)
def run_ocrtsl(  # pylint: disable=too-many-locals
    request: HttpRequest,
    lang_src: m.Language, lang_dst: m.Language,
    box_model: m.OCRBoxModel, ocr_model: m.OCRModel, tsl_model: m.TSLModel,
    contents: str, md5: str, force: bool, options: dict,
    ) -> JsonResponse:
    """Handle a POST request to run OCR and translation.
    Expected data:
    {
        'contents': 'base64',
        'md5': 'md5',
        'force': 'bool',
        'options': 'dict',
    }
    """
    b64 = contents
    frc = force
    opt = options or {}

    opt_box = opt.get(box_model.name if box_model else None, {})
    opt_ocr = opt.get(ocr_model.name if ocr_model else None, {})
    opt_tsl = opt.get(tsl_model.name if tsl_model else None, {})

    options_box, _ = m.OptionDict.objects.get_or_create(options=opt_box)
    options_ocr, _ = m.OptionDict.objects.get_or_create(options=opt_ocr)
    options_tsl, _ = m.OptionDict.objects.get_or_create(options=opt_tsl)

    if b64 is None:
        logger.info('No contents, trying to lazyload')
        if frc:
            return JsonResponse({'error': 'Cannot force ocr without contents'}, status=400)
        try:
            res = ocr_tsl_pipeline_lazy(
                md5,
                options_box=options_box,
                options_ocr=options_ocr,
                options_tsl=options_tsl,
                )
        except ValueError:
            logger.info('Failed to lazyload ocr')
            return JsonResponse({'error': 'Failed to lazyload ocr'}, status=406)
    else:
        binary = base64.b64decode(b64)
        # Doing md5 on the base64 to have consistency with the JS generate one
        # Can't find a way to run md5 on the binary in JS (the blob does not work)
        if md5 != hashlib.md5(b64.encode('utf-8')).hexdigest():
            return JsonResponse({'error': 'md5 mismatch'}, status=400)
        logger.debug(f'md5 {md5} <- {len(binary)} bytes')

        img = Image.open(io.BytesIO(binary))
        # Needed to make sure the image is loaded synchronously before going forward
        # Enforce thread safety. Maybe there is a way to do it without numpy?
        np.array(img)

        # Check if same request is already in queue. If yes attach listener to it
        id_ = (
            md5,
            lang_src.id, lang_dst.id,
            box_model.id, ocr_model.id, tsl_model.id,
            options_box.id, options_ocr.id, options_tsl.id,
            )

        msg = q.put(
            id_ = id_,
            msg = {
                'args': (img, md5),
                'kwargs': {
                    'force': frc,
                    # 'options': opt,
                    'options_box': options_box,
                    'options_ocr': options_ocr,
                    'options_tsl': options_tsl,
                    },
            },
            handler = ocr_tsl_pipeline_work,
        )

        res = msg.response()

        if isinstance(res, Exception):
            logger.error(f'Failed to run ocr: {res}')
            logger.debug(traceback.print_exception(type(res), res, res.__traceback__))
            return JsonResponse({'error': str(res)}, status=500)


    return JsonResponse({
        'result': res,
        })


@csrf_exempt
@method_or_405(['GET'])
@get_backend_langs(strict=True)
@get_data_deserializer(['text'], required=True)
def get_translations(
    request: HttpRequest,
    lang_src: m.Language, lang_dst: m.Language,
    text: str,
    ) -> JsonResponse:
    """Handle a GET request to get translations.
    Expected parameters:
    {
        'text': 'text',
    }
    """
    text_obj = m.Text.objects.filter(text=text).first()
    if text_obj is None:
        return JsonResponse({'error': 'text not found'}, status=404)

    translations = text_obj.to_trans.filter(
        lang_src=lang_src,
        lang_dst=lang_dst,
        )
    return JsonResponse({
        'translations': [{
            'model': str(_.model),
            'text': _.result.text,
            } for _ in translations],
        })

@csrf_exempt
@method_or_405(['POST'])
@get_backend_langs(strict=True)
@post_data_deserializer(['text', 'translation'], required=True)
def set_manual_translation(
    request: HttpRequest,
    lang_src: m.Language, lang_dst: m.Language,
    text: str, translation: str,
    ) -> JsonResponse:
    """Handle a POST request to apply a manual translation.
    Expected data:
    {
        'text': 'text',
        'translation': 'translation',
    }
    """
    text_obj = m.Text.objects.filter(text=text).first()
    if text_obj is None:
        return JsonResponse({'error': 'text not found'}, status=404)

    manual_model = m.TSLModel.objects.filter(name='manual').first()
    params = {
        'model': manual_model,
        'text': text_obj,
        'lang_src': lang_src,
        'lang_dst': lang_dst,
        'options': m.OptionDict.objects.get(options={}),
    }

    tsl_run_obj = m.TranslationRun.objects.filter(**params).first()
    if tsl_run_obj is None:
        res_obj, _ = m.Text.objects.get_or_create(text=translation)
        params['result'] = res_obj
        tsl_run_obj = m.TranslationRun.objects.create(**params)
    else:
        tsl_run_obj.result.text = translation
        tsl_run_obj.result.save()

    return JsonResponse({})

def get_default_options_from_cascade(
        objects: list[Union[str, 'm.OptionDict']], option: str, default: Union[int, float, str, bool] = None
        ) -> Union[int, float, str, bool]:
    """Get the default value of an option from a cascade of objects.

    Args:
        objects (list[Union[str, OptionDict]]): List of option objects or string identifying a model type.
        option (str): Name of the option to get.
        default (Union[int, float, str, bool], optional): Default value to return for the option. Defaults to None.

    Raises:
        ValueError: Invalid string in objects list.
        TypeError: Invalid type in objects list.

    Returns:
        Union[int, float, str, bool]: The default value of the option.
    """
    res = default
    for obj in objects:
        if obj is None:
            continue
        if isinstance(obj, m.OptionDict):
            res = obj.options.get(option, res)
        elif isinstance(obj, str):
            if obj == 'lang_src':
                model = get_lang_src()
            elif obj == 'lang_dst':
                model = get_lang_dst()
            elif obj == 'box_model':
                model = get_box_model()
            elif obj == 'ocr_model':
                model = get_ocr_model()
            elif obj == 'tsl_model':
                model = get_tsl_model()
            else:
                raise ValueError(f'Unknown option cascade object: {obj}')
            res = model.default_options.options.get(option, res)
        else:
            raise TypeError(f'Cannot get default options from {type(obj)}')
    return res

@method_or_405(['GET'])
@get_backend_models(strict=False)
@get_data_deserializer([], required=False)
@wait_for_lock('plugin')
@use_lock('block_plugin_changes', blocking=False)
def get_active_options(
    request: HttpRequest,
    box_model: m.OCRBoxModel, ocr_model: m.OCRModel, tsl_model: m.TSLModel,
    ) -> JsonResponse:
    """Handle a GET request to get active options."""
    res = {}
    for typ,model in [
        ('box_model', box_model),
        ('ocr_model', ocr_model),
        ('tsl_model', tsl_model),
        ]:
        ptr = res.setdefault(typ, {})
        if model == '':
            continue

        for opt,val in model.ALLOWED_OPTIONS.items():
            val = val.copy()
            ptr[opt] = val
            default = val['default']
            if isinstance(default, tuple):
                if default[0] == 'cascade':
                    default = get_default_options_from_cascade(default[1], opt, default[2])
                    default = val['type'](default)
                    val['default'] = default
                else:
                    raise ValueError(f'Unknown default action type: {default[0]}')
            val['type'] = val['type'].__name__

    return JsonResponse({'options': res})

@method_or_405(['GET'])
@wait_for_lock('plugin')
@use_lock('block_plugin_changes', blocking=False)
def get_plugin_data(request: HttpRequest) -> JsonResponse:
    """Handle a GET request to get plugins."""
    resp = {}
    tpl = {
        'homepage': None,
        'warning': None,
        'description': None,
    }
    for plugin in PMNG.plugins_data:
        ptr = {**tpl, **plugin}
        name = ptr.pop('name')
        ptr.pop('dependencies', None)
        ptr['installed'] = name in PMNG.plugins
        resp[name] = ptr
    return JsonResponse(resp)

@csrf_exempt
@method_or_405(['POST'])
@post_data_deserializer(['plugins'], required=True)
@use_lock('plugin', blocking=True)
@use_lock('block_plugin_changes', blocking=True)
def manage_plugins(request: HttpRequest, plugins: dict[str, bool]) -> JsonResponse:
    """Handle a POST request to install a plugin."""
    logger.debug(f'Manage plugins: {plugins}')
    with ep_manager():
        for plugin, present in plugins.items():
            if present:
                PMNG.install_plugin(plugin)
            else:
                PMNG.uninstall_plugin(plugin)
    return JsonResponse({})
