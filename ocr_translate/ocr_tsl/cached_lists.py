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
"""Caches for list of models to be sent to the frontend."""
from django.db.models import Count
from django.db.models.signals import post_save
from django.dispatch import receiver

from .. import models as m
from .lang import get_lang_dst, get_lang_src
from .signals import refresh_model_cache_signal

# Caches for the languages ordered by number of translations
ALL_LANG_SRC: list[m.Language] = None
ALL_LANG_DST: list[m.Language] = None

ALLOWED_BOX_MODELS: list[m.OCRBoxModel] = None
ALLOWED_OCR_MODELS: list[m.OCRModel] = None
ALLOWED_TSL_MODELS: list[m.TSLModel] = None

def refresh_model_cache():
    """Refresh the models cached entry."""
    global ALLOWED_BOX_MODELS
    global ALLOWED_OCR_MODELS
    global ALLOWED_TSL_MODELS

    lang_src = get_lang_src()
    lang_dst = get_lang_dst()

    ALLOWED_BOX_MODELS = []
    ALLOWED_OCR_MODELS = []
    ALLOWED_TSL_MODELS = []
    if not lang_src is None:
        ALLOWED_BOX_MODELS = m.OCRBoxModel.objects.annotate(
            count=Count('box_runs')
            ).filter(languages=lang_src, active=True).order_by('-count').all()
        ALLOWED_OCR_MODELS = m.OCRModel.objects.annotate(
            count=Count('ocr_runs')
            ).filter(languages=lang_src, active=True).order_by('-count').all()
        if not lang_dst is None:
            ALLOWED_TSL_MODELS = m.TSLModel.objects.annotate(
                count=Count('tsl_runs')
                ).filter(src_languages=lang_src, dst_languages=lang_dst, active=True).order_by('-count').all()

def refresh_lang_cache():
    """Refresh the languages cached entry."""
    global ALL_LANG_SRC
    global ALL_LANG_DST
    ALL_LANG_SRC = m.Language.objects.annotate(count=Count('trans_src')).order_by('-count').all()
    ALL_LANG_DST = m.Language.objects.annotate(count=Count('trans_dst')).order_by('-count').all()

def get_all_lang_src():
    """Return all the source languages."""
    if ALL_LANG_SRC is None:
        refresh_lang_cache()
    return ALL_LANG_SRC

def get_all_lang_dst():
    """Return all the destination languages."""
    if ALL_LANG_DST is None:
        refresh_lang_cache()
    return ALL_LANG_DST

def get_allowed_box_models():
    """Return the allowed box models."""
    if ALLOWED_BOX_MODELS is None:
        refresh_model_cache()
    return ALLOWED_BOX_MODELS

def get_allowed_ocr_models():
    """Return the allowed OCR models."""
    if ALLOWED_OCR_MODELS is None:
        refresh_model_cache()
    return ALLOWED_OCR_MODELS

def get_allowed_tsl_models():
    """Return the allowed TSL models."""
    if ALLOWED_TSL_MODELS is None:
        refresh_model_cache()
    return ALLOWED_TSL_MODELS

@receiver(post_save, sender=m.Language)
def refres_lang_callback(sender, instance, **kwargs): # pylint: disable=unused-argument
    """Callback to refresh the cached language list when a language is added/modified."""
    refresh_lang_cache()

@receiver(refresh_model_cache_signal)
@receiver(post_save, sender=m.OCRBoxModel)
@receiver(post_save, sender=m.OCRModel)
@receiver(post_save, sender=m.TSLModel)
def refresh_models_callback(sender, **kwargs): # pylint: disable=unused-argument
    """Callback to refresh the cached model list when a language is added/modified."""
    refresh_model_cache()
