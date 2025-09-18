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
"""Tests for box module."""

import pytest

from ocr_translate import models as m

# from ocr_translate.messaging import Message

# def test_load_box_model_notimplemented():
#     """Test load box model. With not implemented model."""
#     model_id = 'notimplemented'
#     with pytest.raises(NotImplementedError):
#         box.load_box_model(model_id)

@pytest.mark.django_db
def test_load_box_model(monkeypatch, mock_called, box_model: m.OCRBoxModel):
    """Test load box model from scratch."""
    model_id = box_model.id
    def mock_fromentrypoint(*args, **kwargs):
        mock_fromentrypoint.called = True
        return box_model
    # Required to avoid setting global variables for future `from clean` tests
    monkeypatch.setattr(m.OCRBoxModel, 'LOADED_MODEL', None)
    monkeypatch.setattr(m.OCRBoxModel, 'from_entrypoint', mock_fromentrypoint)
    monkeypatch.setattr(box_model, 'load', mock_called)
    m.OCRBoxModel.load_model(model_id)

    assert hasattr(mock_fromentrypoint, 'called')
    assert hasattr(mock_called, 'called')

@pytest.mark.django_db
def test_load_box_model_already_loaded(monkeypatch, mock_called, box_model):
    """Test load box model. With already loaded model."""
    monkeypatch.setattr(m.OCRBoxModel, 'from_entrypoint', mock_called)
    monkeypatch.setattr(m.OCRBoxModel, 'LOADED_MODEL', box_model)
    m.OCRBoxModel.load_model(box_model.name)

    assert not hasattr(mock_called, 'called')

def test_get_box_model(monkeypatch):
    """Test get box model function."""
    monkeypatch.setattr(m.OCRBoxModel, 'LOADED_MODEL', 'test')
    assert m.OCRBoxModel.get_loaded_model() == 'test'
@pytest.mark.django_db

def test_unload_box_model(monkeypatch, box_model, mock_called):
    """Test unload box model function."""
    monkeypatch.setattr(m.OCRBoxModel, 'LOADED_MODEL', box_model)
    monkeypatch.setattr(box_model, 'unload', mock_called)
    m.OCRBoxModel.unload_model()
    assert m.OCRBoxModel.LOADED_MODEL is None
    assert hasattr(mock_called, 'called')

def test_unload_box_model_if_loaded(monkeypatch):
    """Test unload box model is called if load with an already loaded model."""
    class A(): # pylint: disable=missing-class-docstring,invalid-name
        def __init__(self, name):
            self.load_called = False
            self.unload_called = False
            self.name = name
        def load(self): # pylint: disable=missing-function-docstring
            self.load_called = True
        def unload(self): # pylint: disable=missing-function-docstring
            self.unload_called = True
    a = A('test1') # pylint: disable=invalid-name
    b = A('test2') # pylint: disable=invalid-name
    monkeypatch.setattr(m.OCRBoxModel, 'LOADED_MODEL', a)
    monkeypatch.setattr(m.OCRBoxModel, 'from_entrypoint', lambda *args, **kwargs: b)
    m.OCRBoxModel.load_model('test2')

    assert not a.load_called
    assert a.unload_called
    assert b.load_called
    assert not b.unload_called
