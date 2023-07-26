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
