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
import json
import logging
from typing import Union

import numpy as np
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.middleware import csrf
from django.views.decorators.csrf import csrf_exempt
from PIL import Image

from . import __version__array__
from . import models as m
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
from .queues import main_queue as q
from .tries import load_trie_src

logger = logging.getLogger('ocr.general')


def post_data_converter(request: HttpRequest) -> dict:
    """Convert POST data to a dict."""
    if request.content_type == 'application/json':
        return json.loads(request.body)

    raise ValueError('invalid content type')


def handshake(request: HttpRequest) -> JsonResponse:
    """Handshake with the client."""
    if not request.method == 'GET':
        return JsonResponse({'error': f'{request.method} not allowed'}, status=405)

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
def set_models(request: HttpRequest) -> JsonResponse:
    """Handle a POST request to load models.
    Expected data:
    {
        'box_model_id': 'id',
        'ocr_model_id': 'id',
        'tsl_model_id': 'id',
    }
    """
    if request.method == 'POST':
        try:
            data = post_data_converter(request)
        except ValueError:
            return JsonResponse({'error': 'invalid content type'}, status=400)

        logger.info(f'LOAD MODELS: {data}')

        box_model_id = data.pop('box_model_id', None)
        ocr_model_id = data.pop('ocr_model_id', None)
        tsl_model_id = data.pop('tsl_model_id', None)

        if len(data) > 0:
            return JsonResponse({'error': f'invalid data: {data}'}, status=400)

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
    return JsonResponse({'error': f'{request.method} not allowed'}, status=405)

@csrf_exempt
def set_lang(request: HttpRequest) -> JsonResponse:
    """Handle a POST request to set languages.
    Expected data:
    {
        'lang_src': 'id',
        'lang_dst': 'id',
    }
    """
    if request.method != 'POST':
        return JsonResponse({'error': f'{request.method} not allowed'}, status=405)

    try:
        data = post_data_converter(request)
    except ValueError:
        return JsonResponse({'error': 'invalid content type'}, status=400)
    logger.info(f'SET LANG: {data}')

    lang_src = data.pop('lang_src', None)
    lang_dst = data.pop('lang_dst', None)
    if lang_src is None:
        return JsonResponse({'error': 'no lang_src'}, status=400)
    if lang_dst is None:
        return JsonResponse({'error': 'no lang_dst'}, status=400)
    if len(data) > 0:
        return JsonResponse({'error': f'invalid data: {data}'}, status=400)

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
def run_tsl(request: HttpRequest) -> JsonResponse:
    """Handle a POST request to run translation.
    Expected data:
    {
        'text': 'text',
    }
    """
    if request.method != 'POST':
        return JsonResponse({'error': f'{request.method} not allowed'}, status=405)

    try:
        data = post_data_converter(request)
    except ValueError:
        return JsonResponse({'error': 'invalid content type'}, status=400)

    text = data.pop('text', None)
    if text is None:
        return JsonResponse({'error': 'no text'}, status=400)
    if len(data) > 0:
        return JsonResponse({'error': f'invalid data: {data}'}, status=400)

    tsl_model = get_tsl_model()


    src_obj, _ = m.Text.objects.get_or_create(text=text)
    dst_obj = tsl_model.translate(src_obj, get_lang_src(), get_lang_dst())
    dst_obj = next(dst_obj)

    return JsonResponse({
        'text': dst_obj.text,
        })

def run_tsl_get_xunityautotrans(request: HttpRequest) -> JsonResponse:
    """Handle a GET request to run translation.
    Expected parameters:
    {
        'text': 'text',
    }
    """
    if request.method != 'GET':
        return JsonResponse({'error': f'{request.method} not allowed'}, status=405)

    try:
        data = request.GET.dict()
    except ValueError:
        return JsonResponse({'error': 'invalid content type'}, status=400)

    text = data.pop('text', None)
    if text is None:
        return JsonResponse({'error': 'no text'}, status=404)

    tsl_model = get_tsl_model()


    src_obj, _ = m.Text.objects.get_or_create(text=text)
    dst_obj = tsl_model.translate(src_obj, get_lang_src(), get_lang_dst())
    dst_obj = next(dst_obj)

    return HttpResponse(dst_obj.text)

