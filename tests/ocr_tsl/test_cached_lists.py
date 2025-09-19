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
"""Tests for the cached lists."""
#pylint: disable=protected-access

import pytest

from ocr_translate import models as m
from ocr_translate.ocr_tsl import cached_lists as cl
from ocr_translate.ocr_tsl import signals

pytestmark = pytest.mark.django_db

def test_refresh_lang_cache(language):
    """Test that the lang cache is refreshed."""
    cl.refresh_lang_cache()
    assert set(cl.ALL_LANG_SRC) == {language}
    assert set(cl.ALL_LANG_DST) == {language}

def test_refresh_lang_cache2(language, language2):
    """Test that the lang cache is refreshed."""
    cl.refresh_lang_cache()
    assert set(cl.ALL_LANG_SRC) == {language, language2}
    assert set(cl.ALL_LANG_DST) == {language, language2}

def test_get_lang_src_none(monkeypatch, mock_called):
    """Test that the lang cache is refreshed when ALL_LANG_SRC is None."""
    monkeypatch.setattr(cl, 'ALL_LANG_SRC', None)
    monkeypatch.setattr(cl, 'refresh_lang_cache', mock_called)

    assert cl.ALL_LANG_SRC is None
    cl.get_all_lang_src()
    assert hasattr(mock_called, 'called')

def test_get_lang_src_set(monkeypatch, mock_called):
    """Test that the lang cache is not refreshed when ALL_LANG_SRC is set."""
    monkeypatch.setattr(cl, 'ALL_LANG_SRC', 'test')
    monkeypatch.setattr(cl, 'refresh_lang_cache', mock_called)

    assert cl.ALL_LANG_SRC == 'test'
    cl.get_all_lang_src()
    assert not hasattr(mock_called, 'called')

def test_get_lang_dst_none(monkeypatch, mock_called):
    """Test that the lang cache is refreshed when ALL_LANG_DST is None."""
    monkeypatch.setattr(cl, 'ALL_LANG_DST', None)
    monkeypatch.setattr(cl, 'refresh_lang_cache', mock_called)

    assert cl.ALL_LANG_DST is None
    cl.get_all_lang_dst()
    assert hasattr(mock_called, 'called')

def test_get_lang_dst_set(monkeypatch, mock_called):
    """Test that the lang cache is not refreshed when ALL_LANG_DST set."""
    monkeypatch.setattr(cl, 'ALL_LANG_DST', 'test')
    monkeypatch.setattr(cl, 'refresh_lang_cache', mock_called)

    assert cl.ALL_LANG_DST == 'test'
    cl.get_all_lang_dst()
    assert not hasattr(mock_called, 'called')

def test_refresh_model_cache(monkeypatch, language):
    """Test that the model cache is refreshed."""
    monkeypatch.setattr(m.Language, 'LOADED_MODEL_SRC', language)
    monkeypatch.setattr(m.Language, 'LOADED_MODEL_DST', language)
    cl.refresh_model_cache()
    assert set(cl.ALLOWED_BOX_MODELS) == set()
    assert set(cl.ALLOWED_OCR_MODELS) == set()
    assert set(cl.ALLOWED_TSL_MODELS) == set()

def test_refresh_model_cache_all(monkeypatch, language, box_model, ocr_model, tsl_model):
    """Test that the model cache is refreshed."""
    monkeypatch.setattr(m.Language, 'LOADED_MODEL_SRC', language)
    monkeypatch.setattr(m.Language, 'LOADED_MODEL_DST', language)
    cl.refresh_model_cache()
    assert set(cl.ALLOWED_BOX_MODELS) == {box_model}
    assert set(cl.ALLOWED_OCR_MODELS) == {ocr_model}
    assert set(cl.ALLOWED_TSL_MODELS) == {tsl_model}

def test_refresh_model_cache_all_inactive_box(
        monkeypatch, language, box_model, ocr_model, tsl_model, mock_loaded_lang_only
    ):
    """Test that the model cache is refreshed."""
    box_model.active = False
    box_model.save()
    cl.refresh_model_cache()
    assert set(cl.ALLOWED_BOX_MODELS) == set()
    assert set(cl.ALLOWED_OCR_MODELS) == {ocr_model}
    assert set(cl.ALLOWED_TSL_MODELS) == {tsl_model}

def test_refresh_model_cache_all_inactive_ocr(
        monkeypatch, language, box_model, ocr_model, tsl_model, mock_loaded_lang_only
    ):
    """Test that the model cache is refreshed."""
    ocr_model.active = False
    ocr_model.save()
    cl.refresh_model_cache()
    assert set(cl.ALLOWED_BOX_MODELS) == {box_model}
    assert set(cl.ALLOWED_OCR_MODELS) == set()
    assert set(cl.ALLOWED_TSL_MODELS) == {tsl_model}

def test_refresh_model_cache_all_inactive_tsl(
        monkeypatch, language, box_model, ocr_model, tsl_model, mock_loaded_lang_only
    ):
    """Test that the model cache is refreshed."""
    tsl_model.active = False
    tsl_model.save()
    cl.refresh_model_cache()
    assert set(cl.ALLOWED_BOX_MODELS) == {box_model}
    assert set(cl.ALLOWED_OCR_MODELS) == {ocr_model}
    assert set(cl.ALLOWED_TSL_MODELS) == set()

