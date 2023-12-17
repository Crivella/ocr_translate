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
"""Tests for full module."""

import pytest

from ocr_translate import models as m
from ocr_translate.ocr_tsl import box, full, lang, ocr, tsl

pytestmark = pytest.mark.django_db

def test_lazy_nonexistent_image():
    """Test lazy pipeline with nonexistent image."""
    with pytest.raises(ValueError):
        full.ocr_tsl_pipeline_lazy('nonexistent')

def test_lazy_nobox(
        monkeypatch, mock_called,
        language, box_model, ocr_model, image):
    """Test lazy pipeline with no box."""
    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(box, 'BOX_MODEL_OBJ', box_model)
    monkeypatch.setattr(ocr, 'OCR_MODEL_OBJ', ocr_model)
    monkeypatch.setattr(ocr_model, 'ocr', mock_called)
    with pytest.raises(ValueError):
        full.ocr_tsl_pipeline_lazy(image.md5)
    assert not hasattr(mock_called, 'called')

def test_lazy_noocr(
        monkeypatch, mock_called,
        language, box_model, ocr_model, tsl_model, image, bbox, box_run):
    """Test lazy pipeline with no box."""
    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(box, 'BOX_MODEL_OBJ', box_model)
    monkeypatch.setattr(ocr, 'OCR_MODEL_OBJ', ocr_model)
    monkeypatch.setattr(tsl, 'TSL_MODEL_OBJ', tsl_model)
    monkeypatch.setattr(tsl_model, 'translate', mock_called)

    bbox.from_ocr_merged.result_single.add(bbox)
    with pytest.raises(ValueError):
        full.ocr_tsl_pipeline_lazy(image.md5)
    assert not hasattr(mock_called, 'called')

def test_lazy_notsl(
        monkeypatch, mock_called,
        language, box_model, ocr_model, tsl_model, image, bbox, box_run, ocr_run):
    """Test lazy pipeline with no box."""
    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(box, 'BOX_MODEL_OBJ', box_model)
    monkeypatch.setattr(ocr, 'OCR_MODEL_OBJ', ocr_model)
    monkeypatch.setattr(tsl, 'TSL_MODEL_OBJ', tsl_model)
    monkeypatch.setattr(tsl_model, 'translate', mock_called)

    bbox.from_ocr_merged.result_single.add(bbox)
    with pytest.raises(TypeError):
        full.ocr_tsl_pipeline_lazy(image.md5)

    assert hasattr(mock_called, 'called')

def test_lazy_option_favor_manual(monkeypatch, mock_called, box_model, image):
    """Test lazy pipeline with no box."""
    options = {
        'favor_manual': True,
        'other': 'option'
    }
    monkeypatch.setattr(box, 'BOX_MODEL_OBJ', box_model)
    monkeypatch.setattr(box_model, 'box_detection', mock_called)

    with pytest.raises(TypeError):
        full.ocr_tsl_pipeline_lazy(image.md5, options=options)

    called_options: m.OptionDict = mock_called.kwargs['options']
    assert 'favor_manual' not in called_options.options
    assert 'other' in  called_options.options
