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
"""Test environment initialization."""

import importlib

import pytest

from ocr_translate import models as m
from ocr_translate import ocr_tsl
from ocr_translate.ocr_tsl import box, lang, ocr, tsl

pytestmark = pytest.mark.django_db

def test_init_most_used_clean(mock_loaders):
    """Test init_most_used with empty database."""
    ocr_tsl.init_most_used()
    assert box.BBOX_MODEL_OBJ is None
    assert ocr.OCR_MODEL_OBJ is None
    assert tsl.TSL_MODEL_OBJ is None
    assert lang.LANG_SRC is None
    assert lang.LANG_DST is None

def test_init_most_used_content(mock_loaders, language, ocr_box_model, ocr_model, tsl_model):
    """Test init_most_used with content in the database."""
    ocr_tsl.init_most_used()
    assert box.BBOX_MODEL_OBJ == ocr_box_model
    assert ocr.OCR_MODEL_OBJ == ocr_model
    assert tsl.TSL_MODEL_OBJ == tsl_model
    assert lang.LANG_SRC == language
    assert lang.LANG_DST == language

def test_init_most_used_more_content(mock_loaders, language_dict, image, option_dict, text):
    """Test init_most_used with more content in the database. Check that sorting is working."""
    # pylint: disable=unused-variable,too-many-locals
    dct1 = {k:v+'1' for k,v in language_dict.items()}
    dct2 = {k:v+'2' for k,v in language_dict.items()}
    dct3 = {k:v+'3' for k,v in language_dict.items()}
    lang1 = m.Language.objects.create(**dct1)
    lang2 = m.Language.objects.create(**dct2)
    lang3 = m.Language.objects.create(**dct3)

    ocr_box_model1 = m.OCRBoxModel.objects.create(name='test_model1/id')
    ocr_box_model2 = m.OCRBoxModel.objects.create(name='test_model2/id')

    ocr_model1 = m.OCRModel.objects.create(name='test_model1/id')
    ocr_model2 = m.OCRModel.objects.create(name='test_model2/id')

    tsl_model1 = m.TSLModel.objects.create(name='test_model1/id')
    tsl_model2 = m.TSLModel.objects.create(name='test_model2/id')

    box_run1 = m.OCRBoxRun.objects.create(
        model=ocr_box_model1, lang_src=lang1, image=image, options=option_dict
        )
    box_run2_1 = m.OCRBoxRun.objects.create(
        model=ocr_box_model2, lang_src=lang2, image=image, options=option_dict
        )
    box_run2_2 = m.OCRBoxRun.objects.create(
        model=ocr_box_model2, lang_src=lang2, image=image, options=option_dict
        )

    bbox = m.BBox.objects.create(image=image, l=1, b=2, r=3, t=4, from_ocr=box_run1)

    ocr_run1 = m.OCRRun.objects.create(
        lang_src=lang1, bbox=bbox, model=ocr_model1, options=option_dict, result=text
        )
    ocr_run2_1 = m.OCRRun.objects.create(
        lang_src=lang1, bbox=bbox, model=ocr_model2, options=option_dict, result=text
        )
    ocr_run2_2 = m.OCRRun.objects.create(
        lang_src=lang1, bbox=bbox, model=ocr_model2, options=option_dict, result=text
        )

    tsl_run1_1 = m.TranslationRun.objects.create(
        lang_src=lang2, lang_dst=lang3, text=text, model=tsl_model1, options=option_dict, result=text
        )
    tsl_run1_2 = m.TranslationRun.objects.create(
        lang_src=lang2, lang_dst=lang3, text=text, model=tsl_model1, options=option_dict, result=text
        )
    tsl_run2 = m.TranslationRun.objects.create(
        lang_src=lang1, lang_dst=lang1, text=text, model=tsl_model2, options=option_dict, result=text
        )

    ocr_tsl.init_most_used()

    assert lang.LANG_SRC == lang2
    assert lang.LANG_DST == lang3

    assert box.BBOX_MODEL_OBJ == ocr_box_model2
    assert ocr.OCR_MODEL_OBJ == ocr_model2
    assert tsl.TSL_MODEL_OBJ == tsl_model1

def test_auto_create_languages():
    """Test auto_create_languages."""
    ocr_tsl.auto_create_languages()

    assert m.Language.objects.count() > 50

    # Test settings of **kwargs
    jap = m.Language.objects.get(iso1='ja')
    assert jap.facebookM2M == 'ja'
    assert jap.break_chars is not None
    assert jap.ignore_chars is not None

