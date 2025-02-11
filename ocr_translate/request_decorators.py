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
"""Decorators to preparse requests and responses."""

import json
import time
from functools import wraps
from threading import Lock

from django.http import HttpRequest, JsonResponse

from .ocr_tsl.box import get_box_model
from .ocr_tsl.lang import get_lang_dst, get_lang_src
from .ocr_tsl.ocr import get_ocr_model
from .ocr_tsl.tsl import get_tsl_model

locks = {}

def use_lock(lock_name: str, blocking: bool = False):
    """Decorator to use a lock for the function."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            lock = locks.setdefault(lock_name, Lock())
            if blocking:
                with lock:
                    return func(*args, **kwargs)
            else:
                acquired = lock.acquire(blocking=False)
                try:
                    return func(*args, **kwargs)
                finally:
                    if acquired:
                        lock.release()
        return wrapper
    return decorator

def wait_for_lock(lock_name: str, timeout: int = None):
    """Decorator to wait for a lock before executing the function without acquiring the lock."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            lock = locks.get(lock_name, Lock())
            start = time.time()
            while lock.locked():
                time.sleep(0.1)
                if timeout is not None and time.time() - start > timeout:
                    return JsonResponse({'error': 'Timeout waiting for lock'}, status=408)

            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_backend_models(strict: bool = True):
    """Decorator to check and add loaded models."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            box_model = get_box_model() or ''
            ocr_model = get_ocr_model() or ''
            tsl_model = get_tsl_model() or ''
            if strict and (not box_model or not ocr_model or not tsl_model):
                return JsonResponse({'error': 'Models not loaded'}, status=513)
            return func(*args, **kwargs, box_model=box_model, ocr_model=ocr_model, tsl_model=tsl_model)
        return wrapper
    return decorator

def get_backend_langs(strict: bool = True):
    """Decorator to check and add loaded languages."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            lang_src = get_lang_src() or ''
            lang_dst = get_lang_dst() or ''
            if strict and (not lang_src or not lang_dst):
                return JsonResponse({'error': 'Languages not loaded'}, status=512)
            return func(*args, **kwargs, lang_src=lang_src, lang_dst=lang_dst)
        return wrapper
    return decorator

def method_or_405(methods):
    """Decorator to allow only specific methods."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request: HttpRequest = args[0]
            if request.method not in methods:
                return JsonResponse({'error': f'{request.method} not allowed'}, status=405)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def post_data_deserializer(expected_keys: list[str], strict: bool = True, required: bool = True):
    """Decorator to deserialize POST data.

    Args:
        expected_keys (list[str]): List of keys to expect in the POST data.
        strict (bool, optional): If any key not present in `expected_keys` is found, return 400. Defaults to True.
        required (bool, optional): If `True` not found expected keys are set to None, else return 400. Defaults to True.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request: HttpRequest = args[0]
            if request.content_type != 'application/json':
                return JsonResponse({'error': 'Content-Type must be application/json'}, status=400)
            _data = json.loads(request.body)
            data = {}
            for key in expected_keys:
                if key not in _data and required:
                    return JsonResponse({'error': f'{key} not found in POST data'}, status=400)
                data[key] = _data.pop(key, None)
            if strict and _data:
                return JsonResponse({'error': f'Unexpected keys: {", ".join(_data.keys())}'}, status=400)
            return func(*args, **kwargs, **data)
        return wrapper
    return decorator

def get_data_deserializer(expected_keys: list[str], strict: bool = True, required: bool = True):
    """Decorator to deserialize GET data.

    Args:
        expected_keys (list[str]): List of keys to expect in the GET data.
        strict (bool, optional): If any key not present in `expected_keys` is found, return 400. Defaults to True.
        required (bool, optional): If `True` not found expected keys are set to None, else return 400. Defaults to True.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            request: HttpRequest = args[0]
            _data = request.GET.dict()
            data = {}
            for key in expected_keys:
                if key not in _data and required:
                    return JsonResponse({'error': f'{key} not found in GET data'}, status=400)
                data[key] = _data.pop(key, None)
            if strict and _data:
                return JsonResponse({'error': f'Unexpected keys: {", ".join(_data.keys())}'}, status=400)
            return func(*args, **kwargs, **data)
        return wrapper
    return decorator
