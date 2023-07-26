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
"""Fixtures for the tests."""

import numpy as np
import pytest
from PIL import Image

import ocr_translate
from ocr_translate import models as m
from ocr_translate import ocr_tsl, views
from ocr_translate.ocr_tsl import box, lang, ocr, tsl


@pytest.fixture()
def language_dict():
    """Dict defining a language"""
    return {
        'name': 'Japanese',
        'iso1': 'ja',
        'iso2b': 'jpn',
        'iso2t': 'jpn',
        'iso3': 'jpn',
    }

@pytest.fixture()
def ocr_box_model_dict():
    """Dict defiining an OCRBoxModel"""
    return {
        'name': 'test_model/id',
        'language_format': 'iso1'
    }

@pytest.fixture()
def ocr_model_dict():
    """Dict defiining an OCRModel"""
    return {
        'name': 'test_model/id',
        'language_format': 'iso1'
    }

@pytest.fixture()
def tsl_model_dict():
    """Dict defiining a TSLModel"""
    return {
        'name': 'test_model/id',
        'language_format': 'iso1'
    }

@pytest.fixture()
def option_dict():
    """OptionDict database object."""
    return m.OptionDict.objects.create(options={})

@pytest.fixture()
def language(language_dict):
    """Language database object."""
    return m.Language.objects.create(**language_dict)

@pytest.fixture(scope='session')
def image_pillow():
    """Random Pillow image."""
    npimg = np.random.randint(0,255,(25,25,3), dtype=np.uint8)
    return Image.fromarray(npimg)

@pytest.fixture()
def image():
    """Image database object."""
    return m.Image.objects.create(md5='test_md5')

@pytest.fixture()
def text():
    """Text database object."""
    return m.Text.objects.create(text='test_text')

@pytest.fixture()
def ocr_box_model(language, ocr_box_model_dict):
    """OCRBoxModel database object."""
    res = m.OCRBoxModel.objects.create(**ocr_box_model_dict)
    res.languages.add(language)

    return res

@pytest.fixture()
def ocr_model(language, ocr_model_dict):
    """OCRModel database object."""
    res = m.OCRModel.objects.create(**ocr_model_dict)
    res.languages.add(language)

    return res

@pytest.fixture()
def tsl_model(language, tsl_model_dict):
    """TSLModel database object."""
    res = m.TSLModel.objects.create(**tsl_model_dict)
    res.src_languages.add(language)
    res.dst_languages.add(language)

    return res

@pytest.fixture()
def box_run(language, image, ocr_box_model, option_dict):
    """OCRBoxRun database object."""
    return m.OCRBoxRun.objects.create(lang_src=language, image=image, model=ocr_box_model, options=option_dict)


@pytest.fixture()
def bbox(image, box_run):
    """BBox database object."""
    return m.BBox.objects.create(image=image, l=1, b=2, r=3, t=4, from_ocr=box_run)

@pytest.fixture()
def ocr_run(language, bbox, ocr_model, option_dict, text):
    """OCRRun database object."""
    return m.OCRRun.objects.create(lang_src=language, bbox=bbox, model=ocr_model, options=option_dict, result=text)

@pytest.fixture()
def tsl_run(language, text, tsl_model, option_dict):
    """OCRTSRun database object."""
    return m.TranslationRun.objects.create(
        lang_src=language, lang_dst=language, text=text, model=tsl_model, options=option_dict, result=text
        )

@pytest.fixture()
def mock_loaded(monkeypatch, language, ocr_box_model, ocr_model, tsl_model):
    """Mock models being loaded"""
    monkeypatch.setattr(box, 'BOX_MODEL_ID', ocr_box_model.name)
    monkeypatch.setattr(box, 'BBOX_MODEL_OBJ', ocr_box_model)
    monkeypatch.setattr(ocr, 'OBJ_MODEL_ID', ocr_model.name)
    monkeypatch.setattr(ocr, 'OCR_MODEL_OBJ', ocr_model)
    monkeypatch.setattr(tsl, 'TSL_MODEL_ID', tsl_model.name)
    monkeypatch.setattr(tsl, 'TSL_MODEL_OBJ', tsl_model)
    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(lang, 'LANG_DST', language)

@pytest.fixture()
def mock_loaders(monkeypatch):
    """Mock the load functions."""
    def mock_load_lang_src(name):
        monkeypatch.setattr(lang, 'LANG_SRC', m.Language.objects.get(iso1=name))
    def mock_load_lang_dst(name):
        monkeypatch.setattr(lang, 'LANG_DST', m.Language.objects.get(iso1=name))
    def mock_load_box_model(name):
        monkeypatch.setattr(box, 'BOX_MODEL_ID', name)
        monkeypatch.setattr(box, 'BBOX_MODEL_OBJ', m.OCRBoxModel.objects.get(name=name))
    def mock_load_ocr_model(name):
        monkeypatch.setattr(ocr, 'OBJ_MODEL_ID', name)
        monkeypatch.setattr(ocr, 'OCR_MODEL_OBJ', m.OCRModel.objects.get(name=name))
    def mock_load_tsl_model(name):
        monkeypatch.setattr(tsl, 'TSL_MODEL_ID', name)
        monkeypatch.setattr(tsl, 'TSL_MODEL_OBJ', m.TSLModel.objects.get(name=name))

    dct = {
        'load_lang_src': mock_load_lang_src,
        'load_lang_dst': mock_load_lang_dst,
        'load_box_model': mock_load_box_model,
        'load_ocr_model': mock_load_ocr_model,
        'load_tsl_model': mock_load_tsl_model,
    }

    for mod in [ocr_translate, ocr_tsl, box, lang, ocr, tsl, views]:
        for fname, mock in dct.items():
            try:
                monkeypatch.setattr(mod, fname, mock)
            except AttributeError:
                pass