def test_auto_create_models_nolang():
    """Test auto_create_models without creating languages before"""
    with pytest.raises(m.Language.DoesNotExist):
        ocr_tsl.auto_create_models()

def test_auto_create_models_lang():
    """Test auto_create_models after creating languages."""

    ocr_tsl.auto_create_languages()
    ocr_tsl.auto_create_models()

    assert m.OCRBoxModel.objects.count() > 0
    assert m.OCRModel.objects.count() > 0
    assert m.TSLModel.objects.count() > 0

    m2m = m.TSLModel.objects.get(name='facebook/m2m100_418M')
    eocr = m.OCRBoxModel.objects.get(name='easyocr')
    tess = m.OCRModel.objects.get(name='tesseract')

    # Test language code assignment
    assert m2m.language_format == 'facebookM2M'
    assert eocr.language_format == 'easyocr'
    assert tess.language_format == 'tesseract'
    # Test lang assignment for models (many-to-many)
    assert m2m.src_languages.count() > 10
    assert m2m.dst_languages.count() > 10
    assert eocr.languages.count() > 1
    assert tess.languages.count() > 1

def test_env_init_most_used(monkeypatch):
    """Test that init_most_used is called when LOAD_ON_START is 'true'."""
    def mock_init_most_used():
        """Mock init_most_used."""
        mock_init_most_used.called = True

    monkeypatch.setattr(ocr_tsl.initializers, 'init_most_used', mock_init_most_used)
    monkeypatch.setenv('LOAD_ON_START', 'true')

    importlib.reload(ocr_tsl)
    assert mock_init_most_used.called

def test_env_init_most_used_false(monkeypatch):
    """Test that init_most_used is not called when LOAD_ON_START is not 'true'."""
    def mock_init_most_used():
        """Mock init_most_used."""
        mock_init_most_used.called = True

    monkeypatch.setattr(ocr_tsl.initializers, 'init_most_used', mock_init_most_used)
    monkeypatch.setenv('LOAD_ON_START', 'false')

    importlib.reload(ocr_tsl)
    assert not hasattr(mock_init_most_used, 'called')

def test_env_auto_create_languges(monkeypatch):
    """Test that auto_create_languages is called when AUTOCREATE_LANGUAGES is 'true'."""
    def mock_auto_create_languages():
        """Mock auto_create_languages."""
        mock_auto_create_languages.called = True

    monkeypatch.setattr(ocr_tsl.initializers, 'auto_create_languages', mock_auto_create_languages)
    monkeypatch.setenv('AUTOCREATE_LANGUAGES', 'true')

    importlib.reload(ocr_tsl)
    assert mock_auto_create_languages.called

def test_env_auto_create_languges_false(monkeypatch):
    """Test that auto_create_languages is not called when AUTOCREATE_LANGUAGES is not 'true'."""
    def mock_auto_create_languages():
        """Mock auto_create_languages."""
        mock_auto_create_languages.called = True

    monkeypatch.setattr(ocr_tsl.initializers, 'auto_create_languages', mock_auto_create_languages)
    monkeypatch.setenv('AUTOCREATE_LANGUAGES', 'false')

    importlib.reload(ocr_tsl)
    assert not hasattr(mock_auto_create_languages, 'called')

def test_env_auto_create_models(monkeypatch):
    """Test that auto_create_models is called when AUTOCREATE_VALIDATED_MODELS is 'true'."""
    def mock_auto_create_models():
        """Mock auto_create_models."""
        mock_auto_create_models.called = True

    monkeypatch.setattr(ocr_tsl.initializers, 'auto_create_models', mock_auto_create_models)
    monkeypatch.setenv('AUTOCREATE_VALIDATED_MODELS', 'true')

    importlib.reload(ocr_tsl)
    assert mock_auto_create_models.called

def test_env_auto_create_models_false(monkeypatch):
    """Test that auto_create_models is not called when AUTOCREATE_VALIDATED_MODELS is not 'true'."""
    def mock_auto_create_models():
        """Mock auto_create_models."""
        mock_auto_create_models.called = True

    monkeypatch.setattr(ocr_tsl.initializers, 'auto_create_models', mock_auto_create_models)
    monkeypatch.setenv('AUTOCREATE_VALIDATED_MODELS', 'false')

    importlib.reload(ocr_tsl)
    assert not hasattr(mock_auto_create_models, 'called')
