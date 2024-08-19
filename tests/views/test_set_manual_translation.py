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

pytestmark = pytest.mark.django_db

@pytest.fixture()
def post_kwargs(language):
    """Data for POST request."""
    return {
        'data': {
            'translation': 'Ciao',
            'text': 'Hello',
        },
        'content_type': 'application/json',
    }

def test_set_manual_translation_nonpost(client):
    """Test set_manual_translation with non POST request."""
    url = reverse('ocr_translate:set_manual_translation')
    response = client.get(url)
    assert response.status_code == 405

def test_set_manual_translation_post_noheader(client, mock_loaded):
    """Test set_manual_translation with POST request without content/type."""
    url = reverse('ocr_translate:set_manual_translation')
    response = client.post(url)

    assert response.status_code == 400

def test_set_manual_translation_post_missing_text(client, mock_loaded, post_kwargs):
    """Test set_manual_translation with POST request with missing text."""
    del post_kwargs['data']['text']

    url = reverse('ocr_translate:set_manual_translation')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 400

def test_set_manual_translation_post_missing_translation(client, mock_loaded, post_kwargs):
    """Test set_manual_translation with POST request with missing translation."""
    del post_kwargs['data']['translation']

    url = reverse('ocr_translate:set_manual_translation')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 400

def test_set_manual_translation_post_invalid_data(client, mock_loaded, post_kwargs):
    """Test set_manual_translation with POST request with non recognized field."""
    post_kwargs['data']['invalid_field'] = 'test'

    url = reverse('ocr_translate:set_manual_translation')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 400

def test_set_manual_translation_post_text_not_found(client, mock_loaded, post_kwargs):
    """Test set_manual_translation with POST request with text not found."""
    post_kwargs['data']['text'] = 'invalid'

    url = reverse('ocr_translate:set_manual_translation')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 404

def test_set_manual_translation_langnotloaded(
        client, post_kwargs, text,
        manual_model, option_dict, language
        ):
    """Test set_manual_translation with POST but no language loaded."""
    url = reverse('ocr_translate:set_manual_translation')
    post_kwargs['data']['text'] = text.text

    response = client.post(url, **post_kwargs)

    assert response.status_code == 512

def test_set_manual_translation_post_success_new(
        client, post_kwargs, text,
        manual_model, option_dict, language, mock_loaded_lang_only
        ):
    """Test set_manual_translation with POST request with success."""
    post_kwargs['data']['text'] = text.text

    assert m.TranslationRun.objects.count() == 0

    url = reverse('ocr_translate:set_manual_translation')
    response = client.post(url, **post_kwargs)

    assert response.status_code == 200
    assert m.TranslationRun.objects.count() == 1

@pytest.mark.django_db(transaction=True)
def test_set_manual_translation_post_success_exist(
        client, post_kwargs, text,
        manual_model, option_dict, language, mock_loaded_lang_only
        ):
    """Test set_manual_translation with POST request with success."""

    res = m.Text.objects.create(text='TEST')
    assert m.TranslationRun.objects.count() == 0
    m.TranslationRun.objects.create(
        text=text,
        result=res,
        model=manual_model,
        options=option_dict,
        lang_src=language,
        lang_dst=language,
    )
    assert m.TranslationRun.objects.count() == 1
    post_kwargs['data']['text'] = text.text

    url = reverse('ocr_translate:set_manual_translation')
    response = client.post(url, **post_kwargs)

    assert m.TranslationRun.objects.count() == 1

    assert response.status_code == 200