def test_refresh_model_cache_all_none(language, box_model, ocr_model, tsl_model):
    """Test that the model cache is refreshed."""
    cl.refresh_model_cache()
    assert set(cl.ALLOWED_BOX_MODELS) == set()
    assert set(cl.ALLOWED_OCR_MODELS) == set()
    assert set(cl.ALLOWED_TSL_MODELS) == set()

def test_get_allowed_box_models_none(monkeypatch, mock_called):
    """Test that the lang cache is refreshed when ALLOWED_BOX_MODELS is None."""
    monkeypatch.setattr(cl, 'ALLOWED_BOX_MODELS', None)
    monkeypatch.setattr(cl, 'refresh_model_cache', mock_called)

    assert cl.ALLOWED_BOX_MODELS is None
    cl.get_allowed_box_models()
    assert hasattr(mock_called, 'called')

def test_get_allowed_box_models_set(monkeypatch, mock_called):
    """Test that the lang cache is not refreshed when ALLOWED_BOX_MODELS set."""
    monkeypatch.setattr(cl, 'ALLOWED_BOX_MODELS', 'test')
    monkeypatch.setattr(cl, 'refresh_model_cache', mock_called)

    assert cl.ALLOWED_BOX_MODELS == 'test'
    cl.get_allowed_box_models()
    assert not hasattr(mock_called, 'called')

def test_get_allowed_ocr_models_none(monkeypatch, mock_called):
    """Test that the lang cache is refreshed when ALLOWED_OCR_MODELS is None."""
    monkeypatch.setattr(cl, 'ALLOWED_OCR_MODELS', None)
    monkeypatch.setattr(cl, 'refresh_model_cache', mock_called)

    assert cl.ALLOWED_OCR_MODELS is None
    cl.get_allowed_ocr_models()
    assert hasattr(mock_called, 'called')

def test_get_allowed_ocr_models_set(monkeypatch, mock_called):
    """Test that the lang cache is not refreshed when ALLOWED_OCR_MODELS set."""
    monkeypatch.setattr(cl, 'ALLOWED_OCR_MODELS', 'test')
    monkeypatch.setattr(cl, 'refresh_model_cache', mock_called)

    assert cl.ALLOWED_OCR_MODELS == 'test'
    cl.get_allowed_ocr_models()
    assert not hasattr(mock_called, 'called')

def test_get_allowed_tsl_models_none(monkeypatch, mock_called):
    """Test that the lang cache is refreshed when ALLOWED_TSL_MODELS is None."""
    monkeypatch.setattr(cl, 'ALLOWED_TSL_MODELS', None)
    monkeypatch.setattr(cl, 'refresh_model_cache', mock_called)

    assert cl.ALLOWED_TSL_MODELS is None
    cl.get_allowed_tsl_models()
    assert hasattr(mock_called, 'called')

def test_get_allowed_tsl_models_set(monkeypatch, mock_called):
    """Test that the lang cache is not refreshed when ALLOWED_TSL_MODELS set."""
    monkeypatch.setattr(cl, 'ALLOWED_TSL_MODELS', 'test')
    monkeypatch.setattr(cl, 'refresh_model_cache', mock_called)

    assert cl.ALLOWED_TSL_MODELS == 'test'
    cl.get_allowed_tsl_models()
    assert not hasattr(mock_called, 'called')

def test_post_save_lang_signal(monkeypatch, mock_called, language):
    """Test that the lang cache is refreshed on post_save signal."""
    monkeypatch.setattr(cl, 'refresh_lang_cache', mock_called)
    assert not hasattr(mock_called, 'called')
    language.save()
    assert hasattr(mock_called, 'called')

def test_post_save_box_signal(monkeypatch, mock_called, box_model):
    """Test that the model cache is refreshed on post_save signal from OCRBoxModel."""
    monkeypatch.setattr(cl, 'refresh_model_cache', mock_called)
    assert not hasattr(mock_called, 'called')
    box_model.save()
    assert hasattr(mock_called, 'called')

def test_post_save_ocr_signal(monkeypatch, mock_called, ocr_model):
    """Test that the model cache is refreshed on post_save signal from OCRModel."""
    monkeypatch.setattr(cl, 'refresh_model_cache', mock_called)
    assert not hasattr(mock_called, 'called')
    ocr_model.save()
    assert hasattr(mock_called, 'called')

def test_post_save_tsl_signal(monkeypatch, mock_called, tsl_model):
    """Test that the model cache is refreshed on post_save signal from TSLModel."""
    monkeypatch.setattr(cl, 'refresh_model_cache', mock_called)
    assert not hasattr(mock_called, 'called')
    tsl_model.save()
    assert hasattr(mock_called, 'called')

def test_refresh_model_cache_signal(monkeypatch, mock_called):
    """Test that the model cache is refreshed on refresh_model_cache_signal."""
    monkeypatch.setattr(cl, 'refresh_model_cache', mock_called)
    assert not hasattr(mock_called, 'called')
    signals.refresh_model_cache_signal.send(sender=None)
    assert hasattr(mock_called, 'called')
