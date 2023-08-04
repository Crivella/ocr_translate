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
"""Tests for translation module."""

import pytest

from ocr_translate import models as m
from ocr_translate.ocr_tsl import tsl

tsl_globals = ['TSL_MODEL_OBJ']



@pytest.mark.django_db
def test_load_tsl_model(monkeypatch, mock_called, tsl_model: m.TSLModel):
    """Test load tsl model from scratch."""
    model_id = tsl_model.id
    def mock_fromentrypoint(*args, **kwargs):
        mock_fromentrypoint.called = True
        return tsl_model
    monkeypatch.setattr(m.TSLModel, 'from_entrypoint', mock_fromentrypoint)
    tsl_model.load = mock_called
    tsl.load_tsl_model(model_id)

    assert hasattr(mock_fromentrypoint, 'called')
    assert hasattr(mock_called, 'called')

def test_load_tsl_model_already_loaded(monkeypatch, mock_called):
    """Test load box model. With already loaded model."""
    model_id = 'test/id'
    monkeypatch.setattr(m.TSLModel, 'from_entrypoint', mock_called)
    monkeypatch.setattr(tsl, 'TSL_MODEL_ID', model_id)
    tsl.load_tsl_model(model_id)

    assert not hasattr(mock_called, 'called')

def test_unload_tsl_model(monkeypatch):
    """Test unload box model."""
    for key in tsl_globals:
        monkeypatch.setattr(tsl, key, f'mocked_{key}')

    tsl.unload_tsl_model()

    for key in tsl_globals:
        assert getattr(tsl, key) is None

def test_get_tsl_model(monkeypatch):
    """Test get ocr model function."""
    monkeypatch.setattr(tsl, 'TSL_MODEL_OBJ', 'test')
    assert tsl.get_tsl_model() == 'test'
