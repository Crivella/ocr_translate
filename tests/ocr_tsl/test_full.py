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
# pylint: disable=too-many-positional-arguments,too-many-arguments


import pytest

from ocr_translate import models as m
from ocr_translate.ocr_tsl import full, lang

pytestmark = pytest.mark.django_db

def test_lazy_nonexistent_image(option_dict):
    """Test lazy pipeline with nonexistent image."""
    with pytest.raises(ValueError):
        full.ocr_tsl_pipeline_lazy(
            'nonexistent',
            options_box=option_dict, options_ocr=option_dict, options_tsl=option_dict
            )

def test_lazy_nobox(
        monkeypatch, mock_called,
        language, box_model, ocr_model, image, option_dict):
    """Test lazy pipeline with no box."""
    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(m.OCRBoxModel, 'LOADED_MODEL', box_model)
    monkeypatch.setattr(m.OCRModel, 'LOADED_MODEL', ocr_model)
    monkeypatch.setattr(ocr_model, 'ocr', mock_called)
    with pytest.raises(ValueError):
        full.ocr_tsl_pipeline_lazy(
            image.md5,
            options_box=option_dict, options_ocr=option_dict, options_tsl=option_dict
            )
    assert not hasattr(mock_called, 'called')

def test_lazy_noocr(
        monkeypatch, mock_called,
        language, box_model, ocr_model, tsl_model, image, bbox, box_run, option_dict):
    """Test lazy pipeline with no ocr."""
    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(m.OCRBoxModel, 'LOADED_MODEL', box_model)
    monkeypatch.setattr(m.OCRModel, 'LOADED_MODEL', ocr_model)
    monkeypatch.setattr(m.TSLModel, 'LOADED_MODEL', tsl_model)
    monkeypatch.setattr(tsl_model, 'translate', mock_called)

    bbox.from_ocr_merged.result_single.add(bbox)
    with pytest.raises(ValueError):
        full.ocr_tsl_pipeline_lazy(
            image.md5,
            options_box=option_dict, options_ocr=option_dict, options_tsl=option_dict
            )
    assert not hasattr(mock_called, 'called')

def test_lazy_notsl(
        monkeypatch, mock_called,
        language, box_model, ocr_model, tsl_model, image, bbox, box_run, ocr_run, option_dict):
    """Test lazy pipeline with no translation."""
    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(m.OCRBoxModel, 'LOADED_MODEL', box_model)
    monkeypatch.setattr(m.OCRModel, 'LOADED_MODEL', ocr_model)
    monkeypatch.setattr(m.TSLModel, 'LOADED_MODEL', tsl_model)
    monkeypatch.setattr(tsl_model, 'translate', mock_called)

    bbox.from_ocr_merged.result_single.add(bbox)
    with pytest.raises(TypeError):
        full.ocr_tsl_pipeline_lazy(
            image.md5,
            options_box=option_dict, options_ocr=option_dict, options_tsl=option_dict
            )

    assert hasattr(mock_called, 'called')

def test_lazy_option_favor_manual_absent(
        monkeypatch, mock_called,
        language, box_model, ocr_model, tsl_model, image, bbox, box_run, ocr_run, option_dict
        ):
    """Test favor manual translation option when absent."""
    # options = {
    #     'favor_manual': True,
    #     'other': 'option'
    # }
    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(m.OCRBoxModel, 'LOADED_MODEL', box_model)
    monkeypatch.setattr(m.OCRModel, 'LOADED_MODEL', ocr_model)
    monkeypatch.setattr(m.TSLModel, 'LOADED_MODEL', tsl_model)
    monkeypatch.setattr(tsl_model, 'translate', mock_called)

    bbox.from_ocr_merged.result_single.add(bbox)
    with pytest.raises(TypeError):
        full.ocr_tsl_pipeline_work(
            image, image.md5,
            options_box=option_dict, options_ocr=option_dict, options_tsl=option_dict
            )

    assert mock_called.kwargs['favor_manual'] is True

def test_lazy_option_favor_manual_specified_true(
        monkeypatch, mock_called,
        language, box_model, ocr_model, tsl_model, image, bbox, box_run, ocr_run, option_dict
        ):
    """Test favor manual translation option when set True."""
    options = {
        'favor_manual': True,
        'other': 'option'
    }
    new_opt = m.OptionDict.objects.create(options=options)
    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(m.OCRBoxModel, 'LOADED_MODEL', box_model)
    monkeypatch.setattr(m.OCRModel, 'LOADED_MODEL', ocr_model)
    monkeypatch.setattr(m.TSLModel, 'LOADED_MODEL', tsl_model)
    monkeypatch.setattr(tsl_model, 'translate', mock_called)

    bbox.from_ocr_merged.result_single.add(bbox)
    with pytest.raises(TypeError):
        full.ocr_tsl_pipeline_work(
            image, image.md5,
            options_box=option_dict, options_ocr=option_dict, options_tsl=new_opt
            )

    assert mock_called.kwargs['favor_manual'] is True

def test_lazy_option_favor_manual_specified_false(
        monkeypatch, mock_called,
        language, box_model, ocr_model, tsl_model, image, bbox, box_run, ocr_run, option_dict
        ):
    """Test favor manual translation option when set False."""
    options = {
        'favor_manual': False,
        'other': 'option'
    }
    new_opt = m.OptionDict.objects.create(options=options)
    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(m.OCRBoxModel, 'LOADED_MODEL', box_model)
    monkeypatch.setattr(m.OCRModel, 'LOADED_MODEL', ocr_model)
    monkeypatch.setattr(m.TSLModel, 'LOADED_MODEL', tsl_model)
    monkeypatch.setattr(tsl_model, 'translate', mock_called)

    bbox.from_ocr_merged.result_single.add(bbox)
    with pytest.raises(TypeError):
        full.ocr_tsl_pipeline_work(
            image, image.md5,
            options_box=option_dict, options_ocr=option_dict, options_tsl=new_opt
            )

    assert mock_called.kwargs['favor_manual'] is False
