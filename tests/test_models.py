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
"""Tests for the database models."""

import django
import pytest

from ocr_translate import models as m
from ocr_translate.messaging import Message
from ocr_translate.ocr_tsl import box, full, ocr, tsl

pytestmark = pytest.mark.django_db

def test_add_language(language_dict, language):
    """Test adding a language."""
    query = m.Language.objects.filter(**language_dict)
    assert query.exists()
    assert str(query.first()) == language_dict['iso1']

def test_add_language_existing(language_dict, language):
    """Test adding a language."""
    with pytest.raises(django.db.utils.IntegrityError):
        m.Language.objects.create(**language_dict)

def test_add_ocr_box_model(ocr_box_model_dict, ocr_box_model):
    """Test adding a new OCRBoxModel"""
    query = m.OCRBoxModel.objects.filter(**ocr_box_model_dict)
    assert query.exists()
    assert str(query.first()) == ocr_box_model_dict['name']

def test_add_ocr_model(ocr_model_dict, ocr_model):
    """Test adding a new OCRModel"""
    query = m.OCRModel.objects.filter(**ocr_model_dict)
    assert query.exists()
    assert str(query.first()) == ocr_model_dict['name']

def test_add_tsl_model(tsl_model_dict, tsl_model):
    """Test adding a new TSLModel"""
    query = m.TSLModel.objects.filter(**tsl_model_dict)
    assert query.exists()
    assert str(query.first()) == tsl_model_dict['name']

def test_add_option_dict(option_dict):
    """Test adding a new OptionDict"""
    query = m.OptionDict.objects.filter(options={})
    assert query.exists()
    assert str(query.first()) == str({})

def test_box_run(image, language, ocr_box_model, option_dict, monkeypatch):
    """Test adding a new BoxRun"""

    lbrt = (1,2,3,4)
    def mock_pipeline(*args, **kwargs):
        return [lbrt]

    monkeypatch.setattr(box, 'BBOX_MODEL_OBJ', ocr_box_model)
    monkeypatch.setattr(box, 'box_pipeline', mock_pipeline)

    res = box.box_run(image, language, image=1, options=option_dict)

    assert isinstance(res, list)
    assert isinstance(res[0], m.BBox)
    assert res[0].lbrt == lbrt

def test_box_run_reuse(image, language, ocr_box_model, option_dict, monkeypatch):
    """Test adding a new BoxRun"""
    lbrt = (1,2,3,4)
    def mock_pipeline(*args, **kwargs):
        return [lbrt]

    monkeypatch.setattr(box, 'BBOX_MODEL_OBJ', ocr_box_model)
    monkeypatch.setattr(box, 'box_pipeline', mock_pipeline)

    assert m.OCRBoxRun.objects.count() == 0
    box.box_run(image, language, image=1, options=option_dict)
    assert m.OCRBoxRun.objects.count() == 1
    box.box_run(image, language, image=1, options=option_dict)
    assert m.OCRBoxRun.objects.count() == 1

def test_ocr_run(bbox, language, ocr_model, option_dict, monkeypatch):
    """Test performin an ocr_run blocking"""

    text = 'test_text'
    def mock_ocr(*args, **kwargs):
        return text

    monkeypatch.setattr(ocr, 'OCR_MODEL_OBJ', ocr_model)
    monkeypatch.setattr(ocr, 'ocr', mock_ocr)

    gen = ocr.ocr_run(bbox, language, image=1, options=option_dict)

    res = next(gen)

    assert isinstance(res, m.Text)
    assert res.text == text

def test_ocr_run_nonblock(bbox, language, ocr_model, option_dict, monkeypatch):
    """Test performin an ocr_run non-blocking"""
    text = 'test_text'
    def mock_ocr(*args, **kwargs):
        def _handler(text):
            return text
        return Message(id_=0, msg={'args':(text,)}, handler=_handler)

    monkeypatch.setattr(ocr, 'OCR_MODEL_OBJ', ocr_model)
    monkeypatch.setattr(ocr, 'ocr', mock_ocr)

    gen = ocr.ocr_run(bbox, language, image=1, options=option_dict, block=False)

    msg = next(gen)
    msg.resolve()
    res = next(gen)

    assert isinstance(msg, Message)
    assert isinstance(res, m.Text)
    assert res.text == text

