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

from ocr_translate.ocr_tsl import tsl

pytestmark = pytest.mark.django_db

@pytest.fixture()
def post_kwargs(text):
    """Data for POST request."""
    return {
        'data': {
            'text': text.text,
        },
        'content_type': 'application/json',
    }

def test_run_tsl_nonpost(client):
    """Test run_tsl with non POST request."""
    url = reverse('ocr_translate:run_tsl')
    response = client.get(url)
    assert response.status_code == 405

def test_run_tsl_post_noheader(client):
    """Test run_tsl with POST request without content/type."""
    url = reverse('ocr_translate:run_tsl')
    response = client.post(url)

    assert response.status_code == 400

@pytest.mark.parametrize('remove_key', ['text'])
def test_run_tsl_post_missing_required(client, post_kwargs, remove_key):
    """Test run_tsl with POST request missing required field."""
    del post_kwargs['data'][remove_key]
    url = reverse('ocr_translate:run_tsl')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 400

def test_run_tsl_post_invalid_data(client, post_kwargs):
    """Test run_tsl with POST request with non recognized field."""
    post_kwargs['data']['invalid_field'] = 'test'
    url = reverse('ocr_translate:run_tsl')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 400

def test_run_tsl_langnotloaded(client, post_kwargs):
    """Test run_tsl with POST request with language not loaded."""
    post_kwargs['data']['text'] = 'test'
    url = reverse('ocr_translate:run_tsl')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 512

def test_run_tsl_modelnotloaded(client, post_kwargs, mock_loaded_lang_only):
    """Test run_tsl with POST request with model not loaded."""
    post_kwargs['data']['text'] = 'test'
    url = reverse('ocr_translate:run_tsl')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 513

def test_run_tsl_post_valid(client, monkeypatch, post_kwargs, mock_loaded, tsl_model):
    """Test run_tsl with POST request with valid data."""
    def mock_tsl_run(text, *args, **kwargs):
        """Mock translate."""
        yield text
    monkeypatch.setattr(tsl, 'TSL_MODEL_OBJ', tsl_model)
    tsl_model.translate = mock_tsl_run
    url = reverse('ocr_translate:run_tsl')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 200
    content = response.json()

    assert content['text'] == post_kwargs['data']['text']
