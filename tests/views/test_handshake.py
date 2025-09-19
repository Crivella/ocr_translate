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

import http.cookies

import pytest
from django.urls import reverse

from ocr_translate import __version__array__
from ocr_translate.ocr_tsl.cached_lists import refresh_model_cache

pytestmark = pytest.mark.django_db

def test_handshake_wrong_method(client):
    """Test handshake with wrong method."""
    url = reverse('ocr_translate:handshake')
    response = client.post(url)
    assert response.status_code == 405

def test_handshake_clean_empty(client):
    """Test handshake."""
    url = reverse('ocr_translate:handshake')
    response = client.get(url)
    assert response.status_code == 200
    content = response.json()

    # Check that the csrf cookie is set
    assert isinstance(response.cookies, http.cookies.SimpleCookie)
    assert response.cookies['csrftoken']

    assert content['version'] == __version__array__

    for key in ['Languages', 'Languages_hr', 'BOXModels', 'OCRModels', 'TSLModels']:
        assert content[key] == []
    for key in ['box_selected', 'ocr_selected', 'tsl_selected']:
        assert content[key] == ''
    for key in ['lang_src', 'lang_dst']:
        assert content[key] == ''

def test_handshake_clean_content(client, language, box_model, ocr_model, tsl_model):
    """Test handshake with content in the database."""
    url = reverse('ocr_translate:handshake')
    response = client.get(url)
    assert response.status_code == 200
    content = response.json()

    assert content['Languages'] == ['ja']
    assert content['Languages_hr'] == ['Japanese']
    assert content['BOXModels'] == []
    assert content['OCRModels'] == []
    assert content['TSLModels'] == []

    for key in ['box_selected', 'ocr_selected', 'tsl_selected']:
        assert content[key] == ''
    for key in ['lang_src', 'lang_dst']:
        assert content[key] == ''

def test_handshake_initialized_lang_only(
        monkeypatch, client,
        lang_src_loaded, lang_dst_loaded, box_model, ocr_model, tsl_model):
    """Test handshake with content in the database."""
    refresh_model_cache()

    url = reverse('ocr_translate:handshake')
    response = client.get(url)
    assert response.status_code == 200
    content = response.json()

    assert content['Languages'] == ['ja']
    assert content['Languages_hr'] == ['Japanese']
    assert content['BOXModels'] == [box_model.name]
    assert content['OCRModels'] == [ocr_model.name]
    assert content['TSLModels'] == [tsl_model.name]

    assert content['lang_src'] == 'ja'
    assert content['lang_dst'] == 'ja'

    for key in ['box_selected', 'ocr_selected', 'tsl_selected']:
        assert content[key] == ''

def test_handshake_initialized(client, monkeypatch, language, box_model, tsl_model, ocr_model, mock_loaded):
    """Test handshake with content + init."""
    refresh_model_cache()

    url = reverse('ocr_translate:handshake')
    response = client.get(url)
    assert response.status_code == 200
    content = response.json()

    assert content['Languages'] == ['ja']
    assert content['Languages_hr'] == ['Japanese']
    assert content['BOXModels'] == [box_model.name]
    assert content['OCRModels'] == [ocr_model.name]
    assert content['TSLModels'] == [tsl_model.name]

    assert content['box_selected'] == box_model.name
    assert content['ocr_selected'] == ocr_model.name
    assert content['tsl_selected'] == tsl_model.name

    assert content['lang_src'] == 'ja'
    assert content['lang_dst'] == 'ja'
