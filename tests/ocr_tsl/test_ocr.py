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
from ocr_translate.ocr_tsl import ocr

ocr_globals = ['OCR_MODEL_OBJ', 'OBJ_MODEL_ID']

@pytest.mark.django_db
def test_load_ocr_model(monkeypatch, mock_called, ocr_model: m.OCRModel):
    """Test load ocr model from scratch."""
    model_id = ocr_model.id
    def mock_fromentrypoint(*args, **kwargs):
        mock_fromentrypoint.called = True
        return ocr_model
    # Required to avoid setting global variables for future `from clean` tests
    monkeypatch.setattr(ocr, 'OCR_MODEL_OBJ', None)
    monkeypatch.setattr(ocr, 'OBJ_MODEL_ID', None)
    monkeypatch.setattr(m.OCRModel, 'from_entrypoint', mock_fromentrypoint)
    ocr_model.load = mock_called
    ocr.load_ocr_model(model_id)

    assert hasattr(mock_fromentrypoint, 'called')
    assert hasattr(mock_called, 'called')

def test_load_ocr_model_already_loaded(monkeypatch, mock_called):
    """Test load box model. With already loaded model."""
    model_id = 'test/id'
    monkeypatch.setattr(m.OCRModel, 'from_entrypoint', mock_called)
    monkeypatch.setattr(ocr, 'OBJ_MODEL_ID', model_id)
    ocr.load_ocr_model(model_id)

    assert not hasattr(mock_called, 'called')

def test_unload_ocr_model(monkeypatch):
    """Test unload box model."""
    for key in ocr_globals:
        monkeypatch.setattr(ocr, key, f'mocked_{key}')

    ocr.unload_ocr_model()

    for key in ocr_globals:
        assert getattr(ocr, key) is None

def test_get_ocr_model(monkeypatch):
    """Test get ocr model function."""
    monkeypatch.setattr(ocr, 'OCR_MODEL_OBJ', 'test')
    assert ocr.get_ocr_model() == 'test'

def test_unload_ocr_model_if_loaded(monkeypatch):
    """Test unload ocr model is called if load with an already loaded model."""
    class A(): # pylint: disable=invalid-name
        """Mocked OCRModel class."""
        def __init__(self):
            self.load_called = False
            self.unload_called = False
        def load(self): # pylint: disable=missing-function-docstring
            self.load_called = True
        def unload(self): # pylint: disable=missing-function-docstring
            self.unload_called = True
    a = A() # pylint: disable=invalid-name
    b = A() # pylint: disable=invalid-name
    monkeypatch.setattr(ocr, 'OCR_MODEL_OBJ', a)
    monkeypatch.setattr(ocr, 'OBJ_MODEL_ID', 'test')
    monkeypatch.setattr(m.OCRModel, 'from_entrypoint', lambda *args, **kwargs: b)
    ocr.load_ocr_model('test2')

    assert not a.load_called
    assert a.unload_called
    assert b.load_called
    assert not b.unload_called
