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
"""Test django serverside views.handshake."""
# pylint: disable=redefined-outer-name

import pytest
from django.urls import reverse

from ocr_translate import models as m
from ocr_translate.ocr_tsl import lang

pytestmark = pytest.mark.django_db

def test_run_tsl_xua_nonget(client):
    """Test run_tsl_get_xunityautotrans with non GET request."""
    url = reverse('ocr_translate:run_tsl_get_xunityautotrans')
    response = client.post(url)
    assert response.status_code == 405

def test_run_tsl_xua_nolang(client):
    """Test run_tsl_get_xunityautotrans with GET request without loaded models."""
    url = reverse('ocr_translate:run_tsl_get_xunityautotrans')
    response = client.get(url)
    assert response.status_code == 512

def test_run_tsl_xua_no_models(client, mock_loaded_lang_only):
    """Test run_tsl_get_xunityautotrans with GET request without loaded models."""
    url = reverse('ocr_translate:run_tsl_get_xunityautotrans')
    response = client.get(url)
    assert response.status_code == 513

def test_run_tsl_xua_no_text(client, mock_loaded):
    """Test run_tsl_get_xunityautotrans with GET request without text."""
    url = reverse('ocr_translate:run_tsl_get_xunityautotrans')
    response = client.get(url)
    assert response.status_code == 400

class MockReturn:
    """Mock return object of tsl_model.translate(...)."""
    text = 'translated_hello'

@pytest.mark.parametrize('mock_called', [iter([MockReturn])], indirect=True)
def test_run_tsl_xua_ok(client, monkeypatch, mock_loaded, language, tsl_model, mock_called):
    """Test run_tsl_get_xunityautotrans with GET request."""
    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(lang, 'LANG_DST', language)
    monkeypatch.setattr(m.TSLModel, 'LOADED_MODEL', tsl_model)
    monkeypatch.setattr(tsl_model, 'translate', mock_called)

    assert len(m.Text.objects.all()) == 0

    url = reverse('ocr_translate:run_tsl_get_xunityautotrans')
    url += '?text=hello'
    response = client.get(url)

    assert len(m.Text.objects.all()) == 1

    assert response.status_code == 200
    assert response.content == b'translated_hello'
    assert hasattr(mock_called, 'called')
    text_obj = m.Text.objects.first()
    assert mock_called.args == (text_obj, language, language)
