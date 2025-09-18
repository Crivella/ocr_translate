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
"""Test django serverside views.set_lang."""
# pylint: disable=redefined-outer-name

import pytest
from django.urls import reverse

from ocr_translate import models as m
from ocr_translate.ocr_tsl import lang

pytestmark = pytest.mark.django_db

@pytest.fixture()
def post_kwargs(language):
    """Data for POST request."""
    return {
        'data': {
            'lang_src': language.iso1,
            'lang_dst': language.iso1,
        },
        'content_type': 'application/json',
    }

def test_set_lang_nonpost(client):
    """Test set_lang with non POST request."""
    url = reverse('ocr_translate:set_lang')
    response = client.get(url)
    assert response.status_code == 405

def test_set_lang_post_noheader(client):
    """Test set_lang with POST request without content/type."""
    url = reverse('ocr_translate:set_lang')
    response = client.post(url)

    assert response.status_code == 400

def test_set_lang_post_fail_load(client, post_kwargs):
    """Test set_lang with POST request with wrong lang data (cause exceptio in load_lang_XXX)."""
    post_kwargs['data']['lang_src'] = 'invalid'

    url = reverse('ocr_translate:set_lang')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 400

def test_set_lang_post_invalid_data(client, post_kwargs):
    """Test set_lang with POST request with non recognized field."""
    post_kwargs['data']['invalid_field'] = 'test'

    url = reverse('ocr_translate:set_lang')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 400

@pytest.mark.parametrize('remove_key', ['lang_src', 'lang_dst'])
def test_set_lang_post_missing_required(client, post_kwargs, remove_key):
    """Test set_lang with POST request missing required field."""
    del post_kwargs['data'][remove_key]
    url = reverse('ocr_translate:set_lang')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 400

def test_set_lang_post_valid(client, mock_loaders, language, post_kwargs):
    """Test set_lang with POST valid request."""
    url = reverse('ocr_translate:set_lang')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 200

    assert lang.LANG_SRC == language
    assert lang.LANG_DST == language

def test_set_lang_post_no_unload_tsl(
        client, post_kwargs,
        monkeypatch, mock_loaders, mock_called,
        tsl_model,
        language, language2,
        ):
    """Test set_lang with POST valid request. Switching either lang_src or dst has to cause unloading of tsl model
    if the model does not support that language."""
    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(m.TSLModel, 'LOADED_MODEL', tsl_model)
    monkeypatch.setattr(m.TSLModel, 'unload_model', mock_called)

    tsl_model.src_languages.add(language2)

    post_kwargs['data']['lang_src'] = language2.iso1
    url = reverse('ocr_translate:set_lang')
    client.post(url, **post_kwargs)

    assert not hasattr(mock_called, 'called')

def test_set_lang_post_unload_tsl(
        client, post_kwargs,
        monkeypatch, mock_loaders, mock_called,
        tsl_model,
        language, language2,
        ):
    """Test set_lang with POST valid request. Switching either lang_src or dst has to cause unloading of tsl model
    if the model does not support that language."""
    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(m.TSLModel, 'LOADED_MODEL', tsl_model)
    monkeypatch.setattr(m.TSLModel, 'unload_model', mock_called)

    post_kwargs['data']['lang_src'] = language2.iso1
    url = reverse('ocr_translate:set_lang')
    client.post(url, **post_kwargs)

    assert hasattr(mock_called, 'called')

def test_set_lang_post_no_unload_ocr(
        client, post_kwargs,
        monkeypatch, mock_loaders, mock_called,
        ocr_model,
        language, language2,
        ):
    """Test set_lang with POST valid request. Switching lang_src has to cause unloading of ocr model
    if the model does not support that language."""
    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(m.OCRModel, 'LOADED_MODEL', ocr_model)
    monkeypatch.setattr(m.OCRModel, 'unload_model', mock_called)

    ocr_model.languages.add(language2)

    post_kwargs['data']['lang_src'] = language2.iso1
    url = reverse('ocr_translate:set_lang')
    client.post(url, **post_kwargs)

    assert not hasattr(mock_called, 'called')

def test_set_lang_post_unload_ocr(
        client, post_kwargs,
        monkeypatch, mock_loaders, mock_called,
        ocr_model,
        language, language2,
        ):
    """Test set_lang with POST valid request. Switching lang_src has to cause unloading of ocr model
    if the model does not support that language."""
    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(m.OCRModel, 'LOADED_MODEL', ocr_model)
    monkeypatch.setattr(m.OCRModel, 'unload_model', mock_called)

    post_kwargs['data']['lang_src'] = language2.iso1
    url = reverse('ocr_translate:set_lang')
    client.post(url, **post_kwargs)

    assert hasattr(mock_called, 'called')

def test_set_lang_post_no_unload_box(
        client, post_kwargs,
        monkeypatch, mock_loaders, mock_called,
        box_model,
        language, language2,
        ):
    """Test set_lang with POST valid request. Switching lang_src has to cause unloading of box model
    if the model does not support that language."""
    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(m.OCRBoxModel, 'LOADED_MODEL', box_model)
    monkeypatch.setattr(m.OCRBoxModel, 'unload_model', mock_called)

    box_model.languages.add(language2)

    post_kwargs['data']['lang_src'] = language2.iso1
    url = reverse('ocr_translate:set_lang')
    client.post(url, **post_kwargs)

    assert not hasattr(mock_called, 'called')

def test_set_lang_post_unload_box(
        client, post_kwargs,
        monkeypatch, mock_loaders, mock_called,
        box_model,
        language, language2,
        ):
    """Test set_lang with POST valid request. Switching lang_src has to cause unloading of box model
    if the model does not support that language."""
    monkeypatch.setattr(lang, 'LANG_SRC', language)
    monkeypatch.setattr(m.OCRBoxModel, 'LOADED_MODEL', box_model)
    monkeypatch.setattr(m.OCRBoxModel, 'unload_model', mock_called)

    post_kwargs['data']['lang_src'] = language2.iso1
    url = reverse('ocr_translate:set_lang')
    client.post(url, **post_kwargs)

    assert hasattr(mock_called, 'called')
