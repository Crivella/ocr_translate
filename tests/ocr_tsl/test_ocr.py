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
"""Tests for ocr module."""

import pytest

from ocr_translate import models as m


@pytest.mark.django_db
def test_load_ocr_model(monkeypatch, mock_called, ocr_model: m.OCRModel):
    """Test load ocr model from scratch."""
    model_id = ocr_model.name
    def mock_fromentrypoint(*args, **kwargs):
        mock_fromentrypoint.called = True
        return ocr_model
    # Required to avoid setting global variables for future `from clean` tests
    monkeypatch.setattr(m.OCRModel, 'from_entrypoint', mock_fromentrypoint)
    ocr_model.load = mock_called
    m.OCRModel.load_model(model_id)

    assert hasattr(mock_fromentrypoint, 'called')
    assert hasattr(mock_called, 'called')

@pytest.mark.django_db
def test_load_ocr_model_already_loaded(monkeypatch, mock_called, ocr_model_loaded: m.OCRModel):
    """Test load box model. With already loaded model."""
    model_id = ocr_model_loaded.name
    monkeypatch.setattr(m.OCRModel, 'from_entrypoint', mock_called)
    m.OCRModel.load_model(model_id)

    assert not hasattr(mock_called, 'called')

@pytest.mark.django_db
def test_unload_ocr_model(ocr_model_loaded):
    """Test unload box model."""
    assert m.OCRModel.get_loaded_model() == ocr_model_loaded
    ocr_model_loaded.unload = lambda: None
    m.OCRModel.unload_model()
    assert m.OCRModel.get_loaded_model() is None

def test_unload_ocr_model_if_loaded(monkeypatch, mock_base_model):
    """Test unload ocr model is called if load with an already loaded model."""
    base1 = mock_base_model('test1')
    base2 = mock_base_model('test2')
    monkeypatch.setattr(m.OCRModel, 'LOADED_MODEL', base1)
    monkeypatch.setattr(m.OCRModel, 'from_entrypoint', lambda *args, **kwargs: base2)
    m.OCRModel.load_model('test2')

    assert not base1.load_called
    assert base1.unload_called
    assert base2.load_called
    assert not base2.unload_called