@csrf_exempt
def run_ocrtsl(request: HttpRequest) -> JsonResponse:
    """Handle a POST request to run OCR and translation.
    Expected data:
    {
        'contents': 'base64',
        'md5': 'md5',
        'force': 'bool',
        'options': 'dict',
    }
    """
    if request.method != 'POST':
        return JsonResponse({'error': f'{request.method} not allowed'}, status=405)

    try:
        data = post_data_converter(request)
    except ValueError:
        return JsonResponse({'error': 'invalid content type'}, status=400)

    b64 = data.pop('contents', None)
    md5 = data.pop('md5', None)
    frc = data.pop('force', False)
    opt = data.pop('options', {})

    opt = {
        **opt.get(get_box_model().name if get_box_model() else None, {}),
        **opt.get(get_ocr_model().name if get_ocr_model() else None, {}),
        **opt.get(get_tsl_model().name if get_tsl_model() else None, {}),
    }

    if md5 is None:
        return JsonResponse({'error': 'no md5'}, status=400)
    if len(data) > 0:
        return JsonResponse({'error': f'invalid data: {data}'}, status=400)

    if b64 is None:
        logger.info('No contents, trying to lazyload')
        if frc:
            return JsonResponse({'error': 'Cannot force ocr without contents'}, status=400)
        try:
            res = ocr_tsl_pipeline_lazy(md5, options=opt)
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
        lang_src = get_lang_src()
        lang_dst = get_lang_dst()
        box_model = get_box_model()
        ocr_model = get_ocr_model()
        tsl_model = get_tsl_model()
        options, _ = m.OptionDict.objects.get_or_create(options=opt)

        try:
            id_ = (md5, lang_src.id, lang_dst.id, box_model.id, ocr_model.id, tsl_model.id, options.id)
        except AttributeError:
            return JsonResponse({'error': 'No models selected'}, status=400)

        msg = q.put(
            id_ = id_,
            msg = {
                'args': (img, md5),
                'kwargs': {'force': frc, 'options': opt},
            },
            handler = ocr_tsl_pipeline_work,
        )

        res = msg.response()


    return JsonResponse({
        'result': res,
        })


@csrf_exempt
def get_translations(request: HttpRequest) -> JsonResponse:
    """Handle a GET request to get translations.
    Expected parameters:
    {
        'text': 'text',
    }
    """
    if request.method != 'GET':
        return JsonResponse({'error': f'{request.method} not allowed'}, status=405)

    params = request.GET.dict()
    text = params.pop('text', None)

    if len(params) > 0:
        return JsonResponse({'error': f'invalid data: {params}'}, status=400)
    if text is None:
        return JsonResponse({'error': 'no text'}, status=400)

    text_obj = m.Text.objects.filter(text=text).first()
    if text_obj is None:
        return JsonResponse({'error': 'text not found'}, status=404)

    translations = text_obj.to_trans.filter(
        lang_src=get_lang_src(),
        lang_dst=get_lang_dst(),
        )
    return JsonResponse({
        'translations': [{
            'model': str(_.model),
            'text': _.result.text,
            } for _ in translations],
        })

@csrf_exempt
def set_manual_translation(request: HttpRequest) -> JsonResponse:
    """Handle a POST request to apply a manual translation.
    Expected data:
    {
        'text': 'text',
        'translation': 'translation',
    }
    """
    if request.method != 'POST':
        return JsonResponse({'error': f'{request.method} not allowed'}, status=405)

    try:
        data = post_data_converter(request)
    except ValueError:
        return JsonResponse({'error': 'invalid content type'}, status=400)

    text = data.pop('text', None)
    translation = data.pop('translation', None)
    if text is None:
        return JsonResponse({'error': 'no text'}, status=400)
    if translation is None:
        return JsonResponse({'error': 'no translation'}, status=400)
    if len(data) > 0:
        return JsonResponse({'error': f'invalid data: {data}'}, status=400)

    text_obj = m.Text.objects.filter(text=text).first()
    if text_obj is None:
        return JsonResponse({'error': 'text not found'}, status=404)

    manual_model = m.TSLModel.objects.filter(name='manual').first()
    params = {
        'model': manual_model,
        'text': text_obj,
        'lang_src': get_lang_src(),
        'lang_dst': get_lang_dst(),
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
    """    """"""
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

def get_active_options(request: HttpRequest) -> JsonResponse:
    """Handle a GET request to get active options."""
    if request.method != 'GET':
        return JsonResponse({'error': f'{request.method} not allowed'}, status=405)

    params = request.GET.dict()
    if len(params) > 0:
        return JsonResponse({'error': f'invalid data: {params}'}, status=400)

    res = {}
    for typ,model in [
        ('box_model', get_box_model()),
        ('ocr_model', get_ocr_model()),
        ('tsl_model', get_tsl_model()),
        ]:
        ptr = res.setdefault(typ, {})
        if model is None:
            continue
            # return JsonResponse({'error': 'No models selected'}, status=400)

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