def test_tsl_run(text, language, tsl_model, option_dict, monkeypatch):
    """Test performin an tsl_run blocking"""
    def mock_tsl_pipeline(*args, **kwargs):
        return text.text

    monkeypatch.setattr(tsl, 'TSL_MODEL_OBJ', tsl_model)
    monkeypatch.setattr(tsl, 'tsl_pipeline', mock_tsl_pipeline)

    gen = tsl.tsl_run(text, src=language, dst=language, options=option_dict)

    res = next(gen)

    assert isinstance(res, m.Text)
    assert res.text == text.text

def test_tsl_run_nonblock(text, language, tsl_model, option_dict, monkeypatch):
    """Test performin an tsl_run non-blocking"""
    def mock_tsl_pipeline(*args, **kwargs):
        def _handler(text):
            return text
        return Message(id_=0, msg={'args':(text.text,)}, handler=_handler)

    monkeypatch.setattr(tsl, 'TSL_MODEL_OBJ', tsl_model)
    monkeypatch.setattr(tsl, 'tsl_pipeline', mock_tsl_pipeline)

    gen = tsl.tsl_run(text, src=language, dst=language, options=option_dict, block=False)

    msg = next(gen)
    msg.resolve()
    res = next(gen)

    assert isinstance(msg, Message)
    assert isinstance(res, m.Text)
    assert res.text == text.text

def test_tsl_run_lazy(text, language, option_dict):
    """Test tsl pipeline with worker"""
    with pytest.raises(ValueError):
        gen = tsl.tsl_run(text, language, language, force=True, lazy=True)
        next(gen)

    # Nothing in the DB, so should rise ValueError (no previous found and lazy=True)
    with pytest.raises(ValueError):
        gen = tsl.tsl_run(text, language, language, lazy=True)
        next(gen)

def test_ocr_tsl_work_plus_lazy(
        image, image_pillow, text, bbox,
        language, ocr_model, tsl_model, option_dict,
        monkeypatch
        ):
    """Test performin an ocr_tsl_run non-lazy"""
    def mock_box_run(*args, **kwargs):
        return [bbox]
    def mock_ocr_run(*args, block=True, **kwargs):
        if not block:
            yield
        res, _ = m.Text.objects.get_or_create(text = text.text + '_ocred')
        yield res
    def mock_tsl_run(obj, *args, block=True, **kwargs):
        if not block:
            yield
        res, _ = m.Text.objects.get_or_create(text = obj.text + '_translated')
        yield res

    monkeypatch.setattr(full, 'box_run', mock_box_run)
    monkeypatch.setattr(full, 'ocr_run', mock_ocr_run)
    monkeypatch.setattr(full, 'tsl_run', mock_tsl_run)

    res = full.ocr_tsl_pipeline_work(image_pillow, image.md5)

    assert isinstance(res, list)
    assert len(res) == 1
    assert isinstance(res[0], dict)
    assert res[0]['ocr'] == text.text + '_ocred'
    assert res[0]['tsl'] == text.text + '_ocred' + '_translated'
    assert res[0]['box'] == bbox.lbrt

    res_lazy = full.ocr_tsl_pipeline_lazy(image.md5)

    assert res == res_lazy

def test_ocr_tsl_lazy():
    """Test performin an ocr_tsl_run lazy (no image)"""
    with pytest.raises(ValueError, match=r'^Image with md5 .* does not exist$'):
        full.ocr_tsl_pipeline_lazy('')

def test_ocr_tsl_lazy_image(image, option_dict):
    """Test performin an ocr_tsl_run lazy (with image but missing ocr-tsl steps)"""
    with pytest.raises(ValueError):
        full.ocr_tsl_pipeline_lazy(image.md5)
